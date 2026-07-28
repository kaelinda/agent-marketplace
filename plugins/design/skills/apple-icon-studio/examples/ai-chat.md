# Example — AI Chat Assistant

The hardest case in the library: a general-purpose AI assistant, competing directly against
five icons with enormous recognition. Demonstrates the deliberate counter-move.

---

## Layer 1 — Product Analyzer

| Question | Answer |
|---|---|
| What is it? | A general assistant with memory across conversations |
| Why download? | "I want one that remembers me" |
| Why open? | A question, a draft, a decision to think through |
| Why daily? | It accumulated context — it knows the project |
| Why remembered? | Continuity. It does not start over. |

**Category:** AI → read `icon-dna/ai.md`

**Brand Essence:** *Continuity of thought.*

Swap test: this would be wrong on ChatGPT (breadth), wrong on Perplexity (retrieval), wrong on
Cursor (execution). It holds.

**Framing (from AI DNA):** Collaborator, leaning Assistant. Not Oracle — the product does not
promise superiority, it promises persistence.

---

## Layer 2 — Metaphor Generator

The DNA file's exhausted list eliminated four candidates before scoring: sparkle, brain, chat
bubble, glowing orb. Generated ten from the remaining space.

| # | Axis | Metaphor | Dist | 40px | Fit | Long | Total | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Functional | An open lens | 6 | 8 | 5 | 8 | 27 | killed — reads as camera |
| 2 | Functional | A prism | 5 | 8 | 5 | 8 | 26 | killed — fits "transformation", not "continuity" |
| 3 | Emotional | A hand offered | 7 | 4 | 7 | 7 | 25 | killed — human figures fail at 40px |
| 4 | Emotional | A steady flame | 6 | 8 | 8 | 8 | 30 | killed — "flame" reads as streak/gamification |
| 5 | Physical | A thread continuing through a knot | 9 | 6 | 9 | 9 | 33 | kept |
| 6 | Physical | A tuning fork in resonance | 9 | 7 | 7 | 8 | 31 | kept |
| 7 | Abstract | A spiral | 4 | 5 | 8 | 8 | 25 | killed — inner turns merge below 60px |
| 8 | Abstract | An unbroken line entering and leaving a form | 8 | 8 | 9 | 9 | **34** | **kept** |
| 9 | Brand | A bookmark that is also a path | 6 | 6 | 8 | 7 | 27 | killed — two ideas, violates single subject |
| 10 | Brand | A vessel that fills over time | 7 | 8 | 8 | 8 | 31 | killed — "filling" implies a limit |

**Survivors:** #8 unbroken line through a form · #5 thread through a knot · #6 tuning fork

Note: #10 was killed on a semantic detail — a vessel that fills implies it eventually gets
full, which is the opposite of the promise. Metaphors carry implications you did not choose.

---

## Layer 3 — Shape Language

**#8 unbroken line** — a ring with one continuous line passing through it, entering at the
lower-left and leaving at the upper-right. Not a closed ring: the line's ends are visible, which
is the whole point. Continuity means *ongoing*, not *complete*.

Silhouette test at 40px: passes. Reads as a ring with a stroke through it, which is legible and,
critically, unlike anything in the competitive set.

**#5 knot** — too much interior detail; the knot's crossings merge at 60px. Carried anyway.

**#6 tuning fork** — legible, but reads as audio in almost any context. Carried anyway.

---

## Layer 4 — Material Director

From `icon-dna/ai.md`, the explicit recommendation: the whole category renders in cold liquid
glass, so ceramic is the differentiating move. Taken.

```
Primary            Glazed ceramic, warm bone white — the ring
Secondary          Liquid glass, amber — the line
Reflection         Medium (on the line only)
Transparency       25% (line only; ring is opaque)
Edge               Soft chamfer
Surface finish     Semi-gloss glaze
```

**Rationale:** the ceramic ring is the persistent thing; the glass line is the thought passing
through it. Material carries the metaphor rather than merely decorating it — the permanent
element is the solid one, the transient element is the transparent one.

This is also the counter-move: five competitors render in cold indigo glass. A warm ceramic
body is visible in a grid of them at a glance.

---

## Layer 5 — Composition Director

```
Pattern          Centered, floating
Visual weight    Balanced; the line's diagonal is counterweighted by the ring's mass
Negative space   The ring's hole — the strongest available negative space
Balance          Asymmetric (the diagonal) over a symmetric base (the ring)
Focus point      Where the line passes behind the ring, upper-right
Perspective      Flat orthographic
Subject size     64% of canvas
Rotation         Line at 32° — well clear of the 3–8° accident zone
```

The line passes *behind* the ring at one crossing and *in front* at the other. That single
depth inversion is what makes it read as passing through rather than as an overlay, and it is
the detail most likely to be lost in an AI render — state it explicitly in the prompt.

---

## Layer 6 — Color Director

```
Category      AI — indigo/violet is saturated across five leaders
Rivals        OpenAI mono · Anthropic clay · Gemini blue-violet · Perplexity teal · Copilot gradient
Positioning   Persistent, warm, personal
Emotion       Steady
```

| Role | Hex | Name | Share | Rationale |
|---|---|---|---|---|
| Dominant | #0F172A | Deep slate | 60% | Field; near-neutral, lets the warm subject carry |
| Accent | #F5F0E8 | Bone | 30% | Ceramic ring; warm white, distinct from OpenAI's cool mono |
| Highlight | #F59E0B | Amber | 10% | The glass line; the warm counter-move |

