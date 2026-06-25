"""
memory plugin — SharingManager (Phase 3).

The SharingManager is the high-level façade between user-facing skills /
CLI subcommands and the per-adapter share / unshare / list_subscribed
primitives. It centralises:

- **Identity resolution** — what does "the current caller" actually
  mean? It's a tuple of identity strings (user / agent / team[]) that
  every ACL evaluation can be tested against.
- **ACL evaluation** — given a memory dict and an op, can the current
  identity perform that op? Pure-function, runs locally, doesn't talk
  to the backend.
- **Subscription aggregation** — calling ``list_subscribed`` once per
  identity string and merging results, so callers don't have to
  re-implement that loop.
- **share / unshare** delegation — thin pass-through to the adapter,
  but with target validation so a typo'd identity string never reaches
  the backend.

The four design decisions worth knowing:

1. **No RBAC, no roles.** Permissions are flat ``read`` / ``write``
   per (memory, identity) pair. Phase 5 may revisit if real teams need
   group-level grants beyond ``team:X``.
2. **Owner is implicit by scope.** A memory's writer is the entity
   whose scope it lives in. ``owner_id`` on the memory dict is for
   audit / display only; ``can_access`` derives ownership from the
   scope URI when the field is missing, so legacy memories from
   Phase 2 still work.
3. **Default visibility is ``private``.** Anything written through
   capture in Phase 2 has no visibility field → treated as private →
   only the owner (own scope) can read.
4. **Team subscription is automatic.** Belonging to ``team:platform``
   = subscribed to ``viking://.../teams/platform/...`` scope. No
   explicit "join team" call.
"""
from __future__ import annotations

import re
from typing import Iterable, Iterator, Optional

from .config import Config


_VALID_PERMS = ("read", "write")
_IDENTITY_RE = re.compile(r"^(?P<kind>user|agent|team):(?P<id>.+)$")
# Scope marker → entity kind (for parsing scopes that came back from
# adapters that don't echo owner_id, e.g. legacy Phase 2 memories).
_SCOPE_OWNER_RE = re.compile(
    r"/(?P<kind>users|agents|teams)/(?P<id>[^/]+)/"
)


def parse_identity(identity: str) -> Optional[tuple[str, str]]:
    """Parse ``"<kind>:<id>"`` into ``(kind, id)`` tuple, or None if invalid.

    ``kind`` is one of ``user`` / ``agent`` / ``team``.
    """
    if not isinstance(identity, str):
        return None
    m = _IDENTITY_RE.match(identity)
    if not m:
        return None
    return (m.group("kind"), m.group("id"))


def is_identity_string(s: str) -> bool:
    """``True`` iff ``s`` matches the identity-string contract."""
    return parse_identity(s) is not None


def owner_from_scope(scope: str) -> Optional[str]:
    """Extract an identity string from a scope URI, e.g.

    ``"viking://tenants/default/users/alice/memories/"`` →
    ``"user:alice"``.

    Returns None if the scope doesn't match the expected layout
    (e.g. system or doctor scope).
    """
    if not scope:
        return None
    m = _SCOPE_OWNER_RE.search(scope)
    if not m:
        return None
    kind_plural = m.group("kind")
    kind = {"users": "user", "agents": "agent", "teams": "team"}.get(kind_plural)
    if not kind:
        return None
    return f"{kind}:{m.group('id')}"


