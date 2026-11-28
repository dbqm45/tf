#!/usr/bin/env python3
"""The loop's composite commands (tf stress: the bookkeeping cost a model turn per call): `run_report.py start --begin`,
`run_state.py plan` and `run_state.py close` carry one task from the start to the report in four script calls with
`finish-slice`, with the same records as the single steps (stages, approach, flag, parked items, trace, PR description,
a STOP without a remote). python3 .claude/tests/test_loop_composite.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL / "run_state.py").is_file())
STATE, REPORT = ROOT / REL / "run_state.py", ROOT / REL / "run_report.py"
OK = f"{sys.executable} -c \"print('1 passed')\""


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = base / "proj"
        p.mkdir()
        fake = base / "bin"
        fake.mkdir()
        (fake / "semgrep").write_text(f"#!{sys.executable}\nimport json, sys\na = sys.argv[1:]\n"
                                      "json.dump({'version': '2.1.0', 'runs': [{'tool': {'driver': {'name': 'f', 'rules': []}}, "
                                      "'results': []}]}, open(a[a.index('--output') + 1], 'w'))\n", encoding="utf-8")
        (fake / "semgrep").chmod(0o755)
        env = {**{k: v for k, v in os.environ.items() if k not in ("CI", "CLAUDE_CODE_ENTRYPOINT")},
               "CLAUDE_PROJECT_DIR": str(p), "TF_DASHBOARD_OPEN": "0", "TF_DASHBOARD_LIVE": "0",
               "TF_SCAN_PATH": str(fake), "CLAUDE_CONFIG_DIR": str(base / "cfg"), "GIT_CONFIG_GLOBAL": os.devnull,
               "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "T",
               "GIT_COMMITTER_EMAIL": "t@example.invalid"}

        def run(script, *args):
            return subprocess.run([sys.executable, str(script), *args], cwd=p, capture_output=True, text=True, env=env,
                                  timeout=300)

        def git(*args):
            return subprocess.run(["git", "-C", str(p), *args], capture_output=True, text=True, env=env, timeout=60)

        git("init", "-q", "-b", "main")
        (p / "a.py").write_text("def total(x):\n    return x\n")
        (p / ".gitignore").write_text(".tf/\n")
        git("add", "-A")
        git("commit", "-qm", "init")

        r = run(REPORT, "start", "Rabat", "--story", "Jako klient chcę rabat. Kryteria akceptacji: AC-1 total(100) == 90.",
                "--begin", "--auto")
        d = next((p / ".tf" / "runs").glob("T-*-rabat"), None)
        check(r.returncode == 0 and d is not None and git("branch", "--show-current").stdout.strip() == "story/rabat",
              f"C-1: start --begin → the task, the branch, the intake stage: {r.returncode} {r.stdout} {r.stderr}")
        if d is None:
            for f in fails:
                print(f"✗ {f}")
            return 1
        rel = d.relative_to(p).as_posix()
        docs = p / "docs" / "project" / "changes" / d.name
        (docs / "plan.md").write_text("# Plan\n\n- [ ] S1 — rabat · criteria: AC-1 (test_a.py: test_ac1) · files: a.py, "
                                      "test_a.py · verify: `x` · tier: std\n")
        r = run(STATE, "plan", rel, "--weight", "quick", "--rationale", "a.py:1, one function", "--slices", "1",
                "--flag", "none", "--flag-reason", "one function", "--park", "rabat dla firm", "--park", "zaokrąglenia",
                "--auto")
        meta = json.loads((d / "run.json").read_text())
        parked = (d / "parked.md").read_text()
        check(r.returncode == 0 and meta.get("stage") == "plan" and "rabat dla firm" in parked and "zaokrąglenia" in parked,
              f"C-2: plan → approach, flag, two parked items and the plan stage in one call: {r.returncode} "
              f"{meta.get('stage')} {r.stdout[-400:]} {r.stderr[-300:]}")
        r = run(STATE, "plan", rel, "--weight", "nope", "--rationale", "x")
        check(r.returncode != 0 and "stopped at «approach»" in r.stdout,
              f"C-3: a refused step stops the composite and names it: {r.returncode} {r.stdout[-300:]}")
        (p / "test_a.py").write_text("from a import total\n\n\ndef test_ac1():  # AC-1\n    assert total(100) == 90\n")
        (p / "a.py").write_text("def total(x):\n    return x * 9 // 10\n")
        r = run(STATE, "finish-slice", rel, "S1", "--files", "a.py,test_a.py", "--command", OK,
                "--message", "feat(rabat): 10% off")
        check(r.returncode == 0, f"C-4: finish-slice after plan: {r.returncode} {r.stdout[-400:]} {r.stderr[-300:]}")
        r = run(STATE, "close", rel, "--base", "main")
        meta = json.loads((d / "run.json").read_text())
        check(r.returncode == 3 and meta.get("stage") == "needs" and meta.get("stop_code") == "environment"
              and (d / "pr-body.md").is_file() and (docs / "report.md").is_file(),
              f"C-5: close → trace, pr stage, PR description, a STOP without a remote and the report: {r.returncode} "
              f"{meta.get('stage')} {meta.get('stop_code')} {r.stdout[-500:]} {r.stderr[-300:]}")
        check((meta.get("pr_steps") or {}).get("drift") in ("pass", "fail"),
              f"C-6: close records the plan_drift step: {meta.get('pr_steps')}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} composite loop command tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
