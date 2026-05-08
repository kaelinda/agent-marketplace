"""
Adapter contract test — runs the same expectations against every
``MemoryAdapter`` implementation that's importable in the test env.

Phase 2 scope:
- FakeAdapter (always)
- HTTPAdapter (offline path: must surface URLError as ok=False)
- MCPAdapter  (offline path: mcporter not on PATH → ok=False)
- Mem0Adapter (skipped unless ``mem0ai`` is installed)

Real-network tests for HTTP / MCP / mem0 belong in Phase 5; Phase 2
verifies only the *contract* (response shape, error envelope, scope
construction).
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest

from lib import HTTPAdapter, MCPAdapter, MemoryAdapter
from tests.fakes.fake_adapter import FakeAdapter


# ── Adapter parametrisation ─────────────────────────────────


def _maybe_mem0():
    if importlib.util.find_spec("mem0") is None:
        pytest.skip("mem0ai not installed; skipping Mem0Adapter contract")
    from lib.mem0_adapter import Mem0Adapter
    api_key = os.environ.get("MEM0_API_KEY")
    if not api_key:
        pytest.skip("MEM0_API_KEY not set; skipping Mem0Adapter contract")
    return Mem0Adapter(api_key=api_key)


@pytest.fixture(params=["fake", "http", "mcp"])
def adapter(request):
    """Yield a fresh adapter for each parametrised backend."""
    if request.param == "fake":
        a = FakeAdapter()
    elif request.param == "http":
        # Use a deliberately-unreachable URL so the adapter exercises
        # the URLError branch synchronously without hitting a real
        # service. Phase 5 will cover happy-path HTTP via a fixture
        # service.
        a = HTTPAdapter("http://invalid-host-1234567890.example", timeout=2)
    elif request.param == "mcp":
        # No mcporter binary on a typical CI box → adapter takes the
        # FileNotFoundError fallback path and returns ok=False.
        a = MCPAdapter()
    else:
        pytest.fail(f"unknown adapter param: {request.param}")
    yield a
    a.close()


# ── Protocol shape ──────────────────────────────────────────


def test_adapter_implements_protocol(adapter):
    """All adapters must satisfy the runtime-checkable Protocol."""
    assert isinstance(adapter, MemoryAdapter)


def test_build_scope_user(adapter):
    s = adapter.build_scope("tenantA", "user", "alice")
    assert "tenantA" in s
    assert "alice" in s
    # Every backend's scope is a non-empty string.
    assert isinstance(s, str) and s


def test_build_scope_system_distinct(adapter):
    user = adapter.build_scope("tenantA", "user", "alice")
    sys_scope = adapter.build_scope("tenantA", "system", "doctor")
    assert user != sys_scope


# ── Error envelope ──────────────────────────────────────────


@pytest.mark.parametrize("op,call", [
    ("search", lambda a: a.search("anything")),
    ("read",   lambda a: a.read("nonexistent_id_xyz")),
    ("write",  lambda a: a.write({"content": ""})),
    ("delete", lambda a: a.delete("nonexistent_id_xyz")),
    ("browse", lambda a: a.browse(scope="viking://tenants/x/users/x/memories/")),
])
def test_response_envelope_shape(adapter, op, call):
    """
    Every adapter method MUST return a dict with at minimum an "ok" bool
    or a legacy "error" key. After Phase 2 normalisation, all three real
    adapters return "ok"; if any of them ever drops it, this test fails
    loudly and immediately.
    """
    result = call(adapter)
    assert isinstance(result, dict), f"{op} returned {type(result).__name__}"
    assert "ok" in result, f"{op} response missing 'ok' key: {result.keys()}"
    if not result["ok"]:
        # ok=False MUST carry an error string
        assert "error" in result and isinstance(result["error"], str)
        assert result["error"], "ok=False but error string is empty"


def test_unreachable_backend_returns_ok_false(adapter):
    """The two offline real adapters cannot reach a backend in the test
    environment, so they must report ok=False on a basic search."""
    if isinstance(adapter, FakeAdapter):
        pytest.skip("FakeAdapter is always reachable")
    r = adapter.search("ping")
    assert r["ok"] is False
    assert r["error"]


# ── Happy path on FakeAdapter ───────────────────────────────


def test_fake_adapter_write_read_search_delete():
    """Verify the contract is satisfiable on at least one backend."""
    a = FakeAdapter()
    scope = a.build_scope("default", "user", "alice")

    write = a.write({"content": "Nginx is at /etc/nginx", "type": "environment"}, scope=scope)
    assert write["ok"] is True
    mid = write["data"]["id"]

    read = a.read(mid)
    assert read["ok"] is True
    assert read["data"]["content"] == "Nginx is at /etc/nginx"

    search = a.search("Nginx", scope=scope)
    assert search["ok"] is True
    assert any(m["id"] == mid for m in search["data"])

    browse = a.browse(scope=scope)
    assert browse["ok"] is True
    assert len(browse["data"]) == 1

    delete = a.delete(mid)
    assert delete["ok"] is True
    assert delete["data"]["deleted"] is True

    after = a.search("Nginx", scope=scope)
    assert after["ok"] is True
    assert after["data"] == []
    a.close()


def test_fake_adapter_injected_failures_propagate():
    """An injected failure short-circuits and surfaces as ok=False."""
    a = FakeAdapter()
    a.fail_next_call = "search"
    r = a.search("anything")
    assert r["ok"] is False
    assert "forced search failure" in r["error"]
    a.close()
