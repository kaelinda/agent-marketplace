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


def run_capture(config: Config, content: str, memory_type: str = "",
                title: str = "", scope: str = "") -> dict:
    """Capture a new memory after safety checks."""
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
    memory = {
        "id": f"mem_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}",
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
        "created_at": now,
        "updated_at": now,
    }

    # 4. Determine scope
    if not scope:
        scope_map = {
            "preference": config.user_scope.rstrip("/") + "/preferences/",
            "project": config.user_scope.rstrip("/") + "/projects/",
            "environment": config.user_scope.rstrip("/") + "/environments/",
            "case": config.user_scope.rstrip("/") + "/cases/",
            "decision": config.user_scope.rstrip("/") + "/decisions/",
            "profile": config.user_scope.rstrip("/") + "/profile/",
            "agent_reflection": config.agent_scope.rstrip("/") + "/reflections/",
        }
        scope = scope_map.get(memory_type, config.user_scope)

    # 5. Write
    adapter = get_adapter(config)
    result = adapter.write(memory, scope=scope)
    adapter.close()

    if result.get("error"):
        return result

    memory["scope"] = scope
    if "id" in result:
        memory["id"] = result["id"]

    # 6. AFTER_STORE hooks
    hooks.trigger(HookEvent.AFTER_STORE, {"memory": memory, "config": config})

    return memory


if __name__ == "__main__":
    config = load_config()
    content = sys.argv[1] if len(sys.argv) > 1 else "test memory"
    result = run_capture(config, content=content)
    print(json.dumps(result, indent=2, ensure_ascii=False))
