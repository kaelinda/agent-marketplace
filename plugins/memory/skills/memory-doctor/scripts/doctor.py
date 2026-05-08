"""
memory-doctor skill — Diagnostic checks for the memory plugin.
"""
import json
import sys
import os
import time

# Plugin root is three levels up: skills/<skill>/scripts/<file>.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.mcp_adapter import MCPAdapter


def _unwrap(result: dict) -> dict:
    """Flatten an AdapterResponse-shape dict into the form doctor expects.

    All adapters now uniformly return ``{ok, data, error, meta}`` (see
    Phase 2 — ``lib/adapter_protocol.AdapterResponse``). This helper
    converts that into the legacy ``{error, reason, memories, ...}``
    shape this file reads from.
    """
    if not isinstance(result, dict):
        return {"error": True, "reason": "Non-dict response"}
    if result.get("ok") is False:
        flat = {"error": True, "reason": result.get("error", "unknown error")}
        flat.update(result.get("meta", {}))
        return flat
    data = result.get("data")
    if isinstance(data, list):
        return {"memories": data, **result.get("meta", {})}
    if isinstance(data, dict):
        flat = dict(data)
        flat.setdefault("error", None)
        flat.update(result.get("meta", {}))
        return flat
    return {"data": data, **result.get("meta", {})}


def _check(name, fn):
    """Run a single check, return result dict."""
    try:
        result = fn()
        if isinstance(result, dict) and result.get("status"):
            return result
        return {"name": name, "status": "pass", "detail": ""}
    except Exception as e:
        return {"name": name, "status": "fail", "detail": str(e)}


