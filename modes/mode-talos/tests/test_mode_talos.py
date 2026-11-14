#!/usr/bin/env python3
"""Testy warstwy zgodności mode-talos: stare nazwy (skill `talos-story-run`, agent `talos`, stara ścieżka skryptów)
prowadzą do pętli w rdzeniu (skill i agent `tf`). python3 .claude/tests/test_mode_talos.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "packs" / "mode-talos").is_dir())
OLD = ROOT / ".claude" / "skills" / "talos-story-run"
NEW = ROOT / ".claude" / "skills" / "tf"


def run(script: Path, args: list[str], cwd: Path):
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cwd / "cfg"), "TF_DASHBOARD_OPEN": "0", "CLAUDE_PROJECT_DIR": str(cwd)}
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True, env=env, timeout=60)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    agents = ROOT / ".claude" / "agents" / "_generated"
    old_agent = next(iter(agents.rglob("talos.md")), None)
    new_agent = next(iter(agents.rglob("tf.md")), None)
    text = old_agent.read_text(encoding="utf-8") if old_agent else ""
    check(old_agent is not None and new_agent is not None and ".claude/skills/tf/SKILL.md" in text,
          "Z-1: alias agenta `talos` istnieje obok agenta `tf` i czyta skill pętli z rdzenia")
    skill = (OLD / "SKILL.md").read_text(encoding="utf-8") if (OLD / "SKILL.md").is_file() else ""
    check("disable-model-invocation: true" in skill and ".claude/skills/tf/SKILL.md" in skill and "$ARGUMENTS" in skill
          and len(skill) < 2500 and (NEW / "SKILL.md").is_file(),
          f"Z-2: alias skilla jest krótki, uruchamiany tylko przez człowieka i wskazuje skill tf: {len(skill)} znaków")
    names = sorted(p.name for p in (OLD / "scripts").glob("*.py")) if (OLD / "scripts").is_dir() else []
    check(names == ["plan_drift.py", "run_report.py", "run_state.py", "security_scan.py"]
          and all((NEW / "scripts" / n).is_file() for n in names),
          f"Z-3: każda stara ścieżka skryptu ma przekierowanie i odpowiednik w rdzeniu: {names}")
    allow = []
    for name in ("settings.json", "settings.local.json"):
        f = ROOT / ".claude" / name
        if f.is_file():
            allow += json.loads(f.read_text(encoding="utf-8")).get("permissions", {}).get("allow", [])
    check(all(any(f".claude/skills/talos-story-run/scripts/{n}" in a for a in allow) for n in names),
          "Z-4: stare ścieżki skryptów mają uprawnienia, więc nie pytają człowieka")
    guide = ROOT / ".tf" / "factory" / "packs" / "mode-talos" / "GUIDE.md"
    gtext = guide.read_text(encoding="utf-8") if guide.is_file() else ""
    check("/tf" in gtext and "przestarzałe" in gtext.lower() and "tf remove mode-talos" in gtext,
          "Z-5: przewodnik trybu mówi, że to warstwa zgodności, i jak z niej zejść")

    with tempfile.TemporaryDirectory() as t:      # stara ścieżka daje ten sam wynik co nowa
        a, b = Path(t) / "stara", Path(t) / "nowa"
        a.mkdir()
        b.mkdir()
        ra = run(OLD / "scripts" / "run_report.py", ["start", "Limit dobowy", "--key", "PROJ-1", "--story", "x"], a)
        rb = run(NEW / "scripts" / "run_report.py", ["start", "Limit dobowy", "--key", "PROJ-1", "--story", "x"], b)
        fa = sorted(p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file() and "cfg" not in p.parts)
        fb = sorted(p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file() and "cfg" not in p.parts)
        check(ra.returncode == 0 and ra.stdout == rb.stdout == ".tf/runs/PROJ-1\n" and fa == fb and fa,
              f"Z-6: run_report.py start starą ścieżką = nową (wyjście i pliki): {ra.returncode} {ra.stdout!r} {ra.stderr[-200:]}")
        ra = run(OLD / "scripts" / "run_state.py", ["stage", ".tf/runs/PROJ-1", "nie-ma-takiego"], a)
        rb = run(NEW / "scripts" / "run_state.py", ["stage", ".tf/runs/PROJ-1", "nie-ma-takiego"], b)
        check(ra.returncode == rb.returncode == 2 and ra.stdout == rb.stdout,
              f"Z-7: kod wyjścia i komunikat błędu przechodzą przez przekierowanie: {ra.returncode} {ra.stdout!r}")
        ra = run(OLD / "scripts" / "plan_drift.py", ["--help"], a)
        check(ra.returncode == 0 and "plan" in ra.stdout.lower(), f"Z-8: plan_drift.py --help starą ścieżką: {ra.returncode}")
        ra = run(OLD / "scripts" / "security_scan.py", ["verdict"], a)
        rb = run(NEW / "scripts" / "security_scan.py", ["verdict"], b)
        check(ra.returncode == rb.returncode and ra.stdout == rb.stdout,
              f"Z-9: security_scan.py starą ścieżką = nową: {ra.returncode} vs {rb.returncode}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów warstwy zgodności mode-talos")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
