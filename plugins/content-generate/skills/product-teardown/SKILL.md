---
name: product-teardown
description: "Use when the user asks to 'teardown', 'break down', 'reverse-engineer', or do a deep PM/strategy analysis of any product (Linear, Notion, Cursor, a competitor, an internal product, ...). Reverse-engineers the product as a system — JTBD, core loop, architecture, business model, growth, AI readiness, friction, risks, opportunities — through a fixed 15-section Principal-PM framework, then renders a bilingual (EN + ZH) print-ready HTML report with a product-screenshot gallery. Triggers: 拆解某产品, 产品分析, product teardown, reverse-engineer this product, PM breakdown, competitor deep dive."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [product, teardown, pm, strategy, analysis, html, report, bilingual]
    related_skills:
      - md-to-html
      - ali-oss
---

# Product Teardown

## Overview

A Principal-PM-level product teardown. Point it at any product and it reverse-engineers
the thing as a *system* — loops, strategy, moat, opportunities — instead of writing a
"5 things I like about this app" review. The output is a structural read of *why the
product wins, where it leaks, and what the next move should be*.

Adapted from the open-source
[product-teardown-skill](https://github.com/yanliudesign/product-teardown-skill) (MIT) by
Dreameryanyan, restructured to fit this marketplace's plugin/skill conventions.

## When to Use

Invoke when the user asks to "teardown X" / "拆解一下 X" / "break down Notion" /
"analyze this product like a PM" / "reverse-engineer our competitor's app". Works for
consumer, B2B, and AI-native products alike.

## How it works — 2 steps, don't skip either

### Step 1 · Deliver the teardown in chat

Produce the full **15-section analysis** in chat, in order, using the framework below.
Think like a senior PM, not a reviewer:

- Be structured, analytical, and opinionated — avoid marketing language.
- Prefer systems thinking over feature listing; find the loop first, then work outward.
- JTBD beats persona — "what did they hire it to *replace*" beats "who uses it."
- AI readiness is a placement problem (Assistive / Embedded / Autonomous), not a checkbox.
- Opportunities must be concrete and shippable, never "they should add AI."
- When uncertain, state assumptions explicitly. Never invent hard numbers — prefix
  inferred figures with `[inferred]` (EN) / `[推断]` (ZH), or `[需用户补充]` when you
  genuinely don't know.

#### Required sections (always in this order)

1. **Product Snapshot** — what it really is (1–2 sentences), core user promise, category
   + positioning, stated assumptions.
2. **Target Users & Jobs-to-be-Done** — primary segments, functional/emotional/social
   JTBD, trigger moment, frequency and context of use.
3. **Core Product Loop** — Trigger → Action → Reward → Return. Plus acquisition loop,
   activation/aha moment, retention drivers, virality/network effects.
4. **Product Architecture & UX System** — key surfaces, core entities, IA logic,
   navigation/interaction model.
5. **Design Language & Craft Signals** — 5 concrete, copyable craft patterns (not vague
   adjectives) — what it is, why it matters, who else fails to do it.
6. **Value Delivery & UX Quality** — time-to-value, cognitive load, delight moments,
   trust mechanisms, where users struggle.
7. **Business Model & Monetization** — revenue model, free/paid boundary, monetization
   entry points, UX↔monetization alignment.
8. **Competitor Landscape** — 3–5 real rivals scored across 4 concrete dimensions in a
   matrix; where the product still wins, where rivals are catching up (name them).
9. **Growth Strategy** — acquisition channels, growth loops, horizontal/vertical/platform
   expansion vectors.
10. **AI / Future Readiness** — current AI usage placed on the Assistive → Embedded →
    Autonomous spectrum, agentic candidates for the next 12–24 months, deeper AI
    opportunities, strategic AI-disruption risk.
11. **What Metrics They Actually Optimize For** — 1 inferred North Star metric (why it's
    the right unit of value), 3 input metrics, 1 guardrail, 1 metric blindspot.
12. **Friction & Weaknesses** — explicit, opinionated: UX friction, weak loops, retention
    risks, competitive vulnerabilities, over/under-design.
13. **Risk Matrix** — 4 concrete risks: name, category (competitive/market/technical/
    growth/regulatory), severity, likelihood (with a time window), specific mitigation.
14. **Opportunities & Redesign Ideas** — 3 improvement opportunities, 1 high-impact
    strategic shift, 1 moonshot.
15. **Final PM Verdict** — why it wins, where it breaks, its long-term moat (or lack of
    one).

### Step 2 · Generate the bilingual HTML report and open it

After the chat response, without asking permission:

1. **Gather product screenshots.** Prefer real, hot-linkable images from the product's
   own marketing pages (`og:image` tags — `curl -s <url> | grep -i og:image`), not random
   blog posts. You need 6, one per gallery slot, each with a tight PM-voice caption
   (≤ 90 chars).
2. **Build a single JSON data file** with this shape (see
   `references/example-data.json` for a filled, schema-valid stub):

   ```json
   {
     "slug": "product-name",
     "date": "YYYY-MM-DD",
     "shots": { "SHOT_1_URL": "https://...", "...": "... up to SHOT_6_URL" },
     "en": { "PRODUCT": "...", "...": "... every EN placeholder from the 15 sections" },
     "zh": { "PRODUCT": "...", "...": "... every ZH placeholder, same keys, Chinese content" }
   }
   ```

   - `en` and `zh` must each provide every `{{PLACEHOLDER}}` key found in
     `templates/product-teardown-template-en.html` / `-zh.html` (both templates share the
     same key set — verify with
     `grep -oE '\{\{[A-Za-z0-9_★☆]+\}\}' templates/*.html | sort -u`).
   - AI meter: set exactly one of `ACTIVE_IF_ASSISTIVE` / `ACTIVE_IF_EMBEDDED` /
     `ACTIVE_IF_AUTONOMOUS` to the literal string `active`, the other two to `""`.
   - Star row: use `★` / `☆` characters.
   - UX bars (`TTV_BAR`, `COG_BAR`, `DELIGHT_BAR`, `TRUST_BAR`, `STRUGGLE_BAR`): integers
     0–100.
   - Never write real content into `zh` by machine-translating `en` after the fact —
     write both in the same pass so the Chinese reads naturally, not translated.
3. **Render both reports:**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-teardown/scripts/render_teardown.py \
     --data ./teardown-<slug>.json \
     --out-dir ./output
   ```
   The script fails loudly (non-zero exit, listing every unresolved key) if any
   placeholder in either template wasn't supplied — fix the JSON and re-run rather than
   shipping a report with visible `{{...}}` text.
4. Output filenames are `product-teardown-<slug>-{en,zh}-<YYYYMM>.html`, cross-linked via
   the bottom-right language switcher (same-directory relative links — keep both files
   together).
5. Open the EN version (`open <path>` on macOS) so the user can review it and click
   **中文** to switch.

## Design principles

1. **Structure over opinion.** Every section answers a specific question — never "here's
   what I think about this app."
2. **Loops, not features.** The Core Loop section is the spine — features are downstream
   of the loop.
3. **AI placement is a spectrum, not a badge.** Pick one of Assistive/Embedded/Autonomous
   and defend it with evidence.
4. **Screenshots must come from the product itself.** Pull `og:image` marketing assets,
   never random third-party screenshots.
5. **Bilingual by default, written together.** EN + ZH ship in the same run, cross-linked,
   each written fresh — not translated after the fact.

## Repo contents

```
product-teardown/
├── SKILL.md
├── templates/
│   ├── product-teardown-template-en.html   # English report template
│   └── product-teardown-template-zh.html   # Chinese report template (identical placeholders)
├── scripts/
│   └── render_teardown.py                  # Fills both templates from one JSON data file
└── references/
    └── example-data.json                   # Schema-valid stub covering every placeholder key
```

- **Placeholders:** `{{ALL_CAPS_KEYS}}`. `render_teardown.py` fills them via `str.replace`
  with keys sorted longest-first so prefixes never collide (e.g. `SHOT_1_URL` before
  `SHOT_1`).
- **Templates are single-file, dependency-free HTML** (one Google Fonts link for CJK PDF
  embedding). Print-optimized (`Cmd+P` → clean PDF) and include a client-side
  "Export MD" button.
- **Aesthetic:** cream paper + serif display + yellow accent, matching the rest of this
  marketplace's content-generate report templates.

## Pitfalls

1. **Missing keys fail loudly, not silently.** `render_teardown.py` exits non-zero and
   lists every unresolved `{{KEY}}` — never hand-patch a rendered HTML file to hide a
   leftover placeholder; fix the JSON and re-render.
2. **EN and ZH must share the exact same key set.** If you edit one template's markup,
   re-diff the placeholder lists (see command above) before shipping — a key present in
   only one language silently breaks that language's render.
3. **Don't invent hard numbers.** Any figure not directly observable in the product must
   be prefixed `[inferred]` / `[推断]`, or flagged `[需用户补充]` if you genuinely need the
   user to supply it.
4. **Screenshots must be hot-linkable.** A URL that requires auth or blocks hotlinking
   renders as a broken image in the gallery — verify with `curl -sI <url>` before use.
5. **Keep EN/ZH output files in the same directory.** The language switcher uses
   same-directory relative `href`s (`LANG_EN_HREF` / `LANG_ZH_HREF` are bare filenames).
