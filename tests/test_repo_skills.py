#!/usr/bin/env python3
"""Testy skilli repozytorium fabryki (`.claude/skills/` w repo tf — dla autora fabryki, nie instalowane w projektach):
nagłówek, scenariusze ewaluacji, polecenia `tools/workspace.py` i pliki, do których skill odsyła, audyt skilla.
python3 tests/test_repo_skills.py"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
SKILLS = ROOT / ".claude" / "skills"
EXPECTED = ["tf-new-pack"]


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    found = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
    check(set(EXPECTED) <= set(found), f"R-1: skille repozytorium: {found}")
    ws_text = (ROOT / "tools" / "workspace.py").read_text(encoding="utf-8")
    commands = set(re.findall(r'cmd == "([a-z-]+)"', ws_text))
    for name in found:
        d = SKILLS / name
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        head = text.split("---")[1] if text.startswith("---") else ""
        desc = (re.search(r"^description: (.*)$", head, re.M) or [None, ""])[1]
        check(re.search(rf"^name: {re.escape(name)}$", head, re.M), f"R-2 {name}: name = katalog")
        check(desc.startswith("Użyj") and len(desc) <= 170 and ": " not in desc, f"R-3 {name}: opis jako reguła wyboru ≤170: {desc}")
        check("katalog:" in head and "Nie do" in head, f"R-4 {name}: metadata.katalog z granicami")
        ev = d / "evals.json"
        data = json.loads(ev.read_text(encoding="utf-8")) if ev.is_file() else {}
        sc = data.get("scenarios", [])
        trig = [s for s in sc if s.get("expect") == "trigger"]
        check(data.get("skill") == name and len(trig) >= 2 and all(len((s.get("checks") or {}).get("all", [])) >= 2 for s in trig)
              and any(s.get("expect") == "no-trigger" and s.get("neighbor") for s in sc) and "TODO" not in json.dumps(data),
              f"R-5 {name}: scenariusze (≥2 trigger z ≥2 grupami, no-trigger z sąsiadem, bez TODO)")
        used = set(re.findall(r"tools/workspace\.py ([a-z-]+)", text))
        check(used and used <= commands, f"R-6 {name}: polecenia workspace.py istnieją: {sorted(used - commands)}")
        for rel in re.findall(r"`((?:docs|tools|core|tests)/[^`\s]+\.(?:md|py|yml|yaml))`", text):
            check((ROOT / rel).is_file(), f"R-7 {name}: plik `{rel}` istnieje")
        for ref in re.findall(r"`(references/[^`]+)`", text):
            check((d / ref).is_file(), f"R-8 {name}: {ref} istnieje")
        r = subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "skill_audit.py"), str(d)],
                           capture_output=True, text=True)
        check(r.returncode == 0, f"R-9 {name}: audyt bez ustaleń wysokiej i średniej wagi: {r.stdout[-600:]}")
    check(not (ROOT / "core" / "skills" / "tf-new-pack").exists(), "R-10: skill autora fabryki nie trafia do rdzenia")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów skilli repozytorium")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
