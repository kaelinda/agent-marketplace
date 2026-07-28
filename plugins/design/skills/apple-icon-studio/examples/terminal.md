# Example — Terminal Emulator

A GPU-accelerated terminal. Demonstrates the developer register, the menu-bar size constraint,
and a case where the correct answer was **monochrome** — no accent colour at all.

---

## Layer 1 — Product Analyzer

| Question | Answer |
|---|---|
| What is it? | A GPU-rendered terminal emulator with native splits and a config file |
| Why download? | The default terminal drops frames scrolling a large log |
| Why open? | It is open all day; it is the workspace |
| Why daily? | It *is* the daily work |
| Why remembered? | It is instant. Nothing about it is ever waiting on the terminal. |

**Category:** developer → read `icon-dna/developer.md`

**Brand Essence:** *No latency between thought and command.*

Compressed further for the icon: *Instant.*

**Credibility constraint (from developer DNA):** this audience reads over-design as a signal
that effort went into marketing rather than the tool. Restraint is not a stylistic preference
here, it is a functional requirement.

---

## Layer 2 — Metaphor Generator

Exhausted, killed on sight: `>_` prompt, angle brackets, curly braces, gear, terminal window.

| # | Axis | Metaphor | Dist | 40px | Fit | Long | Total | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Functional | A cursor block | 3 | 9 | 7 | 8 | 27 | killed — every terminal app |
| 2 | Functional | A single keystroke depressing | 6 | 6 | 8 | 7 | 27 | killed — needs motion to read |
| 3 | Emotional | Zero resistance | 4 | 4 | 7 | 7 | 22 | killed — not an object |
| 4 | Emotional | A struck match | 6 | 7 | 6 | 7 | 26 | killed — "fast" but also "consumable" |
| 5 | Physical | A machined key / bit | 8 | 8 | 7 | 9 | 32 | kept |
| 6 | Physical | A chisel edge | 8 | 8 | 8 | 9 | **33** | **kept** |
| 7 | Physical | A tuning peg | 7 | 6 | 5 | 8 | 26 | killed — configuration, not speed |
| 8 | Abstract | A single vertical bar with a clean chamfer | 7 | 9 | 8 | 9 | 33 | kept |
| 9 | Abstract | A plumb line | 7 | 7 | 6 | 8 | 28 | killed — correctness, not speed |
| 10 | Brand | A caret rendered as a physical object | 8 | 8 | 8 | 8 | 32 | killed — too close to #1 and #8 to be a distinct option |

**Survivors:** #6 chisel edge · #8 chamfered vertical bar · #5 machined key

#8 deserves comment: a vertical bar is *also* a text cursor, which is #1's territory. It scored
well because the chamfer converts it from a glyph into an object — the difference between
depicting the cursor and depicting a *tool that is shaped like* the cursor. That distinction is
the entire design.

---

## Layer 3 — Shape Language

**#6 chisel edge** — a wedge form, viewed edge-on, tapering to a fine line at the bottom.
Silhouette at 40px: passes, but reads as a triangle, and a triangle in a dev-tool icon reads as
Vercel-adjacent.

**#8 chamfered vertical bar** — a tall rounded rectangle with a pronounced 45° chamfer along
one vertical edge. Silhouette at 40px: passes cleanly. **At 16px (menu bar): passes** — this is
the only survivor that does, and per `utilities.md`'s menu-bar constraint that is close to
decisive for a terminal that ships a menu-bar presence.

**#5 machined key** — the bit's teeth merge below 48px. Fails the menu-bar test.

**Selected:** #8, with #6 carried to critique.

---

## Layer 4 — Material Director

Developer DNA is unambiguous: matte anodised metal, machined chamfer, no gloss.

```
Primary            Matte anodised aluminium, warm graphite
Secondary          None — the chamfer is a geometry feature, not a second material
Reflection         Subtle
Transparency       0%
Edge               45° machined chamfer, the design's entire craft signal
Surface finish     Matte, fine anisotropic grain
```

