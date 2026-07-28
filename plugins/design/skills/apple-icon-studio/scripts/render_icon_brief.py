#!/usr/bin/env python3
"""Render the bilingual Apple Icon Studio design brief from one JSON data file.

Usage:
    python3 render_icon_brief.py --data brief.json --out-dir ./output

Data shape (see references/example-brief.json for a complete working example):

{
  "slug": "acme-notes",
  "date": "2026-07-29",
  "shared": { "SCORE_APPLE": 93, ... },   # values identical across languages
  "en":     { "PRODUCT": "Acme Notes", ..., "METAPHORS": [ {...}, ... ] },
  "zh":     { "PRODUCT": "Acme 笔记", ..., "METAPHORS": [ {...}, ... ] }
}

Static UI chrome lives in templates/strings-{en,zh}.json, so there is exactly ONE
HTML template and label drift between languages is impossible by construction.

Repeat blocks in the template are delimited by:
    <!--REPEAT:NAME--> ... <!--/REPEAT:NAME-->
and are driven by a list of dicts under that key in the language data.

The renderer VALIDATES BEFORE IT WRITES. If any check fails for either language,
nothing is written to disk — a half-filled brief is worse than no brief.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "templates" / "icon-brief-template.html"
STRINGS = {
    "en": SKILL_DIR / "templates" / "strings-en.json",
    "zh": SKILL_DIR / "templates" / "strings-zh.json",
}

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
REPEAT_RE = re.compile(
    r"<!--REPEAT:([A-Z0-9_]+)-->(.*?)<!--/REPEAT:\1-->", re.DOTALL
)

SCORE_KEYS = (
    "SCORE_APPLE",
    "SCORE_RECOGNITION",
    "SCORE_MATERIAL",
    "SCORE_MEMORABILITY",
    "SCORE_SCALABILITY",
    "SCORE_EMOTION",
)
# Recognition and Scalability are weighted 1.5x — see references/CRITIQUE_GUIDE.md.
SCORE_WEIGHTS = {
    "SCORE_APPLE": 1.0,
    "SCORE_RECOGNITION": 1.5,
    "SCORE_MATERIAL": 1.0,
    "SCORE_MEMORABILITY": 1.0,
    "SCORE_SCALABILITY": 1.5,
    "SCORE_EMOTION": 1.0,
}
SHIP_THRESHOLD = 85.0
VALID_STATUS = {"pass", "note", "fail"}
METAPHOR_SCORE_FIELDS = ("DIST", "SMALL", "FIT", "LONG")


def weighted_final(values: dict) -> float:
    """Final = sum(axis * weight) / sum(weights), per CRITIQUE_GUIDE.md."""
    total = sum(float(values[k]) * SCORE_WEIGHTS[k] for k in SCORE_KEYS)
    return round(total / sum(SCORE_WEIGHTS.values()), 1)


def validate(values: dict, lang: str) -> list:
    """Check the invariants SKILL.md documents but the template cannot enforce."""
    problems = []
    p = problems.append

    # --- scorecard ---------------------------------------------------------
    for key in SCORE_KEYS:
        raw = values.get(key)
        if raw is None:
            continue  # absence is caught by the unresolved-placeholder check
        try:
            val = int(str(raw).strip())
        except ValueError:
            p(f"[{lang}] {key} must be an integer 0-100, got {raw!r}")
            continue
        if not 0 <= val <= 100:
            p(f"[{lang}] {key} must be within 0-100, got {val}")

    if all(str(values.get(k, "")).strip().isdigit() for k in SCORE_KEYS):
        expected = weighted_final(values)
        try:
            stated = float(str(values.get("SCORE_FINAL", "")).strip())
        except ValueError:
            p(f"[{lang}] SCORE_FINAL must be a number, got {values.get('SCORE_FINAL')!r}")
        else:
            if abs(stated - expected) > 0.5:
                p(
                    f"[{lang}] SCORE_FINAL is {stated} but the weighted formula "
                    f"(Recognition x1.5, Scalability x1.5) gives {expected}"
                )
            elif stated < SHIP_THRESHOLD:
                p(
                    f"[{lang}] SCORE_FINAL {stated} is below the {SHIP_THRESHOLD} ship "
                    f"threshold — iterate (see references/CRITIQUE_GUIDE.md) before "
                    f"producing a brief"
                )

    # --- metaphor kill discipline -----------------------------------------
    metaphors = values.get("METAPHORS")
    if isinstance(metaphors, list):
        if len(metaphors) < 10:
            p(f"[{lang}] METAPHORS must contain at least 10 entries, got {len(metaphors)}")
        kept = [m for m in metaphors if str(m.get("VERDICT_CLASS", "")).strip() == "kept"]
        if len(kept) != 3:
            p(
                f"[{lang}] exactly 3 metaphors must have VERDICT_CLASS 'kept' "
                f"(kill 7, keep 3); got {len(kept)}"
            )
        for i, m in enumerate(metaphors, 1):
            for field in METAPHOR_SCORE_FIELDS:
                raw = m.get(field)
                try:
                    val = int(str(raw).strip())
                except (ValueError, TypeError):
                    p(f"[{lang}] METAPHORS[{i}].{field} must be an integer 0-10, got {raw!r}")
                    continue
                if not 0 <= val <= 10:
                    p(f"[{lang}] METAPHORS[{i}].{field} must be within 0-10, got {val}")
            try:
                stated = int(str(m.get("TOTAL", "")).strip())
            except (ValueError, TypeError):
                p(f"[{lang}] METAPHORS[{i}].TOTAL must be an integer")
            else:
                parts = []
                for field in METAPHOR_SCORE_FIELDS:
                    try:
                        parts.append(int(str(m.get(field, "")).strip()))
                    except (ValueError, TypeError):
                        parts = None
                        break
                if parts is not None and sum(parts) != stated:
                    p(
                        f"[{lang}] METAPHORS[{i}].TOTAL is {stated} but "
                        f"{'+'.join(str(x) for x in parts)} = {sum(parts)}"
                    )

    # --- rejection log -----------------------------------------------------
    rejections = values.get("REJECTIONS")
    if isinstance(rejections, list):
        if len(rejections) != 11:
            p(
                f"[{lang}] REJECTIONS must contain all 11 standard rejections "
                f"(R1-R11), got {len(rejections)} — passes must be recorded too"
            )
        for i, r in enumerate(rejections, 1):
            status = str(r.get("STATUS", "")).strip()
            if status not in VALID_STATUS:
                p(
                    f"[{lang}] REJECTIONS[{i}].STATUS must be one of "
                    f"{'/'.join(sorted(VALID_STATUS))}, got {status!r}"
                )

    # --- palette -----------------------------------------------------------
    palette = values.get("PALETTE")
    if isinstance(palette, list):
        if not 2 <= len(palette) <= 3:
            p(
                f"[{lang}] PALETTE must have 2-3 entries (no colour overload), "
                f"got {len(palette)}"
            )
        for i, sw in enumerate(palette, 1):
            hex_val = str(sw.get("HEX", "")).strip()
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", hex_val):
                p(f"[{lang}] PALETTE[{i}].HEX must be #RRGGBB, got {hex_val!r}")

    return problems


def render_repeats(template: str, values: dict, lang: str) -> tuple:
    """Expand <!--REPEAT:NAME--> blocks. Returns (html, problems)."""
    problems = []

    def expand(match):
        name, body = match.group(1), match.group(2)
        rows = values.get(name)
        if not isinstance(rows, list):
            problems.append(
                f"[{lang}] template has a REPEAT:{name} block but the data has no "
                f"'{name}' list"
            )
            return ""
        out = []
        for row in rows:
            chunk = body
            for key, val in sorted(row.items(), key=lambda kv: -len(kv[0])):
                chunk = chunk.replace("{{" + key + "}}", html.escape(str(val)))
            out.append(chunk)
        return "".join(out)

    return REPEAT_RE.sub(expand, template), problems


def render(template: str, values: dict, lang: str, other_href: str) -> tuple:
    """Render one language. Returns (html, problems)."""
    merged = dict(values)
    merged["OTHER_LANG_HREF"] = other_href

    out, problems = render_repeats(template, merged, lang)

    scalars = {
        k: v for k, v in merged.items() if not isinstance(v, (list, dict))
    }
    for key, val in sorted(scalars.items(), key=lambda kv: -len(kv[0])):
        out = out.replace("{{" + key + "}}", html.escape(str(val)))

    unresolved = sorted(set(PLACEHOLDER_RE.findall(out)))
    if unresolved:
        problems.append(
            f"[{lang}] {len(unresolved)} unresolved placeholder(s): "
            + ", ".join(unresolved)
        )
    return out, problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", required=True, type=Path, help="path to the brief JSON")
    ap.add_argument("--out-dir", required=True, type=Path, help="output directory")
    args = ap.parse_args()

    try:
        data = json.loads(args.data.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {args.data}: {exc}", file=sys.stderr)
        return 2

    slug = str(data.get("slug", "icon")).strip() or "icon"
    shared = data.get("shared", {})
    if not isinstance(shared, dict):
        print("error: 'shared' must be an object", file=sys.stderr)
        return 2

    template = TEMPLATE.read_text(encoding="utf-8")

    # Both string files must expose exactly the same keys, or one language
    # silently renders a hole where the other renders a label.
    strings = {}
    for lang, path in STRINGS.items():
        strings[lang] = json.loads(path.read_text(encoding="utf-8"))
    only_en = set(strings["en"]) - set(strings["zh"])
    only_zh = set(strings["zh"]) - set(strings["en"])
    if only_en or only_zh:
        print(
            "error: UI string files have drifted — "
            f"en-only: {sorted(only_en) or 'none'}; zh-only: {sorted(only_zh) or 'none'}",
            file=sys.stderr,
        )
        return 1

    outputs, all_problems = {}, []
    for lang in ("en", "zh"):
        lang_data = data.get(lang)
        if not isinstance(lang_data, dict):
            all_problems.append(f"[{lang}] missing or malformed '{lang}' object")
            continue
        values = {
            **strings[lang],
            **shared,
            **lang_data,
            "DATE": data.get("date", ""),
        }
        all_problems.extend(validate(values, lang))

        other = "zh" if lang == "en" else "en"
        out, problems = render(
            template, values, lang, f"icon-brief-{slug}-{other}.html"
        )
        all_problems.extend(problems)
        outputs[lang] = out

    if all_problems:
        print("error: brief did not validate — nothing written.", file=sys.stderr)
        for problem in all_problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for lang, out in outputs.items():
        path = args.out_dir / f"icon-brief-{slug}-{lang}.html"
        path.write_text(out, encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
