"""
memory-commit skill — Extract durable memories from a session.
"""
import sys, os
# Plugin root is three levels up: skills/<skill>/scripts/<file>.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from lib.config import Config
from lib.sensitive_detector import has_sensitive, redact
from lib.classifier import classify
from lib.policy import get_store_worthy_indicators
from lib.skill_loader import load_skill_module


def _extract_candidates(session_data: dict, config: Config) -> list:
    """Extract memory candidates from session data."""
    candidates = []
    messages = session_data.get("messages", session_data.get("turns", []))

    for msg in messages:
        content = ""
        if isinstance(msg, dict):
            content = msg.get("content", msg.get("text", ""))
        elif isinstance(msg, str):
            content = msg

        if not content or len(content) < 30:
            continue

        # Skip sensitive
        if has_sensitive(content):
            continue

        # Check if worth storing
        lower = content.lower()
        is_worthy = any(ind.lower() in lower for ind in get_store_worthy_indicators(config.policy_config))
        if not is_worthy:
            continue

        mem_type = classify(content, classifier_config=config.classifier_config)
        candidates.append({
            "type": mem_type,
            "title": content[:80],
            "content": content[:500],
            "reason": f"Detected as {mem_type} from session",
            "recommended": mem_type in ("decision", "preference", "environment", "case"),
            "confidence": 0.7,
        })

    # Deduplicate by type+title similarity
    seen = set()
    unique = []
    for c in candidates:
        key = f"{c['type']}:{c['title'][:40]}"
        if key not in seen:
            seen.add(key)
            unique.append(c)

    max_memories = config.get("commit.max_memories_per_session", 5)
    return unique[:max_memories]


def run_commit(config: Config, session_data: dict, apply: bool = False) -> dict:
    """Extract and optionally store memory candidates."""
    candidates = _extract_candidates(session_data, config)
    discarded = []

    # Identify discarded (messages that were in session but didn't qualify)
    messages = session_data.get("messages", session_data.get("turns", []))
    candidate_contents = {c["content"][:40] for c in candidates}
    for msg in messages:
        content = msg.get("content", msg.get("text", "")) if isinstance(msg, dict) else str(msg)
        if content and len(content) >= 30:
            if content[:40] not in candidate_contents:
                discarded.append({"content": content[:80], "reason": "Not long-term useful or too short"})

    result = {"candidates": candidates, "discarded": discarded[:5]}

    if apply and candidates:
        # Cross-skill load via lib.skill_loader (skill dir uses kebab-case,
        # which is not a valid Python identifier).
        run_capture = load_skill_module("memory-capture", "capture").run_capture
        stored = []
        for c in candidates:
            r = run_capture(config, content=c["content"], memory_type=c["type"], title=c["title"])
            if not r.get("error"):
                stored.append(r)
        result["stored"] = stored

    return result


if __name__ == "__main__":
    from lib.config import load_config
    import json
    config = load_config()
    f = sys.argv[1] if len(sys.argv) > 1 else "session.json"
    with open(f) as fp:
        data = json.load(fp)
    result = run_commit(config, data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
