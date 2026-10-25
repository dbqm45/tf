#!/usr/bin/env python3
"""Testy trybu mode-talos w zainstalowanym projekcie: agent sesji głównej `talos`, skill procesowy, skrypt przebiegu,
uprawnienie dla skryptu i przewodnik. python3 .claude/tests/test_mode_talos.py"""
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "packs" / "mode-talos").is_dir())


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    agents = ROOT / ".claude" / "agents" / "_generated"
    talos = next(iter(agents.rglob("talos.md")), None)
    text = talos.read_text(encoding="utf-8") if talos else ""
    fm = text.split("---")[1] if text.count("---") >= 2 else ""
    check("Agent(scout, researcher, quick-fixer, scope-reviewer, architect, security-reviewer)" in fm
          and "skills:" not in fm and "maxTurns" not in fm,
          f"T-1: talos — sesja główna z listą agentów, bez preładowania skilli i limitu tur: {fm[:300]}")
    skill = ROOT / ".claude" / "skills" / "talos-story-run"
    check(".claude/skills/talos-story-run/SKILL.md" in text and (skill / "SKILL.md").is_file(),
          "T-2: agent czyta skill procesowy z pliku, który jest zainstalowany")
    script = ".claude/skills/talos-story-run/scripts/run_report.py"
    check((ROOT / script).is_file() and script in (skill / "SKILL.md").read_text(encoding="utf-8"),
          "T-3: skrypt przebiegu przy skillu i ścieżka w skillu")
    allow = []
    for name in ("settings.json", "settings.local.json"):
        f = ROOT / ".claude" / name
        if f.is_file():
            allow += json.loads(f.read_text(encoding="utf-8")).get("permissions", {}).get("allow", [])
    check(any(script in a for a in allow), f"T-4: uprawnienie dla skryptu przebiegu: {[a for a in allow if 'run' in a]}")
    check((ROOT / "factory" / "packs" / "mode-talos" / "GUIDE.md").is_file(), "T-5: przewodnik trybu w projekcie")
    personas = [p for p in agents.rglob("*.md") if p.parent.name not in ("shared", "consult") and p.stem == p.parent.name]
    check(personas == [] or all("`talos`" not in p.read_text(encoding="utf-8") for p in personas),
          "T-6: persony nie delegują do talos (to sesja główna, nie wykonawca)")
    body = (skill / "SKILL.md").read_text(encoding="utf-8") if (skill / "SKILL.md").is_file() else ""
    intake = body.split("## 1.", 1)[-1].split("## 2.", 1)[0]
    check("requirements_lint.py --story" in intake and "STORY-001" in intake and "--auto" in intake
          and "STOP" in intake and "podzia" in intake and "(pack-it)" in intake,
          "T-7: przyjęcie historyjki — lint kształtu (pack-it, warunkowo); z --auto STORY-001 → STOP z propozycją podziału")
    loop = body.split("## 3.", 1)[-1].split("## 4.", 1)[0]
    check("`Flag: " in loop and "release.yaml" in loop and "za flagą" in loop,
          "T-8: kawałek z flagą — kod za flagą i dopisek `Flag: <klucz>` w commicie (plan wydania release.yaml)")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów trybu Talos")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
