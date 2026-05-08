"""
Tests for the identity fail-closed behaviour added in Phase 2.

These guard the most dangerous regression: silently letting two agents
share a default_agent namespace because someone forgot to set OV_AGENT_ID.
"""
from __future__ import annotations

import json

import pytest

from lib.config import ConfigError, load_config


_OV_VARS = (
    "OV_USER_ID", "OV_AGENT_ID", "OV_TENANT_ID",
    "OV_MEMORY_CONFIG", "OPENVIKING_URL", "OPENVIKING_API_KEY",
    "MEM0_API_KEY",
)


def _clean_env(monkeypatch):
    """Remove every OV_* / OPENVIKING_* / MEM0_* env var.

    A direct call inside each test is more robust than a single autouse
    fixture: monkeypatch's LIFO teardown has surprising interactions
    when an autouse fixture and a per-test monkeypatch both touch the
    same variable across tests in the same module.
    """
    for var in _OV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_default_identity_raises_without_optin(tmp_path, monkeypatch):
    """No env, no opt-in → ConfigError on load."""
    _clean_env(monkeypatch)
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")  # everything from defaults
    with pytest.raises(ConfigError) as exc:
        load_config(str(cfg_path))
    msg = str(exc.value)
    assert "identity.user_id" in msg
    assert "identity.agent_id" in msg
    assert "OV_USER_ID" in msg
    assert "OV_AGENT_ID" in msg


def test_env_overrides_satisfy_identity_check(tmp_path, monkeypatch):
    """Setting OV_USER_ID + OV_AGENT_ID is enough."""
    _clean_env(monkeypatch)
    monkeypatch.setenv("OV_USER_ID", "alice")
    monkeypatch.setenv("OV_AGENT_ID", "devbot")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")
    cfg = load_config(str(cfg_path))
    assert cfg.user_id == "alice"
    assert cfg.agent_id == "devbot"


def test_explicit_optin_allows_default_identity(tmp_path, monkeypatch):
    """safety.allow_default_identity=true bypasses the check (tests / one-shots)."""
    _clean_env(monkeypatch)
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({"safety": {"allow_default_identity": True}}))
    cfg = load_config(str(cfg_path))
    assert cfg.user_id == "default_user"
    assert cfg.agent_id == "default_agent"
    assert cfg.get("safety.allow_default_identity") is True


def test_default_config_is_not_mutated_across_calls(tmp_path, monkeypatch):
    """Regression guard: env overrides must not mutate _DEFAULT_CONFIG.

    A shallow copy in load_config() previously caused envs set during
    one call to leak into the next call's identity fields. The fix is
    a real deep copy; this test ensures it stays that way.
    """
    _clean_env(monkeypatch)
    monkeypatch.setenv("OV_USER_ID", "leaky_alice")
    monkeypatch.setenv("OV_AGENT_ID", "leaky_devbot")
    cfg_path = tmp_path / "first.json"
    cfg_path.write_text("{}")
    cfg1 = load_config(str(cfg_path))
    assert cfg1.user_id == "leaky_alice"

    # Now clean the env and load a config that ONLY opts in to default
    # identity. If _DEFAULT_CONFIG was mutated, user_id would still be
    # "leaky_alice"; the deep-copy fix makes this come back as default.
    _clean_env(monkeypatch)
    cfg_path2 = tmp_path / "second.json"
    cfg_path2.write_text(json.dumps({"safety": {"allow_default_identity": True}}))
    cfg2 = load_config(str(cfg_path2))
    assert cfg2.user_id == "default_user", \
        "env override leaked into _DEFAULT_CONFIG (deep-copy regression)"
    assert cfg2.agent_id == "default_agent"


def test_partial_default_user_only_still_raises(tmp_path, monkeypatch):
    """Just OV_AGENT_ID is not enough: user is still default."""
    _clean_env(monkeypatch)
    monkeypatch.setenv("OV_AGENT_ID", "devbot")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")
    with pytest.raises(ConfigError) as exc:
        load_config(str(cfg_path))
    msg = str(exc.value)
    assert "identity.user_id" in msg
    assert "identity.agent_id" not in msg


def test_partial_default_agent_only_still_raises(tmp_path, monkeypatch):
    """Just OV_USER_ID is not enough: agent is still default."""
    _clean_env(monkeypatch)
    monkeypatch.setenv("OV_USER_ID", "alice")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")
    with pytest.raises(ConfigError) as exc:
        load_config(str(cfg_path))
    msg = str(exc.value)
    assert "identity.agent_id" in msg
    assert "identity.user_id" not in msg
