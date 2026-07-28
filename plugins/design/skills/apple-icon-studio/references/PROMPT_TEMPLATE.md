# Image Prompt Builder — Layer 8

Only now do we write a prompt. Every slot below must trace to a decision from layers 1–6. If a
slot has no upstream decision, that is a hole in the analysis — go back and fill it rather than
improvising at the prompt.

---

## The 13 slots

| # | Slot | Comes from | Example |
|---|---|---|---|
| 1 | **Object** | Layer 2 metaphor + layer 3 shape | `a single thick ring, one clean break at the top-right` |
| 2 | **Composition** | Layer 5 | `centered, floating, subject occupies 65% of frame, generous even margin` |
| 3 | **Material** | Layer 4 primary + secondary | `glazed warm-white ceramic body with a liquid-glass indigo inner core` |
| 4 | **Lighting** | Layer 4 lighting | `single large soft key light from above at 12°, gentle ambient fill from below` |
| 5 | **Color** | Layer 6 palette | `deep slate background #0F172A, amber accent #F59E0B, cream highlight` |
| 6 | **Background** | Layer 5 field | `flat deep-slate field with a subtle top-lighter two-stop vertical gradient` |
| 7 | **Reflection** | Layer 4 | `medium reflection, no visible environment, neutral studio` |
| 8 | **Depth** | Layer 5 | `shallow layered depth, foreground subject crisply separated from field` |
| 9 | **Camera** | Layer 5 perspective | `straight-on orthographic view, no perspective distortion, no vanishing point` |
| 10 | **Texture** | Layer 4 finish | `fine glaze micro-variation, no visible grain or noise` |
| 11 | **Surface** | Layer 4 finish | `semi-gloss, soft broad specular along the top edge` |
| 12 | **Shadow** | Layer 4 lighting | `short soft contact shadow directly beneath, 15% opacity, no cast shadow` |
| 13 | **Negative prompt** | standing list below | see below |

---

## Assembly template

```
App icon. {OBJECT}.
{COMPOSITION}.
Material: {MATERIAL}.
Lighting: {LIGHTING}.
Color: {COLOR}.
Background: {BACKGROUND}.
{REFLECTION}. {DEPTH}. {CAMERA}.
Surface: {TEXTURE}, {SURFACE}.
Shadow: {SHADOW}.
Square 1:1, full bleed, 1024x1024, product icon render, Apple design language,
premium industrial design, extremely clean, minimal, single subject.
```

Keep the closing block verbatim — it is doing real work. `square 1:1` and `full bleed` prevent
the model from adding its own rounded corners and drop shadow; `single subject` counteracts the
strong prior toward adding decorative secondary elements.

---

## Standing negative prompt

Use this as the base for every render, then add case-specific exclusions.

```
text, letters, words, numbers, watermark, signature, logo type, UI mockup,
screenshot, app store frame, phone mockup, rounded corner mask, drop shadow border,
multiple objects, cluttered, busy, noisy, small details, tiny elements, badge, sparkle cluster,
photorealistic scene, room, desk, table, floor, ground plane, landscape, environment reflection,
two light sources, conflicting highlights, harsh shadow, long shadow, hard outline stroke,
rainbow, neon glow, lens flare, bokeh, depth of field blur on subject,
3d perspective, vanishing point, tilted camera, isometric grid,
low resolution, blurry, jpeg artifacts, oversaturated, garish
```

Case-specific additions to consider:

- Competing with a known icon → add that icon's dominant hue and its signature form
- Category cliché risk → add the cliché explicitly (`brain, neural network, chat bubble`)
- Trend risk → `iridescent chrome, aurora gradient, holographic, glassmorphism card`

---

## Worked example

**Product:** a local-first note app. **Essence:** *Thinking, kept.*
**Metaphor:** a folded sheet whose fold becomes a bookmark (physical axis).
**Shape:** rounded rectangle with an asymmetric fold. **Material:** heavy paper + brass accent.
**Composition:** centered, slight float. **Palette:** cream dominant, brass accent, graphite
field.

```
App icon. A single sheet of heavy cream cardstock, one corner folded down and inward,
the fold's underside catching a thin brass edge.
Centered, slightly floating, subject occupies 66% of frame, generous even margin.
Material: smooth heavy cardstock with a matte non-reflective finish, brass accent only along
the folded edge.
Lighting: single large soft key light from above at 12 degrees, gentle ambient fill from below,
thin rim highlight along the top edge.
Color: warm cream #FEF3C7 sheet, brushed brass #B08D57 fold edge, deep graphite #1F2937 field.
Background: flat deep graphite field with a subtle top-lighter two-stop vertical gradient.
Medium reflection on the brass only, no visible environment, neutral studio.
Shallow layered depth, sheet crisply separated from the field.
Straight-on orthographic view, no perspective distortion, no vanishing point.
Surface: fine paper smoothness with no visible fibre, soft ambient occlusion inside the fold.
Shadow: short soft contact shadow directly beneath, 15% opacity, no cast shadow.
Square 1:1, full bleed, 1024x1024, product icon render, Apple design language,
premium industrial design, extremely clean, minimal, single subject.

Negative: [standing list] + notebook, spiral binding, pencil, pen, lined paper, torn edge,
crumpled, coffee stain, desk, handwriting
```

---

## Model-specific notes

**Midjourney** — append `--ar 1:1 --style raw --stylize 150`. `--style raw` matters: the
default aesthetic model adds decorative elements that violate the single-subject rule. Keep
stylize low; high stylize invents detail.

**DALL·E / GPT-image** — responds well to the prose-paragraph form above. It tends to add
text unprompted; repeat "no text, no letters" in the positive prompt as well as the negative.

**Stable Diffusion / Flux** — front-load the object and material; these models weight early
tokens heavily. Negative prompts carry real weight here, so use the full standing list.

**Nano Banana / Imagen** — strongest at material realism; can be given the material vocabulary
verbatim from `MATERIAL_LIBRARY.md`. Weak at leaving margin — state the margin requirement
twice.

Across all models: **generate 4–8 variations, not one.** The prompt is a specification, not an
incantation; the variance between samples at fixed prompt is larger than the variance between
two well-written prompts.

---

## After generation

1. **Downsample every candidate to 40px before judging at full size.** Judging at 1024 first
   biases you toward the most detailed candidate, which is usually the one that dies smallest.
2. **Grayscale check** for tinted mode.
3. Take the winner to layer 9 (`ICON_COMPOSER.md`) — the raw render is an input to the icon,
   not the icon.
4. Re-score against `CRITIQUE_GUIDE.md`. The scores from layer 7 were on the *concept*; these
   are on the *artifact*, and they are frequently lower.
