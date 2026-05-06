"""
OpenViking Memory Skill Suite — MCP adapter.
Bridges Skill commands to MCP tool calls via hermes native MCP or subprocess.
"""
import json
import os
import subprocess
from typing import Any, Optional


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
        return self._call_tool(self._tool("search"), args)

    def read(self, memory_id: str) -> dict:
        return self._call_tool(self._tool("read"), {"id": memory_id})

    def write(self, memory: dict, scope: str = "") -> dict:
        mem_copy = dict(memory)
        if scope:
            mem_copy["scope"] = scope
        return self._call_tool(self._tool("write"), mem_copy)

    def update(self, memory_id: str, patch: dict) -> dict:
        args = {"id": memory_id, **patch}
        return self._call_tool(self._tool("update"), args)

    def delete(self, memory_id: str) -> dict:
        return self._call_tool(self._tool("delete"), {"id": memory_id})

    def browse(self, scope: str = "", limit: int = 20, offset: int = 0) -> dict:
        args = {"limit": limit, "offset": offset}
        if scope:
            args["scope"] = scope
        return self._call_tool(self._tool("browse"), args)

    def commit(self, memories: list[dict], scope: str = "") -> dict:
        args = {"memories": memories}
        if scope:
            args["scope"] = scope
        return self._call_tool(self._tool("commit"), args)

    def _call_tool(self, tool_name: str, args: dict) -> dict:
        """
        Call an MCP tool. In the hermes-agent environment, this uses
        the native MCP client. For standalone CLI usage, this shells out
        to `mcporter call` or returns a stub.
        """
        # Try mcporter CLI first (standalone)
        mcporter = os.environ.get("MCPORTER_BIN", "mcporter")
        try:
            cmd = [
                mcporter, "call",
                "--server", self.server_name,
                "--tool", tool_name,
                "--args", json.dumps(args),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {"error": True, "reason": result.stderr.strip() or "mcporter failed"}
        except FileNotFoundError:
            pass
        except Exception as e:
            return {"error": True, "reason": str(e)}

        # Fallback: not available outside agent context
        return {
            "error": True,
            "reason": f"MCP tool '{tool_name}' not available. "
                      "Run inside an agent with MCP configured, or use HTTP adapter.",
        }

    def ping(self) -> dict:
        """Check if the MCP server is reachable by attempting a lightweight tool call."""
        return self._call_tool(self._tool("search"), {"query": "ping", "limit": 1})

    def close(self):
        pass
