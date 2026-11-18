#!/usr/bin/env python3
"""Task spec check tests (.tf/factory/spec_check.py, the `tf spec new|check` commands).
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
        print(f"✗ missing {SCRIPT}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        run(p, TASK, "start", "PROJ-1", "--title", "Limit dobowy")
        spec = p / CHANGES / "PROJ-1" / "spec.md"

        def verdict(text: str, *extra: str):
            spec.write_text(text, encoding="utf-8")
            return run(p, SCRIPT, "check", "PROJ-1", *extra)

        r = run(p, SCRIPT, "check", "PROJ-1")
        check(r.returncode == 2 and "spec.md" in r.stdout, f"SP-1: no file → code 2 with the file name: {r.returncode} {r.stdout}")
        r = verdict(GOOD)
        check(r.returncode == 0 and "2" in r.stdout, f"SP-2: a valid spec in Polish → code 0, number of criteria: {r.stdout}{r.stderr}")
        r = verdict(GOOD_EN)
        check(r.returncode == 0, f"SP-3: in English, a criterion over three lines, “none, because…”: {r.stdout}{r.stderr}")

        r = verdict(GOOD.replace(", wtedy opłata wynosi 45 zł", ""))
        check(r.returncode == 1 and "SPEC-002" in r.stdout and "AC-1" in r.stdout and "5" in r.stdout,
              f"SP-4: a criterion without Wtedy → SPEC-002 with the identifier and line number: {r.stdout}")
        r = verdict(GOOD.replace("- AC-2:", "- AC-1:"))
        check(r.returncode == 1 and "SPEC-003" in r.stdout, f"SP-5: a repeated identifier → SPEC-003: {r.stdout}")
        r = verdict(GOOD.replace("gdy kierowca płaci, wtedy opłata wynosi", "gdy kierowca płaci i gdy wyjeżdża, wtedy opłata wynosi"))
        check(r.returncode == 1 and "SPEC-004" in r.stdout, f"SP-6: two “gdy” in a criterion → SPEC-004: {r.stdout}")
        r = verdict(GOOD.replace("- Pierwsze 30 minut jest bezpłatne.\n", ""))
        check(r.returncode == 1 and "SPEC-005" in r.stdout and "Unchanged" in r.stdout, f"SP-7: an empty section → SPEC-005 with the name: {r.stdout}")
        r = verdict(GOOD.replace("## Poza zakresem\n\n- Abonamenty.\n\n", ""))
        check(r.returncode == 1 and "SPEC-005" in r.stdout and "Out of scope" in r.stdout, f"SP-8: a missing section → SPEC-005: {r.stdout}")
        r = verdict(GOOD.replace("- Abonamenty.", "- brak"))
        check(r.returncode == 1 and "SPEC-005" in r.stdout, f"SP-9: a bare “brak” without a reason → SPEC-005: {r.stdout}")
        r = verdict(GOOD.replace("- Abonamenty.", "- brak, bo historyjka zmienia tylko wartość limitu"))
        check(r.returncode == 0, f"SP-10: “brak, bo …” passes: {r.stdout}")
        r = verdict(GOOD.replace("- Czy limit dotyczy też motocykli?", "- [blokuje] Czy limit dotyczy też motocykli?"))
        check(r.returncode == 1 and "SPEC-006" in r.stdout, f"SP-11: a blocking question → SPEC-006: {r.stdout}")
        r = verdict(GOOD.replace("## Kryteria", "## Kryteria\n\nTu nic nie ma.").replace("- AC-1:", "- ").replace("- AC-2:", "- "))
        check(r.returncode == 1 and "SPEC-001" in r.stdout, f"SP-12: no AC-n criteria → SPEC-001: {r.stdout}")
        # content rules in the core (without the pack-it overlay): an unverifiable outcome and a second action
        r = verdict(GOOD.replace("wtedy opłata wynosi 45 zł", "wtedy system działa poprawnie"))
        check(r.returncode == 1 and "SPEC-008" in r.stdout and "AC-1" in r.stdout and "poprawnie" in r.stdout,
              f"SP-24: a weak outcome (“działa poprawnie”) → SPEC-008 with the word: {r.stdout}")
        r = verdict(GOOD.replace("wtedy opłata wynosi 45 zł", "wtedy opłata 45 zł jest naliczona poprawnie"))
        check(r.returncode == 0, f"SP-25: an outcome with a concrete value passes despite the word “poprawnie”: {r.stdout}")
        r = verdict(GOOD_EN.replace("Then the fee is 45 PLN", "Then everything works as expected"))
        check(r.returncode == 1 and "SPEC-008" in r.stdout, f"SP-26: a weak outcome in English → SPEC-008: {r.stdout}")
        r = verdict(GOOD.replace("gdy kierowca płaci, wtedy opłata wynosi", "gdy kierowca płaci, a następnie wyjeżdża, wtedy opłata wynosi"))
        check(r.returncode == 1 and "SPEC-004" in r.stdout, f"SP-27: “a następnie” in the Gdy part is a second action → SPEC-004: {r.stdout}")
        mixed = (GOOD.replace("# Specyfikacja:", "# Spec:").replace("## Kryteria", "## Acceptance criteria")
                 .replace("## Bez zmian", "## Unchanged").replace("## Poza zakresem", "## Out of scope")
                 .replace("## Otwarte pytania", "## Open questions").replace("Zakładając", "Given")
                 .replace(", gdy", ", when").replace(", wtedy", ", then"))
        r = verdict(mixed)
        check(r.returncode == 0, f"SP-30: English syntax with Polish content (after the 14.0.0 migration) passes: {r.stdout}")
        r = verdict(mixed.replace("- Czy limit", "- [blocking] Czy limit"))
        check(r.returncode == 1 and "SPEC-006" in r.stdout, f"SP-31: znacznik [blocking] blokuje start: {r.stdout}")
        r = verdict(GOOD.replace("Zakładając postój 12 godzin, gdy", "Zakładając postój 12 godzin oraz kartę mieszkańca, gdy"))
        check(r.returncode == 0, f"SP-28: a conjunction in the Zakładając part is not a second action: {r.stdout}")
        # SPEC-009: a warning (not an error) when no criterion describes disallowed behaviour
        r = verdict(GOOD)
        check(r.returncode == 0 and "SPEC-009" in r.stdout and "⚠" in r.stdout,
              f"SP-29: only positive criteria → warning SPEC-009, code 0: {r.stdout}")
        NEG = GOOD.replace("\n\n## Bez zmian", "\n- AC-3: Zakładając nieopłacony postój, gdy kierowca podjeżdża do wyjazdu, "
                           "wtedy szlaban się nie otwiera.\n\n## Bez zmian")
        r = verdict(NEG)
        check(r.returncode == 0 and "SPEC-009" not in r.stdout, f"SP-30: a negative criterion (“nie otwiera”) → no warning: {r.stdout}")
        r = verdict(NEG.replace("wtedy szlaban się nie otwiera", "wtedy system odmawia wyjazdu z komunikatem „Opłać postój”"))
        check(r.returncode == 0 and "SPEC-009" not in r.stdout, f"SP-31: a refusal as the outcome → no warning: {r.stdout}")
        r = verdict(GOOD_EN.replace("Then the fee is 45 PLN", "Then the fee is 45 PLN\n\n### AC-2\nGiven an unpaid stay\n"
                                    "When the driver reaches the exit\nThen the barrier does not open"))
        check(r.returncode == 0 and "SPEC-009" not in r.stdout, f"SP-32: a negative in English (“does not”) → no warning: {r.stdout}")
        r = verdict(GOOD, "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        check(data.get("ok") is True and [w.get("rule") for w in data.get("warnings", [])] == ["SPEC-009"],
              f"SP-33: --json: the warning in the warnings field, ok unchanged: {r.stdout[:300]}")
        r = verdict(GOOD, "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        check(data.get("ok") is True and data.get("criteria") == ["AC-1", "AC-2"] and data.get("errors") == [],
              f"SP-13: --json: ok, the list of criteria, errors: {r.stdout[:200]}")

        # template: `new` creates a file with the task title, does not overwrite, and an unfilled template does not pass
        spec.unlink()
        r = run(p, SCRIPT, "new", "PROJ-1")
        text = spec.read_text(encoding="utf-8") if spec.is_file() else ""
        check(r.returncode == 0 and "Limit dobowy" in text and "AC-1" in text, f"SP-14: new creates spec.md with the task title: {r.stdout}{r.stderr}")
        check("negative" in text, f"SP-34: the template suggests a negative criterion: {text[:400]}")
        r = run(p, SCRIPT, "check", "PROJ-1")
        check(r.returncode == 1 and "SPEC-007" in r.stdout, f"SP-15: an unfilled template → SPEC-007: {r.stdout}")
        r = run(p, SCRIPT, "new", "PROJ-1")
        check(r.returncode == 1 and spec.read_text(encoding="utf-8") == text, f"SP-16: new does not overwrite an existing file: {r.returncode}")
        r = run(p, SCRIPT, "new", "PROJ-404")
        check(r.returncode == 1 and not (p / CHANGES / "PROJ-404").exists(), f"SP-17: new without a task → refusal: {r.returncode} {r.stdout}")

        # stage gate: with an invalid spec the task does not enter the plan stage; after the fix it does
        r = run(p, TASK, "stage", "PROJ-1", "plan")
        check(r.returncode == 1 and "SPEC-007" in r.stdout and "tf spec check PROJ-1" in r.stdout,
              f"SP-18: the plan stage rejected on spec errors: {r.returncode} {r.stdout}")
        r = run(p, TASK, "stage", "PROJ-1", "spec")
        check(r.returncode == 0, f"SP-19: the spec stage can be entered with an unfinished file: {r.stdout}")
        spec.write_text(GOOD, encoding="utf-8")
        r = run(p, TASK, "stage", "PROJ-1", "plan")
        check(r.returncode == 0, f"SP-20: after the fix the plan stage passes: {r.stdout}{r.stderr}")
        run(p, TASK, "start", "PROJ-2", "--title", "Bez specyfikacji")
        r = run(p, TASK, "stage", "PROJ-2", "implementation")
        check(r.returncode == 0, f"SP-21: a task without spec.md works as before: {r.stdout}")
        spec.write_text(GOOD.replace(", wtedy opłata wynosi 45 zł", ""), encoding="utf-8")
        r = run(p, TASK, "stage", "PROJ-1", "implementation", "--force")
        check(r.returncode == 0, f"SP-22: --force skips the spec gate: {r.stdout}")

        # via `tf`: a project with the engine in .tf/factory/ and an install manifest
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
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} task spec tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
