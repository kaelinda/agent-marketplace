# Example — Note App

A local-first note app for people who write to think. Full decision trail including the seven
concepts that were killed.

---

## Layer 1 — Product Analyzer

| Question | Answer |
|---|---|
| What is it, mechanically? | A local markdown editor with backlinks and full-text search |
| Why download? | "My notes should still be mine in ten years" |
| Why open? | Something needs writing down before it evaporates |
| Why daily? | It became the place thinking happens, not the place notes are stored |
| Why remembered? | It is fast and it never loses anything |

**Category:** productivity → read `icon-dna/productivity.md`

**Brand Essence:** *Thinking, kept.*

Checked against the swap test: "Thinking, kept" on Notion would be wrong (Notion is thinking,
*structured*); on Apple Notes it would be wrong (that is capturing, not thinking). It holds.

**Pole (from productivity DNA):** calm, not power. The product's promise is durability and
quiet, not throughput.

---

## Layer 2 — Metaphor Generator

| # | Axis | Metaphor | Dist | 40px | Fit | Long | Total | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Functional | A sheet of paper | 2 | 9 | 6 | 9 | 26 | killed — category default, says nothing |
| 2 | Functional | A pen nib | 3 | 7 | 4 | 8 | 22 | killed — depicts writing, not keeping |
| 3 | Emotional | Still water surface | 6 | 6 | 6 | 9 | 27 | killed — beautiful, but reads as meditation |
| 4 | Emotional | A settled stone | 7 | 9 | 7 | 9 | 32 | kept |
| 5 | Physical | A folded sheet, fold becomes a bookmark | 8 | 8 | 9 | 9 | **34** | **kept** |
| 6 | Physical | A sealed jar | 6 | 8 | 7 | 8 | 29 | killed — "keeping" reads as *storage*, wrong emphasis |
| 7 | Abstract | Nested rectangles | 4 | 8 | 5 | 8 | 25 | killed — reads as a folder; also Files |
| 8 | Abstract | A line that folds back on itself | 8 | 5 | 8 | 9 | 30 | killed — dies below 60px, the fold merges |
| 9 | Brand | A single thread through pages | 7 | 6 | 8 | 8 | 29 | killed — thread stroke too thin for 40px |
| 10 | Brand | An index tab | 8 | 9 | 8 | 8 | 33 | kept |

**Survivors:** #5 folded sheet · #4 settled stone · #10 index tab

