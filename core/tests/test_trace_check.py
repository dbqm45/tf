#!/usr/bin/env python3
"""Testy śladu kryterium → test → commit → dowód (.tf/factory/trace_check.py, `tf trace <KEY>`).
python3 .claude/tests/test_trace_check.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPT = ROOT / ".tf" / "factory" / "trace_check.py"
TASK = ROOT / ".tf" / "factory" / "task_state.py"
CTF = ROOT / ".tf" / "factory" / "tf.py"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'2 passed\')"'
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi 45 zł.\n"
        "- AC-2: Zakładając postój 30 minut, gdy kierowca płaci, wtedy opłata wynosi 0 zł.\n"
        "\n## Bez zmian\n\n- Stawka godzinowa.\n\n## Poza zakresem\n\n- Abonamenty.\n")


def run(project: Path, script: Path, *args: str):
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args], cwd=repo,
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


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
        p = Path(t) / "repo"
        p.mkdir()
        git(p, "init", "-q", "-b", "main")
        write(p, "src/fees.py", "LIMIT = 40\n")
        write(p, "tests/test_old.py", "def test_old():  # AC-7 z dawnego zadania\n    assert True\n")
        git(p, "add", "-A")
        git(p, "commit", "-qm", "init")
        git(p, "checkout", "-qb", "story/limit")
        run(p, TASK, "start", "PROJ-1", "--title", "Limit dobowy")
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0 and "spec.md" in r.stdout, f"TR-1: zadanie bez specyfikacji → kod 0 z informacją: {r.returncode} {r.stdout}")
        write(p, f"{CHANGES.as_posix()}/PROJ-1/spec.md", SPEC)
        write(p, "src/fees.py", "LIMIT = 45  # AC-2 w komentarzu kodu to nie test\n")
        write(p, "tests/test_fees.py", "def test_ac1_limit_dobowy():  # AC-1\n    assert True\n")
        git(p, "add", "-A")
        git(p, "commit", "-qm", "feat: limit")
        sha1 = git(p, "rev-parse", "--short", "HEAD")
        write(p, ".tf/logs/tdd-red.jsonl", json.dumps({"at": "2026-11-13T10:00:00+00:00", "tests": ["tests/test_fees.py"],
                                                       "command": "pytest"}) + "\n")
        run(p, TASK, "verify", "PROJ-1", "K1", "--files", "src/fees.py,tests/test_fees.py", "--command", OK)
        ev = json.loads((p / CHANGES / "PROJ-1" / "evidence" / "K1-1.json").read_text(encoding="utf-8"))
        check(ev.get("red_tests") == {"tests/test_fees.py": "2026-11-13T10:00:00+00:00"},
              f"TR-15: dowód kawałka niesie zapis czerwonego testu z dziennika hooka TDD: {ev.get('red_tests')}")

        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 1 and "TRACE-001" in r.stdout and "AC-2" in r.stdout and "AC-7" not in r.stdout,
              f"TR-2: kryterium bez testu → TRACE-001; komentarz w kodzie i stary test spoza gałęzi się nie liczą: {r.stdout}{r.stderr}")
        r = run(p, TASK, "stage", "PROJ-1", "przeglad")
        check(r.returncode == 1 and "AC-2" in r.stdout and "tf trace PROJ-1" in r.stdout,
              f"TR-3: etap przeglad odrzucony, gdy kryterium nie ma testu: {r.returncode} {r.stdout}")

        write(p, "tests/test_free.py", "def test_ac2_pierwsze_pol_godziny():  # AC-2\n    assert True\n\n"
                                        "def test_ac9_cos_innego():  # AC-9\n    assert True\n")
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 1 and "TRACE-002" in r.stdout and "AC-9" in r.stdout and "TRACE-001" not in r.stdout,
              f"TR-4: test wskazuje kryterium spoza specyfikacji → TRACE-002: {r.stdout}")
        write(p, "tests/test_free.py", "def test_ac2_pierwsze_pol_godziny():  # AC-2\n    assert True\n")
        r = run(p, SCRIPT, "PROJ-1", "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        rows = {x["criterion"]: x for x in data.get("rows", [])}
        check(r.returncode == 0 and data.get("ok") is True
              and rows.get("AC-1", {}).get("tests") == ["tests/test_fees.py:1"] and rows["AC-1"].get("commit") == sha1
              and rows["AC-1"].get("slice") == "K1" and rows["AC-1"].get("evidence") == "zweryfikowany",
              f"TR-5: pełny ślad AC-1: test, commit, kawałek, stan dowodu: {r.stdout[:400]}{r.stderr}")
        check(rows.get("AC-1", {}).get("red") is True and rows.get("AC-2", {}).get("red") is False,
              f"TR-16: ślad mówi, czy test był widziany jako czerwony: {rows.get('AC-1')} {rows.get('AC-2')}")
        check(rows.get("AC-2", {}).get("commit") is None and rows.get("AC-2", {}).get("evidence") == "bez dowodu"
              and any(w.get("rule") == "TRACE-003" for w in data.get("warnings", [])),
              f"TR-6: test niezacommitowany i poza plikami kawałka → ostrzeżenie TRACE-003, bez błędu: {rows.get('AC-2')} {data.get('warnings')}")

        git(p, "add", "-A")
        git(p, "commit", "-qm", "test: free")
        sha2 = git(p, "rev-parse", "--short", "HEAD")
        run(p, TASK, "verify", "PROJ-1", "K2", "--files", "tests/test_free.py", "--command", OK)
        r = run(p, SCRIPT, "PROJ-1", "--md")
        lines = [ln for ln in r.stdout.splitlines() if ln.startswith("| AC-")]
        check("Czerwony przed kodem" in r.stdout and "| tak |" in lines[0] and "brak zapisu" in lines[1],
              f"TR-17: tabela ma kolumnę „Czerwony przed kodem”: {r.stdout}")
        check(r.returncode == 0 and len(lines) == 2 and sha1 in lines[0] and "K1" in lines[0] and "zweryfikowany" in lines[0]
              and sha2 in lines[1] and "tests/test_free.py" in lines[1] and "K2" in lines[1],
              f"TR-7: --md daje tabelę kryterium → test → commit → dowód: {r.stdout}")
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0 and "2/2" in r.stdout, f"TR-8: tekst: wszystkie kryteria mają test: {r.stdout}")
        r = run(p, TASK, "stage", "PROJ-1", "przeglad")
        check(r.returncode == 0, f"TR-9: z pełnym śladem etap przeglad przechodzi: {r.stdout}{r.stderr}")

        write(p, "src/fees.py", "LIMIT = 46\n")
        r = run(p, SCRIPT, "PROJ-1", "--json")
        rows = {x["criterion"]: x for x in json.loads(r.stdout).get("rows", [])} if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and rows.get("AC-1", {}).get("evidence") == "niezweryfikowany",
              f"TR-10: plik kawałka zmieniony po dowodzie widać w śladzie: {rows.get('AC-1')}")
        r = run(p, SCRIPT, "PROJ-1", "--base", "nie-ma-takiej")
        check(r.returncode == 2, f"TR-11: nieznana baza → kod 2: {r.returncode} {r.stdout}")

        (p / ".tf" / "factory").mkdir(parents=True)
        (p / ".claude").mkdir(exist_ok=True)
        (p / ".claude" / "factory-manifest.json").write_text("{}", encoding="utf-8")
        for name in ("trace_check.py", "spec_check.py", "task_state.py"):
            shutil.copy(SCRIPT.with_name(name), p / ".tf" / "factory" / name)
        r = subprocess.run([sys.executable, str(CTF), "trace", "PROJ-1"], cwd=p, capture_output=True, text=True, timeout=60,
                           env={**os.environ, "CLAUDE_PROJECT_DIR": str(p)})
        check(r.returncode == 0 and "AC-1" in r.stdout, f"TR-12: tf trace: {r.returncode} {r.stdout}{r.stderr}")

    with tempfile.TemporaryDirectory() as t:      # poza gitem: śladu nie da się policzyć, bramka etapu go nie wymaga
        p = Path(t)
        run(p, TASK, "start", "PROJ-2", "--title", "Bez gita")
        write(p, f"{CHANGES.as_posix()}/PROJ-2/spec.md", SPEC)
        r = run(p, SCRIPT, "PROJ-2")
        check(r.returncode == 2 and "git" in r.stdout, f"TR-13: poza repozytorium git → kod 2 z wyjaśnieniem: {r.returncode} {r.stdout}")
        r = run(p, TASK, "stage", "PROJ-2", "przeglad")
        check(r.returncode == 0, f"TR-14: bez gita bramka śladu nie blokuje etapu: {r.returncode} {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów śladu kryteriów")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
