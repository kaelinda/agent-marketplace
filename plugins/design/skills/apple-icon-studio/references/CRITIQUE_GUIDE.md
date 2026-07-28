# Apple Reviewer — Layer 7

This layer does not generate. It attacks.

Every concept that reaches here is defended by the fact that you made it. The job of this
layer is to remove that defence. Run every rejection below against every surviving concept and
state the verdict explicitly — **including the passes**, because "checked, passes" is
information and silence is not.

---

## The 11 standard rejections

### R1 — "Too close to <market leader>"

Name the specific product. "Too close to ChatGPT" / "too close to Arc" / "too close to Notion"
/ "too close to Linear."

This is the strongest rejection and needs no further argument. An icon that borrows a
market-leader's silhouette or hue is doing free brand work for them and will be read as a
clone by exactly the audience you are trying to win.

**Check:** name the five apps most likely to sit near this one on a home screen. For each, ask
whether a user glancing at 40px could confuse them. Any yes is a fail.

### R2 — "Too complex"

More than one subject, or one subject with more than two levels of detail hierarchy.

**Check:** count the distinct elements a describer would mention. Three or more is a fail.

### R3 — "Dirty on the home screen"

The icon may be fine alone and still make a home screen look cluttered. Causes: high-frequency
detail, more than three hues, heavy texture, strong drop shadows, or edge-to-edge content
fighting the neighbouring icons' margins.

**Check:** imagine it in a 4×6 grid with the system defaults. Does the grid get noisier?

### R4 — "Illegible at 40px"

**Check:** actually downsample. Do not estimate. Strokes below 1/40 of the canvas vanish,
interior detail merges, and low-contrast material transitions become flat fields.

### R5 — "No colour hierarchy"

Two or more elements competing for first fixation, or a palette where no colour is clearly
dominant. Result: the eye has no entry point and the icon reads as busy even at low element
counts.

**Check:** squint. Which element resolves first? If the answer is "both" or "neither," fail.

### R6 — "Muddled materials"

Three or more materials, or two materials that read as the same material rendered
inconsistently (frosted glass + liquid glass is the classic pairing failure).

**Check:** name every material. More than two is a fail.

### R7 — "Doesn't feel Apple"

Diagnostically vague on its own, so decompose it. The specific causes, in order of frequency:

- Drop shadow too long / too hard (Android Material convention, not Apple)
- Outline stroke around the whole subject (Google/Material convention)
- Flat vector with no material at all (2016 flat-design residue)
- Overly literal skeuomorphism (2010 residue)
- Gradient background with a scene or landscape in it
- Text or a number in the icon
- The subject drawn with the corner radius already applied

**Check:** name which of the above applies. If none do, the concept passes and "doesn't feel
Apple" was taste, not a defect — say so.

### R8 — "Edges too sharp"

Apple surfaces have finished edges: a chamfer, a bevel, a rounded transition, a soft
1–3px falloff. A perfectly hard edge between subject and background reads as a vector paste-up
rather than an object.

### R9 — "Light direction wrong"

Specular highlight on the bottom edge, shadow on top, or — most commonly — two speculars from
opposing directions. The last is the most reliable machine-generated tell.

**Check:** trace the implied light source from every highlight and every shadow. They must all
agree on one position.

### R10 — "Will date within 18 months"

The design's most distinctive quality is a current trend rather than the metaphor. As of 2026:
iridescent chrome blobs, aurora gradients, glassmorphism as the whole idea, AI-sparkle
clusters, and anything whose primary read is "made by an image model."

**Check:** if you removed the trendy treatment, would anything of the concept remain? If not,
the trend *is* the concept, and it will expire.

### R11 — "Fails in tinted / dark mode"

The design's legibility depends on colour contrast that disappears in monochrome, or the
subject vanishes into a darkened background field.

**Check:** grayscale conversion. Subject still separated? Dark field — subject still visible?

---

## The scorecard

Six axes, 0–100 each.

### Apple Feeling (0–100)
Would this sit on an Apple home screen without looking foreign? Judged against the current
system icon set, not against a general sense of "nice design."

### Recognition (0–100)
In a 5×5 grid of the five likeliest neighbours plus generic apps, how fast does the eye find
it? 100 = found before the label is read. Under 70 = it needs the label to function.

### Material (0–100)
Is the surface believable, singular, and appropriate to the essence? Penalise: material count
> 2, conflicting lighting, absent edge treatment, "plastic toy" reads.

### Memorability (0–100)
Could a user describe it accurately a day later, from memory, well enough that you could
redraw it? This is the axis that separates good from great and the one most icons score
lowest on.

### Scalability (0–100)
Survives 1024 → 180 → 80 → 40 → 16px. Score the *worst* size, not the average.

### Emotion (0–100)
Does the first 200ms produce the intended feeling? A calm app whose icon reads as urgent
fails here even if every other axis is perfect.

### Final score

```
Final = (Recognition×1.5 + Scalability×1.5 + Apple×1 + Material×1 + Memorability×1 + Emotion×1) / 7
```

Recognition and Scalability are weighted 1.5× because they are the axes that determine whether
the icon *functions*. The rest determine whether it is *good*. A beautiful icon that nobody can
find is a failed icon.

### Thresholds

| Final | Verdict |
|---|---|
| **≥ 92** | Ship. Proceed to layer 8. |
| **85–91** | Ship-able, but name the weakest axis and try one targeted iteration first. |
| **75–84** | Do not ship. Return to layer 4 (material/colour) — the concept is sound, the execution is not. |
| **< 75** | Do not ship. Return to layer 2 — the metaphor is the problem, and no amount of rendering will fix it. |

**Under 85 does not proceed.** This threshold is the point of the layer. An icon is on a
user's home screen for years; one more iteration round now is the cheapest thing in the entire
project.

---

## Diagnostic routing

The low axis tells you which layer to return to:

| Lowest axis | Return to |
|---|---|
| Recognition | Layer 2 — the metaphor is a category default |
| Memorability | Layer 2 or 3 — no distinctive shape to remember |
| Scalability | Layer 3 or 5 — too complex, or subject too small in canvas |
| Material | Layer 4 — material count, lighting, or edge treatment |
| Apple Feeling | Layer 4 or 5 — shadow, stroke, perspective, or finish conventions |
| Emotion | Layer 1 or 6 — essence mis-stated, or palette contradicts it |

---

## Output format

```markdown
### Concept B — Nested rings closing inward

| Rejection | Verdict |
|---|---|
| R1 Too close to X | Pass — checked vs. ChatGPT / Claude / Gemini / Perplexity / Copilot |
| R2 Too complex | Pass — one subject, two levels |
| R3 Dirty on home screen | Pass |
| R4 Illegible at 40px | **Fail** — inner ring merges below 60px |
| ... | ... |

| Axis | Score |
|---|---|
| Apple Feeling | 94 |
| Recognition | 88 |
| Material | 91 |
| Memorability | 86 |
| Scalability | 72 |
| Emotion | 90 |
| **Final** | **86.1** |

**Verdict:** iterate. Scalability is the blocker (R4). Return to layer 3: drop the inner ring
to two turns and increase the gap, then re-score.
```

Be specific and be harsh. A critique that says "very strong, maybe minor tweaks" has done no
work.
