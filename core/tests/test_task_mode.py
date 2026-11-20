#!/usr/bin/env python3
"""Task mode tests (`tf task mode`): Plan / normal / Auto and entering the implementation stage.
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
        (folder / "plan.md").write_text("# Plan\n- [ ] S1 — eksport · files: export.py\n", encoding="utf-8")
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
        check(r.returncode == 0 and "normal" in r.stdout, f"M-1: the default mode is normal: {r.stdout}{r.stderr}")

        # Plan mode: the run ends at the plan
        r = tf(p, "mode", "A-1", "plan")
        check(r.returncode == 0 and task(p, "A-1").get("mode") == "plan", f"M-2: setting Plan mode: {r.stdout}")
        r = tf(p, "stage", "A-1", "plan")
        check(r.returncode == 0, f"M-3: in Plan mode the task reaches the plan stage: {r.stdout}")
        r = tf(p, "stage", "A-1", "implementation")
        check(r.returncode == 1 and "mode" in r.stdout and "Plan" in r.stdout and "mode A-1 normal" in r.stdout,
              f"M-4: Plan mode does not enter implementation; the message says how to continue: {r.returncode} {r.stdout}")

        # normal mode: a registered plan needs the human's approval
        tf(p, "mode", "A-1", "normal")
        r = tf(p, "stage", "A-1", "implementation")
        check(r.returncode == 1 and "approve A-1 plan.md" in r.stdout and "--auto" in r.stdout,
              f"M-5: normal mode — implementation only after the human approves the plan: {r.returncode} {r.stdout}")
        tf(p, "approve", "A-1", "plan.md", "--by", "human:anna")
        r = tf(p, "stage", "A-1", "implementation")
        check(r.returncode == 0, f"M-6: after approval implementation passes: {r.stdout}")

        # a task run by hand (without a registered plan) works as before
        new_task(p, "A-2", plan=False)
        r = tf(p, "stage", "A-2", "implementation")
        check(r.returncode == 0, f"M-7: without a registered plan normal mode needs no approval: {r.stdout}")

        # Auto mode: without approval, unless the weight is full
        new_task(p, "A-3")
        r = tf(p, "mode", "A-3", "auto")
        r2 = tf(p, "stage", "A-3", "implementation")
        check(r.returncode == 0 and task(p, "A-3").get("mode") == "auto" and r2.returncode == 0,
              f"M-8: Auto mode enters implementation without approval: {r.stdout} | {r2.stdout}")
        new_task(p, "A-4")
        tf(p, "weight", "A-4", "--set", "full")
        r = tf(p, "mode", "A-4", "auto")
        check(r.returncode == 0 and task(p, "A-4").get("mode") == "normal" and "full-weight" in r.stdout and "normal mode" in r.stdout,
              f"M-9: Auto at full weight is unavailable — normal mode stays, with an explanation: {r.returncode} {r.stdout}")
        new_task(p, "A-5")
        tf(p, "mode", "A-5", "auto")
        tf(p, "weight", "A-5", "--set", "full")
        r = tf(p, "stage", "A-5", "implementation")
        check(r.returncode == 1 and "approve A-5 plan.md" in r.stdout,
              f"M-10: weight raised to full in Auto mode — implementation waits for a human: {r.returncode} {r.stdout}")

        r = tf(p, "mode", "A-1", "turbo")
        check(r.returncode == 2, f"M-11: an unknown mode → code 2: {r.returncode} {r.stdout}")
        r = tf(p, "status", "A-3")
        check("mode: auto" in r.stdout, f"M-12: status shows the mode: {r.stdout}")
        new_task(p, "A-6")
        tf(p, "mode", "A-6", "plan")
        r = tf(p, "stage", "A-6", "implementation", "--force")
        check(r.returncode == 0, f"M-13: --force bypasses the mode gate: {r.stdout}")
        r = tf(p, "mode", "NIE-1")
        check(r.returncode != 0 and "Traceback" not in r.stderr, f"M-14: no task → an error without an exception: {r.returncode}")

        # a pdi change-cut task (step E6): the change plan was approved at the pdi gate, so full weight does not stop
        # an unattended run; in normal mode a human is present and approves the plan as in any task
        tf(p, "start", "CHG-12-TSK-57", "--title", "TSK-57: ponowienie płatności", "--change", "CHG-12", "--cut", "TSK-57")
        folder = p / CHANGES / "CHG-12-TSK-57"
        (folder / "ticket.md").write_text("# TSK-57\n\nCięcie TSK-57 zmiany CHG-12.\n", encoding="utf-8")
        (folder / "plan.md").write_text("# Plan\n- [ ] S1 — ponowienie · files: pay.py\n", encoding="utf-8")
        tf(p, "artifact", "CHG-12-TSK-57", "plan.md", "--stage", "plan", "--by", "process:tf", "--inputs", "ticket.md")
        tf(p, "weight", "CHG-12-TSK-57", "--set", "full")
        r = tf(p, "stage", "CHG-12-TSK-57", "implementation")
        check(r.returncode == 1 and "approve CHG-12-TSK-57 plan.md" in r.stdout,
              f"M-15: a full-weight cut in normal mode waits for the human's approval: {r.returncode} {r.stdout}")
        r = tf(p, "mode", "CHG-12-TSK-57", "auto")
        check(r.returncode == 0 and task(p, "CHG-12-TSK-57").get("mode") == "auto" and "CHG-12" in r.stdout
              and "pdi gate" in r.stdout,
              f"M-16: a full-weight cut gets Auto mode with an explanation (the change gate): {r.returncode} {r.stdout}")
        r = tf(p, "stage", "CHG-12-TSK-57", "implementation")
        check(r.returncode == 0, f"M-17: a full-weight cut in Auto mode enters implementation without approval: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} task mode tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
