"""
Tests for the Phase 3 sharing layer.

Coverage:
- SharingManager.can_access ACL evaluation across all five paths
  (owner / public / team / shared_with read / shared_with write).
- share / unshare round-trip on FakeAdapter.
- list_my_subscriptions aggregation across user / agent / team identities.
- Cross-agent recall via search ``extra_scopes`` with the ACL filter
  catching memories the adapter shouldn't have returned.
- Identity-string parsing edge cases.
"""
from __future__ import annotations

import json
import os

import pytest

from lib import (
    Config, ConfigError, SharingManager,
    is_identity_string, owner_from_scope, parse_identity, load_config,
)
from tests.fakes.fake_adapter import FakeAdapter


# ── Identity parsing ────────────────────────────────────────


@pytest.mark.parametrize("s,expected", [
    ("user:alice",       ("user", "alice")),
    ("agent:devbot",     ("agent", "devbot")),
    ("team:platform",    ("team", "platform")),
    ("user:alice@dev",   ("user", "alice@dev")),
    ("team:foo:bar",     ("team", "foo:bar")),  # ids with colons preserved
])
def test_parse_identity_valid(s, expected):
    assert parse_identity(s) == expected
    assert is_identity_string(s) is True


@pytest.mark.parametrize("s", [
    "alice", "agent:", ":bob", "system:doctor",
    "Agent:bob", None, 123,
])
def test_parse_identity_invalid(s):
    assert parse_identity(s) is None
    assert is_identity_string(s) is False


@pytest.mark.parametrize("scope,expected", [
    ("viking://tenants/default/users/alice/memories/", "user:alice"),
    ("viking://tenants/foo/agents/devbot/memories/projects/", "agent:devbot"),
    ("viking://tenants/foo/teams/platform/memories/", "team:platform"),
    ("viking://tenants/foo/system/doctor/", None),
    ("", None),
])
def test_owner_from_scope(scope, expected):
    assert owner_from_scope(scope) == expected


# ── Config / SharingManager fixtures ────────────────────────


@pytest.fixture
def config(tmp_path, monkeypatch):
    """Config with explicit identity opt-in so tests are deterministic."""
    for var in ("OV_USER_ID", "OV_AGENT_ID", "OV_TEAM_IDS",
                "OV_TENANT_ID", "OV_MEMORY_CONFIG"):
        monkeypatch.delenv(var, raising=False)
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "backend": "fake",
        "identity": {
            "tenant_id": "default",
            "user_id": "alice",
            "agent_id": "devbot",
            "team_ids": ["platform"],
        },
    }))
    monkeypatch.setenv("OV_USER_ID", "alice")
    monkeypatch.setenv("OV_AGENT_ID", "devbot")
    monkeypatch.setenv("OV_TEAM_IDS", "platform")
    return load_config(str(cfg_path))


@pytest.fixture
def adapter():
    return FakeAdapter()


@pytest.fixture
def sharing(adapter, config):
    return SharingManager(adapter, config)


# ── ACL evaluation ──────────────────────────────────────────


def test_owner_ACL_allows_all_ops(sharing):
    mem = {"owner_id": "user:alice", "visibility": "private"}
    assert sharing.can_access(mem, "read") is True
    assert sharing.can_access(mem, "write") is True


def test_owner_ACL_via_scope_when_owner_id_missing(sharing):
    # Legacy Phase 2 memory has no owner_id but lives in alice's scope.
    mem = {
        "content": "legacy",
        "scope": "viking://tenants/default/users/alice/memories/",
    }
    assert sharing.can_access(mem, "read") is True
    assert sharing.can_access(mem, "write") is True


def test_private_blocks_others(sharing):
    mem = {"owner_id": "user:bob", "visibility": "private"}
    assert sharing.can_access(mem, "read") is False
    assert sharing.can_access(mem, "write") is False


def test_public_allows_read_blocks_write(sharing):
    mem = {"owner_id": "user:bob", "visibility": "public"}
    assert sharing.can_access(mem, "read") is True
    assert sharing.can_access(mem, "write") is False


def test_team_visibility_via_membership(sharing):
    mem = {
        "owner_id": "agent:other",
        "visibility": "team",
        "scope": "viking://tenants/default/teams/platform/memories/",
    }
    assert sharing.can_access(mem, "read") is True
    # team visibility is read-only by design
    assert sharing.can_access(mem, "write") is False


def test_team_visibility_blocks_non_member(sharing):
    mem = {
        "owner_id": "agent:other",
        "visibility": "team",
        "scope": "viking://tenants/default/teams/secret/memories/",
    }
    assert sharing.can_access(mem, "read") is False


def test_shared_with_read_default(sharing):
    mem = {"owner_id": "user:bob", "shared_with": ["user:alice"]}
    assert sharing.can_access(mem, "read") is True
    # No shared_perms entry → defaults to read only
    assert sharing.can_access(mem, "write") is False


def test_shared_with_write_explicit(sharing):
    mem = {
        "owner_id": "user:bob",
        "shared_with": ["agent:devbot"],
        "shared_perms": {"agent:devbot": "write"},
    }
    assert sharing.can_access(mem, "read") is True
    assert sharing.can_access(mem, "write") is True


def test_shared_with_team_grant(sharing):
    mem = {
        "owner_id": "user:bob",
        "shared_with": ["team:platform"],
    }
    # alice belongs to team:platform → access via the team grant
    assert sharing.can_access(mem, "read") is True


def test_shared_with_unknown_target_blocks(sharing):
    mem = {
        "owner_id": "user:bob",
        "shared_with": ["user:carol"],
    }
    assert sharing.can_access(mem, "read") is False


