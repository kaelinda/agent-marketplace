---
name: product-teardown
description: "Use when the user asks to 'teardown', 'break down', 'reverse-engineer', or do a deep PM/strategy analysis of any product (Linear, Notion, Cursor, a competitor, an internal product, ...). Reverse-engineers the product across four layers — Product, Business, Technology, Strategy — through a fixed, MECE framework where every section answers one specific question, weighted toward Core Loop as the section that explains everything else. Renders a bilingual (EN + ZH) print-ready HTML report with a product-screenshot gallery. Triggers: 拆解某产品, 产品分析, product teardown, reverse-engineer this product, PM breakdown, competitor deep dive."
version: 2.0.0
license: MIT
metadata:
  hermes:
    tags: [product, teardown, pm, strategy, business, architecture, ai, analysis, html, report, bilingual]
    related_skills:
      - competitor-landscape
      - ai-architecture-review
      - md-to-html
      - ali-oss
---

# Product Teardown

## Overview

A Principal-PM-level product teardown. Point it at any product and it reverse-engineers
the thing as a *system* — loops, strategy, moat, opportunities — instead of writing a
"5 things I like about this app" review. The output is a structural read of *why the
product wins, where it leaks, and what the next move should be*.

This is not a prompt that answers "please analyze this." It is a **workflow**:

```
Input (product name / URL)
    → Reasoning (research + inference, assumptions marked)
    → Framework (4 layers, 15 fixed questions, MECE)
    → Artifacts (chat teardown + bilingual HTML report)
    → Output (two cross-linked, print-ready files)
```

Adapted from the open-source
[product-teardown-skill](https://github.com/yanliudesign/product-teardown-skill) (MIT) by
Dreameryanyan, restructured around a 4-layer framework and reweighted toward Core Loop and
opportunity rigor per workspace design review (2026-07-28).

## When to Use

Invoke when the user asks to "teardown X" / "拆解一下 X" / "break down Notion" /
"analyze this product like a PM" / "reverse-engineer our competitor's app". Works for
consumer, B2B, and AI-native products alike.

For a **standalone deep dive** on just the competitive matrix or just the AI/agent
architecture, use the sibling skills `competitor-landscape` and `ai-architecture-review`
instead — this skill calls for the same depth inline (sections 8 and 10 below) but a
narrower, single-topic request is better served by the focused skill.

## The framework: 4 layers, 15 questions, one MECE table

Don't think of this as "11 (or 15) sections to fill in." Every section exists to answer
**exactly one** question — no overlap, no gaps (MECE: Mutually Exclusive, Collectively
Exhaustive). Chained together, the 15 questions trace one thinking path:

```
是什么 → 为什么有人用 → 为什么持续用 → 为什么容易扩张 → 为什么赚钱
  → 为什么增长 → AI 放在哪 → 哪里漏水 → 还能去哪 → 一句总结
```

...which resolves into 4 layers:

| Layer | Resolves | Sections |
|---|---|---|
| **① Product** | Discovery + Retention — what it is, why anyone pays, why they keep coming back | 1 Snapshot · 2 JTBD · **3 Core Loop** · 5 Craft Signals · 6 UX Quality |
| **② Business** | Why it makes money, why it grows | 7 Business Model · 8 Competitor Landscape · 9 Growth Strategy |
| **③ Technology** | Why it's buildable, why it scales, where AI sits | 4 Architecture & Stack · 10 AI / Agent Readiness |
| **④ Strategy** | Where it should go next | 11 Metrics · 12 Friction · 13 Risk Matrix · 14 Opportunities · 15 Final Verdict |

The fixed question each section answers — hold the writer to exactly this, nothing vaguer:

| # | Section | The one question it answers |
|---|---------|------------------------------|
| 1 | Product Snapshot | What is this, beyond the marketing description? |
| 2 | Users & JTBD | Why does anyone pay / show up? |
| 3 | **Core Loop** | Why do they come back? |
| 4 | Architecture & Stack | Why can this scale — technically? |
| 5 | Craft Signals | What concrete decisions make it feel premium? |
| 6 | UX Quality | Where does the experience help or hurt? |
| 7 | Business Model | Why does it make money? |
| 8 | Competitor Landscape | Where does it sit vs. rivals, on which axes? |
| 9 | Growth Strategy | Why does it grow? |
| 10 | AI / Future Readiness | Where does AI sit today, and where next? |
| 11 | Metrics They Optimize For | What do they actually measure (and refuse to)? |
| 12 | Friction & Weaknesses | Where does it leak? |
| 13 | Risk Matrix | What could kill it, and how fast? |
| 14 | Opportunities | What should ship next quarter? |
| 15 | Final PM Verdict | One sentence: wins / breaks / moat. |

## Step 1 · Deliver the teardown in chat

Produce the full 15-question analysis in chat, grouped visibly under the 4 layer headers
above, in order. Ground rules:

- Be structured, analytical, and opinionated — avoid marketing language.
- Prefer systems thinking over feature listing; find the loop first, then work outward.
- JTBD beats persona — "what did they hire it to *replace*" beats "who uses it."
- When uncertain, state assumptions explicitly. Never invent hard numbers — prefix
  inferred figures with `[inferred]` (EN) / `[推断]` (ZH), or `[需用户补充]` when you
  genuinely don't know.

### §3 Core Loop is the spine — give it ~30% of your total analysis effort

Every other section is downstream of the loop:

```
Loop → Feature → UI
```

If the loop is understood, the product is understood. Name the loop as
**Trigger → Action → Reward → Return**, e.g.:

- Linear: `Issue → Assign → Progress → Done → Next Issue`
- Notion: `Write → Share → Collaborate → Knowledge → Write Again`
- Perplexity: `Question → Answer → Follow-up → Discovery → Question`
- Cursor: `Ask → Code → Review → Commit → Ask`

Don't stop at naming the loop — explain what makes each step *sticky* (why the trigger
reliably fires, why the reward outweighs the cost of the action, why "return" isn't
optional).

