"""
OpenViking Memory Skill Suite — Policy engine.
Centralizes all decision-making about when and how to recall, store, merge, forget.

Supports configurable policy profiles via config (policy.profile + policy.profiles).
Built-in defaults are preserved as the "default" profile fallback.
"""
from .config import Config

# ── Memory types and their priority for recall ──────────────
RECALL_PRIORITY = [
    "preference",      # 1. User preferences first
    "project",         # 2. Active projects
    "environment",     # 3. Technical environment
    "case",            # 4. Past troubleshooting cases
    "decision",        # 5. Confirmed decisions
    "agent_reflection",# 6. Agent's own reflections
    "profile",         # 7. User profile
]

# ── Default indicators (used when no profile is configured) ──

_DEFAULT_STORE_WORTHY = [
    "user prefers", "always use", "remember", "don't forget",
    "以后", "记住", "长期", "默认", "always", "never", "prefer",
]

_DEFAULT_SKIP_INDICATORS = [
    "temporary", "just for now", "one-time", "临时", "这次", "先这样",
]

_DEFAULT_RECALL_TRIGGERS = [
    "之前", "上次", "以前", "记得", "recall", "remember",
    "继续", "那个项目", "那个配置", "那个问题",
    "last time", "previously", "as mentioned", "we discussed",
    "my setup", "my server", "my environment",
]


# ── Config-driven getters ──────────────────────────────────

def get_store_worthy_indicators(policy_config: dict = None) -> list[str]:
    """Get store-worthy indicators, merging profile overrides with defaults."""
    cfg = policy_config or {}
    return cfg.get("store_worthy") or list(_DEFAULT_STORE_WORTHY)


def get_skip_indicators(policy_config: dict = None) -> list[str]:
    """Get skip indicators, merging profile overrides with defaults."""
    cfg = policy_config or {}
    return cfg.get("skip_indicators") or list(_DEFAULT_SKIP_INDICATORS)


def get_recall_triggers(policy_config: dict = None) -> list[str]:
    """Get recall triggers, merging profile overrides with defaults."""
    cfg = policy_config or {}
    return cfg.get("recall_triggers") or list(_DEFAULT_RECALL_TRIGGERS)


def get_min_content_length(policy_config: dict = None) -> int:
    """Get minimum content length for storage, with profile override."""
    cfg = policy_config or {}
    return cfg.get("min_content_length") or 20


# ── Core policy functions ──────────────────────────────────

def should_recall(task_description: str, config: Config) -> bool:
    """Determine if the current task warrants a memory recall."""
    if not task_description:
        return False
    lower = task_description.lower()
    triggers = get_recall_triggers(config.policy_config)
    return any(t in lower for t in triggers)


def should_store(content: str, config: Config) -> bool:
    """
    Determine if content is worth storing long-term.
    Conservative by default — only stores when indicators are present.
    """
    if config.auto_store:
        return True
    lower = content.lower()
    worthy = get_store_worthy_indicators(config.policy_config)
    skip = get_skip_indicators(config.policy_config)
    min_len = get_min_content_length(config.policy_config)
    has_worthy = any(ind in lower for ind in worthy)
    has_skip = any(ind in lower for ind in skip)
    if has_skip:
        return False
    if len(content.strip()) < min_len:
        return False
    return has_worthy


def is_auto_store_enabled(config: Config) -> bool:
    return config.auto_store


def get_recall_types_order() -> list[str]:
    return list(RECALL_PRIORITY)


def get_max_recall() -> int:
    return 12


def get_default_recall_limit(config: Config) -> int:
    return config.recall_limit


def allow_cross_user_read(config: Config) -> bool:
    return config.get("safety.allow_cross_user_read", False)


def allow_cross_user_write(config: Config) -> bool:
    return config.get("safety.allow_cross_user_write", False)
