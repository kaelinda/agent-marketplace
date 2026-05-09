"""
OpenViking Memory Skill Suite — Mem0 adapter.
Bridges the MemoryAdapter protocol to mem0ai (v2.x) SDK.

Mem0 v2 API notes:
- Memory.__init__(config) — config dict controls store/embedder/graph etc.
- Memory.add(messages, user_id=, agent_id=, metadata=) — entity IDs are top-level
- Memory.search(query, filters={"user_id": "..."}, top_k=, threshold=) — entity IDs go in filters
- Memory.get_all(filters={"user_id": "..."}, top_k=) — entity IDs go in filters
- Memory.get(memory_id) — get single memory
- Memory.update(memory_id, data, metadata=) — update text + optional metadata
- Memory.delete(memory_id) — delete single
- Memory.delete_all(user_id=, agent_id=) — bulk delete

Filters support rich operators: eq, ne, in, nin, gt, gte, lt, lte, contains, AND, OR, NOT.

Scope mapping:
- viking://tenants/{t}/users/{u}/memories/   → filters={"user_id": "{t}:{u}"}
- viking://tenants/{t}/agents/{a}/memories/  → filters={"agent_id": "{t}:{a}"}
- viking://tenants/{t}/system/{s}/           → filters={"agent_id": "{t}:system:{s}"}
"""
from __future__ import annotations

import os
import re
import time
from typing import Any


# ── Scope URI parser ────────────────────────────────────────

_SCOPE_RE = re.compile(
    r"viking://tenants/(?P<tenant>[^/]+)/(?P<entity_type>users|agents|system)/(?P<entity>[^/]+)"
)


def _parse_scope(scope: str, default_user_id: str = "default_user") -> dict:
    """
    Parse a scope URI into mem0 filters dict.

    Returns:
        {"user_id": "..."} or {"agent_id": "..."} for mem0 filters.
    """
    if not scope:
        return {"user_id": default_user_id}

    m = _SCOPE_RE.search(scope)
    if not m:
        return {"user_id": default_user_id}

    tenant = m.group("tenant")
    entity_type = m.group("entity_type")
    entity = m.group("entity")

    if entity_type == "users":
        return {"user_id": f"{tenant}:{entity}"}
    elif entity_type == "agents":
        return {"agent_id": f"{tenant}:{entity}"}
    else:  # system
        return {"agent_id": f"{tenant}:system:{entity}"}


def _scope_to_entity_params(scope: str, default_user_id: str = "default_user") -> dict:
    """
    Parse scope URI into mem0 add() style top-level params (user_id / agent_id).
    Same logic as _parse_scope, just named differently for clarity.
    """
    return _parse_scope(scope, default_user_id)


# ── Response helpers ────────────────────────────────────────

def _ok(data: Any = None, meta: dict | None = None) -> dict:
    resp = {"ok": True}
    if data is not None:
        resp["data"] = data
    if meta:
        resp["meta"] = meta
    return resp


def _err(error: str, meta: dict | None = None) -> dict:
    resp = {"ok": False, "error": error}
    if meta:
        resp["meta"] = meta
    return resp


def _to_standard_memory(item: dict) -> dict:
    """Convert a mem0 result item to the project's standard memory format."""
    meta = item.get("metadata") or {}
    return {
        "id": item.get("id", ""),
        "type": meta.get("type", ""),
        "title": meta.get("title", ""),
        "content": item.get("memory", item.get("text", "")),
        "summary": meta.get("summary", ""),
        "tags": meta.get("tags", []),
        "entities": meta.get("entities", []),
        "confidence": meta.get("confidence", 0.85),
        "source": {"kind": meta.get("source_kind", "")},
        "policy": {
            "sensitive": meta.get("sensitive", False),
            "retention": meta.get("retention", "long_term"),
        },
        "status": meta.get("status", "active"),
        "created_at": item.get("created_at", ""),
        "updated_at": item.get("updated_at", ""),
        "scope": meta.get("_scope", ""),
    }


def _memory_to_metadata(memory: dict, scope: str = "") -> dict:
    """Extract metadata dict from a project memory object for mem0 storage."""
    return {
        "type": memory.get("type", ""),
        "title": memory.get("title", ""),
        "summary": memory.get("summary", ""),
        "tags": memory.get("tags", []),
        "entities": memory.get("entities", []),
        "confidence": memory.get("confidence", 0.85),
        "source_kind": (memory.get("source") or {}).get("kind", ""),
        "sensitive": (memory.get("policy") or {}).get("sensitive", False),
        "retention": (memory.get("policy") or {}).get("retention", "long_term"),
        "status": memory.get("status", "active"),
        "_scope": scope,
    }


# ── Mem0 Adapter ────────────────────────────────────────────


