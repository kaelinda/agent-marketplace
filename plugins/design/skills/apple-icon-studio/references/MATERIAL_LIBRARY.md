# Material Library — Layer 4

Material is the variable that separates an Apple-looking icon from a generic one, and it is
the variable almost every icon prompt omits. "A blue diamond" and "a blue diamond in polished
ceramic with a liquid-glass inner facet" produce entirely different renders from the same
model.

---

## The six variables

Specify all six. Every one of them changes the output.

| Variable | What it controls | Typical values |
|---|---|---|
| **Primary material** | The dominant surface (70%+ of the subject) | see catalogue below |
| **Secondary / accent material** | The contrast surface — an inner facet, a rim, a core | one material, never two |
| **Reflection** | How much environment the surface returns | none / subtle / medium / strong / mirror |
| **Transparency** | How much passes through | 0% (opaque) → 100% (clear) |
| **Edge** | The transition at the silhouette boundary | hard / soft 2px / chamfered / rounded bevel / feathered |
| **Surface finish** | Micro-roughness | matte / satin / semi-gloss / gloss / high-polish |

Example specification:

```
Primary            Ceramic, warm white
Secondary          Liquid glass, indigo, inner core only
Reflection         Medium
Transparency       15%
Edge               Soft 2px chamfer
Surface finish     Semi-gloss
```

**Hard rule: two materials maximum.** Three materials in one icon is the single most reliable
producer of the "muddled materials" critique. A third material is only acceptable if it is
purely a highlight (a specular glint), not a surface.

---

## Material catalogue

Each entry gives the character, when to use it, its failure mode, and — most importantly —
**the exact prompt vocabulary** the material needs to render correctly.

### Glass

**Character:** clean, precise, modern, weightless, technical
**Use for:** AI, data, clarity, transformation, anything "seeing through"
**Fails when:** overused — glassmorphism-for-its-own-sake reads as a 2021 template
**Prompt vocabulary:** `polished optical glass, true refraction, caustic light, subtle chromatic dispersion at edges, internal reflections, clean specular highlight`
**Pairs with:** metal rim, ceramic base, gradient field background

### Liquid glass

**Character:** the current Apple house material — glass with surface tension, volume, and
motion frozen in it
**Use for:** anything that should read as 2025+ Apple-native
**Fails when:** the form is too complex — liquid glass needs a simple silhouette to show its
refraction, or it turns into visual noise
**Prompt vocabulary:** `liquid glass, molten transparent volume, surface tension meniscus, deep internal refraction, soft rolling specular, dispersive edge glow, thick optical body`
**Pairs with:** ceramic, matte metal. Do **not** pair with frosted glass — the two read as the
same material rendered inconsistently.

### Frosted glass

**Character:** soft, private, layered, calm
**Use for:** privacy, depth, focus, background layers, "something behind"
**Fails when:** used for the subject rather than a layer — a frosted subject loses definition
at small sizes
**Prompt vocabulary:** `frosted glass, translucent diffusion, soft light scatter, matte translucency, gentle backlight bloom, no sharp specular`

### Ceramic

**Character:** premium, warm, tactile, calm, hand-finished, expensive
**Use for:** wellness, productivity, consumer, anything that should feel considered rather
than technical
**Fails when:** the palette is cold — ceramic wants warmth; cold ceramic reads as plastic
**Prompt vocabulary:** `glazed ceramic, subsurface scattering, soft satin glaze, gentle broad specular, hand-thrown edge, fine glaze micro-variation`
**Pairs with:** liquid glass accent, brushed brass, soft fabric. This is the highest-value and
most under-used material in the catalogue.

### Metal

**Character:** engineered, durable, serious, precise
**Sub-variants:**
- *Brushed aluminium* — anisotropic grain, cool, Apple-hardware-adjacent
- *Polished chrome* — mirror, high drama, dates fast
- *Anodised* — coloured metal with a matte-satin finish; excellent for developer tools
- *Brass / bronze* — warm, premium, slightly retro

**Fails when:** polished chrome — it reflects an environment that does not exist in a flat
icon, so the render invents one and it looks wrong
**Prompt vocabulary:** `brushed anodised aluminium, fine anisotropic grain, soft directional specular streak, machined chamfer edge, matte satin metal`

### Rubber / silicone

