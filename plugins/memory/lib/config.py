"""
OpenViking Memory Skill Suite — Configuration loader.
Loads config from: project config.json, ~/.openviking-memory/config.json, env vars.
"""
import json
import os
from pathlib import Path
from typing import Any

_DEFAULT_CONFIG = {
    "openviking": {
        "base_url": "http://127.0.0.1:8000",
        "api_key_env": "OPENVIKING_API_KEY",
        "timeout_seconds": 10,
    },
    "mem0": {
        "api_key_env": "MEM0_API_KEY",
        "version": "v1.1",
    },
    "backend": "openviking",
    # Scope template — {tenant}, {type} (user|agent|system), {entity} are placeholders.
    # Change this when switching backends (Mem0, Zep, etc. use different namespaces).
    "scope_template": "viking://tenants/{tenant}/{type}s/{entity}/memories/",
    "mcp": {
        "enabled": True,
        "server_name": "openviking",
        "tool_names": {
            "search": "memsearch",
            "read": "memread",
            "write": "memwrite",
            "update": "memupdate",
            "delete": "memforget",
            "commit": "memcommit",
            "browse": "membrowse",
        },
    },
    "identity": {
        "tenant_id": "default",
        "user_id": "default_user",
        "agent_id": "default_agent",
    },
    "scopes": {
        "_comment": "Scopes are built dynamically from scope_template + identity. Override here to use fixed values.",
    },
    "recall": {
        "default_limit": 6,
        "max_limit": 12,
        "default_level": "L0",
        "allow_l2": False,
        "min_score": 0.62,
    },
    "store": {
        "auto_store": False,
        "require_confirmation_for_sensitive": True,
        "dedupe_before_store": True,
    },
    "commit": {
        "enabled": True,
        "max_memories_per_session": 5,
        "store_cases": True,
        "store_preferences": True,
        "store_projects": True,
    },
    "safety": {
        "deny_sensitive": True,
        "allow_cross_user_read": False,
        "allow_cross_user_write": False,
        "redact_secrets": True,
    },
    "classifier": {
        "builtin_rules": True,
        "extra_rules": {},
        "plugin": None,
        "default_type": "project",
    },
    "policy": {
        "profile": "default",
        "profiles": {
            "default": {},
            "code_assistant": {
                "store_worthy": ["implement", "fix", "refactor", "merge", "commit", "deploy"],
                "skip_indicators": ["tmp", "scratch", "throwaway"],
                "recall_triggers": ["what did", "show me", "remember when", "上次", "之前"],
                "min_content_length": 10,
            },
            "life_assistant": {
                "store_worthy": ["记住", "以后", "always", "never", "prefer", "like", "dislike"],
                "skip_indicators": ["临时", "这次", "just for now"],
                "recall_triggers": ["记得", "之前", "上次", "my preference", "what do I"],
                "min_content_length": 5,
            },
        },
    },
    "hooks": {
        "plugins": [],
        "builtin": {
            "sensitive_block": True,
            "conflict_detect": True,
            "dedupe": False,
        },
    },
}

_SEARCH_PATHS = [
    Path.cwd() / "config.json",
    Path.cwd() / ".ov-memory" / "config.json",
    Path.home() / ".openviking-memory" / "config.json",
    Path.home() / ".config" / "openviking-memory" / "config.json",
]


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


