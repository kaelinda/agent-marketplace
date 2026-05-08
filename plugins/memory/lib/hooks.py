"""
OpenViking Memory Skill Suite — Hook / middleware system.
Provides event hooks that allow custom logic to be injected into
the memory lifecycle without modifying core code.

Usage:
    from lib.hooks import HookRegistry, HookEvent

    registry = HookRegistry()
    registry.register(HookEvent.BEFORE_STORE, my_before_store_fn)
    registry.register(HookEvent.AFTER_RECALL, my_after_recall_fn)

    # In your workflow:
    ctx = {"content": "...", "memory_type": "project", "config": config}
    ctx = registry.trigger(HookEvent.BEFORE_STORE, ctx)
    if ctx.get("blocked"):
        ...
    else:
        store(ctx["content"])
        registry.trigger(HookEvent.AFTER_STORE, ctx)

Plugins:
    Register hooks via config (hooks.plugins) as a list of
    "module.path:function_name" strings. They will be auto-loaded
    on first HookRegistry instantiation.
"""
from __future__ import annotations

import importlib
import sys
from enum import Enum
from typing import Any, Callable


class HookEvent(str, Enum):
    """Lifecycle events that can be hooked."""
    BEFORE_STORE = "before_store"
    AFTER_STORE = "after_store"
    BEFORE_RECALL = "before_recall"
    AFTER_RECALL = "after_recall"
    ON_CONFLICT = "on_conflict"   # triggered by callers when conflict_detect_hook finds conflicts
    ON_ERROR = "on_error"         # triggered by HookRegistry.trigger() on hook exceptions
    BEFORE_MERGE = "before_merge"
    AFTER_MERGE = "after_merge"
    BEFORE_FORGET = "before_forget"
    AFTER_FORGET = "after_forget"


# Type: a hook function receives a context dict, returns the (possibly modified) dict.
HookFn = Callable[[dict], dict]


class HookRegistry:
    """
    Manages lifecycle hooks. Hooks are ordered (FIFO per event).

    Each hook receives a context dict and returns a modified context dict.
    Returning {"blocked": True, "reason": "..."} from BEFORE_* hooks
    prevents the action from proceeding.
    """

    def __init__(self, config: dict | None = None):
        self._hooks: dict[HookEvent, list[HookFn]] = {e: [] for e in HookEvent}
        self._loaded_plugins = False
        if config:
            self._load_plugins(config)

    def _load_plugins(self, config: dict):
        """Auto-load hook plugins declared in config."""
        if self._loaded_plugins:
            return
        self._loaded_plugins = True
        plugins = config.get("hooks", {}).get("plugins", [])
        for entry in plugins:
            if isinstance(entry, dict):
                event_name = entry.get("event", "")
                plugin_path = entry.get("plugin", "")
            elif isinstance(entry, str):
                # shorthand: "module.path:function_name" → registers for all events
                event_name = ""
                plugin_path = entry
            else:
                continue
            self._load_single_plugin(plugin_path, event_name)

    def _load_single_plugin(self, plugin_path: str, event_name: str = ""):
        """Load a single hook plugin: 'module.path:function_name'."""
        if not plugin_path:
            return
        try:
            module_path, fn_name = plugin_path.rsplit(":", 1)
            mod = importlib.import_module(module_path)
            fn = getattr(mod, fn_name)
            if event_name:
                event = HookEvent(event_name)
                self.register(event, fn)
            else:
                # Register for all events
                for event in HookEvent:
                    self.register(event, fn)
        except Exception as e:
            print(f"[hooks] WARNING: failed to load plugin '{plugin_path}': {e}", file=sys.stderr)

    def register(self, event: HookEvent, fn: HookFn):
        """Register a hook function for a specific event."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(fn)

    def unregister(self, event: HookEvent, fn: HookFn):
        """Remove a registered hook."""
        if event in self._hooks and fn in self._hooks[event]:
            self._hooks[event].remove(fn)

    def trigger(self, event: HookEvent, context: dict) -> dict:
        """
        Trigger all hooks for an event. Returns the final context dict.

        Each hook receives the context and must return a dict.
        If any hook returns {"blocked": True}, the chain short-circuits.
        """
        ctx = dict(context)  # shallow copy to avoid mutation
        for fn in self._hooks.get(event, []):
            try:
                result = fn(ctx)
                if isinstance(result, dict):
                    ctx = result
                # If hook signals blocking, stop chain
                if ctx.get("blocked"):
                    break
            except Exception as e:
                ctx["hook_error"] = str(e)
                print(f"[hooks] WARNING: hook {fn.__name__} raised: {e}", file=sys.stderr)
                # Trigger ON_ERROR hooks (with recursion guard)
                if event != HookEvent.ON_ERROR:
                    ctx = self.trigger(HookEvent.ON_ERROR, {
                        "original_event": event.value,
                        "hook_name": getattr(fn, "__name__", "?"),
                        "error": str(e),
                        **ctx,
                    })
        return ctx

    def has_hooks(self, event: HookEvent) -> bool:
        """Check if any hooks are registered for an event."""
        return bool(self._hooks.get(event))


# ── Built-in hooks ─────────────────────────────────────────


def dedupe_hook(ctx: dict) -> dict:
    """
    BEFORE_STORE hook: checks for duplicate content in recent memories.
    Requires ctx["adapter"] and ctx["content"] to be set.

    If a near-duplicate is found, sets ctx["blocked"] = True and
    ctx["reason"] with the existing memory ID.
    """
    adapter = ctx.get("adapter")
    content = ctx.get("content", "")
    if not adapter or not content:
        return ctx

    try:
        result = adapter.search(query=content[:100], limit=3, min_score=0.9)
        memories = result.get("data", result.get("memories", []))
        if isinstance(memories, list):
            for m in memories:
                if m.get("content", "")[:200] == content[:200]:
                    ctx["blocked"] = True
                    ctx["reason"] = f"Duplicate of memory {m.get('id', '?')}"
                    return ctx
    except Exception:
        pass  # Don't block on dedupe failure
    return ctx


def conflict_detect_hook(ctx: dict) -> dict:
    """
    AFTER_RECALL hook: runs conflict detection on recalled memories.
    Populates ctx["conflicts"] if conflicting memories are found.
    """
    from .conflict_detector import detect_conflicts
    memories = ctx.get("memories", [])
    if len(memories) >= 2:
        conflicts = detect_conflicts(memories)
        if conflicts:
            ctx["conflicts"] = conflicts
    return ctx


def sensitive_block_hook(ctx: dict) -> dict:
    """
    BEFORE_STORE hook: blocks storage of sensitive content.
    Requires ctx["content"] and ctx["config"].
    """
    from .sensitive_detector import classify_sensitivity
    content = ctx.get("content", "")
    config = ctx.get("config")
    if not content:
        return ctx

    sensitivity = classify_sensitivity(content)
    if sensitivity == "block" and config and config.deny_sensitive:
        from .sensitive_detector import has_sensitive, redact
        redacted = redact(content)
        if has_sensitive(redacted):
            ctx["blocked"] = True
            ctx["reason"] = "Content contains sensitive data and cannot be stored."
        else:
            ctx["content"] = redacted
            ctx["redacted"] = True
    return ctx


# ── Convenience: default registry ──────────────────────────

_default_registry: HookRegistry | None = None


def get_default_registry(config: dict | None = None) -> HookRegistry:
    """Get or create the global default hook registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = HookRegistry(config)
    return _default_registry


def reset_default_registry():
    """Reset the global default registry (useful for testing)."""
    global _default_registry
    _default_registry = None
