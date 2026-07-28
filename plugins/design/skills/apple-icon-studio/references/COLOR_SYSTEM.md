# Color System — Layer 6

Colour is derived, not picked. If you cannot explain the palette from the category, the
competitive set, the positioning, and the intended emotion, you have decorated rather than
designed.

---

## The derivation chain

```
Category        What do this category's users already associate with competence here?
   ↓
Competitors     What is already taken? (occupying a rival's hue is a functional defect)
   ↓
Positioning     Premium / accessible / playful / serious / technical
   ↓
Emotion         What should the first 200ms feel like?
   ↓
Palette         2–3 hues. One dominant, one accent, optional highlight.
```

Write each step down. "Indigo because AI, but shifted 15° toward violet and desaturated
because every AI tool is now indigo and this product's positioning is calm rather than
powerful" is a palette rationale. "Indigo, it looks good" is not.

---

## The 60 / 30 / 10 rule

| Role | Share | Job |
|---|---|---|
| **Dominant** | 60–70% | The colour the icon *is*. Usually the background field or the primary material. |
| **Accent** | 20–30% | The subject or the element that creates the focus point. |
| **Highlight** | <10% | Specular, rim light, or a single small detail. Optional. |

**Maximum three hues.** At 40px, four or more hues average into brown-grey mud. Multiple
*values* of one hue do not count against this budget — a three-value indigo ramp is one hue.

---

## Category palettes

Starting points. Each needs a competitive-collision check before adoption.

