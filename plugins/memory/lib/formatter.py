"""
OpenViking Memory Skill Suite — Output formatter.
Formats memory results for Agent context injection and human display.
"""
from typing import Any


def format_recall_block(memories: list[dict], header: str = "Relevant OpenViking Memory") -> str:
    """
    Format recalled memories as an injectable context block for Agents.
    Output looks like:
    [Relevant OpenViking Memory]
    - Project: ...
    - Preference: ...
    [/Relevant OpenViking Memory]
    """
    if not memories:
        return ""
    lines = [f"[{header}]"]
    for m in memories:
        mtype = m.get("type", "unknown").replace("_", " ").title()
        summary = m.get("summary") or m.get("content", "")
        title = m.get("title", "")
        if title and summary:
            lines.append(f"- {mtype}: {title} — {summary}")
        elif summary:
            lines.append(f"- {mtype}: {summary}")
        elif title:
            lines.append(f"- {mtype}: {title}")
    lines.append(f"[/{header}]")
    return "\n".join(lines)


def format_doctor_report(results: dict) -> str:
    """Format doctor check results as a human-readable report."""
    lines = ["OpenViking Memory Doctor", ""]
    meta = results.get("meta", {})
    if meta:
        lines.append(f"Mode: {meta.get('mode', 'standard')}")
        lines.append(f"Endpoint: {meta.get('endpoint', 'unknown')}")
        lines.append(f"Tenant: {meta.get('tenant', 'unknown')}")
        lines.append(f"User: {meta.get('user', 'unknown')}")
        lines.append(f"Agent: {meta.get('agent', 'unknown')}")
        lines.append("")

    checks = results.get("checks", [])
    for c in checks:
        status = c.get("status", "unknown")
        name = c.get("name", "")
        if status == "pass":
            lines.append(f"✅ {name}")
        elif status == "warn":
            lines.append(f"⚠️  {name}")
            detail = c.get("detail", "")
            if detail:
                lines.append(f"   → {detail}")
        elif status == "fail":
            lines.append(f"❌ {name}")
            detail = c.get("detail", "")
            if detail:
                lines.append(f"   → {detail}")

    warnings = results.get("warnings", [])
    if warnings:
        lines.append("")
        lines.append("⚠️  Warnings:")
        for w in warnings:
            lines.append(f"  - {w}")

    errors = results.get("errors", [])
    if errors:
        lines.append("")
        lines.append("❌ Errors:")
        for e in errors:
            lines.append(f"  - {e}")

    result = results.get("result", "UNKNOWN")
    lines.append("")
    lines.append(f"Result: {result}")
    return "\n".join(lines)


def format_commit_candidates(candidates: list[dict], discarded: list[dict] | None = None) -> str:
    """Format commit candidate memories for display."""
    lines = ["Memory Commit Candidates", ""]
    for i, c in enumerate(candidates, 1):
        rec = "✅ RECOMMENDED" if c.get("recommended") else "⬜ optional"
        lines.append(f"{i}. [{c.get('type', 'unknown')}] {c.get('title', 'Untitled')}  ({rec})")
        lines.append(f"   Content: {c.get('content', '')[:120]}")
        reason = c.get("reason", "")
        if reason:
            lines.append(f"   Reason: {reason}")
        lines.append("")

    if discarded:
        lines.append("Discarded:")
        for d in discarded:
            lines.append(f"  - {d.get('content', '')[:80]}: {d.get('reason', '')}")
        lines.append("")

    return "\n".join(lines)


def format_memory_list(memories: list[dict]) -> str:
    """Format a list of memories for browsing."""
    if not memories:
        return "(no memories found)"
    lines = []
    for m in memories:
        mid = m.get("id", "?")
        mtype = m.get("type", "?")
        title = m.get("title", "Untitled")
        status = m.get("status", "active")
        updated = m.get("updated_at", "")
        lines.append(f"[{mid}] ({mtype}) {title} [{status}] {updated}")
    return "\n".join(lines)


def format_memory_detail(m: dict) -> str:
    """Format a single memory for detailed display."""
    lines = []
    lines.append(f"ID:        {m.get('id', '?')}")
    lines.append(f"Type:      {m.get('type', '?')}")
    lines.append(f"Title:     {m.get('title', 'Untitled')}")
    lines.append(f"Status:    {m.get('status', 'active')}")
    lines.append(f"Confidence:{m.get('confidence', '?')}")
    lines.append(f"Scope:     {m.get('scope', '?')}")
    lines.append(f"Created:   {m.get('created_at', '?')}")
    lines.append(f"Updated:   {m.get('updated_at', '?')}")
    lines.append("")
    lines.append(m.get("content", ""))
    tags = m.get("tags", [])
    if tags:
        lines.append(f"\nTags: {', '.join(tags)}")
    return "\n".join(lines)


def format_stats(stats: dict) -> str:
    """Format memory statistics."""
    lines = ["Memory Statistics", ""]
    lines.append(f"Total memories: {stats.get('total', 0)}")
    by_type = stats.get("by_type", {})
    if by_type:
        lines.append("By type:")
        for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"  {t}: {count}")
    by_status = stats.get("by_status", {})
    if by_status:
        lines.append("By status:")
        for s, count in sorted(by_status.items(), key=lambda x: -x[1]):
            lines.append(f"  {s}: {count}")
    return "\n".join(lines)
