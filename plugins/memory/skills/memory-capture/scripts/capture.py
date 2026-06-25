"""
memory-capture skill — Store a new long-term memory.
"""
import sys, os, json, uuid, datetime
from datetime import timezone
# Plugin root is three levels up: skills/<skill>/scripts/<file>.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from lib.config import Config, load_config
from lib.adapter_factory import get_adapter
from lib.sensitive_detector import has_sensitive, redact, classify_sensitivity
from lib.classifier import classify
from lib.hooks import HookRegistry, HookEvent


def _generate_memory_id() -> str:
    """Generate a globally-unique memory ID.

    Format: ``mem_<YYYYMMDDTHHMMSSmmm>_<full uuid4 hex>``.
    The previous 6-hex suffix had only ~16M combinations and could
    collide in busy capture flows; the full UUID4 makes collisions
    practically impossible while the millisecond-precision timestamp
    keeps IDs sortable.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    ts = now.strftime("%Y%m%dT%H%M%S") + f"{now.microsecond // 1000:03d}"
    return f"mem_{ts}_{uuid.uuid4().hex}"


def _join_scope(base: str, suffix: str) -> str:
    """Join a scope URI with a sub-path, normalising slashes.

    ``base`` may end with one or more slashes; ``suffix`` may start with
    them. The result has exactly one slash between them and a single
    trailing slash, regardless of input quirks. Stops the well-known
    ``…//preferences/`` double-slash artifact.
    """
    if not suffix:
        return base if base.endswith("/") else base + "/"
    return base.rstrip("/") + "/" + suffix.strip("/") + "/"


def run_capture(config: Config, content: str, memory_type: str = "",
                title: str = "", scope: str = "",
                visibility: str = "private",
                shared_with: list[str] | None = None) -> dict:
    """Capture a new memory after safety checks.

    Phase 3 args:
        visibility: ``"private"`` (default), ``"team"`` or ``"public"``.
                    ``"team"`` requires the scope to be a team scope.
        shared_with: optional list of identity strings (``"<kind>:<id>"``)
                     to grant read access at write time. The adapter
                     stores them in memory.shared_with; SharingManager
                     evaluates them on recall.
    """
    # 0. Initialize hooks
    hooks = HookRegistry(config.get("hooks", {}))

    # 1. BEFORE_STORE hooks (includes sensitive check + dedupe)
    hook_ctx = {"content": content, "config": config}
    hook_ctx = hooks.trigger(HookEvent.BEFORE_STORE, hook_ctx)
    if hook_ctx.get("blocked"):
        return {"error": True, "reason": hook_ctx.get("reason", "Blocked by hook")}
    content = hook_ctx.get("content", content)

    # 2. Classify if type not provided
    if not memory_type:
        memory_type = classify(content, classifier_config=config.classifier_config)

    # 3. Build memory object
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    if visibility not in ("private", "team", "public"):
        return {"error": True, "reason": f"invalid visibility {visibility!r}"}
    valid_shared_with: list[str] = []
    if shared_with:
        for ident in shared_with:
            if isinstance(ident, str) and ":" in ident and ident.split(":", 1)[0] in ("user", "agent", "team"):
                valid_shared_with.append(ident)
            else:
                return {"error": True, "reason": f"invalid shared_with entry {ident!r}"}
    # Owner identity at write time — used by SharingManager.can_access
    # so we don't have to re-parse the scope. Prefer agent identity for
    # agent_reflection memories so they show up under "agent:devbot".
    owner_id = (
        f"agent:{config.agent_id}" if memory_type == "agent_reflection"
        else f"user:{config.user_id}"
    )
    memory = {
        "id": _generate_memory_id(),
        "type": memory_type,
        "title": title or content[:80],
        "content": content,
        "summary": content[:200] if len(content) > 200 else content,
        "tags": [],
        "entities": [],
        "confidence": 0.85,
        "source": {"kind": "manual"},
        "policy": {"sensitive": False, "user_confirmed": True, "retention": "long_term"},
        "status": "active",
        "owner_id": owner_id,
        "visibility": visibility,
        "shared_with": valid_shared_with,
        "shared_perms": {ident: "read" for ident in valid_shared_with},
        "created_at": now,
        "updated_at": now,
    }

    # 4. Determine scope (use _join_scope so we never produce …//preferences/)
    if not scope:
        scope_map = {
            "preference":       _join_scope(config.user_scope, "preferences"),
            "project":          _join_scope(config.user_scope, "projects"),
            "environment":      _join_scope(config.user_scope, "environments"),
            "case":             _join_scope(config.user_scope, "cases"),
            "decision":         _join_scope(config.user_scope, "decisions"),
            "profile":          _join_scope(config.user_scope, "profile"),
            "agent_reflection": _join_scope(config.agent_scope, "reflections"),
        }
        scope = scope_map.get(memory_type, config.user_scope)

    # 4b. visibility="team" sanity: scope must contain "/teams/" segment
    # so that team membership ACL works without an explicit shared_with
    # list. Fail fast — silent fall-through here = data leak in reverse
    # ("you wanted team-shared but stored as user-only").
    if visibility == "team" and "/teams/" not in scope:
        return {
            "error": True,
            "reason": (
                f"visibility=team requires the scope to be a team scope "
                f"(viking://.../teams/<team_id>/...); got {scope}. "
                f"Pass --scope explicitly or set memory_type to a "
                f"team-routed type."
            ),
        }

    # 5. Write
    adapter = get_adapter(config)
    result = adapter.write(memory, scope=scope)
    adapter.close()

    if not result.get("ok"):
        return {"error": True, "reason": result.get("error", "write failed")}

    memory["scope"] = scope
    written = result.get("data") or {}
    if isinstance(written, dict) and written.get("id"):
        memory["id"] = written["id"]

    # 6. AFTER_STORE hooks
    hooks.trigger(HookEvent.AFTER_STORE, {"memory": memory, "config": config})

    return memory


if __name__ == "__main__":
    config = load_config()
    content = sys.argv[1] if len(sys.argv) > 1 else "test memory"
    result = run_capture(config, content=content)
    print(json.dumps(result, indent=2, ensure_ascii=False))
