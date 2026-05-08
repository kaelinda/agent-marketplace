"""
OpenViking Memory Skill Suite — Sensitive data detector.
Scans content for secrets, PII, and other sensitive patterns before storage.
"""
import re
from typing import NamedTuple


class SensitiveMatch(NamedTuple):
    pattern_name: str
    matched_text: str
    start: int
    end: int


# ── Patterns ────────────────────────────────────────────────
_PATTERNS = [
    ("api_key", re.compile(r'(?i)(api[_-]?key|apikey|openai[_-]?api[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})')),
    ("bearer_token", re.compile(r'(?i)(bearer|token|access[_-]?token|refresh[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_\.\-]{20,})')),
    ("sk_key", re.compile(r'(?i)(sk|pk|rk)[_-][a-zA-Z0-9]{20,}')),
    ("jwt", re.compile(r'(?i)(jwt)\s*[:=]\s*["\']?([a-zA-Z0-9_\.\-]{40,})')),
    ("password", re.compile(r'(?i)(password|passwd|pwd|db[_-]?password|database[_-]?password|secret[_-]?key)\s*[:=]\s*["\']?(\S{6,})')),
    ("ssh_private_key", re.compile(r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----')),
    ("ssh_rsa_pub", re.compile(r'(?i)ssh[_-]rsa\s+[a-zA-Z0-9+/=]{40,}')),
    ("cookie", re.compile(r'(?i)(cookie|set[_-]?cookie)\s*[:=]\s*["\']?(\S{10,})')),
    ("chinese_id", re.compile(r'(?<!\d)\d{17}[\dXx](?!\d)')),
    ("connection_string", re.compile(r'(?i)(mysql|postgres|mongodb|redis):\/\/\S+')),
]


def scan(content: str) -> list[SensitiveMatch]:
    """Scan content for sensitive data patterns. Returns list of matches."""
    matches = []
    for name, pattern in _PATTERNS:
        for m in pattern.finditer(content):
            matches.append(SensitiveMatch(
                pattern_name=name,
                matched_text=m.group()[:60] + ("..." if len(m.group()) > 60 else ""),
                start=m.start(),
                end=m.end(),
            ))
    return matches


def has_sensitive(content: str) -> bool:
    """Quick check: does content contain sensitive data?"""
    return len(scan(content)) > 0


_REDACT_MAP = {
    "api_key": "[REDACTED_API_KEY]",
    "bearer_token": "[REDACTED_TOKEN]",
    "sk_key": "[REDACTED_KEY]",
    "jwt": "[REDACTED_JWT]",
    "password": "[REDACTED_PASSWORD]",
    "ssh_private_key": "[REDACTED_PRIVATE_KEY]",
    "ssh_rsa_pub": "[REDACTED_SSH_KEY]",
    "cookie": "[REDACTED_COOKIE]",
    "chinese_id": "[REDACTED_ID]",
    "connection_string": "[REDACTED_CONNECTION_STRING]",
}


def redact(content: str) -> str:
    """Replace sensitive data with redaction markers."""
    result = content
    for name, pattern in _PATTERNS:
        replacement = _REDACT_MAP.get(name, "[REDACTED]")
        result = pattern.sub(replacement, result)
    return result


def classify_sensitivity(content: str) -> str:
    """
    Return sensitivity level:
    - "safe": no sensitive data detected
    - "warn": borderline (e.g. IP addresses, URLs with ports)
    - "block": definitely contains secrets or PII
    """
    matches = scan(content)
    if not matches:
        return "safe"
    # Any secret/PII = block
    hard_block = {"api_key", "bearer_token", "sk_key", "jwt", "password",
                  "ssh_private_key", "ssh_rsa_pub", "cookie", "chinese_id",
                  "connection_string"}
    for m in matches:
        if m.pattern_name in hard_block:
            return "block"
    return "warn"
