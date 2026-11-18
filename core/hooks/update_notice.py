#!/usr/bin/env python3
"""SessionStart hook: a newer factory release and skills past their review date (standard library only).

In a project with the factory installed: once a day asks the update source (.tf/factory/update.py → notice) and, when there is
a newer release, shows a message to the human (systemMessage) and to the agent. With `update.py --auto on` (private mode)
a new PATCH/MINOR release is installed in the background (`update.py --auto-run`), and the result is shown at the start of the next session. Wherever .tf/factory/freshness.py exists:
a list of skills past their review date — the agent checks volatile facts in them against sources before use. In a project with the factory,
also one sentence when the quality gate is off (`quality_gate.py`: no configuration, kill switch, red batch). The switch for
release checking: CTF_UPDATE_CHECK=0. The hook never blocks session start (exit 0, silence when there is nothing to report).
"""
import importlib.util
import json
import os
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


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def messages(root: Path) -> list[str]:
    out = []
    up = root / ".tf" / "factory" / "update.py"
    if up.is_file():
        try:
            mod = load(up, "ctf_update_notice")
            out += mod.pending_messages(root) if hasattr(mod, "pending_messages") else []
            msg = (mod.start_auto(root) if hasattr(mod, "start_auto") else None) or mod.notice(root)
        except Exception:
            msg = None
        if msg:
            out.append(msg)
    fr = root / ".tf" / "factory" / "freshness.py"
    if fr.is_file():
        try:
            import datetime as dt
            rows = [r for r in load(fr, "ctf_freshness_notice").scan(root, dt.date.today()) if r["status"] == "overdue"]
        except Exception:
            rows = []
        if rows:
            names = ", ".join(r["skill"] for r in rows[:8]) + (" …" if len(rows) > 8 else "")
            out.append(f"Skills past their review date ({len(rows)}): {names}. Check their volatile facts (versions, regulations, "
                       "deadlines, thresholds) in sources before use (core-source-research). The list: "
                       "python3 .tf/factory/freshness.py; a newer factory may have refreshed them already.")
    gate = root / ".claude" / "hooks" / "quality_gate.py"
    if gate.is_file() and (root / ".claude" / "factory-manifest.json").is_file():
        try:   # quality gate disabled: the human and the agent should know from the first moment of the session
            state, text = load(gate, "ctf_gate_notice").gate_status(root)
        except Exception:
            state, text = "on", ""
        if state != "on":
            out.append(text)
    return out


def main() -> int:
    try:
        sys.stdin.read()
    except Exception as e:  # the hook does not interrupt the session; the error goes to the log
        record_error("update_notice", e)
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parent.parent.parent).resolve()
    out = messages(root)
    if out:
        text = "\n".join(out)
        print(json.dumps({"systemMessage": text,
                          "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
