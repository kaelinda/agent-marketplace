# Example — Video Editor

A professional video editor. Demonstrates the creation-side media register and the case where
the shortest route to the answer was killing the metaphor rather than refining the render.

---

## Layer 1 — Product Analyzer

| Question | Answer |
|---|---|
| What is it? | A node-based non-linear editor for short-form work |
| Why download? | Faster than the incumbents for the specific job of cutting short video |
| Why open? | There is footage and a deadline |
| Why daily? | It is where the work lives; the project files are here |
| Why remembered? | It does not stutter on a 4K timeline |

**Category:** media, **creation** side → read `icon-dna/media.md`

**Brand Essence:** *The cut, without friction.*

**Register (from media DNA):** creation, not consumption. This means the icon should read as an
instrument — closer to `developer.md` materially than to a streaming service.

---

## Layer 2 — Metaphor Generator

Exhausted list eliminated on sight: play triangle, film strip, clapperboard, waveform, camera.

| # | Axis | Metaphor | Dist | 40px | Fit | Long | Total | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Functional | A blade | 5 | 9 | 8 | 7 | 29 | killed — reads as a weapon or a utility knife |
| 2 | Functional | A splice point | 7 | 7 | 9 | 8 | 31 | kept |
| 3 | Emotional | A held breath | 5 | 4 | 6 | 7 | 22 | killed — not renderable as an object |
| 4 | Emotional | Precision in motion | 4 | 5 | 6 | 6 | 21 | killed — an adjective, not a metaphor |
| 5 | Physical | A reel of thread | 6 | 8 | 6 | 8 | 28 | killed — reads as sewing, or as film reel |
| 6 | Physical | Two surfaces meeting at a clean seam | 8 | 9 | 9 | 9 | **35** | **kept** |
| 7 | Physical | A machined caliper | 7 | 6 | 7 | 8 | 28 | killed — measurement, not cutting |
| 8 | Abstract | A gap in a continuous form | 8 | 8 | 8 | 9 | 33 | kept |
| 9 | Abstract | Interlocking teeth | 6 | 7 | 7 | 8 | 28 | killed — reads as a gear, category cliché |
| 10 | Brand | A node with converging edges | 7 | 5 | 8 | 7 | 27 | killed — depicts the UI |

**Survivors:** #6 clean seam · #8 gap in a continuous form · #2 splice point

Note #6 and #8 are close relatives — the seam is where two things meet, the gap is where one
thing is interrupted. They diverge sharply at layer 3.

---

## Layer 3 — Shape Language

**#6 clean seam** — a single machined block bisected by one perfectly straight seam, offset
slightly so the two halves are not equal. The offset is the design: an equal bisection reads as
symmetry, an offset one reads as an edit.

Silhouette test: passes as a rounded rectangle, but the *seam is not in the silhouette*. Flag —
this concept depends on interior contrast, so it will be tested hard in layer 7 for tinted mode.

**#8 gap in a continuous form** — a ring with a clean removed segment. Silhouette test: passes
strongly; the gap is in the outline. But it collides conceptually with the AI-chat example's
ring and, more importantly, with a large number of "loading" and "progress" glyphs.

**#2 splice point** — two forms joined at an angle. Silhouette passes; reads as an arrow or a
chevron, which is Strava-adjacent and directionally wrong.

**Selected for lead:** #6, with the tinted-mode risk flagged.

---

## Layer 4 — Material Director

Creation-side media, per the DNA file: matte anodised metal or dark ceramic, satin, minimal
reflection, instrument register.

```
Primary            Matte anodised graphite aluminium
Secondary          One luminous amber edge, along the seam only
Reflection         Subtle
Transparency       0%
Edge               Machined 45° chamfer
Surface finish     Matte, fine anisotropic grain
```

**Rationale:** the seam is the only place light gets in. That makes the cut literally luminous —
the edit is the source of light in the object — which is a rare case of the material and the
metaphor being the same decision.

---

## Layer 5 — Composition Director

```
Pattern          Centered, embedded (the block sits slightly into the field)
Visual weight    Balanced; the offset seam is the only asymmetry
Negative space   Even margin; the seam's dark line is the interior void
Balance          Asymmetric via the offset
Focus point      The luminous seam
Perspective      Flat orthographic
Subject size     68% of canvas
Seam offset      38 / 62 split, at 0° (horizontal)
```

The seam is horizontal and at 0°, not angled. An angled seam reads as dynamic, which is the
consumption register; a horizontal one reads as precise, which is correct here. Deliberate
choice against the more "interesting" option.

---

## Layer 6 — Color Director

```
Category      Media, creation side — dark chrome is the professional convention
Rivals        Final Cut blue-purple · Premiere violet · DaVinci Resolve dark grey-teal · CapCut black
Positioning   Fast, precise, professional
Emotion       Controlled
```

| Role | Hex | Name | Share | Rationale |
|---|---|---|---|---|
| Dominant | #101014 | Near-black | 60% | Field; matches the dark editors it sits beside |
| Accent | #3F3F46 | Graphite | 30% | The block; distinct from field but low contrast by design |
| Highlight | #F59E0B | Amber | 10% | The seam; the only saturated element |

