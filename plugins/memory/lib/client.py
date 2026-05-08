"""
OpenViking Memory Skill Suite — HTTP client for OpenViking Server.
Provides a thin wrapper around the OpenViking REST API.
"""
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Optional


class OVClient:
    """HTTP client for OpenViking Server."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self, extra: dict | None = None) -> dict:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        if extra:
            h.update(extra)
        return h

    def _request(self, method: str, path: str, body: dict | None = None,
                 params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            if qs:
                url = f"{url}?{qs}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                raw = resp.read().decode()
                result = json.loads(raw) if raw.strip() else {}
                result["_status"] = resp.status
                result["_elapsed_ms"] = elapsed_ms
                return result
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            return {
                "ok": False,
                "error": f"HTTP {e.code} {e.reason}".strip(),
                "_status": e.code,
                "_body": body_text,
                "_elapsed_ms": int((time.monotonic() - start) * 1000),
            }
        except urllib.error.URLError as e:
            return {"ok": False, "error": f"URL error: {e.reason}", "_status": 0, "_elapsed_ms": 0}
        except Exception as e:
            return {"ok": False, "error": f"client error: {e}", "_status": 0, "_elapsed_ms": 0}

    # ── Health / Ping ────────────────────────────────────────────

    def ping(self) -> dict:
        """Check if OpenViking is reachable."""
        return self._request("GET", "/health")

    def info(self) -> dict:
        """Get server info."""
        return self._request("GET", "/")

    # ── Memory CRUD ──────────────────────────────────────────────

    def search(self, query: str, scope: str = "", limit: int = 6,
               memory_type: str = "", min_score: float = 0.0) -> dict:
        """Search memories by query."""
        body = {"query": query, "limit": limit}
        if scope:
            body["scope"] = scope
        if memory_type:
            body["type"] = memory_type
        if min_score > 0:
            body["min_score"] = min_score
        return self._request("POST", "/api/v1/memories/search", body)

    def read(self, memory_id: str) -> dict:
        """Read a single memory by ID."""
        return self._request("GET", f"/api/v1/memories/{memory_id}")

    def write(self, memory: dict, scope: str = "") -> dict:
        """Write a new memory."""
        mem_copy = dict(memory)
        if scope:
            mem_copy["scope"] = scope
        return self._request("POST", "/api/v1/memories", mem_copy)

    def update(self, memory_id: str, patch: dict) -> dict:
        """Update an existing memory."""
        return self._request("PATCH", f"/api/v1/memories/{memory_id}", patch)

    def delete(self, memory_id: str) -> dict:
        """Delete a memory by ID."""
        return self._request("DELETE", f"/api/v1/memories/{memory_id}")

    def browse(self, scope: str = "", limit: int = 20, offset: int = 0) -> dict:
        """Browse memories in a scope."""
        params = {"limit": limit, "offset": offset}
        if scope:
            params["scope"] = scope
        return self._request("GET", "/api/v1/memories", params=params)

    def commit(self, memories: list[dict], scope: str = "") -> dict:
        """Batch commit memories."""
        body = {"memories": memories}
        if scope:
            body["scope"] = scope
        return self._request("POST", "/api/v1/memories/commit", body)

    # ── Lifecycle ────────────────────────────────────────────────

    def close(self):
        """No-op for HTTP (no persistent connection)."""
        pass
