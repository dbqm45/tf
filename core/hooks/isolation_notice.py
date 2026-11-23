#!/usr/bin/env python3
"""
SessionStart: one line with the isolation level of this session and what it does not protect (plan
docs/plans/2026-11-20-poziomy-izolacji.md, slice I3), plus the gaps `tf isolation` names (no sandbox in a session
started without `tf code`, Linux without bubblewrap, `container` outside the container).

The level and the gaps come from `.tf/factory/isolation.py`; without the engine the hook says nothing. An error never
blocks the session (it goes to `.tf/logs/hook-errors.jsonl`).
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record
except ImportError:  # an install without the hook logs
    def record(hook: str, exc: BaseException) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: the code page ≠ UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

NOT_COVERED = {
    "basic": "not isolation: commands run by the agent can read and send whatever your user account can",
    "sandbox": "the sandbox limits Bash commands only; Claude's file tools, hooks and MCP servers run outside it",
    "container": "only the project is mounted; Claude's file tools and MCP servers work inside the container too",
}


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = {}
    cwd = data.get("cwd") if isinstance(data, dict) and isinstance(data.get("cwd"), str) else None
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or cwd or os.getcwd())
    engine = project / ".tf" / "factory" / "isolation.py"
    if not engine.is_file():
        sys.exit(0)
    try:
        spec = importlib.util.spec_from_file_location("tf_isolation_notice", engine)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        s = mod.state(project)
    except Exception as e:  # noqa: BLE001 — the session starts anyway
        record("isolation_notice", e)
        sys.exit(0)
    text = f"[isolation] Isolation: {s['level']} — {NOT_COVERED.get(s['level'], '')}."
    if s.get("gaps"):
        text += " Gaps: " + "; ".join(s["gaps"]) + ". The level is changed by a human in a terminal (`tf isolation`)."
    print(json.dumps({"systemMessage": text,
                      "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
                     ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
