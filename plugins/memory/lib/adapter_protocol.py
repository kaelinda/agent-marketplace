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
            entity_type: "user" | "agent" | "system".
            entity_id:   User or agent ID.

        Returns:
            Backend-native scope string.

        Example (OpenViking):
            build_scope("default", "user", "alice")
            → "viking://tenants/default/users/alice/memories/"
        """
        ...

    def search(self, query: str, scope: str = "", limit: int = 6,
               memory_type: str = "", min_score: float = 0.0) -> dict:
        """Search memories by query. Returns AdapterResponse(data=[...])."""
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

    def close(self):
        """Release resources."""
        ...
