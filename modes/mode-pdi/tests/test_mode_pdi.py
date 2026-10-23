#!/usr/bin/env python3
"""Testy trybu mode-pdi w zainstalowanym projekcie: skill i skrypt dziennika zmiany, szablony, uprawnienie dla skryptu,
skill u person i przewodnik. python3 .claude/tests/test_mode_pdi.py"""
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "packs" / "mode-pdi").is_dir())


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    skill = ROOT / ".claude" / "skills" / "pdi-decisions"
    script = ".claude/skills/pdi-decisions/scripts/decision_record.py"
    text = (skill / "SKILL.md").read_text(encoding="utf-8") if (skill / "SKILL.md").is_file() else ""
    check(text and script in text and (ROOT / script).is_file(), "P-1: skill i skrypt zainstalowane, ścieżka w skillu")
    check(all((skill / "templates" / f"{n}.md").is_file() for n in ("intent", "plan", "decisions")),
          "P-2: szablony intent, plan, decisions przy skillu")
    allow = []
    for name in ("settings.json", "settings.local.json"):
        f = ROOT / ".claude" / name
        if f.is_file():
            allow += json.loads(f.read_text(encoding="utf-8")).get("permissions", {}).get("allow", [])
    check(any(script in a for a in allow), "P-3: uprawnienie dla skryptu dziennika zmiany")
    agents = ROOT / ".claude" / "agents" / "_generated"
    personas = [p for p in agents.rglob("*.md") if p.parent.name not in ("shared", "consult") and p.stem == p.parent.name]
    check(personas == [] or all("pdi-decisions" in p.read_text(encoding="utf-8") for p in personas),
          "P-4: skill pdi-decisions u każdej persony")
    check((ROOT / "factory" / "packs" / "mode-pdi" / "GUIDE.md").is_file(), "P-5: przewodnik trybu w projekcie")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów trybu pdi")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
