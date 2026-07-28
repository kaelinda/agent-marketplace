# Icon DNA — Utilities

Launchers, converters, clipboard managers, window managers, system tools, menu-bar apps. The
category where the icon is often seen at **menu-bar size** — 16–22px — which changes almost
every rule.

## 1. Mental model

Utilities are judged on **competence**, and the icon is the first evidence. Users of small
utilities are frequently power users; they read over-design as a signal that the developer
cares about the wrong things.

Two constraints dominate:

1. **Menu-bar legibility.** Many utilities live at 16–22px in a monochrome menu bar. If the
   design only works at 40px+, it fails where it is most seen.
2. **It must not look like a system app.** Sitting beside Apple's own utilities means an icon
   that mimics them reads as either a knock-off or as something the user does not remember
   installing.

| Sub-register | Register |
|---|---|
| Menu-bar resident | Monochrome-first, single shape, maximum simplicity |
| Launcher / command | Precise, geometric, instrument-like |
| Converter / processor | Transformation metaphors, two-state forms |
| System / maintenance | Mechanical, engineered, restrained |

## 2. Metaphors

**Exhausted:**
- Gear / cog
- Wrench, screwdriver, toolbox
- Magic wand
- Switch / toggle
- Magnifying glass (search utilities)
- Lightning bolt (speed)

**In use:** Raycast = red-orange ray form · Alfred = blue bowler hat ·
Rectangle = window frame · CleanMyMac = blue-gradient · 1Password = blue-gradient lock ·
Bartender = menu-bar-derived form · Hazel = orange leaf

**Open:**
- **Aperture / iris** — filtering, scoping
- **Funnel** — conversion and reduction, without the gear
- **Junction / router** — directing flows
- **Notch / keyway** — the exact fit; excellent at small sizes because the negative space
  survives downsampling
- **Two-state form** — one shape half-transformed into another; the clearest "converter"
  metaphor and rarely used
- **Slot and tab** — mechanical fit
- **Caliper / gauge** — measurement and precision
- **Sieve / grid with one gap** — filtering made structural

## 3. Shape language

- **Simple geometric primitives** — circle, rounded square, hexagon. Complexity is the enemy
  at menu-bar size.
- **Negative-space forms** — the hole survives downsampling far better than interior detail
- **Notched forms** — a single clean cut in a simple shape is legible at 16px and distinctive
- **Avoid:** anything with more than two visual elements, and any stroke under 1/24 of the
  canvas (the menu-bar threshold is stricter than the 1/40 home-screen one)

## 4. Material

| Role | Recommendation |
|---|---|
| Primary | **Matte anodised metal** or **soft-touch rubber** |
| Accent | One glass inset, or one bright machined edge |
| Reflection | Subtle |
| Transparency | 0–10% |
| Edge | Machined chamfer |
| Finish | Matte to satin |

Rubber is a good, under-used fit: it reads as a physical tool, it is friendly without being
childish, and it renders cleanly at small sizes because it has no specular to lose.

## 5. Palette

```
Graphite #374151 · Bone #F5F5F4 · one high-visibility accent
```

Accent options: amber #F59E0B, cyan #06B6D4, coral #FB7185.

**Monochrome-first is the correct default here.** Design in greyscale, add at most one accent,
and verify the greyscale version reads at 16px — because in the menu bar, greyscale is what
ships.

**Collision map:** red-orange ray → Raycast · blue bowler hat → Alfred · blue gradient lock →
1Password · blue gradient → CleanMyMac.

## 6. Traps

| Trap | Why it fails |
|---|---|
| A gear | The universal "settings" glyph; conveys nothing about the tool |
| A wrench or toolbox | Second-most exhausted; also reads as generic maintenance |
| A magic wand | Reads as a 2012 photo filter app |
| Designing only at 1024 | Dies in the menu bar, where the app actually lives |
| Mimicking a system app | Reads as a knock-off, or gets forgotten as "something Apple made" |
| Any stroke under 1/24 canvas | Invisible at 16px |
| A gradient carrying the design | Nothing survives the monochrome menu-bar rendering |

## 7. Prompt fragments

**Machined tool:**
```
a simple geometric form in matte anodised graphite with one clean machined notch cut into it,
fine surface grain, one thin bright chamfer highlight, single soft light from above,
bone-coloured field, extremely simple silhouette, legible at very small size
```

**Soft-touch rubber:**
```
a rounded soft-touch silicone form in matte graphite with one amber inset,
gentle subsurface softness, no specular highlight, fine micro-texture,
soft rounded edges, friendly but precise, short soft contact shadow
```

**Two-state transformation:**
```
a single form transitioning from a square on one side to a circle on the other,
one continuous matte anodised surface, clean geometric interpolation,
no seam, single soft key light from above, monochrome with one accent edge
```

**Category negatives:**
```
gear, cog, settings, wrench, screwdriver, hammer, toolbox, tools, magic wand, sparkle,
toggle switch, slider, magnifying glass, lightning bolt, cleaning, broom, brush, dust,
gradient, complex detail, thin lines
```
