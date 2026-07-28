#!/usr/bin/env python3
"""Smoke tests for apple-icon-studio's two scripts.

    python3 tests/test_apple_icon_studio.py

The tests that matter most here are the SILENT-FAILURE ones:

  * a UI label added to strings-en.json but not strings-zh.json — without the
    drift check, the zh brief renders a hole where the en brief renders a label
  * a stated SCORE_FINAL that disagrees with the weighted formula — the number a
    client reads must be the number the rubric produces
  * a partial render being left on disk after a validation failure — a brief with
    {{PLACEHOLDER}} in it is very easy to send to someone by accident

Pure stdlib. No network. Everything runs in a temp directory.
"""
import copy
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
RENDER = SKILL / "scripts" / "render_icon_brief.py"
MAKE_SET = SKILL / "scripts" / "make_icon_set.py"
EXAMPLE = SKILL / "references" / "example-brief.json"
TEMPLATE = SKILL / "templates" / "icon-brief-template.html"
STRINGS_EN = SKILL / "templates" / "strings-en.json"
STRINGS_ZH = SKILL / "templates" / "strings-zh.json"

sys.path.insert(0, str(SKILL / "scripts"))
import render_icon_brief as rib  # noqa: E402

PASSED, FAILED = [], []


def check(name, condition, detail=""):
    if condition:
        PASSED.append(name)
        print(f"  ok   {name}")
    else:
        FAILED.append((name, detail))
        print(f"  FAIL {name}" + (f" — {detail}" if detail else ""))


def run_render(data_path, out_dir):
    return subprocess.run(
        [sys.executable, str(RENDER), "--data", str(data_path), "--out-dir", str(out_dir)],
        capture_output=True,
        text=True,
    )


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def make_png(path, size, colour=(64, 96, 160, 255)):
    """Write a real PNG without any imaging dependency."""
    raw = b"".join(
        b"\x00" + bytes(colour) * size for _ in range(size)
    )

    def chunk(tag, payload):
        body = tag + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


# ---------------------------------------------------------------- static files
def test_static():
    print("\nstatic files")
    en = json.loads(STRINGS_EN.read_text(encoding="utf-8"))
    zh = json.loads(STRINGS_ZH.read_text(encoding="utf-8"))

    check("strings files have identical key sets", set(en) == set(zh),
          f"en-only={sorted(set(en) - set(zh))} zh-only={sorted(set(zh) - set(en))}")
    check("strings are non-empty", all(str(v).strip() for v in en.values())
          and all(str(v).strip() for v in zh.values()))
    check("en declares lang=en", en["UI_HTML_LANG"] == "en")
    check("zh declares lang=zh-CN", zh["UI_HTML_LANG"] == "zh-CN")

    tmpl = TEMPLATE.read_text(encoding="utf-8")
    ui_in_template = {k for k in rib.PLACEHOLDER_RE.findall(tmpl) if k.startswith("UI_")}
    check("every UI_ placeholder in the template has a string",
          ui_in_template <= set(en), f"missing={sorted(ui_in_template - set(en))}")
    check("every string is used by the template",
          set(en) <= ui_in_template, f"unused={sorted(set(en) - ui_in_template)}")

    repeats = set(rib.REPEAT_RE.findall(tmpl) and
                  [m[0] for m in rib.REPEAT_RE.findall(tmpl)])
    check("template declares the three repeat blocks",
          repeats == {"METAPHORS", "PALETTE", "REJECTIONS"}, f"got={sorted(repeats)}")


# ---------------------------------------------------------------- happy path
def test_render_example(tmp):
    print("\nrender: example-brief.json")
    out = tmp / "happy"
    res = run_render(EXAMPLE, out)
    check("exits 0", res.returncode == 0, res.stderr.strip())

    files = sorted(p.name for p in out.glob("*.html")) if out.exists() else []
    check("writes both languages",
          files == ["icon-brief-continuum-en.html", "icon-brief-continuum-zh.html"],
          str(files))
    if not files:
        return

    for lang in ("en", "zh"):
        html = (out / f"icon-brief-continuum-{lang}.html").read_text(encoding="utf-8")
        check(f"[{lang}] no unresolved placeholders", "{{" not in html)
        check(f"[{lang}] no leftover repeat markers", "REPEAT:" not in html)
        check(f"[{lang}] all 11 rejections rendered", html.count('class="rej-row"') == 11)
        check(f"[{lang}] all 10 metaphors rendered", html.count('<td class="num">') == 60)
        check(f"[{lang}] 3 palette swatches rendered", html.count('class="sw"') == 3)
        check(f"[{lang}] cross-links to the other language",
              f"icon-brief-continuum-{'zh' if lang == 'en' else 'en'}.html" in html)

    en_html = (out / "icon-brief-continuum-en.html").read_text(encoding="utf-8")
    zh_html = (out / "icon-brief-continuum-zh.html").read_text(encoding="utf-8")
    check("en declares lang=en", '<html lang="en">' in en_html)
    check("zh declares lang=zh-CN", '<html lang="zh-CN">' in zh_html)


