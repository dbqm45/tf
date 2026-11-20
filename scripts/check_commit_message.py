#!/usr/bin/env python3
"""Checks a commit message or PR title against Conventional Commits (docs/RELEASING.md).

  python3 scripts/check_commit_message.py "feat(build): --only flag for selected personas"   # title
  python3 scripts/check_commit_message.py --file .git/COMMIT_EDITMSG                         # hook commit-msg
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conventional as cc  # noqa: E402


def main(argv: list[str]) -> int:
    if "--file" in argv:
        i = argv.index("--file")
        message = Path(argv[i + 1]).read_text(encoding="utf-8") if i + 1 < len(argv) else ""
    else:
        message = " ".join(argv)
    problems = cc.lint_message(message)
    if problems:
        print("✗ This is not a Conventional Commit:\n" + "\n".join(f"  - {p}" for p in problems), file=sys.stderr)
        print(f"\n  Format: <type>(<scope>)!: <description>   types: {', '.join(cc.TYPES)}", file=sys.stderr)
        print("  Example: feat(install): the --shared mode writes the team-factory workflow   (docs/RELEASING.md)",
              file=sys.stderr)
        return 1
    print("✓ Conventional Commit")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