class Config:
    """Immutable configuration object."""

    def __init__(self, data: dict):
        self._data = data

    def get(self, dotpath: str, default: Any = None) -> Any:
        """Get a config value by dot-path, e.g. 'openviking.base_url'."""
        keys = dotpath.split(".")
        node = self._data
        for k in keys:
            if isinstance(node, dict) and k in node:
                node = node[k]
            else:
                return default
        return node

    @property
    def data(self) -> dict:
        return self._data.copy()

    @property
    def openviking_url(self) -> str:
        return self.get("openviking.base_url", "http://127.0.0.1:8000")

    @property
    def api_key(self) -> str | None:
        env_name = self.get("openviking.api_key_env", "OPENVIKING_API_KEY")
        return os.environ.get(env_name)

    @property
    def timeout(self) -> int:
        return self.get("openviking.timeout_seconds", 10)

    @property
    def tenant_id(self) -> str:
        return self.get("identity.tenant_id", "default")

    @property
    def user_id(self) -> str:
        return self.get("identity.user_id", "default_user")

    @property
    def agent_id(self) -> str:
        return self.get("identity.agent_id", "default_agent")

    @property
    def scope_template(self) -> str:
        """Scope URI template with {tenant}, {type}, {entity} placeholders."""
        return self.get(
            "scope_template",
            "viking://tenants/{tenant}/{type}s/{entity}/memories/"
        )

    def build_scope(self, entity_type: str, entity_id: str) -> str:
        """
        Build a scope URI from the template.

        Args:
            entity_type: "user" | "agent" | "system"
            entity_id:   User ID, agent ID, or system component name.
        """
        # Allow explicit scope overrides in config to take precedence
        override_keys = {
            ("user", self.user_id): "user_memories",
            ("agent", self.agent_id): "agent_memories",
            ("system", "doctor"): "doctor",
        }
        override_key = override_keys.get((entity_type, entity_id))
        if override_key:
            val = self.get(f"scopes.{override_key}", "")
            if val:
                return val
        tmpl = self.scope_template
        if entity_type == "system":
            tmpl = tmpl.replace("/{type}s/{entity}/memories/", "/system/{entity}/")
        return tmpl.format(
            tenant=self.tenant_id, type=entity_type, entity=entity_id
        )

    @property
    def user_scope(self) -> str:
        return self.build_scope("user", self.user_id)

    @property
    def agent_scope(self) -> str:
        return self.build_scope("agent", self.agent_id)

    @property
    def doctor_scope(self) -> str:
        return self.build_scope("system", "doctor")

    @property
    def mem0_config(self) -> dict:
        """Return mem0 backend configuration."""
        return self.get("mem0", {})

    @property
    def mem0_api_key(self) -> str | None:
        env_name = self.get("mem0.api_key_env", "MEM0_API_KEY")
        return os.environ.get(env_name)

    @property
    def mcp_enabled(self) -> bool:
        return self.get("mcp.enabled", True)

    @property
    def mcp_tool_names(self) -> dict:
        return self.get("mcp.tool_names", {})

    @property
    def recall_limit(self) -> int:
        return self.get("recall.default_limit", 6)

    @property
    def recall_min_score(self) -> float:
        return self.get("recall.min_score", 0.62)

    @property
    def auto_store(self) -> bool:
        return self.get("store.auto_store", False)

    @property
    def deny_sensitive(self) -> bool:
        return self.get("safety.deny_sensitive", True)

    @property
    def redact_secrets(self) -> bool:
        return self.get("safety.redact_secrets", True)

    @property
    def classifier_config(self) -> dict:
        """Return classifier configuration (builtin_rules, extra_rules, plugin, default_type)."""
        return self.get("classifier", {})

    @property
    def hooks_config(self) -> dict:
        """Return hooks configuration (plugins, builtin)."""
        return self.get("hooks", {})

    @property
    def policy_profile(self) -> str:
        """Active policy profile name."""
        return self.get("policy.profile", "default")

    @property
    def policy_config(self) -> dict:
        """Return the active policy profile config."""
        profile = self.policy_profile
        profiles = self.get("policy.profiles", {})
        return profiles.get(profile, {})


def load_config(config_path: str | None = None) -> Config:
    """
    Load and merge configuration from defaults + file + env overrides.
    Priority: explicit path > env OV_MEMORY_CONFIG > search paths > defaults.
    """
    merged = dict(_DEFAULT_CONFIG)

    # Determine which file to load
    candidates = []
    if config_path:
        candidates.append(Path(config_path))
    env_path = os.environ.get("OV_MEMORY_CONFIG")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(_SEARCH_PATHS)

    for p in candidates:
        if p.is_file():
            try:
                with open(p) as f:
                    file_cfg = json.load(f)
                merged = _deep_merge(merged, file_cfg)
                break
            except (json.JSONDecodeError, OSError):
                continue

    # Env overrides
    env_url = os.environ.get("OPENVIKING_URL")
    if env_url:
        merged.setdefault("openviking", {})["base_url"] = env_url

    env_tenant = os.environ.get("OV_TENANT_ID")
    if env_tenant:
        merged.setdefault("identity", {})["tenant_id"] = env_tenant

    env_user = os.environ.get("OV_USER_ID")
    if env_user:
        merged.setdefault("identity", {})["user_id"] = env_user

    env_agent = os.environ.get("OV_AGENT_ID")
    if env_agent:
        merged.setdefault("identity", {})["agent_id"] = env_agent

    # Note: scopes are now built dynamically by Config.build_scope()
    # from scope_template + identity. No static rebuild needed.

    return Config(merged)
