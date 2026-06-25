# Cross-Agent Memory Sharing (Phase 3)

> The headline feature of the `memory` plugin. This doc walks through the
> sharing model, the default safety posture, and a complete two-agent
> example. The full reference for the underlying API is the
> `SharingManager` docstring in `lib/sharing.py`; this doc is the user's
> mental model.

## TL;DR

```
agent-A captures a memory
        │
        ├── visibility=private  →  only agent-A sees it
        ├── visibility=team     →  every member of the team scope sees it
        ├── visibility=public   →  everyone in the same tenant can read
        └── shared_with=[…]     →  named identities get explicit access
                                   (per-target read / write in shared_perms)

agent-B recalls
        │
        ├── default                     →  only agent-B's own scope
        └── --include-subscribed        →  + every team scope agent-B is in
                                           (and ACL-filters anything else
                                            that slipped through)
```

## The mental model

There are three things that drive whether agent B can read a memory
written by agent A:

1. **Scope** — every memory lives in exactly one scope URI. Scopes are
   `viking://tenants/<t>/{users|agents|teams}/<id>/memories/...`.
   Membership in a scope is implicit: if your `team_ids` contains
   `platform`, you "belong to" the `viking://tenants/.../teams/platform/`
   scope.
2. **`visibility`** on the memory dict — `private` (default), `team`,
   or `public`. Affects *unrelated* readers; the owner can always read
   regardless of visibility.
3. **`shared_with` + `shared_perms`** — explicit grants. Identities
   listed here can read (and write, if `shared_perms[ident] == "write"`).

`SharingManager.can_access(memory, op)` evaluates these in order:

| Step | Check | Result if matched |
|---|---|---|
| 1 | caller is the memory's owner | allow |
| 2 | `visibility=public`, `op=read` | allow |
| 3 | `visibility=team` AND caller belongs to the memory's team scope, `op=read` | allow |
| 4 | caller (any of their identity strings) is in `shared_with`, `shared_perms` covers `op` | allow |
| 5 | otherwise | deny |

Identity strings have one shape: `<kind>:<id>` where `<kind>` is one of
`user`, `agent`, `team`. SharingManager validates this **before** any
backend call, so a typo'd target never burns a round-trip.

## Default safety posture

- `visibility` defaults to `private`. You have to explicitly opt in to
  `team` or `public` per memory.
- `safety.auto_include_subscribed` defaults to `false`. `recall`
  searches your own scope only, even if you belong to teams. Pass
  `--include-subscribed` (or flip the config) to fold in team scopes.
- Mismatched scope + visibility (e.g. `visibility=team` written to a
  user scope) errors at capture time. Silent fall-through there would
  be a reverse data leak ("you wanted team-shared but it stored as
  user-only"), so we fail loudly.
- `recall` post-filters results through `SharingManager.visible_memories`
  even after the backend returns them. Defence-in-depth: a misconfigured
  backend's ACL bug can't leak data through the plugin.

## Backend support

| Backend | `share` | `unshare` | `list_subscribed` |
|---|---|---|---|
| `mem0` | ✅ native (metadata.shared_with) | ✅ native | ✅ metadata filter |
| `openviking` (HTTP) | ⚠️ client-side read-modify-write | ⚠️ same | ❌ unsupported (Phase 4) |
| `openviking-mcp` | ⚠️ client-side read-modify-write | ⚠️ same | ❌ unsupported (Phase 4) |

If you need full sharing today, use `mem0`. The OpenViking backend
will get server-side ACL endpoints in Phase 4; until then,
`list_subscribed` cleanly returns `ok=False` with the explanatory
error and the rest works via metadata round-tripping.

## Two-agent example

Two agents share the same `tenant_id="default"` and `user_id="alice"`.
They have different `agent_id`s and both belong to `team:platform`.

### Agent A — Alice's local dev assistant

```bash
export OV_USER_ID=alice
export OV_AGENT_ID=devbot
export OV_TEAM_IDS=platform
```

She captures a project memory and shares it with the team:

```bash
memory-cli capture \
  --content "FastAPI project switched to Pydantic v2 syntax this sprint" \
  --type project \
  --scope "viking://tenants/default/teams/platform/memories/" \
  --visibility team
```

Or, granting an explicit named agent write access:

```bash
memory-cli capture \
  --content "Run integration tests with --no-cov locally" \
  --type preference \
  --share-with agent:reviewbot \
  --share-with team:platform
```

She can also share an existing memory after the fact:

```bash
memory-cli share mem_20260509T...  --to team:platform
memory-cli share mem_20260509T...  --to agent:reviewbot --permission write
```

### Agent B — Code review assistant

```bash
export OV_USER_ID=alice           # same human user
export OV_AGENT_ID=reviewbot      # different agent identity
export OV_TEAM_IDS=platform
```

When asked to review something:

```bash
memory-cli recall "FastAPI"
# (no relevant memories found)   ← own scope is empty by default

memory-cli recall "FastAPI" --include-subscribed
# [Relevant OpenViking Memory]
# - Project: FastAPI project switched to Pydantic v2 syntax this sprint (shared by user:alice)
# - Preference: Run integration tests with --no-cov locally (shared by user:alice)
# [/Relevant OpenViking Memory]
```

`memory-cli subscribed` lists the union of all memories shared TO
agent B's identity strings (its own `agent:reviewbot`, the human
`user:alice`, plus every `team:` it belongs to).

### Auto-include in production

Set this once globally in `~/.openviking-memory/config.json`:

```json
{
  "safety": {
    "auto_include_subscribed": true
  }
}
```

Now `memory-cli recall` defaults to including team scopes — review
agents see project context without needing the `--include-subscribed`
flag in every call.

## Common pitfalls

1. **Forgetting `OV_TEAM_IDS`.** Without it, `subscribed_scopes()` is
   empty and `recall --include-subscribed` returns the same as without
   it. The doctor doesn't fail on this (it's a valid config — agent
   has no team), so it's worth checking the env if subscriptions look
   surprisingly empty.
2. **`visibility=public` is read-only by default.** If you want
   public *and* writable by collaborators, list them in `shared_with`
   with `shared_perms[ident] = "write"`.
3. **Identity strings are case-sensitive.** `user:Alice` ≠ `user:alice`.
   The plugin doesn't normalise — if your team uses lowercase IDs, write
   `OV_USER_ID=alice` and stay consistent.
4. **`list_subscribed` is unsupported on HTTP/MCP today.** If you're
   on those backends, use `mem0` for cross-agent flows, or wait for
   Phase 4. The error message is intentional and points to the
   workaround.

## What's NOT included (yet)

- **RBAC / role grants** — flat `read` / `write` per (memory, identity)
  pair. Phase 5 may revisit if needed.
- **Audit logs** — who shared what, when. Out of Phase 3 scope; mem0
  records `updated_at` on the memory but doesn't keep grant history.
- **Server-side ACL on OpenViking** — Phase 4 deliverable.
- **Group-of-groups** (e.g. `team:platform` containing `team:backend`).
  Single-level teams only for now.

See `EVAL.md` §3 Phase 4 / 5 for the roadmap.
