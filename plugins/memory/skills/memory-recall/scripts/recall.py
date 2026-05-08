"""
memory-recall skill — Retrieve relevant memories for current task.
"""
import sys, os
# Plugin root is three levels up: skills/<skill>/scripts/<file>.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.policy import get_recall_types_order, get_default_recall_limit
from lib.hooks import HookRegistry, HookEvent


def run_recall(config: Config, query: str, memory_type: str = "", limit: int = 0) -> list:
    """Recall memories relevant to the query."""
    hooks = HookRegistry(config.get("hooks", {}))

    # BEFORE_RECALL hook
    hook_ctx = hooks.trigger(HookEvent.BEFORE_RECALL, {
        "query": query, "config": config,
    })
    if hook_ctx.get("blocked"):
        return []
    query = hook_ctx.get("query", query)

    if not limit:
        limit = get_default_recall_limit(config)
    limit = min(limit, config.get("recall.max_limit", 12))
    min_score = config.recall_min_score

    adapter = get_adapter(config)

    all_memories = []
    types = [t.strip() for t in memory_type.split(",")] if memory_type else get_recall_types_order()

    for mtype in types:
        result = adapter.search(
            query=query, scope=config.user_scope,
            limit=limit, memory_type=mtype, min_score=min_score,
        )
        if result.get("error"):
            # Try agent scope for agent_reflection
            if mtype == "agent_reflection":
                result = adapter.search(
                    query=query, scope=config.agent_scope,
                    limit=limit, memory_type=mtype, min_score=min_score,
                )
        memories = result.get("memories", result.get("data", []))
        if isinstance(memories, list):
            all_memories.extend(memories)

    # Deduplicate by ID
    seen = set()
    unique = []
    for m in all_memories:
        mid = m.get("id", "")
        if mid and mid not in seen:
            seen.add(mid)
            unique.append(m)

    # Sort by score (descending) and limit
    unique.sort(key=lambda m: m.get("score", m.get("_score", 0)), reverse=True)
    adapter.close()

    result = unique[:limit]

    # AFTER_RECALL hook
    hook_ctx = hooks.trigger(HookEvent.AFTER_RECALL, {
        "memories": result, "query": query, "config": config,
    })
    if "conflicts" in hook_ctx:
        # Attach conflicts info to the result for the caller
        for m in result:
            m["_conflicts"] = hook_ctx.get("conflicts", [])

    return result


if __name__ == "__main__":
    from lib.config import load_config
    from lib.formatter import format_recall_block
    config = load_config()
    q = sys.argv[1] if len(sys.argv) > 1 else "test query"
    memories = run_recall(config, q)
    print(format_recall_block(memories))
