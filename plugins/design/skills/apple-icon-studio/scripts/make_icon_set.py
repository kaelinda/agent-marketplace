#!/usr/bin/env python3
"""Generate platform icon sets from one approved 1024x1024 master PNG.

Usage:
    python3 make_icon_set.py --input master-1024.png --out-dir ./icons
    python3 make_icon_set.py --input master.png --out-dir ./icons --targets ios,macos,web

Targets:
    ios    AppIcon.appiconset/ with a valid Contents.json (single-size 1024 idiom,
           plus the legacy multi-size set for pre-iOS 26 deployment targets)
    macos  AppIcon.iconset/ and, when `iconutil` is available, AppIcon.icns
    web    favicon-{16,32,48,180,192,512}.png plus site.webmanifest

Resizing backend: macOS `sips` when present, otherwise Pillow. Neither is bundled;
the script reports clearly which one it used and fails with an actionable message
when neither is available.

Refuses non-square input, and refuses to upscale — a blurry 1024 generated from a
512 master is worse than an explicit error.
"""
import argparse
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

# (size_pt, scale, idiom) — the legacy set, still required by older deployment targets.
IOS_LEGACY = [
    (20, 2, "iphone"), (20, 3, "iphone"),
    (29, 2, "iphone"), (29, 3, "iphone"),
    (40, 2, "iphone"), (40, 3, "iphone"),
    (60, 2, "iphone"), (60, 3, "iphone"),
    (20, 1, "ipad"), (20, 2, "ipad"),
    (29, 1, "ipad"), (29, 2, "ipad"),
    (40, 1, "ipad"), (40, 2, "ipad"),
    (76, 2, "ipad"),
    (83.5, 2, "ipad"),
]
MACOS_ICONSET = [
    ("icon_16x16", 16), ("icon_16x16@2x", 32),
    ("icon_32x32", 32), ("icon_32x32@2x", 64),
    ("icon_128x128", 128), ("icon_128x128@2x", 256),
    ("icon_256x256", 256), ("icon_256x256@2x", 512),
    ("icon_512x512", 512), ("icon_512x512@2x", 1024),
]
WEB_SIZES = [16, 32, 48, 180, 192, 512]

MASTER_SIZE = 1024


def png_dimensions(path: Path) -> tuple:
    """Read width/height from a PNG IHDR without any imaging dependency."""
    with path.open("rb") as fh:
        header = fh.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG file")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


