#!/usr/bin/env python3
"""Tests of protecting the spec and the approved task files from being written during implementation
(.claude/hooks/guard_paths.py, `tf task freeze|reopen`). python3 .claude/tests/test_task_oracle.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
GUARD = ROOT / ".claude" / "hooks" / "guard_paths.py"
CHANGES = Path("docs") / "project" / "changes"
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci, then opłata wynosi 45 zł.\n"
        "\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")


def tf(project: Path, *args: str):
    return subprocess.run([sys.executable, str(TASK), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def guard(project: Path, tool: str, rel: str, absolute: bool = True) -> tuple[str, str]:
    """The hook's decision for a tool and a file: ("ask" | "deny" | "", reason)."""
    path = str(project / rel) if absolute else rel
    data = {"tool_name": tool, "tool_input": {"file_path": path}, "cwd": str(project)}
    r = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(data), capture_output=True, text=True, timeout=30,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})
    try:
        out = json.loads(r.stdout)["hookSpecificOutput"]
        return out.get("permissionDecision", ""), out.get("permissionDecisionReason", "")
    except (ValueError, KeyError):
        return "", r.stdout + r.stderr


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
        tf(p, "start", "PROJ-1", "--title", "Limit dobowy")
        tf(p, "mode", "PROJ-1", "auto")          # the test is about file protection, not plan approval (normal mode, step E3)
        folder = p / CHANGES / "PROJ-1"
        (folder / "spec.md").write_text(SPEC, encoding="utf-8")
        (folder / "plan.md").write_text("# Plan\n- [ ] S1 — limit\n", encoding="utf-8")
        (p / "tests").mkdir()
        (p / "tests" / "test_fees.py").write_text("def test_ac1_limit():  # AC-1\n    assert True\n", encoding="utf-8")
        (p / "src.py").write_text("x = 1\n", encoding="utf-8")
        spec_rel = f"{CHANGES.as_posix()}/PROJ-1/spec.md"

        # the spec: before implementation it is written freely, from the implementation stage a write needs the human's consent
        d, why = guard(p, "Write", spec_rel)
        check(d == "", f"O-1: spec.md in the intake stage — a write without asking: {d} {why}")
        tf(p, "stage", "PROJ-1", "plan")
        d, why = guard(p, "Edit", spec_rel)
        check(d == "", f"O-2: spec.md in the plan stage — a write without asking: {d} {why}")
        tf(p, "stage", "PROJ-1", "implementation")
        d, why = guard(p, "Edit", spec_rel)
        check(d == "ask" and "PROJ-1" in why and "changes the requirements" in why, f"O-3: spec.md in the implementation stage → ask with an explanation: {d} {why}")
        d, why = guard(p, "Write", spec_rel, absolute=False)
        check(d == "ask", f"O-4: a relative path works the same: {d} {why}")
        d, why = guard(p, "Read", spec_rel)
        check(d == "", f"O-5: reading the spec without asking: {d} {why}")
        d, why = guard(p, "Edit", f"{CHANGES.as_posix()}/PROJ-1/plan.md")
        check(d == "", f"O-6: an unapproved plan — a write without asking: {d} {why}")
        d, why = guard(p, "Edit", "src.py")
        check(d == "", f"O-7: a file outside the task unchanged: {d} {why}")

        # files that only the script writes
        for rel in (f"{CHANGES.as_posix()}/PROJ-1/task.json", f"{CHANGES.as_posix()}/INDEX.md",
                    f"{CHANGES.as_posix()}/PROJ-1/evidence/S1-1.json"):
            d, why = guard(p, "Write", rel)
            check(d == "ask" and "tf task" in why, f"O-8: {rel} is written only by `tf task` → ask: {d} {why}")

        # a task file approved by a human: a write needs consent; reopen removes the approval with a reason
        tf(p, "artifact", "PROJ-1", "plan.md", "--stage", "plan", "--by", "process:tf", "--inputs", "spec.md")
        tf(p, "approve", "PROJ-1", "plan.md", "--by", "human:anna")
        d, why = guard(p, "Edit", f"{CHANGES.as_posix()}/PROJ-1/plan.md")
        check(d == "ask" and "tf task reopen PROJ-1 plan.md" in why, f"O-9: an approved plan → ask with the reopen command: {d} {why}")
        r = tf(p, "reopen", "PROJ-1", "plan.md", "--by", "process:tf", "--reason", "x")
        check(r.returncode == 2, f"O-10: reopen only by a human: {r.returncode} {r.stdout}")
        r = tf(p, "reopen", "PROJ-1", "plan.md", "--by", "human:anna")
        check(r.returncode == 2 and "--reason" in r.stdout, f"O-11: reopen requires a reason: {r.returncode} {r.stdout}")
        r = tf(p, "reopen", "PROJ-1", "plan.md", "--by", "human:anna", "--reason", "requirements change: limit 50 PLN")
        task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
        log = task.get("reopened") or []
        check(r.returncode == 0 and task["artifacts"]["plan.md"]["status"] == "draft"
              and log and log[-1].get("file") == "plan.md" and "limit 50" in log[-1].get("reason", "")
              and log[-1].get("by") == "human:anna",
              f"O-12: reopen removes the approval and records the reason: {r.stdout} {log}")
        d, why = guard(p, "Edit", f"{CHANGES.as_posix()}/PROJ-1/plan.md")
        check(d == "", f"O-13: after reopen a plan write without asking: {d} {why}")

        # an acceptance test frozen by a human (a file outside the task directory)
        r = tf(p, "freeze", "PROJ-1", "tests/test_fees.py", "--by", "process:tf")
        check(r.returncode == 2, f"O-14: freeze only by a human: {r.returncode} {r.stdout}")
        r = tf(p, "freeze", "PROJ-1", "tests/no-such-file.py", "--by", "human:anna")
        check(r.returncode == 2, f"O-15: freeze of a nonexistent file → code 2: {r.returncode} {r.stdout}")
        r = tf(p, "freeze", "PROJ-1", "tests/test_fees.py", "--by", "human:anna")
        check(r.returncode == 0, f"O-16: freeze records the test file: {r.returncode} {r.stdout}{r.stderr}")
        d, why = guard(p, "Edit", "tests/test_fees.py")
        check(d == "ask" and "PROJ-1" in why and "reopen" in why, f"O-17: a frozen test → ask: {d} {why}")
        r = tf(p, "check", "PROJ-1")
        check(r.returncode == 0, f"O-18: check without changes in the frozen file → code 0: {r.stdout}")
        (p / "tests" / "test_fees.py").write_text("def test_ac1_limit():  # AC-1\n    assert 1\n", encoding="utf-8")
        r = tf(p, "check", "PROJ-1")
        check(r.returncode == 1 and "tests/test_fees.py" in r.stdout, f"O-19: a change of the frozen file (e.g. via the shell) → check code 1: {r.stdout}")
        r = tf(p, "stage", "PROJ-1", "review")
        check(r.returncode == 1 and "tests/test_fees.py" in r.stdout, f"O-20: the review stage rejected with a changed frozen file: {r.stdout}")
        r = tf(p, "reopen", "PROJ-1", "tests/test_fees.py", "--by", "human:anna", "--reason", "the test had an error in its data")
        d, why = guard(p, "Edit", "tests/test_fees.py")
        check(r.returncode == 0 and d == "" and tf(p, "check", "PROJ-1").returncode == 0,
              f"O-21: reopen removes the freeze: {r.stdout} {d}")
        r = tf(p, "reopen", "PROJ-1", "src.py", "--by", "human:anna", "--reason", "x")
        check(r.returncode == 1, f"O-22: reopen of a file that is neither approved nor frozen → refusal: {r.returncode} {r.stdout}")

        # a closed task protects nothing any more; a corrupt task.json does not crash the hook
        tf(p, "freeze", "PROJ-1", "tests/test_fees.py", "--by", "human:anna")
        tf(p, "stage", "PROJ-1", "closed", "--force")
        d1, _ = guard(p, "Edit", "tests/test_fees.py")
        d2, _ = guard(p, "Edit", spec_rel)
        check(d1 == "" and d2 == "", f"O-23: after the task is closed the files are not protected: {d1} {d2}")
        (p / CHANGES / "PROJ-9").mkdir()
        (p / CHANGES / "PROJ-9" / "task.json").write_text("{nie json", encoding="utf-8")
        d, why = guard(p, "Edit", "src.py")
        check(d == "", f"O-24: a corrupt task.json of another task does not block work: {d} {why}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} task file protection tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
