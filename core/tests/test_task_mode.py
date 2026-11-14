#!/usr/bin/env python3
"""Testy trybu zadania (`tf task mode`): Plan / zwykły / Auto i wejście do etapu realizacji.
python3 .claude/tests/test_task_mode.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
CHANGES = Path("docs") / "project" / "changes"


def tf(project: Path, *args: str):
    return subprocess.run([sys.executable, str(TASK), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def task(project: Path, key: str) -> dict:
    return json.loads((project / CHANGES / key / "task.json").read_text(encoding="utf-8"))


def new_task(project: Path, key: str, plan: bool = True) -> Path:
    tf(project, "start", key, "--title", "Eksport sesji")
    folder = project / CHANGES / key
    (folder / "ticket.md").write_text("# Eksport sesji\n\nJako operator chcę eksport sesji do pliku.\n", encoding="utf-8")
    if plan:
        (folder / "plan.md").write_text("# Plan\n- [ ] K1 — eksport · pliki: export.py\n", encoding="utf-8")
        tf(project, "artifact", key, "plan.md", "--stage", "plan", "--by", "process:tf", "--inputs", "ticket.md")
    return folder


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        new_task(p, "A-1")
        r = tf(p, "mode", "A-1")
        check(r.returncode == 0 and "zwykły" in r.stdout, f"M-1: tryb domyślny to zwykły: {r.stdout}{r.stderr}")

        # tryb Plan: przebieg kończy się na planie
        r = tf(p, "mode", "A-1", "plan")
        check(r.returncode == 0 and task(p, "A-1").get("mode") == "plan", f"M-2: ustawienie trybu Plan: {r.stdout}")
        r = tf(p, "stage", "A-1", "plan")
        check(r.returncode == 0, f"M-3: w trybie Plan zadanie dochodzi do etapu plan: {r.stdout}")
        r = tf(p, "stage", "A-1", "realizacja")
        check(r.returncode == 1 and "tryb" in r.stdout and "Plan" in r.stdout and "mode A-1 zwykly" in r.stdout,
              f"M-4: tryb Plan nie wchodzi w realizację; komunikat mówi, jak kontynuować: {r.returncode} {r.stdout}")

        # tryb zwykły: zarejestrowany plan wymaga zgody człowieka
        tf(p, "mode", "A-1", "zwykly")
        r = tf(p, "stage", "A-1", "realizacja")
        check(r.returncode == 1 and "approve A-1 plan.md" in r.stdout and "--auto" in r.stdout,
              f"M-5: tryb zwykły — realizacja dopiero po zgodzie człowieka na plan: {r.returncode} {r.stdout}")
        tf(p, "approve", "A-1", "plan.md", "--by", "human:anna")
        r = tf(p, "stage", "A-1", "realizacja")
        check(r.returncode == 0, f"M-6: po zgodzie realizacja przechodzi: {r.stdout}")

        # zadanie prowadzone ręcznie (bez zarejestrowanego planu) działa jak dotąd
        new_task(p, "A-2", plan=False)
        r = tf(p, "stage", "A-2", "realizacja")
        check(r.returncode == 0, f"M-7: bez zarejestrowanego planu tryb zwykły nie wymaga zgody: {r.stdout}")

        # tryb Auto: bez zgody, chyba że waga pełna
        new_task(p, "A-3")
        r = tf(p, "mode", "A-3", "auto")
        r2 = tf(p, "stage", "A-3", "realizacja")
        check(r.returncode == 0 and task(p, "A-3").get("mode") == "auto" and r2.returncode == 0,
              f"M-8: tryb Auto wchodzi w realizację bez zgody: {r.stdout} | {r2.stdout}")
        new_task(p, "A-4")
        tf(p, "weight", "A-4", "--set", "pelna")
        r = tf(p, "mode", "A-4", "auto")
        check(r.returncode == 0 and task(p, "A-4").get("mode") == "zwykly" and "pełn" in r.stdout and "zwykły" in r.stdout,
              f"M-9: Auto przy wadze pełnej niedostępne — zostaje tryb zwykły z wyjaśnieniem: {r.returncode} {r.stdout}")
        new_task(p, "A-5")
        tf(p, "mode", "A-5", "auto")
        tf(p, "weight", "A-5", "--set", "pelna")
        r = tf(p, "stage", "A-5", "realizacja")
        check(r.returncode == 1 and "approve A-5 plan.md" in r.stdout,
              f"M-10: waga podniesiona do pełnej w trybie Auto — realizacja czeka na człowieka: {r.returncode} {r.stdout}")

        r = tf(p, "mode", "A-1", "turbo")
        check(r.returncode == 2, f"M-11: nieznany tryb → kod 2: {r.returncode} {r.stdout}")
        r = tf(p, "status", "A-3")
        check("tryb: auto" in r.stdout, f"M-12: status pokazuje tryb: {r.stdout}")
        new_task(p, "A-6")
        tf(p, "mode", "A-6", "plan")
        r = tf(p, "stage", "A-6", "realizacja", "--force")
        check(r.returncode == 0, f"M-13: --force omija bramkę trybu: {r.stdout}")
        r = tf(p, "mode", "NIE-1")
        check(r.returncode != 0 and "Traceback" not in r.stderr, f"M-14: brak zadania → błąd bez wyjątku: {r.returncode}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów trybu zadania")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
