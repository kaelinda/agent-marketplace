"""
FakeAdapter — in-memory ``MemoryAdapter`` implementation for tests.

Stores memories in a dict keyed by id, scoped per-namespace. Returns
properly-shaped ``AdapterResponse`` dicts so it can be substituted for
HTTPAdapter / MCPAdapter / Mem0Adapter without any caller change.

This adapter is the reference implementation that the contract test
parametrises over alongside HTTPAdapter / MCPAdapter / Mem0Adapter.
If FakeAdapter passes the contract, the contract is correctly written;
if a real adapter doesn't, *that* adapter has a protocol violation.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

from lib.adapter_protocol import AdapterResponse


class FakeAdapter:
    """A trivially correct in-memory ``MemoryAdapter`` for tests."""

    def __init__(self, *args, **kwargs):
        # By scope -> {id: memory}
        self._store: dict[str, dict[str, dict]] = {}
        # Optional knobs the contract suite uses to inject failures
        self.fail_next_call: str | None = None
        self.calls: list[tuple[str, dict]] = []

    # ── Protocol methods ────────────────────────────────────

    def build_scope(self, tenant_id: str, entity_type: str,
                    entity_id: str) -> str:
        if entity_type == "system":
            return f"viking://tenants/{tenant_id}/system/{entity_id}/"
        return f"viking://tenants/{tenant_id}/{entity_type}s/{entity_id}/memories/"

    def search(self, query: str, scope: str = "", limit: int = 6,
               memory_type: str = "", min_score: float = 0.0,
               extra_scopes: list[str] = ()) -> dict:
        self.calls.append((
            "search",
            {"query": query, "scope": scope, "extra_scopes": list(extra_scopes)},
        ))
        if self._maybe_fail("search"):
            return self._err("forced search failure")
        scopes_to_search = [scope] if scope else []
        scopes_to_search.extend(extra_scopes or ())
        seen_ids: set[str] = set()
        hits: list[dict] = []
        for s in scopes_to_search:
            for m in self._store.get(s, {}).values():
                if memory_type and m.get("type") != memory_type:
                    continue
                if query and query.lower() not in (m.get("content") or "").lower():
                    continue
                mid = m.get("id", "")
                if mid in seen_ids:
                    continue
                seen_ids.add(mid)
                hits.append(dict(m, score=1.0))
                if len(hits) >= limit:
                    break
            if len(hits) >= limit:
                break
        return self._ok(hits)

    def read(self, memory_id: str) -> dict:
        self.calls.append(("read", {"id": memory_id}))
        if self._maybe_fail("read"):
            return self._err("forced read failure")
        for bucket in self._store.values():
            if memory_id in bucket:
                return self._ok(dict(bucket[memory_id]))
        return self._err(f"memory {memory_id} not found")

    def write(self, memory: dict, scope: str = "") -> dict:
        self.calls.append(("write", {"scope": scope}))
        if self._maybe_fail("write"):
            return self._err("forced write failure")
        if not isinstance(memory, dict):
            return self._err("memory must be a dict")
        if not memory.get("content"):
            return self._err("content is required")
        mem = dict(memory)
        if not mem.get("id"):
            mem["id"] = f"fake_{uuid.uuid4().hex}"
        mem["scope"] = scope
        mem.setdefault("created_at", _now_iso())
        mem["updated_at"] = _now_iso()
        self._store.setdefault(scope, {})[mem["id"]] = mem
        return self._ok(dict(mem))

    def update(self, memory_id: str, patch: dict) -> dict:
        self.calls.append(("update", {"id": memory_id}))
        if self._maybe_fail("update"):
            return self._err("forced update failure")
        for bucket in self._store.values():
            if memory_id in bucket:
                bucket[memory_id].update(patch)
                bucket[memory_id]["updated_at"] = _now_iso()
                return self._ok(dict(bucket[memory_id]))
        return self._err(f"memory {memory_id} not found")

    def delete(self, memory_id: str) -> dict:
        self.calls.append(("delete", {"id": memory_id}))
        if self._maybe_fail("delete"):
            return self._err("forced delete failure")
        for bucket in self._store.values():
            if memory_id in bucket:
                del bucket[memory_id]
                return self._ok({"id": memory_id, "deleted": True})
        return self._err(f"memory {memory_id} not found")

    def browse(self, scope: str = "", limit: int = 20, offset: int = 0) -> dict:
        self.calls.append(("browse", {"scope": scope}))
        if self._maybe_fail("browse"):
            return self._err("forced browse failure")
        bucket = self._store.get(scope, {})
        items = list(bucket.values())[offset : offset + limit]
        return self._ok([dict(m) for m in items])

    def commit(self, memories: list[dict], scope: str = "") -> dict:
        self.calls.append(("commit", {"scope": scope, "n": len(memories)}))
        committed = []
        for mem in memories:
            r = self.write(mem, scope=scope)
            if r.get("ok"):
                committed.append(r["data"])
        return self._ok({"committed": len(committed), "memories": committed})

    # ── Sharing (Phase 3) ──────────────────────────────────────

    def share(self, memory_id: str, target: str,
              permission: str = "read") -> dict:
        self.calls.append(("share", {"id": memory_id, "target": target,
                                       "permission": permission}))
        if self._maybe_fail("share"):
            return self._err("forced share failure")
        if permission not in ("read", "write"):
            return self._err(f"invalid permission {permission!r}; expected read|write")
        if not _is_identity_string(target):
            return self._err(
                f"invalid target {target!r}; must match '<entity_type>:<id>' "
                f"with entity_type in user|agent|team"
            )
        for bucket in self._store.values():
            if memory_id in bucket:
                mem = bucket[memory_id]
                shared_with = list(mem.get("shared_with") or [])
                if target not in shared_with:
                    shared_with.append(target)
                mem["shared_with"] = shared_with
                perms = dict(mem.get("shared_perms") or {})
                perms[target] = permission
                mem["shared_perms"] = perms
                mem["updated_at"] = _now_iso()
                return self._ok({"id": memory_id, "target": target,
                                   "permission": permission})
        return self._err(f"memory {memory_id} not found")

    def unshare(self, memory_id: str, target: str) -> dict:
        self.calls.append(("unshare", {"id": memory_id, "target": target}))
        if self._maybe_fail("unshare"):
            return self._err("forced unshare failure")
        for bucket in self._store.values():
            if memory_id in bucket:
                mem = bucket[memory_id]
                shared_with = [t for t in (mem.get("shared_with") or []) if t != target]
                mem["shared_with"] = shared_with
                perms = {k: v for k, v in (mem.get("shared_perms") or {}).items()
                         if k != target}
                mem["shared_perms"] = perms
                mem["updated_at"] = _now_iso()
                # Idempotent — unsharing a target that wasn't shared is fine.
                return self._ok({"id": memory_id, "target": target})
        return self._err(f"memory {memory_id} not found")

    def list_subscribed(self, identity: str) -> dict:
        self.calls.append(("list_subscribed", {"identity": identity}))
        if self._maybe_fail("list_subscribed"):
            return self._err("forced list_subscribed failure")
        if not _is_identity_string(identity):
            return self._err(
                f"invalid identity {identity!r}; must match '<entity_type>:<id>'"
            )
        results: list[dict] = []
        seen: set[str] = set()
        # 1. team scope memberships: if identity is "team:X", every memory
        #    living in viking://.../teams/X/... is subscribed.
        if identity.startswith("team:"):
            team_id = identity.split(":", 1)[1]
            team_marker = f"/teams/{team_id}/"
            for scope, bucket in self._store.items():
                if team_marker in scope:
                    for m in bucket.values():
                        mid = m.get("id", "")
                        if mid and mid not in seen:
                            seen.add(mid)
                            results.append(dict(m))
        # 2. explicit shared_with grants — across all scopes
        for bucket in self._store.values():
            for m in bucket.values():
                shared_with = m.get("shared_with") or []
                if identity in shared_with:
                    mid = m.get("id", "")
                    if mid and mid not in seen:
                        seen.add(mid)
                        results.append(dict(m))
        return self._ok(results)

    def ping(self) -> dict:
        self.calls.append(("ping", {}))
        if self._maybe_fail("ping"):
            return self._err("forced ping failure")
        return self._ok({"reachable": True})

    def close(self):
        self._store.clear()
        self.calls.clear()

    # ── Helpers ─────────────────────────────────────────────

    def _ok(self, data: Any = None) -> dict:
        return AdapterResponse(ok=True, data=data, meta={"backend": "fake"}).to_dict()

    def _err(self, msg: str) -> dict:
        return AdapterResponse(ok=False, error=msg, meta={"backend": "fake"}).to_dict()

    def _maybe_fail(self, op: str) -> bool:
        if self.fail_next_call == op:
            self.fail_next_call = None
            return True
        return False


def _now_iso() -> str:
    # Lightweight UTC ISO timestamp, no tzdata dependency.
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _is_identity_string(s: str) -> bool:
    """Validate ``<entity_type>:<id>`` where entity_type is user|agent|team."""
    if not isinstance(s, str) or ":" not in s:
        return False
    head, _, tail = s.partition(":")
    return head in ("user", "agent", "team") and bool(tail)