Amber was chosen over terracotta specifically because terracotta is now Anthropic's, per the
DNA file's collision map. The warm move is right; the specific warm hue had to dodge.

Grayscale: bone L\* 95 vs slate L\* 18 — 77% delta. Amber line L\* 74 against bone L\* 95 —
21% delta, which is under the 25% guideline. **Fixed:** amber darkened to #D97706 (L\* 62),
giving 33%. This is exactly the kind of failure the grayscale check exists to catch.

---

## Layer 7 — Apple Reviewer

### Concept #8 — unbroken line through a ring

| Rejection | Verdict |
|---|---|
| R1 Too close to X | Pass — explicitly checked vs. ChatGPT, Claude, Gemini, Perplexity, Copilot. Nothing in the set uses a ring-with-through-line, and none uses warm ceramic. |
| R2 Too complex | Pass — one subject, one modifier |
| R3 Dirty on home screen | Pass |
| R4 Illegible at 40px | Pass — crossing survives to 32px |
| R5 No colour hierarchy | Pass after the amber correction |
| R6 Muddled materials | Pass — two |
| R7 Doesn't feel Apple | Pass |
| R8 Edges too sharp | Pass |
| R9 Light direction wrong | Pass |
| R10 Dates within 18 months | Pass — no sparkle, no iridescence, no gradient-as-idea |
| R11 Fails tinted/dark | Pass after correction |

| Axis | Score |
|---|---|
| Apple Feeling | 92 |
| Recognition | 94 |
| Material | 93 |
| Memorability | 90 |
| Scalability | 91 |
| Emotion | 88 |
| **Final** | **91.7** |

### #5 knot — Scalability 64. **Final 78.9**, killed (R4).
### #6 tuning fork — Recognition 71, reads as audio. **Final 82.3**, killed.

**Verdict:** 91.7 is in the 85–91 band, so one targeted iteration. Weakest axis is Emotion
(88) — "steady" is landing as "static." Iteration: increase the line's exit-side length by 15%
so it reads as continuing beyond the frame rather than terminating. Re-scored Emotion 92,
**Final 92.3.** Ship.

---

## Layer 8 — Image Prompt

```
App icon. A thick ring in warm bone-white glazed ceramic, with a single continuous amber
liquid-glass line passing through it at 32 degrees — passing behind the ring at the lower-left
crossing and in front of it at the upper-right crossing, both ends of the line visible and
extending toward the frame edges.
Centered, floating, subject occupies 64% of frame, generous even margin.
Material: glazed warm bone-white ceramic ring with soft subsurface scattering; the line is
liquid glass in deep amber with true internal refraction.
Lighting: single large soft key light from above at 12 degrees, gentle ambient fill from below,
thin rim highlight along the ring's top edge.
Color: deep slate #0F172A field, bone-white #F5F0E8 ceramic, deep amber #D97706 glass line.
Background: flat deep slate field with a subtle top-lighter two-stop vertical gradient.
Medium reflection on the glass line only, ceramic is semi-gloss, no visible environment,
neutral studio.
Shallow layered depth, clear separation between the line, the ring, and the field.
Straight-on orthographic view, no perspective distortion, no vanishing point.
Surface: fine glaze micro-variation on the ceramic, high optical clarity in the glass.
Shadow: short soft contact shadow directly beneath the ring, 15% opacity, no cast shadow.
Square 1:1, full bleed, 1024x1024, product icon render, Apple design language,
premium industrial design, extremely clean, minimal, single subject.

Negative: [standing list] + brain, neural network, node graph, chat bubble, sparkle, sparkles,
stars, robot, glowing orb, infinity symbol, circuit board, hologram, iridescent chrome,
indigo, violet, purple gradient
```

Note the negative prompt explicitly excludes indigo and violet. Image models have a strong
learned prior that "AI app icon" means purple, and it will reassert itself without this.

---

## Layer 9 — Icon Composer

Between the ceramic and liquid-glass rows, weighted toward ceramic since it is the larger area:

| Parameter | Value |
|---|---|
| Glass | 30% |
| Blur | 16% |
| Refraction | 42% |
| Specular | 58% |
| Shadow | soft |
| Depth | medium |
| Glow | weak |

**Layers:** background = slate gradient · mid = the ceramic ring · foreground = the amber
glass line. Three layers is correct here because the depth inversion at the crossings is real
geometry, not a drawn effect — Icon Composer can render it with actual parallax.

---

## Layer 10 — Icon Evolution

**Dead present?** None.

**Emerging present?** Liquid glass yes (as accent), layered depth yes, restrained palette yes,
monochrome-first yes.

**What would Apple do in 2026?**
- *Simplify further* — considered and rejected; the crossing is the metaphor, removing it
  removes the idea
- *Make the ceramic warmer* — accepted, #F5F0E8 → #F7F2E9
- *Reduce the line's transparency so it holds in clear mode* — accepted, 25% → 18%

Re-scored: **Final 92.5.** Ship.

---

## What this example demonstrates

- In a saturated category, the differentiating decision was **material**, not shape or
  metaphor. Warm ceramic in a field of cold glass is visible from across the room.
- The grayscale check caught a real failure (21% delta) that looked fine in colour.
- A metaphor's *implications* matter: the "vessel filling" concept was killed for implying a
  limit nobody intended.
- The negative prompt had to actively fight the model's category prior toward purple.
