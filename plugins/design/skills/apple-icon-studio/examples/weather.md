# Example — Weather App

A hyperlocal weather app. The hardest possible test of Recognition, because the category's
metaphor space is three symbols wide and Apple ships a system app in the same slot.

---

## Layer 1 — Product Analyzer

| Question | Answer |
|---|---|
| What is it? | Minute-by-minute precipitation for your exact location |
| Why download? | The system app was wrong about rain one too many times |
| Why open? | About to leave the house |
| Why daily? | It is a 3-second check that happens every morning |
| Why remembered? | It told them it would rain in 12 minutes and it did |

**Category:** utilities-adjacent, but the shelf is weather → no dedicated DNA file; use
`utilities.md` for the small-size constraints and treat the metaphor space independently.

**Brand Essence:** *The next twelve minutes.*

Swap test: wrong on Apple Weather (broad forecast), wrong on Windy (data depth), wrong on
Carrot (personality). It holds — and it is unusually specific, which is a good sign.

---

## Layer 2 — Metaphor Generator

The category's entire conventional vocabulary is: sun, cloud, raindrop, and combinations. All
three are exhausted at a level beyond any other category — they are not just used, they are
the *universal pictographic standard* for weather.

This is the case where the correct move is to **abandon the category vocabulary entirely** and
depict the essence instead. "The next twelve minutes" is a *time* metaphor, not a weather one.

| # | Axis | Metaphor | Dist | 40px | Fit | Long | Total | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Functional | Sun behind cloud | 1 | 9 | 4 | 9 | 23 | killed — Apple Weather, verbatim |
| 2 | Functional | A single raindrop | 2 | 9 | 5 | 9 | 25 | killed — universal standard |
| 3 | Functional | Radar sweep | 5 | 7 | 7 | 7 | 26 | killed — reads as military/aviation |
| 4 | Emotional | Being ready | 3 | 3 | 6 | 6 | 18 | killed — not an object |
| 5 | Physical | A window with light through it | 6 | 5 | 7 | 8 | 26 | killed — too much interior detail |
| 6 | Physical | A surface just before it is struck | 8 | 7 | 9 | 8 | 32 | kept |
| 7 | Physical | A barometer needle | 6 | 6 | 6 | 7 | 25 | killed — instrument, not imminence |
| 8 | Abstract | An arc segment — a slice of the coming hour | 8 | 9 | 9 | 9 | **35** | **kept** |
| 9 | Abstract | Concentric rings, one incomplete | 5 | 8 | 8 | 8 | 29 | killed — AirDrop collision |
| 10 | Brand | A held-open door | 7 | 6 | 7 | 7 | 27 | killed — reads as an entry/exit app |

**Survivors:** #8 arc segment · #6 surface before impact

Only two survived scoring above 30, which is honest — this category is genuinely constrained
and pretending otherwise would produce a padded list.

---

## Layer 3 — Shape Language

**#8 arc segment** — a thick arc occupying roughly 70° of a circle, positioned so the implied
full circle is obvious. The arc represents the near-future slice of time. Reading: "this much
is coming."

Silhouette test at 40px: passes strongly. An arc is one of the most legible small-size forms
available, because the eye completes the implied circle.

Risk: an arc is also the progress-indicator glyph and is used by Overcast and Spotify. Checked
in layer 7.

**#6 surface before impact** — a flat plane with a single perturbation. Silhouette test:
**fails.** The perturbation is a surface detail, not an outline feature; at 40px it becomes a
flat rectangle. Killed at layer 3 rather than carried, because a silhouette failure is not
recoverable by material.

**Selected:** #8, sole survivor into layer 4.

---

## Layer 4 — Material Director

Small-size constraints from `utilities.md` apply — this icon is checked at a glance, often in a
widget or a lock-screen context at reduced size.

```
Primary            Frosted glass — the arc
Secondary          Liquid glass, deeper tone, inner edge of the arc only
Reflection         Subtle
Transparency       40%
Edge               Soft rounded
Surface finish     Matte translucency
```

