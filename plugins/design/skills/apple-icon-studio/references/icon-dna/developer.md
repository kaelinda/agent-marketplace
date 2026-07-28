# Icon DNA — Developer Tools

Editors, terminals, CLIs, version control, infrastructure, debugging. The audience with the
strongest and least forgiving taste, and the one most likely to notice — and resent — an icon
that is trying too hard.

## 1. Mental model

Developers read an icon as a **credibility signal**. An over-designed developer tool icon
actively reduces trust: it suggests the effort went into marketing rather than into the tool.

What earns credibility here:

- **Precision.** Exact geometry, deliberate alignment, no accidental asymmetry.
- **Restraint.** Two colours, one subject, nothing decorative.
- **Material honesty.** Anodised metal and matte graphite read as *instrument*.
- **Confidence in monochrome.** The strongest developer icons work in pure greyscale.

What destroys it: gradients doing the heavy lifting, mascots (unless the project already has
one with real equity), sparkles, glossy plastic, and any hint of enterprise stock imagery.

Note the exception: developer tools that *want* to feel playful (Homebrew, Rust's crab, Go's
gopher) trade credibility-through-restraint for credibility-through-community. That is a valid
but different strategy, and it only works when the mascot predates the icon.

## 2. Metaphors

**Exhausted:**
- Terminal prompt `>_` or `$`
- Angle brackets `< >`
- Gear / cog
- Curly braces `{ }`
- Bug / ladybug (debuggers)
- Cloud with an arrow

**In use:** VS Code = blue infinity-ribbon · Cursor = angular black cursor form ·
GitHub = octocat / monochrome mark · JetBrains = per-product gradient squares ·
Docker = whale · Kubernetes = helm · Vercel = triangle · Warp = angular gradient form ·
Zed = angular Z · iTerm = terminal

**Open:**
- **Chisel / burin** — precision instrument, excellent material affordance
- **Lattice / scaffold** — structure being built; strong geometric silhouette
- **Junction / switch point** — routing, branching (a much better VCS metaphor than a tree)
- **Tuning peg / calibration dial** — configuration, tuning
- **Plumb line / level** — correctness, alignment; unusually literal in a good way
- **Machined key / bit** — the exact tool for the exact job
- **Braid** — merging branches; far better than the ubiquitous branch-tree glyph
- **Aperture stop** — scoping, filtering, focus

## 3. Shape language

- **Rounded rectangle / machined block** — instrument; the honest default
- **Diamond** — precision, transformation, automation
- **Hexagon** — modular systems (heavily used in infra, so collision risk)
- **Angular asymmetric marks** — the current house style for the newer generation (Zed, Warp,
  Cursor); differentiating power is dropping fast as everyone adopts it
- **Avoid:** literal terminal windows, code brackets, anything depicting a UI chrome

## 4. Material

| Role | Recommendation |
|---|---|
| Primary | **Matte anodised aluminium** or **matte graphite** |
| Accent | A single machined edge in a brighter metal, or one glass inset |
| Reflection | Subtle — a strong reflection reads as consumer, not instrument |
| Transparency | 0–10% |
| Edge | Machined chamfer — the strongest credibility signal available |
| Finish | Matte to satin. **Not gloss.** |

Gloss is the single most common material error here. A glossy developer tool icon reads as a
game.

## 5. Palette

```
Graphite #18181B · Blue #3B82F6 · White #FFFFFF
```

Terminal accents, used sparingly as a small highlight only:
```
Green #22C55E · Amber #F59E0B · Cyan #06B6D4 · Magenta #E879F9
```

**Collision map:** blue ribbon → VS Code · near-black angular → Cursor · monochrome octocat →
GitHub · multi-hue gradient squares → JetBrains · white triangle on black → Vercel.

Monochrome plus one accent is the strongest formula in this category. Genuinely consider
pure monochrome — it is rare enough to differentiate and it signals total confidence.

## 6. Traps

| Trap | Why it fails |
|---|---|
| `>_` terminal prompt | Every terminal-adjacent tool; conveys "CLI", nothing more |
| Gradients as the main idea | Reads as marketing; the audience is allergic |
| Gloss / plastic | Reads as a game or a consumer app |
| A mascot invented for the icon | Only works when the community made it first |
| Enterprise blue with a swoosh | Reads as 2008 middleware |
| Rotating something 5° for "dynamism" | Reads as an alignment bug to this audience specifically |
| Depicting code | Text rule violation, and unreadable at any real size |

## 7. Prompt fragments

**Machined instrument:**
```
a precisely machined form in matte anodised graphite aluminium, fine anisotropic surface grain,
crisp 45-degree chamfered edge catching a single thin specular streak,
single soft key light from directly above, deep near-black field,
engineered, exact, no gloss
```

**Monochrome restraint:**
```
a single geometric mark in matte warm white on a deep graphite field,
no gradient, no reflection, soft 2px edge falloff only,
extremely restrained, confident, high contrast
```

**Metal + glass inset:**
```
a brushed aluminium block with one clean optical-glass inset at its centre,
true refraction through the inset, subtle dispersion at its edges,
matte metal body with no reflection, single key light from above
```

**Category negatives:**
```
terminal window, command prompt, dollar sign, angle brackets, curly braces, code, source code,
syntax highlighting, gear, cog, bug, ladybug, cloud, server rack, mascot, cartoon, glossy,
plastic, swoosh, enterprise
```