class Resizer:
    """Resize backend: sips (macOS) or Pillow. Chosen once, reported once."""

    def __init__(self):
        self.backend = None
        self._pil = None
        if shutil.which("sips"):
            self.backend = "sips"
            return
        try:
            from PIL import Image

            self._pil = Image
            self.backend = "pillow"
        except ImportError:
            self.backend = None

    def resize(self, src: Path, dst: Path, size: int) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if self.backend == "sips":
            subprocess.run(
                ["sips", "-z", str(size), str(size), str(src), "--out", str(dst)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        elif self.backend == "pillow":
            with self._pil.open(src) as img:
                img.convert("RGBA").resize(
                    (size, size), self._pil.LANCZOS
                ).save(dst, "PNG")
        else:  # pragma: no cover - guarded in main()
            raise RuntimeError("no resize backend available")


def build_ios(master: Path, out_dir: Path, resizer: Resizer) -> Path:
    appiconset = out_dir / "AppIcon.appiconset"
    appiconset.mkdir(parents=True, exist_ok=True)

    images = []

    # iOS 26 single-size entry — the modern, preferred form.
    shutil.copyfile(master, appiconset / "AppIcon-1024.png")
    images.append(
        {
            "filename": "AppIcon-1024.png",
            "idiom": "universal",
            "platform": "ios",
            "size": "1024x1024",
        }
    )

    for pt, scale, idiom in IOS_LEGACY:
        px = int(round(pt * scale))
        pt_label = f"{pt:g}"
        name = f"AppIcon-{pt_label}x{pt_label}@{scale}x-{idiom}.png"
        resizer.resize(master, appiconset / name, px)
        images.append(
            {
                "filename": name,
                "idiom": idiom,
                "scale": f"{scale}x",
                "size": f"{pt_label}x{pt_label}",
            }
        )

    contents = {
        "images": images,
        "info": {"author": "apple-icon-studio", "version": 1},
    }
    (appiconset / "Contents.json").write_text(
        json.dumps(contents, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return appiconset


def build_macos(master: Path, out_dir: Path, resizer: Resizer) -> tuple:
    iconset = out_dir / "AppIcon.iconset"
    iconset.mkdir(parents=True, exist_ok=True)
    for name, px in MACOS_ICONSET:
        if px == MASTER_SIZE:
            shutil.copyfile(master, iconset / f"{name}.png")
        else:
            resizer.resize(master, iconset / f"{name}.png", px)

    icns = None
    if shutil.which("iconutil"):
        icns = out_dir / "AppIcon.icns"
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(icns)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    return iconset, icns


def build_web(master: Path, out_dir: Path, resizer: Resizer) -> Path:
    web = out_dir / "web"
    web.mkdir(parents=True, exist_ok=True)
    for px in WEB_SIZES:
        resizer.resize(master, web / f"favicon-{px}.png", px)
    manifest = {
        "icons": [
            {
                "src": f"favicon-{px}.png",
                "sizes": f"{px}x{px}",
                "type": "image/png",
            }
            for px in WEB_SIZES
        ]
    }
    (web / "site.webmanifest").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return web


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, type=Path, help="1024x1024 master PNG")
    ap.add_argument("--out-dir", required=True, type=Path, help="output directory")
    ap.add_argument(
        "--targets",
        default="ios,macos,web",
        help="comma-separated subset of ios,macos,web (default: all)",
    )
    args = ap.parse_args()

    master = args.input
    if not master.is_file():
        print(f"error: {master} does not exist", file=sys.stderr)
        return 2

    try:
        width, height = png_dimensions(master)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if width != height:
        print(
            f"error: master must be square, got {width}x{height}. An app icon canvas "
            f"is 1:1 — crop or re-render rather than letting a resize distort it.",
            file=sys.stderr,
        )
        return 2

    if width < MASTER_SIZE:
        print(
            f"error: master is {width}x{height}, below the required "
            f"{MASTER_SIZE}x{MASTER_SIZE}. Upscaling would produce a soft App Store "
            f"icon; re-render the master at 1024 instead.",
            file=sys.stderr,
        )
        return 2

    targets = {t.strip() for t in args.targets.split(",") if t.strip()}
    unknown = targets - {"ios", "macos", "web"}
    if unknown:
        print(f"error: unknown target(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2
    if not targets:
        print("error: no targets selected", file=sys.stderr)
        return 2

    resizer = Resizer()
    if resizer.backend is None:
        print(
            "error: no resize backend. Install Pillow (`pip install Pillow`) or run "
            "on macOS where `sips` is available.",
            file=sys.stderr,
        )
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)

    if width > MASTER_SIZE:
        normalized = args.out_dir / "master-1024.png"
        resizer.resize(master, normalized, MASTER_SIZE)
        print(f"note: downscaled {width}px master to 1024px → {normalized}")
        master = normalized

    print(f"resize backend: {resizer.backend}")

    if "ios" in targets:
        path = build_ios(master, args.out_dir, resizer)
        print(f"wrote {path} ({len(IOS_LEGACY) + 1} images + Contents.json)")
    if "macos" in targets:
        iconset, icns = build_macos(master, args.out_dir, resizer)
        print(f"wrote {iconset} ({len(MACOS_ICONSET)} images)")
        if icns:
            print(f"wrote {icns}")
        else:
            print("note: iconutil not found — .icns not generated (iconset is still valid)")
    if "web" in targets:
        path = build_web(master, args.out_dir, resizer)
        print(f"wrote {path} ({len(WEB_SIZES)} favicons + site.webmanifest)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
