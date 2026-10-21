#!/usr/bin/env python3
"""
Przełącznik agent teams Claude Code w tym projekcie (tryb mode-team, skill team-session).

  python3 .claude/skills/team-session/scripts/team_switch.py on       # włącz (od następnej sesji)
  python3 .claude/skills/team-session/scripts/team_switch.py off      # wyłącz
  python3 .claude/skills/team-session/scripts/team_switch.py status

Zmienna `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` trafia do `env` w `.claude/settings.local.json` — osobista decyzja,
także przy instalacji zespołowej (plik nie jest commitowany). Pozostałe ustawienia zostają bez zmian. Po włączeniu
podagent, któremu Claude nada nazwę, startuje jako członek zespołu, dlatego po sesji zespołu flagę wyłączasz.
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
        print(f"✗ {LOCAL}: nie da się odczytać ({e}) — popraw plik ręcznie; nic nie zmieniono.", file=sys.stderr)
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
        print(f"agent teams: {'włączone' if env.get(VAR) == '1' else 'wyłączone'} ({LOCAL})")
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
    state = "włączone" if cmd == "on" else "wyłączone"
    print(f"✓ agent teams {state} w {LOCAL} — zmiana działa od następnej sesji: zamknij tę i otwórz nową sesję.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
