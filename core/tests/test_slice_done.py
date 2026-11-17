#!/usr/bin/env python3
"""Koniec kawałka jednym poleceniem: `run_state.py done <katalog> K<n> --message "<typ>(<zakres>): <opis>"` zapisuje
zaliczony przegląd zakresu bieżącej rundy, robi commit plików z dowodu (z treścią `Kawałek K<n>: …` i stopkami),
odhacza kawałek i podaje następny. Bez aktualnego dowodu albo ze złym tytułem niczego nie zapisuje.
python3 .claude/tests/test_slice_done.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "run_state.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL
REPORT = SCRIPT.with_name("run_report.py")
TASK = ROOT / ".tf" / "factory" / "task_state.py"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'3 passed\')"'
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci kartą, wtedy opłata "
        "wynosi 45 zł.\n\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")
PLAN = ("# Plan\n\n- [ ] K1 — płatność kartą · kryteria: AC-1 · pliki: pay.py\n"
        "- [ ] K2 — paragon · kryteria: AC-1 · pliki: pay.py\n")


def env(project: Path) -> dict:
    return {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
            "TF_DASHBOARD_OPEN": "0", "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com", "GIT_CONFIG_GLOBAL": os.devnull}


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True,
                          env=env(project), timeout=120)


def git(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(project), "-c", "commit.gpgsign=false", *args], capture_output=True,
                          text=True, env=env(project), timeout=60)


def prepare(p: Path, with_git: bool = True) -> str:
    """Przebieg IMP-1 z zatwierdzonym planem (K1, K2), testem i kodem K1; zwraca katalog przebiegu."""
    p.mkdir(parents=True)
    if with_git:
        git(p, "init", "-q", "-b", "main")
        (p / "README.md").write_text("x\n", encoding="utf-8")
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "chore: init")
        git(p, "checkout", "-q", "-b", "story/platnosc-karta")
    call(p, REPORT, "start", "Płatność kartą", "--key", "IMP-1", "--story", "Jako kierowca chcę zapłacić kartą.")
    d = str(p / ".tf" / "runs" / "IMP-1")
    doc = p / CHANGES / "IMP-1"
    (doc / "spec.md").write_text(SPEC, encoding="utf-8")
    (doc / "plan.md").write_text(PLAN, encoding="utf-8")
    call(p, SCRIPT, "flag", d, "none", "--reason", "bez flagi, bo zmiana jest za zgodą człowieka w planie")
    call(p, SCRIPT, "stage", d, "plan")
    call(p, SCRIPT, "approve", d)
    call(p, SCRIPT, "step", d, "K1", "R1", "test", "run")
    (p / "pay.py").write_text("FEE = 45\n", encoding="utf-8")
    (p / "test_pay.py").write_text("def test_ac1_card_fee():  # AC-1\n    assert True\n", encoding="utf-8")
    return d


def meta(d: str) -> dict:
    return json.loads((Path(d) / "run.json").read_text(encoding="utf-8"))


def plan_text(p: Path) -> str:
    return (p / CHANGES / "IMP-1" / "plan.md").read_text(encoding="utf-8")


def commits(p: Path) -> list[str]:
    return [c for c in git(p, "log", "--format=%B%x00").stdout.split("\x00") if c.strip()]


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = base / "main"
        d = prepare(p)
        (p / "notes.txt").write_text("szkic poza kawałkiem\n", encoding="utf-8")

        # bez dowodu: odmowa, nic nie zapisane
        r = call(p, SCRIPT, "done", d, "K1", "--message", "feat(pay): card payment")
        cur = meta(d).get("current") or {}
        check(r.returncode != 0 and "verify" in r.stdout + r.stderr and len(commits(p)) == 1
              and "- [x] K1" not in plan_text(p) and (cur.get("rounds") or [{}])[-1].get("scope") != "pass",
              f"DN-1: bez dowodu done odmawia i niczego nie zapisuje: {r.returncode} {r.stdout}{r.stderr} {cur}")

        call(p, SCRIPT, "verify", d, "K1", "--files", "pay.py,test_pay.py", "--command", OK)
        # zły tytuł: odmowa przed zapisem
        r = call(p, SCRIPT, "done", d, "K1", "--message", "dodałem płatność")
        check(r.returncode != 0 and "Conventional" in r.stdout + r.stderr and len(commits(p)) == 1
              and "- [x] K1" not in plan_text(p),
              f"DN-2: tytuł spoza Conventional Commits → odmowa przed commitem: {r.returncode} {r.stdout}{r.stderr}")

        r = call(p, SCRIPT, "done", d, "K1", "--message", "feat(pay): card payment")
        log = commits(p)
        files = set(git(p, "show", "--name-only", "--format=", "HEAD").stdout.split())
        check(r.returncode == 0 and len(log) == 2 and log[0].startswith("feat(pay): card payment")
              and "Slice K1: płatność kartą" in log[0],
              f"DN-3: commit z tytułem i treścią „Slice K1: <wartość z planu>”: {r.returncode} {r.stdout}{r.stderr} {log[:1]}")
        check(files == {"pay.py", "test_pay.py"} and "notes.txt" in git(p, "status", "--porcelain").stdout,
              f"DN-4: commit obejmuje tylko pliki z dowodu, reszta zostaje niezatwierdzona: {files}")
        cur = meta(d).get("current") or {}
        check(cur.get("k") == "K1" and (cur.get("rounds") or [{}])[-1].get("scope") == "pass",
              f"DN-5: zapisany zaliczony przegląd zakresu bieżącej rundy: {cur}")
        check("- [x] K1" in plan_text(p) and "- [ ] K2" in plan_text(p) and "Dalej: K2" in r.stdout,
              f"DN-6: kawałek odhaczony, wyjście podaje następny: {r.stdout} {plan_text(p)}")

        # ponowienie: nic nowego do zatwierdzenia, bez nowego commita, kod 0
        r = call(p, SCRIPT, "done", d, "K1", "--message", "feat(pay): card payment")
        check(r.returncode == 0 and len(commits(p)) == 2,
              f"DN-7: ponowne done bez zmian plików nie tworzy commita: {r.returncode} {r.stdout}{r.stderr} {len(commits(p))}")

        # druga runda: przegląd R1 nie przeszedł, done zapisuje R2; treść z „Kawałek” nie jest dublowana; flaga → stopka
        call(p, TASK, "flag", "IMP-1", "set", "imp_1_paragon", "--remove-by", "2027-01-31")
        call(p, SCRIPT, "step", d, "K2", "R1", "test", "run")
        (p / "pay.py").write_text("FEE = 45\nRECEIPT = True\n", encoding="utf-8")
        call(p, SCRIPT, "verify", d, "K2", "--files", "pay.py,test_pay.py", "--command", OK)
        call(p, SCRIPT, "finding", d, "K2", "paragon drukuje się dwa razy [ważne]", "--round", "1")
        call(p, SCRIPT, "step", d, "K2", "R1", "scope", "fail")
        call(p, SCRIPT, "step", d, "K2", "R2", "code", "run")
        (p / "pay.py").write_text("FEE = 45\nRECEIPT = 1\n", encoding="utf-8")
        call(p, SCRIPT, "verify", d, "K2", "--files", "pay.py,test_pay.py", "--command", OK)
        r = call(p, SCRIPT, "done", d, "K2", "--message", "feat(pay): print receipt\n\nKawałek K2: paragon")
        log = commits(p)
        rounds = (meta(d).get("current") or {}).get("rounds") or []
        check(r.returncode == 0 and len(rounds) == 2 and rounds[0].get("scope") == "fail"
              and rounds[1].get("scope") == "pass",
              f"DN-8: done zapisuje przegląd bieżącej rundy (R2), R1 zostaje fail: {r.returncode} {r.stdout}{r.stderr} {rounds}")
        check(log[0].count("Kawałek K2") == 1 and "Flag: imp_1_paragon" in log[0],
              f"DN-9: treść „Kawałek” nie jest dublowana, flaga zadania dodaje stopkę: {log[:1]}")
        check("- [x] K2" in plan_text(p) and "zakończenie" in r.stdout,
              f"DN-10: ostatni kawałek odhaczony, wyjście mówi o zakończeniu: {r.stdout}")

        # plik zmieniony po dowodzie: odmowa
        p = base / "stale"
        d = prepare(p)
        call(p, SCRIPT, "verify", d, "K1", "--files", "pay.py,test_pay.py", "--command", OK)
        (p / "pay.py").write_text("FEE = 46\n", encoding="utf-8")
        r = call(p, SCRIPT, "done", d, "K1", "--message", "feat(pay): card payment")
        check(r.returncode != 0 and len(commits(p)) == 1 and "- [x] K1" not in plan_text(p),
              f"DN-11: plik zmieniony po dowodzie → odmowa bez commita: {r.returncode} {r.stdout}{r.stderr}")

        # odmowa commita (hook commit-msg): kawałek nieodhaczony, wyjście gita w odpowiedzi
        p = base / "hook"
        d = prepare(p)
        hook = p / ".git" / "hooks" / "commit-msg"
        hook.write_text("#!/bin/sh\necho 'brak stopki Change' >&2\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        call(p, SCRIPT, "verify", d, "K1", "--files", "pay.py,test_pay.py", "--command", OK)
        r = call(p, SCRIPT, "done", d, "K1", "--message", "feat(pay): card payment")
        check(r.returncode != 0 and "brak stopki Change" in r.stdout + r.stderr and "- [x] K1" not in plan_text(p),
              f"DN-12: commit odrzucony przez hook → kod ≠ 0, kawałek nieodhaczony: {r.returncode} {r.stdout}{r.stderr}")

    # treść skilla prowadzi przez done
    skill = (ROOT / ".claude" / "skills" / "tf" / "SKILL.md").read_text(encoding="utf-8")
    check("run_state.py done" in skill, "DN-13: SKILL.md kieruje koniec kawałka do `run_state.py done`")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów końca kawałka")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
