# Composition Director — Layer 5

Where the subject sits, how much room it gets, and what the empty space is doing. Composition
is what makes an icon look *designed* rather than *centred by default*.

---

## Canvas geometry

Work at **1024×1024**. Full bleed — do not draw the rounded corners; the system masks them.

```
┌──────────────────────────────────┐  1024
│  ← 10% margin: nothing here →    │
│   ┌────────────────────────┐     │
│   │                        │     │
│   │   SUBJECT              │     │  subject box ≈ 60–70% of canvas
│   │   614–717 px           │     │  ≈ 614–717 px
│   │                        │     │
│   └────────────────────────┘     │
│                                  │
└──────────────────────────────────┘
```

- **Subject:** 60–70% of canvas width. Below 55% the icon looks lost; above 75% it looks
  cramped and will collide with the corner mask.
- **Margin:** ≥10% (102px) on all sides, meaningful content only.
- **Corner exclusion:** the outer corner arcs — roughly a 180px radius region at each corner —
  are background field only. The squircle mask eats them.
- **Optical centre:** ~2% above mathematical centre for most subjects. Bottom-heavy forms need
  more; radially symmetric forms need none.

---

## The eight patterns

### 1. Centered
Subject dead centre, symmetrical, equal margins.

- **Reads as:** authoritative, stable, timeless, confident
- **Use when:** the metaphor is strong enough to carry the icon with no compositional help
- **Risk:** the default, so it does nothing to differentiate; a weak metaphor centred is just
  a weak metaphor
- **Examples:** Safari, Podcasts, Clock

### 2. Floating
Subject centred but visually lifted off the background — separated by shadow, scale, and
depth-of-field rather than position.

- **Reads as:** premium, light, modern, dimensional
- **Use when:** the subject is a discrete object and the material can carry depth
- **Requires:** a contact shadow and a background field with slight blur or gradient falloff
- **Risk:** the shadow doing too much work; keep it soft, short, and under 20% opacity

### 3. Diagonal
Subject rotated 12–45°, often with a directional axis corner to corner.

- **Reads as:** energetic, dynamic, in motion, forward
- **Use when:** the essence involves speed, progress, or transformation
- **Risk:** rotation between 3° and 8° reads as a mistake rather than a decision. Commit to
  ≥12° or to 0°.

### 4. Framed
Subject inside an explicit inner frame, ring, or aperture.

- **Reads as:** focused, contained, curated, precise
- **Use when:** the product is about looking at something, or about boundaries and scope
- **Risk:** a rectangular frame inside a rounded-square canvas creates shape echo; use a
  circle or a distinctly different form for the frame

### 5. Stacked
Two or three layers offset in depth or position.

- **Reads as:** history, versioning, composition, accumulation
- **Use when:** the metaphor is about layers, iterations, or built-up state
- **Rule:** three layers maximum. Four becomes texture and dies at 40px.
- **Examples:** Shortcuts, Photos (radially stacked)

### 6. Embedded
Subject partially inset into the background plane rather than sitting on it.

- **Reads as:** integrated, native, systemic, part of the platform
- **Use when:** the product extends a system rather than sitting beside it
- **Requires:** inner shadow along the top edge of the inset, and a matching lower highlight

### 7. Nested
A form containing a smaller instance of itself, or concentric containment.

- **Reads as:** recursion, depth, focus, containment, "inside"
- **Use when:** the metaphor is recursive or about cores and shells
- **Rule:** concentric radii — outer radius minus gap equals inner radius. Getting this wrong
  is immediately visible even to non-designers.

### 8. Suspended
Subject held in the field with visible space above and below, often with a light source
implying it hovers.

- **Reads as:** weightless, considered, gallery-like, precious
- **Use when:** the object is small and the negative space is the statement
- **Risk:** at 40px a small suspended subject becomes a dot; only use when the subject can
  still occupy ≥50% of canvas

---

## Five analyses

Run all five before locking the composition.

### Visual weight
Every element has perceived weight from size, darkness, saturation, and detail density. Sum
them and find the centre of mass. If it is not at (or very near) the optical centre, the icon
will feel like it is tipping.

Adjust by moving, resizing, or — usually best — desaturating the heavy element.

### Negative space
The empty space is a designed element, not leftover. Ask:

- Is the negative space a *coherent shape*, or arbitrary leftover?
- Is it distributed, or pooling on one side?
- Does it carry meaning? (a ring's hole, a crescent's cut)

The strongest icons have negative space you could describe as a shape in its own right.

### Balance
Symmetric balance: calm, formal, stable. Easy to achieve, easy to make boring.
Asymmetric balance: dynamic, contemporary, harder — a large light element balanced against a
small dark one. When it works it is more interesting; when it fails it just looks off.

Choose one deliberately. Near-symmetry is the worst outcome — it reads as failed symmetry.

### Focus point
Exactly one. The place the eye lands first, driven by the highest local contrast, the
convergence of implied lines, or the brightest specular.

If two areas compete for first fixation, the icon reads as busy even when it is simple.

### Perspective
- **Flat / orthographic** — safest, most timeless, most Apple. Default here.
- **Slight isometric** — adds dimension without a scene; acceptable for stacked layers.
- **True perspective with a vanishing point** — avoid. It implies a camera in a room, and an
  icon does not live in a room.

Depth should come from *material and layering*, not from camera angle. This is the single most
common way an otherwise good icon stops looking native.

---

## Background field

The background is a field, never a scene.

| Option | When |
|---|---|
| Flat single colour | Maximum silhouette clarity; safest for complex subjects |
| Two-stop linear gradient, 15–30% luminance delta, top-lighter | The default; reads as designed |
| Soft radial glow behind the subject | When the subject should feel luminous |
| Very subtle noise/grain (<3%) | Kills banding on large gradients; invisible at 40px |

Never: photographic textures, landscapes, patterns with representational content, or anything
that competes with the subject for the focus point.

---

## Composition checklist

- [ ] Subject occupies 60–70% of canvas
- [ ] ≥10% clear margin on all sides; nothing in the corner arcs
- [ ] Optically centred (not merely mathematically centred)
- [ ] Exactly one focus point
- [ ] Negative space is a describable shape
- [ ] Balance is decisively symmetric or decisively asymmetric
- [ ] Rotation is 0° or ≥12°, never 3–8°
- [ ] No true-perspective vanishing point
- [ ] Background is a field, not a scene
- [ ] Maximum three stacked layers
- [ ] Nested forms use concentric radii
