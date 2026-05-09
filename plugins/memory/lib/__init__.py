"""memory plugin — core library."""
from .config import Config, ConfigError, load_config
from .client import OVClient
from .http_adapter import HTTPAdapter
from .mcp_adapter import MCPAdapter
from .mem0_adapter import Mem0Adapter
from .adapter_protocol import AdapterResponse, MemoryAdapter
from .adapter_factory import get_adapter, list_backends, register_backend
from .skill_loader import load_skill_module, load_subcommand_module
from .sharing import (
    SharingManager,
    parse_identity, is_identity_string, owner_from_scope,
)
from .policy import (
    should_recall, should_store, get_recall_types_order,
    get_default_recall_limit, RECALL_PRIORITY,
    get_store_worthy_indicators, get_skip_indicators,
    get_recall_triggers, get_min_content_length,
)
from .classifier import classify, classify_with_confidence
from .sensitive_detector import scan, has_sensitive, redact, classify_sensitivity
from .conflict_detector import detect_conflicts, format_conflicts
from .hooks import HookRegistry, HookEvent
from .formatter import (
    format_recall_block, format_doctor_report, format_commit_candidates,
    format_memory_list, format_memory_detail, format_stats,
)

__all__ = [
    "HookRegistry", "HookEvent",
    "Config", "ConfigError", "load_config",
    "OVClient", "HTTPAdapter", "MCPAdapter", "Mem0Adapter",
    "AdapterResponse", "MemoryAdapter",
    "get_adapter", "list_backends", "register_backend",
    "load_skill_module", "load_subcommand_module",
    "SharingManager", "parse_identity", "is_identity_string", "owner_from_scope",
    "should_recall", "should_store", "get_recall_types_order",
    "get_default_recall_limit", "RECALL_PRIORITY",
    "get_store_worthy_indicators", "get_skip_indicators",
    "get_recall_triggers", "get_min_content_length",
    "classify", "classify_with_confidence",
    "scan", "has_sensitive", "redact", "classify_sensitivity",
    "detect_conflicts", "format_conflicts",
    "format_recall_block", "format_doctor_report", "format_commit_candidates",
    "format_memory_list", "format_memory_detail", "format_stats",
]
