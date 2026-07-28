# Shape Language — Layer 3

The silhouette is the only thing that survives at every size, in every rendering mode, in
peripheral vision, and in tinted mode. Choose it deliberately.

---

## Primary shapes

### Circle

**Reads as:** friendly, calm, balanced, complete, human, safe

The most approachable form. No corners means no aggression; radial symmetry means no implied
direction, so it reads as "at rest."

- **Use when:** the essence is calm, wellness, community, completeness, or continuity
- **Avoid when:** the product's promise is speed, precision, or power — a circle will read as
  soft and slightly passive
- **Risk:** the single most-used shape in app icons; a plain circle needs material or a
  distinctive interior to avoid disappearing into the shelf
- **Apple examples:** Safari (compass), Podcasts (radiating), Clock

### Square / rounded rectangle

**Reads as:** reliable, stable, professional, structured, systematic

Grounded and orthogonal. Reads as infrastructure. Because the icon canvas is itself a rounded
square, an inner square risks looking like a frame rather than a subject — it needs rotation,
offset, or a material contrast to read as an object.

- **Use when:** the essence is organisation, structure, storage, or enterprise trust
- **Avoid when:** the essence is creative or playful; squares read as institutional
- **Risk:** shape-echo with the canvas mask
- **Apple examples:** Notes, Numbers, Files (folder is a modified rectangle)

### Triangle

**Reads as:** speed, energy, direction, ascent, focus

The only primary shape with inherent direction. A triangle points, and the eye follows. That
directionality is powerful and hard to neutralise — a triangle is never neutral.

- **Use when:** the essence involves movement, playback, growth, or navigation
- **Avoid when:** the product is contemplative or ambient; a triangle injects urgency
- **Risk:** the play triangle is so overloaded in media that any triangle in a media app reads
  as "play" whether intended or not
- **Apple examples:** Music (implied), Compass needle

### Diamond (rotated square)

**Reads as:** automation, precision, technology, value, crystalline logic

A square rotated 45° stops reading as architecture and starts reading as a gem or a node. It
carries a strong sense of engineered precision.

- **Use when:** the essence is automation, orchestration, transformation, or systems
- **Avoid when:** warmth matters; the diamond is cool and impersonal
- **Risk:** reads as "blockchain" in fintech contexts
- **Apple examples:** Shortcuts (layered diamond) — the canonical case

### Organic blob / fluid form

**Reads as:** creativity, play, warmth, generativity, softness

Asymmetric, hand-drawn-feeling, alive. Signals that the product is not rigid.

- **Use when:** the essence is creative, generative, playful, or child-facing
- **Avoid when:** the product must convey precision or trust with money/health data
- **Risk:** the hardest shape to make legible at 40px, because an organic form has no canonical
  outline for the eye to complete; also the most trend-exposed
- **Apple examples:** Freeform, Photos (the pinwheel is a controlled organic radial)

---

## Secondary and compound forms

### Hexagon
Modular, networked, technical-but-warm (warmer than the diamond). Reads as "system of parts."
Overused in blockchain and biotech.

### Arc / crescent
Motion, progress, partial completion, protection. Excellent for progress-oriented products.
Its openness makes it feel in-progress rather than finished, which is either the point or a
problem.

### Ring / annulus
Cycle, continuity, focus, containment. The hole is the design — it creates instant negative
space and gives the interior somewhere to live. Very strong at small sizes because the hole
survives downsampling better than an interior detail does.

### Spiral
Depth, recursion, growth, inward focus. Beautiful at 1024, generally fails below 60px as the
inner turns merge. Use only if the outer two turns alone still read.

### Layered stack
Depth, history, composition, versioning. Currently well aligned with Apple's layered-material
direction. Three layers maximum; four becomes texture.

### Negative-space form
The subject defined by what is *removed* from a field rather than what is added — FedEx's
arrow being the canonical non-Apple example. Highest craft signal when it works, complete
failure when it does not read instantly. It either lands in under a second or it is not a
negative-space form, it is a mistake.

---

## Choosing

Work backwards from the Brand Essence, not forwards from taste.

```
Brand Essence
   → What is the emotional register?   (calm / urgent / precise / warm / powerful)
   → Does the metaphor imply direction? (if yes, the shape must accommodate it)
   → What does the category already use? (avoid the saturated shape)
   → Which shape says this before any detail resolves?
```

### Essence → shape starting points

| If the essence is… | Start with |
|---|---|
| Calm, focus, wellbeing | Circle, ring |
| Structure, reliability, records | Rounded rectangle, layered stack |
| Speed, execution, shipping | Triangle, arc |
| Automation, orchestration | Diamond, hexagon |
| Creation, generation, play | Organic blob, spiral |
| Depth, memory, history | Layered stack, ring |
| Intelligence, synthesis | Sphere-in-ring, nested forms |
| Protection, trust | Shield-arc, ring, rounded rect |

These are starting points, not conclusions. The best outcome is often a *deliberate* mismatch
— a calm product in a triangle, justified — but a mismatch has to be argued, not stumbled into.

---

## The silhouette test

Mandatory before proceeding to layer 4.

1. Render (or describe) the concept as **solid black on white**, no interior detail, no colour.
2. Downsample to **40px**.
3. Ask three questions:
   - Is the outline still a coherent, closed, describable form?
   - Could it be confused with another app on a typical home screen?
   - Does the shape alone still gesture at the metaphor?

Failing any of these means the design is leaning on colour or detail, and it will collapse in
tinted mode and at small sizes.

---

## Geometry notes

- **Optical centring, not mathematical centring.** A triangle centred by bounding box looks
  low; shift it up ~2–3% of canvas. Circles look correct at mathematical centre. Any form with
  more visual weight at the bottom needs to be nudged up.
- **Optical size compensation.** A circle at the same bounding-box size as a square looks
  smaller. Scale circles up ~4–5% to match perceived size when designing a family.
- **Corner radii should be related, not identical.** Nested rounded forms need *concentric*
  radii (outer radius − gap = inner radius), otherwise the shapes look like they were drawn
  by different people.
- **Stroke weight floor.** No stroke thinner than 1/40 of the canvas (≈25px at 1024) if it
  needs to survive to 40px. Below that, convert the stroke to a filled shape.
- **Rotation.** 45° reads as deliberate; 12–20° reads as dynamic; 3–8° reads as an accident.
  Avoid the accident zone.
