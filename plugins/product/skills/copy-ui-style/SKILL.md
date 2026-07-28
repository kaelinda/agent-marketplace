---
name: copy-ui-style
description: "Use when the user wants to extract, copy, or reverse-engineer a product's UI style / visual design system from screenshots, a URL, or a code repo — and turn it into reusable design tokens plus coding rules an AI agent will actually follow. Produces a ui-style/ bundle: DESIGN.md, AGENTS.md, components.md, tokens.json, tokens.css, style-dna.json. Triggers: 抄这个 UI 风格, 提取 UI 风格, 复刻这个产品的设计, 把这个截图的风格变成设计系统, copy this UI style, extract design system from screenshot, make my app look like Linear/Stripe/Notion, design tokens from screenshot, UI style guide from this site."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [ui, design-system, design-tokens, style-extraction, frontend, screenshot, agents-md, css]
    related_skills:
      - product-teardown
      - ai-architecture-review
---

# Copy UI Style

## Overview

Point this at a screenshot, a URL, or a front-end repo, and it reverse-engineers the
**visual language** into a design system an AI coding agent can be held to:

```
Input (screenshots / URL / repo)
    → Collect      (get real pixels + real values, not memories of the brand)
    → Analyze      (visual personality, before any number)
    → Extract      (tokens: color, type, spacing, radius, shadow, motion)
    → Components   (Button / Card / Input / Row / Nav / Modal specs)
    → Generate     (one JSON → validated ui-style/ bundle)
```

The point is the last step. A style read that lives in the chat log gets ignored by the
next agent session; `ui-style/AGENTS.md` + `ui-style/tokens.css` get read and obeyed.

Sibling to `product-teardown`: that skill asks *why the product works*, this one asks
*what makes it look like itself*. Run both on the same product and they compose — the
teardown's §5 Craft Signals is the one-paragraph version of what this produces in full.

## When to Use

- "把这个截图的 UI 风格提取成设计系统" / "我想让我的项目长得像 Linear"
- "extract design tokens from this screenshot / this site"
- "give Claude Code rules so it stops inventing random colors"
- Before starting a new frontend, to give the agent a style contract up front.

Not this skill: reviewing an existing UI for polish (`design-review`), or picking a brand
from scratch with no reference (`design-consultation`).

## Step 0 · Ground rules

1. **Extract the design language, never the brand.** Tokens, spacing rhythm, component
   proportions, layout patterns — fair game. Logo, wordmark, icon set, illustrations,
   marketing copy, screenshots — never. Say this to the user once if they asked to "copy"
   a product wholesale.
2. **Measure, don't recall.** You know what Stripe "looks like"; that memory is a
   stereotype, and it will produce a generic purple-gradient result. Read the actual
   pixels or the actual CSS. If you truly can't measure a value, write it as `[inferred]`
   — and `[需用户补充]` when the user has to supply it.
3. **Personality before numbers.** #5E6AD2 tells the next agent nothing. "One saturated
   indigo against a fully neutral palette; color means 'act here'" tells it everything.
   Every token needs a rule attached, or it will be used wrong.

## Step 1 · Collect

Whatever the input, land on concrete evidence:

| Input | How to get real values |
|---|---|
| **Screenshot / image** | Read the image directly. Ask for 2–4 shots if given one: a list/dense screen, a form, an overlay or modal, and a marketing page — density and elevation only show up across screens. |
| **URL** | Prefer live inspection over guessing: use a browser tool (Playwright / chrome-devtools MCP if available) to screenshot at 1440px and 390px, and to read computed styles (`getComputedStyle`) on `body`, a button, a card, an input. Fallback: `curl -s <url>` and grep the CSS for custom properties — `grep -oE '\-\-[a-z-]+:\s*[^;]+' style.css \| sort -u` often hands you the entire token set. |
| **Repo** | Read the source of truth, not the components: `tailwind.config.*`, `theme.*`, `tokens.*`, `:root {}` blocks, `*.css` custom properties, SwiftUI `Color`/`Font` extensions, Flutter `ThemeData`. Then check 2–3 components for how the tokens are actually applied. |

Record what you looked at — it goes into `source.inputs` and makes the bundle auditable.

## Step 2 · Analyze the visual personality

Before a single hex value, answer these in chat (short, opinionated, no marketing words):

1. **Personality** — 2–5 adjectives (`minimal`, `premium`, `playful`, `dense`,
   `editorial`, `brutalist`, `developer-focused`, ...).
2. **Theme** — dark / light / both, and which one is the *designed* one.
3. **Density** — compact / comfortable / spacious. Look at row heights and gaps, not
   marketing pages.
4. **Emotion** — what the interface is trying to make the user feel (`trust`, `focus`,
   `speed`, `calm`, `delight`).
5. **Visual dials**, each 0.0–1.0: `roundness`, `density`, `contrast`, `elevation`,
   `motion`. These force a judgment the adjectives let you dodge.
6. **Signature moves** — 3–6 specific decisions that make the style *itself*. This is the
   highest-value part of the whole skill; give it the most thought. "Separation by 1px
   border instead of shadow" is a signature move; "uses a modern font" is not.
7. **Anti-patterns** — 2–5 things that would instantly break the look.

Describe design language only — never the screenshot's content, product names, or copy.

## Step 3 · Extract tokens

