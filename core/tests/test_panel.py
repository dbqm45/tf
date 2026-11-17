#!/usr/bin/env python3
"""Panel recenzentów przy wadze pełnej (krok H11, decyzja D11): zadanie o wadze pełnej przechodzi do etapu `pr`
dopiero z werdyktem `pass` od `security-reviewer` i `spec-reviewer` dla bieżącego commita; waga lekka i zwykła bez
zmian. `run_state.py panel` podaje skład panelu, zlecenia i polecenie zapisu werdyktu.
python3 .claude/tests/test_panel.py"""
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
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci kartą, wtedy opłata "
        "wynosi 45 zł.\n\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")
PLAN = "# Plan\n\n- [ ] K1 — płatność kartą · kryteria: AC-1 · pliki: pay.py · weryfikacja: `pytest`\n"


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
           "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          timeout=120)


def git(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(project), "-c", "user.email=t@example.com", "-c", "user.name=T",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, timeout=60)


def ready_task(p: Path, weight: str) -> None:
    """Zadanie IMP-1 gotowe do etapu pr: specyfikacja, zatwierdzony plan, zweryfikowany kawałek, decyzja o fladze."""
    p.mkdir(parents=True, exist_ok=True)
    (p / "pay.py").write_text("x = 1\n", encoding="utf-8")
    call(p, TASK, "start", "IMP-1", "--title", "Płatność kartą", "--weight", weight)
    doc = p / CHANGES / "IMP-1"
    (doc / "spec.md").write_text(SPEC, encoding="utf-8")
    (doc / "plan.md").write_text(PLAN, encoding="utf-8")
    call(p, TASK, "artifact", "IMP-1", "plan.md", "--stage", "plan", "--by", "process:tf")
    call(p, TASK, "approve", "IMP-1", "plan.md", "--by", "human:anna")
    call(p, TASK, "stage", "IMP-1", "plan")
    call(p, TASK, "stage", "IMP-1", "implementation")
    call(p, TASK, "verify", "IMP-1", "K1", "--files", "pay.py", "--command", OK)
    call(p, TASK, "flag", "IMP-1", "none", "--reason", "bez flagi, bo zmiana jest za zgodą człowieka w planie")