**One material.** Not two. This is the only example in the library that uses a single material,
and it is deliberate: in a category where restraint is the credibility signal, dropping to one
material is itself a statement. The chamfer provides all the surface variation needed because
it catches the key light differently from the face.

---

## Layer 5 — Composition Director

```
Pattern          Centered, floating
Visual weight    Vertically balanced; the chamfer's highlight sits left, counterweighted by
                 shifting the bar 1.5% right
Negative space   Generous and even — the bar is narrow, so the field is most of the icon
Balance          Asymmetric (single chamfered edge) over a symmetric form
Focus point      The chamfer highlight
Perspective      Flat orthographic
Subject size     Bar height 64% of canvas, width 18% — the implied bounding box is 64%
Rotation         0°
```

The bar is narrow, which means a large amount of empty field. That is correct and it should not
be "fixed" by scaling up: the emptiness reads as confidence, and it is what makes the icon
quiet enough to sit in a dock all day.

---

## Layer 6 — Color Director

```
Category      Developer — monochrome plus one accent is the strongest formula
Rivals        VS Code blue ribbon · Cursor near-black angular · iTerm · Warp gradient · Ghostty
Positioning   Instant, precise, no ceremony
Emotion       Certainty
```

Considered a single accent (terminal green #22C55E or amber #F59E0B) per the DNA file's
standard formula. **Rejected.**

Reasoning: the accent would be the only saturated element and would therefore become the focus
point, displacing the chamfer. But the chamfer *is* the design — it is the craft signal that
carries the whole "precision instrument" read. An accent colour would make the icon slightly
more eye-catching and considerably less coherent.

| Role | Hex | Name | Share | Rationale |
|---|---|---|---|---|
| Dominant | #0C0C0E | Near-black | 70% | Field; matches the terminal it launches |
| Accent | #52525B | Graphite | 25% | The bar face |
| Highlight | #D4D4D8 | Light grey | 5% | The chamfer catching the key light |

**Pure monochrome.** Three values, one hue-neutral family.

Grayscale: identical to the colour version by construction, which means tinted mode is a
non-issue — the strongest possible outcome on R11. Graphite L\* 38 vs near-black L\* 6 —
32% delta.

---

## Layer 7 — Apple Reviewer

### Concept #8 — chamfered vertical bar, monochrome

| Rejection | Verdict |
|---|---|
| R1 Too close to X | Pass — checked vs. VS Code, Cursor, iTerm, Warp, Ghostty, Alacritty. Cursor is the nearest (near-black, angular) but is a distinctly different form. |
| R2 Too complex | Pass — one subject, no modifier |
| R3 Dirty on home screen | Pass — the quietest icon in the library |
| R4 Illegible at 40px | Pass — and at 16px, verified |
| R5 No colour hierarchy | Pass — value hierarchy is explicit, 70/25/5 |
| R6 Muddled materials | Pass — one material |
| R7 Doesn't feel Apple | Pass — machined chamfer is squarely in Apple's industrial-design idiom |
| R8 Edges too sharp | Pass — the chamfer *is* the edge treatment |
| R9 Light direction wrong | Pass — single source, one highlight, one contact shadow |
| R10 Dates within 18 months | Pass — monochrome and machined geometry have no trend exposure |
| R11 Fails tinted/dark | Pass trivially — already monochrome |

| Axis | Score |
|---|---|
| Apple Feeling | 95 |
| Recognition | 88 |
| Material | 94 |
| Memorability | 87 |
| Scalability | 98 |
| Emotion | 89 |
| **Final** | **92.4** |

### #6 chisel — reads as a triangle, Vercel-adjacent. Recognition 74. **Final 84.1**, killed.

**Verdict:** 92.4 — above the 92 ship threshold. Ship without iteration.

Weakest axis is Memorability (87), which is the expected cost of extreme restraint: a
monochrome bar is harder to describe from memory than a coloured object. That trade was made
knowingly at layer 6 in exchange for Apple Feeling 95 and Scalability 98, and Scalability is
weighted 1.5×. The arithmetic supports the trade.

---

## Layer 8 — Image Prompt

```
App icon. A single tall narrow bar in matte warm-graphite anodised aluminium, with one
pronounced 45-degree machined chamfer running the full length of its left vertical edge,
the chamfer catching a single clean light-grey specular.
Centered, floating, bar height 64% of frame and width 18%, offset 1.5% right for optical
balance, generous empty field on all sides.
Material: matte anodised aluminium with fine anisotropic surface grain, single material
throughout, no gloss, no second material.
Lighting: single large soft key light from above at 12 degrees, gentle ambient fill from below,
the chamfer is the only bright surface.
Color: near-black #0C0C0E field, graphite #52525B bar face, light grey #D4D4D8 chamfer
highlight. Strictly monochrome, no colour hue anywhere.
Background: flat near-black field with a very subtle top-lighter two-stop vertical gradient.
Subtle reflection only, no visible environment, neutral studio.
Shallow layered depth, bar crisply separated from the field.
Straight-on orthographic view, no perspective distortion, no vanishing point.
Surface: fine machined grain, matte, no gloss anywhere.
Shadow: short soft contact shadow directly beneath, 12% opacity, no cast shadow.
Square 1:1, full bleed, 1024x1024, product icon render, Apple design language,
premium industrial design, extremely clean, minimal, single subject, extremely restrained.

Negative: [standing list] + terminal window, command prompt, dollar sign, caret, cursor,
angle brackets, curly braces, code, syntax highlighting, gear, cog, green text, matrix,
retro CRT, scanlines, glow, neon, colour, coloured accent, gradient on subject, mascot
```

`colour, coloured accent` in the negative prompt is doing real work — image models will add a
green or amber accent to a terminal icon unprompted, because the training distribution for
"terminal" is saturated with it.

---

## Layer 9 — Icon Composer

Metal row, near-verbatim:

| Parameter | Value |
|---|---|
| Glass | 14% |
| Blur | 10% |
| Refraction | 16% |
| Specular | 80% |
| Shadow | soft |
| Depth | shallow |
| Glow | none |

Specular raised to 80% from the metal row's 78% — the chamfer highlight is the only bright
element and it should be crisp.

**Layers:** background = near-black gradient · mid = none · foreground = the bar.

Two layers only. There is no depth relationship to render, and adding a third layer to "use the
feature" would be exactly the over-design this category punishes.

**Variants:** dark — the field is already near-black, so author the dark variant as near
identical with the chamfer highlight raised ~6% to compensate for the darker surround.
clear — the graphite bar is mid-value and survives any wallpaper; retain the contact shadow.
tinted — identical by construction.

---

## Layer 10 — Icon Evolution

**Dead present?** None. Specifically checked for the retro-CRT and green-phosphor register,
which is a live temptation in terminal branding and is thoroughly period-coded.

**Emerging present?** Monochrome-first yes, single subject yes, restrained palette yes,
machined material yes. Liquid glass deliberately absent — glass on a precision instrument reads
as consumer, per `developer.md`.

**What would Apple do in 2026?**
- *Add a material accent* — rejected, for the same reason the colour accent was rejected at
  layer 6
- *Soften the chamfer* — rejected; the chamfer's crispness is the craft signal
- *Widen the bar slightly for presence at 16px* — accepted, width 18% → 20%. Verified: still
  reads as a bar, not as a block, and gains meaningfully in the menu bar.

Re-scored after the diff: Scalability 98 → 99, Final 92.4 → **92.6.** Ship.

---

## What this example demonstrates

- **One material, three values, no colour.** The most restrained result in the library, and the
  highest Apple Feeling and Scalability scores. Restraint is not a compromise, it is a strategy.
- The accent colour was rejected on a *structural* argument (it would displace the focus point
  from the element carrying the design), not on taste.
- Menu-bar legibility at 16px eliminated two of three survivors at layer 3. Knowing where an
  icon actually lives changes which layer does the killing.
- Memorability was knowingly traded down for Scalability, and the weighted formula was the
  arbiter. That is what the weighting is for.
