#!/usr/bin/env python3
"""
Did the factory hooks run on the latest commits — compares hook traces in .tf/logs with the git history.

  python3 .tf/factory/hooks_status.py              # one line: active / inactive / no hooks
  python3 .tf/factory/hooks_status.py --json       # {"active": true|false|null, "last_log", "after_commits", "first_after"}
  --root <repozytorium>

Hook traces: `ts` entries in .tf/logs/skill-hints.jsonl (every command) and usage.jsonl (end of session). A commit
made more than an hour after the last trace has no coverage in the logs; from two such commits the hooks are treated as inactive
(one is usually the current session before it is saved). Typical cause: a cloud session with several repositories or a session
started from a parent directory — the hooks from .claude/settings.json are not loaded, so tdd_guard,
path protection and cost logs do not work. The result is information (exit code 0), not an error. Standard library only.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ("skill-hints.jsonl", "usage.jsonl")
GRACE = dt.timedelta(hours=1)
MIN_COMMITS = 2


def ts(text: str) -> dt.datetime | None:
    try:
        t = dt.datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def has_hooks(root: Path) -> bool:
    try:
        return bool(json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8")).get("hooks"))
    except (OSError, ValueError, AttributeError):
        return False


def last_log(root: Path) -> dt.datetime | None:
    last = None
    for name in LOGS:
        f = root / ".tf" / "logs" / name
        if not f.is_file():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                t = ts(json.loads(line).get("ts", ""))
            except (ValueError, AttributeError):
                continue
            if t and (last is None or t > last):
                last = t
    return last


def commit_times(root: Path) -> list[dt.datetime]:
    r = subprocess.run(["git", "-C", str(root), "log", "--format=%cI"], capture_output=True, text=True)
    return [t for t in (ts(x) for x in r.stdout.split()) if t] if r.returncode == 0 else []


def status(root: Path) -> dict:
    if os.environ.get("CI") or not has_hooks(root):   # there is no Claude Code session in CI, so there is nothing to check
        return {"active": None, "last_log": None, "after_commits": 0, "first_after": None}
    last = last_log(root)
    after = sorted(t for t in commit_times(root) if last is None or t > last + GRACE)
    return {"active": len(after) < MIN_COMMITS, "last_log": last.isoformat() if last else None,
            "after_commits": len(after), "first_after": after[0].isoformat() if after else None}


def line(s: dict) -> str:
    if s["active"] is None:
        return "· factory hooks: no hooks in .claude/settings.json, or CI. Nothing to check"
    if s["active"]:
        return "✓ factory hooks: active (traces in .tf/logs cover the recent commits)"
    since = f"after the last hook trace ({s['last_log'][:16]})" if s["last_log"] else "with no hook trace in .tf/logs"
    return (f"⚠ factory hooks are probably not active: {s['after_commits']} commits {since}. tdd_guard, path "
            "protection and cost logs do not work. Run the tests and gates by hand. Start the next cloud session "
            "with one repository (README: Cloud session).")


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv[1:])
    for a in it:
        if a == "--root":
            opts[a] = next(it, "")
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    s = status(Path(opts.get("--root") or ROOT).resolve())
    print(json.dumps(s, ensure_ascii=False) if opts.get("--json") else line(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