class SharingManager:
    """Façade for cross-agent memory sharing.

    Construct one per-adapter-per-config; reusable across calls.
    """

    def __init__(self, adapter, config: Config):
        self.adapter = adapter
        self.config = config

    # ── Identity helpers ────────────────────────────────────

    def my_identity_strings(self) -> list[str]:
        """All identity strings this caller speaks for.

        Thin wrapper over ``Config.my_identity_strings()`` so callers
        only need a SharingManager handle.
        """
        return self.config.my_identity_strings()

    # ── Pass-through with validation ────────────────────────

    def share(self, memory_id: str, target: str,
              permission: str = "read") -> dict:
        """Validate inputs then delegate to ``adapter.share``.

        The adapter could do this validation itself, but doing it here
        means a typo'd identity string never burns a backend round-trip.
        """
        if permission not in _VALID_PERMS:
            return _err(
                f"invalid permission {permission!r}; expected one of {_VALID_PERMS}"
            )
        if not is_identity_string(target):
            return _err(
                f"invalid target {target!r}; must match '<kind>:<id>' "
                f"with kind in user|agent|team"
            )
        return self.adapter.share(memory_id, target, permission)

    def unshare(self, memory_id: str, target: str) -> dict:
        if not is_identity_string(target):
            return _err(
                f"invalid target {target!r}; must match '<kind>:<id>'"
            )
        return self.adapter.unshare(memory_id, target)

    # ── Subscription aggregation ────────────────────────────

    def list_my_subscriptions(self) -> dict:
        """Aggregate ``list_subscribed`` across every identity string
        the caller speaks for.

        Returns:
            Dict with shape ``{ok, data: [memory dicts], meta}``.
            Per-identity errors are collected into ``meta.errors``;
            an outer ok=False is returned only if EVERY identity errored.
        """
        identities = self.my_identity_strings()
        memories: list[dict] = []
        seen_ids: set[str] = set()
        errors: list[dict] = []
        successes = 0
        for identity in identities:
            r = self.adapter.list_subscribed(identity)
            if r.get("ok"):
                successes += 1
                data = r.get("data") or []
                if isinstance(data, list):
                    for m in data:
                        if not isinstance(m, dict):
                            continue
                        mid = m.get("id", "")
                        if mid and mid not in seen_ids:
                            seen_ids.add(mid)
                            memories.append(m)
            else:
                errors.append({"identity": identity, "error": r.get("error", "unknown")})
        meta = {"checked": identities}
        if errors:
            meta["errors"] = errors
        if successes == 0 and errors:
            return _err(
                "list_subscribed failed on every identity; backend may not "
                "support cross-agent subscription discovery",
                meta=meta,
            )
        return _ok(memories, meta=meta)

    def subscribed_scopes(self) -> list[str]:
        """Scope URIs the caller is subscribed to via team membership.

        Used as ``extra_scopes`` for ``adapter.search``. This is a
        cheap, fully-local computation — it does not hit the adapter.
        """
        return list(self.config.team_scopes)

    # ── ACL evaluation ──────────────────────────────────────

    def owner_of(self, memory: dict) -> Optional[str]:
        """Best-effort owner identity for a memory.

        Uses ``memory["owner_id"]`` if set; otherwise falls back to
        parsing the scope URI. Returns None if neither is available.
        """
        owner = memory.get("owner_id")
        if isinstance(owner, str) and is_identity_string(owner):
            return owner
        return owner_from_scope(memory.get("scope") or "")

    def can_access(self, memory: dict, op: str = "read") -> bool:
        """Pure ACL judgement for ``memory`` from the caller's POV.

        Order of evaluation (first match wins):

        1. **Owner** — caller speaks for the memory's owner identity.
        2. **Visibility public** — anyone in the same tenant can read.
           Public memories cannot be written without an explicit grant.
        3. **Visibility team** — caller belongs to a team referenced in
           the scope (i.e. the memory lives in the team's scope).
        4. **shared_with** — caller's identity (or any of their team
           identities) appears in shared_with, with ``shared_perms``
           covering ``op``. Default permission is ``read``.
        5. Otherwise → False.
        """
        if op not in _VALID_PERMS:
            return False
        my_ids = set(self.my_identity_strings())

        # 1. Ownership
        owner = self.owner_of(memory)
        if owner and owner in my_ids:
            return True

        visibility = memory.get("visibility") or "private"

        # 2. Public — read-only by default
        if visibility == "public" and op == "read":
            return True

        # 3. Team scope membership
        if visibility == "team":
            scope_owner = owner_from_scope(memory.get("scope") or "")
            if scope_owner and scope_owner in my_ids and op == "read":
                return True

        # 4. Explicit grants
        shared_with = memory.get("shared_with") or []
        if not isinstance(shared_with, list):
            shared_with = []
        shared_perms = memory.get("shared_perms") or {}
        if not isinstance(shared_perms, dict):
            shared_perms = {}

        for ident in shared_with:
            if ident not in my_ids:
                continue
            granted = shared_perms.get(ident, "read")
            if op == "read":
                # Either read or write grants imply read access.
                return True
            if op == "write" and granted == "write":
                return True

        return False

    def visible_memories(self, memories: Iterable[dict],
                         op: str = "read") -> Iterator[dict]:
        """Filter an iterable of memory dicts to the ones the caller
        can perform ``op`` on. Generator, no allocation if you don't
        materialise the result."""
        for m in memories:
            if isinstance(m, dict) and self.can_access(m, op):
                yield m


# ── Internal helpers — minimal stand-ins so SharingManager doesn't
#    need to import AdapterResponse for trivial cases ─────────────


def _ok(data, meta: dict | None = None) -> dict:
    out = {"ok": True, "data": data}
    if meta:
        out["meta"] = meta
    return out


def _err(error: str, meta: dict | None = None) -> dict:
    out = {"ok": False, "error": error}
    if meta:
        out["meta"] = meta
    return out
