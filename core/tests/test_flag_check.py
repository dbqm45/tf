#!/usr/bin/env python3
"""Testy flagi funkcji na zadanie (`tf task flag`, .tf/factory/flag_check.py, karta operacyjna z `tf onboard`).
python3 .claude/tests/test_flag_check.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPT = ROOT / ".tf" / "factory" / "flag_check.py"
TASK = ROOT / ".tf" / "factory" / "task_state.py"
ONBOARD = ROOT / ".tf" / "factory" / "onboard.py"
CHANGES = Path("docs") / "project" / "changes"
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi 45 zł.\n"
        "\n## Bez zmian\n\n- Stawka godzinowa.\n\n## Poza zakresem\n\n- Abonamenty.\n")
CARD = {"flags": {"file": "config/flags.json", "envs": ["test", "qa", "prod"], "test_env": "test"}}


def run(project: Path, script: Path, *args: str):
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                          cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


def flags(repo: Path, **states) -> None:
    """config/flags.json w układzie środowisko → flaga → stan."""
    write(repo, "config/flags.json", json.dumps({env: {"proj_1_limit": on, "inna": False} for env, on in states.items()}, indent=1))


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
        flags(p, test=False, qa=False, prod=False)
        write(p, "src/fees.py", "LIMIT = 40\n")
        git(p, "add", "-A")
        git(p, "commit", "-qm", "init")
        git(p, "checkout", "-qb", "story/limit")
        run(p, TASK, "start", "PROJ-1", "--title", "Limit dobowy")
        task_file = p / CHANGES / "PROJ-1" / "task.json"

        def task() -> dict:
            return json.loads(task_file.read_text(encoding="utf-8"))

        # flaga zadania: klucz z datą usunięcia albo jawne „bez flagi, bo…”
        r = run(p, TASK, "flag", "PROJ-1", "none")
        check(r.returncode == 2 and "--reason" in r.stdout, f"F-1: „bez flagi” wymaga powodu: {r.returncode} {r.stdout}")
        r = run(p, TASK, "flag", "PROJ-1", "set", "proj_1_limit", "--remove-by", "2027-01-31")
        f = task().get("flag", {})
        check(r.returncode == 0 and f.get("key") == "proj_1_limit" and f.get("remove_by") == "2027-01-31",
              f"F-2: flag set zapisuje klucz i datę usunięcia: {r.stdout} {f}")
        r = run(p, TASK, "flag", "PROJ-1", "set", "proj_1_limit", "--remove-by", "kiedyś")
        check(r.returncode == 2, f"F-3: data usunięcia w formacie RRRR-MM-DD: {r.returncode} {r.stdout}")
        r = run(p, TASK, "status", "PROJ-1")
        check("proj_1_limit" in r.stdout and "2027-01-31" in r.stdout, f"F-4: status pokazuje flagę: {r.stdout}")

        # kontrola diffu konfiguracji flag: bez karty operacyjnej skrypt mówi, że sprawdzić trzeba ręcznie
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0 and "ręcznie" in r.stdout and "operations.json" in r.stdout,
              f"F-5: brak karty → informacja „sprawdź ręcznie”, kod 0: {r.returncode} {r.stdout}")
        write(p, ".tf/config/operations.json", json.dumps(CARD))
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0 and "proj_1_limit" in r.stdout, f"F-6: flaga wyłączona wszędzie → kod 0: {r.stdout}{r.stderr}")
        flags(p, test=True, qa=False, prod=False)
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0, f"F-7: włączenie na środowisku testowym → kod 0: {r.stdout}")
        flags(p, test=True, qa=False, prod=True)
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 1 and "FLAG-001" in r.stdout and "prod" in r.stdout and "tf task flag PROJ-1 allow prod" in r.stdout,
              f"F-8: włączenie na prod bez decyzji człowieka → FLAG-001 z poleceniem: {r.returncode} {r.stdout}")
        git(p, "add", "-A")
        git(p, "commit", "-qm", "feat: limit za flagą")
        r = run(p, SCRIPT, "PROJ-1", "--json")
        data = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and data.get("checked") is True and [e.get("env") for e in data.get("errors", [])] == ["prod"],
              f"F-9: to samo po commicie (diff gałęzi względem bazy), --json: {r.stdout[:300]}")
        r = run(p, TASK, "flag", "PROJ-1", "allow", "prod", "--by", "process:talos")
        check(r.returncode == 2, f"F-10: decyzję o innym środowisku zapisuje tylko człowiek: {r.returncode} {r.stdout}")
        r = run(p, TASK, "flag", "PROJ-1", "allow", "prod", "--by", "human:anna")
        check(r.returncode == 0 and task()["flag"].get("allowed", {}).get("prod", {}).get("by") == "human:anna"
              and run(p, SCRIPT, "PROJ-1").returncode == 0,
              f"F-11: po decyzji człowieka kontrola przechodzi: {r.stdout}")

        # układ flaga → środowisko → stan i wartość {"enabled": …}
        write(p, "config/flags.json", json.dumps({"proj_1_limit": {"test": {"enabled": True}, "qa": {"enabled": True},
                                                                   "prod": {"enabled": True}}}))
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 1 and "qa" in r.stdout and "FLAG-001" in r.stdout,
              f"F-12: układ flaga → środowisko: qa bez decyzji → FLAG-001: {r.stdout}")
        write(p, "config/flags.json", "to nie json")
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0 and "ręcznie" in r.stdout, f"F-13: plik, którego skrypt nie rozumie → „sprawdź ręcznie”, kod 0: {r.stdout}")
        flags(p, test=True, qa=False, prod=False)

        # bramka etapu: zadanie ze specyfikacją potrzebuje flagi albo powodu jej braku; zmiana na prod bez decyzji blokuje
        run(p, TASK, "start", "PROJ-2", "--title", "Bez flagi")
        write(p, f"{CHANGES.as_posix()}/PROJ-2/spec.md", SPEC)
        write(p, "tests/test_x.py", "def test_ac1():  # AC-1\n    assert True\n")
        r = run(p, TASK, "stage", "PROJ-2", "pr")
        check(r.returncode == 1 and "tf task flag PROJ-2" in r.stdout, f"F-14: etap pr odrzucony bez flagi i bez powodu: {r.returncode} {r.stdout}")
        r = run(p, TASK, "flag", "PROJ-2", "none", "--reason", "poprawka błędu, nie ma czego ukrywać")
        r2 = run(p, TASK, "stage", "PROJ-2", "pr")
        check(r.returncode == 0 and r2.returncode == 0 and "poprawka błędu" in run(p, SCRIPT, "PROJ-2").stdout,
              f"F-15: „bez flagi, bo…” wystarcza: {r.stdout} {r2.stdout}")
        run(p, TASK, "start", "PROJ-3", "--title", "Bez specyfikacji")
        r = run(p, TASK, "stage", "PROJ-3", "pr")
        check(r.returncode == 0, f"F-16: zadanie bez spec.md nie wymaga flagi: {r.stdout}")
        run(p, TASK, "start", "PROJ-4", "--title", "Flaga na prod")
        write(p, f"{CHANGES.as_posix()}/PROJ-4/spec.md", SPEC)
        run(p, TASK, "flag", "PROJ-4", "set", "proj_1_limit")
        flags(p, test=True, qa=False, prod=True)
        r = run(p, TASK, "stage", "PROJ-4", "pr")
        check(r.returncode == 1 and "FLAG-001" in r.stdout, f"F-17: etap pr odrzucony, gdy flaga jest włączona na prod bez decyzji: {r.stdout}")

        # wyłącznik w konfiguracji: flagi dodaje człowiek sam (w kodzie, w zewnętrznej usłudze) — fabryka ich nie wymaga
        run(p, TASK, "start", "PROJ-5", "--title", "Flagi ręcznie")
        write(p, f"{CHANGES.as_posix()}/PROJ-5/spec.md", SPEC)
        r = run(p, SCRIPT, "PROJ-5", "--json")
        data = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and data.get("auto") is True, f"F-21: domyślnie automatyczne flagi są włączone: {r.stdout[:200]}")
        write(p, ".tf/config/config.yaml", "feature_flags:\n  auto: false\n")
        r = run(p, SCRIPT, "PROJ-5")
        check(r.returncode == 0 and "feature_flags.auto" in r.stdout and "samodzielnie" in r.stdout,
              f"F-22: feature_flags.auto: false → zadanie bez flagi przechodzi, z wyjaśnieniem: {r.returncode} {r.stdout}")
        r = run(p, TASK, "stage", "PROJ-5", "pr")
        check(r.returncode == 0, f"F-23: przy wyłączonych automatycznych flagach etap pr nie wymaga flagi: {r.stdout}")
        r = run(p, SCRIPT, "PROJ-4")
        check(r.returncode == 1 and "FLAG-001" in r.stdout,
              f"F-24: flaga zapisana w zadaniu jest sprawdzana także przy wyłączonym automacie: {r.stdout}")
        (p / ".tf" / "config" / "config.yaml").unlink()

    with tempfile.TemporaryDirectory() as t:      # karta operacyjna z tf onboard
        p = Path(t)
        git(p, "init", "-q", "-b", "main")
        write(p, "package.json", json.dumps({"scripts": {"test": "node -e 0"}}))
        write(p, "config/flags.json", json.dumps({"dev": {"x": False}, "prod": {"x": False}}))
        r = run(p, ONBOARD, "--yes")
        card = p / ".tf" / "config" / "operations.json"
        data = json.loads(card.read_text(encoding="utf-8")) if card.is_file() else {}
        check(data.get("flags", {}).get("file") == "config/flags.json" and data["flags"].get("envs") == ["dev", "prod"]
              and data["flags"].get("test_env") == "dev" and "operations.json" in r.stdout,
              f"F-18: onboard wykrywa plik flag, środowiska i środowisko testowe: {data} {r.stdout[-300:]}")
        card.write_text(json.dumps(CARD), encoding="utf-8")
        run(p, ONBOARD, "--yes")
        check(json.loads(card.read_text(encoding="utf-8")) == CARD, "F-19: onboard nie nadpisuje istniejącej karty")
    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        write(p, "package.json", json.dumps({"scripts": {"test": "node -e 0"}}))
        r = run(p, ONBOARD, "--yes")
        card = p / ".tf" / "config" / "operations.json"
        data = json.loads(card.read_text(encoding="utf-8")) if card.is_file() else {}
        check(data.get("flags", {}).get("file") is None and "flag" in r.stdout.lower(),
              f"F-20: bez pliku flag karta powstaje pusta, a raport mówi, co uzupełnić: {data} {r.stdout[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów flagi funkcji")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