# ---------------------------------------------------------------- validation
def test_validation(tmp):
    print("\nvalidation (each must fail AND write nothing)")
    base = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    cases = {
        "missing content key": lambda d: d["en"].pop("BRAND_ESSENCE"),
        "score out of range": lambda d: d["shared"].__setitem__("SCORE_APPLE", 140),
        "score not an integer": lambda d: d["shared"].__setitem__("SCORE_MATERIAL", "high"),
        "final disagrees with formula": lambda d: d["shared"].__setitem__("SCORE_FINAL", 99.0),
        "final below ship threshold": lambda d: (
            d["shared"].update(
                {k: 70 for k in rib.SCORE_KEYS}, SCORE_FINAL=70.0
            )
        ),
        "fewer than 10 metaphors": lambda d: d["en"].__setitem__(
            "METAPHORS", d["en"]["METAPHORS"][:8]
        ),
        "not exactly 3 kept": lambda d: d["en"]["METAPHORS"][0].__setitem__(
            "VERDICT_CLASS", "kept"
        ),
        "metaphor total does not add up": lambda d: d["en"]["METAPHORS"][0].__setitem__(
            "TOTAL", 99
        ),
        "metaphor sub-score out of range": lambda d: d["en"]["METAPHORS"][0].__setitem__(
            "DIST", 42
        ),
        "not all 11 rejections logged": lambda d: d["en"].__setitem__(
            "REJECTIONS", d["en"]["REJECTIONS"][:9]
        ),
        "invalid rejection status": lambda d: d["en"]["REJECTIONS"][0].__setitem__(
            "STATUS", "maybe"
        ),
        "four-colour palette": lambda d: d["en"]["PALETTE"].append(
            {"HEX": "#123456", "NAME": "x", "SHARE": "5%", "ROLE": "y"}
        ),
        "malformed hex": lambda d: d["en"]["PALETTE"][0].__setitem__("HEX", "0F172A"),
        "missing language object": lambda d: d.pop("zh"),
    }

    for name, mutate in cases.items():
        data = copy.deepcopy(base)
        mutate(data)
        path = tmp / "bad.json"
        write_json(path, data)
        out = tmp / f"out-{abs(hash(name))}"
        res = run_render(path, out)
        wrote = list(out.glob("*.html")) if out.exists() else []
        check(f"rejects: {name}", res.returncode != 0, "exited 0")
        check(f"writes nothing: {name}", not wrote, f"wrote {[p.name for p in wrote]}")


def test_string_drift(tmp):
    """The silent-failure case: a label added to one language only."""
    print("\nvalidation: UI string drift")
    sandbox = tmp / "skill-copy"
    shutil.copytree(SKILL, sandbox, ignore=shutil.ignore_patterns("tmp-out", "__pycache__"))

    en = json.loads((sandbox / "templates" / "strings-en.json").read_text(encoding="utf-8"))
    en["UI_BRAND_NEW_LABEL"] = "Something"
    (sandbox / "templates" / "strings-en.json").write_text(
        json.dumps(en, ensure_ascii=False), encoding="utf-8"
    )

    out = tmp / "drift-out"
    res = subprocess.run(
        [
            sys.executable,
            str(sandbox / "scripts" / "render_icon_brief.py"),
            "--data", str(EXAMPLE),
            "--out-dir", str(out),
        ],
        capture_output=True,
        text=True,
    )
    check("rejects a label present in en but not zh", res.returncode != 0)
    check("names the drifted key", "UI_BRAND_NEW_LABEL" in res.stderr, res.stderr.strip())
    check("writes nothing on drift", not (out.exists() and list(out.glob("*.html"))))


