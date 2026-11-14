#!/usr/bin/env python3
"""Zamknięcie zadania (krok G4): `tf task close` zamyka tylko scaloną zmianę, wymaga kontroli do każdego ważnego
ustalenia przeglądu, przypomina o fladze, zapisuje lekcję podaną przez człowieka; `tf status` pokazuje zadania w toku.
python3 .claude/tests/test_close.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
CHANGES = Path("docs") / "project" / "changes"
LESSON = ("**Sprawdzaj limit dobowy na granicy doby** — Kontekst: opłaty za postój, fees.py · Zamiast tego: test "
          "z postojem przez północ · Dotyczy: realizacja")
FINDING = "usunięta asercja testu limitu przy końcu doby"
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi "
        "45 zł.\n\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
           "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          stdin=subprocess.DEVNULL, timeout=120)


def git(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(project), "-c", "user.email=t@example.com", "-c", "user.name=T",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, timeout=60)


def task(project: Path, key: str = "IMP-1") -> dict:
    return json.loads((project / CHANGES / key / "task.json").read_text(encoding="utf-8"))


def new_task(project: Path, merged: bool = True, key: str = "IMP-1") -> None:
    """Repozytorium z zadaniem na etapie pr; `merged` — katalog zadania jest już na gałęzi main (scalenie squash)."""
    if not (project / ".git").exists():
        project.mkdir(parents=True, exist_ok=True)
        git(project, "init", "-q", "-b", "main")
        (project / "fees.py").write_text("x = 1\n", encoding="utf-8")
        git(project, "add", "-A")
        git(project, "commit", "-q", "-m", "chore: init")
    git(project, "checkout", "-q", "-b", f"story/{key.lower()}")
    call(project, TASK, "start", key, "--title", "Limit dobowy")
    call(project, TASK, "stage", key, "pr", "--force")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", f"docs(task): record {key}")
    git(project, "checkout", "-q", "main")
    if merged:
        git(project, "merge", "-q", "--squash", f"story/{key.lower()}")
        git(project, "commit", "-q", "-m", f"feat: daily cap ({key})")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        # zmiana niescalona: odmowa; człowiek może zamknąć mimo to
        p = Path(t) / "unmerged"
        new_task(p, merged=False)
        git(p, "checkout", "-q", "story/imp-1")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 1 and "scalon" in r.stdout and task(p)["stage"] == "pr" and "closed" not in task(p),
              f"CL-1: niescalonej zmiany nie da się zamknąć: {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--force")
        check(r.returncode == 2 and "human:" in r.stdout and task(p)["stage"] == "pr",
              f"CL-2: zamknięcie mimo braku scalenia to decyzja człowieka (--force --by human:<id>): {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--force", "--by", "human:anna")
        check(r.returncode == 0 and task(p)["stage"] == "zamkniecie" and task(p)["closed"].get("forced") is True
              and task(p)["closed"].get("by") == "human:anna",
              f"CL-3: człowiek zamyka mimo braku potwierdzenia scalenia; zapis w zadaniu: {r.stdout} {task(p).get('closed')}")

        # zmiana scalona (squash): zamknięcie przechodzi
        p = Path(t) / "merged"
        new_task(p)
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and task(p)["stage"] == "zamkniecie" and task(p)["closed"].get("at")
              and "zamknięte" in r.stdout and "forced" not in task(p)["closed"],
              f"CL-4: scalona zmiana (squash) → etap zamkniecie i zapis closed: {r.returncode} {r.stdout}")
        check("testem dymnym" in r.stdout,
              f"CL-5: zamknięcie mówi wprost, że wdrożenie nie było sprawdzone testem dymnym: {r.stdout}")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and "już" in r.stdout, f"CL-6: ponowne zamknięcie nie jest błędem: {r.returncode} {r.stdout}")

        # ważne ustalenia przeglądu: bez kontroli nie ma zamknięcia
        p = Path(t) / "findings"
        new_task(p)
        r1 = call(p, TASK, "finding", "IMP-1", "add", FINDING, "--slice", "K1")
        r2 = call(p, TASK, "finding", "IMP-1", "add", "kod spoza kryteriów w msg.py")
        fs = task(p).get("findings") or []
        check(r1.returncode == 0 and r2.returncode == 0 and [f.get("id") for f in fs] == ["F1", "F2"]
              and fs[0].get("text") == FINDING and fs[0].get("slice") == "K1" and fs[0].get("at") and "F1" in r1.stdout,
              f"CL-7: ważne ustalenia zapisane w zadaniu z identyfikatorem, kawałkiem i datą: {r1.stdout} {fs}")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 1 and "F1" in r.stdout and "F2" in r.stdout and "finding IMP-1 control" in r.stdout
              and task(p)["stage"] == "pr",
              f"CL-8: ustalenie bez kontroli blokuje zamknięcie; komunikat podaje polecenie: {r.returncode} {r.stdout}")
        r = call(p, TASK, "finding", "IMP-1", "control", "F9", "test")
        check(r.returncode != 0 and "F9" in r.stdout, f"CL-9: kontrola do nieznanego ustalenia → odmowa: {r.returncode} {r.stdout}")
        call(p, TASK, "finding", "IMP-1", "control", "F1", "test test_fees.py::test_cap_at_midnight")
        call(p, TASK, "finding", "IMP-1", "control", "F2", "brak kontroli: jednorazowa pomyłka przy scalaniu")
        r = call(p, TASK, "status", "IMP-1")
        check("F1" in r.stdout and "test_cap_at_midnight" in r.stdout and FINDING in r.stdout,
              f"CL-10: tf task status pokazuje ustalenia z kontrolami: {r.stdout}")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and task(p)["stage"] == "zamkniecie",
              f"CL-11: po zapisaniu kontroli zamknięcie przechodzi: {r.returncode} {r.stdout}")

        p = Path(t) / "odd"
        new_task(p)
        f = p / CHANGES / "IMP-1" / "task.json"
        f.write_text(json.dumps({**task(p), "deploy": {"state": ["ok"]}}), encoding="utf-8")
        r = call(p, TASK, "close", "IMP-1", "--force", "--by", "human:anna")
        check(r.returncode == 0 and "Traceback" not in r.stderr,
              f"CL-31: nietypowy zapis wdrożenia w task.json nie wywraca zamknięcia: {r.stderr[-200:]}")

        # czerwony test dymny bez decyzji blokuje zamknięcie
        p = Path(t) / "red"
        new_task(p)
        card = p / ".tf" / "config" / "operations.json"
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text(json.dumps({"deploy": {"smoke": f'{sys.executable} -c "raise SystemExit(7)"'}}), encoding="utf-8")
        call(p, TASK, "deployed", "IMP-1")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 1 and "wycofani" in r.stdout and task(p)["stage"] == "pr",
              f"CL-12: wdrożenie czekające na decyzję o wycofaniu blokuje zamknięcie: {r.returncode} {r.stdout}")

        # flaga: przypomnienie o dacie usunięcia albo o jej braku
        p = Path(t) / "flag"
        new_task(p)
        call(p, TASK, "flag", "IMP-1", "set", "limit-dobowy", "--remove-by", "2027-01-31")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and "limit-dobowy" in r.stdout and "2027-01-31" in r.stdout,
              f"CL-13: zamknięcie przypomina o dacie usunięcia flagi: {r.stdout}")
        p = Path(t) / "flag2"
        new_task(p)
        call(p, TASK, "flag", "IMP-1", "set", "limit-dobowy")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and "limit-dobowy" in r.stdout and "--remove-by" in r.stdout,
              f"CL-14: flaga bez daty usunięcia → przypomnienie, jak ją ustawić: {r.stdout}")

        # lekcja: tylko od człowieka, z „Zamiast tego”, dopisana raz
        p = Path(t) / "lesson"
        new_task(p)
        lessons = p / "docs" / "project" / "lessons.md"
        r = call(p, TASK, "close", "IMP-1", "--lesson", LESSON)
        check(r.returncode == 2 and "human:" in r.stdout and not lessons.exists() and task(p)["stage"] == "pr",
              f"CL-15: lekcję zapisuje człowiek (--by human:<id>): {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--lesson", "Uważaj na limit dobowy", "--by", "human:anna")
        check(r.returncode == 2 and "Zamiast tego" in r.stdout and not lessons.exists(),
              f"CL-16: lekcja bez „Zamiast tego:” nie jest lekcją: {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--by", "human:anna")
        text = lessons.read_text(encoding="utf-8") if lessons.is_file() else ""
        check(r.returncode == 0 and text.count(LESSON) == 1 and "IMP-1" in text and text.startswith("# ")
              and task(p)["closed"].get("lesson") is True,
              f"CL-17: lekcja człowieka trafia do docs/project/lessons.md z datą i kluczem zadania: {r.stdout} {text}")
        call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--by", "human:anna")
        check((lessons.read_text(encoding="utf-8") if lessons.is_file() else "").count(LESSON) == 1,
              "CL-18: ta sama lekcja nie jest dopisywana drugi raz")
        check("lessons.md" not in call(Path(t) / "merged", TASK, "status", "IMP-1").stdout
              and not (Path(t) / "merged" / "docs" / "project" / "lessons.md").exists(),
              "CL-19: bez --lesson fabryka niczego nie dopisuje do lekcji")

        p = Path(t) / "lesson2"
        new_task(p)
        lessons = p / "docs" / "project" / "lessons.md"
        lessons.parent.mkdir(parents=True, exist_ok=True)
        old = ("# Lekcje projektu\n\n## Wykonanie i weryfikacja\n\n- 2026-01-01 **Stara lekcja** — Kontekst: x · Zamiast "
               "tego: y\n\n## Powłoka i narzędzia\n\n- 2026-01-02 **Inna** — Kontekst: x · Zamiast tego: y\n")
        lessons.write_text(old, encoding="utf-8")
        call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--by", "human:anna")
        text = lessons.read_text(encoding="utf-8")
        check(text.count("## Wykonanie i weryfikacja") == 1 and "## Powłoka i narzędzia" in text
              and text.index(LESSON) < text.index("Stara lekcja") < text.index("## Powłoka") and "Inna" in text,
              f"CL-30: lekcja trafia pod istniejący nagłówek, nad starsze wpisy; reszta pliku bez zmian: {text}")

        # tf status: zamknięte zadania nie są na liście zadań w toku
        p = Path(t) / "merged"
        new_task(p, key="IMP-2")
        r = call(p, TASK, "list")
        check("IMP-2" in r.stdout and "IMP-1" not in r.stdout and "zamknięte: 1" in r.stdout and "--all" in r.stdout,
              f"CL-20: tf status pokazuje zadania w toku, zamknięte liczy jedną linią: {r.stdout}")
        r = call(p, TASK, "list", "--all")
        check("IMP-1" in r.stdout and "IMP-2" in r.stdout, f"CL-21: tf status --all pokazuje wszystkie: {r.stdout}")
        r = call(p, TASK, "list", "--json")
        check({x["key"] for x in json.loads(r.stdout)} == {"IMP-1", "IMP-2"},
              f"CL-22: wynik --json zawiera wszystkie zadania jak dotąd: {r.stdout[:200]}")

        # katalog bez gita: scalenia nie da się potwierdzić
        p = Path(t) / "nogit"
        p.mkdir()
        call(p, TASK, "start", "IMP-1", "--title", "Limit dobowy")
        call(p, TASK, "stage", "IMP-1", "pr", "--force")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 1 and "--force" in r.stdout and "Traceback" not in r.stdout + r.stderr,
              f"CL-23: bez repozytorium git scalenia nie da się potwierdzić — odmowa z drogą dla człowieka: {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-9")
        check(r.returncode != 0 and "nie ma zadania" in r.stdout, f"CL-24: nieznane zadanie → odmowa: {r.stdout}")

    # pętla: nieudany przegląd zakresu wymaga zapisanego ustalenia z tej rundy
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        p.mkdir()
        rs = SCRIPTS / "run_state.py"
        call(p, SCRIPTS / "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
        d = str(p / ".tf" / "runs" / "IMP-1")
        call(p, rs, "weight", d, "--set", "zwykla")
        call(p, TASK, "mode", "IMP-1", "auto")
        (p / CHANGES / "IMP-1" / "spec.md").write_text(SPEC, encoding="utf-8")
        call(p, rs, "flag", d, "none", "--reason", "bez flagi, bo zmiana jest w konfiguracji")
        call(p, rs, "step", d, "K1", "R1", "kod", "run")
        r = call(p, rs, "step", d, "K1", "R1", "zakres", "fail")
        check(r.returncode == 2 and "finding" in r.stdout and "K1" in r.stdout and not task(p).get("findings"),
              f"CL-25: `zakres fail` bez zapisanego ustalenia → odmowa z poleceniem: {r.returncode} {r.stdout}")
        r = call(p, rs, "finding", d, "K1", FINDING)
        fs = task(p).get("findings") or []
        check(r.returncode == 0 and len(fs) == 1 and fs[0].get("slice") == "K1" and fs[0].get("round") == 1
              and fs[0].get("text") == FINDING,
              f"CL-26: run_state.py finding zapisuje ustalenie z kawałkiem i rundą: {r.returncode} {r.stdout} {fs}")
        r = call(p, rs, "step", d, "K1", "R1", "zakres", "fail")
        check(r.returncode == 0, f"CL-27: po zapisie ustalenia `zakres fail` przechodzi: {r.returncode} {r.stdout}")
        call(p, rs, "step", d, "K1", "R2", "kod", "run")
        r = call(p, rs, "step", d, "K1", "R2", "zakres", "fail")
        check(r.returncode == 2 and "finding" in r.stdout,
              f"CL-28: druga runda wymaga własnego ustalenia: {r.returncode} {r.stdout}")
        r = call(p, rs, "step", d, "K1", "R2", "zakres", "pass")
        check(r.returncode == 0, f"CL-29: `zakres pass` nie wymaga ustalenia: {r.returncode} {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów zamknięcia zadania")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
