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
from lib.sharing import SharingManager


def run_recall(config: Config, query: str, memory_type: str = "", limit: int = 0,
               include_subscribed: bool | None = None) -> list:
    """Recall memories relevant to the query.

    Phase 3: when ``safety.auto_include_subscribed`` is true (or
    ``include_subscribed=True`` is passed explicitly), team scopes the
    current identity belongs to are added as ``extra_scopes`` so a
    single recall surfaces both own + subscribed memories. After the
    raw search, results are filtered through ``SharingManager.can_access``
    so private memories from other agents that share the same team
    scope still get rejected (defence in depth — the adapter shouldn't
    have returned them in the first place, but this stops a misconfigured
    backend from leaking).
    """
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

    if include_subscribed is None:
        include_subscribed = bool(config.get("safety.auto_include_subscribed", False))

    adapter = get_adapter(config)
    sharing = SharingManager(adapter, config)
    extra_scopes = sharing.subscribed_scopes() if include_subscribed else []

    all_memories = []
    types = [t.strip() for t in memory_type.split(",")] if memory_type else get_recall_types_order()

    for mtype in types:
        result = adapter.search(
            query=query, scope=config.user_scope,
            limit=limit, memory_type=mtype, min_score=min_score,
            extra_scopes=extra_scopes,
        )
        if not result.get("ok") and mtype == "agent_reflection":
            # Retry agent scope for agent_reflection types
            result = adapter.search(
                query=query, scope=config.agent_scope,
                limit=limit, memory_type=mtype, min_score=min_score,
                extra_scopes=extra_scopes,
            )
        if not result.get("ok"):
            continue
        data = result.get("data")
        # Adapters may return either a bare list or a dict with "memories"
        if isinstance(data, list):
            all_memories.extend(data)
        elif isinstance(data, dict):
            inner = data.get("memories", data.get("results", []))
            if isinstance(inner, list):
                all_memories.extend(inner)

    # Deduplicate by ID
    seen = set()
    unique = []
    for m in all_memories:
        mid = m.get("id", "")
        if mid and mid not in seen:
            seen.add(mid)
            unique.append(m)

    # ACL filter: drop anything the current identity can't read. This
    # is a no-op for legacy private memories in own scope (owner check
    # passes) and only meaningful when extra_scopes folded in shared
    # data the caller can't actually access.
    unique = list(sharing.visible_memories(unique, op="read"))

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
