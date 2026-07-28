#!/usr/bin/env python3
"""Smoke tests for generate_ui_style.py — run after editing a template or the script.

    python3 tests/test_generate_ui_style.py

Catches the failure modes that are otherwise silent: a placeholder added to a template but
never filled by the script, a validation rule that stopped firing, and a bundle that
renders with visible {{...}} text.
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import generate_ui_style as g  # noqa: E402

EXAMPLE = json.loads((SKILL_DIR / "references" / "example-style.json").read_text(encoding="utf-8"))
SKELETON = json.loads((SKILL_DIR / "references" / "skeleton-style.json").read_text(encoding="utf-8"))

failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        failures.append(name)


def test_example_is_valid():
    errors, warnings = g.validate(EXAMPLE)
    check("example-style.json validates", not errors, "; ".join(errors))
    check("example-style.json has no warnings", not warnings, "; ".join(warnings))


def test_every_template_placeholder_is_filled():
    values = g.build_values(EXAMPLE)
    for tpl in sorted((SKILL_DIR / "templates").glob("*.tpl")):
        keys = set(g.PLACEHOLDER_RE.findall(tpl.read_text(encoding="utf-8")))
        missing = sorted(keys - set(values))
        check(f"{tpl.name}: every placeholder has a value", not missing, ", ".join(missing))


def test_full_generate_writes_bundle():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ui-style"
        rc = g.generate(copy.deepcopy(EXAMPLE), out)
        check("generate() exits 0 on the example", rc == 0)
        expected = {"DESIGN.md", "AGENTS.md", "components.md",
                    "tokens.json", "tokens.css", "style-dna.json"}
        written = {p.name for p in out.glob("*")} if out.exists() else set()
        check("all six bundle files are written", expected <= written, str(sorted(expected - written)))
        for name in sorted(written):
            text = (out / name).read_text(encoding="utf-8")
            check(f"{name} has no leftover placeholder", "{{" not in text)
            check(f"{name} is non-empty", len(text.strip()) > 0)
        css = (out / "tokens.css").read_text(encoding="utf-8")
        check("tokens.css exposes the primary color", "--color-primary: #5E6AD2;" in css)
        check("tokens.css exposes the spacing unit", "--space-unit: 4px;" in css)
        agents = (out / "AGENTS.md").read_text(encoding="utf-8")
        check("AGENTS.md names every component", all(c in agents for c in EXAMPLE["components"]))


def test_invalid_inputs_are_rejected():
    cases = {
        "missing tokens.color role": lambda d: d["tokens"]["color"].pop("primary"),
        "non-color token value": lambda d: d["tokens"]["color"].update(primary="indigo"),
        "visual dial out of range": lambda d: d["style_dna"]["visual"].update(roundness=1.7),
        "bad theme": lambda d: d["style_dna"].update(theme="neon"),
        "bad density": lambda d: d["style_dna"].update(density="airy"),
        "bad slug": lambda d: d.update(slug="Not Kebab"),
        "bad date": lambda d: d["source"].update(date="28/07/2026"),
        "too few components": lambda d: d.update(components={"Button": d["components"]["Button"]}),
        "component missing style": lambda d: d["components"]["Button"].update(style=""),
        "unitless spacing step": lambda d: d["tokens"]["spacing"]["scale"].update({"2": "8"}),
        "missing radius key": lambda d: d["tokens"]["radius"].pop("md"),
        "too few signature moves": lambda d: d["style_dna"].update(signature_moves=["only one"]),
        "bad duration": lambda d: d["tokens"]["motion"]["duration"].update(base="fast"),
        "empty personality item": lambda d: d["style_dna"].update(personality=["minimal", ""]),
    }
    for name, mutate in cases.items():
        data = copy.deepcopy(EXAMPLE)
        mutate(data)
        errors, _ = g.validate(data)
        check(f"rejects: {name}", bool(errors))


def test_low_contrast_warns_and_strict_blocks():
    data = copy.deepcopy(EXAMPLE)
    data["tokens"]["color"]["text_primary"] = "#1A1B1E"  # nearly invisible on #08090A
    errors, warnings = g.validate(data)
    check("low contrast is a warning, not an error", not errors and bool(warnings))
    with tempfile.TemporaryDirectory() as tmp:
        rc_soft = g.generate(copy.deepcopy(data), Path(tmp) / "soft")
        rc_strict = g.generate(copy.deepcopy(data), Path(tmp) / "strict", strict=True)
        check("low contrast still renders by default", rc_soft == 0)
        check("--strict blocks on warnings", rc_strict == 1)
        check("--strict wrote nothing", not (Path(tmp) / "strict").exists())


def test_contrast_math():
    check("contrast(white, black) == 21", round(g.contrast_ratio("#FFFFFF", "#000000"), 1) == 21.0)
    check("contrast is symmetric", g.contrast_ratio("#FFFFFF", "#767676") == g.contrast_ratio("#767676", "#FFFFFF"))
    check("non-hex color returns None", g.contrast_ratio("rgb(0 0 0)", "#FFFFFF") is None)


def test_skeleton_is_a_scaffold_not_a_valid_file():
    errors, _ = g.validate(SKELETON)
    check("skeleton is structurally parseable JSON with the right top-level keys",
          {"slug", "source", "style_dna", "tokens", "components"} <= set(SKELETON))
    check("skeleton fails validation until filled in", bool(errors))


def main():
    for test in (
        test_example_is_valid,
        test_every_template_placeholder_is_filled,
        test_full_generate_writes_bundle,
        test_invalid_inputs_are_rejected,
        test_low_contrast_warns_and_strict_blocks,
        test_contrast_math,
        test_skeleton_is_a_scaffold_not_a_valid_file,
    ):
        print(f"{test.__name__}:")
        test()
    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: {', '.join(failures)}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
