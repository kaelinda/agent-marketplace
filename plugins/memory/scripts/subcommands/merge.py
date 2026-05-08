"""
merge sub-skill — Update and merge existing memories.
"""
import sys, os, datetime
from datetime import timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.hooks import HookEvent, get_default_registry, reset_default_registry


def run_merge(config: Config, memory_id: str, new_content: str) -> dict:
    """Merge new content into an existing memory."""
    adapter = get_adapter(config)

    # Read existing
    existing = adapter.read(memory_id)
    if existing.get("error"):
        adapter.close()
        return existing

    # ── Hook: BEFORE_MERGE ──
    reset_default_registry()
    registry = get_default_registry(config.data)
    ctx = registry.trigger(HookEvent.BEFORE_MERGE, {
        "memory_id": memory_id,
        "old_content": existing.get("content", ""),
        "new_content": new_content,
        "config": config,
        "adapter": adapter,
    })
    if ctx.get("blocked"):
        adapter.close()
        return {"error": True, "reason": ctx.get("reason", "Merge blocked by hook.")}
    new_content = ctx.get("new_content", new_content)

    # Merge: append new content with separator
    old_content = existing.get("content", "")
    merged = f"{old_content}\n\n[Updated] {new_content}"

    now = datetime.datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    patch = {
        "content": merged,
        "summary": new_content[:200] if len(new_content) > 200 else new_content,
        "updated_at": now,
    }

    result = adapter.update(memory_id, patch)

    # ── Hook: AFTER_MERGE ──
    registry.trigger(HookEvent.AFTER_MERGE, {
        "memory_id": memory_id,
        "result": result,
        "config": config,
    })

    adapter.close()
    return result


if __name__ == "__main__":
    from lib.config import load_config
    import json
    config = load_config()
    if len(sys.argv) < 3:
        print("Usage: merge.py <memory_id> <new_content>")
        sys.exit(1)
    result = run_merge(config, sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2, ensure_ascii=False))
