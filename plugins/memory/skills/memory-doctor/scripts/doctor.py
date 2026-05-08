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
    """Normalize adapter response to a flat dict.

    HTTPAdapter returns raw API JSON: {"id": "...", "error": True, ...}
    Mem0Adapter wraps in AdapterResponse shape: {"ok": True, "data": {...}} or {"ok": False, "error": "..."}

    This helper flattens both into a consistent dict where:
    - "error" key is present and truthy when the call failed
    - "id" is at top level (extracted from "data" if needed)
    - "memories" / "data" list is at top level as "memories"
    """
    if not isinstance(result, dict):
        return {"error": True, "reason": "Non-dict response"}

    # Already a flat error (HTTP style)
    if result.get("error") is True and "ok" not in result:
        return result

    # AdapterResponse-wrapped error
    if result.get("ok") is False:
        flat = {"error": True, "reason": result.get("error", "unknown error")}
        flat.update(result.get("meta", {}))
        return flat

    # AdapterResponse-wrapped success
    if result.get("ok") is True and "data" in result:
        data = result["data"]
        if isinstance(data, list):
            return {"memories": data}
        if isinstance(data, dict):
            flat = dict(data)
            flat.setdefault("error", None)
            return flat
        return {"data": data}

    # HTTP-style flat success (no "ok" key, no "error" key)
    return result


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

    # 3. Identity warnings
    if user == "default_user":
        warnings.append('user_id is "default_user". Production should use a real user id.')
    if agent == "default_agent":
        warnings.append('agent_id is "default_agent". Production should use a real agent id.')
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

    # 8. Namespace isolation check
    if user == "default_user":
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
