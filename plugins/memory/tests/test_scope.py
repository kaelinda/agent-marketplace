"""
Tests for Phase 3 scope / identity primitives.

Covers ``Config.build_scope`` for every entity_type, scope-template
override behaviour, OV_TEAM_IDS env parsing edge cases, and the
``my_identity_strings`` aggregation that SharingManager keys off.
"""
from __future__ import annotations

import json

import pytest

from lib.config import Config, ConfigError, load_config


_OV_VARS = (
    "OV_USER_ID", "OV_AGENT_ID", "OV_TENANT_ID", "OV_TEAM_IDS",
    "OV_MEMORY_CONFIG",
)


def _clean_env(monkeypatch):
    for v in _OV_VARS:
        monkeypatch.delenv(v, raising=False)


@pytest.fixture
def base_config(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("OV_USER_ID", "alice")
    monkeypatch.setenv("OV_AGENT_ID", "devbot")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")
    return load_config(str(cfg_path))


def test_build_scope_user(base_config):
    s = base_config.build_scope("user", "alice")
    assert s == "viking://tenants/default/users/alice/memories/"


def test_build_scope_agent(base_config):
    s = base_config.build_scope("agent", "devbot")
    assert s == "viking://tenants/default/agents/devbot/memories/"


def test_build_scope_team(base_config):
    s = base_config.build_scope("team", "platform")
    assert s == "viking://tenants/default/teams/platform/memories/"


def test_build_scope_system_uses_special_layout(base_config):
    s = base_config.build_scope("system", "doctor")
    # System scopes drop the "/memories/" suffix
    assert s == "viking://tenants/default/system/doctor/"


def test_build_scope_rejects_unknown_entity_type(base_config):
    with pytest.raises(ValueError) as exc:
        base_config.build_scope("orange", "x")
    assert "entity_type" in str(exc.value)


def test_team_scopes_property(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("OV_USER_ID", "alice")
    monkeypatch.setenv("OV_AGENT_ID", "devbot")
    monkeypatch.setenv("OV_TEAM_IDS", "platform,backend , data")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")
    cfg = load_config(str(cfg_path))
    # spaces tolerated, empty entries dropped
    assert cfg.team_ids == ["platform", "backend", "data"]
    assert cfg.team_scopes == [
        "viking://tenants/default/teams/platform/memories/",
        "viking://tenants/default/teams/backend/memories/",
        "viking://tenants/default/teams/data/memories/",
    ]


def test_team_scopes_empty_when_unset(base_config):
    assert base_config.team_ids == []
    assert base_config.team_scopes == []


def test_my_identity_strings(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("OV_USER_ID", "alice")
    monkeypatch.setenv("OV_AGENT_ID", "devbot")
    monkeypatch.setenv("OV_TEAM_IDS", "platform,data")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}")
    cfg = load_config(str(cfg_path))
    assert cfg.my_identity_strings() == [
        "user:alice", "agent:devbot", "team:platform", "team:data",
    ]


def test_my_identity_strings_no_teams(base_config):
    assert base_config.my_identity_strings() == [
        "user:alice", "agent:devbot",
    ]


def test_team_ids_from_config_file(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("OV_USER_ID", "alice")
    monkeypatch.setenv("OV_AGENT_ID", "devbot")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "identity": {"team_ids": ["alpha", "beta"]},
    }))
    cfg = load_config(str(cfg_path))
    assert cfg.team_ids == ["alpha", "beta"]


def test_OV_TEAM_IDS_overrides_file(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("OV_USER_ID", "alice")
    monkeypatch.setenv("OV_AGENT_ID", "devbot")
    monkeypatch.setenv("OV_TEAM_IDS", "platform")
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "identity": {"team_ids": ["alpha", "beta"]},
    }))
    cfg = load_config(str(cfg_path))
    assert cfg.team_ids == ["platform"]
