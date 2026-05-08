"""
memory-admin skill — Backup, restore, dedupe, prune, stats, audit.
"""
import sys, os, json as _json, datetime, re
# Plugin root is three levels up: skills/<skill>/scripts/<file>.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from lib.config import Config
from lib.adapter_factory import get_adapter
from lib.sensitive_detector import scan
from lib.formatter import format_stats


def _memories_from(result: dict) -> list:
    """Extract memory list from a normalised AdapterResponse dict."""
    if not isinstance(result, dict) or not result.get("ok"):
        return []
    data = result.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("memories", "results", "items"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def _parse_older_than(expr: str) -> datetime.datetime | None:
    """
    Parse a relative time expression like '180d', '30d', '6m', '1y', '24h'
    and return the UTC datetime that far back from now.

    Supported units: h (hours), d (days), m (months), y (years).
    Returns None if the expression is unparseable.
    """
    if not expr:
        return None
    m = re.match(r"^\s*(\d+)\s*(h|d|m|y)\s*$", expr.strip().lower())
    if not m:
        return None
    value, unit = int(m.group(1)), m.group(2)
    now = datetime.datetime.now(datetime.timezone.utc)
    if unit == "h":
        return now - datetime.timedelta(hours=value)
    elif unit == "d":
        return now - datetime.timedelta(days=value)
    elif unit == "m":
        # Approximate months as 30 days each
        return now - datetime.timedelta(days=value * 30)
    elif unit == "y":
        # Approximate years as 365 days each
        return now - datetime.timedelta(days=value * 365)
    return None


def run_admin(config: Config, action: str, scope: str = "", output: str = "",
              file: str = "", older_than: str = "", memory_type: str = "",
              status: str = "") -> int:
    adapter = get_adapter(config)
    target_scope = scope or config.user_scope

    if action == "stats":
        result = adapter.browse(scope=target_scope, limit=500)
        memories = _memories_from(result)
        by_type = {}
        by_status = {}
        for m in memories:
            t = m.get("type", "unknown")
            s = m.get("status", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
            by_status[s] = by_status.get(s, 0) + 1
        print(format_stats({"total": len(memories), "by_type": by_type, "by_status": by_status}))

    elif action == "backup":
        result = adapter.browse(scope=target_scope, limit=500)
        memories = _memories_from(result)
        out = output or f"backup_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(out, "w") as f:
            _json.dump({"scope": target_scope, "memories": memories, "backed_up_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")},
                       f, indent=2, ensure_ascii=False)
        print(f"Backed up {len(memories)} memories to {out}")

    elif action == "restore":
        if not file or not os.path.isfile(file):
            print(f"Error: file not found: {file}", file=sys.stderr)
            return 1
        with open(file) as f:
            data = _json.load(f)
        memories = data.get("memories", [])
        restored = 0
        failed = 0
        for m in memories:
            mid = m.get("id")
            payload = {k: v for k, v in m.items() if k != "id"}
            result = adapter.write(payload, scope=data.get("scope", target_scope))
            if result.get("ok"):
                restored += 1
            else:
                failed += 1
                err = result.get("error", "unknown error")
                print(f"  WARN: Failed to restore [{mid or '?'}]: {err}", file=sys.stderr)
        print(f"Restored {restored}/{len(memories)} memories ({failed} failed)")

    elif action == "dedupe":
        result = adapter.browse(scope=target_scope, limit=500)
        memories = _memories_from(result)
        # Simple dedupe: same title + type = keep newest
        seen = {}
        dupes = []
        for m in memories:
            key = f"{m.get('type','')}:{m.get('title','')[:60]}".lower()
            if key in seen:
                # Keep the newer one
                old = seen[key]
                old_time = old.get("updated_at", old.get("created_at", ""))
                new_time = m.get("updated_at", m.get("created_at", ""))
                if new_time > old_time:
                    dupes.append(old)
                    seen[key] = m
                else:
                    dupes.append(m)
            else:
                seen[key] = m
        # Hard-delete duplicates instead of leaving "status=deleted"
        # tombstones (which still appeared in browse / search and grew
        # storage indefinitely — see EVAL.md §2.4).
        deleted = 0
        for d in dupes:
            mid = d.get("id", "")
            if not mid:
                continue
            res = adapter.delete(mid)
            if res.get("ok"):
                deleted += 1
            else:
                err = res.get("error", "unknown error")
                print(f"  WARN: dedupe could not delete [{mid}]: {err}", file=sys.stderr)
        print(f"Found {len(dupes)} duplicate memories, hard-deleted {deleted}")

    elif action == "prune":
        result = adapter.browse(scope=target_scope, limit=500)
        memories = _memories_from(result)
        # Filter: if specific status given, use it; otherwise default to deleted+obsolete
        if status:
            targets = [m for m in memories if m.get("status") == status]
        else:
            targets = [m for m in memories if m.get("status") in ("deleted", "obsolete")]
        # Filter by age if --older-than specified
        cutoff = _parse_older_than(older_than)
        if cutoff:
            cutoff_iso = cutoff.isoformat().replace("+00:00", "Z")
            before_count = len(targets)
            targets = [
                m for m in targets
                if (m.get("updated_at") or m.get("created_at") or "") < cutoff_iso
            ]
            print(f"Age filter (--older-than {older_than}): {before_count} → {len(targets)} candidates")
        pruned = 0
        for m in targets:
            mid = m.get("id", "")
            if mid:
                adapter.delete(mid)
                pruned += 1
        print(f"Pruned {pruned} memories")

    elif action == "audit":
        result = adapter.browse(scope=target_scope, limit=500)
        memories = _memories_from(result)
        flagged = []
        for m in memories:
            content = m.get("content", "")
            matches = scan(content)
            if matches:
                flagged.append({"id": m.get("id", "?"), "title": m.get("title", ""),
                                "matches": [(mt.pattern_name, mt.matched_text) for mt in matches]})
        if flagged:
            print(f"AUDIT: {len(flagged)} memories contain sensitive data patterns:")
            for f_item in flagged:
                print(f"  [{f_item['id']}] {f_item['title']}")
                for pname, ptext in f_item['matches']:
                    print(f"    - {pname}: {ptext}")
        else:
            print("AUDIT: No sensitive data patterns found in stored memories.")

    adapter.close()
    return 0
