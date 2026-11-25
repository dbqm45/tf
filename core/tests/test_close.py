#!/usr/bin/env python3
"""Closing a task (step G4): `tf task close` closes only a merged change, requires a control for every important
review finding, reminds about the flag, records a lesson given by the human (with evidence; without it the lesson is parked
as unverified); `tf status` shows tasks in progress.
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
PROOF = "https://github.com/acme/app/pull/41#discussion_r1"
FINDING = "usunięta asercja testu limitu przy końcu doby"
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci, then opłata wynosi "
        "45 zł.\n\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")


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
    """A repository with a task at the pr stage; `merged` — the task directory is already on the main branch (squash merge)."""
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
        # unmerged change: refusal; the human may close it anyway
        p = Path(t) / "unmerged"
        new_task(p, merged=False)
        git(p, "checkout", "-q", "story/imp-1")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 1 and "merged" in r.stdout and task(p)["stage"] == "pr" and "closed" not in task(p),
              f"CL-1: an unmerged change cannot be closed: {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--force")
        check(r.returncode == 2 and "human:" in r.stdout and task(p)["stage"] == "pr",
              f"CL-2: closing despite no merge is the human's decision (--force --by human:<id>): {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--force", "--by", "human:anna")
        check(r.returncode == 0 and task(p)["stage"] == "closed" and task(p)["closed"].get("forced") is True
              and task(p)["closed"].get("by") == "human:anna",
              f"CL-3: the human closes despite no merge confirmation; record in the task: {r.stdout} {task(p).get('closed')}")

        # merged change (squash): closing succeeds
        p = Path(t) / "merged"
        new_task(p)
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and task(p)["stage"] == "closed" and task(p)["closed"].get("at")
              and "closed" in r.stdout and "forced" not in task(p)["closed"],
              f"CL-4: scalona zmiana (squash) → etap closed i zapis closed: {r.returncode} {r.stdout}")
        check("smoke test" in r.stdout,
              f"CL-5: closing says explicitly that the deployment was not checked with a smoke test: {r.stdout}")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and "already" in r.stdout, f"CL-6: closing again is not an error: {r.returncode} {r.stdout}")

        # important review findings: no closing without a control
        p = Path(t) / "findings"
        new_task(p)
        r1 = call(p, TASK, "finding", "IMP-1", "add", FINDING, "--slice", "S1")
        r2 = call(p, TASK, "finding", "IMP-1", "add", "code outside the criteria in msg.py")
        fs = task(p).get("findings") or []
        check(r1.returncode == 0 and r2.returncode == 0 and [f.get("id") for f in fs] == ["F1", "F2"]
              and fs[0].get("text") == FINDING and fs[0].get("slice") == "S1" and fs[0].get("at") and "F1" in r1.stdout,
              f"CL-7: important findings recorded in the task with an id, slice and date: {r1.stdout} {fs}")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 1 and "F1" in r.stdout and "F2" in r.stdout and "finding IMP-1 control" in r.stdout
              and task(p)["stage"] == "pr",
              f"CL-8: a finding without a control blocks closing; the message gives the command: {r.returncode} {r.stdout}")
        r = call(p, TASK, "finding", "IMP-1", "control", "F9", "test")
        check(r.returncode != 0 and "F9" in r.stdout, f"CL-9: a control for an unknown finding → refusal: {r.returncode} {r.stdout}")
        call(p, TASK, "finding", "IMP-1", "control", "F1", "test test_fees.py::test_cap_at_midnight")
        call(p, TASK, "finding", "IMP-1", "control", "F2", "no control: a one-off mistake during the merge")
        r = call(p, TASK, "status", "IMP-1")
        check("F1" in r.stdout and "test_cap_at_midnight" in r.stdout and FINDING in r.stdout,
              f"CL-10: tf task status shows the findings with controls: {r.stdout}")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and task(p)["stage"] == "closed",
              f"CL-11: after recording the controls closing succeeds: {r.returncode} {r.stdout}")

        p = Path(t) / "odd"
        new_task(p)
        f = p / CHANGES / "IMP-1" / "task.json"
        f.write_text(json.dumps({**task(p), "deploy": {"state": ["ok"]}}), encoding="utf-8")
        r = call(p, TASK, "close", "IMP-1", "--force", "--by", "human:anna")
        check(r.returncode == 0 and "Traceback" not in r.stderr,
              f"CL-31: an unusual deployment record in task.json does not break closing: {r.stderr[-200:]}")

        # a red smoke test without a decision blocks closing
        p = Path(t) / "red"
        new_task(p)
        card = p / ".tf" / "config" / "operations.json"
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text(json.dumps({"deploy": {"smoke": f'{sys.executable} -c "raise SystemExit(7)"'}}), encoding="utf-8")
        call(p, TASK, "deployed", "IMP-1")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 1 and "rollback" in r.stdout and task(p)["stage"] == "pr",
              f"CL-12: a deployment waiting for a rollback decision blocks closing: {r.returncode} {r.stdout}")

        # flag: a reminder about the removal date or its absence
        p = Path(t) / "flag"
        new_task(p)
        call(p, TASK, "flag", "IMP-1", "set", "limit-dobowy", "--remove-by", "2027-01-31")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and "limit-dobowy" in r.stdout and "2027-01-31" in r.stdout,
              f"CL-13: closing reminds about the flag removal date: {r.stdout}")
        p = Path(t) / "flag2"
        new_task(p)
        call(p, TASK, "flag", "IMP-1", "set", "limit-dobowy")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 0 and "limit-dobowy" in r.stdout and "--remove-by" in r.stdout,
              f"CL-14: a flag without a removal date → a reminder how to set it: {r.stdout}")

        # lesson: only from the human, with an "Instead" part, added once
        p = Path(t) / "lesson"
        new_task(p)
        lessons = p / "docs" / "project" / "lessons.md"
        r = call(p, TASK, "close", "IMP-1", "--lesson", LESSON)
        check(r.returncode == 2 and "human:" in r.stdout and not lessons.exists() and task(p)["stage"] == "pr",
              f"CL-15: the human records the lesson (--by human:<id>): {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--lesson", "Watch the daily limit", "--by", "human:anna")
        check(r.returncode == 2 and "Instead" in r.stdout and not lessons.exists(),
              f"CL-16: a lesson without 'Instead:' is not a lesson: {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--evidence", PROOF, "--by", "human:anna")
        text = lessons.read_text(encoding="utf-8") if lessons.is_file() else ""
        check(r.returncode == 0 and text.count(LESSON) == 1 and "IMP-1" in text and text.startswith("# ")
              and f"Evidence: {PROOF}" in text
              and task(p)["closed"].get("lesson") is True,
              f"CL-17: the human's lesson goes to docs/project/lessons.md with the date and the task key: {r.stdout} {text}")
        call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--evidence", PROOF, "--by", "human:anna")
        check((lessons.read_text(encoding="utf-8") if lessons.is_file() else "").count(LESSON) == 1,
              "CL-18: the same lesson is not added a second time")
        check("lessons.md" not in call(Path(t) / "merged", TASK, "status", "IMP-1").stdout
              and not (Path(t) / "merged" / "docs" / "project" / "lessons.md").exists(),
              "CL-19: without --lesson the factory adds nothing to the lessons")

        p = Path(t) / "lesson2"
        new_task(p)
        lessons = p / "docs" / "project" / "lessons.md"
        lessons.parent.mkdir(parents=True, exist_ok=True)
        old = ("# Lekcje projektu\n\n## Execution and verification\n\n- 2026-01-01 **Stara lekcja** — Kontekst: x · Zamiast "
               "tego: y\n\n## Powłoka i narzędzia\n\n- 2026-01-02 **Inna** — Kontekst: x · Zamiast tego: y\n")
        lessons.write_text(old, encoding="utf-8")
        call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--evidence", "abc1234", "--by", "human:anna")
        text = lessons.read_text(encoding="utf-8")
        check(text.count("## Execution and verification") == 1 and "## Powłoka i narzędzia" in text
              and text.index(LESSON) < text.index("Stara lekcja") < text.index("## Powłoka") and "Inna" in text
              and old.split("\n## Execution and verification\n\n", 1)[1] in text,
              f"CL-30: the lesson goes under the existing heading, above older entries; the rest of the file is unchanged: {text}")

        p = Path(t) / "lesson3"
        new_task(p)
        lessons = p / "docs" / "project" / "lessons.md"
        en = "**Check the daily cap at midnight** — Context: parking fees · Instead: test a stay over midnight · Applies to: implementation"
        (p / ".tf" / "runs" / "IMP-1").mkdir(parents=True)
        (p / ".tf" / "runs" / "IMP-1" / "report.md").write_text("# Report\n", encoding="utf-8")
        r = call(p, TASK, "close", "IMP-1", "--lesson", en, "--by", "human:anna",
                 "--evidence", ".tf/runs/IMP-1/report.md: verify 27 min, 2 identical runs")
        text = lessons.read_text(encoding="utf-8") if lessons.is_file() else ""
        check(r.returncode == 0 and text.startswith("# Project lessons") and "## Execution and verification" in text
              and en in text and "Task: IMP-1" in text and "Evidence: .tf/runs/IMP-1/report.md: verify 27 min" in text,
              f"CL-31: the lesson in the Context / Instead / Applies to format, a new file with an English heading: {r.stdout} {text}")

        # evidence: required for lessons.md; a missing local file is refused; no evidence → parked as unverified
        p = Path(t) / "lesson4"
        new_task(p)
        lessons, parked = p / "docs" / "project" / "lessons.md", p / "docs" / "project" / "parked.md"
        r = call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--by", "human:anna",
                 "--evidence", ".tf/runs/IMP-1/evidence/S1-2.json")
        check(r.returncode == 2 and "S1-2.json" in r.stdout and "does not exist" in r.stdout and not lessons.exists()
              and task(p)["stage"] == "pr",
              f"CL-32: an evidence path that does not exist is refused, the task stays open: {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--by", "human:anna", "--evidence", "  ")
        check(r.returncode == 2 and "empty" in r.stdout and not lessons.exists(),
              f"CL-33: an empty evidence pointer is refused: {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--evidence", PROOF, "--by", "human:anna")
        check(r.returncode == 2 and "--lesson" in r.stdout and task(p)["stage"] == "pr",
              f"CL-34: --evidence goes with --lesson: {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--by", "human:anna")
        ptext = parked.read_text(encoding="utf-8") if parked.is_file() else ""
        lines = [ln for ln in r.stdout.splitlines() if "lesson:" in ln]
        check(r.returncode == 0 and task(p)["stage"] == "closed" and not lessons.exists()
              and "unverified lesson" in ptext and LESSON in ptext and len(lines) == 1 and "parked" in lines[0]
              and task(p)["closed"].get("lesson_parked") is True and "lesson" not in task(p)["closed"],
              f"CL-35: a lesson without evidence is parked as unverified, not in lessons.md; one line says so: "
              f"{r.stdout} {ptext}")
        r = call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--by", "human:anna", "--evidence", "fees.py")
        text = lessons.read_text(encoding="utf-8") if lessons.is_file() else ""
        check(r.returncode == 0 and LESSON in text and "Evidence: fees.py" in text and task(p)["closed"].get("lesson") is True,
              f"CL-36: a parked lesson given again with evidence after closing goes to lessons.md: {r.stdout} {text}")

        p = Path(t) / "lesson5"
        new_task(p)
        (p / ".tf" / "runs" / "IMP-1").mkdir(parents=True)
        r = call(p, TASK, "close", "IMP-1", "--lesson", LESSON, "--by", "human:anna")
        run_parked = p / ".tf" / "runs" / "IMP-1" / "parked.md"
        check(r.returncode == 0 and run_parked.is_file() and "unverified lesson" in run_parked.read_text(encoding="utf-8")
              and not (p / "docs" / "project" / "parked.md").exists(),
              f"CL-37: with a run directory the unverified lesson goes to the task's parked.md: {r.stdout}")

        # tf status: closed tasks are not on the in-progress list
        p = Path(t) / "merged"
        new_task(p, key="IMP-2")
        r = call(p, TASK, "list")
        check("IMP-2" in r.stdout and "IMP-1" not in r.stdout and "closed: 1" in r.stdout and "--all" in r.stdout,
              f"CL-20: tf status shows tasks in progress, counts the closed ones in one line: {r.stdout}")
        r = call(p, TASK, "list", "--all")
        check("IMP-1" in r.stdout and "IMP-2" in r.stdout, f"CL-21: tf status --all pokazuje wszystkie: {r.stdout}")
        r = call(p, TASK, "list", "--json")
        check({x["key"] for x in json.loads(r.stdout)} == {"IMP-1", "IMP-2"},
              f"CL-22: the --json result contains all tasks as before: {r.stdout[:200]}")

        # a directory without git: the merge cannot be confirmed
        p = Path(t) / "nogit"
        p.mkdir()
        call(p, TASK, "start", "IMP-1", "--title", "Limit dobowy")
        call(p, TASK, "stage", "IMP-1", "pr", "--force")
        r = call(p, TASK, "close", "IMP-1")
        check(r.returncode == 1 and "--force" in r.stdout and "Traceback" not in r.stdout + r.stderr,
              f"CL-23: without a git repository the merge cannot be confirmed — a refusal with a way out for the human: {r.returncode} {r.stdout}")
        r = call(p, TASK, "close", "IMP-9")
        check(r.returncode != 0 and "there is no task" in r.stdout, f"CL-24: nieznane zadanie → odmowa: {r.stdout}")

    # loop: a failed scope review requires a recorded finding from this round
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        p.mkdir()
        rs = SCRIPTS / "run_state.py"
        call(p, SCRIPTS / "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
        d = str(p / ".tf" / "runs" / "IMP-1")
        call(p, rs, "weight", d, "--set", "normal")
        call(p, TASK, "mode", "IMP-1", "auto")
        (p / CHANGES / "IMP-1" / "spec.md").write_text(SPEC, encoding="utf-8")
        call(p, rs, "flag", d, "none", "--reason", "no flag, because the change is in configuration")
        call(p, rs, "step", d, "S1", "R1", "code", "run")
        r = call(p, rs, "step", d, "S1", "R1", "scope", "fail")
        check(r.returncode == 2 and "finding" in r.stdout and "S1" in r.stdout and not task(p).get("findings"),
              f"CL-25: `zakres fail` bez zapisanego ustalenia → odmowa z poleceniem: {r.returncode} {r.stdout}")
        r = call(p, rs, "finding", d, "S1", FINDING)
        fs = task(p).get("findings") or []
        check(r.returncode == 0 and len(fs) == 1 and fs[0].get("slice") == "S1" and fs[0].get("round") == 1
              and fs[0].get("text") == FINDING,
              f"CL-26: run_state.py finding records the finding with the slice and round: {r.returncode} {r.stdout} {fs}")
        r = call(p, rs, "step", d, "S1", "R1", "scope", "fail")
        check(r.returncode == 0, f"CL-27: po zapisie ustalenia `zakres fail` przechodzi: {r.returncode} {r.stdout}")
        call(p, rs, "step", d, "S1", "R2", "code", "run")
        r = call(p, rs, "step", d, "S1", "R2", "scope", "fail")
        check(r.returncode == 2 and "finding" in r.stdout,
              f"CL-28: the second round requires its own finding: {r.returncode} {r.stdout}")
        r = call(p, rs, "step", d, "S1", "R2", "scope", "pass")
        check(r.returncode == 0, f"CL-29: `zakres pass` does not require a finding: {r.returncode} {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} task closing tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
