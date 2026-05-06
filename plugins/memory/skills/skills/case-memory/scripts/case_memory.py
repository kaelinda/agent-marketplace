"""
case-memory sub-skill — Manage troubleshooting case memories.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.formatter import format_memory_list, format_recall_block


def run_case(config: Config, action: str, title: str = "",
             problem: str = "", solution: str = "", query: str = "") -> int:
    adapter = get_adapter(config)
    scope = config.user_scope.rstrip("/") + "/cases/"

    if action == "list":
        result = adapter.browse(scope=scope)
        memories = result.get("memories", result.get("data", []))
        print(format_memory_list(memories))

    elif action == "create":
        if not title or not problem:
            print("Error: --title and --problem required", file=sys.stderr)
            return 1
        content = f"Problem: {problem}"
        if solution:
            content += f"\nSolution: {solution}"
        from skills.capture.scripts.capture import run_capture
        r = run_capture(config, content=content, memory_type="case",
                        title=title, scope=scope)
        if r.get("error"):
            print(f"Error: {r.get('reason')}", file=sys.stderr)
            return 1
        print(f"Case memory created: [{r.get('id', '?')}] {title}")

    elif action == "recall":
        q = query or problem or title
        if not q:
            print("Error: --query, --problem, or --title required", file=sys.stderr)
            return 1
        result = adapter.search(query=q, scope=scope, limit=config.recall_limit)
        memories = result.get("memories", result.get("data", []))
        if memories:
            print(format_recall_block(memories, header="Case Memory"))
        else:
            print("(no case memories found)")

    adapter.close()
    return 0