Grayscale: graphite L\* 33 vs near-black L\* 8 — 25% delta, exactly at the guideline floor.
Amber seam L\* 74 against graphite L\* 33 — 41%. The seam carries the icon in tinted mode,
which resolves the layer-3 risk flag: the seam is bright enough to survive monochrome.

---

## Layer 7 — Apple Reviewer

### Concept #6 — bisected block, luminous seam

| Rejection | Verdict |
|---|---|
| R1 Too close to X | Pass — checked vs. Final Cut, Premiere, Resolve, CapCut, Descript |
| R2 Too complex | Pass |
| R3 Dirty on home screen | Pass — very quiet |
| R4 Illegible at 40px | Pass — the seam is a 2.5% -of-canvas bright line, survives to 24px |
| R5 No colour hierarchy | Pass |
| R6 Muddled materials | Pass — one material plus a light |
| R7 Doesn't feel Apple | Pass |
| R8 Edges too sharp | Pass — 45° chamfer |
| R9 Light direction wrong | **Note** — the seam is a light *source*, not a reflection. The key light from above must still produce a consistent top-chamfer specular. Both must be present and must not conflict. Verified consistent. |
| R10 Dates within 18 months | Pass |
| R11 Fails tinted/dark | Pass — seam delta 41% |

| Axis | Score |
|---|---|
| Apple Feeling | 90 |
| Recognition | 87 |
| Material | 95 |
| Memorability | 84 |
| Scalability | 93 |
| Emotion | 89 |
| **Final** | **89.4** |

### #8 gap in a ring — Recognition 72 (collides with progress/loading glyphs). **Final 83.0**, killed.
### #2 splice point — reads as a chevron; Recognition 70. **Final 81.4**, killed.

**Verdict:** 89.4, in the iterate band. Weakest is Memorability (84) — a graphite block with a
line is precise but not describable a day later. Iteration: shift the seam offset from 38/62 to
30/70 and add a 4% lateral displacement between the two halves, so the block reads as *cut and
slightly moved* rather than merely *scored*.

That single change converts the icon from "a block with a line" to "a block that has been
edited," which is the whole point of the product. Memorability 84 → 91.

**Final after iteration: 92.1.** Ship.

---

## Layer 8 — Image Prompt

```
App icon. A single machined block in matte graphite anodised aluminium, cut cleanly into two
unequal parts by one perfectly straight horizontal seam at a 30/70 split, the upper part
displaced 4% laterally from the lower, warm amber light emitting from within the seam.
Centered, slightly embedded into the field, subject occupies 68% of frame, generous even margin.
Material: matte anodised aluminium with fine anisotropic grain, 45-degree machined chamfer on
all edges, no gloss.
Lighting: single large soft key light from above at 12 degrees producing one thin specular
streak along the top chamfer; the seam is a separate warm internal light source, consistent
with the key light and not conflicting with it.
Color: near-black #101014 field, graphite #3F3F46 block, warm amber #F59E0B seam light.
Background: flat near-black field with a very subtle top-lighter two-stop vertical gradient.
Subtle reflection only, no visible environment, neutral studio.
Shallow layered depth, block crisply separated from the field.
Straight-on orthographic view, no perspective distortion, no vanishing point.
Surface: fine machined grain, matte, no gloss.
Shadow: short soft contact shadow directly beneath, 15% opacity, no cast shadow.
Square 1:1, full bleed, 1024x1024, product icon render, Apple design language,
premium industrial design, extremely clean, minimal, single subject.

Negative: [standing list] + play button, play triangle, film strip, clapperboard, waveform,
musical note, camera, timeline, scissors, blade, knife, glow everywhere, lens flare, neon,
two light sources
```

---

## Layer 9 — Icon Composer

Metal row, adjusted for the internal light:

| Parameter | Value |
|---|---|
| Glass | 12% |
| Blur | 10% |
| Refraction | 15% |
| Specular | 74% |
| Shadow | soft |
| Depth | shallow |
| Glow | medium |

Glow is `medium` here rather than the metal row's `none` — the seam is genuinely luminous and
this is one of the few cases where a stronger glow is correct rather than decorative.

**Layers:** background = near-black gradient · mid = lower block half · foreground = upper
block half. Splitting the two halves across layers lets Icon Composer render the 4% displacement
with real parallax, which is the single most valuable thing the tool does for this design.

---

## Layer 10 — Icon Evolution

**Dead present?** None.

**Emerging present?** Layered depth yes (and used meaningfully), restrained palette yes,
monochrome-first yes. Liquid glass absent and correctly so — glass on a precision instrument
would read as consumer.

**What would Apple do in 2026?**
- *Reduce the glow* — accepted; the amber was reading slightly hot. Reduced ~15%.
- *Warm the graphite* — rejected; cold graphite is the professional signal here
- *Split into more layers* — already done

**Final: 92.1.** Ship.

---

## What this example demonstrates

- The winning iteration was a **4% displacement** — the smallest change in any example here,
  and it moved Memorability seven points. Small geometry changes that alter the *meaning* beat
  large changes that alter the *appearance*.
- A layer-3 risk flag ("this depends on interior contrast") was carried forward and explicitly
  resolved at layer 6 rather than being forgotten.
- Two of three survivors died on Recognition against *glyph conventions* (progress rings,
  chevrons) rather than against named competitors. The shelf includes system glyphs, not just
  apps.
