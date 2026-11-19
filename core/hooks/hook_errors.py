#!/usr/bin/env python3
"""
Hook error log: a hook does not interrupt the session on its own error, but the error is recorded.

  from hook_errors import record      # in a hook: except Exception as e: record("nazwa_hooka", e)
  python3 .claude/hooks/hook_errors.py --summary [--days 7]   # summary (called by `tf doctor`)

An entry in `<project>/.tf/logs/hook-errors.jsonl`: time, hook, exception type, location (file:line of the deepest frame),
message truncated to 200 characters. No hook input content (it may contain code and data). The log has at most
MAX_BYTES — after exceeding it the newer half is kept. `record` never raises: the log is meant to help, not to
add failures. Standard library only.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

MAX_BYTES = 256_000
LOG = Path(".tf") / "logs" / "hook-errors.jsonl"
BLOCKS = Path(".tf") / "logs" / "hook-blocks.jsonl"   # hook blocks (time, hook, decision) — no content


def _log_path() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".") / LOG


def record(hook: str, exc: BaseException) -> None:
    """Record a hook error; never raises."""
    try:
        frames = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
        where = f"{Path(frames[-1].filename).name}:{frames[-1].lineno}" if frames else "?"
        entry = {"ts": round(time.time(), 3), "hook": hook, "type": type(exc).__name__, "where": where,
                 "msg": str(exc)[:200]}
        p = _log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if p.stat().st_size > MAX_BYTES:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            keep, size = [], 0
            for line in reversed(lines):
                size += len(line.encode("utf-8")) + 1
                if size > MAX_BYTES // 2:
                    break
                keep.append(line)
            p.write_text("\n".join(reversed(keep)) + "\n", encoding="utf-8")
    except Exception:  # noqa: BLE001 — the error log must not itself break the hook
        return None


def _append(p: Path, entry: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if p.stat().st_size > MAX_BYTES:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        p.write_text("\n".join(lines[len(lines) // 2:]) + "\n", encoding="utf-8")


def record_block(hook: str, decision: str) -> None:
    """Record a hook block (`deny` or `ask`): time, hook, decision — no command, path or content. From this
    log `metrics.py --after-update` counts blocks before and after a factory update. Never raises."""
    try:
        _append(Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".") / BLOCKS,
                {"ts": round(time.time(), 3), "hook": str(hook)[:40], "decision": str(decision)[:10]})
    except Exception:  # noqa: BLE001
        return None


def summary(days: int = 7) -> str:
    """One line for `tf doctor`, or an empty string when there were no errors in the window."""
    p = _log_path()
    if not p.is_file():
        return ""
    since, hooks = time.time() - days * 86400, Counter()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(e, dict) and float(e.get("ts", 0)) >= since:
            hooks[f"{e.get('hook')} ({e.get('type')} w {e.get('where')})"] += 1
    if not hooks:
        return ""
    top = ", ".join(f"{k} ×{v}" for k, v in hooks.most_common(5))
    return (f"⚠ hook errors in the last {days} days: {sum(hooks.values())} — {top}. The hooks did not stop the work, "
            f"but their protection may not have worked; details: {LOG.as_posix()}")


def main(argv: list[str]) -> int:
    for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know „⚠”, „×” — always UTF-8
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if "--summary" in argv:
        days = 7
        if "--days" in argv and argv.index("--days") + 1 < len(argv):
            try:
                days = int(argv[argv.index("--days") + 1])
            except ValueError:
                days = 7
        text = summary(days)
        if text:
            print(text)
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
