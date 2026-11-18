#!/usr/bin/env python3
"""
Toggle for Claude Code agent teams in this project (mode-team, skill team-session).

  python3 .claude/skills/team-session/scripts/team_switch.py on       # enable (from the next session)
  python3 .claude/skills/team-session/scripts/team_switch.py off      # disable
  python3 .claude/skills/team-session/scripts/team_switch.py status

The variable `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` goes into `env` in `.claude/settings.local.json` — a personal decision,
even in a team installation (the file is not committed). Other settings are left unchanged. Once enabled, a
subagent that Claude gives a name starts as a team member, which is why you turn the flag off after a team session.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

VAR = "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"
LOCAL = Path(".claude") / "settings.local.json"


def load() -> dict | None:
    if not LOCAL.exists():
        return {}
    try:
        data = json.loads(LOCAL.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"✗ {LOCAL}: cannot read it ({e}) — fix the file by hand; nothing was changed.", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd not in ("on", "off", "status"):
        print(__doc__)
        return 2
    data = load()
    if data is None:
        return 2
    env = data.get("env") or {}
    if cmd == "status":
        print(f"agent teams: {'on' if env.get(VAR) == '1' else 'off'} ({LOCAL})")
        return 0
    if cmd == "on":
        env[VAR] = "1"
    else:
        env.pop(VAR, None)
    if env:
        data["env"] = env
    else:
        data.pop("env", None)
    LOCAL.parent.mkdir(parents=True, exist_ok=True)
    LOCAL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state = "on" if cmd == "on" else "off"
    print(f"✓ agent teams {state} in {LOCAL} — the change takes effect from the next session: close this one and "
          "open a new session.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
