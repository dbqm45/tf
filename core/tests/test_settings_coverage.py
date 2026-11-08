#!/usr/bin/env python3
"""Pokrycie poleceń Bash Talosa przez permissions.allow (PRB-32): skille talos-story-run (SKILL.md i scripts/)
oraz skrypty fazy delivery pdi (phase_run.py cuts publish) uruchamiają git i gh; każde takie wywołanie musi być
w `permissions.allow` zestawionych ustawień projektu (.claude/settings.json, core + mode-talos + mode-pdi).

Źródło (odczyt 2026-11-05 code.claude.com/docs/en/permissions): bez pokrywającej reguły `permissions.allow` polecenie
Bash w `claude --print --permission-mode acceptEdits` prosi człowieka, a w `-p` prośba kończy się odmową.

Dwa układy: w przestrzeni fabryki (źródło `core/` + `modes/`) test zestawia ustawienia z plików nakładek, w zainstalowanym
projekcie (`.claude/tests/` obok `.claude/skills/`) czyta `.claude/settings.json` i `.claude/settings.local.json`
i sprawdza tylko polecenia skilli, które są zainstalowane (bez talos-story-run i pdi-decisions — pominięcie).

  python3 .claude/tests/test_settings_coverage.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
# zainstalowany projekt: <projekt>/.claude/tests/test_settings_coverage.py (ma pierwszeństwo — także w .work/ fabryki)
INSTALLED = HERE.parent.name == "tests" and HERE.parent.parent.name == ".claude" \
    and (HERE.parent.parent / "skills").is_dir()
ROOT = HERE.parents[2] if INSTALLED else next(
    (p for p in HERE.parents if (p / "core" / "settings.json").is_file() and (p / "modes" / "mode-talos").is_dir()),
    None)
TALOS = ".claude/skills/talos-story-run/"
PDI = ".claude/skills/pdi-decisions/"
PY = "python3"

# Polecenia, które Talos i fazy pdi uruchamiają w sesji (persona w --print). Każde musi mieć regułę `allow`.
# Nie wymieniamy tu `git push` ani `gh pr …` fazy cuts publish, bo one są w phase_run.py (uruchamiane spoza sesji
# persony), a nie w zapytaniu Talosa.
REQUIRED = [
    # Talos w trakcie przebiegu (SKILL.md: start, pętla kawałka, zakończenie)
    "git status",
    "git status --porcelain",
    "git diff",
    "git diff --name-only HEAD",
    "git log --oneline -5",
    "git show HEAD",
    "git branch --show-current",
    "git switch main",                         # powrót na gałąź domyślną po kawałku
    "git switch -c story/tsk-1-fundament",     # gałąź historyjki (cięcie)
    "git switch -c story/import-cdr",          # gałąź historyjki (zwykła)
    "git add -A",
    "git add src/payments/retry.ts",
    "git commit -m 'feat(x): y'",
    # skrypty Talosa
    "python3 .claude/skills/talos-story-run/scripts/run_report.py start --task TSK-1",
    "python3 .claude/skills/talos-story-run/scripts/run_report.py finish tmp/talos/runs/2026-11-05-x",
    "python3 .claude/skills/talos-story-run/scripts/plan_drift.py tmp/talos/runs/x --base main",
    "python3 .claude/skills/talos-story-run/scripts/security_scan.py scan --slice K1 --attempt 1",
    # skrypt pdi wywoływany na końcu fazy architecture/design (decision_record.py check — w prompcie phase_run.py)
    "python3 .claude/skills/pdi-decisions/scripts/decision_record.py check",
    # pętla PR talosa (N2, pr_loop.py fix): poprawka uwag, weryfikacja N3 i commit z trzema -m
    "./verify.sh",
    "git commit -m 'fix(x): y' -m 'Runda pętli PR 1' -m 'Change: TSK-1'",
    # kroki pętli PR w kontenerze fazy (pdi uruchamia je poza sesją persony; wpis na wypadek ręcznego użycia)
    "python3 .claude/skills/pdi-decisions/scripts/pr_loop.py verify",
]


def installed_python() -> str:
    """Polecenie Pythona z manifestu instalacji — instalator wpisuje je w reguły zamiast `python3` (apply_python)."""
    try:
        data = json.loads((ROOT / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
        return str(data.get("python") or PY)
    except (OSError, ValueError):
        return PY


def load_installed_allow() -> list[str]:
    """Reguły `permissions.allow` zainstalowanego projektu (tryb zespołowy i prywatny), z `python3` w miejsce
    polecenia Pythona wybranego przy instalacji."""
    py = installed_python()
    rules: list[str] = []
    for name in ("settings.json", "settings.local.json"):
        f = ROOT / ".claude" / name
        if f.is_file():
            rules += (json.loads(f.read_text(encoding="utf-8")).get("permissions") or {}).get("allow") or []
    if py != PY:
        rules = [f"Bash({PY} " + r[len(f"Bash({py} "):] if r.startswith(f"Bash({py} ") else r for r in rules]
    return rules


def load_allow() -> list[str]:
    """Reguły `permissions.allow` zestawione z core + mode-talos + mode-pdi + pack-it (SKILL Talosa wywołuje
    `requirements_lint.py` z pack-it, jeśli jest zainstalowany — instalator zestawia settings tak samo)."""
    if INSTALLED:
        return load_installed_allow()
    rules: list[str] = []
    for rel in ("core/settings.json", "modes/mode-talos/settings.json", "modes/mode-pdi/settings.json",
                "packs/pack-it/settings.json"):
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        rules += (data.get("permissions") or {}).get("allow") or []
    return rules


def bash_patterns(rules: list[str]) -> list[str]:
    """Wzorce `Bash(...)` ze zestawionych reguł — zwraca tylko polecenia (bez `Bash(` i `)`)."""
    return [m.group(1) for r in rules if (m := re.fullmatch(r"Bash\((.*)\)", r))]


def to_regex(pattern: str) -> re.Pattern:
    """Reguła `Bash(foo *)` matchuje każde polecenie zaczynające się od `foo` (z opcjonalnym argumentem lub bez).
    Reguła `Bash(foo)` matchuje tylko dokładnie `foo` (bez trailing *)."""
    # obsłuż też wariant z ':*' (równoważny według code.claude.com/docs/en/permissions)
    if pattern.endswith(":*"):
        pattern = pattern[:-2] + " *"
    if pattern.endswith(" *"):
        # `foo *` matchuje `foo`, `foo arg`, `foo arg1 arg2 …`
        head = re.escape(pattern[:-2])
        return re.compile(rf"^{head}(?:\s.*)?$")
    return re.compile(f"^{re.escape(pattern)}$")


def covers(cmd: str, patterns: list[re.Pattern]) -> bool:
    return any(p.match(cmd) for p in patterns)


def skill_path() -> Path:
    if INSTALLED:
        return ROOT / TALOS / "SKILL.md"
    return ROOT / "modes" / "mode-talos" / "skills" / "talos-story-run" / "SKILL.md"


def required() -> list[str]:
    """Polecenia do sprawdzenia: w zainstalowanym projekcie tylko te, których skill jest zainstalowany."""
    if not INSTALLED:
        return REQUIRED
    talos, pdi = (ROOT / TALOS).is_dir(), (ROOT / PDI).is_dir()
    return [c for c in REQUIRED if (PDI in c and pdi) or (PDI not in c and talos)]


def main() -> int:
    if ROOT is None:
        print("✗ brak katalogu głównego z core/settings.json i modes/mode-talos/")
        return 1
    cmds = required()
    if not cmds:
        print("– pomijam: w projekcie nie ma skilli talos-story-run ani pdi-decisions (mode-talos, mode-pdi) — "
              "nie ma czego sprawdzać; pełne sprawdzenie w przestrzeni fabryki (tools/workspace.py check)")
        return 0
    allow = load_allow()
    patterns = [to_regex(p) for p in bash_patterns(allow)]
    fails: list[str] = []
    for cmd in cmds:
        if not covers(cmd, patterns):
            fails.append(f"polecenie Bash bez reguły allow: {cmd!r}")
    # SKILL.md Talosa wymienia polecenia skryptów — sprawdź, że każdy z nich ma dopuszczenie prefiksowe.
    # W zainstalowanym projekcie pomijamy skrypty skilli spoza instalacji (np. requirements_lint.py z pack-it).
    skill = skill_path()
    text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
    script_calls = set(re.findall(r"python3 \.claude/skills/[^\s`]+\.py", text))
    if INSTALLED:
        script_calls = {c for c in script_calls if (ROOT / c.split(" ", 1)[1]).is_file()}
    # każdy skrypt skilla Talosa (scripts/*.py) ma regułę allow
    scripts_dir = skill.parent / "scripts"
    script_calls |= {f"python3 {TALOS}scripts/{p.name}" for p in sorted(scripts_dir.glob("*.py"))} \
        if skill.is_file() else set()
    for call in sorted(script_calls):
        if not covers(f"{call} --test", patterns):
            fails.append(f"skrypt Talosa (SKILL.md lub scripts/) bez reguły allow: {call}")
    for f in fails:
        print(f"✗ {f}")
    total = len(cmds) + len(script_calls)
    where = "zainstalowane .claude/settings*.json" if INSTALLED else "core + nakładki"
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} poleceń Bash pokrytych przez allow ({where})")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
