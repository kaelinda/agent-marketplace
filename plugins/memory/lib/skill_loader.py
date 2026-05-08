"""
Dynamic skill / subcommand loader.

Skill directories use kebab-case (e.g. ``memory-capture``) which is not a
valid Python identifier, so we cannot ``import skills.memory-capture...``.
This helper loads scripts by absolute file path instead, the same way the
CLI loads sub-skill modules.

Layout assumed:
    <plugin_root>/lib/skill_loader.py        (this file)
    <plugin_root>/skills/<skill-name>/scripts/<module>.py
    <plugin_root>/scripts/subcommands/<module>.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType


def _plugin_root() -> str:
    """Return the absolute path of the plugin root (parent of lib/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_skill_module(skill_dir: str, module_name: str) -> ModuleType:
    """
    Load a sub-skill module living at
    ``<plugin_root>/skills/<skill_dir>/scripts/<module_name>.py``.

    Cached in ``sys.modules`` under a synthetic key so multiple callers
    share the same instance.
    """
    module_path = os.path.join(
        _plugin_root(), "skills", skill_dir, "scripts", f"{module_name}.py"
    )
    return _load_path(f"_memory_skill.{skill_dir}.{module_name}", module_path)


def load_subcommand_module(module_name: str) -> ModuleType:
    """
    Load a CLI subcommand module living at
    ``<plugin_root>/scripts/subcommands/<module_name>.py``.
    """
    module_path = os.path.join(
        _plugin_root(), "scripts", "subcommands", f"{module_name}.py"
    )
    return _load_path(f"_memory_subcommand.{module_name}", module_path)


def _load_path(cache_key: str, module_path: str) -> ModuleType:
    if cache_key in sys.modules:
        return sys.modules[cache_key]
    if not os.path.isfile(module_path):
        raise FileNotFoundError(f"Module file not found: {module_path}")
    spec = importlib.util.spec_from_file_location(cache_key, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create import spec for {module_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[cache_key] = mod
    spec.loader.exec_module(mod)
    return mod