Note that the two obvious functional metaphors (#1, #2) scored lowest. That is the normal
pattern and it is why generating ten matters — the first two ideas are almost always the
category default.

---

## Layer 3 — Shape Language

All three survivors carried to shape.

**#5 folded sheet** — rounded rectangle with an asymmetric corner fold. The fold breaks the
canvas shape-echo problem that a plain rounded rectangle would have, and it gives the
silhouette a single memorable irregularity.
Silhouette test at 40px: passes cleanly. The notch reads.

**#4 settled stone** — organic blob. Silhouette test: passes as a shape, *fails as an
identifier* — a smooth blob at 40px could be any of a dozen wellness apps.

**#10 index tab** — rounded rectangle with a protruding tab. Silhouette test: passes, but the
tab crosses into the corner-mask exclusion zone unless the whole form is scaled down to ~55%
of canvas, at which point it looks lost.

**Selected:** #5. The other two carried to layer 7 anyway rather than being cut here, per the
workflow — narrowing before critique tends to lock in the first-liked option.

---

## Layer 4 — Material Director

From `icon-dna/productivity.md`: calm pole → ceramic or paper primary. Paper is thematically
right and the fold metaphor demands a material that folds.

```
Primary            Heavy cream cardstock
Secondary          Brushed brass, folded edge only
Reflection         Subtle (brass only)
Transparency       0%
Edge               Soft 2px, slight deckle on the fold
Surface finish     Matte
```

**Rationale:** paper is the honest material for the metaphor and it carries the "yours, plain,
durable" positioning. The brass edge is the entire craft signal — one small expensive-feeling
detail against an otherwise humble material, which is the ceramic-plus-glass move from the DNA
file transposed to paper-plus-brass.

Deliberately 0% transparency: this app's promise is durability, and a solid object reads as
durable.

---

## Layer 5 — Composition Director

```
Pattern          Centered, slightly floating
Visual weight    Slightly bottom-heavy from the fold shadow → subject nudged up 2.5%
Negative space   Even margin; the fold's negative triangle is the designed void
Balance          Asymmetric — the fold is the only irregularity, everything else symmetric
Focus point      The brass edge of the fold
Perspective      Flat orthographic
Subject size     66% of canvas
```

The fold is placed top-right rather than the conventional bottom-right, because bottom-right
folds read as "dog-eared page" (already-read) and top-right reads as "bookmarked" (kept).
Small decision, carries the whole metaphor.

---

## Layer 6 — Color Director

```
Category      Productivity — warm neutrals dominate the calm pole
Rivals        Notion monochrome · Apple Notes yellow · Bear red-orange · Obsidian purple
Positioning   Durable, plain, yours
Emotion       Settled
```

| Role | Hex | Name | Share | Rationale |
|---|---|---|---|---|
| Dominant | #1F2937 | Graphite | 60% | Field; keeps the cream sheet as the focus |
| Accent | #FEF3C7 | Cream | 30% | The sheet; warm without going to Apple Notes yellow |
| Highlight | #B08D57 | Brass | 10% | Fold edge; the craft signal |

Grayscale check: cream (L\* 94) against graphite (L\* 25) — 69% delta. Passes comfortably.
Dark mode: field to #0A0A0F, cream unchanged, brass +8% luminance.

---

## Layer 7 — Apple Reviewer

### Concept #5 — folded sheet

| Rejection | Verdict |
|---|---|
| R1 Too close to X | Pass — checked vs. Notion, Bear, Apple Notes, Craft, Obsidian |
| R2 Too complex | Pass — one subject, one modifier |
| R3 Dirty on home screen | Pass — two hues, low saturation |
| R4 Illegible at 40px | Pass — fold notch survives to 24px |
| R5 No colour hierarchy | Pass — clear 60/30/10 |
| R6 Muddled materials | Pass — two |
| R7 Doesn't feel Apple | Pass — no stroke, no long shadow, no perspective |
| R8 Edges too sharp | Pass — 2px soft, deckle on the fold |
| R9 Light direction wrong | Pass — single source above, fold occlusion consistent |
| R10 Dates within 18 months | Pass — no trend treatment present |
| R11 Fails tinted/dark | Pass — 69% luminance delta |

| Axis | Score |
|---|---|
| Apple Feeling | 93 |
| Recognition | 89 |
| Material | 94 |
| Memorability | 91 |
| Scalability | 95 |
| Emotion | 92 |
| **Final** | **92.4** |

### Concept #4 — settled stone

Failed R1 (adjacent to several meditation apps) and Recognition scored 68. **Final 79.6** —
below threshold, killed.

### Concept #10 — index tab

Failed R4 at the size required to keep the tab out of the corner mask. **Final 82.1** —
below threshold, killed.

**Verdict:** ship #5.

---

## Layer 8 — Image Prompt

```
App icon. A single sheet of heavy cream cardstock, its top-right corner folded down and
inward, the fold's underside catching a thin brushed-brass edge.
Centered, slightly floating, subject occupies 66% of frame, generous even margin,
nudged 2.5% above centre.
Material: smooth heavy cardstock with a matte non-reflective finish, brushed brass accent
only along the folded edge.
Lighting: single large soft key light from above at 12 degrees, gentle ambient fill from
below, thin rim highlight along the top edge.
Color: warm cream #FEF3C7 sheet, brushed brass #B08D57 fold edge, deep graphite #1F2937 field.
Background: flat deep graphite field with a subtle top-lighter two-stop vertical gradient.
Subtle reflection on the brass only, no visible environment, neutral studio.
Shallow layered depth, sheet crisply separated from the field.
Straight-on orthographic view, no perspective distortion, no vanishing point.
Surface: fine paper smoothness with no visible fibre, soft ambient occlusion inside the fold.
Shadow: short soft contact shadow directly beneath, 15% opacity, no cast shadow.
Square 1:1, full bleed, 1024x1024, product icon render, Apple design language,
premium industrial design, extremely clean, minimal, single subject.

Negative: [standing list] + checkmark, clipboard, pencil, pen, spiral binding, lined paper,
torn edge, crumpled, coffee stain, desk, handwriting, notebook, sticky note
```

---

## Layer 9 — Icon Composer

Paper row from `ICON_COMPOSER.md`, adjusted up slightly for the brass accent:

| Parameter | Value |
|---|---|
| Glass | 8% |
| Blur | 8% |
| Refraction | 6% |
| Specular | 30% |
| Shadow | soft |
| Depth | shallow |
| Glow | none |

**Layers:** background = graphite two-stop gradient · mid = none · foreground = folded sheet,
transparent, 66% of canvas

**Variants:** dark — separate #0A0A0F field, brass +8% luminance. clear — the cream sheet is
light, so the contact shadow must be retained for light wallpapers. tinted — passes.

---

## Layer 10 — Icon Evolution

**Dead language present?** None. No skeuomorphic texture (paper is smooth, no fibre), no long
shadow, no outline stroke, no flat-vector look.

**Emerging language present?** Layered depth yes, single subject yes, restrained two-hue
palette yes. Liquid glass deliberately absent — correct for this metaphor; forcing glass onto
paper would be following the trend rather than serving the product.

**What would Apple do in 2026?** Concrete diff considered:
- *Add a subtle material behaviour to the paper* — accepted; a very slight sheen variation
  across the sheet, invisible at 40px, rewarding at 1024
- *Split into more layers* — rejected; two layers is correct for a single flat object
- *Warm the graphite field slightly* — accepted; #1F2937 → #1F2622, a barely perceptible warm
  shift that makes the cream sit better

Re-scored after the diff: Material 94 → 96, Final 92.4 → **92.7**. Ship.

---

## What this example demonstrates

- The two most obvious metaphors scored lowest and died first. That is normal.
- The winning decision was a *placement* detail (fold top-right, not bottom-right) that took
  one sentence and carried the entire meaning.
- Two concepts survived to layer 7 and both were killed there. Without the critique layer, one
  of them would have shipped, because at layer 3 the stone concept was the prettiest.
