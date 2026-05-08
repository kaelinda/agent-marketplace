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
               memory_type: str = "", min_score: float = 0.0) -> dict:
        self.calls.append(("search", {"query": query, "scope": scope}))
        if self._maybe_fail("search"):
            return self._err("forced search failure")
        bucket = self._store.get(scope, {})
        hits = [
            dict(m, score=1.0) for m in bucket.values()
            if (not memory_type or m.get("type") == memory_type)
            and (not query or query.lower() in (m.get("content") or "").lower())
        ]
        hits = hits[:limit]
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
