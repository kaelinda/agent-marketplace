# Codex Dual-Runtime Support Design

Date: 2026-07-10
Status: Approved for implementation

## Goal

Make manji a first-class plugin marketplace for both Claude Code and Codex while
keeping one implementation of every skill. Users must be able to discover,
install, and run the seven existing plugins through either host's native plugin
workflow.

## Success Criteria

1. Claude Code continues to consume `.claude-plugin/marketplace.json` and each
   plugin's `.claude-plugin/plugin.json`.
2. Codex consumes `.agents/plugins/marketplace.json` and each plugin's
   `.codex-plugin/plugin.json` without relying on legacy compatibility behavior.
3. Both marketplaces expose the same seven plugin names, order, and logical
   sources; the paired plugin manifests expose matching identity and versions.
4. A skill has one `SKILL.md`; runtime-specific manifests do not duplicate skill
   implementation.
5. Installed skills do not depend on `${CLAUDE_PLUGIN_ROOT}`, Claude-only tools,
   or files outside their plugin package.
6. An isolated Codex home can add this repository as a marketplace, list all
   seven plugins, and install at least one representative plugin.
7. Existing focused tests remain green and a new compatibility suite prevents
   the two runtime surfaces from drifting.

## Chosen Approach

Use dual native manifests with shared implementation:

```text
agent-marketplace/
├── .claude-plugin/marketplace.json
├── .agents/plugins/marketplace.json
└── plugins/<name>/
    ├── .claude-plugin/plugin.json
    ├── .codex-plugin/plugin.json
    └── skills/<skill>/SKILL.md
```

The Claude files remain authoritative for Claude Code. The Codex files are
committed release artifacts, not generated during installation, so a local or
Git marketplace works without an extra build step. Cross-file tests enforce
parity instead of introducing a manifest generator.

## Marketplace Metadata

The Codex marketplace uses the native repo-local schema:

- top-level name `manji` and display name `Manji`
- one entry per existing plugin, in the same order as the Claude marketplace
- local sources under `./plugins/<name>`
- `policy.installation` set to `AVAILABLE`
- `policy.authentication` set to `ON_INSTALL`
- a human-readable Codex category for every entry

Each Codex plugin manifest contains the existing identity and license metadata,
`skills: "./skills/"`, and an `interface` block with display name, descriptions,
developer name, category, capabilities, repository URL, starter prompts, and a
restrained brand color. No icon or screenshot path is declared unless the file
exists inside the plugin.

## Runtime-Neutral Skills

Skill instructions use paths relative to their own directory. Existing
`${CLAUDE_PLUGIN_ROOT}` examples become `<skill_dir>/...` examples, which both
hosts can resolve from the selected `SKILL.md`.

References to `AskUserQuestion` become behavioral instructions:

- use the host's structured user-input tool when one is available
- otherwise ask one concise question in the conversation
- never infer consent for writes, publishing, destructive Git operations, or
  external side effects

Host names remain where they describe actual data sources or behavior, such as
the MBTI skill reading both `~/.claude/projects` and `~/.codex/sessions`.

## Core Plugin

The core plugin remains responsible for update detection, but update execution
must be host-native:

- Codex: `codex plugin marketplace upgrade manji`
- Claude Code: `/plugin marketplace update manji`

The skill asks for confirmation before updating and reports the applicable
command. It no longer invokes a repository-level script that performs
`git reset --hard`. Version-checking support needed by the plugin moves under
`plugins/core/scripts/` so the installed plugin is self-contained. Any root
helper retained for backwards compatibility delegates to the plugin-local
implementation and performs no destructive update.

## Old-Bird Plugin

`local-distill-me` becomes a dual-runtime private-rules manager:

- Claude Code keeps `CLAUDE.local.md` linked to the shared private index.
- Codex uses `AGENTS.override.md` linked to a Codex-specific shared index.
- Both indexes point to the same project rule documents where their semantics
  overlap.
- The Codex override explicitly instructs Codex to read a tracked `AGENTS.md`
  when present before applying private additions, so repository guidance is not
  silently discarded.
- Generated local entry files are added to `.gitignore` and remain outside
  version control.
- Existing files are backed up before replacement; reruns remain idempotent.

The setup asks which hosts to configure and defaults to both when both CLIs or
state directories are detected. It does not modify global Codex configuration.

## Other Plugins

- `agents`: retain Cursor dispatch behavior; remove wording that assumes the
  Claude Bash tool is the only caller.
- `memory`: keep the shared CLI and six skills; document natural-language skill
  invocation for Codex alongside Claude slash commands.
- `content-generate`: replace plugin-root variables in cover and publishing
  workflows; preserve existing external credential checks and confirmation
  gates.
- `playground`: retain explicit Claude and Codex session-source support.
- `project-docs`: keep one generation workflow and document invocation through
  natural language or the host's skill surface.

## Validation And Tests

A root-level Python `unittest` suite will fail before compatibility files are
added, then enforce:

1. Both marketplace files parse as JSON.
2. Plugin name, order, and logical source remain aligned across marketplaces.
3. Every plugin has both manifests and matching identity/version fields.
4. Every Codex manifest has required `interface` metadata and a valid skills
   path.
5. Every discovered `SKILL.md` has `name` and `description` frontmatter.
6. Active skill instructions contain no `${CLAUDE_PLUGIN_ROOT}` or direct
   `AskUserQuestion` dependency.
7. Plugin-local scripts referenced by compatibility-sensitive skills exist.

Verification also runs:

- the Codex plugin validator against all seven plugin directories
- existing focused Python test suites
- shell syntax checks for changed shell scripts
- JSON parsing and `git diff --check`
- `codex plugin marketplace add`, `codex plugin list`, and
  `codex plugin add project-docs@manji` with a temporary isolated `CODEX_HOME`

The isolated home prevents validation from changing the user's installed Codex
plugins or marketplaces.

## Documentation And Versioning

The root README, contribution guide, and onboarding documents will describe
both installation paths and dual-manifest contribution rules. Generated
onboarding HTML will be rebuilt from the Markdown source when its build script
supports the current document set.

The marketplace version moves from `0.6.0` to `0.7.0`. Plugins with changed
runtime behavior receive a compatible minor or patch release in both manifests;
plugins receiving packaging metadata only retain their current version. The
Claude marketplace entry, Claude manifest, and Codex manifest must always agree
for each plugin.

## Non-Goals

- Removing Claude Code support or replacing its native marketplace files
- Maintaining separate Claude and Codex copies of a skill
- Adding MCP servers, hooks, apps, icons, or screenshots that do not already
  exist
- Modifying the user's real Codex marketplace configuration during tests
- Redesigning the functional behavior of content, memory, MBTI, or documentation
  workflows beyond compatibility requirements

## Risks And Mitigations

- Manifest drift: parity tests compare both surfaces on every validation run.
- Host-specific wording returns later: forbidden-pattern tests cover active
  skill instructions.
- Codex private rules hide tracked guidance: the generated override explicitly
  loads tracked `AGENTS.md` before private additions.
- Update flow mutates a checkout: destructive updater behavior is removed and
  replaced with host-native marketplace update commands.
- Local verification pollutes user state: all Codex integration checks use a
  temporary `CODEX_HOME`.
