#!/usr/bin/env python3
"""
PostToolUse (Edit|Write): scans the written file for secrets.
Exit 2 → the message goes to Claude, who must remove the secret before proceeding.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record_block  # block to .tf/logs/hook-blocks.jsonl (warning after an update)
except ImportError:  # older install without the block log — the hook works as before
    def record_block(hook: str, decision: str) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RULES = [
    ("AWS access key", r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("klucz prywatny", r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    ("GitHub token", r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
    ("Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    ("Anthropic API key", r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    ("OpenAI-style API key", r"\bsk-(proj-)?[A-Za-z0-9]{32,}\b"),
    ("Google API key", r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ("Stripe live key", r"\b(sk|rk)_live_[0-9a-zA-Z]{20,}\b"),
    ("JWT", r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    ("password/secret in code",
     r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|client[_-]?secret)\b\s*[:=]\s*['\"]([^'\"\s]{12,})['\"]"),
]
PLACEHOLDER = re.compile(r"(?i)(example|changeme|change_me|placeholder|your[_-]|xxx|dummy|test|fake|<|\$\{|process\.env|os\.environ)")
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".lock"}


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    path = (data.get("tool_input") or {}).get("file_path", "")
    p = Path(path)
    if not path or not p.is_file() or p.suffix.lower() in SKIP_EXT or p.stat().st_size > 2_000_000:
        sys.exit(0)
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        sys.exit(0)

    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for label, rx in RULES:
            m = re.search(rx, line)
            if m and not PLACEHOLDER.search(m.group(0)):
                findings.append(f"  {path}:{lineno}: {label}")
    if findings:
        print("[scan_secrets] Likely secrets were found in the saved file:\n" + "\n".join(findings[:10]) +
              "\nRemove them and read the value from an environment variable. If it is a real secret, "
              "tell the user that it must be rotated.", file=sys.stderr)
        record_block("scan_secrets", "deny")
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
