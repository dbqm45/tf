#!/usr/bin/env python3
"""The deployment card and the post-merge check (step G3): the `deploy` section of the operations card, `tf task deployed` with a smoke
test, the 'roll back?' question after a red result and the 'waiting for you' list.
python3 .claude/tests/test_deploy.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
ONBOARD = ROOT / ".tf" / "factory" / "onboard.py"
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
CHANGES = Path("docs") / "project" / "changes"
CARD = Path(".tf") / "config" / "operations.json"
GREEN = f'{sys.executable} -c "print(\'smoke ok\')"'
RED = f'{sys.executable} -c "print(\'HTTP 500 /health\'); raise SystemExit(7)"'
SLOW = f'{sys.executable} -c "import time; time.sleep(30)"'
ROLLBACK = "Wdróż poprzednią wersję: ./deploy.sh --previous"
LOGS = "kubectl logs deploy/parking --since=10m"
NODE = {"scripts": {"test": "vitest run", "smoke": "node scripts/smoke.mjs"}}


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
           "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          stdin=subprocess.DEVNULL, timeout=120)


def card(project: Path, deploy: dict | None, **rest) -> None:
    f = project / CARD
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({**rest, **({"deploy": deploy} if deploy is not None else {})}, ensure_ascii=False),
                 encoding="utf-8")


def task(project: Path, key: str = "IMP-1") -> dict:
    return json.loads((project / CHANGES / key / "task.json").read_text(encoding="utf-8"))


def new_task(project: Path, stage: str = "pr") -> None:
    project.mkdir(parents=True)
    call(project, TASK, "start", "IMP-1", "--title", "Limit dobowy")
    if stage != "intake":
        call(project, TASK, "stage", "IMP-1", stage, "--force")


def waiting(project: Path) -> list[dict]:
    r = call(project, TASK, "list", "--json")
    try:
        return next(x for x in json.loads(r.stdout) if x["key"] == "IMP-1")["waiting"]
    except (ValueError, KeyError, StopIteration, TypeError):
        return [{"error": r.stdout + r.stderr}]


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        # a task before the PR: a deployment cannot be recorded
        p = Path(t) / "early"
        new_task(p, "intake")
        card(p, {"smoke": GREEN})
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode != 0 and "pr" in r.stdout and task(p)["stage"] == "intake" and "deploy" not in task(p),
              f"DP-1: a deployment is recorded after the pr stage; refusal before it: {r.returncode} {r.stdout}")

        # without a card and without a smoke test: a message, not an error; the stage unchanged
        p = Path(t) / "nocard"
        new_task(p)
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode == 0 and "deploy.smoke" in r.stdout and "ends at the merge" in r.stdout
              and task(p)["stage"] == "pr" and not list((p / CHANGES / "IMP-1").glob("evidence/deploy-*.json")),
              f"DP-2: without a card the factory ends at the merge and says so outright (code 0, no evidence): {r.returncode} {r.stdout}")
        card(p, {"smoke": "", "rollback": ROLLBACK})
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode == 0 and "deploy.smoke" in r.stdout and task(p)["stage"] == "pr",
              f"DP-3: a card without a smoke test command — the same: {r.returncode} {r.stdout}")

        # a green smoke test -> evidence and the deploy stage
        p = Path(t) / "green"
        new_task(p)
        card(p, {"smoke": GREEN, "rollback": ROLLBACK, "rollback_minutes": 5, "logs": LOGS,
                 "approval": "wdrożenie na produkcję zatwierdza kierownik zmiany"})
        r = call(p, TASK, "deployed", "IMP-1", "--version", "2.4.0")
        ev = p / CHANGES / "IMP-1" / "evidence" / "deploy-1.json"
        data = json.loads(ev.read_text(encoding="utf-8")) if ev.is_file() else {}
        check(r.returncode == 0 and task(p)["stage"] == "deploy" and data.get("exit_code") == 0
              and data.get("command") == GREEN and data.get("version") == "2.4.0" and data.get("at")
              and data.get("kind") == "deploy",
              f"DP-4: a green smoke test records evidence (command, code, version, date) and the deploy stage: {r.stdout} {data}")
        check(task(p).get("deploy", {}).get("state") == "ok" and task(p)["deploy"].get("evidence") == "evidence/deploy-1.json"
              and not waiting(p) and set(data) == {"kind", "command", "exit_code", "version", "sha", "at", "log"}
              and "smoke ok" in (p / ".tf" / "runs" / "IMP-1" / "deploy-1.log").read_text(encoding="utf-8"),
              f"DP-5: the deployment state 'ok' in task.json, nothing waits, and the command output does not go to git: {task(p).get('deploy')}")
        check("zatwierdza kierownik zmiany" in r.stdout,
              f"DP-6: the message reminds what the human approves (from the card): {r.stdout}")
        r = call(p, TASK, "status", "IMP-1")
        check("deployment" in r.stdout and "2.4.0" in r.stdout,
              f"DP-7: tf task status shows the deployment result and the version: {r.stdout}")

        # a red smoke test -> the 'roll back?' question, the rollback step, logs; the task waits for a human
        p = Path(t) / "red"
        new_task(p)
        card(p, {"smoke": RED, "rollback": ROLLBACK, "rollback_minutes": 5, "logs": LOGS})
        r = call(p, TASK, "deployed", "IMP-1", "--version", "2.4.0")
        check(r.returncode == 1 and "Roll back" in r.stdout and ROLLBACK in r.stdout and "5 min" in r.stdout
              and LOGS in r.stdout and "HTTP 500 /health" in r.stdout and "code 7" in r.stdout,
              f"DP-8: a red test: the rollback question, the rollback step and time, the logs command, the test output: "
              f"{r.returncode} {r.stdout}")
        check(task(p)["stage"] == "pr" and task(p).get("deploy", {}).get("state") == "red"
              and (p / CHANGES / "IMP-1" / "evidence" / "deploy-1.json").is_file(),
              f"DP-9: a red result recorded with evidence; the stage does not move to deploy: {task(p).get('deploy')}")
        w = waiting(p)
        check(len(w) == 1 and w[0].get("kind") == "deploy" and "Roll back" in (w[0].get("question") or "")
              and w[0].get("recommended") and any(ROLLBACK in (o.get("skutek") or "") for o in w[0].get("options") or [])
              and "--rolled-back" in (w[0].get("how") or ""),
              f"DP-10: the 'waiting for you' list: the rollback question with options, a recommendation and a command: {w}")
        r = call(p, TASK, "list")
        check("waiting for you" in r.stdout and "Roll back" in r.stdout,
              f"DP-11: tf status shows a task waiting for a rollback decision: {r.stdout}")

        # the rollback decision belongs to a human
        r = call(p, TASK, "deployed", "IMP-1", "--rolled-back")
        check(r.returncode == 2 and "human:" in r.stdout and waiting(p),
              f"DP-12: a rollback is recorded by a human (--by human:<id>): {r.returncode} {r.stdout}")
        r = call(p, TASK, "deployed", "IMP-1", "--rolled-back", "--by", "human:anna")
        d = task(p).get("deploy", {})
        check(r.returncode == 0 and d.get("state") == "rolled-back" and d.get("decided_by") == "human:anna"
              and d.get("decided_at") and not waiting(p),
              f"DP-13: recording the rollback decision takes the task off the list: {r.returncode} {r.stdout} {d}")

        # after a fix, a green test again -> deploy, a second piece of evidence
        card(p, {"smoke": GREEN, "rollback": ROLLBACK})
        r = call(p, TASK, "deployed", "IMP-1", "--version", "2.4.1")
        check(r.returncode == 0 and task(p)["stage"] == "deploy" and task(p)["deploy"].get("state") == "ok"
              and task(p)["deploy"].get("evidence") == "evidence/deploy-2.json" and not waiting(p),
              f"DP-14: a green test again after a fix: the deploy stage and a second piece of evidence: {r.stdout} {task(p).get('deploy')}")

        # a smoke test time-out is a red result, not an exception trace
        p = Path(t) / "slow"
        new_task(p)
        card(p, {"smoke": SLOW})
        r = call(p, TASK, "deployed", "IMP-1", "--timeout", "1")
        check(r.returncode == 1 and "Traceback" not in r.stdout + r.stderr and ("time limit" in r.stdout or "limit czasu" in r.stdout)
              and "git revert" in r.stdout and task(p)["deploy"].get("state") == "red",
              f"DP-15: time limit -> a red result; without a step in the card the default step is given: {r.returncode} {r.stdout} {r.stderr}")

        # an unreadable or wrongly shaped card does not break the command
        p = Path(t) / "broken"
        new_task(p)
        (p / CARD).parent.mkdir(parents=True, exist_ok=True)
        (p / CARD).write_text("{nie json", encoding="utf-8")
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode == 0 and "Traceback" not in r.stdout + r.stderr and "deploy.smoke" in r.stdout,
              f"DP-16: an unreadable card = no smoke test, no exception trace: {r.returncode} {r.stdout} {r.stderr}")
        card(p, {"smoke": ["rm", "-rf", "x"]})
        r = call(p, TASK, "deployed", "IMP-1")
        check(r.returncode == 0 and "deploy.smoke" in r.stdout and task(p)["stage"] == "pr",
              f"DP-17: a smoke test that is not text is not run: {r.returncode} {r.stdout}")

        # security review findings: hostile values in the card and in the task do not break the commands
        p = Path(t) / "hostile"
        new_task(p)
        (p / CARD).parent.mkdir(parents=True, exist_ok=True)
        (p / CARD).write_text('{"deploy": {"smoke": %s, "rollback": "cofnij", "rollback_minutes": 1%s, '
                              '"logs": "logi \\u001b[2J tu"}}' % (json.dumps(RED), "0" * 400), encoding="utf-8")
        r = call(p, TASK, "deployed", "IMP-1")
        r2 = call(p, TASK, "list")
        check(r.returncode == 1 and "Traceback" not in r.stdout + r.stderr + r2.stdout + r2.stderr
              and "waiting for you" in r2.stdout and "cofnij" in r.stdout,
              f"DP-24: a huge number in rollback_minutes breaks neither deployed nor tf status: {r.stderr[-300:]} {r2.stderr[-300:]}")
        check("\x1b" not in r.stdout and "logi" in r.stdout,
              f"DP-25: control characters from the card do not reach the terminal: {r.stdout!r}")
        for bad in ("nan", "inf", "1e20", "0"):
            r = call(p, TASK, "deployed", "IMP-1", "--timeout", bad)
            check(r.returncode == 2 and "Traceback" not in r.stdout + r.stderr,
                  f"DP-26: time limit {bad} is rejected with code 2: {r.returncode} {r.stdout} {r.stderr[-200:]}")
        p = Path(t) / "noRed"
        new_task(p)
        r = call(p, TASK, "deployed", "IMP-1", "--rolled-back", "--by", "human:anna")
        check(r.returncode != 0 and "deploy" not in task(p),
              f"DP-27: a rollback can be recorded only after a red smoke test: {r.returncode} {r.stdout}")
        f = p / CHANGES / "IMP-1" / "task.json"
        f.write_text(json.dumps({**task(p), "deploy": {"state": ["ok"]}}), encoding="utf-8")
        r = call(p, TASK, "status", "IMP-1")
        check(r.returncode == 0 and "Traceback" not in r.stderr,
              f"DP-28: an unusual deployment record in task.json does not break tf task status: {r.stderr[-200:]}")

        # tf onboard adds the deploy section and detects the smoke test; it does not change existing fields
        p = Path(t) / "onb"
        p.mkdir()
        (p / "package.json").write_text(json.dumps(NODE), encoding="utf-8")
        (p / "package-lock.json").write_text("{}", encoding="utf-8")
        card(p, None, tracker={"type": "jira", "prefix": "EBO"})
        r = call(p, ONBOARD, "--yes")
        c = json.loads((p / CARD).read_text(encoding="utf-8"))
        check(r.returncode == 0 and c.get("tracker") == {"type": "jira", "prefix": "EBO"} and "flags" in c
              and c.get("deploy", {}).get("smoke") == "npm run smoke"
              and all(k in c.get("deploy", {}) for k in ("rollback", "rollback_minutes", "smoke", "approval", "logs")),
              f"DP-18: onboard adds the deploy section with the detected smoke test and leaves the tracker alone: {c}")
        check("deploy" in r.stdout and "rollback" in r.stdout and "npm run smoke" in r.stdout,
              f"DP-19: onboard says what it detected and what to fill in in the deployment part: {r.stdout}")
        c.setdefault("deploy", {})["rollback"] = ROLLBACK
        (p / CARD).write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        call(p, ONBOARD, "--yes")
        check(json.loads((p / CARD).read_text(encoding="utf-8")) == c,
              "DP-20: a repeated onboard does not overwrite a filled-in card")
        p = Path(t) / "onb2"
        (p / "scripts").mkdir(parents=True)
        (p / "scripts" / "smoke.sh").write_text("#!/bin/sh\ncurl -fsS localhost/health\n", encoding="utf-8")
        (p / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
        call(p, ONBOARD, "--yes")
        c = json.loads((p / CARD).read_text(encoding="utf-8")) if (p / CARD).is_file() else {}
        check(c.get("deploy", {}).get("smoke") == "./scripts/smoke.sh",
              f"DP-21: scripts/smoke.sh detected as a smoke test: {c.get('deploy')}")

        # finishing the run gives the next step after the merge
        p = Path(t) / "finish"
        p.mkdir()
        call(p, SCRIPTS / "run_report.py", "start", "Limit dobowy", "--key", "IMP-1", "--story", "Popraw literówkę w README.")
        d = str(p / ".tf" / "runs" / "IMP-1")
        r = call(p, SCRIPTS / "run_report.py", "finish", d)
        check("deploy.smoke" in r.stdout and "tf task deployed" not in r.stdout,
              f"DP-22: finish without a smoke test in the card says the factory ends at the merge: {r.stdout}")
        card(p, {"smoke": GREEN})
        r = call(p, SCRIPTS / "run_report.py", "finish", d)
        check("tf task deployed IMP-1" in r.stdout,
              f"DP-23: finish with a smoke test in the card gives the post-deployment command: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} deployment card tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
