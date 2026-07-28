# {{PRODUCT}} — UI Style System

> Reverse-engineered visual language, extracted on {{DATE}}.
> Sources: {{SOURCES_LINE}}
>
> This describes a **design language**, not {{PRODUCT}}'s content, copy, logo, or
> proprietary assets. Reuse the system; never reproduce the brand.

## 1. Style DNA

| Axis | Value |
|---|---|
| Personality | {{PERSONALITY_LINE}} |
| Tone | {{TONE}} |
| Theme | {{THEME}} |
| Density | {{DENSITY}} |
| Emotion | {{EMOTION_LINE}} |

Visual dials (0.0 → 1.0):

```
{{VISUAL_BARS}}
```

## 2. Signature moves

The decisions that make an interface read as "{{PRODUCT}}-like". Copy these and the style
survives; drop them and the tokens alone won't carry it.

{{SIGNATURE_MOVES}}

## 3. Anti-patterns

Things that break the look immediately:

{{ANTI_PATTERNS}}

## 4. Color

{{COLOR_TABLE}}

{{CONTRAST_NOTE}}

## 5. Typography

{{TYPOGRAPHY_TABLE}}

## 6. Spacing

Base unit: **{{SPACING_UNIT}}** — every gap, padding, and margin is a multiple of it.

{{SPACING_TABLE}}

## 7. Radius

{{RADIUS_TABLE}}

## 8. Elevation / shadow

{{SHADOW_TABLE}}

## 9. Motion

{{MOTION_TABLE}}

## 10. Components

{{COMPONENT_SUMMARY}}

Per-component specs: see [`components.md`](./components.md).

## 11. Files in this bundle

```
ui-style/
├── DESIGN.md        # this file — human read
├── AGENTS.md        # coding rules for Claude Code / Codex
├── components.md    # per-component specs
├── tokens.json      # design tokens, machine-readable
├── tokens.css       # the same tokens as CSS custom properties
└── style-dna.json   # personality / visual dials, machine-readable
```
