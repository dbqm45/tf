#!/usr/bin/env python3
"""Testy sprawdzania specyfikacji zadania (.tf/factory/spec_check.py, polecenia `tf spec new|check`).
python3 .claude/tests/test_spec_check.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPT = ROOT / ".tf" / "factory" / "spec_check.py"
TASK = ROOT / ".tf" / "factory" / "task_state.py"
CTF = ROOT / ".tf" / "factory" / "tf.py"
CHANGES = Path("docs") / "project" / "changes"

GOOD = """# Specyfikacja: Limit dobowy

## Kryteria

- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi 45 zł.
- AC-2: Zakładając postój 25 godzin i 1 minutę, gdy kierowca płaci, wtedy opłata to 45 zł i stawka za drugą dobę.

## Bez zmian

- Pierwsze 30 minut jest bezpłatne.

## Poza zakresem

- Abonamenty.

## Otwarte pytania

- Czy limit dotyczy też motocykli?
"""
GOOD_EN = """# Specification: Daily cap

## Acceptance criteria

### AC-1
Given a 12-hour stay
When the driver pays
Then the fee is 45 PLN

## Unchanged

- The first 30 minutes are free.

## Out of scope

- none, because the story only changes the cap value

## Open questions
"""


def run(project: Path, script: Path, *args: str):
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not SCRIPT.is_file():
        print(f"✗ brak {SCRIPT}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        run(p, TASK, "start", "PROJ-1", "--title", "Limit dobowy")
        spec = p / CHANGES / "PROJ-1" / "spec.md"

        def verdict(text: str, *extra: str):
            spec.write_text(text, encoding="utf-8")
            return run(p, SCRIPT, "check", "PROJ-1", *extra)

        r = run(p, SCRIPT, "check", "PROJ-1")
        check(r.returncode == 2 and "spec.md" in r.stdout, f"SP-1: brak pliku → kod 2 z nazwą pliku: {r.returncode} {r.stdout}")
        r = verdict(GOOD)
        check(r.returncode == 0 and "2" in r.stdout, f"SP-2: poprawna specyfikacja po polsku → kod 0, liczba kryteriów: {r.stdout}{r.stderr}")
        r = verdict(GOOD_EN)
        check(r.returncode == 0, f"SP-3: po angielsku, kryterium w trzech liniach, „none, because…”: {r.stdout}{r.stderr}")

        r = verdict(GOOD.replace(", wtedy opłata wynosi 45 zł", ""))
        check(r.returncode == 1 and "SPEC-002" in r.stdout and "AC-1" in r.stdout and "5" in r.stdout,
              f"SP-4: kryterium bez Wtedy → SPEC-002 z identyfikatorem i numerem linii: {r.stdout}")
        r = verdict(GOOD.replace("- AC-2:", "- AC-1:"))
        check(r.returncode == 1 and "SPEC-003" in r.stdout, f"SP-5: powtórzony identyfikator → SPEC-003: {r.stdout}")
        r = verdict(GOOD.replace("gdy kierowca płaci, wtedy opłata wynosi", "gdy kierowca płaci i gdy wyjeżdża, wtedy opłata wynosi"))
        check(r.returncode == 1 and "SPEC-004" in r.stdout, f"SP-6: dwa „gdy” w kryterium → SPEC-004: {r.stdout}")
        r = verdict(GOOD.replace("- Pierwsze 30 minut jest bezpłatne.\n", ""))
        check(r.returncode == 1 and "SPEC-005" in r.stdout and "Bez zmian" in r.stdout, f"SP-7: pusta sekcja → SPEC-005 z nazwą: {r.stdout}")
        r = verdict(GOOD.replace("## Poza zakresem\n\n- Abonamenty.\n\n", ""))
        check(r.returncode == 1 and "SPEC-005" in r.stdout and "Poza zakresem" in r.stdout, f"SP-8: brak sekcji → SPEC-005: {r.stdout}")
        r = verdict(GOOD.replace("- Abonamenty.", "- brak"))
        check(r.returncode == 1 and "SPEC-005" in r.stdout, f"SP-9: samo „brak” bez powodu → SPEC-005: {r.stdout}")
        r = verdict(GOOD.replace("- Abonamenty.", "- brak, bo historyjka zmienia tylko wartość limitu"))
        check(r.returncode == 0, f"SP-10: „brak, bo …” przechodzi: {r.stdout}")
        r = verdict(GOOD.replace("- Czy limit dotyczy też motocykli?", "- [blokuje] Czy limit dotyczy też motocykli?"))
        check(r.returncode == 1 and "SPEC-006" in r.stdout, f"SP-11: pytanie blokujące → SPEC-006: {r.stdout}")
        r = verdict(GOOD.replace("## Kryteria", "## Kryteria\n\nTu nic nie ma.").replace("- AC-1:", "- ").replace("- AC-2:", "- "))
        check(r.returncode == 1 and "SPEC-001" in r.stdout, f"SP-12: brak kryteriów AC-n → SPEC-001: {r.stdout}")
        # reguły treści w rdzeniu (bez nakładki pack-it): wynik, którego nie da się sprawdzić, i druga akcja
        r = verdict(GOOD.replace("wtedy opłata wynosi 45 zł", "wtedy system działa poprawnie"))
        check(r.returncode == 1 and "SPEC-008" in r.stdout and "AC-1" in r.stdout and "poprawnie" in r.stdout,
              f"SP-24: słaby wynik („działa poprawnie”) → SPEC-008 ze słowem: {r.stdout}")
        r = verdict(GOOD.replace("wtedy opłata wynosi 45 zł", "wtedy opłata 45 zł jest naliczona poprawnie"))
        check(r.returncode == 0, f"SP-25: wynik z konkretną wartością przechodzi mimo słowa „poprawnie”: {r.stdout}")
        r = verdict(GOOD_EN.replace("Then the fee is 45 PLN", "Then everything works as expected"))
        check(r.returncode == 1 and "SPEC-008" in r.stdout, f"SP-26: słaby wynik po angielsku → SPEC-008: {r.stdout}")
        r = verdict(GOOD.replace("gdy kierowca płaci, wtedy opłata wynosi", "gdy kierowca płaci, a następnie wyjeżdża, wtedy opłata wynosi"))
        check(r.returncode == 1 and "SPEC-004" in r.stdout, f"SP-27: „a następnie” w części Gdy to druga akcja → SPEC-004: {r.stdout}")
        r = verdict(GOOD.replace("Zakładając postój 12 godzin, gdy", "Zakładając postój 12 godzin oraz kartę mieszkańca, gdy"))
        check(r.returncode == 0, f"SP-28: spójnik w części Zakładając nie jest drugą akcją: {r.stdout}")
        r = verdict(GOOD, "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        check(data.get("ok") is True and data.get("criteria") == ["AC-1", "AC-2"] and data.get("errors") == [],
              f"SP-13: --json: ok, lista kryteriów, błędy: {r.stdout[:200]}")

        # szablon: `new` zakłada plik z tytułem zadania, nie nadpisuje, a niewypełniony szablon nie przechodzi
        spec.unlink()
        r = run(p, SCRIPT, "new", "PROJ-1")
        text = spec.read_text(encoding="utf-8") if spec.is_file() else ""
        check(r.returncode == 0 and "Limit dobowy" in text and "AC-1" in text, f"SP-14: new zakłada spec.md z tytułem zadania: {r.stdout}{r.stderr}")
        r = run(p, SCRIPT, "check", "PROJ-1")
        check(r.returncode == 1 and "SPEC-007" in r.stdout, f"SP-15: niewypełniony szablon → SPEC-007: {r.stdout}")
        r = run(p, SCRIPT, "new", "PROJ-1")
        check(r.returncode == 1 and spec.read_text(encoding="utf-8") == text, f"SP-16: new nie nadpisuje istniejącego pliku: {r.returncode}")
        r = run(p, SCRIPT, "new", "PROJ-404")
        check(r.returncode == 1 and not (p / CHANGES / "PROJ-404").exists(), f"SP-17: new bez zadania → odmowa: {r.returncode} {r.stdout}")

        # bramka etapu: z niepoprawną specyfikacją zadanie nie wchodzi do etapu plan; po poprawce wchodzi
        r = run(p, TASK, "stage", "PROJ-1", "plan")
        check(r.returncode == 1 and "SPEC-007" in r.stdout and "tf spec check PROJ-1" in r.stdout,
              f"SP-18: etap plan odrzucony przy błędach specyfikacji: {r.returncode} {r.stdout}")
        r = run(p, TASK, "stage", "PROJ-1", "specyfikacja")
        check(r.returncode == 0, f"SP-19: do etapu specyfikacja wchodzi się z niegotowym plikiem: {r.stdout}")
        spec.write_text(GOOD, encoding="utf-8")
        r = run(p, TASK, "stage", "PROJ-1", "plan")
        check(r.returncode == 0, f"SP-20: po poprawce etap plan przechodzi: {r.stdout}{r.stderr}")
        run(p, TASK, "start", "PROJ-2", "--title", "Bez specyfikacji")
        r = run(p, TASK, "stage", "PROJ-2", "realizacja")
        check(r.returncode == 0, f"SP-21: zadanie bez spec.md działa jak dotąd: {r.stdout}")
        spec.write_text(GOOD.replace(", wtedy opłata wynosi 45 zł", ""), encoding="utf-8")
        r = run(p, TASK, "stage", "PROJ-1", "realizacja", "--force")
        check(r.returncode == 0, f"SP-22: --force pomija bramkę specyfikacji: {r.stdout}")

        # przez `tf`: projekt z silnikiem w .tf/factory/ i manifestem instalacji
        (p / ".tf" / "factory").mkdir(parents=True)
        (p / ".claude").mkdir()
        (p / ".claude" / "factory-manifest.json").write_text("{}", encoding="utf-8")
        for name in ("spec_check.py", "task_state.py"):
            shutil.copy(SCRIPT.with_name(name), p / ".tf" / "factory" / name)
        r = subprocess.run([sys.executable, str(CTF), "spec", "check", "PROJ-1"], cwd=p, capture_output=True, text=True,
                           timeout=60, env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        check(r.returncode == 1 and "SPEC-002" in r.stdout, f"SP-23: tf spec check: {r.returncode} {r.stdout}{r.stderr}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów specyfikacji zadania")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
