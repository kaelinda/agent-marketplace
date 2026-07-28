#!/usr/bin/env python3
"""Smoke tests for render_teardown.py — run with `python3 tests/test_render_teardown.py`.

Guards the invariants that are easy to break when editing the templates:
  1. EN and ZH templates expose the exact same placeholder set.
  2. The bundled example fixture covers every placeholder (so it stays a valid stub).
  3. A clean render produces two files with no leftover {{...}}.
  4. Bad input (AI meter, out-of-range bars, missing keys) fails and writes nothing.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "render_teardown.py"
TMPL_EN = SKILL_DIR / "templates" / "product-teardown-template-en.html"
TMPL_ZH = SKILL_DIR / "templates" / "product-teardown-template-zh.html"
FIXTURE = SKILL_DIR / "references" / "example-data.json"

PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_★☆]+)\}\}")
# {{PLACEHOLDER}} is a doc comment in the template header, not a real field.
# The lang-switcher keys are injected by the script, not supplied in the data file.
NOT_DATA_KEYS = {"PLACEHOLDER", "LANG_EN_HREF", "LANG_ZH_HREF", "ACTIVE_IF_EN", "ACTIVE_IF_ZH"}

failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{(' — ' + detail) if detail else ''}")
        failures.append(name)


def keys_of(path):
    return set(PLACEHOLDER_RE.findall(path.read_text(encoding="utf-8"))) - {"PLACEHOLDER"}


def run(data, out_dir):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
        data_path = fh.name
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", data_path, "--out-dir", str(out_dir)],
        capture_output=True, text=True,
    )
    Path(data_path).unlink()
    return proc


print("templates")
en_keys, zh_keys = keys_of(TMPL_EN), keys_of(TMPL_ZH)
check("EN and ZH placeholder sets are identical", en_keys == zh_keys,
      f"only-EN={sorted(en_keys - zh_keys)} only-ZH={sorted(zh_keys - en_keys)}")
check("EN template declares lang=\"en\"", '<html lang="en">' in TMPL_EN.read_text(encoding="utf-8"))
check("ZH template declares lang=\"zh-CN\"", '<html lang="zh-CN">' in TMPL_ZH.read_text(encoding="utf-8"))

print("fixture")
fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
required = en_keys - NOT_DATA_KEYS
for lang in ("en", "zh"):
    supplied = set(fixture[lang]) | set(fixture.get("shots", {}))
    check(f"fixture covers every placeholder ({lang})", required <= supplied,
          f"missing={sorted(required - supplied)}")

print("render · happy path")
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    proc = run(fixture, out)
    check("exits 0", proc.returncode == 0, proc.stderr.strip())
    files = sorted(out.glob("*.html"))
    check("writes exactly 2 files", len(files) == 2, str(files))
    for f in files:
        body = f.read_text(encoding="utf-8")
        leftovers = set(PLACEHOLDER_RE.findall(body)) - {"PLACEHOLDER"}
        check(f"no unresolved placeholders in {f.name}", not leftovers, str(sorted(leftovers)))

print("render · rejects bad input")
cases = {
    "two AI meter stages active": lambda d: d["en"].update(ACTIVE_IF_EMBEDDED="active"),
    "no AI meter stage active": lambda d: d["en"].update(ACTIVE_IF_ASSISTIVE=""),
    "bar out of 0-100 range": lambda d: d["zh"].update(TTV_BAR="150"),
    "bar not an integer": lambda d: d["zh"].update(COG_BAR="high"),
    "missing placeholder key": lambda d: d["en"].pop("FINAL_WINS", None),
}
for name, mutate in cases.items():
    bad = json.loads(json.dumps(fixture))
    mutate(bad)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "nested"
        proc = run(bad, out)
        check(f"{name} → exits non-zero", proc.returncode != 0)
        check(f"{name} → writes nothing", not out.exists() or not list(out.glob("*.html")))

print()
if failures:
    print(f"FAILED ({len(failures)}): {', '.join(failures)}")
    sys.exit(1)
print("all checks passed")
