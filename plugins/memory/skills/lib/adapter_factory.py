"""
OpenViking Memory Skill Suite — Adapter factory.
Centralizes adapter creation so sub-skills never import a specific backend directly.

Usage:
    from lib.adapter_factory import get_adapter
    adapter = get_adapter(config)
    result = adapter.search("query")
    adapter.close()

To add a new backend:
    1. Create lib/xxx_adapter.py implementing MemoryAdapter
    2. Register it in _ADAPTER_REGISTRY below
    3. Set config backend to "xxx"
"""
from .config import Config

# ── Registry ────────────────────────────────────────────────

_ADAPTER_REGISTRY: dict[str, str] = {
    "openviking": "lib.http_adapter:HTTPAdapter",
    "openviking-mcp": "lib.mcp_adapter:MCPAdapter",
    "mem0": "lib.mem0_adapter:Mem0Adapter",
}

_DEFAULT_BACKEND = "openviking"


def _import_class(dotted_path: str):
    """Import a class from 'module.path:ClassName' format."""
    module_path, class_name = dotted_path.rsplit(":", 1)
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def get_adapter(config: Config, backend: str | None = None) -> object:
    """
    Create and return a memory adapter based on config.
    
    Args:
        config: Config instance
        backend: Override backend name (default: from config or "openviking")
    
    Returns:
        An object implementing the MemoryAdapter protocol.
    """
    backend = backend or config.get("backend", _DEFAULT_BACKEND)

    if backend not in _ADAPTER_REGISTRY:
        available = ", ".join(_ADAPTER_REGISTRY.keys())
        raise ValueError(
            f"Unknown backend '{backend}'. Available: {available}. "
            f"To add a new backend, create an adapter and register it in lib/adapter_factory.py"
        )

    dotted = _ADAPTER_REGISTRY[backend]
    cls = _import_class(dotted)

    # Build kwargs based on what the adapter class accepts
    import inspect
    sig = inspect.signature(cls.__init__)
    params = set(sig.parameters.keys()) - {"self"}
    kwargs = {}

    if "base_url" in params:
        kwargs["base_url"] = config.openviking_url
    if "api_key" in params:
        kwargs["api_key"] = config.api_key
    if "timeout" in params:
        kwargs["timeout"] = config.timeout
    if "server_name" in params:
        kwargs["server_name"] = config.get("mcp.server_name", "openviking")
    if "tool_names" in params:
        kwargs["tool_names"] = config.mcp_tool_names
    # mem0-specific: pass full mem0 config dict if available
    if "mem0_config" in params:
        mem0_cfg = dict(config.get("mem0", {}))
        # Inject resolved API key into the mem0 config
        if mem0_cfg and "api_key" not in mem0_cfg:
            resolved_key = config.mem0_api_key
            if resolved_key:
                mem0_cfg["api_key"] = resolved_key
        if mem0_cfg:
            kwargs["mem0_config"] = mem0_cfg
    # Also pass api_key for mem0 if no mem0_config (fallback)
    if "api_key" in params and backend == "mem0" and not kwargs.get("api_key"):
        kwargs["api_key"] = config.mem0_api_key

    return cls(**kwargs)


def list_backends() -> list[str]:
    """List all registered backend names."""
    return list(_ADAPTER_REGISTRY.keys())


def register_backend(name: str, dotted_path: str):
    """
    Register a new backend adapter at runtime.
    
    Args:
        name: Backend identifier (e.g. "mem0")
        dotted_path: "module.path:ClassName" (e.g. "lib.mem0_adapter:Mem0Adapter")
    """
    _ADAPTER_REGISTRY[name] = dotted_path
