#!/usr/bin/env python3
"""Testy przełącznika agent teams (tryb mode-team, skill team-session, scripts/team_switch.py).
python3 .claude/tests/test_team_switch.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "team-session" / "scripts" / "team_switch.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL
VAR = "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"


def run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=60)


def main() -> int:
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        proj = Path(t)
        local = proj / ".claude" / "settings.local.json"

        r = run(proj, "status")
        check(r.returncode == 0 and "wyłączone" in r.stdout and not local.exists(), f"S-1: status bez ustawień: {r.stdout}")

        local.parent.mkdir(parents=True)
        local.write_text(json.dumps({"permissions": {"allow": ["Bash(ls)"]}, "env": {"FOO": "1"}}), encoding="utf-8")
        r = run(proj, "on")
        data = json.loads(local.read_text(encoding="utf-8"))
        check(r.returncode == 0 and data["env"] == {"FOO": "1", VAR: "1"} and data["permissions"]["allow"] == ["Bash(ls)"],
              f"S-2: on dopisuje zmienną, reszta nietknięta: {data}")
        check("nową sesję" in r.stdout, f"S-3: przypomnienie o nowej sesji: {r.stdout}")
        r = run(proj, "on")
        check(r.returncode == 0 and json.loads(local.read_text(encoding="utf-8"))["env"][VAR] == "1", "S-4: on dwa razy")
        r = run(proj, "status")
        check("włączone" in r.stdout and "wyłączone" not in r.stdout, f"S-5: status po on: {r.stdout}")

        r = run(proj, "off")
        data = json.loads(local.read_text(encoding="utf-8"))
        check(r.returncode == 0 and data["env"] == {"FOO": "1"}, f"S-6: off usuwa tylko tę zmienną: {data}")
        local.write_text(json.dumps({"env": {VAR: "1"}}), encoding="utf-8")
        run(proj, "off")
        check(json.loads(local.read_text(encoding="utf-8")) == {}, "S-7: off usuwa pusty env")

        local.write_text("{nie json", encoding="utf-8")
        r = run(proj, "on")
        check(r.returncode == 2 and local.read_text(encoding="utf-8") == "{nie json" and "Traceback" not in r.stderr,
              f"S-8: zły JSON → kod 2, plik nietknięty: {r.returncode} {r.stderr[-200:]}")
        r = run(proj, "coś")
        check(r.returncode == 2, f"S-9: nieznane polecenie → kod 2: {r.returncode}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {9 - len(fails)}/9 testów przełącznika agent teams")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
