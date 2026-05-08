"""
OpenViking Memory Skill Suite — Memory classifier.
Auto-classifies content into memory types (project, environment, case, preference, etc.).

Supports:
  - Built-in bilingual regex rules (default)
  - Extra rules via config (classifier.extra_rules)
  - External plugin classifier via config (classifier.plugin = "module.path:function_name")
"""
import importlib
import re
from typing import Optional

# ── Built-in classification rules ──────────────────────────

_BUILTIN_RULES: dict[str, list[str]] = {
    "preference": [
        r"(?i)\b(prefer|喜欢|偏好|习惯|风格)\b",
        r"(?i)\b(always|never|usually|默认|default)\b.*\b(use|用|给|写)\b",
        r"(?i)\b(language|语言|回答|answer|style)\b",
        r"(?i)以后.*?(回答|给|用|写)",
        r"(?i)prefer.*?(chinese|english|中文|完整|简洁)",
    ],
    "environment": [
        r"(?i)\b(nginx|apache|docker|k8s|kubernetes|centos|ubuntu|debian|alpine)\b",
        r"(?i)\b(node|python|java|jdk|go|rust|swift|xcode)\b.*\b(version|版本|v\d)\b",
        r"(?i)\b(server|服务器|ecs|vps|域名|domain|端口|port|路径|path)\b",
        r"(?i)\b(install|部署|deploy|compose|pm2|systemd)\b",
        r"(?i)\b(macOS|windows|linux|arm64|x86_64)\b",
        r"(?i)(Nginx|配置|路径|位于|located)",
    ],
    "project": [
        r"(?i)\b(project|项目|工程|repo|仓库)\b",
        r"(?i)\b(正在开发|working on|building|developing|设计)\b",
        r"(?i)\b(feature|功能|模块|module|架构|architecture)\b",
        r"(?i)\b(milestone|roadmap|backlog|sprint)\b",
    ],
    "case": [
        r"(?i)\b(bug|error|issue|problem|问题|故障|报错|异常)\b",
        r"(?i)\b(502|503|500|404|403|401|timeout|ECONNREFUSED)\b",
        r"(?i)\b(fix|solve|repair|修复|解决|排查|troubleshoot)\b",
        r"(?i)\b(root\s*cause|根因|原因|solution|解决方案)\b",
    ],
    "decision": [
        r"(?i)\b(decide|decision|决定|决策|选择|choose)\b",
        r"(?i)\b(approve|confirm|确认|同意|采纳)\b",
        r"(?i)\b(方案|plan|approach|strategy)\b",
        r"(?i)(最终|结论|conclusion|确定)",
    ],
    "agent_reflection": [
        r"(?i)\b(learned|lesson|经验|教训|pattern|模式)\b",
        r"(?i)\b(when.*遇到|遇到.*先|first\s*check|先检查)\b",
        r"(?i)\b(next\s*time|下次|以后遇到)\b",
    ],
    "profile": [
        r"(?i)\b(name|名字|age|年龄|role|角色|职业|developer|开发者)\b",
        r"(?i)\b(我是|I am|I'm)\b",
    ],
}

# Plugin cache
_plugin_fn = None
_plugin_loaded = False


def _load_plugin(plugin_path: str):
    """Load a classifier plugin: 'module.path:function_name' -> callable(text) -> (type, confidence)."""
    global _plugin_fn, _plugin_loaded
    if _plugin_loaded:
        return _plugin_fn
    _plugin_loaded = True
    if not plugin_path:
        _plugin_fn = None
        return None
    try:
        module_path, fn_name = plugin_path.rsplit(":", 1)
        mod = importlib.import_module(module_path)
        _plugin_fn = getattr(mod, fn_name)
        return _plugin_fn
    except Exception as e:
        import sys
        print(f"[classifier] WARNING: failed to load plugin '{plugin_path}': {e}", file=sys.stderr)
        _plugin_fn = None
        return None


def _get_rules(classifier_config: dict = None) -> dict[str, list[str]]:
    """Merge built-in rules with extra rules from config."""
    cfg = classifier_config or {}
    rules: dict[str, list[str]] = {}
    if cfg.get("builtin_rules", True):
        rules.update({k: list(v) for k, v in _BUILTIN_RULES.items()})
    extra = cfg.get("extra_rules", {})
    for mem_type, patterns in extra.items():
        if mem_type in rules:
            rules[mem_type].extend(patterns)
        else:
            rules[mem_type] = list(patterns)
    return rules


def classify(content: str, context: str = "",
             classifier_config: dict = None) -> str:
    """
    Classify memory content into a type.
    Returns one of: preference, environment, project, case, decision, agent_reflection, profile.
    Defaults to the configured default_type (default: 'project') if ambiguous.
    """
    return classify_with_confidence(content, context, classifier_config)[0]


def classify_with_confidence(content: str, context: str = "",
                             classifier_config: dict = None) -> tuple[str, float]:
    """
    Classify and return (type, confidence) where confidence is 0.0-1.0.

    Priority:
      1. External plugin (if configured)
      2. Regex rules (built-in + extra_rules)
    """
    cfg = classifier_config or {}
    default_type = cfg.get("default_type", "project")
    text = f"{context} {content}".strip()

    # 1. Try plugin first
    plugin_path = cfg.get("plugin", "")
    if plugin_path:
        fn = _load_plugin(plugin_path)
        if fn:
            try:
                result = fn(text)
                if result and isinstance(result, (tuple, list)) and len(result) == 2:
                    return (str(result[0]), float(result[1]))
            except Exception as e:
                import sys
                print(f"[classifier] WARNING: plugin error: {e}", file=sys.stderr)

    # 2. Regex-based classification
    rules = _get_rules(cfg)
    scores: dict[str, int] = {}
    for mem_type, patterns in rules.items():
        score = 0
        for pat in patterns:
            if re.search(pat, text):
                score += 1
        if score > 0:
            scores[mem_type] = score

    if not scores:
        return (default_type, 0.3)

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    matched_patterns = rules.get(best_type, [])
    confidence = min(1.0, best_score / max(len(matched_patterns) * 0.5, 1))
    confidence = max(0.4, confidence)  # floor at 0.4 if any match
    return (best_type, round(confidence, 2))
