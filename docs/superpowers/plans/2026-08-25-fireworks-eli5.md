# Fireworks ELI5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a self-contained `fireworks-eli5` marketplace plugin that turns a technical topic into a beginner-friendly, visual HTML explainer with a validated Fireworks SVG diagram and PNG export.

**Architecture:** The plugin has one public `fireworks-eli5` skill. Its prompt defines the ELI5 content contract and delegates diagram rendering to vendored Fireworks Tech Graph scripts/templates/references, so it does not depend on a private path such as `~/.agents` or `~/.claude`. The final artifact is a single offline HTML file with inline CSS and embedded SVG/PNG data, while the source SVG/PNG remain available for inspection and reuse.

**Tech Stack:** Claude Code plugin manifest, Markdown `SKILL.md`, Python 3 standard library, Bash, SVG, CairoSVG with `rsvg-convert`/Puppeteer fallback, JSON fixtures, existing marketplace/site build scripts.

---

## Baseline and Isolation

The current checkout is on `main`, aligned to the currently known `origin/main`, but it has user-owned modifications in `scripts/build-site.py`, `site/app.js`, `site/content.json`, `site/styles.css`, and `site/template.html`. Those files must not be reset or stashed away without the user's approval.

After approval, preserve the current checkout untouched, run `git fetch origin --prune`, and create the implementation branch from the fetched remote tip in an isolated sibling worktree:

```bash
git fetch origin --prune
git worktree add -b feat/fireworks-eli5 ../agent-marketplace-fireworks-eli5 origin/main
cd ../agent-marketplace-fireworks-eli5
```

The plan file can be copied into that worktree as part of Task 1. All implementation and tests run there; no user changes from the original checkout are carried into the branch.

### Task 1: Create the plugin skeleton and manifests

**Files:**
- Create: `plugins/fireworks-eli5/.claude-plugin/plugin.json`
- Create: `plugins/fireworks-eli5/README.md`
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/SKILL.md`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `VERSION`
- Modify: `README.md`
- Modify: `site/content.json`

- [ ] **Step 1: Add the plugin manifest**

Create `plugins/fireworks-eli5/.claude-plugin/plugin.json` with `name: fireworks-eli5`, SemVer `0.1.0`, MIT license, and keywords covering `eli5`, `diagram`, `svg`, `html`, and `visual-explainer`. Keep the manifest name, directory name, and marketplace entry identical.

- [ ] **Step 2: Register the plugin and synchronize market metadata**

Add one `plugins[]` entry to `.claude-plugin/marketplace.json` with category `docs` and a description that says it creates offline beginner explainers with Fireworks diagrams. Resolve the existing remote baseline's `VERSION`/market metadata mismatch while making the new plugin visible: update both `VERSION` and `metadata.version` to the next minor market version (`0.11.0`), and update the README badges/counts and plugin/skill tables to include the new plugin. Do not overwrite the unrelated site edits from the original checkout.

- [ ] **Step 3: Add plugin documentation and site overrides**

Document capabilities, trigger examples, output files, runtime prerequisites, attribution, and a local installation example in `plugins/fireworks-eli5/README.md`. Add `docs` category, plugin tagline/status, and skill description overrides to `site/content.json` so the generated marketplace page has a concise Chinese label and does not rely on a long manifest fallback.

- [ ] **Step 4: Validate manifests before continuing**

Run:

```bash
python3 -c "import json,sys; [json.load(open(p)) for p in sys.argv[1:]]; print('OK')" \
  .claude-plugin/marketplace.json plugins/fireworks-eli5/.claude-plugin/plugin.json
