#!/usr/bin/env python3
"""Turn one extracted-style JSON file into a complete `ui-style/` bundle.

Usage:
    python3 generate_ui_style.py --init ./ui-style-<slug>.json     # write a skeleton to fill in
    python3 generate_ui_style.py --data ./ui-style-<slug>.json --out-dir ./ui-style
    python3 generate_ui_style.py --data ./ui-style-<slug>.json --out-dir ./ui-style --strict

Input shape (see references/example-style.json for a filled, valid file):

{
  "slug": "kebab-case-name",
  "source": {"product": "Linear", "date": "YYYY-MM-DD", "inputs": ["screenshot: ...", "https://..."]},
  "style_dna": {"personality": [...], "tone": "...", "theme": "dark|light|both",
                "density": "compact|comfortable|spacious", "emotion": [...],
                "visual": {"roundness": 0.0-1.0, "density": ..., "contrast": ..., "elevation": ..., "motion": ...},
                "signature_moves": [...], "anti_patterns": [...]},
  "tokens": {"color": {...}, "typography": {...}, "spacing": {...}, "radius": {...},
             "shadow": {...}, "motion": {...}},
  "components": {"Button": {"height": "36px", ...}, ...}
}

Outputs, all written into --out-dir:
    DESIGN.md  AGENTS.md  components.md  tokens.json  tokens.css  style-dna.json

Nothing is written unless the whole input validates — a half-written bundle (or a doc with
visible {{PLACEHOLDER}} text) is worse than no output. Pure standard library.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "templates"
SKELETON = SKILL_DIR / "references" / "skeleton-style.json"

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
FUNC_COLOR_RE = re.compile(r"^(rgb|rgba|hsl|hsla|oklch|color)\(.+\)$")
LENGTH_RE = re.compile(r"^-?\d+(\.\d+)?(px|rem|em|%)$")
DURATION_RE = re.compile(r"^\d+(\.\d+)?(ms|s)$")

# Roles a design system cannot be reconstructed without.
REQUIRED_COLOR_ROLES = (
    "background", "surface", "border", "text_primary", "text_secondary", "primary",
)
REQUIRED_RADIUS_KEYS = ("sm", "md", "lg")
REQUIRED_VISUAL_DIALS = ("roundness", "density", "contrast", "elevation", "motion")
REQUIRED_COMPONENT_FIELDS = ("style", "notes")
THEMES = ("dark", "light", "both")
DENSITIES = ("compact", "comfortable", "spacious")
MIN_COMPONENTS = 4


# --------------------------------------------------------------------------- validation


def _is_color(value) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip()
    return bool(HEX_RE.match(v) or FUNC_COLOR_RE.match(v)) or v.startswith("var(")


def _flat_colors(color_obj, prefix=""):
    """Yield (dotted_name, value) for a possibly one-level-nested color object."""
    for key, value in color_obj.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            yield from _flat_colors(value, prefix=f"{name}.")
        else:
            yield name, value


def _srgb_channel(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str):
    """WCAG relative luminance for a #RGB / #RRGGBB color. None if not parseable."""
    v = hex_color.strip().lstrip("#")
    if len(v) in (3, 4):
        v = "".join(ch * 2 for ch in v[:3])
    if len(v) in (6, 8):
        v = v[:6]
    else:
        return None
    try:
        r, g, b = (int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return None
    return 0.2126 * _srgb_channel(r) + 0.7152 * _srgb_channel(g) + 0.0722 * _srgb_channel(b)


def contrast_ratio(fg: str, bg: str):
    """WCAG contrast ratio, or None when either color isn't a plain hex value."""
    lf, lb = relative_luminance(fg), relative_luminance(bg)
    if lf is None or lb is None:
        return None
    hi, lo = max(lf, lb), min(lf, lb)
    return (hi + 0.05) / (lo + 0.05)


def validate(data: dict):
    """Return (errors, warnings). Errors block output; warnings block only under --strict."""
    errors, warnings = [], []

    def req(obj, key, where):
        if key not in obj:
            errors.append(f"{where} is missing required key {key!r}")
            return None
        return obj[key]

    slug = req(data, "slug", "root")
    if slug is not None and not SLUG_RE.match(str(slug)):
        errors.append(f"slug must be kebab-case ([a-z0-9-]), got {slug!r}")

    source = req(data, "source", "root") or {}
    if isinstance(source, dict):
        if not str(source.get("product", "")).strip():
            errors.append("source.product must be a non-empty product name")
        date = source.get("date", "")
        if not DATE_RE.match(str(date)):
            errors.append(f"source.date must be YYYY-MM-DD, got {date!r}")
        if not source.get("inputs"):
            errors.append("source.inputs must list what was analysed (screenshots, URLs, repo paths)")
    else:
        errors.append("source must be an object")

    dna = req(data, "style_dna", "root") or {}
    if isinstance(dna, dict):
        for key in ("personality", "emotion"):
            vals = dna.get(key)
            if not isinstance(vals, list) or not 2 <= len(vals) <= 5:
                errors.append(f"style_dna.{key} must be a list of 2-5 short adjectives")
            elif any(not str(v).strip() for v in vals):
                errors.append(f"style_dna.{key} contains an empty item")
        if not str(dna.get("tone", "")).strip():
            errors.append("style_dna.tone must be a non-empty string")
        if dna.get("theme") not in THEMES:
            errors.append(f"style_dna.theme must be one of {THEMES}, got {dna.get('theme')!r}")
        if dna.get("density") not in DENSITIES:
            errors.append(f"style_dna.density must be one of {DENSITIES}, got {dna.get('density')!r}")
        visual = dna.get("visual", {})
        if not isinstance(visual, dict):
            errors.append("style_dna.visual must be an object of 0.0-1.0 dials")
        else:
            for dial in REQUIRED_VISUAL_DIALS:
                if dial not in visual:
                    errors.append(f"style_dna.visual is missing dial {dial!r}")
                    continue
                val = visual[dial]
                if not isinstance(val, (int, float)) or isinstance(val, bool) or not 0.0 <= val <= 1.0:
                    errors.append(f"style_dna.visual.{dial} must be a number 0.0-1.0, got {val!r}")
        for key, low in (("signature_moves", 3), ("anti_patterns", 2)):
            vals = dna.get(key)
            if not isinstance(vals, list) or len(vals) < low:
                errors.append(f"style_dna.{key} must be a list of at least {low} concrete items")
            elif any(not str(v).strip() for v in vals):
                errors.append(f"style_dna.{key} contains an empty item")
    else:
        errors.append("style_dna must be an object")

    tokens = req(data, "tokens", "root") or {}
    if isinstance(tokens, dict):
        color = tokens.get("color")
        if not isinstance(color, dict):
            errors.append("tokens.color must be an object of role -> color")
        else:
            flat = dict(_flat_colors(color))
            for role in REQUIRED_COLOR_ROLES:
                if role not in flat:
                    errors.append(f"tokens.color is missing required role {role!r}")
            for name, value in flat.items():
                if not _is_color(value):
                    errors.append(
                        f"tokens.color.{name} must be a hex / rgb() / hsl() / oklch() color, got {value!r}"
                    )
            for fg_role, label in (("text_primary", "body text"), ("text_secondary", "secondary text")):
                ratio = contrast_ratio(str(flat.get(fg_role, "")), str(flat.get("background", "")))
                if ratio is not None and ratio < 4.5:
                    warnings.append(
                        f"contrast: {fg_role} on background is {ratio:.2f}:1 — below the 4.5:1 "
                        f"WCAG AA floor for {label}. Re-check the extraction or adjust the token."
                    )

        typo = tokens.get("typography")
        if not isinstance(typo, dict):
            errors.append("tokens.typography must be an object")
        else:
            if not str(typo.get("font_sans", "")).strip():
                errors.append("tokens.typography.font_sans is required (the primary UI font stack)")
            scale = typo.get("scale")
            if not isinstance(scale, dict) or len(scale) < 3:
                errors.append("tokens.typography.scale must be an object with at least 3 steps")
            else:
                for step, size in scale.items():
                    if not LENGTH_RE.match(str(size)):
                        errors.append(
                            f"tokens.typography.scale.{step} must be a css length (px/rem/em), got {size!r}"
                        )

        spacing = tokens.get("spacing")
        if not isinstance(spacing, dict):
            errors.append("tokens.spacing must be an object")
        else:
            unit = spacing.get("unit")
            if not LENGTH_RE.match(str(unit or "")):
                errors.append(f"tokens.spacing.unit must be a css length, got {unit!r}")
            scale = spacing.get("scale")
            if not isinstance(scale, dict) or len(scale) < 3:
                errors.append("tokens.spacing.scale must be an object with at least 3 steps")
            else:
                for step, size in scale.items():
                    if not LENGTH_RE.match(str(size)):
                        errors.append(f"tokens.spacing.scale.{step} must be a css length, got {size!r}")

        radius = tokens.get("radius")
        if not isinstance(radius, dict):
            errors.append("tokens.radius must be an object")
        else:
            for key in REQUIRED_RADIUS_KEYS:
                if key not in radius:
                    errors.append(f"tokens.radius is missing required key {key!r}")
            for key, val in radius.items():
                if not (LENGTH_RE.match(str(val)) or str(val) in ("0", "9999px", "50%")):
                    errors.append(f"tokens.radius.{key} must be a css length, got {val!r}")

        motion = tokens.get("motion")
        if isinstance(motion, dict):
            for step, val in (motion.get("duration") or {}).items():
                if not DURATION_RE.match(str(val)):
                    errors.append(f"tokens.motion.duration.{step} must be e.g. '150ms' or '0.2s', got {val!r}")
        elif motion is not None:
            errors.append("tokens.motion must be an object when present")
    else:
        errors.append("tokens must be an object")

    components = req(data, "components", "root") or {}
    if not isinstance(components, dict):
        errors.append("components must be an object of ComponentName -> spec")
    else:
        if len(components) < MIN_COMPONENTS:
            errors.append(
                f"components must cover at least {MIN_COMPONENTS} components "
                f"(Button/Card/Input/Nav... ), got {len(components)}"
            )
        for name, spec in components.items():
            if not isinstance(spec, dict) or not spec:
                errors.append(f"components.{name} must be a non-empty object of property -> value")
                continue
            for field in REQUIRED_COMPONENT_FIELDS:
                if not str(spec.get(field, "")).strip():
                    errors.append(f"components.{name} is missing a non-empty {field!r} field")

    return errors, warnings


# ----------------------------------------------------------------------------- fragments


def md_list(items) -> str:
    return "\n".join(f"- {item}" for item in items)


def md_table(headers, rows) -> str:
    head = "| " + " | ".join(headers) + " |"
    sep = "|" + "|".join(["---"] * len(headers)) + "|"
    body = "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
    return "\n".join([head, sep, body]) if rows else head + "\n" + sep


def bar(value: float, width: int = 20) -> str:
    filled = round(value * width)
    return "█" * filled + "·" * (width - filled)


def visual_bars(visual: dict) -> str:
    width = max(len(k) for k in visual)
    return "\n".join(
        f"{k.ljust(width)}  {bar(float(v))}  {float(v):.2f}" for k, v in visual.items()
    )


def color_table(color: dict) -> str:
    rows = [(f"`{name}`", f"`{value}`") for name, value in _flat_colors(color)]
    return md_table(["Role", "Value"], rows)


def contrast_note(color: dict) -> str:
    flat = dict(_flat_colors(color))
    lines = []
    for fg in ("text_primary", "text_secondary"):
        ratio = contrast_ratio(str(flat.get(fg, "")), str(flat.get("background", "")))
        if ratio is not None:
            verdict = "AA ✓" if ratio >= 4.5 else ("AA large-text only" if ratio >= 3 else "below AA ✗")
            lines.append(f"- `{fg}` on `background`: **{ratio:.2f}:1** — {verdict}")
    if not lines:
        return "_Contrast not computed (non-hex color values)._"
    return "Measured contrast (WCAG 2.1, AA body text needs 4.5:1):\n\n" + "\n".join(lines)


def typography_table(typo: dict) -> str:
    rows = []
    for key in ("font_sans", "font_mono", "font_display"):
        if typo.get(key):
            rows.append((f"`{key}`", f"`{typo[key]}`"))
    for step, size in (typo.get("scale") or {}).items():
        rows.append((f"size `{step}`", f"`{size}`"))
    for step, weight in (typo.get("weights") or {}).items():
        rows.append((f"weight `{step}`", f"`{weight}`"))
    for step, lh in (typo.get("line_height") or {}).items():
        rows.append((f"line-height `{step}`", f"`{lh}`"))
    for step, ls in (typo.get("letter_spacing") or {}).items():
        rows.append((f"letter-spacing `{step}`", f"`{ls}`"))
    return md_table(["Token", "Value"], rows)


def simple_table(obj: dict, label: str) -> str:
    rows = [(f"`{k}`", f"`{v}`") for k, v in obj.items()]
    return md_table([label, "Value"], rows)


def motion_table(motion: dict) -> str:
    rows = []
    for group in ("duration", "easing"):
        for k, v in (motion.get(group) or {}).items():
            rows.append((f"`{group}.{k}`", f"`{v}`"))
    for k, v in motion.items():
        if k not in ("duration", "easing"):
            rows.append((f"`{k}`", f"`{v}`"))
    if not rows:
        return "_No motion tokens extracted — treat transitions as: 150ms, ease-out, opacity + transform only._"
    return md_table(["Token", "Value"], rows)


def component_summary(components: dict) -> str:
    rows = []
    for name, spec in components.items():
        shape = spec.get("height") or spec.get("padding") or spec.get("size") or "—"
        rows.append((f"**{name}**", f"`{shape}`", f"`{spec.get('radius', '—')}`", spec.get("style", "")))
    return md_table(["Component", "Size", "Radius", "Style"], rows)


def component_sections(components: dict) -> str:
    blocks = []
    for name, spec in components.items():
        rows = [(f"`{k}`", str(v)) for k, v in spec.items() if k != "notes"]
        block = [f"## {name}", "", md_table(["Property", "Value"], rows)]
        if spec.get("notes"):
            block += ["", f"**Notes:** {spec['notes']}"]
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def color_rules(color: dict, dna: dict) -> str:
    flat = dict(_flat_colors(color))
    lines = [
        f"- Surfaces stack as `background` → `surface` → `border`; "
        f"never introduce a third grey that isn't a token.",
        f"- `primary` (`{flat.get('primary')}`) is for the single most important action per view. "
        f"Two primary buttons in one view is a bug.",
        f"- Text uses `text_primary` for content and `text_secondary` for meta/labels — "
        f"opacity tricks on `text_primary` are not a substitute.",
    ]
    for role in ("success", "warning", "danger", "accent"):
        if role in flat:
            lines.append(f"- `{role}` (`{flat[role]}`) is reserved for its semantic meaning only — never decorative.")
    if dna.get("theme") == "both":
        lines.append("- Both themes ship: every color is referenced through a token that flips with the theme, "
                     "never a literal that only works in one mode.")
    else:
        lines.append(f"- This is a **{dna.get('theme')}-first** system; if you add the other mode, "
                     f"re-derive the neutrals rather than inverting them mechanically.")
    return "\n".join(lines)


def typo_rules(typo: dict) -> str:
    scale = typo.get("scale") or {}
    steps = ", ".join(f"`{k}` {v}" for k, v in scale.items())
    lines = [
        f"- Font stack: `{typo.get('font_sans')}`. Do not introduce a second UI typeface.",
        f"- Only these sizes exist: {steps}. A size not on the scale is not allowed.",
    ]
    if typo.get("font_mono"):
        lines.append(f"- Code, IDs, and numeric data use `{typo['font_mono']}`.")
    weights = typo.get("weights") or {}
    if weights:
        lines.append(
            "- Weights: " + ", ".join(f"`{k}` {v}" for k, v in weights.items())
            + ". Emphasis comes from weight and color, not from size jumps."
        )
    return "\n".join(lines)


def spacing_rules(spacing: dict, dna: dict) -> str:
    unit = spacing.get("unit")
    scale = spacing.get("scale") or {}
    lines = [
        f"- Base unit **{unit}**. Allowed steps: " + ", ".join(f"`{k}`={v}" for k, v in scale.items()) + ".",
        f"- Density is **{dna.get('density')}** — when unsure between two steps, "
        + ("pick the tighter one." if dna.get("density") == "compact" else "pick the more generous one."),
        "- Vertical rhythm beats horizontal decoration: group related items by reducing the gap, "
        "not by adding a border or a box.",
    ]
    if spacing.get("container_max"):
        lines.append(f"- Content max-width: `{spacing['container_max']}`.")
    if spacing.get("grid"):
        lines.append(f"- Layout grid: `{spacing['grid']}`.")
    return "\n".join(lines)


def radius_rules(radius: dict, shadow: dict, dna: dict) -> str:
    roundness = float((dna.get("visual") or {}).get("roundness", 0.5))
    read = "sharp and technical" if roundness < 0.4 else ("softly rounded" if roundness < 0.7 else "pill-soft and friendly")
    lines = [
        f"- Radius scale: " + ", ".join(f"`{k}`={v}" for k, v in radius.items())
        + f". The system reads **{read}** (roundness {roundness:.2f}) — keep it consistent.",
        "- Radius follows element size: small controls get `sm`, cards get `md`/`lg`. "
        "Never mix two radii on nested elements without an intentional step down.",
    ]
    elevation = float((dna.get("visual") or {}).get("elevation", 0.5))
    if not shadow or elevation < 0.25:
        lines.append("- Elevation is **near-flat**: separate surfaces with a 1px border and a background "
                     "shift, not with drop shadows.")
    else:
        lines.append("- Shadows: " + ", ".join(f"`{k}`" for k in shadow) + " only. "
                     "One elevation step per overlay level; no custom blur values.")
    return "\n".join(lines)


def motion_rules(motion: dict, dna: dict) -> str:
    m = float((dna.get("visual") or {}).get("motion", 0.5))
    durations = (motion or {}).get("duration") or {}
    easings = (motion or {}).get("easing") or {}
    lines = []
    if durations:
        lines.append("- Durations: " + ", ".join(f"`{k}`={v}" for k, v in durations.items()) + ". Nothing longer.")
    else:
        lines.append("- Default transition: 150ms. Nothing longer than 300ms.")
    if easings:
        lines.append("- Easing: " + ", ".join(f"`{k}`={v}" for k, v in easings.items()) + ".")
    if m < 0.35:
        lines.append("- Motion is **restrained** — transitions confirm state changes; they never entertain. "
                     "No entrance animations on page load.")
    elif m > 0.7:
        lines.append("- Motion is **expressive** — but it still has to be interruptible and never block input.")
    else:
        lines.append("- Motion is **functional** — animate opacity and transform only; never animate "
                     "layout properties (`width`, `top`, `height`).")
    lines.append("- Honor `prefers-reduced-motion: reduce` by dropping transforms, keeping opacity fades.")
    return "\n".join(lines)


def component_rules(components: dict) -> str:
    lines = []
    for name, spec in components.items():
        parts = [f"`{k}` {v}" for k, v in spec.items() if k != "notes"]
        lines.append(f"- **{name}** — " + ", ".join(parts) + ".")
    lines.append("- A component not listed here must be composed from these tokens and the nearest "
                 "listed component's proportions — do not invent a new visual idiom.")
    return "\n".join(lines)


def tokens_css(tokens: dict, slug: str) -> str:
    lines = [f"/* {slug} design tokens — generated, do not edit by hand */", ":root {"]

    def emit(group, obj, prefix):
        out = [f"  /* {group} */"]
        for name, value in obj.items():
            if isinstance(value, dict):
                for sub, subval in value.items():
                    out.append(f"  --{prefix}-{_kebab(name)}-{_kebab(sub)}: {subval};")
            else:
                out.append(f"  --{prefix}-{_kebab(name)}: {value};")
        return out

    color = tokens.get("color") or {}
    lines += ["  /* color */"] + [
        f"  --color-{_kebab(name.replace('.', '-'))}: {value};" for name, value in _flat_colors(color)
    ]

    typo = tokens.get("typography") or {}
    lines.append("  /* typography */")
    for key in ("font_sans", "font_mono", "font_display"):
        if typo.get(key):
            lines.append(f"  --{_kebab(key)}: {typo[key]};")
    for group, prefix in (("scale", "text"), ("weights", "weight"),
                          ("line_height", "leading"), ("letter_spacing", "tracking")):
        for name, value in (typo.get(group) or {}).items():
            lines.append(f"  --{prefix}-{_kebab(name)}: {value};")

    spacing = tokens.get("spacing") or {}
    lines.append("  /* spacing */")
    if spacing.get("unit"):
        lines.append(f"  --space-unit: {spacing['unit']};")
    for name, value in (spacing.get("scale") or {}).items():
        lines.append(f"  --space-{_kebab(name)}: {value};")
    for extra in ("container_max", "grid"):
        if spacing.get(extra):
            lines.append(f"  --{_kebab(extra)}: {spacing[extra]};")

    lines += emit("radius", tokens.get("radius") or {}, "radius")
    if tokens.get("shadow"):
        lines += emit("shadow", tokens["shadow"], "shadow")
    motion = tokens.get("motion") or {}
    if motion:
        lines.append("  /* motion */")
        for name, value in (motion.get("duration") or {}).items():
            lines.append(f"  --duration-{_kebab(name)}: {value};")
        for name, value in (motion.get("easing") or {}).items():
            lines.append(f"  --ease-{_kebab(name)}: {value};")

    lines.append("}")
    return "\n".join(lines) + "\n"


def _kebab(name: str) -> str:
    return str(name).replace("_", "-").lower()


# ------------------------------------------------------------------------------- render


def build_values(data: dict) -> dict:
    source = data["source"]
    dna = data["style_dna"]
    tokens = data["tokens"]
    components = data["components"]

    return {
        "PRODUCT": source["product"],
        "SLUG": data["slug"],
        "DATE": source["date"],
        "SOURCES_LINE": "; ".join(str(s) for s in source["inputs"]),
        "PERSONALITY_LINE": " · ".join(dna["personality"]),
        "TONE": dna["tone"],
        "THEME": dna["theme"],
        "DENSITY": dna["density"],
        "EMOTION_LINE": " · ".join(dna["emotion"]),
        "VISUAL_BARS": visual_bars(dna["visual"]),
        "SIGNATURE_MOVES": md_list(dna["signature_moves"]),
        "ANTI_PATTERNS": md_list(dna["anti_patterns"]),
        "COLOR_TABLE": color_table(tokens["color"]),
        "CONTRAST_NOTE": contrast_note(tokens["color"]),
        "TYPOGRAPHY_TABLE": typography_table(tokens["typography"]),
        "SPACING_UNIT": tokens["spacing"]["unit"],
        "SPACING_TABLE": simple_table(tokens["spacing"].get("scale") or {}, "Step"),
        "RADIUS_TABLE": simple_table(tokens["radius"], "Step"),
        "SHADOW_TABLE": (
            simple_table(tokens["shadow"], "Level") if tokens.get("shadow")
            else "_Flat system — no shadow tokens extracted; surfaces separate via border + background._"
        ),
        "MOTION_TABLE": motion_table(tokens.get("motion") or {}),
        "COMPONENT_SUMMARY": component_summary(components),
        "COMPONENT_SECTIONS": component_sections(components),
        "COLOR_RULES": color_rules(tokens["color"], dna),
        "TYPO_RULES": typo_rules(tokens["typography"]),
        "SPACING_RULES": spacing_rules(tokens["spacing"], dna),
        "RADIUS_RULES": radius_rules(tokens["radius"], tokens.get("shadow") or {}, dna),
        "MOTION_RULES": motion_rules(tokens.get("motion") or {}, dna),
        "COMPONENT_RULES": component_rules(components),
    }


def render(template_path: Path, values: dict):
    text = template_path.read_text(encoding="utf-8")
    for key in sorted(values, key=len, reverse=True):
        text = text.replace("{{" + key + "}}", str(values[key]))
    return text, sorted(set(PLACEHOLDER_RE.findall(text)))


def generate(data: dict, out_dir: Path, strict: bool = False) -> int:
    errors, warnings = validate(data)
    if errors:
        print("Refusing to write — fix the style JSON and re-run:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if warnings:
        stream = sys.stderr
        print("Warnings:", file=stream)
        for w in warnings:
            print(f"  - {w}", file=stream)
        if strict:
            print("--strict: refusing to write while warnings remain.", file=stream)
            return 1

    values = build_values(data)
    files = {}
    unresolved = []
    for tpl_name, out_name in (
        ("DESIGN.md.tpl", "DESIGN.md"),
        ("AGENTS.md.tpl", "AGENTS.md"),
        ("components.md.tpl", "components.md"),
    ):
        text, remaining = render(TEMPLATE_DIR / tpl_name, values)
        if remaining:
            unresolved += [f"{out_name}: {{{{{r}}}}}" for r in remaining]
        files[out_name] = text

    if unresolved:
        print("Refusing to write — unresolved placeholders (template/script out of sync):", file=sys.stderr)
        for u in unresolved:
            print(f"  - {u}", file=sys.stderr)
        return 1

    files["tokens.json"] = json.dumps(data["tokens"], indent=2, ensure_ascii=False) + "\n"
    files["style-dna.json"] = json.dumps(data["style_dna"], indent=2, ensure_ascii=False) + "\n"
    files["tokens.css"] = tokens_css(data["tokens"], data["slug"])

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (out_dir / name).write_text(content, encoding="utf-8")
        print(f"Wrote: {out_dir / name}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--data", help="Path to the extracted-style JSON file")
    parser.add_argument("--out-dir", default="./ui-style", help="Bundle output directory (default: ./ui-style)")
    parser.add_argument("--init", metavar="PATH", help="Write a skeleton style JSON to PATH and exit")
    parser.add_argument("--strict", action="store_true", help="Treat warnings (e.g. low contrast) as errors")
    args = parser.parse_args()

    if args.init:
        target = Path(args.init)
        if target.exists():
            print(f"Refusing to overwrite existing file: {target}", file=sys.stderr)
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(SKELETON.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Wrote skeleton: {target}")
        return 0

    if not args.data:
        parser.error("--data is required (or use --init to scaffold one)")

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    return generate(data, Path(args.out_dir), strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
