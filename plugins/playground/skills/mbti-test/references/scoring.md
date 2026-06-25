# mbti-test scoring reference

This document explains exactly how `mbti_test.py` turns your prompt history into a
4-letter type. It is intentionally simple and transparent — the tool is for fun, not
psychometrics — but the heuristics are deterministic and reproducible.

## Pipeline

1. **Discover** session files (Claude Code + Codex).
2. **Extract** only the user's own typed prompts (see SKILL.md for what is dropped).
3. **Filter** by `--days` / `--project` / `--min-len` / `--max-chars`.
4. **Measure** keyword rates and structural densities per prompt.
5. **Score** each axis into evidence points → probability → letter + confidence.

## Per-prompt measurements

- **length_units** = (count of CJK characters) + (count of ASCII word tokens). This
  keeps Chinese and English prompts roughly comparable.
- **keyword hits** per pole, matched case-insensitively. CJK keywords match as
  substrings; ASCII keywords match on word boundaries. Each keyword's count is capped
  at `_KW_CAP_PER_PROMPT = 3` within a single prompt so one repetitive or pasted
  message cannot dominate the corpus.
- **structural densities** (each capped per prompt, then averaged across the corpus):
  - `path_density` — file-path-like tokens + `:line` references → Sensing
  - `code_density` — backtick spans + camelCase/snake_case/`foo()` identifiers → Sensing
  - `num_density` — standalone integers → Sensing
  - `emoji_density`, `exclaim_density`, `polite_density` → Feeling
  - `why_density` — `为什么` / `why` → Intuition
  - `seq_density` — `先 … 然后/再` sequencing → Judging
- **terse_ratio** — fraction of prompts ≤ 6 length-units → Introversion
- **median length** and **prompts-per-session** feed the E/I axis (median is used
  instead of mean so a few huge prompts don't swing the result).

## Evidence points per pole

`kw_rate[X]` = average capped mentions of pole-X keywords per prompt.

```
E = 1.4·kw_rate[E] + 0.3·len_excess  + 0.5·pps_excess
I = 0.9·terse_ratio + 0.3·len_deficit + 0.5·pps_deficit
S = 1.0·kw_rate[S] + 1.2·path_d + 0.8·code_d + 0.6·num_d
N = 1.2·kw_rate[N] + 0.6·why_d
T = 1.0·kw_rate[T] + 0.25            # mild "blunt by default" prior for devs
F = 1.4·kw_rate[F] + 0.8·polite_d + 0.6·emoji_d + 0.4·exclaim_d
J = 1.2·kw_rate[J] + 0.4·seq_d
P = 1.2·kw_rate[P]
```

where, with median length `m`, sessions count and `pps = prompts / sessions`:

```
len_excess  = max(0, (m   - 12) / 16)      len_deficit = max(0, (12 - m)   / 16)
pps_excess  = max(0, (pps - 10) / 12)      pps_deficit = max(0, (10 - pps) / 12)
```

## From points to a letter

For an axis with poles (L, R) and a Laplace prior `α = 0.15`:

```
p_left  = (points_L + α) / (points_L + points_R + 2α)
p_right = 1 − p_left
letter  = L if p_left ≥ p_right else R
confidence% = round(100 · max(p_left, p_right))
```

The prior keeps a sparse corpus close to 50/50 instead of swinging hard on one or two
matched keywords. The I, and partly T, poles lean on structural/length signals rather
than keyword lists (there is no natural "introvert vocabulary").

## Caveats

- The lexicons are hand-built and skewed toward developer phrasing in Chinese and
  English; other languages will under-match.
- Coefficients are tuned by eyeballing real local corpora, not validated against any
  ground-truth MBTI assessment. Treat the result as a mirror of your *prompting style*,
  not your personality.
- Auto-generated plan pastes and slash-command expansions are excluded by default
  (`--max-chars 4000`) because they reflect tooling, not how you talk.
