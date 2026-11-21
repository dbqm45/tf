#!/usr/bin/env python3
"""Mode proposal tests (`tf task mode <KEY> --propose [--apply]`, .tf/factory/task_weight.py propose_mode): the factory proposes
how much autonomy a task gets from the gaps in its content, its weight and whether the change is mechanical; it may lower
the mode by itself, raising it is only a proposal for the human; the proposal stays within task.allowed_modes.
python3 .claude/tests/test_mode_proposal.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
CHANGES = Path("docs") / "project" / "changes"
TICKETS = {
    "TYP-1": "# Literówka w README\n\nPopraw literówkę w README: „instlacja” na „instalacja”.\n",
    "REN-1": "# Zmiana nazwy\n\nZmień nazwę funkcji calcFee na calculateFee we wszystkich miejscach.\n",
    "CSV-1": ("# Eksport sesji\n\nJako operator chcę wyeksportować sesje ładowania z wybranego dnia do CSV. "
              "Kryteria akceptacji: plik ma nagłówek i jeden wiersz na sesję.\n"),
    "VAG-1": "# Raporty\n\nRaporty.\n",
    "NOC-1": ("# Filtr regionu\n\nJako operator chcę filtrować listę stacji po regionie, żeby szybciej znaleźć swoje stacje "
              "w panelu.\n"),
    "TBD-1": ("# Powiadomienia\n\nJako kierowca chcę dostać powiadomienie o końcu ładowania. Kanał: do ustalenia (SMS czy push?). "
              "AC1: powiadomienie przychodzi w ciągu minuty.\n"),
    "PRF-1": ("# Wolny raport\n\nRaport miesięczny liczy się kilka minut przy milionach wierszy. Przyspiesz go. "
              "AC1: raport z 1 mln sesji w mniej niż 5 s.\n"),
    "LOG-1": "# Reset hasła\n\nJako użytkownik chcę zresetować hasło linkiem z maila. AC1: link ważny 30 minut.\n",
}


def tf(project: Path, *args: str):
    return subprocess.run([sys.executable, str(TASK), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def propose(project: Path, key: str, *args: str) -> tuple[int, dict, str]:
    r = tf(project, "mode", key, "--propose", *args, "--json")
    try:
        return r.returncode, json.loads(r.stdout), r.stdout + r.stderr
    except ValueError:
        return r.returncode, {}, r.stdout + r.stderr


def task(project: Path, key: str) -> dict:
    return json.loads((project / CHANGES / key / "task.json").read_text(encoding="utf-8"))


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        for key, text in TICKETS.items():
            tf(p, "start", key, "--title", text.splitlines()[0].lstrip("# "))
            (p / CHANGES / key / "ticket.md").write_text(text, encoding="utf-8")
            tf(p, "weight", key, "--apply")

        # the proposal, always with a reason; asking writes nothing
        before = (p / CHANGES / "TYP-1" / "task.json").read_text(encoding="utf-8")
        code, out, raw = propose(p, "TYP-1")
        check(code == 0 and out.get("proposal") == "auto" and out.get("reasons") and out.get("mode") == "normal",
              f"MP-1: a typo → proposal auto with a reason, the mode not changed: {raw}")
        check((p / CHANGES / "TYP-1" / "task.json").read_text(encoding="utf-8") == before, "MP-2: --propose alone writes nothing")
        code, out, raw = propose(p, "REN-1")
        check(out.get("proposal") == "auto" and any("mechanical" in r for r in out.get("reasons", [])),
              f"MP-3: a rename is mechanical → auto: {raw}")
        code, out, raw = propose(p, "CSV-1")
        check(out.get("proposal") == "normal", f"MP-4: a clear task that changes behaviour → normal: {raw}")

        # gaps in the content lower the autonomy
        code, out, raw = propose(p, "VAG-1")
        check(out.get("proposal") == "plan" and any("short" in r for r in out.get("reasons", [])),
              f"MP-5: one word, no criteria → plan (only the spec and the plan): {raw}")
        code, out, raw = propose(p, "NOC-1")
        check(out.get("proposal") == "normal" and any("acceptance criteria" in r for r in out.get("reasons", [])),
              f"MP-6: no acceptance criteria → normal with questions, never auto: {raw}")
        code, out, raw = propose(p, "TBD-1")
        check(out.get("proposal") == "normal" and any("open question" in r for r in out.get("reasons", [])),
              f"MP-7: an open question in the content → normal: {raw}")
        code, out, raw = propose(p, "PRF-1")
        check(out.get("proposal") == "normal" and any("performance" in r for r in out.get("reasons", [])),
              f"MP-8: a performance task → normal (the result needs a measurement and a review): {raw}")
        code, out, raw = propose(p, "LOG-1")
        check(out.get("proposal") == "normal" and any("weight" in r for r in out.get("reasons", [])),
              f"MP-9: the full weight (a sensitive area) → never auto: {raw}")

        # the specification counts: a short story whose criteria were worked out into spec.md is not "too short"
        (p / CHANGES / "VAG-1" / "spec.md").write_text("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given a day, when the operator "
                                                    "opens the report, then it lists the sessions.\n", encoding="utf-8")
        code, out, raw = propose(p, "VAG-1")
        check(out.get("proposal") == "normal", f"MP-17: criteria in spec.md count — a short story with a spec → normal, not plan: {raw}")
        (p / CHANGES / "VAG-1" / "spec.md").unlink()

        # --apply: lowering by itself, raising only as a proposal for the human
        tf(p, "mode", "NOC-1", "auto")                       # the human chose Auto in the command: the factory keeps it
        code, out, raw = propose(p, "NOC-1", "--apply")
        check(task(p, "NOC-1")["mode"] == "auto" and out.get("applied") is False and "human" in raw,
              f"MP-10: a mode the human chose is not lowered, the proposal is shown: {raw}")
        data = task(p, "VAG-1")
        data["mode"] = "auto"                                # Auto from a work style (autonomous), not from the human's command
        (p / CHANGES / "VAG-1" / "task.json").write_text(json.dumps(data), encoding="utf-8")
        code, out, raw = propose(p, "VAG-1", "--apply")
        check(task(p, "VAG-1")["mode"] == "plan" and out.get("applied") is True and task(p, "VAG-1").get("mode_by") == "process:tf",
              f"MP-11: a default mode is lowered by the factory to the proposal, recorded as the process: {raw}")
        code, out, raw = propose(p, "TYP-1", "--apply")
        check(task(p, "TYP-1")["mode"] == "normal" and out.get("applied") is False and "AskUserQuestion" in raw,
              f"MP-12: a more autonomous proposal is not applied — the human is asked: {raw}")

        # within the allowed modes
        (p / ".tf" / "config").mkdir(parents=True, exist_ok=True)
        (p / ".tf" / "config" / "config.yaml").write_text("task:\n  allowed_modes: [plan, normal]\n", encoding="utf-8")
        code, out, raw = propose(p, "TYP-1")
        check(out.get("proposal") == "normal" and any("allowed" in r for r in out.get("reasons", [])),
              f"MP-13: Auto turned off in the project → the proposal stays within the allowed modes: {raw}")

        # a pdi cut keeps the mode approved at the gate
        tf(p, "start", "CHG-1-TSK-1", "--title", "Cięcie", "--change", "CHG-1", "--cut", "TSK-1")
        (p / CHANGES / "CHG-1-TSK-1" / "ticket.md").write_text("# Cięcie\n\nRaporty.\n", encoding="utf-8")
        code, out, raw = propose(p, "CHG-1-TSK-1", "--apply")
        check(code == 0 and out.get("proposal") is None and out.get("applied") is False,
              f"MP-14: a pdi cut gets no proposal (its plan was approved at the gate): {raw}")

    # in the loop: the intake stage shows the proposal and lowers a default mode; the human's --auto is kept
    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        for d in (".claude/skills", ".tf/factory"):          # an installed project: the loop scripts and the engine
            shutil.copytree(ROOT / d, p / d, ignore=shutil.ignore_patterns("__pycache__"))
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(p), "TF_DASHBOARD_OPEN": "0"}
        git = lambda *a: subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=p, capture_output=True)
        git("init", "-q"); git("add", "-A"); git("commit", "-qm", "init")
        py = lambda script, *a: subprocess.run([sys.executable, str(p / ".claude/skills/tf/scripts" / script), *a], cwd=p,
                                               capture_output=True, text=True, timeout=120, env=env)
        r = py("run_report.py", "start", "Raporty", "--story", "Raporty.")
        run = next(iter(sorted((p / ".tf" / "runs").glob("T-*"))), None)
        key = run.name if run else ""
        data = task(p, key) if key else {}
        data["mode"] = "auto"                                # Auto from the person's style (autonomous)
        (p / CHANGES / key / "task.json").write_text(json.dumps(data), encoding="utf-8") if key else None
        r = py("run_state.py", "stage", str(run), "intake") if run else r
        check(run and "Mode: lowered to Plan" in r.stdout + r.stderr and task(p, key)["mode"] == "plan",
              f"MP-15: the intake stage lowers Auto from the style to Plan for one word of content: {r.stdout}{r.stderr}")
        r = py("run_report.py", "start", "Eksport", "--story", "Jako operator chcę eksport sesji do CSV, z nagłówkiem i "
               "jednym wierszem na sesję, bez kryteriów.")
        run2 = next((d for d in sorted((p / ".tf" / "runs").glob("T-*")) if d != run), None)
        r = py("run_state.py", "stage", str(run2), "intake", "--auto") if run2 else r
        check(run2 and task(p, run2.name)["mode"] == "auto" and "chosen by the human" in r.stdout + r.stderr,
              f"MP-16: --auto from the human's command is kept, the proposal is only named: {r.stdout}{r.stderr}")

    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} mode proposal tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
