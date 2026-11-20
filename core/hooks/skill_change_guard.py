#!/usr/bin/env python3
"""
Guards the skill quality gate (.tf/factory/skill_gate.py).

PostToolUse (Edit|Write): after a skill file (`.claude/skills/<skill>/…`) or its scenarios
(`…/skill_evals/<skill>.json`) changes, appends a gate reminder to the context — once per skill per session.
Stop: if a skill was changed in this session and its content differs from the last passed gate, shows the human
the list (a message, not a block).

Disable: CLAUDE_SKILL_GATE=0. Standard library only; an error never blocks work.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record as record_error  # hook error to .tf/logs/hook-errors.jsonl (tf doctor)
except ImportError:  # older install without the log module — the hook works as before
    def record_error(hook: str, exc: BaseException) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

PATH_RE = re.compile(r"(?:\.claude|\.tf/plugin)/skills/([a-z0-9][a-z0-9-]*)/|skill_evals/([a-z0-9][a-z0-9-]*)\.json$")


def has_skill(root: Path, skill: str) -> bool:
    """The skill's SKILL.md in .claude/skills (your own) or in the factory plugin (factory mode)."""
    return any((root / d / "skills" / skill / "SKILL.md").exists() for d in (".claude", ".tf/plugin"))


def root_of(data: dict) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")


def state_path(root: Path) -> Path:
    return root / ".tf" / "logs" / "skill-changes.json"


def load_state(root: Path) -> dict:
    try:
        return json.loads(state_path(root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(root: Path, state: dict) -> None:
    p = state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(list(state.items())[-50:]), ensure_ascii=False), encoding="utf-8")


def on_edit(data: dict) -> None:
    path = str((data.get("tool_input") or {}).get("file_path") or "").replace("\\", "/")
    m = PATH_RE.search(path)
    if not m:
        return
    skill = m.group(1) or m.group(2)
    root = root_of(data)
    if not has_skill(root, skill) and not path.endswith("SKILL.md"):
        return
    state = load_state(root)
    sess = str(data.get("session_id") or "?")
    seen = state.setdefault(sess, [])
    if skill in seen:
        return
    seen.append(skill)
    save_state(root, state)
    msg = (f"The skill {skill} was changed. Before you consider the work finished, run the quality gate: "
           f"`python3 .tf/factory/skill_gate.py {skill}` (free: structure, scenarios, hint, regression of other "
           "skills, language). A new skill starts from evaluation scenarios (the core-skill-authoring skill). An evaluation "
           f"on a model (`--model haiku,sonnet`) you run only after a human's consent — it is paid.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}},
                     ensure_ascii=False))


def on_stop(data: dict) -> None:
    root = root_of(data)
    seen = load_state(root).get(str(data.get("session_id") or "?")) or []
    if not seen:
        return
    build_py = root / ".tf" / "factory" / "build.py"
    if not build_py.exists():
        return
    spec = importlib.util.spec_from_file_location("factory_build", build_py)
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    reg = build.gate_registry()
    stale = [s for s in seen if has_skill(root, s)
             and reg.get(s, {}).get("fingerprint") != build.skill_fingerprint(s)]
    if stale:
        print(json.dumps({"systemMessage": "⚠ Skills changed in this session without a passed quality gate: "
                          + ", ".join(stale) + f". Run: python3 .tf/factory/skill_gate.py {' '.join(stale)}"},
                         ensure_ascii=False))


def main() -> int:
    if os.environ.get("CLAUDE_SKILL_GATE") == "0":
        return 0
    try:
        data = json.load(sys.stdin)
        if data.get("hook_event_name") == "Stop":
            on_stop(data)
        else:
            on_edit(data)
    except Exception as e:  # the hook does not interrupt the session; the error goes to the log
        record_error("skill_change_guard", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