### §4 Architecture & Stack — go past information architecture

The original framework's "Architecture" section is easy to shrink into "here are the
tabs in the left nav" (information architecture). That's necessary but not sufficient —
cover the technical substrate too, at whatever depth is publicly inferable:

- **Core surfaces + entities** (information architecture — keep this, it's still useful).
- **Data & backend**: what's the system of record, how is it structured, what's cached
  vs. computed on demand.
- **Search / retrieval**: full-text, vector, hybrid — and what it's indexing.
- **Integration surface**: public API, webhooks, plugin/extension model.
- **For AI-native products**, treat this as its own sub-question — see §10 below and
  reach for the `ai-architecture-review` sibling skill if the user wants that depth
  standalone.

### §7–9 Business layer — go past "revenue model" and "growth loops"

A VC-grade read needs the unit-economics chain, not just the label:

```
Revenue → Cost → Margin → CAC → LTV → Expansion (PLG / Enterprise / Hybrid)
```

State each link even when [inferred] — "PLG-led, CAC near-zero for the bottom-up motion,
LTV expansion via seat growth + tier upgrades" is a sentence, not a research project.

### §8 Competitor Landscape — matrix *and* a 2D positioning read

Keep the existing dimension-by-dimension matrix (already in the template), but also state
where the product sits on a 2D map in prose — pick the two axes that matter most for this
category (e.g. Enterprise ↔ Personal on one axis, Opinionated ↔ Configurable on the
other) and place each named rival on it. For a deeper, standalone competitive session
(more rivals, more axes, a dedicated write-up), use the `competitor-landscape` skill.

### §10 AI / Future Readiness — go past Assistive/Embedded/Autonomous

Keep the 3-stage placement (the template needs it), but for AI-native or AI-augmented
products, analyze the actual AI architecture underneath, not just the UI-level label:

```
Model → Tool → Memory → Planning → Agent → Workflow → Evaluation
```

E.g. Cursor's real AI architecture is `Prompt → Context → Repo Index → Retrieval →
Planning → Edit → Apply → Feedback` — that's the analysis that matters, not "it has AI
autocomplete." For a full standalone AI/agent-architecture deep dive, use the
`ai-architecture-review` sibling skill.

### §14 Opportunities — every idea must trace a chain, not assert a feature

Reject "they should add AI." Require:

```
Feature → which JTBD does it serve → which loop step does it strengthen → which metric moves
```

Each of the 3 improvement opportunities + 1 strategic shift + 1 moonshot must show this
chain explicitly (even briefly) in its `_DETAIL` field.

## Step 2 · Generate the bilingual HTML report and open it

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

1. **Structure over opinion.** Every section answers a specific, fixed question — never
   "here's what I think about this app."
2. **Loops, not features.** Core Loop is the spine and gets the most analytical effort —
   features are downstream of the loop.
3. **AI placement is a spectrum, not a badge.** Pick one of Assistive/Embedded/Autonomous
   and defend it with evidence; for AI-native products, go one level deeper into the
   Model/Tool/Memory/Planning/Agent/Workflow/Evaluation stack.
4. **Opportunities must trace a chain.** Feature → JTBD → Loop step → Metric, every time.
5. **Screenshots must come from the product itself.** Pull `og:image` marketing assets,
   never random third-party screenshots.
6. **Bilingual by default, written together.** EN + ZH ship in the same run, cross-linked,
   each written fresh — not translated after the fact.

## Why this isn't split into 20 micro-skills

An earlier design review proposed decomposing this into ~20 tiny skills (one per
sub-question: `jtbd`, `core-loop`, `pricing`, `moat`, `code-review`, `observability`, ...).
That was deliberately not done here: Claude Code skills are selected by trigger-phrase
matching, not programmatically chained, so 20 near-identical "分析一下这个产品的 X" triggers
would mostly collide and hurt discoverability rather than help it, without buying real
composability. Instead: this skill stays a single cohesive workflow with the deepened
4-layer content above, and only the two sub-topics with a genuinely distinct, likely-to-be-
invoked-alone use case were split out as real sibling skills — `competitor-landscape` and
`ai-architecture-review`. Generic engineering review (code review, performance,
security, observability) was intentionally left out of this plugin: those are
product-agnostic and already exist as skills elsewhere in this environment — duplicating
them here would be scope creep, not composability.

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
  marketplace's report templates.

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
6. **Don't let Opportunity collapse into feature-listing.** If a `_DETAIL` field could be
   the answer to "what feature should we build," but doesn't say which JTBD/loop
   step/metric it moves, it's not done yet.
