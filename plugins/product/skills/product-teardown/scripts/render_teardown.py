#!/usr/bin/env python3
"""Fill the EN + ZH product-teardown HTML templates from a single JSON data file.

Usage:
    python3 render_teardown.py --data teardown.json --out-dir ./output

The JSON data file must have this shape:

{
  "slug": "linear",
  "date": "2026-07-01",
  "shots": {
    "SHOT_1_URL": "https://...", ... up to SHOT_6_URL
  },
  "en": { "PRODUCT": "Linear", ... all EN placeholder keys ... },
  "zh": { "PRODUCT": "Linear", ... all ZH placeholder keys ... }
}

Every {{PLACEHOLDER}} in the templates must be present as a key in "en" / "zh"
(SHOT_*_URL keys come from the shared "shots" object and are merged in automatically).
Keys are substituted longest-first so prefixes never collide (e.g. SHOT_1_URL vs SHOT_1).
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TMPL_EN = SKILL_DIR / "templates" / "product-teardown-template-en.html"
TMPL_ZH = SKILL_DIR / "templates" / "product-teardown-template-zh.html"

PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_★☆]+)\}\}")

AI_METER_KEYS = ("ACTIVE_IF_ASSISTIVE", "ACTIVE_IF_EMBEDDED", "ACTIVE_IF_AUTONOMOUS")
BAR_KEYS = ("TTV_BAR", "COG_BAR", "DELIGHT_BAR", "TRUST_BAR", "STRUGGLE_BAR")


def validate(values: dict, lang: str) -> list:
    """Check the invariants SKILL.md documents but the templates can't enforce.

    Returns a list of human-readable problems (empty == valid).
    """
    problems = []

    active = [k for k in AI_METER_KEYS if str(values.get(k, "")).strip() == "active"]
    if len(active) != 1:
        problems.append(
            f'[{lang}] exactly one of {"/".join(AI_METER_KEYS)} must be the string "active"; '
            f"got {len(active)} ({', '.join(active) or 'none'})"
        )

    for key in BAR_KEYS:
        raw = values.get(key)
        if raw is None:
            continue  # absence is already caught by the unresolved-placeholder check
        try:
            val = int(str(raw).strip())
        except ValueError:
            problems.append(f"[{lang}] {key} must be an integer 0-100, got {raw!r}")
            continue
        if not 0 <= val <= 100:
            problems.append(f"[{lang}] {key} must be within 0-100, got {val}")

    return problems


def render(template_path: Path, values: dict, shots: dict, lang_hrefs: dict, active_lang: str) -> str:
    html = template_path.read_text(encoding="utf-8")
    v = dict(values)
    v.update(shots)
    v["LANG_EN_HREF"] = lang_hrefs["en"]
    v["LANG_ZH_HREF"] = lang_hrefs["zh"]
    v["ACTIVE_IF_EN"] = "active" if active_lang == "en" else ""
    v["ACTIVE_IF_ZH"] = "active" if active_lang == "zh" else ""

    for key in sorted(v, key=len, reverse=True):
        html = html.replace("{{" + key + "}}", str(v[key]))

    remaining = sorted(set(PLACEHOLDER_RE.findall(html)) - {"PLACEHOLDER"})
    return html, remaining


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", required=True, help="Path to the teardown JSON data file")
    parser.add_argument("--out-dir", default="./output", help="Directory to write the two HTML reports into (default: ./output)")
    args = parser.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    slug = data["slug"]
    date = data["date"]
    ym = date.replace("-", "")[:6]
    shots = data.get("shots", {})

    out_dir = Path(args.out_dir)
    out_en = out_dir / f"product-teardown-{slug}-en-{ym}.html"
    out_zh = out_dir / f"product-teardown-{slug}-zh-{ym}.html"
    lang_hrefs = {"en": out_en.name, "zh": out_zh.name}

    # Render and validate both languages BEFORE writing anything — a half-written pair
    # (or a report with visible {{...}} in it) is worse than no output at all.
    rendered = {}
    problems = []
    for target, tmpl, key, lang in [
        (out_en, TMPL_EN, "en", "en"),
        (out_zh, TMPL_ZH, "zh", "zh"),
    ]:
        if key not in data:
            problems.append(f'data file is missing the "{key}" object')
            continue
        problems.extend(validate(data[key], lang))
        html, remaining = render(tmpl, data[key], shots, lang_hrefs, lang)
        if remaining:
            problems.append(
                f"[{lang}] unresolved placeholders in {target.name}: "
                + ", ".join("{{" + r + "}}" for r in remaining)
            )
        rendered[target] = html

    if problems:
        print("Refusing to write — fix the data file and re-run:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    for target, html in rendered.items():
        target.write_text(html, encoding="utf-8")
        print(f"Wrote: {target}")


if __name__ == "__main__":
    main()
