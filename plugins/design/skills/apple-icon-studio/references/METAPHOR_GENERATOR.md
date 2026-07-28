# Metaphor Generator — Layer 2

The single highest-leverage layer. A strong metaphor makes every later decision easy; a weak
one cannot be rescued by material or colour.

---

## The core insight

Apple icons almost never depict the product. They depict a **metaphor** for what the product
does to your life.

| App | Not this | But this |
|---|---|---|
| AirDrop | A Wi-Fi / Bluetooth diagram | Radiating concentric circles |
| Files | A filesystem tree | A single folder |
| GarageBand | A DAW timeline | An electric guitar |
| Shortcuts | A workflow node graph | A layered diamond |
| Podcasts | A audio waveform | An antenna radiating |
| Photos | A photo | A colour pinwheel |
| Safari | A browser window | A compass |
| Freeform | A canvas UI | A blank board with a marker |

The pattern: **the metaphor is one step more abstract than the product, and one step more
concrete than the concept.** "A folder" is more abstract than "a file browser UI" and more
concrete than "storage." That middle rung is the target.

Too concrete → you have drawn a screenshot. Too abstract → you have drawn a generic gradient
sphere that could be anything.

---

## The five axes

Generate along all five. Each axis reliably produces different answers, which is the point —
generating ten variations on one axis produces ten near-identical icons.

### 1. Functional metaphor — *what it does*

The mechanical action, objectified. Ask: if this product were a physical tool on a workbench,
which tool?

- A note app → a sheet, a pen, a bookmark
- A search tool → a lens, a beam, a compass
- A backup tool → a vault, a strongbox, a duplicate

Strength: instantly legible. Weakness: the most crowded space — everyone lands here first, so
the functional metaphor is usually the one already taken.

### 2. Emotional metaphor — *how it should feel*

The feeling the product is selling, objectified. Ask: what is the user's emotional state
*after* a good session?

- A calm task manager → still water, a settled stone, dawn light
- A fast dev tool → a spark, a bolt, a slipstream
- A meditation app → a breathing sphere, an expanding ring

Strength: differentiates in crowded categories, because competitors sell the same function but
rarely the same feeling. Weakness: risks vagueness — an emotion with no object is a gradient.

### 3. Physical metaphor — *what real object behaves like this*

Ask: what physical thing exhibits the same *behaviour*? Not the same purpose — the same
behaviour.

- Version control → sedimentary layers, a braid, a river delta
- A clipboard manager → a stack of cards, a spring-loaded tray
- A sync service → two tuning forks in resonance

Strength: gives the material director something real to work with, because a real object has a
real surface. Physical metaphors produce the most convincing renders. Weakness: can drift
into skeuomorphism if rendered too literally.

### 4. Abstract metaphor — *the geometry of the idea*

Strip to pure form. Ask: if this idea had a shape and no representational content, what shape?

- Convergence → nested rings closing inward
- Branching → a trifurcating stem
- Transformation → a shape mid-morph between two states
- Recursion → a form containing a smaller copy of itself

Strength: scales perfectly, ages best, most "Apple." Weakness: needs the strongest justification
— an abstract mark with a weak rationale is indistinguishable from arbitrary decoration.

### 5. Brand metaphor — *the thing only this product could own*

Ask: what could no competitor put on their icon without it being obviously theft?

This is the hardest axis and the most valuable. It usually comes from something specific and
slightly odd about the product's origin, philosophy, or vocabulary — the internal codename, a
recurring word in the docs, a shape the UI already uses.

- Notion's blocks, Linear's speed lines, Raycast's ray, Arc's arc.

Strength: uncopyable by construction. Weakness: requires actually knowing the product deeply
— you cannot generate this from a one-line description.

---

## Generation protocol

1. **Two per axis, minimum.** Ten total. Fewer than ten and the kill step is meaningless
   because you never had real alternatives.
2. **Write each as a noun phrase, not a description.** "A layered diamond" — not "something
   that represents automation and layering."
