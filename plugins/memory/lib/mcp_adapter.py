"""
memory plugin — MCP adapter.

Bridges adapter operations to MCP tool calls via the ``mcporter`` CLI
(when running standalone). All results are normalised to
``AdapterResponse`` shape so callers can treat HTTP / MCP / mem0
backends uniformly.

Subprocess env handling
-----------------------
The mcporter child process inherits a deliberately *narrow* env that
only contains entries with the ``MCP_`` prefix plus the few platform
variables required to find the binary (``PATH``, ``HOME``, ``USER``,
``LANG``). This prevents the OpenViking / mem0 API keys from leaking
into mcporter's stderr (the failure path returns child stderr to the
caller), which would otherwise show up in agent logs.
"""
import json
import os
import subprocess
from typing import Any, Optional

from .adapter_protocol import AdapterResponse


_ENV_ALLOWLIST_PREFIXES = ("MCP_",)
_ENV_ALLOWLIST_NAMES = frozenset({
    "PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE",
    "TMPDIR", "TZ", "PYTHONPATH",
})


def _safe_env() -> dict:
    """Return an env dict scrubbed of secrets (keep only MCP_*+platform vars)."""
    parent = os.environ
    safe = {k: v for k, v in parent.items() if k in _ENV_ALLOWLIST_NAMES}
    for k, v in parent.items():
        if any(k.startswith(p) for p in _ENV_ALLOWLIST_PREFIXES):
            safe[k] = v
    return safe


class MCPAdapter:
    """Adapter that calls OpenViking via MCP protocol tools."""

    def __init__(self, server_name: str = "openviking", tool_names: dict | None = None,
                 scope_template: str = ""):
        self.server_name = server_name
        self.tool_names = tool_names or {
            "search": "memsearch",
            "read": "memread",
            "write": "memwrite",
            "update": "memupdate",
            "delete": "memforget",
            "commit": "memcommit",
            "browse": "membrowse",
        }
        # Scope template with {tenant}, {type}, {entity} placeholders.
        # Defaults to OpenViking format if empty.
        self._scope_template = scope_template or (
            "viking://tenants/{tenant}/{type}s/{entity}/memories/"
        )

    def _tool(self, action: str) -> str:
        return self.tool_names.get(action, action)

    def build_scope(self, tenant_id: str, entity_type: str,
                    entity_id: str) -> str:
        """Construct a scope string using the configured template."""
        if entity_type == "system":
            tmpl = self._scope_template.replace("/{type}s/{entity}/memories/", "/system/{entity}/")
            return tmpl.format(tenant=tenant_id, type=entity_type, entity=entity_id)
        return self._scope_template.format(
            tenant=tenant_id, type=entity_type, entity=entity_id
        )

    def search(self, query: str, scope: str = "", limit: int = 6,
               memory_type: str = "", min_score: float = 0.0) -> dict:
        args = {"query": query, "limit": limit}
        if scope:
            args["scope"] = scope
        if memory_type:
            args["type"] = memory_type
        if min_score > 0:
            args["min_score"] = min_score
        return self._wrap(self._call_tool(self._tool("search"), args))

    def read(self, memory_id: str) -> dict:
        return self._wrap(self._call_tool(self._tool("read"), {"id": memory_id}))

    def write(self, memory: dict, scope: str = "") -> dict:
        mem_copy = dict(memory)
        if scope:
            mem_copy["scope"] = scope
        return self._wrap(self._call_tool(self._tool("write"), mem_copy))

    def update(self, memory_id: str, patch: dict) -> dict:
        args = {"id": memory_id, **patch}
        return self._wrap(self._call_tool(self._tool("update"), args))

    def delete(self, memory_id: str) -> dict:
        return self._wrap(self._call_tool(self._tool("delete"), {"id": memory_id}))

    def browse(self, scope: str = "", limit: int = 20, offset: int = 0) -> dict:
        args = {"limit": limit, "offset": offset}
        if scope:
            args["scope"] = scope
        return self._wrap(self._call_tool(self._tool("browse"), args))

    def commit(self, memories: list[dict], scope: str = "") -> dict:
        args = {"memories": memories}
        if scope:
            args["scope"] = scope
        return self._wrap(self._call_tool(self._tool("commit"), args))

    @staticmethod
    def _wrap(raw: Any) -> dict:
        """Normalise an mcporter response into AdapterResponse dict shape."""
        if not isinstance(raw, dict):
            return AdapterResponse(
                ok=False, error=f"Non-dict response: {type(raw).__name__}"
            ).to_dict()
        return AdapterResponse.from_dict(raw).to_dict()

    def _call_tool(self, tool_name: str, args: dict) -> dict:
        """
        Call an MCP tool. In the hermes-agent environment, this uses
        the native MCP client. For standalone CLI usage, this shells
        out to ``mcporter call`` with a scrubbed env (see _safe_env).

        Returns a raw dict (success or ``{"ok": False, "error": ...}``).
        Final normalisation happens in :py:meth:`_wrap` before the
        result reaches the caller.
        """
        mcporter = os.environ.get("MCPORTER_BIN", "mcporter")
        try:
            cmd = [
                mcporter, "call",
                "--server", self.server_name,
                "--tool", tool_name,
                "--args", json.dumps(args),
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                env=_safe_env(),
            )
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    return {"ok": False, "error": f"mcporter returned non-JSON: {e}"}
            return {"ok": False, "error": result.stderr.strip() or "mcporter failed"}
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"MCP tool '{tool_name}' timed out (30s)"}
        except Exception as e:
            return {"ok": False, "error": f"MCP call failed: {e}"}

        # Fallback: mcporter not on PATH (and we are not running inside an agent context)
        return {
            "ok": False,
            "error": (
                f"MCP tool '{tool_name}' not available — install mcporter "
                "or run inside an agent with MCP configured, or use the HTTP adapter."
            ),
        }

    def ping(self) -> dict:
        """Check if the MCP server is reachable via a minimal search call."""
        return self._wrap(
            self._call_tool(self._tool("search"), {"query": "ping", "limit": 1})
        )

    def close(self):
        pass
