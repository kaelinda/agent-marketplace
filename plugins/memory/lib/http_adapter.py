"""
OpenViking Memory Skill Suite — HTTP adapter.
Wraps the OVClient into the same interface as MCPAdapter for unified usage.
"""
from .client import OVClient


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
        return self.client.search(query, scope, limit, memory_type, min_score)

    def read(self, memory_id: str) -> dict:
        return self.client.read(memory_id)

    def write(self, memory: dict, scope: str = "") -> dict:
        return self.client.write(memory, scope)

    def update(self, memory_id: str, patch: dict) -> dict:
        return self.client.update(memory_id, patch)

    def delete(self, memory_id: str) -> dict:
        return self.client.delete(memory_id)

    def browse(self, scope: str = "", limit: int = 20, offset: int = 0) -> dict:
        return self.client.browse(scope, limit, offset)

    def commit(self, memories: list[dict], scope: str = "") -> dict:
        return self.client.commit(memories, scope)

    def close(self):
        self.client.close()
