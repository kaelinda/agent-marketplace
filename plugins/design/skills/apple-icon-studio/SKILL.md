---
name: apple-icon-studio
description: "Use when the user needs an app icon / brand mark designed — for an iOS, macOS, watchOS, or visionOS app, a CLI tool, a browser extension, a public account, or any product that needs a memorable square icon. Not a one-shot image prompt: runs a 10-layer Apple-Design-Team workflow (brand essence → metaphor generation → shape language → material → composition → color → adversarial critique → image prompt → Icon Composer params → 2026 evolution check), kills 7 of 10 concepts on purpose, scores the survivors against a fixed rubric, and ships a bilingual print-ready HTML design brief plus a ready-to-render prompt. Triggers: 设计一个 App 图标, 做个 icon, 帮我设计图标, app icon, design an app icon, icon design, brand mark, 图标设计, appiconset, Icon Composer."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [design, icon, app-icon, branding, apple, hig, ios, macos, visual-identity, image-prompt, html, report]
    related_skills:
      - product-teardown
      - wechat-cover-image
      - ali-oss
---

# Apple Icon Studio

## Overview

Most icon prompts fail the same way: they start drawing. This skill does not draw until
layer 8 of 10.

The premise is that a great app icon is not an illustration problem, it is a **positioning
problem that happens to end in a picture**. Apple's own icons are almost never pictures of
the product — AirDrop is not a Wi-Fi diagram, it is radiating circles; Shortcuts is not a
workflow graph, it is a layered diamond. Getting there requires deciding *what the product
means* before deciding *what to render*.

So this is a workflow, not a prompt:

```
Product              → what is this, really
    → Brand Essence  → one sentence, the seed for everything downstream
    → Metaphors      → generate 10, score them, keep 3
    → Shape          → what the silhouette says before the eye resolves detail
    → Material       → the single most under-specified variable in AI icon generation
    → Composition    → weight, negative space, focus, perspective
    → Color          → derived from category + rivals + emotion, never picked at random
    → Critique       → adversarial pass; most concepts die here
    → Image Prompt   → 13 slots, built from every decision above
    → Icon Composer  → glass / blur / refraction / specular numbers for Apple's tool
    → Evolution      → would the 2026 Apple design team still ship this?
```

The output is two artifacts: a chat-side design record, and a self-contained bilingual HTML
brief (`scripts/render_icon_brief.py`) that a designer or a client can actually read.

## When to Use

- "帮我给这个 App 设计一个图标" / "design an app icon for my CLI tool"
- "我的图标太像 ChatGPT 了，帮我重做" (the critique layer is the point here)
- "把这套图标风格迁移到我的另外三个产品上" (Brand Essence + Icon DNA make this consistent)
- Producing an `AppIcon.appiconset` / `.icns` / favicon set from an approved 1024 master
  (`scripts/make_icon_set.py`)

**Not** for: general illustration, in-app SF-Symbol-style glyphs, logotypes with wordmarks,
or marketing hero images. Icons are a square-canvas, small-size, home-screen-context problem
and this skill's entire rubric assumes that context.

## Reference files

Load only what the current layer needs — the whole library is far larger than any one run
requires.

| File | Load when |
|---|---|
| `references/DESIGN_PRINCIPLES.md` | Always — the non-negotiables (safe area, single subject, silhouette-first) |
| `references/METAPHOR_GENERATOR.md` | Layer 2 — the 5 metaphor axes and the scoring rubric |
| `references/SHAPE_LANGUAGE.md` | Layer 3 — shape → meaning table |
| `references/MATERIAL_LIBRARY.md` | Layer 4 — 11 materials with the prompt vocabulary each one needs |
| `references/COMPOSITION.md` | Layer 5 — 8 composition patterns + balance analysis |
| `references/COLOR_SYSTEM.md` | Layer 6 — category palettes, contrast rules, dark-mode behaviour |
| `references/CRITIQUE_GUIDE.md` | Layer 7 — the 11 standard rejections and the 6-axis scorecard |
| `references/PROMPT_TEMPLATE.md` | Layer 8 — 13-slot prompt skeleton + negative prompt |
| `references/ICON_COMPOSER.md` | Layer 9 — Apple Icon Composer parameter ranges |
| `references/ICON_EVOLUTION.md` | Layer 10 — iOS 7 → 26 trajectory, what's dead, what's next |
| `references/CHECKLIST.md` | Before shipping — the pass/fail gate |
| `references/icon-dna/<category>.md` | Layer 1, as soon as the category is known — pre-digested DNA for that industry |

