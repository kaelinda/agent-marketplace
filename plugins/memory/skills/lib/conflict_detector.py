"""
OpenViking Memory Skill Suite — Conflict detector.
Detects contradictory memories that could confuse Agent behavior.
"""
import re
from typing import NamedTuple


class ConflictResult(NamedTuple):
    memory_a: dict
    memory_b: dict
    field: str
    reason: str
    severity: str  # "warn" or "block"


# ── Known contradictory pairs ───────────────────────────────

_OS_CONFLICTS = {
    "centos": "centos", "ubuntu": "ubuntu", "debian": "debian",
    "alpine": "alpine", "macos": "macos", "windows": "windows",
}

_VERSION_PATTERN = re.compile(r'(\w+)[\s-]*(v?\d+[\.\d]*)')


def detect_conflicts(memories: list[dict]) -> list[ConflictResult]:
    """
    Check a list of memories for contradictions.
    Returns list of ConflictResult.
    """
    conflicts: list[ConflictResult] = []

    # Group by type
    by_type: dict[str, list[dict]] = {}
    for m in memories:
        t = m.get("type", "unknown")
        by_type.setdefault(t, []).append(m)

    # Check environment conflicts
    envs = by_type.get("environment", [])
    for i, a in enumerate(envs):
        for b in envs[i + 1:]:
            c = _check_env_conflict(a, b)
            if c:
                conflicts.append(c)

    # Check preference conflicts
    prefs = by_type.get("preference", [])
    for i, a in enumerate(prefs):
        for b in prefs[i + 1:]:
            c = _check_pref_conflict(a, b)
            if c:
                conflicts.append(c)

    # Check project status conflicts
    projects = by_type.get("project", [])
    for i, a in enumerate(projects):
        for b in projects[i + 1:]:
            if a.get("title", "").lower() == b.get("title", "").lower():
                if a.get("status") != b.get("status"):
                    conflicts.append(ConflictResult(
                        memory_a=a, memory_b=b,
                        field="status",
                        reason=f"Same project has different statuses: '{a.get('status')}' vs '{b.get('status')}'",
                        severity="warn",
                    ))

    return conflicts


def _check_env_conflict(a: dict, b: dict) -> ConflictResult | None:
    """Check if two environment memories contradict each other."""
    content_a = (a.get("content", "") + " " + a.get("title", "")).lower()
    content_b = (b.get("content", "") + " " + b.get("title", "")).lower()

    # OS conflict
    os_a = None
    os_b = None
    for os_key in _OS_CONFLICTS:
        if os_key in content_a:
            os_a = os_key
        if os_key in content_b:
            os_b = os_key

    if os_a and os_b and os_a != os_b:
        # Could be different servers — only flag if both seem to describe same context
        if _same_context(a, b):
            return ConflictResult(
                memory_a=a, memory_b=b,
                field="operating_system",
                reason=f"Conflicting OS: '{os_a}' vs '{os_b}' in same context",
                severity="warn",
            )

    return None


def _check_pref_conflict(a: dict, b: dict) -> ConflictResult | None:
    """Check if two preference memories contradict each other."""
    content_a = (a.get("content", "") + " " + a.get("title", "")).lower()
    content_b = (b.get("content", "") + " " + b.get("title", "")).lower()

    # Language preference conflict
    lang_a = None
    lang_b = None
    if "中文" in content_a or "chinese" in content_a:
        lang_a = "chinese"
    if "english" in content_a or "英文" in content_a:
        lang_a = "english"
    if "中文" in content_b or "chinese" in content_b:
        lang_b = "chinese"
    if "english" in content_b or "英文" in content_b:
        lang_b = "english"

    if lang_a and lang_b and lang_a != lang_b:
        if _same_context(a, b):
            return ConflictResult(
                memory_a=a, memory_b=b,
                field="language",
                reason=f"Conflicting language preference: '{lang_a}' vs '{lang_b}'",
                severity="warn",
            )

    return None


def _same_context(a: dict, b: dict) -> bool:
    """
    Heuristic: do two memories describe the same context?
    Checks overlapping tags, entities, or title similarity.
    """
    tags_a = set(t.lower() for t in a.get("tags", []))
    tags_b = set(t.lower() for t in b.get("tags", []))
    if tags_a & tags_b:
        return True

    entities_a = set(e.lower() for e in a.get("entities", []))
    entities_b = set(e.lower() for e in b.get("entities", []))
    if entities_a & entities_b:
        return True

    # Title similarity (simple word overlap)
    words_a = set(a.get("title", "").lower().split())
    words_b = set(b.get("title", "").lower().split())
    if words_a & words_b and len(words_a & words_b) >= 2:
        return True

    return False


def format_conflicts(conflicts: list[ConflictResult]) -> str:
    """Format conflicts for display."""
    if not conflicts:
        return "No conflicts detected."
    lines = [f"Found {len(conflicts)} conflict(s):", ""]
    for i, c in enumerate(conflicts, 1):
        lines.append(f"{i}. [{c.severity.upper()}] {c.field}")
        lines.append(f"   Reason: {c.reason}")
        lines.append(f"   Memory A: [{c.memory_a.get('id', '?')}] {c.memory_a.get('title', '')}")
        lines.append(f"   Memory B: [{c.memory_b.get('id', '?')}] {c.memory_b.get('title', '')}")
        lines.append("")
    return "\n".join(lines)
