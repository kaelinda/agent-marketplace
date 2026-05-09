"""
memory-share skill — share / unshare / list-subscribed memory operations.

Thin wrapper over ``lib.sharing.SharingManager`` so the skill keeps the
same lifecycle (validation → adapter call → AdapterResponse) and the
CLI / slash command never duplicate validation logic.
"""
import os
import sys

# Plugin root is three levels up: skills/<skill>/scripts/<file>.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from lib.adapter_factory import get_adapter
from lib.config import Config
from lib.sharing import SharingManager


def _build_manager(config: Config):
    """Construct ``(adapter, SharingManager)`` for a single op.

    Caller is responsible for closing the adapter via ``adapter.close()``
    when done.
    """
    adapter = get_adapter(config)
    return adapter, SharingManager(adapter, config)


def run_share(config: Config, memory_id: str, target: str,
              permission: str = "read") -> dict:
    """Grant ``target`` ``permission`` on ``memory_id``."""
    if not memory_id:
        return {"ok": False, "error": "memory_id is required"}
    if not target:
        return {"ok": False, "error": "target is required"}
    adapter, sharing = _build_manager(config)
    try:
        return sharing.share(memory_id, target, permission)
    finally:
        adapter.close()


def run_unshare(config: Config, memory_id: str, target: str) -> dict:
    """Revoke ``target``'s access to ``memory_id``."""
    if not memory_id:
        return {"ok": False, "error": "memory_id is required"}
    if not target:
        return {"ok": False, "error": "target is required"}
    adapter, sharing = _build_manager(config)
    try:
        return sharing.unshare(memory_id, target)
    finally:
        adapter.close()


def run_list_subscribed(config: Config) -> dict:
    """List memories shared TO any of the caller's identity strings."""
    adapter, sharing = _build_manager(config)
    try:
        return sharing.list_my_subscriptions()
    finally:
        adapter.close()