def test_unknown_op_returns_false(sharing):
    mem = {"owner_id": "user:alice"}
    assert sharing.can_access(mem, "delete") is False


# ── share / unshare round-trip ──────────────────────────────


def test_share_validates_target_format(sharing, adapter):
    # Write a memory we own
    w = adapter.write({"content": "x", "type": "project"},
                      scope="viking://tenants/default/users/alice/memories/")
    mid = w["data"]["id"]
    bad = sharing.share(mid, "devbot", "read")  # no kind prefix
    assert bad["ok"] is False
    assert "kind" in bad["error"]
    bad2 = sharing.share(mid, "agent:devbot", "admin")  # invalid permission
    assert bad2["ok"] is False
    assert "permission" in bad2["error"]


def test_share_then_unshare_round_trip(sharing, adapter):
    w = adapter.write({"content": "x", "type": "project"},
                      scope="viking://tenants/default/users/alice/memories/")
    mid = w["data"]["id"]

    s = sharing.share(mid, "agent:devbot", "write")
    assert s["ok"] is True
    assert s["data"]["permission"] == "write"

    mem = adapter.read(mid)["data"]
    assert "agent:devbot" in mem["shared_with"]
    assert mem["shared_perms"]["agent:devbot"] == "write"

    u = sharing.unshare(mid, "agent:devbot")
    assert u["ok"] is True
    mem2 = adapter.read(mid)["data"]
    assert "agent:devbot" not in mem2["shared_with"]
    assert "agent:devbot" not in mem2["shared_perms"]


def test_unshare_idempotent(sharing, adapter):
    w = adapter.write({"content": "x", "type": "project"},
                      scope="viking://tenants/default/users/alice/memories/")
    mid = w["data"]["id"]
    # Never shared, but unshare succeeds anyway (no-op)
    u = sharing.unshare(mid, "agent:nobody")
    assert u["ok"] is True


# ── list_my_subscriptions aggregation ───────────────────────


def test_list_my_subscriptions_unions_across_identities(sharing, adapter):
    # 1. Memory in alice's team scope (matches via team membership)
    adapter.write(
        {"content": "team-shared note", "type": "project",
         "visibility": "team", "owner_id": "agent:other"},
        scope="viking://tenants/default/teams/platform/memories/",
    )
    # 2. Memory shared explicitly with alice (matches via shared_with)
    adapter.write(
        {"content": "for alice", "type": "project",
         "owner_id": "user:bob",
         "shared_with": ["user:alice"]},
        scope="viking://tenants/default/users/bob/memories/",
    )
    # 3. Memory shared with devbot (matches via agent identity)
    adapter.write(
        {"content": "for devbot", "type": "project",
         "owner_id": "user:bob",
         "shared_with": ["agent:devbot"]},
        scope="viking://tenants/default/users/bob/memories/",
    )
    # 4. Memory shared with someone else entirely (must NOT match)
    adapter.write(
        {"content": "for carol", "type": "project",
         "owner_id": "user:bob",
         "shared_with": ["user:carol"]},
        scope="viking://tenants/default/users/bob/memories/",
    )

    res = sharing.list_my_subscriptions()
    assert res["ok"] is True
    contents = sorted(m["content"] for m in res["data"])
    assert contents == ["for alice", "for devbot", "team-shared note"]


def test_list_my_subscriptions_dedup_by_id(sharing, adapter):
    # A memory shared with both team:platform AND user:alice should
    # appear only once even though two identities match it.
    adapter.write(
        {"content": "double-shared", "type": "project",
         "owner_id": "user:bob",
         "shared_with": ["user:alice", "team:platform"]},
        scope="viking://tenants/default/teams/platform/memories/",
    )
    res = sharing.list_my_subscriptions()
    assert res["ok"] is True
    assert len(res["data"]) == 1


# ── Cross-agent recall via extra_scopes ─────────────────────


def test_search_extra_scopes_merges_results(adapter, config):
    user_scope = config.user_scope
    team_scope = config.team_scope("platform")
    adapter.write({"content": "alice's note about FastAPI", "type": "project"},
                  scope=user_scope)
    adapter.write({"content": "team's note about FastAPI", "type": "project",
                    "visibility": "team"}, scope=team_scope)

    no_extra = adapter.search("FastAPI", scope=user_scope, limit=10,
                               memory_type="project")
    assert no_extra["ok"] is True
    assert len(no_extra["data"]) == 1

    with_extra = adapter.search(
        "FastAPI", scope=user_scope, limit=10, memory_type="project",
        extra_scopes=[team_scope],
    )
    assert with_extra["ok"] is True
    assert len(with_extra["data"]) == 2


def test_recall_acl_filter_drops_unauthorized(sharing, adapter, config):
    """Defence-in-depth: even if a buggy adapter returns memories the
    caller can't access, ``visible_memories`` filters them out."""
    bob_scope = adapter.build_scope("default", "user", "bob")
    adapter.write({"content": "bob's private", "type": "project",
                    "owner_id": "user:bob", "visibility": "private"},
                  scope=bob_scope)
    adapter.write({"content": "bob shared with alice", "type": "project",
                    "owner_id": "user:bob",
                    "shared_with": ["user:alice"]}, scope=bob_scope)

    raw = adapter.search("bob", scope=bob_scope, limit=10,
                          memory_type="project")
    assert raw["ok"] and len(raw["data"]) == 2

    visible = list(sharing.visible_memories(raw["data"]))
    assert len(visible) == 1
    assert visible[0]["content"] == "bob shared with alice"