# ---------------------------------------------------------------- formula
def test_formula():
    print("\nweighted score formula")
    perfect = {k: 100 for k in rib.SCORE_KEYS}
    check("all 100 → 100.0", rib.weighted_final(perfect) == 100.0)

    weighted = {k: 60 for k in rib.SCORE_KEYS}
    weighted["SCORE_RECOGNITION"] = 100
    weighted["SCORE_SCALABILITY"] = 100
    # (60*4 + 100*1.5 + 100*1.5) / 7 = (240 + 300) / 7 = 77.1
    check("Recognition and Scalability weigh 1.5x",
          rib.weighted_final(weighted) == 77.1, str(rib.weighted_final(weighted)))

    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))["shared"]
    check("example-brief's stated final matches the formula",
          abs(rib.weighted_final(example) - float(example["SCORE_FINAL"])) <= 0.5,
          f"formula={rib.weighted_final(example)} stated={example['SCORE_FINAL']}")


# ---------------------------------------------------------------- icon set
def test_make_icon_set(tmp):
    print("\nmake_icon_set.py")

    non_square = tmp / "wide.png"
    make_png(non_square, 8)
    # hand-patch the IHDR to claim a non-square size
    blob = bytearray(non_square.read_bytes())
    blob[16:24] = struct.pack(">II", 16, 8)
    non_square.write_bytes(bytes(blob))
    res = subprocess.run(
        [sys.executable, str(MAKE_SET), "--input", str(non_square), "--out-dir", str(tmp / "ns")],
        capture_output=True, text=True,
    )
    check("rejects non-square master", res.returncode != 0)
    check("says why it rejected non-square", "square" in res.stderr.lower())

    small = tmp / "small.png"
    make_png(small, 512)
    res = subprocess.run(
        [sys.executable, str(MAKE_SET), "--input", str(small), "--out-dir", str(tmp / "sm")],
        capture_output=True, text=True,
    )
    check("refuses to upscale a sub-1024 master", res.returncode != 0)
    check("says why it refused to upscale", "1024" in res.stderr)

    res = subprocess.run(
        [sys.executable, str(MAKE_SET), "--input", str(small),
         "--out-dir", str(tmp / "bad"), "--targets", "android"],
        capture_output=True, text=True,
    )
    check("rejects an unknown target", res.returncode != 0)

    master = tmp / "master.png"
    make_png(master, 1024)
    out = tmp / "icons"
    res = subprocess.run(
        [sys.executable, str(MAKE_SET), "--input", str(master), "--out-dir", str(out)],
        capture_output=True, text=True,
    )
    if res.returncode != 0 and "no resize backend" in res.stderr:
        print("  skip generation tests — no sips and no Pillow on this machine")
        return

    check("generates without error", res.returncode == 0, res.stderr.strip())
    appiconset = out / "AppIcon.appiconset"
    check("creates AppIcon.appiconset", appiconset.is_dir())

    contents_path = appiconset / "Contents.json"
    check("writes Contents.json", contents_path.is_file())
    if contents_path.is_file():
        contents = json.loads(contents_path.read_text(encoding="utf-8"))
        check("Contents.json parses and lists every image",
              len(contents["images"]) == len(rib_ios_count()), str(len(contents["images"])))
        missing = [
            img["filename"]
            for img in contents["images"]
            if not (appiconset / img["filename"]).is_file()
        ]
        check("every filename in Contents.json exists on disk", not missing, str(missing))
        check("includes the iOS 26 single-size 1024 entry",
              any(i.get("size") == "1024x1024" for i in contents["images"]))

    iconset = out / "AppIcon.iconset"
    check("creates AppIcon.iconset with 10 images",
          iconset.is_dir() and len(list(iconset.glob("*.png"))) == 10)
    check("creates the web favicon set",
          (out / "web" / "favicon-32.png").is_file()
          and (out / "web" / "site.webmanifest").is_file())


def rib_ios_count():
    sys.path.insert(0, str(SKILL / "scripts"))
    import make_icon_set as mis

    return [None] * (len(mis.IOS_LEGACY) + 1)


def main():
    print("apple-icon-studio smoke tests")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_static()
        test_render_example(tmp)
        test_formula()
        test_validation(tmp)
        test_string_drift(tmp)
        test_make_icon_set(tmp)

    total = len(PASSED) + len(FAILED)
    print(f"\n{len(PASSED)}/{total} checks passed")
    if FAILED:
        print("\nfailures:")
        for name, detail in FAILED:
            print(f"  - {name}" + (f": {detail}" if detail else ""))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
