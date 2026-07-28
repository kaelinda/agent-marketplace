---
name: ai-architecture-review
description: "Use when the user wants a standalone, deep technical analysis of an AI-native or AI-augmented product's actual AI/agent architecture — not the UI-level 'has an AI feature' read, but Model / Tool / Memory / Planning / Agent / Workflow / Evaluation. Triggers: AI 架构分析, agent 架构, how does X's AI actually work, AI readiness deep dive, agent architecture teardown."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [product, architecture, ai, agent, technical-analysis]
    related_skills:
      - product-teardown
---

# AI / Agent Architecture Review

## Overview

The deep version of what `product-teardown` §10 does inline (Assistive / Embedded /
Autonomous placement). Use this skill directly when the request is specifically "how does
X's AI actually work" — a full product teardown isn't needed, just the technical AI/agent
stack read.

## When to Use

- "分析一下 X 的 AI 架构 / agent 架构"
- "how is Cursor's AI actually built, not just 'it has autocomplete'"
- As a deeper follow-up after a `product-teardown` run, when the AI section needs more
  than the 3-stage spectrum placement.

## Method

For any AI-touching surface, reverse-engineer it as this pipeline (skip stages that
genuinely don't apply, but state that they don't rather than omitting silently):

1. **Model** — what's actually generating output: which model family/tier is inferable
   from latency, cost signals, and output style (frontier vs. distilled/fine-tuned);
   single-model or router across tasks.
2. **Tool** — what the model can call: search, code execution, file/repo access, external
   APIs. Name the concrete tools, not "it has tool use."
3. **Memory** — what persists across turns/sessions: conversation history, retrieved
   context (RAG over what corpus), user/task-level state, long-term memory writes.
4. **Planning** — single-shot completion vs. multi-step plan-then-execute vs. ReAct-style
   interleaved reasoning/action; is there a visible plan artifact the user can inspect.
5. **Agent** — degree of autonomy: does it ask for confirmation per step, per plan, or
   run fully unsupervised; what's the blast radius of a wrong action (reversible edit vs.
   sent email vs. spent money).
6. **Workflow** — how single actions compose into the product's actual core loop (tie
   this back explicitly to `product-teardown`'s Core Loop section if one exists).
7. **Evaluation** — what signal the product surfaces (or is inferable) that the AI
   output was good: user accept/reject actions, thumbs, downstream metric movement, or
   none visible (state that as a finding — it's often a real gap).

Worked example — Cursor's real pipeline, not "it has AI":
```
Prompt → Context → Repo Index → Retrieval → Planning → Edit → Apply → Feedback
```

## Placement on the readiness spectrum

Close with the same 3-stage placement `product-teardown` uses, now backed by the stack
analysis above instead of asserted from the UI:

- **Assistive** — suggests, human executes every action.
- **Embedded** — executes narrow, bounded actions inline, human reviews the result.
- **Autonomous / Agentic** — plans and executes multi-step work with minimal human
  checkpoints.

State the evidence for the placement in one sentence, and name the single most likely
next capability to graduate the product to the next stage.

## Output

Chat-only by default: the 7-stage breakdown (skip stages that don't apply, explicitly) +
the readiness placement + the one likely next-stage capability. If the user wants this
embedded in a shareable report, hand the findings to `product-teardown`'s §10 placeholders
(`CURRENT_AI_USAGE_PARAGRAPH`, `AGENTIC_CANDIDATE_*`, `AI_OPPORTUNITY_*` keys) or render a
standalone page with the `md-to-html` skill.

## Pitfalls

1. **Don't stop at the UI label.** "Has AI autocomplete" is not an architecture — trace
   it through Model → Tool → Memory → Planning → Agent → Workflow → Evaluation.
2. **Say when a stage doesn't apply.** A single-shot chat feature genuinely has no
   Planning or Agent stage — say so; don't force-fit a stage that isn't there.
3. **Evaluation is the stage everyone skips — don't.** "No visible evaluation signal" is
   itself a real finding (often the actual friction point for the product).