`references/icon-dna/` covers `ai`, `productivity`, `developer`, `media`, `finance`,
`education`, `health`, `social`, `utilities`, `games`. Each file front-loads the category's
metaphors, shapes, materials, palettes, lighting, traps, and reusable prompt fragments — read
it *before* generating metaphors so layer 2 starts from the state of the art rather than from
zero.

`examples/` holds five worked runs (`note-app`, `ai-chat`, `video-editor`, `weather`,
`terminal`) showing the full decision trail including the concepts that were killed.

---

## The 10 layers

### Layer 1 — Product Analyzer

Do not accept the product's own marketing description. Answer five questions in the user's
own domain language, then compress:

```
这到底是什么产品？      What is it, mechanically?
别人为什么下载？        What promise makes someone install it?
别人为什么打开？        What triggers a session?
别人为什么每天打开？    What makes it a habit rather than a tool?
别人为什么会记住？      What would they describe to a friend?
```

Compress into a **Brand Essence**: one sentence, ideally 2–4 words, that every later layer
must be traceable to.

```
Notion    → Think in blocks.
Linear    → Speed.
Raycast   → Command everything.
ChatGPT   → Intelligence.
Things    → Calm productivity.
```

If the essence could be swapped onto a competitor without anyone noticing, it is not an
essence yet — go again. Then open the matching `references/icon-dna/<category>.md`.

**Gate:** no metaphor generation until the Brand Essence is written down.

### Layer 2 — Metaphor Generator

Apple icons depict a metaphor, not the product. Generate along five axes (see
`references/METAPHOR_GENERATOR.md`):

```
Functional metaphor  → what it does
Emotional metaphor   → how it should feel
Physical metaphor    → what real object behaves like this
Abstract metaphor    → the geometry of the idea
Brand metaphor       → the thing only this product could own
```

Produce **10 metaphors**, score each on Distinctiveness / Legibility-at-40px /
Essence-fit / Longevity (0–10 each), then **kill 7 and keep 3**. Killing is mandatory and the
reason for each kill goes in the brief — the discarded column is the part that proves the
survivors were chosen rather than defaulted to.

### Layer 3 — Shape Language

Choose the silhouette before any detail. The shape carries meaning at the size where detail
does not survive:

| Shape | Reads as |
|---|---|
| Circle | Friendly, calm, balanced |
| Square / rounded rect | Reliable, stable, professional |
| Triangle | Speed, energy, direction |
| Diamond | Automation, precision, technology |
| Organic blob | Creativity, play, warmth |

Explain *why this shape for this essence* — not "it looks nice." Full table with hybrid and
negative-space forms in `references/SHAPE_LANGUAGE.md`.

### Layer 4 — Material Director

The layer nearly every icon prompt omits, and the one that most separates an Apple-looking
icon from a generic one. Specify six variables, never fewer:

```
Primary material     Ceramic
Secondary / accent   Liquid glass
Reflection           Medium
Transparency         15%
Edge                 Soft 2px chamfer
Surface finish       Semi-gloss
```

Material vocabulary (glass, ceramic, rubber, metal, paper, fabric, wood, crystal, resin,
frosted glass, liquid glass) with the exact prompt phrasing each one requires is in
`references/MATERIAL_LIBRARY.md`. Mixing more than two materials is a documented failure mode
— see the critique guide.

### Layer 5 — Composition Director

Pick one of eight patterns — centered, floating, diagonal, framed, stacked, embedded, nested,
suspended — then analyse visual weight, negative space, balance, focus point, and perspective.
`references/COMPOSITION.md` has the safe-area geometry: the subject occupies roughly 60–70% of
the canvas, and nothing meaningful crosses the corner-mask radius.

### Layer 6 — Color Director

Colour is derived, not chosen:

```
Category → what the category's users already expect
   → Rivals → what is already taken (avoid collision)
   → Positioning → premium / playful / serious / technical
   → Emotion → what the first 200ms should feel like
   → Palette → 2–3 hues max, one dominant, one accent
```

Category starting points (full version, plus dark-mode and accessibility rules, in
`references/COLOR_SYSTEM.md`):

| Category | Palette |
|---|---|
| AI | Indigo · Purple · Black · Glass white |
| Finance | Emerald · Navy · Silver |
| Music / media | Orange · Pink · Black |
| Developer tools | Graphite · Blue · White |

Hard rule: **no colour overload.** More than three hues at 40px becomes mud.

### Layer 7 — Apple Reviewer (the layer that carries the skill)

This layer does not generate. It attacks. Run the 11 standard rejections from
`references/CRITIQUE_GUIDE.md` against each surviving concept — "too close to ChatGPT",
"too close to Arc", "too busy", "dirty on the home screen", "illegible at 40px", "no colour
hierarchy", "muddled materials", "doesn't feel Apple", "edges too sharp", "light direction
wrong", "will date within 18 months" — and state each verdict explicitly, including the passes.