**Character:** friendly, tactile, durable, playful, grippy
**Use for:** utilities, tools, kid-facing, hardware companions
**Fails when:** premium positioning — rubber reads as inexpensive
**Prompt vocabulary:** `soft-touch silicone, matte rubber, gentle subsurface softness, rounded soft edges, no specular highlight, fine micro-texture`

### Paper

**Character:** honest, calm, analog, low-tech, contemplative
**Use for:** notes, writing, reading, journaling
**Fails when:** rendered with heavy fibre texture — at 40px it becomes noise; keep it smooth
**Prompt vocabulary:** `smooth heavy cardstock, soft paper fold, gentle ambient occlusion in the crease, subtle deckled edge, matte non-reflective`

### Fabric

**Character:** warm, human, soft, domestic
**Use for:** social, community, home, wellbeing
**Fails when:** technical products — fabric on a dev tool reads as a category error
**Prompt vocabulary:** `tight woven textile, soft fibre sheen, gentle fabric drape, matte weave micro-texture`

### Wood

**Character:** natural, crafted, warm, grounded, slow
**Use for:** journaling, learning, craft, sustainability
**Fails when:** rendered with strong grain — the grain competes with the silhouette
**Prompt vocabulary:** `smooth finished hardwood, fine subtle grain, satin oil finish, warm tone, soft rounded edge`

### Crystal

**Character:** precise, faceted, valuable, sharp, cold
**Use for:** precision tools, premium tiers, "clarity"
**Fails when:** too many facets — under 100px, facets merge into grey
**Prompt vocabulary:** `cut crystal, clean geometric facets, sharp refractive edges, prismatic light dispersion, high clarity`

### Resin

**Character:** contemporary, saturated, deep, glossy, encapsulating
**Use for:** creative tools, anything with "something suspended inside"
**Fails when:** the depth cue is absent — resin only reads as resin if something is embedded
in it
**Prompt vocabulary:** `clear cast resin, deep glossy pour, embedded element suspended inside, thick optical depth, high-gloss domed surface`

---

## Category → material starting points

| Category | Primary | Accent |
|---|---|---|
| AI | Liquid glass | Anodised metal or ceramic |
| Productivity | Ceramic | Liquid glass |
| Developer | Anodised / brushed metal | Glass |
| Media | Resin or glass | Polished metal |
| Finance | Brushed metal or ceramic | Crystal |
| Education | Ceramic or paper | Wood |
| Health | Ceramic | Frosted glass |
| Social | Ceramic or fabric | Liquid glass |
| Utilities | Rubber or anodised metal | Glass |
| Games | Resin | Metal |

---

## Lighting

Material without lighting is unspecified. Apple's default:

```
Key light      Above, 10–15° off vertical, slightly front, large soft source
Fill           Ambient, low, from below — lifts the shadow side without a second specular
Rim            Optional thin top-edge highlight; strongest craft signal when subtle
Shadow         Short, soft, directly below, low opacity — contact shadow, not cast shadow
Environment    Neutral studio; no visible reflected scene
```

Prompt phrasing: `single soft key light from above, large diffuse source, gentle ambient fill,
thin rim highlight on the top edge, soft short contact shadow, neutral studio environment`

**Never** specify a second key light. Conflicting speculars on opposing edges is the most
reliable tell that an icon was machine-generated.

---

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| "Looks like a plastic toy" | Gloss + saturated colour + no subsurface | Switch to ceramic; add subsurface scattering; desaturate ~15% |
| "Looks AI-generated" | Two light sources, or environment reflections implying a room | One key light; neutral environment; remove reflected scene |
| "Materials look muddled" | Three or more materials | Cut to two; demote the third to a highlight |
| "Flat and cheap" | No specular, no edge treatment | Add rim highlight and an edge chamfer |
| "Muddy at 40px" | Low-contrast material transitions | Increase luminance delta between primary and accent to >30% |
| "Dated glassmorphism" | Frosted glass on everything, no other material | Give the subject a solid material; reserve glass for one accent |
| "Too heavy / dark" | Transparency 0% and a dark palette | Raise transparency to 10–20% or add an inner luminance |

---

## Transparency guidance

| Value | Reads as |
|---|---|
| 0% | Solid object — safest, most legible at small sizes |
| 10–20% | Premium hint of depth; the current Apple sweet spot |
| 30–50% | Clearly translucent; needs a background field with structure to refract |
| 60%+ | Effectively glass; the silhouette must be exceptionally strong to survive |

Above 50%, run the 40px legibility test again — transparency and small-size legibility are
directly in tension.