def run_doctor(config: Config, mode: str = "standard") -> dict:
    """Run diagnostic checks. mode: quick | standard | full."""
    checks = []
    warnings = []
    errors = []
    backend = config.get("backend", "openviking")
    endpoint = config.openviking_url if backend != "mem0" else "mem0 cloud API"
    tenant = config.tenant_id
    user = config.user_id
    agent = config.agent_id

    # ── Quick checks (always run) ────────────────────────────

    # 1. Config loaded
    checks.append({"name": "Config loaded", "status": "pass"})

    # 2. API key
    if backend == "mem0":
        api_key = config.mem0_api_key
        env_name = config.get("mem0.api_key_env", "MEM0_API_KEY")
    else:
        api_key = config.api_key
        env_name = config.get("openviking.api_key_env", "OPENVIKING_API_KEY")
    if api_key:
        checks.append({"name": f"API key loaded from {env_name}", "status": "pass"})
    else:
        checks.append({"name": "API key loaded", "status": "warn",
                        "detail": f"No API key found. Set {env_name} env var."})
        warnings.append(f"No API key configured for {backend} backend. Some operations may fail.")

    # 3. Identity safety (Critical — see EVAL.md §2.4 / config.py)
    allow_default = config.get("safety.allow_default_identity", False)
    if user == "default_user":
        if allow_default:
            checks.append({"name": "Identity user_id (opt-in default)", "status": "warn",
                            "detail": "Using default_user with allow_default_identity=true."})
            warnings.append('user_id is "default_user" (allow_default_identity=true). Multi-agent collisions possible.')
        else:
            checks.append({"name": "Identity user_id", "status": "fail",
                            "detail": "user_id resolves to default_user sentinel; set OV_USER_ID."})
            errors.append('user_id is "default_user". Set OV_USER_ID or identity.user_id in config.json.')
    else:
        checks.append({"name": f"Identity user_id = {user}", "status": "pass"})
    if agent == "default_agent":
        if allow_default:
            checks.append({"name": "Identity agent_id (opt-in default)", "status": "warn",
                            "detail": "Using default_agent with allow_default_identity=true."})
            warnings.append('agent_id is "default_agent" (allow_default_identity=true). Multi-agent collisions possible.')
        else:
            checks.append({"name": "Identity agent_id", "status": "fail",
                            "detail": "agent_id resolves to default_agent sentinel; set OV_AGENT_ID."})
            errors.append('agent_id is "default_agent". Set OV_AGENT_ID or identity.agent_id in config.json.')
    else:
        checks.append({"name": f"Identity agent_id = {agent}", "status": "pass"})
    if not config.auto_store:
        warnings.append("auto_store is disabled. This is safe, but memory will only be stored explicitly.")

    if mode == "quick":
        result = "PASS_WITH_WARNINGS" if warnings else "PASS"
        return {
            "result": result,
            "meta": {"mode": mode, "endpoint": endpoint, "tenant": tenant,
                     "user": user, "agent": agent},
            "checks": checks, "warnings": warnings, "errors": errors,
        }

    # ── Standard checks ──────────────────────────────────────

    # 4. Service reachable
    adapter = get_adapter(config)
    if hasattr(adapter, "ping"):
        ping = adapter.ping()
    elif hasattr(adapter, "client") and hasattr(adapter.client, "ping"):
        ping = adapter.client.ping()
    else:
        ping = {"error": True, "reason": "Adapter has no ping capability"}
    ping = _unwrap(ping)
    if ping.get("error"):
        checks.append({"name": "OpenViking service reachable", "status": "fail",
                        "detail": ping.get("reason", "unreachable")})
        errors.append(f"Cannot reach OpenViking at {endpoint}")
    else:
        elapsed = ping.get("elapsed_ms", ping.get("_elapsed_ms", "?"))
        checks.append({"name": f"OpenViking service reachable: {elapsed}ms", "status": "pass"})

    # 5. MCP server (if enabled)
    if config.mcp_enabled:
        mcp = MCPAdapter(server_name=config.get("mcp.server_name", "openviking"),
                         tool_names=config.mcp_tool_names)
        required_tools = ["search", "read", "write", "delete", "commit"]
        tool_names = config.mcp_tool_names
        found = []
        missing = []
        for action in required_tools:
            tname = tool_names.get(action, action)
            # We can't actually probe MCP tools without calling them,
            # so we just check config has them defined
            if tname:
                found.append(tname)
            else:
                missing.append(action)
        if missing:
            checks.append({"name": f"MCP tools configured", "status": "warn",
                            "detail": f"Missing tool mappings: {', '.join(missing)}"})
        else:
            checks.append({"name": f"Required tools found: {', '.join(found)}", "status": "pass"})
    else:
        checks.append({"name": "MCP server", "status": "skip", "detail": "MCP disabled in config"})

    # 6. Scope readable
    user_scope = config.user_scope
    if user_scope:
        checks.append({"name": "User memory scope configured", "status": "pass"})
    else:
        checks.append({"name": "User memory scope configured", "status": "fail",
                        "detail": "scopes.user_memories is empty"})
        errors.append("User memory scope not configured.")

    if mode == "standard":
        result = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
        return {
            "result": result,
            "meta": {"mode": mode, "endpoint": endpoint, "tenant": tenant,
                     "user": user, "agent": agent},
            "checks": checks, "warnings": warnings, "errors": errors,
        }

    # ── Full checks ──────────────────────────────────────────

    # 7. Write → search → read → delete loop
    doctor_scope = config.doctor_scope
    test_memory = {
        "type": "project",
        "title": "OV Memory Doctor Test",
        "content": "This is a temporary test memory created by ov-memory doctor.",
        "tags": ["doctor-test"],
        "status": "active",
        "policy": {"sensitive": False, "user_confirmed": True, "retention": "short_term"},
    }

    # Write
    write_result = _unwrap(adapter.write(test_memory, scope=doctor_scope))
    if write_result.get("error"):
        checks.append({"name": "Doctor write test", "status": "fail",
                        "detail": write_result.get("reason", "")})
        errors.append("Write test failed.")
    else:
        test_id = write_result.get("id", "")
        checks.append({"name": "Doctor write test passed", "status": "pass"})

        # Search
        time.sleep(0.5)  # brief wait for indexing
        search_result = _unwrap(adapter.search("Doctor Test", scope=doctor_scope, limit=1))
        found = search_result.get("memories", search_result.get("data", []))
        if found:
            checks.append({"name": "Doctor search test passed", "status": "pass"})
        else:
            checks.append({"name": "Doctor search test", "status": "warn",
                            "detail": "Write succeeded but search returned empty. Index may be delayed."})
            warnings.append("Search may have indexing delay.")

        # Read
        if test_id:
            read_result = _unwrap(adapter.read(test_id))
            if read_result.get("error"):
                checks.append({"name": "Doctor read test", "status": "fail",
                                "detail": read_result.get("reason", "")})
                errors.append("Read test failed.")
            else:
                checks.append({"name": "Doctor read test passed", "status": "pass"})

            # Delete
            del_result = _unwrap(adapter.delete(test_id))
            if del_result.get("error"):
                checks.append({"name": "Doctor delete test", "status": "warn",
                                "detail": "Could not clean up test memory."})
                warnings.append(f"Test memory {test_id} was not cleaned up.")
            else:
                checks.append({"name": "Doctor delete test passed", "status": "pass"})

    # 8. Namespace isolation check (already enforced via identity check
    # in step 3; this just records context-aware notes for full mode)
    if user == "default_user" and config.get("safety.allow_default_identity", False):
        warnings.append("Namespace may have cross-user collision risk with default_user.")

    result = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    adapter.close()
    return {
        "result": result,
        "meta": {"mode": mode, "endpoint": endpoint, "tenant": tenant,
                 "user": user, "agent": agent},
        "checks": checks, "warnings": warnings, "errors": errors,
    }


if __name__ == "__main__":
    from lib.config import load_config
    config = load_config()
    result = run_doctor(config, mode="full")
    from lib.formatter import format_doctor_report
    print(format_doctor_report(result))
