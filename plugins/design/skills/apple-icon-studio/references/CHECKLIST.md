# Ship Checklist

The gate. Run this before declaring an icon done. Any unchecked box is a blocker, not a note.

---

## Concept

- [ ] Brand Essence written as one sentence, 2–4 words
- [ ] Brand Essence could not be swapped onto a competitor unnoticed
- [ ] 10 metaphors generated across all five axes
- [ ] 7 killed, each with a written reason
- [ ] Chosen metaphor traces to the essence in one inferential step
- [ ] Metaphor is not on the category cliché list (or has an exceptional justification)

## Form

- [ ] Recognisable as a solid black silhouette
- [ ] Exactly one subject
- [ ] Shape choice justified against the essence, not taste
- [ ] Subject occupies 60–70% of canvas
- [ ] ≥10% clear margin; nothing in the corner arcs
- [ ] Optically centred, not merely mathematically centred
- [ ] Rotation is 0° or ≥12°
- [ ] No stroke thinner than 1/40 of the canvas
- [ ] Nested forms use concentric radii
- [ ] Maximum three stacked layers

## Material and light

- [ ] Two materials maximum
- [ ] All six material variables specified (primary, secondary, reflection, transparency, edge, finish)
- [ ] Exactly one light source; every highlight and shadow agrees on its position
- [ ] Light from above, 10–15° off vertical
- [ ] Edges are finished (chamfer, bevel, or soft falloff) — not hard vector edges
- [ ] Shadow is a short soft contact shadow, not a long cast shadow
- [ ] No environment reflection implying a room or scene

## Colour

- [ ] Three hues maximum
- [ ] Clear 60 / 30 / 10 hierarchy
- [ ] Subject vs. background luminance delta ≥30%
- [ ] No element separated by hue alone
- [ ] Palette derived from category → rivals → positioning → emotion, written down
- [ ] Background is #FAFAF9-ish or #0A0A0F-ish, not pure white or pure black
- [ ] Dominant saturation ≤85%

## Rendering modes

- [ ] Grayscale conversion: subject still clearly separated (tinted mode)
- [ ] Dark mode: subject does not vanish into the darkened field
- [ ] Clear mode: foreground legible against both light and dark wallpapers
- [ ] Explicit dark background authored, not just auto-darkened

## Sizes

- [ ] Checked at 1024px — rewards inspection
- [ ] Checked at 180px
- [ ] Checked at 80px
- [ ] Checked at 40px — still identifiable
- [ ] Checked at 16px — silhouette still coherent
- [ ] Checked under a circular mask (if shipping watchOS or visionOS)

## Distinctiveness

- [ ] Placed in a mental 5×5 grid with the five likeliest neighbours
- [ ] Findable without reading the label
- [ ] All 11 rejections from `CRITIQUE_GUIDE.md` run and verdicts stated, including passes
- [ ] Named specifically which market-leading icons it was checked against

## Score

- [ ] All six axes scored 0–100
- [ ] Final computed with the weighted formula (Recognition ×1.5, Scalability ×1.5)
- [ ] **Final ≥ 85** — under 85 does not ship
- [ ] If 85–91: weakest axis named and one targeted iteration attempted

## Currency

- [ ] Checked against the dead-language list in `ICON_EVOLUTION.md`
- [ ] Nothing in it is primarily a 2026 trend artifact
- [ ] "What would Apple do in 2026" answered as a concrete diff, and applied
- [ ] Re-scored after applying the diff

## Delivery

- [ ] No text, letters, or numbers anywhere in the icon
- [ ] Full bleed 1024×1024; rounded corners **not** pre-applied
- [ ] Layered source retained (background / mid / foreground), not only a flat PNG
- [ ] Icon Composer parameters emitted
- [ ] Size set generated and spot-checked (`scripts/make_icon_set.py`)
- [ ] `Contents.json` validates in Xcode
- [ ] Design brief rendered in both languages (`scripts/render_icon_brief.py`)
- [ ] Anything durable learned about the category written back to `references/icon-dna/<category>.md`

---

## The one-line version

If you only check one thing: **downsample to 40px, convert to grayscale, and place it next to
the five apps it will actually sit beside.** Most icons that fail, fail that test — and most
people never run it.