def task(p: Path) -> dict:
    return json.loads((p / CHANGES / "IMP-1" / "task.json").read_text(encoding="utf-8"))


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        # waga pełna: bez werdyktów panelu etap pr jest odrzucany
        p = base / "full"
        ready_task(p, "full")
        r = call(p, TASK, "stage", "IMP-1", "pr")
        check(r.returncode != 0 and "security-reviewer" in r.stdout and "spec-reviewer" in r.stdout
              and "run_state.py panel" in r.stdout and task(p)["stage"] != "pr",
              f"PN-1: waga pełna — etap pr bez panelu odrzucony, odmowa wymienia recenzentów i polecenie: {r.returncode} {r.stdout}")
        r = call(p, TASK, "review", "IMP-1", "security-reviewer", "pass", "--note", "bez ustaleń krytycznych")
        rv = (task(p).get("reviews") or {}).get("security-reviewer") or {}
        check(r.returncode == 0 and rv.get("verdict") == "pass" and rv.get("at") and rv.get("note") == "bez ustaleń krytycznych",
              f"PN-2: werdykt recenzenta zapisany w task.json (werdykt, czas, uwaga): {r.stdout} {rv}")
        r = call(p, TASK, "stage", "IMP-1", "pr")
        check(r.returncode != 0 and "spec-reviewer" in r.stdout and "security-reviewer" not in r.stdout.split("brakuje", 1)[-1],
              f"PN-3: jeden werdykt to za mało — odmowa wymienia tylko brakującego recenzenta: {r.stdout}")
        call(p, TASK, "review", "IMP-1", "spec-reviewer", "fail", "--note", "AC-1 bez testu kwoty 45 zł")
        r = call(p, TASK, "stage", "IMP-1", "pr")
        check(r.returncode != 0 and "spec-reviewer" in r.stdout and "fail" in r.stdout and "AC-1 bez testu" in r.stdout,
              f"PN-4: werdykt fail blokuje etap pr i odmowa podaje uwagę recenzenta: {r.stdout}")
        call(p, TASK, "review", "IMP-1", "spec-reviewer", "pass")
        r = call(p, TASK, "stage", "IMP-1", "pr")
        check(r.returncode == 0 and task(p)["stage"] == "pr", f"PN-5: oba werdykty pass → etap pr: {r.returncode} {r.stdout}")
        r = call(p, TASK, "review", "IMP-1", "spec-reviewer", "maybe")
        check(r.returncode != 0, f"PN-6: werdykt spoza pass/fail odrzucony: {r.returncode} {r.stdout}")
        r = call(p, TASK, "status", "IMP-1")
        check("security-reviewer" in r.stdout and "pass" in r.stdout, f"PN-7: tf task status pokazuje werdykty panelu: {r.stdout}")

        # waga zwykła: bez panelu jak dotąd
        p = base / "normal"
        ready_task(p, "normal")
        r = call(p, TASK, "stage", "IMP-1", "pr")
        check(r.returncode == 0, f"PN-8: waga zwykła przechodzi do pr bez panelu: {r.returncode} {r.stdout}")

        # werdykt dotyczy commita: zmiana kodu po przeglądzie wymaga przeglądu od nowa
        p = base / "git"
        p.mkdir()
        git(p, "init", "-q", "-b", "main")
        (p / "README.md").write_text("x\n", encoding="utf-8")
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "chore: init")
        git(p, "checkout", "-q", "-b", "story/platnosc-karta")   # ślad kryteriów liczy testy względem main
        ready_task(p, "full")
        (p / "test_pay.py").write_text("def test_ac1_card_fee():\n    assert True  # AC-1\n", encoding="utf-8")
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "feat: płatność kartą\n\nKawałek K1: płatność kartą")
        call(p, TASK, "verify", "IMP-1", "K1", "--files", "pay.py,test_pay.py", "--command", OK)
        call(p, TASK, "review", "IMP-1", "security-reviewer", "pass")
        call(p, TASK, "review", "IMP-1", "spec-reviewer", "pass")
        head = git(p, "rev-parse", "HEAD").stdout.strip()
        check(((task(p).get("reviews") or {}).get("spec-reviewer") or {}).get("sha") == head, f"PN-9: werdykt zapisuje commit HEAD: {task(p).get('reviews')}")
        (p / "pay.py").write_text("x = 2\n", encoding="utf-8")
        git(p, "commit", "-qam", "fix: poprawka po przeglądzie")
        call(p, TASK, "verify", "IMP-1", "K1", "--files", "pay.py,test_pay.py", "--command", OK)   # nowy dowód po poprawce
        r = call(p, TASK, "stage", "IMP-1", "pr")
        check(r.returncode != 0 and "spec-reviewer" in r.stdout and ("nowszy" in r.stdout or "od nowa" in r.stdout),
              f"PN-10: po nowym commicie werdykty są nieaktualne → etap pr odrzucony: {r.returncode} {r.stdout}")

        # run_state.py panel: skład, zlecenia i zapis werdyktu przez pętlę
        p = base / "loop"
        p.mkdir()
        call(p, SCRIPTS / "run_report.py", "start", "Płatność kartą", "--key", "IMP-1", "--story",
             "Jako kierowca chcę zapłacić kartą za postój.")
        d = str(p / ".tf" / "runs" / "IMP-1")
        call(p, SCRIPTS / "run_state.py", "weight", d, "--set", "full")
        r = call(p, SCRIPTS / "run_state.py", "panel", d)
        check(r.returncode == 0 and "security-reviewer" in r.stdout and "spec-reviewer" in r.stdout and "spec.md" in r.stdout
              and "--record" in r.stdout and "AC-n" in r.stdout and "Unchanged" in r.stdout,
              f"PN-11: panel drukuje skład, zlecenia (spec.md, kryterium po kryterium, Unchanged) i polecenie zapisu: {r.stdout}")
        r = call(p, SCRIPTS / "run_state.py", "panel", d, "--record", "spec-reviewer", "pass", "--note", "AC-1 spełnione")
        check(r.returncode == 0 and (task(p).get("reviews") or {}).get("spec-reviewer", {}).get("verdict") == "pass",
              f"PN-12: panel --record zapisuje werdykt w zadaniu: {r.returncode} {r.stdout} {task(p).get('reviews')}")
        r = call(p, SCRIPTS / "run_state.py", "panel", d)
        check("spec-reviewer: pass" in r.stdout, f"PN-13: panel pokazuje zapisane werdykty: {r.stdout}")
        call(p, SCRIPTS / "run_state.py", "weight", d)
        p2 = base / "loop2"
        p2.mkdir()
        call(p2, SCRIPTS / "run_report.py", "start", "Literówka", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
        r = call(p2, SCRIPTS / "run_state.py", "panel", str(p2 / ".tf" / "runs" / "IMP-1"))
        check(r.returncode == 0 and "nie wymaga" in r.stdout,
              f"PN-14: przy wadze innej niż pełna panel mówi, że nie jest wymagany: {r.returncode} {r.stdout}")

    # agent spec-reviewer: tylko odczyt, dostępny dla pętli
    cfg = (ROOT / ".tf" / "factory" / "config.yaml").read_text(encoding="utf-8")
    block = cfg.split("\n  spec-reviewer:", 1)[-1].split("\n\n", 1)[0] if "\n  spec-reviewer:" in cfg else ""
    check(block and "tools: [Read, Grep, Glob, Bash]" in block and "AC-n" in block and "Unchanged" in block,
          f"PN-15: agent spec-reviewer — tylko odczyt, sprawdza kryterium po kryterium i reguły „Bez zmian”: {block[:300]}")
    tf_tools = cfg.split("\n  tf:", 1)[-1].split("\n", 6)[:6] if "\n  tf:" in cfg else []
    check(any("spec-reviewer" in ln for ln in tf_tools), f"PN-16: pętla tf może wołać spec-reviewer: {tf_tools}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów panelu recenzentów")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