### AI / ML
```
Indigo #4F46E5 · Violet #7C3AED · Near-black #0A0A0F · Glass white #F8FAFC
```
Warm counter-option: amber/copper — genuinely differentiating right now because the category
is saturated with cool violets. Consider it seriously.
**Collision watch:** OpenAI (near-black + white), Anthropic (clay/terracotta #D97757),
Gemini (blue→violet gradient), Perplexity (teal #20808D), Copilot (blue→pink gradient).

### Productivity / tasks
```
Warm white #FAFAF9 · Graphite #1F2937 · one saturated accent
```
Accent choice is the entire brand decision. Things = warm blue, Todoist = red, Linear =
violet-grey, Notion = pure monochrome.
**Collision watch:** monochrome is Notion's; red is Todoist's.

### Developer tools
```
Graphite #18181B · Blue #3B82F6 · White #FFFFFF
```
Optional single terminal-accent (green #22C55E or amber #F59E0B) used sparingly.
**Collision watch:** VS Code blue, GitHub monochrome, Cursor black, JetBrains gradient.

### Media / music / video
```
Orange #F97316 · Pink #EC4899 · Black #0A0A0A
```
High saturation is licensed here in a way it is not elsewhere — media icons are allowed to
shout.
**Collision watch:** Spotify green, Apple Music pink→red, YouTube red, Netflix red.

### Finance
```
Emerald #059669 · Navy #1E3A8A · Silver #CBD5E1
```
Trust palette. Red is reserved for loss — never use red as a primary in finance.
**Collision watch:** Stripe indigo, Robinhood green, Cash App green, Revolut black.

### Health / wellness
```
Soft teal #14B8A6 · Sage #84CC16 · Warm off-white #FEFCE8
```
Low saturation, high luminance. Avoid clinical white-and-blue, which reads as insurance
software rather than wellbeing.

### Education
```
Warm blue #2563EB · Amber #F59E0B · Cream #FEF3C7
```
Warmth is the differentiator; cold blue reads as institutional.

### Social / community
```
Coral #FB7185 · Warm purple #A855F7 · Cream #FFF7ED
```
**Collision watch:** almost everything is taken. Instagram gradient, Discord blurple,
Slack multi-hue, Telegram blue, WhatsApp green. This is the hardest category for colour
differentiation — win on shape instead.

### Utilities
```
Neutral graphite #374151 · one high-visibility accent (#F59E0B or #06B6D4)
```
Utilities benefit from looking like tools, not brands.

### Games
```
Saturated primary + complementary accent + deep near-black
```
The one category where colour maximalism is correct.

---

## Emotion → hue

| Emotion | Hue family | Notes |
|---|---|---|
| Calm, trust | Blue, teal | Lower saturation increases the calm |
| Energy, urgency | Red, orange | Fatigues fast; use as accent, not dominant |
| Growth, health | Green | Yellow-green = fresh; blue-green = clinical |
| Premium, considered | Deep navy, near-black, warm grey | Restraint reads as expensive |
| Creative, playful | Violet, magenta, coral | High saturation licensed |
| Intelligent, technical | Indigo, violet | Saturated; extremely crowded |
| Warm, human | Amber, terracotta, coral | The most under-used direction in tech |
| Natural, grounded | Sage, sand, clay | Desaturate everything ~20% |

---

## Contrast requirements

- **Subject vs. background luminance delta: ≥30%.** Below that, the silhouette dissolves at
  40px. Measure in L\* (perceptual lightness), not in RGB distance.
- **Accent vs. dominant: ≥25% luminance delta** *or* ≥90° hue separation. Two colours that
  differ only in hue at the same lightness vibrate and read as a single muddy value when
  downsampled.
- **Never rely on hue alone** to separate two elements. Red and green at equal lightness are
  indistinguishable to roughly 8% of male users and merge for everyone at small sizes.

---

## The three rendering modes

Modern iOS renders every icon three ways. Design for all three or the OS will do it for you,
badly.

### Light
The design as authored.

### Dark
The background field darkens substantially. Check:
- Does a dark subject vanish into the darkened field? If so, add a rim highlight or switch the
  subject to a luminous material.
- Does a bright saturated accent now glare? Reduce accent saturation ~10–15% in the dark
  variant.
- Best practice: author a *separate* dark background field rather than letting the system
  darken the light one.

### Tinted (monochrome)
All colour is discarded. The icon is rendered as grayscale luminance, then a single system hue
is applied.

This is the harshest test in the system and it is not optional. If the design's legibility
came from a red-on-green contrast, tinted mode reduces it to one flat grey rectangle.

**Check:** convert to grayscale. Is the subject still clearly separated from the background?
If not, the luminance structure is wrong regardless of how good the colour version looks.

---

## Gradients

- **Two stops.** Three-stop gradients are almost always a mistake in an icon at this scale.
- **15–30% luminance delta** between stops. Below 15% it reads as flat and you have paid the
  complexity cost for nothing; above 40% it reads as a lighting effect rather than a surface.
- **Light at the top**, matching the key light from above. A bottom-lighter gradient fights
  the lighting model.
- **Linear or subtle radial.** Angular/conic gradients read as a 2021 trend.
- Add **<3% noise** on large gradient fields to prevent banding. Invisible at icon sizes,
  removes the artifact at 1024.

---

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Four or more hues | Mud at 40px, no hierarchy |
| Rainbow / full-spectrum | Reads as "we couldn't decide"; also unusable in tinted mode |
| Neon on black | High initial impact, ages badly, glares in dark mode |
| Pure #FFFFFF background | Blends into light-mode system chrome; use #FAFAF9 or #F8FAFC |
| Pure #000000 background | Disappears against dark-mode OLED; use #0A0A0F |
| Competitor's exact hue | Free brand equity — for them |
| Gradient carrying the whole design | Nothing left in tinted mode |
| Saturation above ~85% on the dominant | Reads as cheap; premium palettes sit at 55–75% |

---

## Palette output format

```markdown
| Role | Hex | Name | Share | Rationale |
|---|---|---|---|---|
| Dominant | #0F172A | Deep slate | 65% | Restraint; avoids the crowded indigo field |
| Accent | #F59E0B | Amber | 25% | Warm counter-move against a uniformly cool category |
| Highlight | #FEF3C7 | Cream | 10% | Rim light; carries the ceramic read |
```

Always state the grayscale check result and the dark-mode adjustment alongside it.
