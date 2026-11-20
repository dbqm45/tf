#!/usr/bin/env python3
"""SessionStart hook of the factory plugin (factory mode, docs/plans/2026-11-20-tryb-fabryki-plan.md): gives the factory
rules from .tf/plugin/RULES.md as the session's context. Registered only in .tf/plugin/hooks/hooks.json, so only a
factory session (tf code) gets the rules; a plain claude session in the project does not.
Without the file it prints nothing and exits 0."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")


def main() -> int:
    try:
        sys.stdin.read()
    except (OSError, ValueError):
        pass
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    try:
        rules = (root / ".tf" / "plugin" / "RULES.md").read_text(encoding="utf-8").strip()
    except OSError:
        return 0
    if rules:
        sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                            "additionalContext": rules}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
