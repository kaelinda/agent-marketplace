"""
memory plugin — HTTP adapter.

Thin wrapper that exposes ``OVClient`` through the ``MemoryAdapter`` protocol
and normalises every response into ``AdapterResponse.to_dict()`` shape.
"""
from .adapter_protocol import AdapterResponse
from .client import OVClient


def _wrap(raw: dict) -> dict:
    """Normalise a raw OVClient response into AdapterResponse dict."""
    if not isinstance(raw, dict):
        return AdapterResponse(
            ok=False, error=f"Non-dict response: {type(raw).__name__}"
        ).to_dict()
    return AdapterResponse.from_dict(raw).to_dict()


class HTTPAdapter:
    """Adapter that calls OpenViking directly via HTTP REST API."""

    def __init__(self, base_url: str, api_key: str | None = None, timeout: int = 10):
        self.client = OVClient(base_url, api_key, timeout)

    def build_scope(self, tenant_id: str, entity_type: str,
                    entity_id: str) -> str:
        """Construct an OpenViking scope URI."""
        if entity_type == "system":
            return f"viking://tenants/{tenant_id}/system/{entity_id}/"
        return f"viking://tenants/{tenant_id}/{entity_type}s/{entity_id}/memories/"

    def search(self, query: str, scope: str = "", limit: int = 6,
               memory_type: str = "", min_score: float = 0.0,
               extra_scopes: list[str] = ()) -> dict:
        # OpenViking REST does not (yet) support multi-scope search in a
        # single request; iterate client-side and merge by id.
        primary = _wrap(self.client.search(query, scope, limit, memory_type, min_score))
        if not extra_scopes:
            return primary
        if not primary.get("ok"):
            return primary
        seen_ids: set[str] = set()
        merged: list[dict] = []
        primary_data = primary.get("data") or []
        if isinstance(primary_data, dict):
            primary_data = primary_data.get("memories") or primary_data.get("results") or []
        for m in primary_data:
            mid = m.get("id", "") if isinstance(m, dict) else ""
            if mid and mid not in seen_ids:
                seen_ids.add(mid)
                merged.append(m)
        for s in extra_scopes:
            extra = _wrap(self.client.search(query, s, limit, memory_type, min_score))
            if not extra.get("ok"):
                continue
            extra_data = extra.get("data") or []
            if isinstance(extra_data, dict):
                extra_data = extra_data.get("memories") or extra_data.get("results") or []
            for m in extra_data:
                mid = m.get("id", "") if isinstance(m, dict) else ""
                if mid and mid not in seen_ids:
                    seen_ids.add(mid)
                    merged.append(m)
                    if len(merged) >= limit:
                        break
            if len(merged) >= limit:
                break
        return AdapterResponse(ok=True, data=merged[:limit], meta={"backend": "http"}).to_dict()

    def read(self, memory_id: str) -> dict:
        return _wrap(self.client.read(memory_id))

    def write(self, memory: dict, scope: str = "") -> dict:
        return _wrap(self.client.write(memory, scope))

    def update(self, memory_id: str, patch: dict) -> dict:
        return _wrap(self.client.update(memory_id, patch))

    def delete(self, memory_id: str) -> dict:
        return _wrap(self.client.delete(memory_id))

    def browse(self, scope: str = "", limit: int = 20, offset: int = 0) -> dict:
        return _wrap(self.client.browse(scope, limit, offset))

    def commit(self, memories: list[dict], scope: str = "") -> dict:
        return _wrap(self.client.commit(memories, scope))

    # ── Sharing (Phase 3) ──────────────────────────────────────
    # OpenViking's REST API doesn't (yet) expose ACL endpoints, so the
    # HTTP adapter falls back to client-side update of the memory's
    # shared_with / shared_perms metadata. This works because the
    # backend stores arbitrary metadata fields. SharingManager treats
    # the result identically to a server-side ACL grant.

    def share(self, memory_id: str, target: str,
              permission: str = "read") -> dict:
        if permission not in ("read", "write"):
            return AdapterResponse(
                ok=False, error=f"invalid permission {permission!r}"
            ).to_dict()
        # Read-modify-write the memory's ACL fields.
        read = _wrap(self.client.read(memory_id))
        if not read.get("ok"):
            return read
        mem = read.get("data") or {}
        if not isinstance(mem, dict):
            return AdapterResponse(
                ok=False, error="unexpected non-dict response from read()"
            ).to_dict()
        shared_with = list(mem.get("shared_with") or [])
        if target not in shared_with:
            shared_with.append(target)
        perms = dict(mem.get("shared_perms") or {})
        perms[target] = permission
        patch = {"shared_with": shared_with, "shared_perms": perms}
        return _wrap(self.client.update(memory_id, patch))

    def unshare(self, memory_id: str, target: str) -> dict:
        read = _wrap(self.client.read(memory_id))
        if not read.get("ok"):
            return read
        mem = read.get("data") or {}
        if not isinstance(mem, dict):
            return AdapterResponse(
                ok=False, error="unexpected non-dict response from read()"
            ).to_dict()
        shared_with = [t for t in (mem.get("shared_with") or []) if t != target]
        perms = {k: v for k, v in (mem.get("shared_perms") or {}).items()
                 if k != target}
        patch = {"shared_with": shared_with, "shared_perms": perms}
        return _wrap(self.client.update(memory_id, patch))

    def list_subscribed(self, identity: str) -> dict:
        # OpenViking REST has no subscription index; we'd have to scan.
        # Return ok=False until backend support lands (Phase 4).
        return AdapterResponse(
            ok=False,
            error=(
                "OpenViking HTTP backend does not expose a subscription index; "
                "use mem0 backend or wait for Phase 4 ACL endpoints."
            ),
        ).to_dict()

    def ping(self) -> dict:
        """Pass-through health check used by doctor / contract tests."""
        return _wrap(self.client.ping())

    def close(self):
        self.client.close()
