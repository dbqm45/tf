#!/usr/bin/env python3
"""Tests of the quality gate `.claude/hooks/quality_gate.py` (Stop/SubagentStop: build and tests green before finishing)
and of the test lock `.claude/hooks/test_lock.py` in a temporary git repository. python3 tests/test_quality_gate.py"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
GATE = ROOT / ".claude" / "hooks" / "quality_gate.py"
LOCK = ROOT / ".claude" / "hooks" / "test_lock.py"

CHECK = """import pathlib, sys, time
p = pathlib.Path(__file__).parent
(p / "runs.log").open("a").write("run\\n")
mode = (p / "mode.txt").read_text().strip() if (p / "mode.txt").exists() else "pass"
if mode == "slow":
    time.sleep(5)
if mode == "long":   # a long log: the first error at the beginning, the summary at the end
    print("FIRST ERROR test_start: oczekiwano 1, jest 2")
    for i in range(400):
        print(f"line {i:04d} " + ("MIDDLE " if i == 200 else "") + "x" * 30)
    print("SUMMARY 1 failed, 399 passed")
    sys.exit(1)
if mode == "fail":
    print("FAILED test_suma: expected 4, got 5")
    sys.exit(1)
print("2 passed")
"""


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def setup(tmp: Path, config: dict | None) -> Path:
    repo = tmp / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "docs").mkdir()
    (repo / "src" / "app.py").write_text("x = 1\n")
    (repo / "docs" / "notes.md").write_text("# n\n")
    (repo / "check.py").write_text(CHECK)
    git(repo, "init", "-q")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    (repo / ".claude").mkdir()
    if config is not None:
        (repo / ".claude" / "quality-gate.json").write_text(json.dumps(config))
    return repo


def hook(repo, event="Stop", **env):
    data = {"hook_event_name": event, "stop_hook_active": False, "session_id": "s1"}
    return subprocess.run([sys.executable, str(GATE)], input=json.dumps(data), capture_output=True, text=True,
                          timeout=60, env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo), **env})


def runs(repo) -> int:
    f = repo / "runs.log"
    return len(f.read_text().splitlines()) if f.exists() else 0


def blocked(r) -> dict | None:
    try:
        out = json.loads(r.stdout) if r.stdout.strip() else {}
    except ValueError:
        return None
    return out if out.get("decision") == "block" else None


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    for f in (GATE, LOCK):
        if not f.is_file():
            print(f"✗ missing {f}")
            return 1
    cfg = {"command": f"{sys.executable} check.py", "watch": ["src/"], "timeout": 3, "max_blocks": 2}
    with tempfile.TemporaryDirectory() as t:
        repo = setup(Path(t) / "a", None)
        (repo / "src" / "app.py").write_text("x = 2\n")
        r = hook(repo)
        check(r.returncode == 0 and not r.stdout.strip() and runs(repo) == 0, f"Q-1: without a configuration it does nothing: {r.stdout}{r.stderr}")

        repo = setup(Path(t) / "b", cfg)
        r = hook(repo)
        check(r.returncode == 0 and runs(repo) == 0, f"Q-2: without changes the tests are not run: {runs(repo)}")

        (repo / "src" / "app.py").write_text("x = 2\n")
        (repo / "mode.txt").write_text("fail")
        r = hook(repo)
        b = blocked(r)
        check(b is not None and "test_suma" in b.get("reason", "") and runs(repo) == 1,
              f"Q-3: red tests after a change in watch -> a block with the end of the output: {r.stdout}{r.stderr}")

        (repo / "mode.txt").write_text("pass")
        (repo / "src" / "app.py").write_text("x = 3\n")
        r = hook(repo)
        n = runs(repo)
        r2 = hook(repo)
        check(blocked(r) is None and blocked(r2) is None and runs(repo) == n,
              f"Q-4: green -> no block, the same diff a second time without a run: {r.stdout} {runs(repo)} vs {n}")

        (repo / "docs" / "notes.md").write_text("# change\n")
        n = runs(repo)
        r = hook(repo)
        check(blocked(r) is None and runs(repo) == n, f"Q-5: a change outside watch does not run the tests: {runs(repo)} vs {n}")

        # the task directory (docs/project/changes/, written by `tf task`) is not a code change — also without `watch`
        wide = setup(Path(t) / "b2", {k: v for k, v in cfg.items() if k != "watch"})
        (wide / "mode.txt").write_text("fail")
        git(wide, "add", "-A")
        git(wide, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "configuration")
        (wide / "docs" / "project" / "changes" / "T-1").mkdir(parents=True)
        (wide / "docs" / "project" / "changes" / "T-1" / "task.json").write_text("{}")
        (wide / "docs" / "project" / "changes" / "INDEX.md").write_text("# Tasks\n")
        r = hook(wide)
        check(blocked(r) is None and runs(wide) == 0, f"Q-5a: a change only in the task directory does not run the gate: {r.stdout} {runs(wide)}")
        (wide / "src" / "app.py").write_text("x = 9\n")
        r = hook(wide)
        check(blocked(r) is not None and runs(wide) == 1, f"Q-5b: a code change next to task files still runs the gate: {r.stdout} {runs(wide)}")

        (repo / "mode.txt").write_text("fail")
        (repo / "src" / "app.py").write_text("x = 4\n")
        (repo / ".claude" / "quality-gate.expected-red").write_text("batch K2: a red test from the plan")
        r = hook(repo)
        check(blocked(r) is None, f"Q-6: a declared red batch (expected-red) let through: {r.stdout}")
        (repo / ".claude" / "quality-gate.expected-red").unlink()

        r1, r2, r3 = hook(repo), hook(repo), hook(repo)
        check(blocked(r1) and blocked(r2) and blocked(r3) is None and "human" in (r3.stdout + r3.stderr).lower(),
              f"Q-7: after max_blocks blocks of the same diff it lets through with a message: {r3.stdout}{r3.stderr}")

        (repo / "src" / "app.py").write_text("x = 5\n")
        n = runs(repo)
        r = hook(repo, QG_GATE_DISABLE="1")
        check(blocked(r) is None and runs(repo) == n, f"Q-8: QG_GATE_DISABLE=1 turns the gate off: {r.stdout}")

        r = hook(repo, event="SubagentStop")
        check(blocked(r) is not None, f"Q-9: SubagentStop also blocks red: {r.stdout}{r.stderr}")

        (repo / "mode.txt").write_text("slow")
        (repo / "src" / "app.py").write_text("x = 6\n")
        r = hook(repo)
        b = blocked(r)
        check(b is not None and "limit" in b.get("reason", "").lower(), f"Q-10: timeout exceeded -> a block with a description: {r.stdout}{r.stderr}")

        # test lock
        holder = subprocess.Popen([sys.executable, str(LOCK), "--", sys.executable, "-c", "import time; time.sleep(4)"],
                                  cwd=repo, env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)})
        time.sleep(1)
        r = subprocess.run([sys.executable, str(LOCK), "--", sys.executable, "-c", "print('executed')"], cwd=repo,
                           capture_output=True, text=True, timeout=30,
                           env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo), "QG_LOCK_WAIT": "1"})
        check(r.returncode == 75 and "executed" not in r.stdout and "LOCK" in (r.stdout + r.stderr).upper(),
              f"L-1: the lock busy for longer than QG_LOCK_WAIT -> code 75 without running: {r.returncode} {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(LOCK), "--", sys.executable, "-c", "print('executed')"], cwd=repo,
                           capture_output=True, text=True, timeout=30,
                           env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo), "QG_LOCK_WAIT": "1",
                                "TF_TEST_LOCK_HELD": "1"})
        check(r.returncode == 0 and "executed" in r.stdout, f"L-2: re-entrant (TF_TEST_LOCK_HELD) runs immediately: {r.stdout}{r.stderr}")
        holder.wait(timeout=20)
        r = subprocess.run([sys.executable, str(LOCK), "--", sys.executable, "-c", "import sys; sys.exit(3)"], cwd=repo,
                           capture_output=True, text=True, timeout=30, env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)})
        check(r.returncode == 3, f"L-3: a free lock -> the command's exit code: {r.returncode}")

    # bounded output: the agent gets the beginning and the end of a long log, all of it is in a file
    with tempfile.TemporaryDirectory() as t:
        repo = setup(Path(t) / "o1", cfg)
        (repo / "src" / "app.py").write_text("x = 3\n")
        (repo / "mode.txt").write_text("long")
        b = blocked(hook(repo)) or {}
        reason = b.get("reason", "")
        full = repo / ".tf" / "logs" / "quality-gate-output.txt"
        saved = full.read_text(encoding="utf-8") if full.is_file() else ""
        check("FIRST ERROR test_start" in reason and "SUMMARY 1 failed" in reason and "MIDDLE" not in reason,
              f"B-1: a long log -> the message has the beginning and the end, without the middle: {reason[:200]} … {reason[-200:]}")
        check(".tf/logs/quality-gate-output.txt" in reason and "skipped" in reason and len(reason) < 5000,
              f"B-2: the message says how much was skipped and where the whole is; it stays short ({len(reason)} characters)")
        check("FIRST ERROR" in saved and "MIDDLE" in saved and "SUMMARY" in saved,
              f"B-3: the full output saved in .tf/logs/quality-gate-output.txt ({len(saved)} characters)")
        (repo / "src" / "app.py").write_text("x = 4\n")
        (repo / "mode.txt").write_text("fail")
        b = blocked(hook(repo)) or {}
        check("test_suma" in b.get("reason", "") and "skipped" not in b.get("reason", ""),
              f"B-4: short output goes into the message in full, without a note about skipping: {b.get('reason', '')[-200:]}")
        now = full.read_text(encoding="utf-8") if full.is_file() else ""
        check("test_suma" in now and "MIDDLE" not in now, "B-5: the file with the full output contains the last run, not the previous one")

    # the gate state in plain language (tf doctor, session start)
    def status(repo, *flags, **env):
        base = {k: v for k, v in os.environ.items() if k != "QG_GATE_DISABLE"}
        return subprocess.run([sys.executable, str(GATE), "--status", *flags], capture_output=True, text=True,
                              timeout=30, env={**base, "CLAUDE_PROJECT_DIR": str(repo), **env})

    with tempfile.TemporaryDirectory() as t:
        repo = setup(Path(t) / "s1", None)
        r = status(repo)
        check(r.returncode == 0 and "disabled" in r.stdout and "quality-gate.json" in r.stdout
              and "will not block red tests" in r.stdout, f"S-1: no configuration -> disabled, with the reason and the effect: {r.stdout}{r.stderr}")
        repo = setup(Path(t) / "s2", cfg)
        r = status(repo)
        check(r.returncode == 0 and "gate on" in r.stdout and "check.py" in r.stdout and "disabled" not in r.stdout,
              f"S-2: a configuration with a command -> enabled, with the command: {r.stdout}{r.stderr}")
        r = status(repo, "--quiet-ok")
        check(r.returncode == 0 and r.stdout.strip() == "", f"S-3: --quiet-ok is silent when the gate works: {r.stdout!r}")
        r = status(repo, "--quiet-ok", QG_GATE_DISABLE="1")
        check("disabled" in r.stdout and "QG_GATE_DISABLE" in r.stdout, f"S-4: a switch in the environment -> disabled: {r.stdout}")
        (repo / ".claude" / "settings.local.json").write_text(json.dumps({"env": {"QG_GATE_DISABLE": "1"}}))
        r = status(repo)
        check("disabled" in r.stdout and "settings.local.json" in r.stdout, f"S-5: a switch in the settings -> the file is named: {r.stdout}")
        (repo / ".claude" / "settings.local.json").unlink()
        (repo / ".claude" / "quality-gate.expected-red").write_text("TDD batch: CDR import")
        r = status(repo, "--quiet-ok")
        check("lets red tests through" in r.stdout and "CDR import" in r.stdout, f"S-6: a red-batch marker -> a warning with the reason: {r.stdout}")
        repo = setup(Path(t) / "s7", {"watch": ["src/"]})
        r = status(repo)
        check("disabled" in r.stdout and "command" in r.stdout, f"S-7: a configuration without a command -> disabled: {r.stdout}")
        (repo / ".claude" / "quality-gate.json").write_text("{not json")
        r = status(repo)
        check(r.returncode == 0 and "disabled" in r.stdout and "JSON" in r.stdout, f"S-8: a corrupted file -> disabled, no exception: {r.stdout}{r.stderr}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} quality gate tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
