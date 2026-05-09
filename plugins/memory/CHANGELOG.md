# Changelog — memory plugin

All notable changes to the `memory` plugin are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — Phase 3 (iter3)

### Added
- **Cross-agent sharing layer.** New `lib/sharing.py` `SharingManager`
  + identity-string helpers (`parse_identity`, `is_identity_string`,
  `owner_from_scope`). Pure-Python ACL evaluation runs locally — the
  adapter only stores grants.
- **`MemoryAdapter` protocol grew three methods**: `share()`,
  `unshare()`, `list_subscribed()`. `search()` gained a fifth keyword
  arg `extra_scopes` so callers can fold in shared / team scopes
  without N round-trips.
- **`team` entity_type** in `Config.build_scope()`. New config slots:
  `identity.team_ids: list[str]`, `safety.auto_include_subscribed:
  bool`. `OV_TEAM_IDS` env override (comma-separated, whitespace tolerated).
- **ACL fields on memory schema**: `owner_id`, `visibility`
  (`private` | `team` | `public`, default `private`), `shared_with` (list of
  identity strings), `shared_perms` (per-target `read` | `write`).
- **New skill `memory-share`** (`skills/memory-share/`) with three
  entry-points: `run_share`, `run_unshare`, `run_list_subscribed`.
  Goes via SharingManager so target validation runs before any backend
  call.
- **New slash command** `/memory-share` (`commands/memory-share.md`)
  dispatching `share` / `unshare` / `subscribed`.
- **CLI subcommands**: `memory-cli share <id> --to <target>`,
  `memory-cli unshare <id> --to <target>`, `memory-cli subscribed`.
  `capture` got `--visibility` + repeatable `--share-with`. `recall`
  got `--include-subscribed` / `--no-include-subscribed`.
- **Formatter provenance**: `format_recall_block(memories,
  viewer_identity=...)` now appends `(shared by user:bob)` after lines
  whose `owner_id` differs from the viewer.
- **Tests**: `tests/test_sharing.py` (28 cases — ACL paths, share
  round-trip, subscription dedup, recall ACL filter), `tests/test_scope.py`
  (10 cases — `build_scope` per entity_type, OV_TEAM_IDS edge cases,
  identity aggregation).

### Changed
- `capture.run_capture` now writes `owner_id` (`user:` for most types,
  `agent:` for `agent_reflection`), `visibility` (default `private`),
  `shared_with`, `shared_perms` on every new memory. Legacy Phase 2
  memories without these fields still work — `SharingManager.can_access`
  falls back to parsing `scope`.
- `capture` rejects `visibility="team"` when the resolved scope doesn't
  contain `/teams/` (silent fall-through here would be a reverse data
  leak: "user wanted team visibility but stored under user scope").
- `recall.run_recall` has a new optional `include_subscribed` arg and
  passes `extra_scopes=SharingManager.subscribed_scopes()` to
  `adapter.search` when enabled. Results are post-filtered through
  `SharingManager.visible_memories` so a misbehaving adapter cannot
  leak unauthorized memories. Off by default — `safety.auto_include_subscribed`
  flips it on globally.
- `Config.build_scope` now rejects unknown `entity_type` with
  `ValueError`. Previously it would silently format whatever you gave
  it into the URI template.
- `adapter_protocol.AdapterResponse.from_dict` documentation tightened
  to call out the legacy / new error-shape support is for migration.
- All three real adapters (`HTTPAdapter`, `MCPAdapter`, `Mem0Adapter`)
  now satisfy the expanded `MemoryAdapter` protocol — Mem0Adapter
  with full sharing support via `metadata.shared_with`, HTTP / MCP
  via client-side read-modify-write of memory metadata.
  HTTP / MCP `list_subscribed` returns ok=False with the explanatory
  error "OpenViking ... does not expose a subscription index; use mem0
  backend or wait for Phase 4 ACL endpoints."

### Migration

Phase 2 memories are forward-compatible. They have no `owner_id` /
`visibility` / `shared_with`, which means `SharingManager.can_access`
treats them as private and uses the scope URI to derive ownership.
No migration script needed.

If you have automation that calls `Config.build_scope` with an unusual
`entity_type`, audit it — Phase 3 raises on unknown types. Before, it
silently produced URIs like `viking://tenants/x/orgs/y/memories/`.

## Phase 2 (iter2) — released 2026-05-08