3. **Do not self-censor during generation.** The obviously-bad ones calibrate the scale.
4. **Score, then kill 7.**

---

## Scoring rubric

Four axes, 0–10 each. Total out of 40.

### Distinctiveness (0–10)
Would this collide with an existing icon in the same category?

- 0–3: essentially an existing market-leader's icon
- 4–6: generic-but-clean; the category default
- 7–8: recognisably its own
- 9–10: nobody else could use this

### Legibility at 40px (0–10)
Does the metaphor survive at home-screen size?

- 0–3: requires detail to read at all
- 4–6: readable but loses its point
- 7–8: reads clearly, keeps meaning
- 9–10: reads faster than the label does

Complexity is the enemy here. "An electric guitar" scores lower than "a folder," which is why
GarageBand's guitar is rendered as a heavily simplified silhouette rather than a real guitar.

### Essence fit (0–10)
Is the line from Brand Essence to this metaphor short and obvious?

- 0–3: no traceable connection
- 4–6: connects via two or more inferential steps
- 7–8: one step, obvious once stated
- 9–10: feels inevitable in hindsight

The "inevitable in hindsight" quality is the marker of the winning metaphor. Nobody looks at
the Files icon and thinks "interesting choice."

### Longevity (0–10)
Will this still be right in five years?

- 0–3: depicts current hardware, a trend, or a temporary feature
- 4–6: tied to how the product works today
- 7–8: tied to what the product means
- 9–10: tied to a human constant

---

## The kill step

**Keep 3, kill 7, write down why each died.** The kill reasons go in the brief.

This is not ceremony. Recording the kills does three things:

1. Prevents the same dead end being re-proposed in the next round.
2. Gives the client the argument for the survivor — "we considered the obvious one, here is
   why it loses" is far more persuasive than presenting only the winner.
3. Forces honesty about *why* the winner won, which is often "it was first" rather than "it
   was best.

Standard kill reasons, phrased for the brief:

- *Collides with <competitor>* — the strongest kill; no further discussion needed
- *Dies below 60px* — legibility failure
- *Requires explanation* — if the metaphor needs a sentence, it fails at the moment of use
- *Category cliché* — the lightbulb for ideas, the rocket for launch, the brain for AI
- *Depicts the UI, not the meaning* — most common failure of the functional axis
- *No material affordance* — nothing physical to render; would end as a flat glyph
- *Trend-locked* — will read as "2026" in 2029

---

## Category clichés to kill on sight

These are not banned, but any of them needs an exceptional justification because the shelf is
saturated:

| Category | Cliché |
|---|---|
| AI | Brain, sparkle cluster, neural mesh, glowing orb, chat bubble |
| Productivity | Checkmark, clipboard, calendar grid |
| Finance | Upward arrow, dollar sign, bar chart, coin stack |
| Developer | Terminal prompt `>_`, angle brackets, gear |
| Media | Play triangle, film strip, waveform |
| Health | Heart, pulse line, water drop |
| Social | Speech bubble, two overlapping heads |
| Education | Graduation cap, open book, apple |
| Utilities | Wrench, gear, toolbox |
| Games | Controller, joystick, D-pad |

The sparkle cluster deserves special mention: from roughly 2023 it became the universal "this
has AI in it" marker, which means by 2026 it conveys no information and actively signals
follower rather than leader. See `icon-dna/ai.md`.

---

## Output format for layer 2

```markdown
| # | Axis | Metaphor | Dist | 40px | Fit | Long | Total | Verdict |
|---|------|----------|------|------|-----|------|-------|---------|
| 1 | Functional | A folded sheet | 4 | 9 | 7 | 8 | 28 | killed — category default |
| 2 | Abstract | Nested rings closing | 8 | 8 | 9 | 9 | 34 | **kept** |
...
```

Then, for each of the three survivors, one paragraph: what it depicts, why it fits the
essence, and what its biggest risk is. Carry all three into layer 3 — do not narrow to one
until after the critique in layer 7.
