"""
project-memory sub-skill — Manage long-term project context.
"""
import sys, os, json as _json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.formatter import format_memory_list


def run_project(config: Config, action: str, name: str = "",
                query: str = "", content: str = "") -> int:
    adapter = get_adapter(config)
    scope = config.user_scope.rstrip("/") + "/projects/"

    if action == "list":
        result = adapter.browse(scope=scope)
        memories = result.get("memories", result.get("data", []))
        print(format_memory_list(memories))

    elif action == "create":
        if not name:
            print("Error: project name required", file=sys.stderr)
            return 1
        from skills.capture.scripts.capture import run_capture
        mem_content = content or f"Project: {name}"
        r = run_capture(config, content=mem_content, memory_type="project",
                        title=name, scope=scope)
        if r.get("error"):
            print(f"Error: {r.get('reason')}", file=sys.stderr)
            return 1
        print(f"Project memory created: [{r.get('id', '?')}] {name}")

    elif action == "recall":
        q = query or name
        if not q:
            print("Error: query or name required", file=sys.stderr)
            return 1
        result = adapter.search(query=q, scope=scope, limit=config.recall_limit)
        memories = result.get("memories", result.get("data", []))
        if memories:
            from lib.formatter import format_recall_block
            print(format_recall_block(memories, header="Project Memory"))
        else:
            print("(no project memories found)")

    elif action == "update":
        if not name:
            print("Error: project name required for update", file=sys.stderr)
            return 1
        # Search for existing project
        result = adapter.search(query=name, scope=scope, limit=1)
        memories = result.get("memories", result.get("data", []))
        if not memories:
            print(f"No project memory found matching: {name}", file=sys.stderr)
            return 1
        mid = memories[0].get("id")
        from skills.merge.scripts.merge import run_merge
        r = run_merge(config, mid, content)
        print(f"Project memory updated: {mid}")

    adapter.close()
    return 0
