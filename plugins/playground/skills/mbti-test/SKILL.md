---
name: mbti-test
description: Use when the user wants a fun MBTI personality reading inferred from their own local AI-coding history — analyzes the prompts they typed into Claude Code (~/.claude/projects) and Codex (~/.codex/sessions) and scores the four MBTI dichotomies (E/I, S/N, T/F, J/P) with transparent, fully local heuristics. Entertainment only, never uploads data. Triggers: "测一下我的 MBTI"、"根据我的对话历史分析人格"、"my coding personality"、"分析我和 AI 的聊天风格".
---

# mbti-test

Infer a playful MBTI type from **how you talk to your coding agents**. The script
reads the prompts *you* typed into Claude Code and Codex, measures four behavioural
axes, and prints a personality card with evidence.

> 娱乐向工具，不是心理诊断。它只反映你在 AI 编码会话里的**表达习惯**。

**Privacy:** 100% local. It only reads local session files, only analyses *your own*
text (assistant replies, tool output, sub-agent transcripts and oversized pastes are
filtered out), and never makes a network call. Run it offline.

## Quick Start

```bash
SCRIPT=plugins/playground/skills/mbti-test/scripts/mbti_test.py

# Full reading across both tools, all time
python3 $SCRIPT analyze

# Show the keyword evidence behind each axis
python3 $SCRIPT analyze -v

# Scope it
python3 $SCRIPT analyze --source codex --days 30      # only Codex, last 30 days
python3 $SCRIPT analyze --project hr-console          # only sessions whose cwd ~ "hr-console"

# Machine-readable
python3 $SCRIPT analyze --json

# What would be analysed?
python3 $SCRIPT sources
```

`analyze` is the default — `python3 $SCRIPT` alone behaves like `python3 $SCRIPT analyze`.

## Commands & options

| Command | Purpose |
|---------|---------|
| `analyze` (default) | Score the corpus and print the MBTI card. |
| `sources` | List the discovered Claude/Codex session files and counts. |

| Option (analyze) | Default | Effect |
|------------------|---------|--------|
| `--source {all,claude,codex}` | `all` | Which tool's history to read. |
| `--days N` | all time | Only sessions modified within the last N days. |
| `--project SUBSTR` | — | Only sessions whose `cwd` contains SUBSTR. |
| `--min-len N` | `2` | Ignore prompts shorter than N length-units. |
| `--max-chars N` | `4000` | Ignore messages longer than N chars (pastes / slash-command expansions / auto-generated plans — not conversational voice). `0` = no limit. |
| `-v, --verbose` | off | Show the top matched keywords per axis. |
| `--json` | off | Emit structured JSON. |
| `--no-color` | off | Disable ANSI color. |

## How it reads your history

- **Claude Code**: `~/.claude/projects/**/*.jsonl` — keeps `type:"user"` turns whose
  content is your typed text. Drops tool results, sub-agent **sidechain** turns,
  SDK/system messages, harness `<system-reminder>` blocks, and `/clear`-style meta.
- **Codex**: `~/.codex/sessions/**/rollout-*.jsonl` and `~/.codex/archived_sessions/`
  — keeps `event_msg` entries of type `user_message`.
- Sub-agent transcript files (`**/subagents/**`, `agent-*.jsonl`) are skipped entirely.

Override the locations with `CLAUDE_HISTORY_DIR` / `CODEX_HISTORY_DIR` if your data
lives elsewhere (handy for testing).

## How the four axes are scored

Each axis collects **evidence points** for both poles from keyword rates (Chinese +
English lexicons) and structural signals, then converts them to a probability with a
small Laplace prior so a thin corpus stays near 50/50.

| Axis | Leans left when… | Leans right when… |
|------|------------------|-------------------|
| **E / I** | longer prompts, more turns per session, "我们/讨论/let's" think-aloud | terse one-liners, fewer turns |
| **S / N** | concrete: file paths, line refs, `字段/参数/具体/error` | abstract: `架构/思路/原理/为什么/design` |
| **T / F** | impersonal logic: `逻辑/验证/对比/performance` | politeness & warmth: `请/谢谢/please/thanks`, emoji, `!` |
| **J / P** | plan-first: `计划/先…然后/列出/plan/steps` | exploratory: `试试/看看/或者/maybe/tweak` |

Per-keyword counts are capped per prompt so one repetitive message can't dominate;
the E/I length signal uses the **median** prompt size to resist outliers. Full
coefficient table and rationale: [`references/scoring.md`](references/scoring.md).

## Output

A card with the 4-letter type and Chinese nickname, a bar per axis with the winning
letter and confidence %, a signals panel (median length, prompts/session, densities),
and — with `-v` — the matched-keyword evidence. Small samples (<20 prompts) print a
low-confidence warning.

## Tests

```bash
python3 plugins/playground/skills/mbti-test/tests/test_mbti_test.py
```

Offline, synthetic transcripts only — covers extraction filters, the keyword cap,
oversized/sub-agent skipping, and directional sanity checks for each axis.
