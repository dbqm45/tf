#!/usr/bin/env python3
"""Tests of the per-task feature flag (`tf task flag`, .tf/factory/flag_check.py, the operations card from `tf onboard`).
python3 .claude/tests/test_flag_check.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPT = ROOT / ".tf" / "factory" / "flag_check.py"
TASK = ROOT / ".tf" / "factory" / "task_state.py"
ONBOARD = ROOT / ".tf" / "factory" / "onboard.py"
CHANGES = Path("docs") / "project" / "changes"
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci, then opłata wynosi 45 zł.\n"
        "\n## Unchanged\n\n- Stawka godzinowa.\n\n## Out of scope\n\n- Abonamenty.\n")
CARD = {"flags": {"file": "config/flags.json", "envs": ["test", "qa", "prod"], "test_env": "test"}}


def run(project: Path, script: Path, *args: str):
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                          cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


def flags(repo: Path, **states) -> None:
    """config/flags.json in the environment → flag → state layout."""
    write(repo, "config/flags.json", json.dumps({env: {"proj_1_limit": on, "inna": False} for env, on in states.items()}, indent=1))


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not SCRIPT.is_file():
        print(f"✗ missing {SCRIPT}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "repo"
        p.mkdir()
        git(p, "init", "-q", "-b", "main")
        flags(p, test=False, qa=False, prod=False)
        write(p, "src/fees.py", "LIMIT = 40\n")
        git(p, "add", "-A")
        git(p, "commit", "-qm", "init")
        git(p, "checkout", "-qb", "story/limit")
        run(p, TASK, "start", "PROJ-1", "--title", "Limit dobowy")
        task_file = p / CHANGES / "PROJ-1" / "task.json"

        def task() -> dict:
            return json.loads(task_file.read_text(encoding="utf-8"))

        # the task's flag: a key with a removal date or an explicit “bez flagi, bo…” (no flag, because…)
        r = run(p, TASK, "flag", "PROJ-1", "none")
        check(r.returncode == 2 and "--reason" in r.stdout, f"F-1: “bez flagi” requires a reason: {r.returncode} {r.stdout}")
        r = run(p, TASK, "flag", "PROJ-1", "set", "proj_1_limit", "--remove-by", "2027-01-31")
        f = task().get("flag", {})
        check(r.returncode == 0 and f.get("key") == "proj_1_limit" and f.get("remove_by") == "2027-01-31",
              f"F-2: flag set records the key and the removal date: {r.stdout} {f}")
        r = run(p, TASK, "flag", "PROJ-1", "set", "proj_1_limit", "--remove-by", "someday")
        check(r.returncode == 2, f"F-3: the removal date in the YYYY-MM-DD format: {r.returncode} {r.stdout}")
        r = run(p, TASK, "status", "PROJ-1")
        check("proj_1_limit" in r.stdout and "2027-01-31" in r.stdout, f"F-4: status shows the flag: {r.stdout}")

        # the flag configuration diff check: without an operations card the script says it must be checked by hand
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0 and "by hand" in r.stdout and "operations.json" in r.stdout,
              f"F-5: no card → the “check by hand” notice, code 0: {r.returncode} {r.stdout}")
        write(p, ".tf/config/operations.json", json.dumps(CARD))
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0 and "proj_1_limit" in r.stdout, f"F-6: the flag off everywhere → code 0: {r.stdout}{r.stderr}")
        flags(p, test=True, qa=False, prod=False)
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0, f"F-7: enabling on a test environment → code 0: {r.stdout}")
        flags(p, test=True, qa=False, prod=True)
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 1 and "FLAG-001" in r.stdout and "prod" in r.stdout and "tf task flag PROJ-1 allow prod" in r.stdout,
              f"F-8: enabling on prod without a human's decision → FLAG-001 with a command: {r.returncode} {r.stdout}")
        git(p, "add", "-A")
        git(p, "commit", "-qm", "feat: limit behind a flag")
        r = run(p, SCRIPT, "PROJ-1", "--json")
        data = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and data.get("checked") is True and [e.get("env") for e in data.get("errors", [])] == ["prod"],
              f"F-9: the same after a commit (the branch diff against the base), --json: {r.stdout[:300]}")
        r = run(p, TASK, "flag", "PROJ-1", "allow", "prod", "--by", "process:tf")
        check(r.returncode == 2, f"F-10: only a human records a decision about another environment: {r.returncode} {r.stdout}")
        r = run(p, TASK, "flag", "PROJ-1", "allow", "prod", "--by", "human:anna")
        check(r.returncode == 0 and task()["flag"].get("allowed", {}).get("prod", {}).get("by") == "human:anna"
              and run(p, SCRIPT, "PROJ-1").returncode == 0,
              f"F-11: after the human's decision the check passes: {r.stdout}")

        # the flag → environment → state layout and the value {"enabled": …}
        write(p, "config/flags.json", json.dumps({"proj_1_limit": {"test": {"enabled": True}, "qa": {"enabled": True},
                                                                   "prod": {"enabled": True}}}))
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 1 and "qa" in r.stdout and "FLAG-001" in r.stdout,
              f"F-12: the flag → environment layout: qa without a decision → FLAG-001: {r.stdout}")
        write(p, "config/flags.json", "to nie json")
        r = run(p, SCRIPT, "PROJ-1")
        check(r.returncode == 0 and "by hand" in r.stdout, f"F-13: a file the script does not understand → “check by hand”, code 0: {r.stdout}")
        flags(p, test=True, qa=False, prod=False)

        # stage gate: a task with a spec needs a flag or a reason for its absence; a change on prod without a decision blocks
        run(p, TASK, "start", "PROJ-2", "--title", "Bez flagi")
        write(p, f"{CHANGES.as_posix()}/PROJ-2/spec.md", SPEC)
        write(p, "tests/test_x.py", "def test_ac1():  # AC-1\n    assert True\n")
        r = run(p, TASK, "stage", "PROJ-2", "pr")
        check(r.returncode == 1 and "tf task flag PROJ-2" in r.stdout, f"F-14: the pr stage rejected without a flag and without a reason: {r.returncode} {r.stdout}")
        r = run(p, TASK, "flag", "PROJ-2", "none", "--reason", "bug fix, nothing to hide")
        r2 = run(p, TASK, "stage", "PROJ-2", "pr")
        check(r.returncode == 0 and r2.returncode == 0 and "bug fix" in run(p, SCRIPT, "PROJ-2").stdout,
              f"F-15: “bez flagi, bo…” is enough: {r.stdout} {r2.stdout}")
        run(p, TASK, "start", "PROJ-3", "--title", "Bez specyfikacji")
        r = run(p, TASK, "stage", "PROJ-3", "pr")
        check(r.returncode == 0, f"F-16: a task without spec.md does not require a flag: {r.stdout}")
        run(p, TASK, "start", "PROJ-4", "--title", "Flag on prod")
        write(p, f"{CHANGES.as_posix()}/PROJ-4/spec.md", SPEC)
        run(p, TASK, "flag", "PROJ-4", "set", "proj_1_limit")
        flags(p, test=True, qa=False, prod=True)
        r = run(p, TASK, "stage", "PROJ-4", "pr")
        check(r.returncode == 1 and "FLAG-001" in r.stdout, f"F-17: the pr stage rejected when the flag is enabled on prod without a decision: {r.stdout}")

        # a switch in the configuration: a human adds flags themselves (in code, in an external service) — the factory does not require them
        run(p, TASK, "start", "PROJ-5", "--title", "Flags by hand")
        write(p, f"{CHANGES.as_posix()}/PROJ-5/spec.md", SPEC)
        r = run(p, SCRIPT, "PROJ-5", "--json")
        data = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and data.get("auto") is True, f"F-21: automatic flags are on by default: {r.stdout[:200]}")
        write(p, ".tf/config/config.yaml", "feature_flags:\n  auto: false\n")
        r = run(p, SCRIPT, "PROJ-5")
        check(r.returncode == 0 and "feature_flags.auto" in r.stdout and "yourself" in r.stdout,
              f"F-22: feature_flags.auto: false → a task without a flag passes, with an explanation: {r.returncode} {r.stdout}")
        r = run(p, TASK, "stage", "PROJ-5", "pr")
        check(r.returncode == 0, f"F-23: with automatic flags off the pr stage does not require a flag: {r.stdout}")
        r = run(p, SCRIPT, "PROJ-4")
        check(r.returncode == 1 and "FLAG-001" in r.stdout,
              f"F-24: a flag recorded in the task is checked even with the automation off: {r.stdout}")
        (p / ".tf" / "config" / "config.yaml").unlink()

    with tempfile.TemporaryDirectory() as t:      # the operations card from tf onboard
        p = Path(t)
        git(p, "init", "-q", "-b", "main")
        write(p, "package.json", json.dumps({"scripts": {"test": "node -e 0"}}))
        write(p, "config/flags.json", json.dumps({"dev": {"x": False}, "prod": {"x": False}}))
        r = run(p, ONBOARD, "--yes")
        card = p / ".tf" / "config" / "operations.json"
        data = json.loads(card.read_text(encoding="utf-8")) if card.is_file() else {}
        check(data.get("flags", {}).get("file") == "config/flags.json" and data["flags"].get("envs") == ["dev", "prod"]
              and data["flags"].get("test_env") == "dev" and "operations.json" in r.stdout,
              f"F-18: onboard detects the flag file, the environments and the test environment: {data} {r.stdout[-300:]}")
        card.write_text(json.dumps(CARD), encoding="utf-8")
        run(p, ONBOARD, "--yes")
        after = json.loads(card.read_text(encoding="utf-8"))
        check({k: v for k, v in after.items() if k != "deploy"} == CARD,
              f"F-19: onboard does not change the card's existing fields (since step G3 it only adds the missing deploy section): {after}")
        run(p, ONBOARD, "--yes")
        check(json.loads(card.read_text(encoding="utf-8")) == after, "F-19b: a repeated onboard changes nothing in the card")
        card.write_text(json.dumps({"tracker": {"type": "jira"}}), encoding="utf-8")
        r = run(p, ONBOARD, "--yes")
        data = json.loads(card.read_text(encoding="utf-8"))
        check(data.get("tracker") == {"type": "jira"} and data.get("flags", {}).get("file") == "config/flags.json"
              and "operations.json" in r.stdout,
              f"F-19a: a card without a flags section (created when the tracker was saved) gets flags, the tracker stays: {data}")
    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        write(p, "package.json", json.dumps({"scripts": {"test": "node -e 0"}}))
        r = run(p, ONBOARD, "--yes")
        card = p / ".tf" / "config" / "operations.json"
        data = json.loads(card.read_text(encoding="utf-8")) if card.is_file() else {}
        check(data.get("flags", {}).get("file") is None and "flag" in r.stdout.lower(),
              f"F-20: without a flag file the card is created empty, and the report says what to fill in: {data} {r.stdout[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} feature flag tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
