"""
OpenViking Memory Skill Suite — Memory adapter protocol.
Defines the interface that all backend adapters must implement,
along with standardized response contracts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


# ── Response contracts ──────────────────────────────────────


@dataclass
class AdapterResponse:
    """
    Standardized response envelope returned by all adapter methods.

    All adapter methods MUST return an AdapterResponse (or a dict that
    conforms to the same shape). Consumers should check `ok` before
    accessing `data`.

    Fields:
        ok:     Whether the operation succeeded.
        data:   Payload (varies by method — see method docstrings).
        error:  Error description when ok=False.
        meta:   Optional metadata (status code, elapsed_ms, backend, etc.).
    """
    ok: bool = True
    data: Any = None
    error: str = ""
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"ok": self.ok}
        if self.data is not None:
            d["data"] = self.data
        if self.error:
            d["error"] = self.error
        if self.meta:
            d["meta"] = self.meta
        return d

    @classmethod
    def from_dict(cls, raw: dict) -> "AdapterResponse":
        """Build an AdapterResponse from a raw dict (e.g. HTTP JSON body).

        Recognises three shapes for backwards compatibility:
        - new: ``{"ok": False, "error": "..."}`` → preserved as-is
        - legacy HTTP: ``{"error": True, "reason": "..."}`` → translated
        - any other dict → wrapped as ``ok=True, data=raw``
        """
        if raw.get("ok") is False or raw.get("error") is True:
            err_field = raw.get("error")
            err_msg = err_field if isinstance(err_field, str) else None
            err_msg = err_msg or raw.get("reason") or "unknown error"
            meta = {k: v for k, v in raw.items() if k.startswith("_")}
            return cls(ok=False, error=err_msg, meta=meta)
        meta = {k: v for k, v in raw.items() if k.startswith("_")}
        # Strip meta keys from the surfaced data payload
        data = {k: v for k, v in raw.items() if not k.startswith("_")}
        return cls(ok=True, data=data, meta=meta)


# ── Response shape docs (for implementors) ─────────────────
#
# Method          | data type          | Description
# ----------------|--------------------|------------------------------------
# search()        | list[dict]         | List of matching memories, each has
#                 |                    | at least: id, content, type, score
# read()          | dict               | Single memory with id, content, type,
#                 |                    | scope, metadata, created_at, updated_at
# write()         | dict               | Created memory (same shape as read)
# update()        | dict               | Updated memory
# delete()        | dict               | {"id": "...", "deleted": True}
# browse()        | list[dict]         | List of memories in scope
# commit()        | dict               | {"committed": N, "memories": [...]}
# close()         | None               | No return value
#
# Error shape:    | AdapterResponse(ok=False, error="reason string")


# ── Protocol ───────────────────────────────────────────────


@runtime_checkable
class MemoryAdapter(Protocol):
    """
    Protocol for memory backend adapters.
    Any backend (OpenViking, Mem0, Zep, local SQLite, etc.) must implement
    this interface.

    Contract:
    - All methods MUST return AdapterResponse or a dict convertible via
      AdapterResponse.from_dict().
    - On failure, return AdapterResponse(ok=False, error="...").
    - The `scope` parameter uses the backend's native namespace format.
      Use build_scope() to construct it.
    """

    def build_scope(self, tenant_id: str, entity_type: str,
                    entity_id: str) -> str:
        """
        Construct a scope/namespace string for this backend.

        Args:
            tenant_id:   Tenant identifier.
            entity_type: ``user`` | ``agent`` | ``team`` | ``system``.
                         Phase 3 added ``team`` for cross-agent shared
                         memories (multiple agents subscribe to one
                         team scope).
            entity_id:   User / agent / team ID, or system component.

        Returns:
            Backend-native scope string.

        Example (OpenViking):
            build_scope("default", "user", "alice")
            → "viking://tenants/default/users/alice/memories/"
            build_scope("default", "team", "platform")
            → "viking://tenants/default/teams/platform/memories/"
        """
        ...

    def search(self, query: str, scope: str = "", limit: int = 6,
               memory_type: str = "", min_score: float = 0.0,
               extra_scopes: list[str] = ()) -> dict:
        """Search memories by query.

        Phase 3: ``extra_scopes`` lets callers fold in additional scopes
        (e.g. team scopes the current identity is subscribed to) so a
        single adapter call can return memories from "own" + "subscribed"
        without N round-trips. Adapters that can't natively multi-scope
        a single query must iterate and merge client-side.

        Returns AdapterResponse(data=[...]).
        """
        ...

    def read(self, memory_id: str) -> dict:
        """Read a single memory by ID. Returns AdapterResponse(data={...})."""
        ...

    def write(self, memory: dict, scope: str = "") -> dict:
        """Write a new memory. Returns AdapterResponse(data={...})."""
        ...

    def update(self, memory_id: str, patch: dict) -> dict:
        """Update an existing memory. Returns AdapterResponse(data={...})."""
        ...

    def delete(self, memory_id: str) -> dict:
        """Delete a memory by ID. Returns AdapterResponse(data={"id":..., "deleted": True})."""
        ...

    def browse(self, scope: str = "", limit: int = 20, offset: int = 0) -> dict:
        """Browse memories in a scope. Returns AdapterResponse(data=[...])."""
        ...

    def commit(self, memories: list[dict], scope: str = "") -> dict:
        """Batch commit memories. Returns AdapterResponse(data={"committed": N})."""
        ...

    # ── Sharing (Phase 3) ──────────────────────────────────────
    #
    # All three methods MUST return AdapterResponse-shape dicts.
    # Backends that don't natively support sharing (e.g. plain
    # OpenViking REST without ACL) should:
    #   1. Implement client-side fallback if feasible (e.g. mem0 stores
    #      shared_with in metadata and filters via metadata query)
    #   2. Otherwise return ok=False with a clear "backend doesn't
    #      support sharing — see Phase 4 for ACL support" error string.
    # Either way, lib.sharing.SharingManager treats both equivalently.

    def share(self, memory_id: str, target: str,
              permission: str = "read") -> dict:
        """Grant ``target`` access to memory ``memory_id``.

        Args:
            memory_id:  ID of the memory to share.
            target:     Identity string of the recipient — must match
                        ``^(user|agent|team):.+$`` (e.g. ``team:platform``).
            permission: ``"read"`` (default) or ``"write"``.

        Returns:
            AdapterResponse(data={"id": ..., "target": ..., "permission": ...})
            on success, or ok=False with explanatory error on failure /
            unsupported backend.
        """
        ...

    def unshare(self, memory_id: str, target: str) -> dict:
        """Revoke ``target``'s access to memory ``memory_id``.

        Returns AdapterResponse(data={"id": ..., "target": ...}) on
        success. Unsharing a target that wasn't shared is a no-op
        success (idempotent).
        """
        ...

    def list_subscribed(self, identity: str) -> dict:
        """List memories that have been shared TO ``identity``.

        Args:
            identity: Identity string ``"<entity_type>:<id>"``.

        Returns:
            AdapterResponse(data=[memory dicts]) — each memory has its
            full metadata. Backends should NOT filter by visibility
            here; SharingManager.can_access does the final ACL check
            so the same data path can support both audit ("show me what
            I have access to") and recall flows.
        """
        ...

    def close(self):
        """Release resources."""
        ...
