# Apple Icon Composer Handoff — Layer 9

An AI image is not a shipped icon. Apple's Icon Composer (shipped with Xcode 26) composites a
layered source into the light / dark / clear / tinted variants the system actually renders, and
applies the platform's own glass, blur, refraction, specular, and shadow treatment.

Skipping this step is why AI-generated icons read as "a render pasted into a square" rather
than as system-native.

---

## What Icon Composer wants

Not a flat PNG. A **layered document**:

| Layer | Contains | Notes |
|---|---|---|
| **Background** | The field only — flat colour or two-stop gradient | Full bleed, no subject |
| **Mid** | Supporting form: a ring, a plate, a container | Optional |
| **Foreground** | The subject | Transparent background, ≥10% margin |

Each layer gets its own material treatment, and the system composites them with real
parallax and refraction across variants. A single flattened image gets a single flat treatment
— which is exactly the "pasted in" look.

**Practical path from an AI render:** separate the subject from the field (any segmentation
tool), export the subject as a transparent PNG at 1024, and rebuild the background as a clean
vector gradient rather than reusing the render's field. The render's field usually carries
lighting artifacts that fight the system's compositing.

---

## Parameter set

Emit these numbers as part of the design brief so whoever opens Icon Composer is not guessing.

| Parameter | Range | Default | What it does |
|---|---|---|---|
| **Glass** | 0–100% | 32% | Amount of glass material applied to the layer. High values need a simple silhouette. |
| **Blur** | 0–100% | 18% | Background diffusion behind translucent layers. Raise for depth, lower for crispness. |
| **Refraction** | 0–100% | 45% | How much the layer bends what is behind it. The signature iOS 26 parameter. |
| **Specular** | 0–100% | 60% | Strength of the moving highlight. Above ~75% reads as wet plastic. |
| **Shadow** | none / soft / medium / hard | soft | Contact shadow under the layer. `hard` is almost never right. |
| **Depth** | flat / shallow / medium / deep | medium | Parallax separation between layers. |
| **Glow** | none / weak / medium / strong | weak | Inner luminance. Reserve `medium`+ for genuinely luminous metaphors. |

### Starting points by material

| Primary material | Glass | Blur | Refraction | Specular | Shadow | Depth | Glow |
|---|---|---|---|---|---|---|---|
| Liquid glass | 55% | 24% | 65% | 68% | soft | medium | weak |
| Glass | 45% | 20% | 55% | 62% | soft | medium | none |
| Frosted glass | 40% | 38% | 25% | 30% | soft | shallow | weak |
| Ceramic | 22% | 14% | 30% | 55% | soft | medium | none |
| Metal | 15% | 10% | 18% | 78% | soft | shallow | none |
| Paper | 8% | 8% | 6% | 22% | soft | shallow | none |
| Rubber | 5% | 6% | 4% | 12% | soft | flat | none |
| Resin | 48% | 18% | 58% | 70% | soft | medium | weak |
| Crystal | 60% | 12% | 78% | 82% | soft | medium | weak |
| Wood | 6% | 8% | 5% | 30% | soft | shallow | none |
| Fabric | 4% | 10% | 3% | 10% | soft | flat | none |

Tune from the starting point; do not treat these as fixed.

---

## The four variants

Icon Composer generates all four from the layered source. Check each — the system's defaults
are reasonable but not always right.

### Light
The authored design. Baseline.

### Dark
The background field is replaced by a dark equivalent; the foreground keeps its material.

**Check:** does a dark subject disappear? Fix by authoring an explicit dark background layer
rather than accepting the auto-darkened one, and by adding a rim highlight to the foreground.

### Clear
Background becomes translucent and picks up the wallpaper behind it; only the foreground
carries material.

**Check:** the foreground must be legible against *any* wallpaper. This is where a subject that
relied on a specific background contrast fails. If the foreground is light-coloured, it needs
an edge or shadow to survive a light wallpaper.

### Tinted
Grayscale luminance, single system hue applied.

**Check:** the luminance structure must carry the whole design. This is the strictest test in
the system — see `COLOR_SYSTEM.md`.

---

## Platform specifics

| Platform | Mask | Notes |
|---|---|---|
| iOS / iPadOS 26 | Squircle | Full glass/refraction pipeline; author layered |
| macOS 26 | Squircle | Larger display sizes, so material detail matters more; more depth is licensed |
| watchOS | Circle | The corner content is cut entirely — check the concept survives a circular mask |
| visionOS | Circle + real parallax | Layers separate in 3D space; depth setting is genuinely visible |
| tvOS | Rounded rect, layered parallax | Layers shift on focus; needs ≥2 layers to look right |

If shipping across platforms, verify the concept in a **circular mask** early. A design tuned
to a squircle can lose its corners entirely on watchOS.

---

## Fallback without Icon Composer

Not everyone has Xcode 26. If exporting flat PNGs directly:

1. Author at 1024×1024, full bleed, no pre-applied rounded corners.
2. Author explicit **light** and **dark** versions rather than relying on auto-darkening.
3. Author a **monochrome/tinted** version by hand: convert to grayscale, then adjust the
   luminance separation until the subject reads clearly. The auto-conversion is frequently
   worse than a hand-tuned one.
4. Generate the size set with `scripts/make_icon_set.py`.

You lose the live refraction and parallax, but you keep the variant coverage — which is the
part users actually notice.

---

## Brief output format

```markdown
### Icon Composer parameters

| Parameter | Value |
|---|---|
| Glass | 32% |
| Blur | 18% |
| Refraction | 45% |
| Specular | 60% |
| Shadow | soft |
| Depth | medium |
| Glow | weak |

**Layers:** background = deep-slate two-stop gradient · mid = none ·
foreground = ceramic ring with amber core, transparent, 66% of canvas

**Variant notes:** dark — author a separate #0A0A0F field, add top rim highlight to the ring.
clear — foreground is light, needs the contact shadow retained for light wallpapers.
tinted — passes; luminance delta between ring and core is 34%.
```
