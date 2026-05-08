"""
agent-reflection sub-skill — Manage Agent reusable experience memories.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.formatter import format_memory_list, format_recall_block


def run_reflection(config: Config, action: str, title: str = "",
                   content: str = "", query: str = "") -> int:
    adapter = get_adapter(config)
    scope = config.agent_scope.rstrip("/") + "/reflections/"

    if action == "list":
        result = adapter.browse(scope=scope)
        memories = result.get("memories", result.get("data", []))
        print(format_memory_list(memories))

    elif action == "add":
        if not content:
            print("Error: --content required", file=sys.stderr)
            return 1
        from skills.capture.scripts.capture import run_capture
        r = run_capture(config, content=content, memory_type="agent_reflection",
                        title=title or content[:80], scope=scope)
        if r.get("error"):
            print(f"Error: {r.get('reason')}", file=sys.stderr)
            return 1
        print(f"Reflection added: [{r.get('id', '?')}]")

    elif action == "recall":
        q = query or title
        if not q:
            print("Error: --query required", file=sys.stderr)
            return 1
        result = adapter.search(query=q, scope=scope, limit=config.recall_limit)
        memories = result.get("memories", result.get("data", []))
        if memories:
            print(format_recall_block(memories, header="Agent Reflections"))
        else:
            print("(no reflections found)")

    adapter.close()
    return 0
