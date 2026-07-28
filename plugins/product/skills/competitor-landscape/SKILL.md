---
name: competitor-landscape
description: "Use when the user wants a standalone, deep competitive analysis of a product against its rivals — not a full product teardown, just the positioning question: where does it sit vs. 3-6 named competitors, on which axes, and where is the gap closing. Produces a dimension-by-dimension matrix plus an explicit 2D positioning map. Triggers: 竞品分析, 竞争格局, competitive landscape, competitor matrix, positioning map, who competes with X."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [product, competitor, positioning, strategy, matrix]
    related_skills:
      - product-teardown
---

# Competitor Landscape

## Overview

A focused competitive-positioning session — the deep version of what `product-teardown`
§8 does inline. Use this skill directly when the user only wants the competitive read
(no full 15-question teardown needed), e.g. "who really competes with Linear and where do
they each win."

## When to Use

- "帮我做一下 X 的竞品分析 / 竞争格局图"
- "positioning map for X vs Y vs Z"
- As a deeper follow-up after a `product-teardown` run, when the user wants more rivals
  or more axes than the teardown's fixed 4-dimension matrix covered.

## Method

1. **Name 3–6 real rivals.** Prefer naming the ones a buyer would actually shortlist —
   not every adjacent tool. State why each one is in scope (direct substitute, adjacent
   expansion threat, aspirational benchmark).

2. **Pick 4–6 dimensions that actually differentiate this category** — not generic
   "features vs. pricing." Good dimensions name a real strategic tension, e.g.:
   - Philosophy (opinionated vs. configurable)
   - Speed & craft (engineering quality as experienced by the user)
   - Non-core-audience fit (does it work for the users *outside* its primary segment)
   - AI depth (bolt-on vs. native vs. autonomous)
   - Enterprise readiness (governance, permissions, audit)
   - Distribution motion (PLG vs. sales-led vs. hybrid)

3. **Build the matrix.** One row per dimension, one column per competitor (target product
   included, marked as "own"). Every cell is a specific claim, not an adjective — "sub-
   100ms optimistic UI on a custom sync engine," not "fast."

4. **Draw the 2D positioning map in prose** (this skill doesn't render a chart — describe
   it precisely enough that the reader could draw it themselves, or hand it to
   `ai-architecture-review`'s sibling report renderer if a visual is needed). Pick the
   two axes that matter most for *this* category and place every named rival:
   ```
                  Enterprise
                      ↑
              Jira  ClickUp
                    Linear
                      ↓
                  Personal
   ```
   State explicitly why the target product sits where it does, and which rival is
   closest to it on the map (that's usually the real competitive threat, not the market
   leader).

5. **Close with two verdicts**, each one sentence:
   - Where the product still clearly wins, and against whom specifically.
   - Where a named rival is closing the gap, and on what time horizon.

## Output

Chat-only by default: the matrix (as a markdown table) + the 2D positioning read + the
two verdicts. If the user wants this embedded in a shareable report, either hand the
matrix content to `product-teardown`'s §8 placeholders (`COMP_*` keys in its render
pipeline) or render it as a standalone page with the `md-to-html` skill
(`plugins/content-generate/skills/md-to-html`).

## Pitfalls

1. **Don't pad the rival list.** 3–6 named competitors that a real buyer would compare
   against — a 10-row list of tangential tools dilutes the read.
2. **Don't reuse generic dimensions across every teardown.** "Features" and "Pricing" are
   not analysis — pick the 4–6 axes that are actually in tension for *this* category.
3. **The 2D map's value is in *why*, not just placement.** "X sits here because it
   refuses to add setting Y" is the finding; the dot on the grid is just the summary.