```

Expected output: `OK`.

### Task 2: Vendor the Fireworks diagram runtime

**Files:**
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/scripts/generate-from-template.py`
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/scripts/generate-diagram.sh`
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/scripts/validate-svg.sh`
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/scripts/test-all-styles.sh`
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/templates/*.svg`
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/references/{icons.md,style-1-flat-icon.md,style-2-dark-terminal.md,style-3-blueprint.md,style-4-notion-clean.md,style-5-glassmorphism.md,style-6-claude-official.md,style-7-openai.md,style-diagram-matrix.md,svg-layout-best-practices.md}`
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/fixtures/*.json`
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/vendor/fireworks-tech-graph-LICENSE`

- [ ] **Step 1: Copy only reusable runtime assets from the installed Fireworks skill**

Copy the generator, validation/export scripts, all supported SVG templates, regression fixtures, and the referenced style/icon/layout documents from `/Users/nowcoder/.agents/skills/fireworks-tech-graph` into the plugin's skill directory. Do not copy absolute paths or make the new prompt depend on the installed skill. Preserve the upstream MIT notice in `vendor/fireworks-tech-graph-LICENSE`.

- [ ] **Step 2: Make scripts resolve their own skill directory**

Check every copied script for path assumptions and ensure it resolves templates/references relative to its own directory. Keep the existing behavior: `generate-from-template.py` accepts a template type, output path, and JSON data; `generate-diagram.sh` validates and exports; `validate-svg.sh` performs XML/tag/marker checks.

- [ ] **Step 3: Add a deterministic fixture command**

Use a checked-in fixture such as `fixtures/agent-memory-types-style4.json` to define the smoke-test input. The fixture must generate an SVG whose arrows use source/target IDs and semantic flow types, so the validation covers the same routing contract the skill will ask agents to use.

- [ ] **Step 4: Verify the vendored runtime**

Run:

```bash
bash -n plugins/fireworks-eli5/skills/fireworks-eli5/scripts/*.sh
python3 plugins/fireworks-eli5/skills/fireworks-eli5/scripts/generate-from-template.py \
  agent plugins/fireworks-eli5/skills/fireworks-eli5/test-output/smoke.svg \
  "$(cat plugins/fireworks-eli5/skills/fireworks-eli5/fixtures/agent-memory-types-style4.json)"
python3 -c "import xml.etree.ElementTree as ET; ET.parse('plugins/fireworks-eli5/skills/fireworks-eli5/test-output/smoke.svg'); print('SVG XML OK')"
```

Expected output includes `SVG XML OK`; then run `generate-diagram.sh` on that SVG and assert the PNG exists. Keep `test-output/` ignored or remove generated output before commit.

### Task 3: Write the merged `fireworks-eli5` skill contract

**Files:**
- Modify: `plugins/fireworks-eli5/skills/fireworks-eli5/SKILL.md`

- [ ] **Step 1: Define activation and input contract**

Use frontmatter with a precise trigger description for requests such as “用小白能懂的方式解释”“画一张解释图”“/fireworks-eli5 <topic>”. Accept `$ARGUMENTS` as the topic, and state that the skill can explain systems, APIs, code flows, concepts, and agent architectures.

- [ ] **Step 2: Define the ELI5 content pipeline**

Require the agent to identify the audience, write one plain-language takeaway, reduce the topic to 3–5 numbered steps, replace jargon with concrete metaphors, and keep visible copy short. Require a “what goes in / what happens / what comes out” flow before adding implementation details.

- [ ] **Step 3: Define the Fireworks diagram pipeline**

Require diagram classification, structural extraction, layout planning, style/reference selection, semantic shapes, labeled arrows, orthogonal routing, arrow-label backgrounds, legend when two or more flows are present, and the Fireworks SVG/XML/PNG validation sequence. The prompt must call local scripts using `${CLAUDE_PLUGIN_ROOT}/skills/fireworks-eli5/scripts/...` and provide a direct local-path fallback for runtimes that do not set that variable.

- [ ] **Step 4: Define the offline HTML artifact contract**

Require one self-contained HTML output, for example `./fireworks-eli5/<slug>.html`, with:

```text
<title>topic — ELI5</title>
<main>
  <h1>one plain-language question</h1>
  <p class="takeaway">one-sentence answer</p>
  <figure aria-labelledby="diagram-caption">inline SVG or embedded PNG</figure>
  <ol>3–5 short steps</ol>
  <section>optional “why it matters” and “tiny glossary”</section>
</main>
```

Inline all CSS and SVG (or use a PNG data URI), include meaningful `alt`/caption text, responsive layout, no external network requests, no emoji in CairoSVG-rendered SVG text, and preserve the source `.svg` and `.png` beside the HTML.

- [ ] **Step 5: Define failure and safety behavior**

The skill must stop with an actionable dependency message when Python, the SVG renderer, or a required local script is unavailable; never fabricate a diagram or claim PNG export succeeded. It must not upload topics or artifacts, change git state, or overwrite an existing output without telling the user.

### Task 4: Add offline tests for the plugin contract

**Files:**
- Create: `plugins/fireworks-eli5/skills/fireworks-eli5/tests/test_fireworks_eli5.py`

- [ ] **Step 1: Test frontmatter and required workflow phrases**

Read `SKILL.md` with Python stdlib and assert it has `name`, `description`, the ELI5 output contract, local Fireworks script references, SVG/XML validation, PNG export, self-contained HTML, and dependency-failure wording.

- [ ] **Step 2: Test manifest and marketplace parity**

Parse both JSON manifests and assert `plugin.json.name == marketplace_entry.name == "fireworks-eli5"`, the source path exists, the plugin version is valid SemVer, and `VERSION == marketplace.metadata.version`.

- [ ] **Step 3: Test the renderer smoke path**

Run the vendored generator against the fixture in a temporary directory, parse the resulting SVG using `xml.etree.ElementTree`, run `validate-svg.sh`, export PNG using the available renderer, and assert the PNG has non-zero bytes. Skip only optional renderer branches with an explicit reason; the test must fail if no renderer is available.

- [ ] **Step 4: Run the focused test**

Run:

```bash
python3 plugins/fireworks-eli5/skills/fireworks-eli5/tests/test_fireworks_eli5.py
```

Expected output ends with `OK` and a non-zero exit code is treated as a failure.

### Task 5: Build and inspect the generated marketplace artifact

**Files:**
- Modify only as required by generated-site validation: `.claude-plugin/marketplace.json`, `plugins/fireworks-eli5/**`, `VERSION`, `README.md`, `site/content.json`

- [ ] **Step 1: Build the static site**

Run:

```bash
python3 scripts/build-site.py --out /tmp/fireworks-eli5-site
```

Expected output reports the new plugin and skill counts, and `/tmp/fireworks-eli5-site/index.html` exists.

- [ ] **Step 2: Assert discoverability and no placeholder leakage**

Check the generated HTML contains `fireworks-eli5`, its trigger description, and the install command, and contains no `{{...}}` template placeholders. Confirm the generated site reads only the intended branch files and does not include the original checkout's unrelated dirty edits.

- [ ] **Step 3: Run repository regression checks**

Run the focused existing tests for touched conventions plus the new test:

```bash
python3 plugins/fireworks-eli5/skills/fireworks-eli5/tests/test_fireworks_eli5.py
python3 plugins/project-docs/skills/project-docs/tests/test_build_html.py
python3 plugins/playground/skills/mbti-test/tests/test_mbti_test.py
```

Run `git diff --check` and `git status --short` to catch whitespace errors and accidental generated files.

### Task 6: Final review and delivery handoff

**Files:**
- Review: all files under `plugins/fireworks-eli5/` and metadata/docs files listed above

- [ ] **Step 1: Review the diff against fetched `origin/main`**

Confirm the diff contains only the new plugin, its market/docs registration, the intentional market-version/count updates, and the plan file if the user wants it committed. Confirm no private absolute path, secret, cache, or generated `test-output` file is tracked.

- [ ] **Step 2: Check attribution and installability**

Confirm the Fireworks MIT notice is present, the plugin can be installed from the local marketplace path, and `README.md` shows a concrete usage example:

```text
/plugin install fireworks-eli5@manji
/fireworks-eli5 how does a vector database find similar text?
```

- [ ] **Step 3: Report the result without overstating runtime verification**

Report the new branch name, fetched base SHA, changed files, test commands/results, generated artifact paths from the smoke run, and any unavailable optional renderer or Claude Code interactive installation check. Do not claim a live `/plugin install` or browser rendering check unless it actually ran.
