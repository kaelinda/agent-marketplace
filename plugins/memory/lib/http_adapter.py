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
               memory_type: str = "", min_score: float = 0.0) -> dict:
        return _wrap(self.client.search(query, scope, limit, memory_type, min_score))

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

    def ping(self) -> dict:
        """Pass-through health check used by doctor / contract tests."""
        return _wrap(self.client.ping())

    def close(self):
        self.client.close()
