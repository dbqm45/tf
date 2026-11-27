#!/usr/bin/env python3
"""tf stress hook probe: wraps one factory hook, passes stdin/stdout/stderr and the exit code through unchanged, and
appends {hook, event, tool, ms, rc} to .stress/hooks.jsonl in the project. tf stress rewrites the project's hook
registrations to `python3 .stress/hookprobe.py <hook script> [args]` before a model run. Standard library only."""
import json
import os
import subprocess
import sys
import time


def main() -> int:
    data = sys.stdin.buffer.read()
    t = time.perf_counter()
    p = subprocess.run([sys.executable, *sys.argv[1:]], input=data, capture_output=True)
    ms = (time.perf_counter() - t) * 1000
    sys.stdout.buffer.write(p.stdout)
    sys.stderr.buffer.write(p.stderr)
    try:
        d = json.loads(data or b"{}")
        root = os.environ.get("CLAUDE_PROJECT_DIR") or d.get("cwd") or "."
        os.makedirs(os.path.join(root, ".stress"), exist_ok=True)
        rec = {"t": time.time(), "hook": os.path.basename(sys.argv[1]) + ("" if len(sys.argv) < 3 else " " + " ".join(sys.argv[2:])),
               "event": d.get("hook_event_name"), "tool": d.get("tool_name"), "agent": d.get("agent_id"),
               "ms": round(ms, 1), "rc": p.returncode,
               "blocked": p.returncode == 2 or b'"deny"' in p.stdout or b'"block"' in p.stdout}
        with open(os.path.join(root, ".stress", "hooks.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
    except Exception:
        pass
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
