#!/usr/bin/env python3
"""A fake `claude` for `tools/stress.py run --claude "python3 tools/stress/fake_claude.py"`: no model, no network.

It plays a short stream-json session in the current directory (a tf stress project copy): a model turn, a Bash
tool call of the factory's run_state.py (a phase marker), a failing call (a wasted turn), an edit that fixes the
fixture's heading typo, a commit on a story branch, and the final `result` event with cost and turns — enough for the
profiler, the evaluator and the reports to be tested without a model. Standard library only."""
import json
import subprocess
import sys
import time
from pathlib import Path


def emit(obj):
    print(json.dumps(obj), flush=True)


def main() -> int:
    sid = "fake-session"
    emit({"type": "system", "subtype": "init", "session_id": sid})
    tid = 0

    def call(name, inp, out, err=False, pause=0.05):
        nonlocal tid
        tid += 1
        mid = f"msg_{tid}"
        time.sleep(pause)
        emit({"type": "assistant", "message": {"id": mid, "content": [{"type": "tool_use", "id": f"tu_{tid}", "name": name,
                                                                         "input": inp}]}, "parent_tool_use_id": None})
        time.sleep(pause)
        emit({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"tu_{tid}", "content": out,
                                                       "is_error": err}]}, "parent_tool_use_id": None})

    call("Bash", {"command": "git status --porcelain"}, "")
    call("Bash", {"command": "python3 .claude/skills/tf/scripts/run_state.py stage .tf/runs/K intake --auto"}, "✓ stage: intake")
    call("Bash", {"command": "python3 .claude/hooks/missing.py wip done x"}, "Exit code 2 no such file", err=True)
    p = Path("public/index.html")
    if p.exists():
        p.write_text(p.read_text(encoding="utf-8").replace("Moje zadnia", "Moje zadania"), encoding="utf-8")
    call("Edit", {"file_path": str(p.resolve())}, "ok")
    git = ["git", "-c", "user.name=fake", "-c", "user.email=fake@example.invalid"]
    subprocess.run([*git, "switch", "-q", "-c", "story/fake"], capture_output=True)
    subprocess.run([*git, "commit", "-qam", "fix(ui): heading typo"], capture_output=True)
    call("Bash", {"command": "git commit -am 'fix(ui): heading typo'"}, "[story/fake abc123] fix")
    time.sleep(0.05)
    emit({"type": "assistant", "message": {"id": "msg_end", "content": [{"type": "text", "text": "Done."}]},
          "parent_tool_use_id": None})
    emit({"type": "result", "subtype": "success", "is_error": False, "num_turns": 6, "total_cost_usd": 0.12,
          "duration_api_ms": 400, "result": "Done.", "session_id": sid,
          "usage": {"cache_creation_input_tokens": 1000, "cache_read_input_tokens": 5000, "output_tokens": 50},
          "modelUsage": {"fake-model": {"costUSD": 0.12}}})
    return 0


if __name__ == "__main__":
    sys.exit(main())