Then score, 0–100 per axis:

```
Apple Feeling      Does it belong on an Apple home screen?
Recognition        Identifiable in a 5×5 grid of rivals?
Material           Is the surface believable and singular?
Memorability       Describable from memory a day later?
Scalability        Survives 1024 → 40 → 16px?
Emotion            Does it make the right first impression?
────────────────
Final              Weighted: Recognition ×1.5, Scalability ×1.5, others ×1
```

**A concept scoring under 85 final does not ship — it goes back to layer 2 or 4.** Iterate.
Being harsh here is cheaper than being harsh after the app is on the store.

### Layer 8 — Image Prompt Builder

Only now write the prompt, and write it as 13 explicit slots rather than a paragraph:

```
Object · Composition · Material · Lighting · Color · Background
Reflection · Depth · Camera · Texture · Surface · Shadow · Negative Prompt
```

Every slot must trace back to a decision from layers 1–6 — if a slot has no upstream decision,
that is a hole in the analysis, not a detail to improvise. Skeleton and worked examples in
`references/PROMPT_TEMPLATE.md`.

### Layer 9 — Apple Icon Composer handoff

An AI image is not a shipped icon. Emit the parameter set for Apple's Icon Composer so the
result lands in system-native territory rather than "AI render pasted into a square":

```
Glass 32%  ·  Blur 18%  ·  Refraction 45%  ·  Specular 60%
Shadow soft  ·  Depth medium  ·  Glow weak
```

Ranges, layer-splitting guidance (background / mid / foreground), and the light/dark/clear
variant rules are in `references/ICON_COMPOSER.md`.

### Layer 10 — Icon Evolution

Finally, date-check the design against where Apple actually is. `references/ICON_EVOLUTION.md`
traces iOS 7 → 26 and answers three questions for this specific icon:

1. **What design language here is already dead?** (heavy skeuomorphism, busy texture,
   Android-style drop shadows, long shadows, gradient-mesh backgrounds)
2. **What is becoming the default?** (liquid glass, refraction, soft speculars, single
   subject, clean silhouette, layered depth over flat)
3. **If Apple's design team redesigned this icon in 2026, what would they do differently?**

If the answer to (3) is substantial, apply it and re-run layer 7.

---

## Output

Run the layers in chat, then produce the deliverable:

```bash
python3 scripts/render_icon_brief.py --data brief.json --out-dir ./output
```

Writes `icon-brief-<slug>-en.html` and `icon-brief-<slug>-zh.html` — self-contained, no
network, print-ready, cross-linked, with the metaphor kill-list, the scorecard, the palette
swatches, both prompts, and the Icon Composer parameters. `references/example-brief.json`
is a complete working example covering every field.

Rendering **validates before it writes**: unresolved `{{PLACEHOLDER}}`, out-of-range scores,
a stated final score that disagrees with the weighted formula, or EN/ZH key drift all fail the
run and **nothing is written to disk** — a half-filled brief on disk is worse than no brief.

Adding a field is always a **four-file change**: both templates, `example-brief.json`, and the
test's expected-key list. The test suite exists to catch exactly the case where one language
gets a new field and the other silently renders a hole:

```bash
python3 tests/test_render_icon_brief.py
```

### Producing the actual asset set

Once a 1024×1024 master PNG is approved:

```bash
python3 scripts/make_icon_set.py --input master-1024.png --out-dir ./icons \
    --targets ios,macos,web
```

Emits `AppIcon.appiconset/` with a valid `Contents.json`, a macOS `.iconset/` (and `.icns`
when `iconutil` is present), and web favicons. Uses macOS `sips`/`iconutil` when available and
falls back to Pillow, so it runs on Linux CI too. It refuses non-square input and warns when
upscaling would be required rather than silently producing a blurry 1024.

## Why the workflow, not a prompt

A single prompt produces a plausible icon on the first try and then cannot tell you why it is
wrong or how to make the next one match. The layers exist so that:

- **The essence is reusable.** Ship a second product and layers 1 and 6 carry over — that is
  how a family of icons stays coherent.
- **The critique is separable from the generation.** The same rubric can be pointed at an icon
  this skill never made, which is most of the real requests.
- **The failure is diagnosable.** "Score 71, failed Recognition and Scalability" localises the
  fix to layer 2 or 3, instead of re-rolling the prompt and hoping.

The `icon-dna/` library is the compounding part: every run that discovers something durable
about a category belongs back in that file, so the next run in the same category starts from a
better place than this one did.
