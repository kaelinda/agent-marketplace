"""
environment-memory sub-skill — Manage user technical environment memories.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.formatter import format_memory_list


def run_env(config: Config, action: str, name: str = "",
            os_name: str = "", nginx_path: str = "", content: str = "") -> int:
    adapter = get_adapter(config)
    scope = config.user_scope.rstrip("/") + "/environments/"

    if action == "list":
        result = adapter.browse(scope=scope)
        memories = result.get("memories", result.get("data", []))
        print(format_memory_list(memories))

    elif action == "capture":
        parts = []
        if name:
            parts.append(f"Environment: {name}")
        if os_name:
            parts.append(f"OS: {os_name}")
        if nginx_path:
            parts.append(f"Nginx path: {nginx_path}")
        if content:
            parts.append(content)
        if not parts:
            print("Error: at least one of --name, --os, --nginx-path, --content required", file=sys.stderr)
            return 1
        full_content = ". ".join(parts)
        from skills.capture.scripts.capture import run_capture
        r = run_capture(config, content=full_content, memory_type="environment",
                        title=name or full_content[:80], scope=scope)
        if r.get("error"):
            print(f"Error: {r.get('reason')}", file=sys.stderr)
            return 1
        print(f"Environment memory created: [{r.get('id', '?')}]")

    elif action == "update":
        if not content:
            print("Error: --content required for update", file=sys.stderr)
            return 1
        result = adapter.search(query=name or content[:40], scope=scope, limit=1)
        memories = result.get("memories", result.get("data", []))
        if not memories:
            print("No matching environment memory found.", file=sys.stderr)
            return 1
        mid = memories[0].get("id")
        from skills.merge.scripts.merge import run_merge
        run_merge(config, mid, content)
        print(f"Environment memory updated: {mid}")

    adapter.close()
    return 0
