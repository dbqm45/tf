#!/usr/bin/env python3
"""Kawałek zablokowany zamiast STOP (krok F3, przełącznik `loop.blocked_slices`): pytanie blokuje tylko swój
kawałek, skrypt mówi, który kawałek można robić dalej, a pytania i odpowiedzi zapisuje w `events.jsonl` zadania.
python3 .claude/tests/test_work_events.py"""
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
OK = f'{sys.executable} -c "print(\'3 passed\')"'
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi "
        "45 zł.\n\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")
PLAN = ("# Plan: Limit dobowy\n\n"
        "- [ ] K1 — limit dobowy · kryteria: AC-1 · pliki: fees.py · weryfikacja: `pytest`\n"
        "- [ ] K2 — komunikat o limicie · pliki: msg.py · po: brak\n"
        "- [ ] K3 — tłumaczenie komunikatu · pliki: i18n.py\n"
        "- [ ] K4 — raport limitów · pliki: report.py · po: K1\n")
QUESTION = "Czy limit dotyczy też abonamentów?"


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
           "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          timeout=120)


def new_run(project: Path, plan: str = PLAN) -> str:
    """Zadanie IMP-1 gotowe do pętli kawałka: waga zwykła, tryb Auto, specyfikacja, brak flagi, plan."""
    project.mkdir(parents=True)
    for name in ("fees.py", "msg.py", "i18n.py", "report.py"):
        (project / name).write_text("x = 1\n", encoding="utf-8")
    call(project, SCRIPTS / "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
    d = str(project / ".tf" / "runs" / "IMP-1")
    call(project, SCRIPTS / "run_state.py", "weight", d, "--set", "zwykla")
    call(project, TASK, "mode", "IMP-1", "auto")
    doc = project / CHANGES / "IMP-1"
    (doc / "spec.md").write_text(SPEC, encoding="utf-8")
    (doc / "plan.md").write_text(plan, encoding="utf-8")
    call(project, SCRIPTS / "run_state.py", "flag", d, "none", "--reason", "bez flagi, bo zmiana jest w konfiguracji")
    return d


def switch(project: Path, on: bool) -> None:
    cfg = project / ".tf" / "config" / "config.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(f"loop:\n  blocked_slices: {'true' if on else 'false'}\n", encoding="utf-8")


def task(project: Path) -> dict:
    return json.loads((project / CHANGES / "IMP-1" / "task.json").read_text(encoding="utf-8"))


def events(project: Path) -> list[dict]:
    f = project / CHANGES / "IMP-1" / "events.jsonl"
    return [json.loads(ln) for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()] if f.is_file() else []


def done(project: Path, d: str, slice_id: str, file: str) -> None:
    call(project, TASK, "verify", "IMP-1", slice_id, "--files", file, "--command", OK)
    call(project, SCRIPTS / "run_state.py", "tick", d, slice_id)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    rs = SCRIPTS / "run_state.py"
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        d = new_run(p)

        # przełącznik wyłączony (domyślnie): pętla działa jak dotąd — pytanie to blok STOP
        r = call(p, rs, "block", d, "K1", "--question", QUESTION)
        check(r.returncode == 2 and "loop.blocked_slices" in r.stdout and "--code pytanie" in r.stdout
              and not events(p) and (task(p).get("slices") or {}).get("K1", {}).get("state") != "blocked",
              f"WE-1: bez przełącznika `block` odmawia i wskazuje STOP z kodem pytanie: {r.returncode} {r.stdout}")
        call(p, rs, "step", d, "K1", "R1", "test", "run")
        r = call(p, rs, "stage", d, "needs", "--needs", "stop", "--code", "pytanie", "--reason", QUESTION)
        check(r.returncode == 0, f"WE-2: bez przełącznika STOP z kodem pytanie przechodzi jak dotąd: {r.returncode} {r.stdout}")
        call(p, rs, "step", d, "K1", "R1", "test", "run")

        switch(p, True)
        # STOP z pytaniem o bieżący kawałek, gdy jest kawałek niezależny → odmowa z podpowiedzią `block`
        r = call(p, rs, "stage", d, "needs", "--needs", "stop", "--code", "pytanie", "--reason", QUESTION)
        check(r.returncode == 2 and "block" in r.stdout and "K2" in r.stdout and "--task" in r.stdout,
              f"WE-3: z przełącznikiem STOP z pytaniem o jeden kawałek jest odrzucany, gdy jest co robić dalej: {r.returncode} {r.stdout}")
        r = call(p, rs, "block", d, "K1", "--question", QUESTION)
        ev = events(p)
        check(r.returncode == 0 and "Dalej: K2" in r.stdout and task(p)["slices"]["K1"].get("state") == "blocked"
              and task(p)["slices"]["K1"].get("reason") == QUESTION,
              f"WE-4: block blokuje tylko K1 i wskazuje niezależny kawałek K2: {r.returncode} {r.stdout} {task(p).get('slices')}")
        check(len(ev) == 1 and ev[0].get("type") == "question" and ev[0].get("slice") == "K1"
              and ev[0].get("text") == QUESTION and ev[0].get("by") == "process:tf" and ev[0].get("at"),
              f"WE-5: pytanie zapisane w events.jsonl zadania (kto, kiedy, co): {ev}")
        r = call(p, TASK, "list")
        check("czeka na Ciebie" in r.stdout and "K1" in r.stdout and QUESTION in r.stdout,
              f"WE-6: pytanie zablokowanego kawałka jest na liście „czeka na Ciebie”: {r.stdout}")

        # kolejność wg zależności: K3 (bez dopisku) zależy od K2, K4 zależy od zablokowanego K1
        done(p, d, "K2", "msg.py")
        r = call(p, rs, "next", d)
        check(r.returncode == 0 and "Dalej: K3" in r.stdout, f"WE-7: po K2 kolej na K3 (zależy od poprzedniego): {r.stdout}")
        done(p, d, "K3", "i18n.py")
        r = call(p, rs, "next", d)
        check(r.returncode == 0 and "Dalej: STOP" in r.stdout and QUESTION in r.stdout and "--code pytanie" in r.stdout
              and "K4" in r.stdout,
              f"WE-8: gdy nic niezależnego nie zostało (K4 czeka na K1) → STOP z listą pytań: {r.stdout}")
        r = call(p, rs, "stage", d, "needs", "--needs", "stop", "--code", "pytanie", "--reason", QUESTION)
        check(r.returncode == 0, f"WE-9: STOP z pytaniem przechodzi, gdy nie ma już kawałka do zrobienia: {r.returncode} {r.stdout}")

        # odpowiedź człowieka odblokowuje kawałek
        r = call(p, rs, "answer", d, "K1", "Nie, tylko postój jednorazowy")
        check(r.returncode == 2 and "human:" in r.stdout and task(p)["slices"]["K1"].get("state") == "blocked",
              f"WE-10: odpowiedź zapisuje się z identyfikatorem człowieka (--by human:<id>): {r.returncode} {r.stdout}")
        r = call(p, rs, "answer", d, "K1", "Nie, tylko postój jednorazowy", "--by", "human:anna")
        ev = events(p)
        check(r.returncode == 0 and "Dalej: K1" in r.stdout and task(p)["slices"]["K1"].get("state") != "blocked"
              and len(ev) == 2 and ev[1].get("type") == "answer" and ev[1].get("by") == "human:anna"
              and ev[1].get("text") == "Nie, tylko postój jednorazowy" and ev[1].get("slice") == "K1",
              f"WE-11: answer odblokowuje K1, zapisuje odpowiedź i wskazuje go jako następny: {r.returncode} {r.stdout} {ev}")
        r = call(p, TASK, "list")
        check("czeka na Ciebie" not in r.stdout, f"WE-12: po odpowiedzi nic nie czeka: {r.stdout}")

    # plan bez zależności: kawałki idą po kolei, więc pytanie w K1 zatrzymuje przebieg jak dotąd
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        d = new_run(p, PLAN.replace(" · po: brak", "").replace(" · po: K1", ""))
        switch(p, True)
        call(p, rs, "step", d, "K1", "R1", "test", "run")
        r = call(p, rs, "block", d, "K1", "--question", QUESTION)
        check(r.returncode == 0 and "Dalej: STOP" in r.stdout and "--code pytanie" in r.stdout,
              f"WE-13: plan bez dopisków „po:” — pytanie w K1 nie zostawia nic do zrobienia: {r.stdout}")
        # pytanie o całe zadanie: STOP od razu, bez blokowania kawałka
        r = call(p, rs, "stage", d, "needs", "--needs", "stop", "--code", "pytanie", "--reason", QUESTION, "--task")
        check(r.returncode == 0, f"WE-14: `--task` (pytanie o całe zadanie) przepuszcza STOP: {r.returncode} {r.stdout}")
        r = call(p, rs, "stage", d, "plan")
        check("po:" in r.stdout and "po: brak" in r.stdout,
              f"WE-15: etap plan z włączonym przełącznikiem przypomina o zapisie zależności kawałków: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów kawałka zablokowanego")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
