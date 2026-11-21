#!/usr/bin/env python3
"""Ending a slice with one command: `run_state.py done <dir> S<n> --message "<type>(<scope>): <description>"` records
a passed scope review of the current round, commits the evidence files (with the body `Slice S<n>: …` and footers),
ticks the slice and gives the next one. Without current evidence or with a bad title it records nothing.
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
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci kartą, then opłata "
        "wynosi 45 zł.\n\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")
PLAN = ("# Plan\n\n- [ ] S1 — płatność kartą · criteria: AC-1 · files: pay.py\n"
        "- [ ] S2 — paragon · criteria: AC-1 · files: pay.py\n")


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
    """Run IMP-1 with an approved plan (S1, S2), a test and S1's code; returns the run directory."""
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
    call(p, SCRIPT, "flag", d, "none", "--reason", "no flag, because the change is approved by a human in the plan")
    call(p, SCRIPT, "stage", d, "plan")
    call(p, SCRIPT, "approve", d)
    call(p, SCRIPT, "step", d, "S1", "R1", "test", "run")
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
        (p / "notes.txt").write_text("a draft outside the slice\n", encoding="utf-8")

        # without evidence: refusal, nothing recorded
        r = call(p, SCRIPT, "done", d, "S1", "--message", "feat(pay): card payment")
        cur = meta(d).get("current") or {}
        check(r.returncode != 0 and "verify" in r.stdout + r.stderr and len(commits(p)) == 1
              and "- [x] S1" not in plan_text(p) and (cur.get("rounds") or [{}])[-1].get("scope") != "pass",
              f"DN-1: without evidence done refuses and records nothing: {r.returncode} {r.stdout}{r.stderr} {cur}")

        call(p, SCRIPT, "verify", d, "S1", "--files", "pay.py,test_pay.py", "--command", OK)
        # a bad title: refusal before recording
        r = call(p, SCRIPT, "done", d, "S1", "--message", "added payment")
        check(r.returncode != 0 and "Conventional" in r.stdout + r.stderr and len(commits(p)) == 1
              and "- [x] S1" not in plan_text(p),
              f"DN-2: a title outside Conventional Commits → refusal before the commit: {r.returncode} {r.stdout}{r.stderr}")

        r = call(p, SCRIPT, "done", d, "S1", "--message", "feat(pay): card payment")
        log = commits(p)
        files = set(git(p, "show", "--name-only", "--format=", "HEAD").stdout.split())
        check(r.returncode == 0 and len(log) == 2 and log[0].startswith("feat(pay): card payment")
              and "Slice S1: płatność kartą" in log[0],
              f"DN-3: a commit with the title and the body “Slice S1: <value from the plan>”: {r.returncode} {r.stdout}{r.stderr} {log[:1]}")
        check(files == {"pay.py", "test_pay.py"} and "notes.txt" in git(p, "status", "--porcelain").stdout,
              f"DN-4: the commit covers only the evidence files, the rest stays uncommitted: {files}")
        cur = meta(d).get("current") or {}
        check(cur.get("k") == "S1" and (cur.get("rounds") or [{}])[-1].get("scope") == "pass",
              f"DN-5: a passed scope review of the current round recorded: {cur}")
        check("- [x] S1" in plan_text(p) and "- [ ] S2" in plan_text(p) and "Next: S2" in r.stdout,
              f"DN-6: the slice ticked, the output gives the next one: {r.stdout} {plan_text(p)}")

        # repeat: nothing new to commit, no new commit, code 0
        r = call(p, SCRIPT, "done", d, "S1", "--message", "feat(pay): card payment")
        check(r.returncode == 0 and len(commits(p)) == 2,
              f"DN-7: a repeated done without file changes does not create a commit: {r.returncode} {r.stdout}{r.stderr} {len(commits(p))}")

        # second round: the R1 review did not pass, done records R2; a body with “Slice” is not duplicated; a flag → a footer
        call(p, TASK, "flag", "IMP-1", "set", "imp_1_paragon", "--remove-by", "2027-01-31")
        call(p, SCRIPT, "step", d, "S2", "R1", "test", "run")
        (p / "pay.py").write_text("FEE = 45\nRECEIPT = True\n", encoding="utf-8")
        call(p, SCRIPT, "verify", d, "S2", "--files", "pay.py,test_pay.py", "--command", OK)
        call(p, SCRIPT, "finding", d, "S2", "paragon drukuje się dwa razy [ważne]", "--round", "1")
        call(p, SCRIPT, "step", d, "S2", "R1", "scope", "fail")
        call(p, SCRIPT, "step", d, "S2", "R2", "code", "run")
        (p / "pay.py").write_text("FEE = 45\nRECEIPT = 1\n", encoding="utf-8")
        call(p, SCRIPT, "verify", d, "S2", "--files", "pay.py,test_pay.py", "--command", OK)
        r = call(p, SCRIPT, "done", d, "S2", "--message", "feat(pay): print receipt\n\nSlice S2: paragon")
        log = commits(p)
        rounds = (meta(d).get("current") or {}).get("rounds") or []
        check(r.returncode == 0 and len(rounds) == 2 and rounds[0].get("scope") == "fail"
              and rounds[1].get("scope") == "pass",
              f"DN-8: done records the review of the current round (R2), R1 stays fail: {r.returncode} {r.stdout}{r.stderr} {rounds}")
        check(log[0].count("Slice S2") == 1 and "Flag: imp_1_paragon" in log[0],
              f"DN-9: the “Slice” footer is not duplicated, the task's flag adds a footer: {log[:1]}")
        check("- [x] S2" in plan_text(p) and "finishing" in r.stdout,
              f"DN-10: the last slice ticked, the output speaks of finishing: {r.stdout}")

        # a file changed after the evidence: refusal
        p = base / "stale"
        d = prepare(p)
        call(p, SCRIPT, "verify", d, "S1", "--files", "pay.py,test_pay.py", "--command", OK)
        (p / "pay.py").write_text("FEE = 46\n", encoding="utf-8")
        r = call(p, SCRIPT, "done", d, "S1", "--message", "feat(pay): card payment")
        check(r.returncode != 0 and len(commits(p)) == 1 and "- [x] S1" not in plan_text(p),
              f"DN-11: a file changed after the evidence → refusal without a commit: {r.returncode} {r.stdout}{r.stderr}")

        # commit refusal (the commit-msg hook): the slice unticked, git's output in the response
        p = base / "hook"
        d = prepare(p)
        hook = p / ".git" / "hooks" / "commit-msg"
        hook.write_text("#!/bin/sh\necho 'brak stopki Change' >&2\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        call(p, SCRIPT, "verify", d, "S1", "--files", "pay.py,test_pay.py", "--command", OK)
        r = call(p, SCRIPT, "done", d, "S1", "--message", "feat(pay): card payment")
        check(r.returncode != 0 and "brak stopki Change" in r.stdout + r.stderr and "- [x] S1" not in plan_text(p),
              f"DN-12: a commit rejected by the hook → code ≠ 0, the slice unticked: {r.returncode} {r.stdout}{r.stderr}")

    # the skill content leads through done
    skill = (ROOT / ".claude" / "skills" / "tf-task" / "SKILL.md").read_text(encoding="utf-8")
    check("run_state.py done" in skill, "DN-13: SKILL.md directs the end of a slice to `run_state.py done`")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} slice completion tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
