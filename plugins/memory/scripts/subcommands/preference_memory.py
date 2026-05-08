"""
preference-memory sub-skill — Manage user preference memories.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.formatter import format_memory_list, format_recall_block


def run_pref(config: Config, action: str, key: str = "",
             value: str = "", content: str = "") -> int:
    adapter = get_adapter(config)
    scope = config.user_scope.rstrip("/") + "/preferences/"

    if action == "list":
        result = adapter.browse(scope=scope)
        memories = result.get("memories", result.get("data", []))
        print(format_memory_list(memories))

    elif action == "set":
        if not key or not value:
            print("Error: --key and --value required", file=sys.stderr)
            return 1
        pref_content = content or f"User preference: {key} = {value}"
        # Check for existing preference with same key
        result = adapter.search(query=key, scope=scope, limit=1)
        memories = result.get("memories", result.get("data", []))
        if memories:
            # Update existing
            mid = memories[0].get("id")
            from skills.merge.scripts.merge import run_merge
            run_merge(config, mid, f"{key} = {value}")
            print(f"Preference updated: {mid}")
        else:
            # Create new
            from skills.capture.scripts.capture import run_capture
            r = run_capture(config, content=pref_content, memory_type="preference",
                            title=f"Preference: {key}", scope=scope)
            if r.get("error"):
                print(f"Error: {r.get('reason')}", file=sys.stderr)
                return 1
            print(f"Preference created: [{r.get('id', '?')}] {key}")

    elif action == "get":
        q = key or value
        if not q:
            print("Error: --key required", file=sys.stderr)
            return 1
        result = adapter.search(query=q, scope=scope, limit=3)
        memories = result.get("memories", result.get("data", []))
        if memories:
            print(format_recall_block(memories, header="Preferences"))
        else:
            print("(no matching preferences)")

    elif action == "delete":
        q = key
        if not q:
            print("Error: --key required", file=sys.stderr)
            return 1
        result = adapter.search(query=q, scope=scope, limit=3)
        memories = result.get("memories", result.get("data", []))
        for m in memories:
            mid = m.get("id")
            if mid:
                adapter.update(mid, {"status": "deleted"})
                print(f"Deleted: {mid}")
        if not memories:
            print("(no matching preferences)")

    adapter.close()
    return 0
