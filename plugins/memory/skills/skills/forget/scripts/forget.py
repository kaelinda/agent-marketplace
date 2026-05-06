"""
forget sub-skill — Delete, obsolete, or hide memories.
"""
import sys, os, datetime
from datetime import timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.hooks import HookEvent, get_default_registry, reset_default_registry


def run_forget(config: Config, memory_id: str = "", query: str = "",
               scope: str = "", mode: str = "soft") -> dict:
    """Forget memories by ID, query, or scope."""
    adapter = get_adapter(config)

    ids = []

    if memory_id:
        ids = [memory_id]
    elif query:
        result = adapter.search(query=query, scope=scope or config.user_scope, limit=10)
        memories = result.get("memories", result.get("data", []))
        ids = [m.get("id") for m in memories if m.get("id")]
    elif scope:
        result = adapter.browse(scope=scope, limit=50)
        memories = result.get("memories", result.get("data", []))
        ids = [m.get("id") for m in memories if m.get("id")]

    if not ids:
        adapter.close()
        return {"count": 0, "error": True, "reason": "No matching memories found."}

    # ── Hook: BEFORE_FORGET ──
    reset_default_registry()
    registry = get_default_registry(config.data)
    ctx = registry.trigger(HookEvent.BEFORE_FORGET, {
        "ids": ids,
        "mode": mode,
        "query": query,
        "scope": scope,
        "config": config,
        "adapter": adapter,
    })
    if ctx.get("blocked"):
        adapter.close()
        return {"error": True, "reason": ctx.get("reason", "Forget blocked by hook.")}
    ids = ctx.get("ids", ids)
    mode = ctx.get("mode", mode)

    processed = 0
    failed = 0
    now = datetime.datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for mid in ids:
        if mode == "hard":
            result = adapter.delete(mid)
        elif mode == "obsolete":
            result = adapter.update(mid, {"status": "obsolete", "updated_at": now})
        else:  # soft
            result = adapter.update(mid, {"status": "deleted", "updated_at": now})

        if not result.get("error"):
            processed += 1
        else:
            failed += 1

    output = {"count": processed, "failed": failed, "mode": mode, "ids": ids}

    # ── Hook: AFTER_FORGET ──
    registry.trigger(HookEvent.AFTER_FORGET, {
        "result": output,
        "config": config,
    })

    adapter.close()
    return output


if __name__ == "__main__":
    from lib.config import load_config
    import json
    config = load_config()
    q = sys.argv[1] if len(sys.argv) > 1 else ""
    result = run_forget(config, query=q)
    print(json.dumps(result, indent=2, ensure_ascii=False))