| Group | Extract | Required |
|---|---|---|
| **color** | `background`, `surface`, `border`, `text_primary`, `text_secondary`, `primary` + any semantic roles (`success` / `warning` / `danger` / `accent`) and extra surfaces | all six |
| **typography** | `font_sans` (+ `font_mono`, `font_display`), `scale` (≥3 steps), `weights`, `line_height`, `letter_spacing` | `font_sans`, `scale` |
| **spacing** | `unit` (usually 4px or 8px), `scale`, optional `container_max`, `grid` | `unit`, `scale` (≥3) |
| **radius** | `sm` / `md` / `lg` (+ `full`) | all three |
| **shadow** | named elevation levels — omit entirely if the system is flat (that's a finding) | — |
| **motion** | `duration`, `easing` | — |

Extraction rules:

- **Derive the scale, don't transcribe every value.** If you measure 11/12/13/15/18/22px,
  that's the scale. If you measure 13 different sizes, you mis-measured — or the product
  has no system, which is itself worth saying.
- **Sample from the dense screen.** Marketing pages lie about density and type scale.
- **Neutrals carry the style.** Most products have one accent and 5–8 neutrals; getting
  the neutral ramp right matters more than nailing the accent hue.
- **A missing group is a finding, not a gap to fill.** "No shadow tokens — separation is
  border-only" is a real result; do not invent an elevation ramp to look complete.

## Step 4 · Specify components

Cover at least 4, ideally: `Button`, `Card`, `Input`, `ListRow`, `Navigation`, `Modal`.
Per component record whatever is measurable (`height`, `radius`, `padding_x`, `font`,
`background`, `border`) plus two required fields:

- `style` — the one-line visual idiom ("solid primary; secondary is transparent + 1px border").
- `notes` — what a re-implementer would get wrong, including responsive/state behavior.

Also record `states` (hover / focus / selected / disabled) wherever visible — that's where
most style clones fall apart.

## Step 5 · Generate the bundle

Write everything into one JSON file, then render. Scaffold it if you like:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/copy-ui-style/scripts/generate_ui_style.py \
  --init ./ui-style-<slug>.json
```

Fill it (shape and a complete worked example: `references/example-style.json`), then:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/copy-ui-style/scripts/generate_ui_style.py \
  --data ./ui-style-<slug>.json --out-dir ./ui-style
```

The script validates first and **writes nothing** unless the whole file is clean — it
exits non-zero listing every problem (missing color role, non-hex value, unitless spacing
step, visual dial outside 0–1, a component with no `style`). It also computes real WCAG
contrast for `text_primary` / `text_secondary` against `background`, reporting anything
under 4.5:1 as a warning; `--strict` turns warnings into a hard failure.

Output:

```
ui-style/
├── DESIGN.md        # human read: DNA, signature moves, every token table, contrast report
├── AGENTS.md        # the deliverable that matters: rules for Claude Code / Codex
├── components.md    # per-component specs
├── tokens.json      # tokens, machine-readable
├── tokens.css       # the same tokens as :root custom properties
└── style-dna.json   # personality + dials, machine-readable
```

Then tell the user the one line that makes it stick — add to the project's root
`CLAUDE.md` / `AGENTS.md`:

```md
UI work must follow `ui-style/AGENTS.md` and use the tokens in `ui-style/tokens.css`.
```

## Step 6 · Verify (don't skip)

Build one small screen with the bundle — a list + a form + a button row — and put it next
to the original screenshot. If it doesn't read as the same family, the gap is almost never
the colors; it's density, type scale, or a missed signature move. Fix the JSON and
re-render rather than hand-editing the generated files.

## Design principles

1. **Rules beat values.** A token list without a rule per group gets used wrong. Every
   section of `AGENTS.md` is an instruction, not a table.
2. **Signature moves are the product.** Tokens are commodity; the 3–6 specific decisions
   are what makes the copy recognizable.
3. **Fail loudly.** Half-extracted systems are worse than none — the validator refuses
   rather than emitting a plausible-looking bundle with an invented radius ramp.
4. **Accessibility is part of the style, not a later pass.** Contrast is computed, not
   asserted; an inaccessible extraction gets flagged at generation time.
5. **Design language, not brand assets.** Always.

## Repo contents

```
copy-ui-style/
├── SKILL.md
├── scripts/
│   └── generate_ui_style.py     # validate + render the whole bundle from one JSON
├── templates/
│   ├── DESIGN.md.tpl
│   ├── AGENTS.md.tpl
│   └── components.md.tpl
├── references/
│   ├── example-style.json       # filled, valid example (dark, dense, developer-focused)
│   └── skeleton-style.json      # scaffold written by --init
└── tests/
    └── test_generate_ui_style.py
```

After editing a template or the script, re-run the tests — they catch the silent failure
(a placeholder added to a template that nothing fills):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/copy-ui-style/tests/test_generate_ui_style.py
```

**Dependencies:** Python 3 standard library only. Browser tooling (Playwright /
chrome-devtools MCP) is optional and only helps Step 1 for URL inputs — without it, fall
back to user-supplied screenshots or `curl` + CSS grep.

## Pitfalls

1. **Don't extract from memory.** "It's Stripe, so purple gradients" produces a generic
   result that matches nothing. Measure the pixels you were actually given.
2. **Don't sample marketing pages for density.** Hero sections are 3× more spacious than
   the product. Type scale and spacing come from the dense app screen.
3. **Don't fabricate a complete system.** Missing shadows / motion tokens are findings.
   The validator won't force them; don't force yourself.
4. **One accent, unless proven otherwise.** Multi-accent extractions are usually you
   picking up illustration colors or data-viz palettes as UI tokens.
5. **`states` is where clones die.** A Button spec without hover/focus/disabled will be
   implemented with browser defaults and instantly look off-brand.
6. **Never hand-edit files in `ui-style/`.** They're generated — fix the JSON and re-run,
   or the next regeneration silently reverts you.
7. **Copy the language, not the product.** If the user is asking for a pixel clone of a
   competitor including logo and copy, say plainly that the skill extracts the design
   system only.