### Added
- `commands/recall.md` and `commands/memory-doctor.md` slash commands so
  users can invoke memory operations from inside Claude Code (previously
  the only entry point was `python scripts/ov-memory ...`).
- `tests/` test infrastructure: `pytest.ini`, `conftest.py`,
  `tests/fakes/fake_adapter.py` (in-memory `MemoryAdapter` implementation),
  and `tests/test_adapter_contract.py` (shared adapter contract suite).
- `lib/skill_loader.py` with `load_skill_module()` and
  `load_subcommand_module()` helpers for dynamic loading of kebab-case
  skill / subcommand modules.
- `ConfigError` raised when `identity.user_id` / `identity.agent_id`
  defaults to `default_*` and `safety.allow_default_identity` is not
  explicitly set to `true`.
- `doctor` now hard-fails when default identity is detected outside opt-in.

### Changed
- **Directory layout flattened** to comply with Claude Code plugin spec:
  - `plugins/memory/skills/lib/` → `plugins/memory/lib/`
  - `plugins/memory/skills/scripts/` → `plugins/memory/scripts/`
  - `plugins/memory/skills/schema/` → `plugins/memory/schema/`
  - `plugins/memory/skills/config.example.json` →
    `plugins/memory/config.example.json`
  - `plugins/memory/skills/skills/<name>/` →
    `plugins/memory/skills/memory-<name>/` (5 keepers only)
- `scripts/ov-memory` renamed to `scripts/memory-cli`. `scripts/ov-memory`
  remains as a shell-shim alias for one minor version and will be removed
  in v0.3.0.
- Skill set reduced from 12 to 5 Claude Code skills:
  `memory-recall`, `memory-capture`, `memory-commit`, `memory-doctor`,
  `memory-admin`. The other 7 (`forget`, `merge`, `project-memory`,
  `environment-memory`, `case-memory`, `preference-memory`,
  `agent-reflection`) became plain CLI subcommands under
  `scripts/subcommands/<name>.py` — identical behavior, no SKILL.md.
- All adapters (`HTTPAdapter`, `MCPAdapter`, `Mem0Adapter`) now return
  a normalized `AdapterResponse` dict (`{ok, data, error, meta}`) per
  the protocol in `lib/adapter_protocol.py`. Callers should check
  `result.get("ok")` instead of `result.get("error")`.
- `OVClient` error shape changed from `{"error": True, "reason": ...}`
  to `{"ok": False, "error": "..."}`.
- `capture.py` memory ID generator now uses a full UUID4 plus
  millisecond-precision timestamp (was 6-hex suffix; collision-prone
  in busy capture flows).
- `capture.py` scope assembly normalizes leading/trailing slashes to
  avoid `…//preferences/`-style double-slash paths.
- `admin.py dedupe` now hard-deletes duplicates instead of marking them
  `status="deleted"` (the old behavior left tombstones that polluted
  `browse` / `search` indefinitely).
- `admin.py restore` no longer mutates the input dicts (used `m.pop("id")`
  which broke re-iteration / re-saving of the backup data).
- `mcp_adapter.py` subprocess invocations now use an env whitelist
  (`MCP_*` only). Previously the child inherited the whole parent env,
  including `OPENVIKING_API_KEY` / `MEM0_API_KEY`.
- License declaration on the plugin top-level docs corrected to **MIT**
  to match `plugin.json`. The earlier `Private` claim in
  `skills/README.md` was a leftover from internal use.

### Removed
- `plugins/memory/skills/SKILL.md` (package-level SKILL.md is not
  recognized by Claude Code; skills are folder-scoped).
- `plugins/memory/skills/skills/` (the doubly-nested directory and the
  7 SKILL.md files for demoted sub-skills).
- The `openviking-memory-skills` skill name. The plugin name is `memory`.

### Migration

If you have a script that calls `ov-memory ...`, no immediate change is
needed — the alias still works. To update, replace `ov-memory` with
`memory-cli`. Both binaries live in `plugins/memory/scripts/`.

If you have a config file at `~/.openviking-memory/config.json`,
it continues to be read; no migration required.

### Notes

This is the first iteration where all 9 public adapter methods uniformly
return `AdapterResponse`. Any external integration that previously relied
on `result.get("error")` (the old HTTP/MCP shape) needs to switch to
`result.get("ok") is False`.
