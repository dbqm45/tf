#!/usr/bin/env python3
"""A blocked slice instead of STOP (step F3, the `loop.blocked_slices` switch): a question blocks only its own
slice, the script says which slice can be done next, and records the questions and answers in the task's `events.jsonl`.
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
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci, then opłata wynosi "
        "45 zł.\n\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")
PLAN = ("# Plan: Limit dobowy\n\n"
        "- [ ] S1 — limit dobowy · criteria: AC-1 · files: fees.py · verify: `pytest`\n"
        "- [ ] S2 — komunikat o limicie · files: msg.py · after: none\n"
        "- [ ] S3 — tłumaczenie komunikatu · files: i18n.py\n"
        "- [ ] S4 — raport limitów · files: report.py · after: S1\n")
QUESTION = "Czy limit dotyczy też abonamentów?"


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
           "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          timeout=120)


def new_run(project: Path, plan: str = PLAN) -> str:
    """Task IMP-1 ready for the slice loop: normal weight, Auto mode, a spec, no flag, a plan."""
    project.mkdir(parents=True)
    for name in ("fees.py", "msg.py", "i18n.py", "report.py"):
        (project / name).write_text("x = 1\n", encoding="utf-8")
    call(project, SCRIPTS / "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
    d = str(project / ".tf" / "runs" / "IMP-1")
    call(project, SCRIPTS / "run_state.py", "weight", d, "--set", "normal")
    call(project, TASK, "mode", "IMP-1", "auto")
    doc = project / CHANGES / "IMP-1"
    (doc / "spec.md").write_text(SPEC, encoding="utf-8")
    (doc / "plan.md").write_text(plan, encoding="utf-8")
    call(project, SCRIPTS / "run_state.py", "flag", d, "none", "--reason", "no flag, because the change is in configuration")
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
    call(project, SCRIPTS / "run_state.py", "step", d, slice_id, "R1", "scope", "pass")   # scope review before the tick
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

        # the switch off (default): the loop works as before — a question is a STOP block
        r = call(p, rs, "block", d, "S1", "--question", QUESTION)
        check(r.returncode == 2 and "loop.blocked_slices" in r.stdout and "--code question" in r.stdout
              and not events(p) and (task(p).get("slices") or {}).get("S1", {}).get("state") != "blocked",
              f"WE-1: without the switch `block` refuses and points to STOP with the code question: {r.returncode} {r.stdout}")
        call(p, rs, "step", d, "S1", "R1", "test", "run")
        r = call(p, rs, "stage", d, "needs", "--needs", "stop", "--code", "question", "--reason", QUESTION)
        check(r.returncode == 0, f"WE-2: without the switch STOP with the code question passes as before: {r.returncode} {r.stdout}")
        call(p, rs, "step", d, "S1", "R1", "test", "run")

        switch(p, True)
        # STOP with a question about the current slice when an independent slice exists → a refusal with a `block` hint
        r = call(p, rs, "stage", d, "needs", "--needs", "stop", "--code", "question", "--reason", QUESTION)
        check(r.returncode == 2 and "block" in r.stdout and "S2" in r.stdout and "--task" in r.stdout,
              f"WE-3: with the switch a STOP with a question about one slice is rejected when there is something else to do: {r.returncode} {r.stdout}")
        r = call(p, rs, "block", d, "S1", "--question", QUESTION)
        ev = events(p)
        check(r.returncode == 0 and "Next: S2" in r.stdout and task(p)["slices"]["S1"].get("state") == "blocked"
              and task(p)["slices"]["S1"].get("reason") == QUESTION,
              f"WE-4: block blocks only S1 and points to the independent slice S2: {r.returncode} {r.stdout} {task(p).get('slices')}")
        check(len(ev) == 1 and ev[0].get("type") == "question" and ev[0].get("slice") == "S1"
              and ev[0].get("text") == QUESTION and ev[0].get("by") == "process:tf" and ev[0].get("at"),
              f"WE-5: pytanie zapisane w events.jsonl zadania (kto, kiedy, co): {ev}")
        r = call(p, TASK, "list")
        check("waiting for you" in r.stdout and "S1" in r.stdout and QUESTION in r.stdout,
              f"WE-6: the blocked slice's question is on the 'waiting for you' list: {r.stdout}")

        # order by dependencies: S3 (without a suffix) depends on S2, S4 depends on the blocked S1
        done(p, d, "S2", "msg.py")
        r = call(p, rs, "next", d)
        check(r.returncode == 0 and "Next: S3" in r.stdout, f"WE-7: after S2 comes S3 (it depends on the previous one): {r.stdout}")
        done(p, d, "S3", "i18n.py")
        r = call(p, rs, "next", d)
        check(r.returncode == 0 and "Next: STOP" in r.stdout and QUESTION in r.stdout and "--code question" in r.stdout
              and "S4" in r.stdout,
              f"WE-8: when nothing independent is left (S4 waits for S1) → STOP with a list of questions: {r.stdout}")
        r = call(p, rs, "stage", d, "needs", "--needs", "stop", "--code", "question", "--reason", QUESTION)
        check(r.returncode == 0, f"WE-9: STOP with a question passes when there is no slice left to do: {r.returncode} {r.stdout}")

        # the human's answer unblocks the slice
        r = call(p, rs, "answer", d, "S1", "Nie, tylko postój jednorazowy")
        check(r.returncode == 2 and "human:" in r.stdout and task(p)["slices"]["S1"].get("state") == "blocked",
              f"WE-10: the answer is recorded with the human's identifier (--by human:<id>): {r.returncode} {r.stdout}")
        r = call(p, rs, "answer", d, "S1", "Nie, tylko postój jednorazowy", "--by", "human:anna")
        ev = events(p)
        check(r.returncode == 0 and "Next: S1" in r.stdout and task(p)["slices"]["S1"].get("state") != "blocked"
              and len(ev) == 2 and ev[1].get("type") == "answer" and ev[1].get("by") == "human:anna"
              and ev[1].get("text") == "Nie, tylko postój jednorazowy" and ev[1].get("slice") == "S1",
              f"WE-11: answer unblocks S1, records the answer and points to it as the next one: {r.returncode} {r.stdout} {ev}")
        r = call(p, TASK, "list")
        check("waiting for you" not in r.stdout, f"WE-12: after the answer nothing waits: {r.stdout}")

    # a plan without dependencies: slices go in order, so a question in S1 stops the run as before
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        d = new_run(p, PLAN.replace(" · after: none", "").replace(" · after: S1", ""))
        switch(p, True)
        call(p, rs, "step", d, "S1", "R1", "test", "run")
        r = call(p, rs, "block", d, "S1", "--question", QUESTION)
        check(r.returncode == 0 and "Next: STOP" in r.stdout and "--code question" in r.stdout,
              f"WE-13: a plan without 'po:' suffixes — a question in S1 leaves nothing to do: {r.stdout}")
        # a question about the whole task: STOP right away, without blocking a slice
        r = call(p, rs, "stage", d, "needs", "--needs", "stop", "--code", "question", "--reason", QUESTION, "--task")
        check(r.returncode == 0, f"WE-14: `--task` (a question about the whole task) lets STOP through: {r.returncode} {r.stdout}")
        r = call(p, rs, "stage", d, "plan")
        check("after:" in r.stdout and "after: none" in r.stdout,
              f"WE-15: the plan stage with the switch on reminds to record the slice dependencies: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} blocked slice tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
