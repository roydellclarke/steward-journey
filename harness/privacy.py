"""PII and secret hygiene helpers."""

from __future__ import annotations

from pathlib import Path
import re


DEFAULT_SENSITIVE_PATTERNS = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*secret*",
    "*token*",
    "workspace/screenshots/*",
    "workspace/state/cost_log.json",
]

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\d)")
API_KEY_RE = re.compile(r"\b(?:sk|pk|ghp|gho|github_pat|ya29|xoxb|xoxp)[-_A-Za-z0-9]{12,}\b")
BEARER_RE = re.compile(r"\bBearer\s+[-._~+/A-Za-z0-9]+=*", re.IGNORECASE)


def redact_text(text: str) -> str:
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    redacted = API_KEY_RE.sub("[REDACTED_SECRET]", redacted)
    redacted = BEARER_RE.sub("Bearer [REDACTED_SECRET]", redacted)
    return redacted


def load_ignore_patterns(root: Path, filenames: tuple[str, ...] = (".piiignore", ".secretignore")) -> list[str]:
    patterns: list[str] = []
    for filename in filenames:
        path = root / filename
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def is_sensitive_path(path: str | Path, root: Path | None = None) -> bool:
    candidate = Path(path)
    text = str(candidate)
    if root is not None:
        try:
            text = str(candidate.resolve().relative_to(root.resolve()))
        except (ValueError, OSError):
            text = str(candidate)
    patterns = [*DEFAULT_SENSITIVE_PATTERNS]
    if root is not None:
        patterns.extend(load_ignore_patterns(root))
    return any(candidate.match(pattern) or Path(text).match(pattern) or pattern in text for pattern in patterns)