class Mem0Adapter:
    """
    MemoryAdapter implementation backed by mem0ai SDK (v2.x).

    Config (via config.json):
        {
            "backend": "mem0",
            "mem0": {
                "api_key_env": "MEM0_API_KEY",
                "version": "v1.1",
                "org_id": "...",
                "project_id": "..."
            }
        }

    Or pass a pre-built config dict to __init__(mem0_config=...).
    """

    def __init__(
        self,
        base_url: str = "",
        api_key: str | None = None,
        timeout: int = 10,
        mem0_config: dict | None = None,
    ):
        """
        Args:
            base_url: Ignored (mem0 uses its own API endpoint). Kept for factory compat.
            api_key:  Mem0 API key. Falls back to MEM0_API_KEY env var.
            timeout:  Ignored (mem0 SDK handles its own timeouts).
            mem0_config: Full mem0 config dict passed to Memory(config=...).
                         If None, builds a default cloud config from api_key.
        """
        # Lazy import — don't crash at module load if mem0ai isn't installed
        from mem0 import Memory

        if mem0_config:
            self._config = mem0_config
        else:
            resolved_key = api_key or os.environ.get("MEM0_API_KEY", "")
            if not resolved_key:
                raise ValueError(
                    "Mem0 API key required. Set MEM0_API_KEY env var, pass api_key, "
                    "or provide mem0_config dict."
                )
            self._config = {
                "version": "v1.1",
                "api_key": resolved_key,
            }

        self._mem0 = Memory(config=self._config)

        # Default identity from config or fallback
        self.default_user_id = "default_user"

    # ── Scope ───────────────────────────────────────────────

    def build_scope(self, tenant_id: str, entity_type: str, entity_id: str) -> str:
        """Construct a scope URI (same format as other adapters)."""
        if entity_type == "system":
            return f"viking://tenants/{tenant_id}/system/{entity_id}/"
        return f"viking://tenants/{tenant_id}/{entity_type}s/{entity_id}/memories/"

    # ── Search ──────────────────────────────────────────────

    def search(
        self,
        query: str,
        scope: str = "",
        limit: int = 6,
        memory_type: str = "",
        min_score: float = 0.0,
        extra_scopes: list[str] = (),
    ) -> dict:
        """Search memories by semantic similarity.

        Phase 3: ``extra_scopes`` is honoured by issuing one mem0 search
        per scope and merging client-side. mem0's filter API is
        single-entity (one user_id or one agent_id per query), so
        multi-scope can't be done in a single round-trip.
        """
        start = time.monotonic()

        try:
            scopes_to_search = [scope] if scope else []
            scopes_to_search.extend(extra_scopes or ())
            if not scopes_to_search:
                scopes_to_search = [""]

            seen_ids: set[str] = set()
            memories: list[dict] = []
            for s in scopes_to_search:
                filters = _parse_scope(s, self.default_user_id)
                if memory_type:
                    filters["metadata"] = {"type": memory_type}
                raw = self._mem0.search(
                    query=query,
                    filters=filters,
                    top_k=limit,
                    threshold=min_score if min_score > 0 else 0.1,
                )
                results = raw.get("results", []) if isinstance(raw, dict) else []
                for item in results:
                    mem = _to_standard_memory(item)
                    mem["score"] = item.get("score", 0.0)
                    if min_score > 0 and mem["score"] < min_score:
                        continue
                    mid = mem.get("id", "")
                    if mid in seen_ids:
                        continue
                    seen_ids.add(mid)
                    memories.append(mem)
                    if len(memories) >= limit:
                        break
                if len(memories) >= limit:
                    break

            elapsed_ms = int((time.monotonic() - start) * 1000)
            return _ok(memories, {"backend": "mem0", "elapsed_ms": elapsed_ms})

        except Exception as e:
            return _err(f"mem0 search failed: {e}", {"backend": "mem0"})

    # ── Read ────────────────────────────────────────────────

    def read(self, memory_id: str) -> dict:
        """Read a single memory by ID."""
        try:
            raw = self._mem0.get(memory_id)

            if not raw:
                return _err(f"Memory {memory_id} not found")

            # mem0 get() may return the item directly or nested
            item = raw if isinstance(raw, dict) and "id" in raw else raw
            return _ok(_to_standard_memory(item), {"backend": "mem0"})

        except Exception as e:
            return _err(f"mem0 read failed: {e}", {"backend": "mem0"})

    # ── Write ───────────────────────────────────────────────

    def write(self, memory: dict, scope: str = "") -> dict:
        """Write a new memory. The memory's content is stored as text,
        all other fields are preserved in metadata."""
        start = time.monotonic()

        content = memory.get("content", "")
        if not content:
            return _err("content is required")

        try:
            entity_params = _scope_to_entity_params(scope, self.default_user_id)
            metadata = _memory_to_metadata(memory, scope)

            raw = self._mem0.add(
                messages=content,
                metadata=metadata,
                **entity_params,
            )

            elapsed_ms = int((time.monotonic() - start) * 1000)

            # Extract new memory ID from response
            new_id = ""
            results = raw.get("results", []) if isinstance(raw, dict) else []
            if results:
                new_id = results[0].get("id", "")
            elif isinstance(raw, dict) and "id" in raw:
                new_id = raw["id"]

            result_data = dict(memory)
            result_data["id"] = new_id or memory.get("id", "")
            result_data["scope"] = scope

            return _ok(result_data, {"backend": "mem0", "elapsed_ms": elapsed_ms})

        except Exception as e:
            return _err(f"mem0 write failed: {e}", {"backend": "mem0"})

    # ── Update ──────────────────────────────────────────────

    def update(self, memory_id: str, patch: dict) -> dict:
        """Update an existing memory.

        If patch contains 'content', it becomes the new text.
        Otherwise the text is unchanged and only metadata is updated.
        """
        try:
            new_text = patch.get("content", patch.get("title", ""))

            # Build metadata from patch (merge with scope hint if available)
            metadata = {}
            if "type" in patch:
                metadata["type"] = patch["type"]
            if "title" in patch:
                metadata["title"] = patch["title"]
            if "summary" in patch:
                metadata["summary"] = patch["summary"]
            if "tags" in patch:
                metadata["tags"] = patch["tags"]
            if "status" in patch:
                metadata["status"] = patch["status"]

            raw = self._mem0.update(
                memory_id,
                data=new_text if new_text else None,
                metadata=metadata if metadata else None,
            )

            return _ok(
                {"id": memory_id, **patch},
                {"backend": "mem0"},
            )

        except Exception as e:
            return _err(f"mem0 update failed: {e}", {"backend": "mem0"})

    # ── Delete ──────────────────────────────────────────────

    def delete(self, memory_id: str) -> dict:
        """Delete a memory by ID."""
        try:
            self._mem0.delete(memory_id)
            return _ok(
                {"id": memory_id, "deleted": True},
                {"backend": "mem0"},
            )
        except Exception as e:
            return _err(f"mem0 delete failed: {e}", {"backend": "mem0"})

    # ── Browse ──────────────────────────────────────────────

    def browse(self, scope: str = "", limit: int = 20, offset: int = 0) -> dict:
        """Browse memories in a scope.

        Note: mem0 get_all doesn't support server-side offset pagination.
        We fetch `limit + offset` items and slice locally.
        For large datasets this will be slow — consider adding cursor support later.
        """
        try:
            filters = _parse_scope(scope, self.default_user_id)

            # Fetch enough to cover offset + limit
            fetch_count = min(limit + offset, 1000)  # safety cap

            raw = self._mem0.get_all(
                filters=filters,
                top_k=fetch_count,
            )

            results = raw.get("results", [])
            memories = [_to_standard_memory(item) for item in results]

            # Local slice to simulate offset
            sliced = memories[offset : offset + limit]

            return _ok(sliced, {
                "backend": "mem0",
                "total": len(results),
                "offset": offset,
                "limit": limit,
            })

        except Exception as e:
            return _err(f"mem0 browse failed: {e}", {"backend": "mem0"})

    # ── Commit (batch write) ────────────────────────────────

    def commit(self, memories: list[dict], scope: str = "") -> dict:
        """Batch commit memories to mem0.

        mem0 has no native batch add, so we iterate.
        Uses sequential writes with error collection.
        """
        committed = []
        errors = []

        for mem in memories:
            result = self.write(mem, scope=scope)
            if result.get("ok"):
                committed.append(result.get("data", {}))
            else:
                errors.append({
                    "title": mem.get("title", mem.get("content", "")[:50]),
                    "error": result.get("error", "unknown"),
                })

        ok = len(errors) == 0
        data = {
            "committed": len(committed),
            "memories": committed,
        }
        if errors:
            data["errors"] = errors

        return _ok(data, {"backend": "mem0"}) if ok else _err(
            f"{len(errors)} of {len(memories)} memories failed to commit",
            {"backend": "mem0", "committed": len(committed), "errors": errors},
        )

    # ── Sharing (Phase 3) ──────────────────────────────────────
    #
    # mem0's metadata is queryable, so we store ACL fields on the
    # memory's metadata and use metadata filters to find subscribed
    # memories. SharingManager.can_access does the final ACL check
    # so we don't have to push complex predicates to mem0.

    def share(self, memory_id: str, target: str,
              permission: str = "read") -> dict:
        if permission not in ("read", "write"):
            return _err(f"invalid permission {permission!r}; expected read|write")
        try:
            raw = self._mem0.get(memory_id)
            if not raw:
                return _err(f"memory {memory_id} not found")
            metadata = (raw.get("metadata") or {}) if isinstance(raw, dict) else {}
            shared_with = list(metadata.get("shared_with") or [])
            if target not in shared_with:
                shared_with.append(target)
            perms = dict(metadata.get("shared_perms") or {})
            perms[target] = permission
            new_metadata = dict(metadata)
            new_metadata["shared_with"] = shared_with
            new_metadata["shared_perms"] = perms
            self._mem0.update(memory_id, data=None, metadata=new_metadata)
            return _ok(
                {"id": memory_id, "target": target, "permission": permission},
                {"backend": "mem0"},
            )
        except Exception as e:
            return _err(f"mem0 share failed: {e}", {"backend": "mem0"})

    def unshare(self, memory_id: str, target: str) -> dict:
        try:
            raw = self._mem0.get(memory_id)
            if not raw:
                return _err(f"memory {memory_id} not found")
            metadata = (raw.get("metadata") or {}) if isinstance(raw, dict) else {}
            shared_with = [t for t in (metadata.get("shared_with") or []) if t != target]
            perms = {k: v for k, v in (metadata.get("shared_perms") or {}).items()
                     if k != target}
            new_metadata = dict(metadata)
            new_metadata["shared_with"] = shared_with
            new_metadata["shared_perms"] = perms
            self._mem0.update(memory_id, data=None, metadata=new_metadata)
            return _ok({"id": memory_id, "target": target}, {"backend": "mem0"})
        except Exception as e:
            return _err(f"mem0 unshare failed: {e}", {"backend": "mem0"})

    def list_subscribed(self, identity: str) -> dict:
        """Find memories whose metadata.shared_with contains ``identity``.

        For ``team:<id>`` we additionally union memories living in the
        team's mem0 entity (agent_id = "{tenant}:{team_id}") so a write
        to a team scope is automatically subscribed by every member.
        """
        try:
            results: list[dict] = []
            seen: set[str] = set()
            # Team scope: memories written into the team's entity
            if identity.startswith("team:"):
                team_id = identity.split(":", 1)[1]
                # Use the same encoding as _parse_scope for system→agent_id.
                # We don't know tenant here so we can't be precise; iterate
                # over the in-mem cache by metadata _scope marker to be safe.
                team_marker = f"/teams/{team_id}/"
                raw = self._mem0.get_all(filters={}, top_k=1000)
                for item in (raw.get("results") or []):
                    meta = item.get("metadata") or {}
                    if team_marker in (meta.get("_scope") or ""):
                        mem = _to_standard_memory(item)
                        mid = mem.get("id", "")
                        if mid and mid not in seen:
                            seen.add(mid)
                            results.append(mem)
            # Explicit shared_with grants — mem0 metadata filter
            try:
                raw = self._mem0.search(
                    query="*",  # match-anything; threshold low
                    filters={"metadata": {"shared_with": {"contains": identity}}},
                    top_k=1000,
                    threshold=0.0,
                )
                items = raw.get("results", []) if isinstance(raw, dict) else []
            except Exception:
                # Fallback: get_all and filter client-side
                items = (self._mem0.get_all(filters={}, top_k=1000) or {}).get("results", [])
            for item in items:
                meta = item.get("metadata") or {}
                if identity in (meta.get("shared_with") or []):
                    mem = _to_standard_memory(item)
                    mid = mem.get("id", "")
                    if mid and mid not in seen:
                        seen.add(mid)
                        results.append(mem)
            return _ok(results, {"backend": "mem0"})
        except Exception as e:
            return _err(f"mem0 list_subscribed failed: {e}", {"backend": "mem0"})

    # ── Scope-level operations ──────────────────────────────

    def delete_all(self, scope: str = "") -> dict:
        """Delete all memories in a scope.

        Note: not part of the standard MemoryAdapter protocol,
        but useful for admin/doctor operations.
        """
        try:
            entity_params = _scope_to_entity_params(scope, self.default_user_id)
            self._mem0.delete_all(**entity_params)
            return _ok({"deleted_all": True, "scope": scope}, {"backend": "mem0"})
        except Exception as e:
            return _err(f"mem0 delete_all failed: {e}", {"backend": "mem0"})

    # ── Lifecycle ───────────────────────────────────────────

    def close(self):
        """Release resources (mem0 SDK has no persistent connection)."""
        try:
            self._mem0.close()
        except Exception:
            pass

    # ── Diagnostics ─────────────────────────────────────────

    def ping(self) -> dict:
        """Lightweight health check — try a trivial search."""
        try:
            raw = self._mem0.search(
                query="ping",
                filters={"user_id": "__health_check__"},
                top_k=1,
                threshold=0.99,
            )
            return _ok({"reachable": True}, {"backend": "mem0"})
        except Exception as e:
            return _err(f"mem0 ping failed: {e}", {"backend": "mem0"})
