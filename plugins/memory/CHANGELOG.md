# Changelog — memory plugin

All notable changes to the `memory` plugin are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — Phase 2 (iter2)

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
