"""
Pytest configuration for the memory plugin.

Adds the plugin root to ``sys.path`` so tests can ``from lib import ...``
without installing anything.
"""
import os
import sys

_PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)