**Rationale:** frosted glass is the one material in the library that reads as *atmosphere*
without depicting a cloud. It carries the weather association through material rather than
through the exhausted pictographic vocabulary — which is the whole strategy of this design.

40% transparency is high and was checked against the legibility guidance in
`MATERIAL_LIBRARY.md`: at that level the silhouette must be exceptionally strong, which the arc
is. This is the case where the high-transparency exception is earned.

---

## Layer 5 — Composition Director

```
Pattern          Centered, floating
Visual weight    The arc's mass sits upper-right; counterweighted by nudging the whole form
                 left 2% and down 1%
Negative space   The implied-but-absent remainder of the circle — the designed void, and the
                 metaphor itself
Balance          Asymmetric
Focus point      The arc's leading end
Perspective      Flat orthographic
Subject size     66% of canvas (measured on the implied full circle, not the arc)
Arc span         70°, leading end at 1 o'clock
```

The negative space here is doing the semantic work: the missing 290° of circle is "the rest of
the day, which you did not ask about." That is the clearest case in these examples of negative
space carrying meaning rather than merely providing breathing room.

---

## Layer 6 — Color Director

```
Category      Weather — Apple Weather owns blue-to-blue gradients at system level
Rivals        Apple Weather blue gradient · Carrot orange-black · Windy dark data · Weather.com blue
Positioning   Immediate, precise, calm
Emotion       Reassured
```

| Role | Hex | Name | Share | Rationale |
|---|---|---|---|---|
| Dominant | #1E293B | Deep slate | 60% | Field; deliberately not sky-blue |
| Accent | #E0F2FE | Ice | 30% | The frosted arc; cool without being Apple Weather's blue |
| Highlight | #38BDF8 | Sky | 10% | Inner arc edge only |

Deliberate: the field is slate, not sky. Every weather app has a blue-gradient field. Making
the *field* neutral and letting the *subject* carry the cool tone inverts the category
convention and is instantly visible in a grid.

Grayscale: ice L\* 94 vs slate L\* 22 — 72% delta. Passes with room.

---

## Layer 7 — Apple Reviewer

### Concept #8 — arc segment in frosted glass

| Rejection | Verdict |
|---|---|
| R1 Too close to X | **Partial** — arc form is shared with Overcast (orange) and Spotify (green radiating arcs). Mitigated by: different span (70° vs. their near-full radiating sets), different count (one vs. three), and a completely different palette. Verdict: pass, but this is the icon's weakest point and it is the reason Recognition scores below the other examples. |
| R2 Too complex | Pass — one subject |
| R3 Dirty on home screen | Pass — very quiet |
| R4 Illegible at 40px | Pass — arcs downsample well |
| R5 No colour hierarchy | Pass |
| R6 Muddled materials | Pass — frosted plus liquid glass is normally a **flagged pairing** (see `MATERIAL_LIBRARY.md`), but here they occupy clearly separate geometry (body vs. inner edge) and differ in transparency by 25 points. Verified visually distinct. |
| R7 Doesn't feel Apple | Pass |
| R8 Edges too sharp | Pass |
| R9 Light direction wrong | Pass |
| R10 Dates within 18 months | **Note** — frosted glass is trend-adjacent. Mitigated: if the frosting were removed the arc still carries the design, so the trend is not the concept. Pass. |
| R11 Fails tinted/dark | Pass — 72% delta |

| Axis | Score |
|---|---|
| Apple Feeling | 93 |
| Recognition | 85 |
| Material | 92 |
| Memorability | 88 |
| Scalability | 96 |
| Emotion | 91 |
| **Final** | **90.1** |

**Verdict:** iterate band. Weakest is Recognition (85), and the cause is known: arc collision.
Iteration considered — add a single break in the arc, splitting it into a long segment and a
short one, which no competitor's arc has. Re-scored Recognition 85 → 90; but Scalability
dropped 96 → 91 as the break merges at 24px.

