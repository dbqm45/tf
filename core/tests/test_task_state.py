#!/usr/bin/env python3
"""Task state tests (.tf/factory/task_state.py): the `docs/project/changes/<KEY>/` directory with `task.json`, stages
and the task index: one writer, no model, no network. python3 tests/test_task_state.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPT = ROOT / ".tf" / "factory" / "task_state.py"
CTF = ROOT / ".tf" / "factory" / "tf.py"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'8 passed\')"'
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci, then opłata wynosi "
        "{limit} zł.\n\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")
RED = f'{sys.executable} -c "print(\'FAILED test_x\'); raise SystemExit(3)"'


def run(project: Path, *args: str):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def task(project: Path, key: str) -> dict:
    f = project / CHANGES / key / "task.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def index_rows(project: Path) -> list[str]:
    """Task list rows (`tf status`): one per task. The INDEX.md listing no longer exists (test_task_index.py)."""
    out = run(project, "list").stdout
    return [ln for ln in out.splitlines() if ln and not ln.startswith(" ")]


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not SCRIPT.is_file():
        print(f"✗ missing {SCRIPT}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        p.mkdir()
        r = run(p, "start", "PROJ-123", "--title", "Limit dobowy 45 zł", "--weight", "light", "--mode", "auto")
        d = task(p, "PROJ-123")
        check(r.returncode == 0 and d.get("key") == "PROJ-123" and d.get("title") == "Limit dobowy 45 zł"
              and d.get("stage") == "intake" and d.get("weight") == "light" and d.get("mode") == "auto"
              and d.get("schema") == 1 and d.get("created") and d.get("created") == d.get("updated"),
              f"TS-1: start creates docs/project/changes/<KEY>/task.json with the intake stage: {r.stdout}{r.stderr}{d}")
        rows = index_rows(p)
        check(len(rows) == 1 and "PROJ-123" in rows[0] and "Limit dobowy 45 zł" in rows[0] and "intake" in rows[0]
              and not (p / CHANGES / "INDEX.md").exists(),
              f"TS-2: the list has a task row with its stage; the script does not create INDEX.md: {rows}")

        before = (p / CHANGES / "PROJ-123" / "task.json").read_text(encoding="utf-8")
        r = run(p, "start", "PROJ-123", "--title", "Inny tytuł")
        check(r.returncode == 1 and (p / CHANGES / "PROJ-123" / "task.json").read_text(encoding="utf-8") == before
              and "already exists" in r.stdout, f"TS-3: a repeated start does not overwrite the task: {r.returncode} {r.stdout}")

        for bad in ("abc", "../x", "proj-1", "PROJ 1", "PROJ-"):
            r = run(p, "start", bad, "--title", "x")
            check(r.returncode == 2 and not any(p.glob(f"**/{bad.strip('./')}/task.json")),
                  f"TS-4: a key outside the pattern is rejected ({bad!r}): {r.returncode} {r.stdout}")
        check(not (p.parent / "x").exists(), "TS-5: a key with a path creates nothing outside the task directory")

        r = run(p, "stage", "PROJ-123", "wymyslony")
        check(r.returncode == 2 and task(p, "PROJ-123")["stage"] == "intake" and "spec" in r.stdout,
              f"TS-6: unknown stage -> error with the list of stages, state unchanged: {r.stdout}")
        r = run(p, "stage", "PROJ-123", "plan")
        d = task(p, "PROJ-123")
        check(r.returncode == 0 and d["stage"] == "plan" and d["updated"] >= d["created"]
              and "plan" in index_rows(p)[0], f"TS-7: a forward stage is saved in task.json and visible on the list: {r.stdout}{d}")
        r = run(p, "stage", "PROJ-123", "spec")
        check(r.returncode == 1 and task(p, "PROJ-123")["stage"] == "plan" and "--force" in r.stdout,
              f"TS-8: a backward stage without --force is rejected: {r.returncode} {r.stdout}")
        r = run(p, "stage", "PROJ-123", "spec", "--force")
        check(r.returncode == 0 and task(p, "PROJ-123")["stage"] == "spec", f"TS-9: --force moves the stage back: {r.stdout}")

        run(p, "start", "ABC-7", "--title", "Raport | z kreską")
        run(p, "stage", "ABC-7", "spec")
        run(p, "stage", "PROJ-123", "plan")
        rows = index_rows(p)
        check(len(rows) == 2 and rows[0].startswith("ABC-7 ") and rows[1].startswith("PROJ-123 ")
              and "Raport | z kreską" in rows[0],
              f"TS-10: one row per task, sorted; a pipe in the title stays in the title: {rows}")

        r = run(p, "status", "PROJ-123", "--json")
        try:
            s = json.loads(r.stdout)
        except ValueError:
            s = {}
        check(r.returncode == 0 and s.get("stage") == "plan" and s.get("key") == "PROJ-123", f"TS-11: status --json: {r.stdout}")
        r = run(p, "status", "PROJ-123")
        check(r.returncode == 0 and "PROJ-123" in r.stdout and "plan" in r.stdout and "{" not in r.stdout,
              f"TS-12: human-readable status in plain text: {r.stdout}")
        r = run(p, "status", "NIE-MA")
        check(r.returncode == 1 and "NIE-MA" in r.stdout and "start" in r.stdout, f"TS-13: unknown task -> hint: {r.stdout}")
        r = run(p, "stage", "NIE-MA", "plan")
        check(r.returncode == 1 and not (p / CHANGES / "NIE-MA").exists(), "TS-14: a stage for a nonexistent task creates nothing")

        # change directory from pdi mode: the script adds task.json and leaves the pdi files alone
        pdi = p / CHANGES / "CHG-12"
        pdi.mkdir(parents=True)
        plan = "---\nartifact: plan\nchange: CHG-12\nstatus: draft\ntasks: [TSK-57]\n---\n# Plan\n"
        (pdi / "plan.md").write_text(plan, encoding="utf-8")
        r = run(p, "start", "CHG-12", "--title", "Import CDR")
        check(r.returncode == 0 and task(p, "CHG-12").get("key") == "CHG-12"
              and (pdi / "plan.md").read_text(encoding="utf-8") == plan,
              f"TS-15: an existing pdi directory gets task.json, plan.md unchanged: {r.stdout}{r.stderr}")
        check(sum(ln.startswith("CHG-12 ") for ln in index_rows(p)) == 1, "TS-16: a pdi task is on the list once")

        r = run(p, "start", "T-20261113-bez-tytulu")
        check(r.returncode == 2 and "--title" in r.stdout, f"TS-17: start without a title -> usage: {r.stdout}")
        r = run(p, "start", "T-20261113-waga", "--title", "x", "--weight", "ogromna")
        check(r.returncode == 2 and not (p / CHANGES / "T-20261113-waga").exists(), f"TS-18: unknown weight rejected: {r.stdout}")

        # C2: slices and evidence — "done" means "there is evidence created after the last file change"
        def states(key):
            r = run(p, "status", key, "--json")
            try:
                return json.loads(r.stdout).get("slice_states", {})
            except ValueError:
                return {"error": r.stdout + r.stderr}

        (p / "src").mkdir()
        (p / "src" / "fees.py").write_text("CAP = 4000\n", encoding="utf-8")
        run(p, "start", "EV-1", "--title", "Dowody")
        r = run(p, "slice", "EV-1", "S1", "planned", "--title", "limit 45 zł")
        check(r.returncode == 0 and states("EV-1") == {"S1": "planned"}, f"TS-20: slice planned: {r.stdout}{states('EV-1')}")
        run(p, "slice", "EV-1", "S1", "implemented")
        check(states("EV-1") == {"S1": "unverified"}, f"TS-21: done without evidence is unverified: {states('EV-1')}")
        r = run(p, "verify", "EV-1", "S1", "--command", OK, "--files", "src/fees.py")
        ev = p / CHANGES / "EV-1" / "evidence" / "S1-1.json"
        e = json.loads(ev.read_text(encoding="utf-8")) if ev.is_file() else {}
        check(r.returncode == 0 and e.get("command") == OK and e.get("exit_code") == 0 and e.get("at")
              and len((e.get("files") or {}).get("src/fees.py", "")) == 64 and e.get("slice") == "S1",
              f"TS-22: evidence in evidence/S1-1.json: command, exit code, time, file hashes: {r.stdout}{r.stderr}{e}")
        check(states("EV-1") == {"S1": "verified"}, f"TS-23: green evidence on the current files -> verified: {states('EV-1')}")
        (p / "src" / "fees.py").write_text("CAP = 4500\n", encoding="utf-8")
        r = run(p, "status", "EV-1")
        check(states("EV-1") == {"S1": "unverified"} and "changed" in r.stdout and "S1" in r.stdout,
              f"TS-24: a file change after the evidence -> unverified, with a reason: {r.stdout}")
        r = run(p, "stage", "EV-1", "review")
        check(r.returncode == 1 and "S1" in r.stdout and task(p, "EV-1")["stage"] == "intake",
              f"TS-25: review rejected when a slice is not verified: {r.returncode} {r.stdout}")
        r = run(p, "verify", "EV-1", "S1", "--command", RED, "--files", "src/fees.py")
        e2 = json.loads((ev.parent / "S1-2.json").read_text(encoding="utf-8")) if (ev.parent / "S1-2.json").is_file() else {}
        log = p / ".tf" / "runs" / "EV-1" / "S1-2.log"
        check(r.returncode == 1 and e2.get("exit_code") == 3 and log.is_file() and "FAILED test_x" in log.read_text(encoding="utf-8")
              and "FAILED test_x" in r.stdout,
              f"TS-37: verify runs the command itself: the real exit code in the evidence, the output in .tf/runs/: {r.returncode} {r.stdout}{e2}")
        check(states("EV-1") == {"S1": "red"} and ev.is_file() and (ev.parent / "S1-2.json").is_file(),
              f"TS-26: red evidence -> red; the previous evidence stays, the new one gets the next number: {states('EV-1')}")
        run(p, "verify", "EV-1", "S1", "--command", OK, "--files", "src/fees.py")
        r = run(p, "stage", "EV-1", "review")
        check(r.returncode == 0 and task(p, "EV-1")["stage"] == "review", f"TS-27: review allowed after green evidence: {r.stdout}")
        (p / "src" / "fees.py").unlink()
        check(states("EV-1") == {"S1": "unverified"}, f"TS-28: a file deleted after the evidence -> unverified: {states('EV-1')}")

        (p / "src" / "cli.py").write_text("x = 1\n", encoding="utf-8")
        run(p, "start", "EV-2", "--title", "Blokada")
        r = run(p, "slice", "EV-2", "S1", "blocked", "--reason", "czeka na decyzję o stawce")
        check(states("EV-2") == {"S1": "blocked"} and run(p, "stage", "EV-2", "review").returncode == 1
              and "czeka na decyzję" in run(p, "status", "EV-2").stdout,
              f"TS-29: a blocked slice with a reason holds back the review: {r.stdout}{states('EV-2')}")
        r = run(p, "verify", "EV-2", "S2", "--command", OK)
        check(r.returncode == 2 and "--files" in r.stdout, f"TS-30: evidence without files rejected: {r.returncode} {r.stdout}")
        r = run(p, "verify", "EV-2", "S2", "--command", OK, "--files", "../poza.py")
        check(r.returncode == 2 and not (p / CHANGES / "EV-2" / "evidence").exists(), f"TS-31: a file outside the project rejected: {r.stdout}")
        r = run(p, "verify", "EV-2", "S2", "--command", OK, "--files", "src/nie-ma.py")
        check(r.returncode == 2 and "nie-ma.py" in r.stdout, f"TS-32: a nonexistent file rejected: {r.stdout}")
        r = run(p, "slice", "EV-2", "X1", "planned")
        check(r.returncode == 2, f"TS-33: a bad slice identifier rejected: {r.returncode} {r.stdout}")
        r = run(p, "slice", "EV-2", "S3", "gotowe")
        check(r.returncode == 2 and "implemented" in r.stdout, f"TS-34: unknown slice state -> list of states: {r.stdout}")
        run(p, "start", "EV-3", "--title", "Bez kawałków")
        check(run(p, "stage", "EV-3", "review").returncode == 0, "TS-35: a task without slices moves on to review")
        r = run(p, "verify", "EV-3", "S1", "--command", OK, "--files", "src/cli.py")
        check(r.returncode == 0 and states("EV-3") == {"S1": "verified"}, f"TS-36: verify creates the slice if it did not exist: {r.stdout}")
        r = run(p, "verify", "EV-3", "S2", "--files", "src/cli.py")
        check(r.returncode == 2 and "quality-gate.json" in r.stdout, f"TS-38: no --command and no gate -> nothing to run: {r.stdout}")
        (p / ".claude").mkdir(exist_ok=True)
        (p / ".claude" / "quality-gate.json").write_text(json.dumps({"command": OK}), encoding="utf-8")
        r = run(p, "verify", "EV-3", "S2", "--files", "src/cli.py")
        e3 = json.loads((p / CHANGES / "EV-3" / "evidence" / "S2-1.json").read_text(encoding="utf-8")) if r.returncode == 0 else {}
        check(r.returncode == 0 and e3.get("command") == OK and states("EV-3").get("S2") == "verified",
              f"TS-39: without --command verify runs the quality gate command: {r.stdout}{r.stderr}")
        r = run(p, "verify", "EV-3", "S2", "--command", OK, "--exit", "0", "--files", "src/cli.py")
        check(r.returncode == 2, f"TS-40: the exit code cannot be declared (--exit rejected): {r.returncode}")

        # C3: task files — who generated and approved them, what they were built from, whether they are still current
        def astates(key):
            r = run(p, "status", key, "--json")
            try:
                return json.loads(r.stdout).get("artifact_states", {})
            except ValueError:
                return {"error": r.stdout + r.stderr}

        run(p, "start", "AR-1", "--title", "Pliki zadania")
        folder = p / CHANGES / "AR-1"
        (folder / "spec.md").write_text(SPEC.format(limit=45), encoding="utf-8")
        (folder / "plan.md").write_text("# Plan\n- [ ] S1\n", encoding="utf-8")
        r = run(p, "artifact", "AR-1", "spec.md", "--stage", "spec", "--by", "tf/1.0.0")
        a = task(p, "AR-1").get("artifacts", {}).get("spec.md", {})
        check(r.returncode == 0 and a.get("stage") == "spec" and a.get("generated", {}).get("by") == "tf/1.0.0"
              and a.get("generated", {}).get("at") and astates("AR-1") == {"spec.md": "draft"},
              f"TS-41: file registered as a draft, with the author and time: {r.stdout}{r.stderr}{a}")
        r = run(p, "artifact", "AR-1", "nie-ma.md", "--stage", "plan", "--by", "tf/1.0.0")
        check(r.returncode == 2 and "nie-ma.md" in r.stdout, f"TS-42: a nonexistent file rejected: {r.stdout}")
        r = run(p, "approve", "AR-1", "spec.md", "--by", "tf/1.0.0")
        check(r.returncode == 2 and astates("AR-1") == {"spec.md": "draft"} and "human:" in r.stdout,
              f"TS-43: only a human approves (human:<id>): {r.returncode} {r.stdout}")
        r = run(p, "approve", "AR-1", "spec.md", "--by", "human:anna")
        a = task(p, "AR-1")["artifacts"]["spec.md"]
        check(r.returncode == 0 and astates("AR-1") == {"spec.md": "approved"}
              and a.get("verified", [{}])[-1].get("by") == "human:anna" and a["verified"][-1].get("at"),
              f"TS-44: approval by a human recorded with the time: {r.stdout}{a}")
        run(p, "artifact", "AR-1", "plan.md", "--stage", "plan", "--by", "tf/1.0.0", "--inputs", "spec.md")
        run(p, "approve", "AR-1", "plan.md", "--by", "human:anna")
        r = run(p, "check", "AR-1")
        check(r.returncode == 0 and astates("AR-1") == {"plan.md": "approved", "spec.md": "approved"},
              f"TS-45: everything current -> check 0: {r.returncode} {r.stdout}")
        (folder / "spec.md").write_text(SPEC.format(limit=50), encoding="utf-8")
        r = run(p, "check", "AR-1")
        s = astates("AR-1")
        check(r.returncode == 1 and s.get("plan.md") == "stale" and s.get("spec.md") == "changed-after-approval"
              and "spec.md" in r.stdout and "plan.md" in r.stdout,
              f"TS-46: a change to spec.md after the plan was approved -> plan stale, spec to be re-approved: {r.stdout}{s}")
        r = run(p, "status", "AR-1")
        check("stale" in r.stdout and "plan.md" in r.stdout, f"TS-47: human-readable status shows the stale file: {r.stdout}")
        run(p, "artifact", "AR-1", "plan.md", "--stage", "plan", "--by", "tf/1.0.0", "--inputs", "spec.md")
        check(astates("AR-1").get("plan.md") == "draft", f"TS-48: re-registering refreshes the inputs and clears the approval: {astates('AR-1')}")
        run(p, "approve", "AR-1", "spec.md", "--by", "human:anna")
        run(p, "approve", "AR-1", "plan.md", "--by", "human:jan")
        r = run(p, "check", "AR-1")
        check(r.returncode == 0 and len(task(p, "AR-1")["artifacts"]["plan.md"]["verified"]) == 1,
              f"TS-49: after re-approval check 0; old approvals do not remain: {r.stdout}")
        for bad, why in ((("artifact", "AR-1", "plan.md", "--stage", "plan", "--by", "tf/1.0.0", "--inputs", "../../x.md"), "input outside the directory"),
                         (("artifact", "AR-1", "plan.md", "--stage", "wymyslony", "--by", "tf/1.0.0"), "unknown stage"),
                         (("artifact", "AR-1", "plan.md", "--stage", "plan", "--by", "ktoś"), "bad author notation"),
                         (("artifact", "AR-1", "../EV-1/task.json", "--stage", "plan", "--by", "tf/1.0.0"), "file outside the directory"),
                         (("approve", "AR-1", "report.md", "--by", "human:anna"), "unregistered file")):
            r = run(p, *bad)
            check(r.returncode == 2, f"TS-50: rejected ({why}): {r.returncode} {r.stdout}")
        # file with a pdi contract header: registering and approving do not change a single byte
        run(p, "artifact", "CHG-12", "plan.md", "--stage", "plan", "--by", "process:pdi")
        run(p, "approve", "CHG-12", "plan.md", "--by", "human:anna")
        check((pdi / "plan.md").read_text(encoding="utf-8") == plan and astates("CHG-12") == {"plan.md": "approved"},
              f"TS-51: a pdi file registered and approved without changing its content: {astates('CHG-12')}")
        r = run(p, "stage", "AR-1", "implementation")
        (folder / "spec.md").write_text(SPEC.format(limit=55), encoding="utf-8")
        r = run(p, "stage", "AR-1", "review")
        check(r.returncode == 1 and "plan.md" in r.stdout and task(p, "AR-1")["stage"] == "implementation",
              f"TS-52: review rejected when a task file is stale: {r.returncode} {r.stdout}")

        # tf task ... runs the script in the project
        q = Path(t) / "viatf"
        (q / ".tf" / "factory").mkdir(parents=True)
        (q / ".claude").mkdir()
        (q / ".claude" / "factory-manifest.json").write_text(json.dumps({"version": "1.0.0"}))
        shutil.copy(SCRIPT, q / ".tf" / "factory" / "task_state.py")
        r = subprocess.run([sys.executable, str(CTF), "task", "start", "PROJ-9", "--title", "Przez tf"], cwd=q,
                           capture_output=True, text=True, timeout=60)
        check(r.returncode == 0 and task(q, "PROJ-9").get("title") == "Przez tf", f"TS-19: tf task start: {r.stdout}{r.stderr}")

        # task list (step C5): `tf status` — stage, slices with evidence, files to refresh; state computed on read
        r = run(q, "list")
        check(r.returncode == 0 and "PROJ-9" in r.stdout and "intake" in r.stdout and "Przez tf" in r.stdout,
              f"TS-53: list shows the task with its stage and title: {r.stdout}{r.stderr}")
        (q / "src").mkdir(exist_ok=True)
        (q / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
        run(q, "verify", "PROJ-9", "S1", "--command", OK, "--files", "src/a.py")
        run(q, "slice", "PROJ-9", "S2", "planned")
        r = run(q, "list", "--json")
        try:
            rows = {x["key"]: x for x in json.loads(r.stdout)}
        except (ValueError, KeyError, TypeError):
            rows = {}
        row = rows.get("PROJ-9", {})
        check(row.get("stage") == "intake" and row.get("slices") == {"S1": "verified", "S2": "planned"}
              and row.get("verified") == 1 and row.get("stale") == [],
              f"TS-54: list --json: stage, slice states, number verified: {r.stdout[:300]}{r.stderr}")
        (q / "src" / "a.py").write_text("a = 2\n", encoding="utf-8")
        r = run(q, "list")
        line = next((ln for ln in r.stdout.splitlines() if "PROJ-9" in ln), "")
        check("0/2" in line and "unverified" in r.stdout, f"TS-55: a file change after the evidence is visible on the list: {r.stdout}")
        r = subprocess.run([sys.executable, str(CTF), "status"], cwd=q, capture_output=True, text=True, timeout=60)
        check(r.returncode == 0 and "PROJ-9" in r.stdout, f"TS-56: tf status is the task list: {r.stdout}{r.stderr}")
        with tempfile.TemporaryDirectory() as e:
            r = run(Path(e), "list")
            check(r.returncode == 0 and "tf task start" in r.stdout, f"TS-57: no tasks -> hint, exit code 0: {r.returncode} {r.stdout}")

    # cut task of a pdi change (step E6): key <CHG>-<TSK>, fields `change` and `cut`, no row in INDEX.md
    with tempfile.TemporaryDirectory() as tmp:
        c = Path(tmp)
        r = run(c, "start", "CHG-12-TSK-57", "--title", "TSK-57: ponowienie płatności", "--change", "CHG-12", "--cut", "TSK-57")
        t = task(c, "CHG-12-TSK-57")
        check(r.returncode == 0 and t.get("change") == "CHG-12" and t.get("cut") == "TSK-57",
              f"TS-58: a cut task records the change and the cut: {r.returncode} {r.stdout}{r.stderr} {t}")
        check(not (c / CHANGES / "INDEX.md").exists(),
              "TS-59: a cut task does not create INDEX.md (PRs of one change's cuts have nothing to collide on)")
        run(c, "start", "PROJ-9", "--title", "Eksport sesji")
        r = run(c, "start", "CHG-12-TSK-58", "--title", "TSK-58: brak podwójnego obciążenia", "--change", "CHG-12", "--cut", "TSK-58")
        run(c, "stage", "CHG-12-TSK-58", "spec")
        check(r.returncode == 0 and not (c / CHANGES / "INDEX.md").exists()
              and len([ln for ln in index_rows(c) if "TSK-5" in ln]) == 2,
              f"TS-60: task writes do not create INDEX.md; the cuts are on the list: {index_rows(c)}")
        r = run(c, "list")
        line = next((ln for ln in r.stdout.splitlines() if "CHG-12-TSK-57" in ln), "")
        check("cut TSK-57 of the change CHG-12" in line, f"TS-61: the list shows the cut and its change: {r.stdout}")
        r = run(c, "list", "--json")
        try:
            rows = {x["key"]: x for x in json.loads(r.stdout)}
        except (ValueError, KeyError, TypeError):
            rows = {}
        check(rows.get("CHG-12-TSK-57", {}).get("change") == "CHG-12" and rows.get("CHG-12-TSK-57", {}).get("cut") == "TSK-57"
              and "change" not in rows.get("PROJ-9", {"change": 1}),
              f"TS-62: list --json gives the change and the cut only for a cut task: {r.stdout[:400]}")
        r = run(c, "status", "CHG-12-TSK-57")
        check("cut TSK-57 of the change CHG-12" in r.stdout, f"TS-63: status shows the cut and its change: {r.stdout}")
        r = run(c, "start", "CHG-12-TSK-60", "--title", "x", "--cut", "TSK-60")
        r2 = run(c, "start", "CHG-12-TSK-61", "--title", "x", "--change", "CHG-12")
        check(r.returncode == 2 and r2.returncode == 2 and not task(c, "CHG-12-TSK-60") and not task(c, "CHG-12-TSK-61"),
              f"TS-64: --cut and --change only together -> exit code 2: {r.returncode} {r2.returncode}")
        r = run(c, "start", "TSK-62", "--title", "x", "--change", "CHG-12", "--cut", "TSK-62")
        check(r.returncode == 2 and "CHG-12-TSK-62" in r.stdout and not task(c, "TSK-62"),
              f"TS-65: a cut task key is <CHG>-<TSK> -> exit code 2 with a hint: {r.returncode} {r.stdout}")
        r = run(c, "start", "CHG-12-TSK-63", "--title", "x", "--change", "chg/12", "--cut", "TSK-63")
        check(r.returncode == 2, f"TS-66: bad shape of the change key -> exit code 2: {r.returncode} {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} task state tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
