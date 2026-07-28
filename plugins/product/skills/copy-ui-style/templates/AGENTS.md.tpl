# UI Implementation Rules — {{PRODUCT}} style

Generated from `ui-style/DESIGN.md` on {{DATE}}. Any UI you write in this repo must follow
these rules. When a rule and your own taste disagree, the rule wins.

Read alongside: `ui-style/tokens.json`, `ui-style/tokens.css`, `ui-style/components.md`.

## 0. The one-line brief

Build **{{PERSONALITY_LINE}}** interfaces: {{THEME}} theme, {{DENSITY}} density,
optimizing for {{EMOTION_LINE}}.

## 1. Tokens are the only source of values

- Import `ui-style/tokens.css` and use `var(--*)`. Never hard-code a hex color, a font
  size, a radius, or a shadow in a component.
- A value that has no token is a signal the token set is incomplete — add the token, then
  use it. Do not inline "just this once".
- Spacing: every gap/padding/margin is a multiple of **{{SPACING_UNIT}}**. No `13px`.

## 2. Color

{{COLOR_RULES}}

## 3. Typography

{{TYPO_RULES}}

## 4. Spacing & layout

{{SPACING_RULES}}

## 5. Radius & elevation

{{RADIUS_RULES}}

## 6. Motion

{{MOTION_RULES}}

## 7. Components

{{COMPONENT_RULES}}

## 8. Signature moves — implement these deliberately

{{SIGNATURE_MOVES}}

## 9. Never do this

{{ANTI_PATTERNS}}

## 10. Accessibility floor

- Body text vs. its background: contrast ratio ≥ 4.5:1. Large text (≥ 24px, or ≥ 19px
  bold) and UI borders: ≥ 3:1. Check before shipping a new color pair.
- Every interactive element needs a visible focus state — a token-based ring, not
  `outline: none`.
- Hit targets ≥ 44×44px on touch, even when the visual control is smaller.
- Respect `prefers-reduced-motion`: drop transforms and long transitions, keep opacity.

## 11. Legal / originality

This is an extracted *design language*, not a clone kit. Do not reproduce {{PRODUCT}}'s
logo, wordmark, illustrations, icon set, marketing copy, or screenshots. Layout patterns,
spacing rhythm, and token values are fair game; brand assets are not.