**Net: 90.1 → 90.8.** Marginal. The iteration was **accepted** on the grounds that Recognition
is the axis with a named, concrete failure mode while the Scalability loss is at 24px, below
the sizes the icon is actually used at.

**Final: 90.8.** Ship — with a note that this is the lowest-scoring example in the library and
that is a fair reflection of a genuinely constrained category, not a defect in the process.

---

## Layer 8 — Image Prompt

```
App icon. A single thick arc spanning about 70 degrees of an implied circle, its leading end at
the 1 o'clock position, with one clean narrow break dividing it into a long segment and a short
segment. Rendered in frosted translucent glass with a deeper liquid-glass inner edge.
Centered, floating, the implied full circle occupies 66% of frame, generous even margin,
offset 2% left and 1% down for optical balance.
Material: frosted glass with soft light diffusion and matte translucency, 40 percent
transparent; a narrower band of deeper liquid glass along the arc's inner edge only.
Lighting: single large soft key light from above at 12 degrees, gentle ambient fill, soft
backlight bloom through the frosted body, no sharp specular.
Color: deep slate #1E293B field, ice-white #E0F2FE frosted arc, sky #38BDF8 inner edge.
Background: flat deep slate field with a subtle top-lighter two-stop vertical gradient.
Subtle reflection, no visible environment, neutral studio.
Shallow layered depth, arc clearly separated from the field.
Straight-on orthographic view, no perspective distortion, no vanishing point.
Surface: smooth frosted diffusion, no texture, no grain.
Shadow: short soft contact shadow, 12% opacity, no cast shadow.
Square 1:1, full bleed, 1024x1024, product icon render, Apple design language,
premium industrial design, extremely clean, minimal, single subject.

Negative: [standing list] + sun, cloud, clouds, raindrop, rain, snowflake, lightning, storm,
rainbow, thermometer, umbrella, radar, map, sky, sky blue gradient, weather symbols,
progress ring, loading spinner
```

Note the negative prompt excludes *sky blue gradient* explicitly. The model's prior for
"weather app icon" is overwhelming and will reassert the blue field without this.

---

## Layer 9 — Icon Composer

Frosted glass row:

| Parameter | Value |
|---|---|
| Glass | 42% |
| Blur | 36% |
| Refraction | 28% |
| Specular | 32% |
| Shadow | soft |
| Depth | shallow |
| Glow | weak |

Refraction raised from the frosted row's 25% to 28% to let the inner liquid-glass edge do
visible work.

**Layers:** background = slate gradient · mid = none · foreground = the arc.

**Variants:** clear mode is the one to watch — a 40%-transparent ice-white arc over an
arbitrary wallpaper can wash out entirely. Mitigation: retain the contact shadow and add a
1px darker outer edge to the arc in the clear variant specifically.

---

## Layer 10 — Icon Evolution

**Dead present?** None. Notably, the entire sun/cloud/raindrop vocabulary is *not* on the dead
list — it is not dated, it is merely universal, which is a different and in some ways harder
problem.

**Emerging present?** Frosted/liquid glass yes, restrained palette yes, single subject yes.

**What would Apple do in 2026?** Honestly: Apple would probably ship the sun-behind-cloud,
because as the platform owner they benefit from the universal vocabulary rather than being
crowded out by it. That asymmetry is worth stating — **the right answer for Apple is not always
the right answer for a third-party app in Apple's store.** A challenger cannot win by matching
the incumbent's vocabulary.

Concrete diff applied: none. The design already reflects the challenger position correctly.

---

## What this example demonstrates

- When the category vocabulary is *universal* rather than merely crowded, the correct move is
  to leave it entirely and depict the essence instead.
- A concept was killed at **layer 3** (silhouette failure), not carried to critique. Silhouette
  failures are not recoverable downstream and carrying them wastes a round.
- An iteration was accepted despite a net score gain of only 0.7, because the axes are not
  equivalent in *kind*: a named collision is a concrete defect, a 24px degradation is
  theoretical.
- The lowest-scoring example in the library, honestly reported. Not every category permits a 94.
