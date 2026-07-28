# Design Principles

The non-negotiables. Everything in the other reference files is a choice; this file is the
set of constraints those choices must satisfy. Read this on every run.

---

## 1. Silhouette first

Before colour, before material, before detail: if the black-filled silhouette of the icon is
not recognisable, nothing downstream will save it.

**Test:** flatten the concept to a solid black shape on white. Can you still tell which app it
is? If not, the shape is doing no work and the icon is relying entirely on colour — which
fails the moment it sits next to another app of the same hue.

Apple icons that pass this trivially: Podcasts (antenna radiating), Shortcuts (layered
diamond), Compass, Photos (pinwheel), Weather (sun behind cloud).

## 2. One subject

Exactly one subject per icon. Not "a document and a pen and a sparkle." One.

The most common failure in AI-generated icons is the accumulation of tiny secondary elements —
a badge, a sparkle, a small gear in the corner — each individually defensible, collectively
producing noise. At 40px those elements are not "subtle detail," they are dirt.

If the concept genuinely needs two elements, one of them must be a *modifier* of the other
(the sparkle *on* the sphere), not a *peer* beside it.

## 3. Legible at 40px, distinctive at 1024

Both directions matter and they pull against each other.

- **40px** (home screen, spotlight, notification): shape and colour only. Any line thinner
  than roughly 1/40 of the canvas disappears. Any text disappears. Any gradient with less than
  ~25% luminance delta becomes a flat field.
- **1024px** (App Store, Finder, marketing): the render must reward inspection. Material
  detail, refraction, micro-texture, edge highlight — this is where the craft lives.

Design the shape for 40 and the surface for 1024. An icon designed only at 1024 turns to mush;
an icon designed only at 40 looks cheap in the store.

**Mandatory check:** render or mentally downsample to 40px and 16px before scoring.

## 4. Safe area and the corner mask

The system applies a rounded-rectangle (or, increasingly, a squircle) mask. The canvas is
1024×1024 but the *usable* area is not.

- Subject occupies **60–70%** of the canvas, centred.
- Leave **~10%** margin on all sides. Nothing meaningful in the outer 10%.
- **Nothing crosses the corner radius.** Corners are for background field only.
- Do not draw the rounded corners yourself. Supply a full-bleed square; the system masks it.
  A pre-rounded icon rendered onto a rounded mask produces a visible double-radius artifact.

An icon that fills 90% of the canvas does not look "bigger," it looks cramped — the negative
space *is* the composition.

## 5. Single, consistent light source

Pick one light direction and hold it across every surface, highlight, and shadow.

Apple's convention: **light from above, slightly front**, roughly 10–15° off vertical. Top
edges catch a specular highlight, bottom edges carry contact shadow, and the shadow falls
short and soft rather than long and hard.

Two light sources is the fastest way to make a render read as "AI-generated." Conflicting
speculars on opposite edges is the specific tell.

## 6. Depth over flatness, but never literal 3D

Current Apple language is volumetric — layered, refractive, with real material behaviour — but
it is not a perspective render of an object sitting in a room.

- **Yes:** layered depth, parallax between background/mid/foreground, soft internal shadow,
  refraction through glass.
- **No:** vanishing-point perspective, cast shadows onto a visible ground plane, an object
  photographed at a three-quarter angle.

The icon lives *on* the glass of the screen, not *behind* it in a scene.

## 7. Background is a field, not a scene

The background layer is a single flat colour, a two-stop gradient, or a subtle radial. It is
never a landscape, a room, a desk, or a texture with representational content.

A two-stop vertical gradient with 15–30% luminance delta is the safest default and reads as
"designed" rather than "flat."

## 8. Colour hierarchy

Two to three hues. One dominant (60–70% of the visible area), one accent (20–30%), optionally
one highlight (<10%).

If three colours are competing for the same visual weight, the eye has no entry point and the
icon reads as busy even when the shape is simple. See `COLOR_SYSTEM.md`.

## 9. No text, no wordmarks, no numbers

Except when the letterform *is* the brand and is a single character (a monogram). Even then,
one character, geometric, and it must still pass the 40px test.

Multi-letter wordmarks in an app icon are a hallmark of amateur work and are unreadable at
every size the icon is actually used at.

## 10. Distinctiveness is measured against the shelf, not in isolation

An icon is never seen alone. It is seen in a grid of 24 other icons, half of which are in the
same category and were designed with the same references.

**Test:** place the concept in a mental 5×5 grid alongside the five most likely neighbours
(for an AI app: ChatGPT, Claude, Gemini, Perplexity, Copilot). Does the eye find it? If it
requires reading the label, the icon has failed its primary job.

This is why layer 7's "too close to X" rejections are not nitpicking — proximity to a
market-leading icon is a functional defect, not a taste disagreement.

## 11. It must survive dark mode and tinted mode

Modern iOS renders three variants: light, dark, and tinted (monochrome). The design must hold
in all three.

- **Dark:** the background field darkens; the subject must not disappear into it. A dark
  subject on a dark field needs an edge highlight or a luminous material.
- **Tinted:** all colour is stripped and replaced by a single system hue applied to a
  grayscale rendering. **Everything colour was doing is gone.** If the concept only worked
  because of a colour contrast, tinted mode exposes it.

Tinted mode is, in effect, principle #1 (silhouette first) enforced by the operating system.

## 12. Longevity

Ask: will this look dated in 24 months?

Signals that date fast: whatever visual trick is currently trending in AI-generated design
work (as of 2026: iridescent chrome blobs, aurora gradients, glassmorphism applied for its own
sake), literal depictions of current-generation hardware, and any style that is legible
primarily as "made by an image model."

Signals that age well: a clear metaphor, a strong silhouette, restrained colour, and material
honesty. Every Apple icon that has survived a decade has these and little else.

---

## Quick gate

An icon concept that cannot answer all of these does not proceed to layer 8:

- [ ] Recognisable as a black silhouette
- [ ] Exactly one subject
- [ ] Legible at 40px
- [ ] Subject within 60–70% of canvas, nothing in the corner radius
- [ ] One light direction
- [ ] Background is a field, not a scene
- [ ] Two to three hues with clear hierarchy
- [ ] No text
- [ ] Distinguishable from its five nearest shelf neighbours
- [ ] Holds up in dark and tinted variants
- [ ] Nothing in it is a 2026 trend artifact
