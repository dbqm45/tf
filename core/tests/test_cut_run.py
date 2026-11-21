#!/usr/bin/env python3
"""A pdi change cut run in the task layout (step E6): `/tf TSK-57 --change CHG-12` creates the task
`CHG-12-TSK-57` with a specification, evidence and a flag from the release plan, and pdi gets what it has so far — the cut report
in `docs/project/changes/CHG-12/runs/TSK-57.md`, the `story/tsk-57-...` branch and the first commit with a slice.
python3 .claude/tests/test_cut_run.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPTS = ROOT / ".claude" / "skills" / "tf" / "scripts"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'3 passed\')"'

PLAN_MD = """---
artifact: plan
phase: plan
status: accepted
version: 1
created: 2026-10-25
updated: 2026-10-25
change: CHG-12
tasks: [TSK-57, TSK-58, TSK-59]
---
# Plan zmiany CHG-12

| Slice | Release | Flag | Value | Files | Verification |
|---|---|---|---|---|---|
| TSK-57 | R1 | payment-retry | klient ponawia nieudaną płatność | src/retry.py | `pytest -k retry` |
| TSK-58 | R1 | payment-retry | brak podwójnego obciążenia | src/charge.py | `pytest -k charge` |
| TSK-59 | R2 | — | historia prób w panelu | src/history.py | `pytest -k history` |
"""
INTENT_MD = """---
artifact: intent
phase: discovery
status: accepted
version: 1
created: 2026-10-25
updated: 2026-10-25
change: CHG-12
---
# Zamiar zmiany CHG-12

## Problem
Klient nie może ponowić nieudanej płatności i porzuca zamówienie.
"""
RELEASE = """change: CHG-12
flags:
  - key: payment-retry
    tasks: [TSK-57, TSK-58]
    owner: PO Payments
    remove_by: 2026-12-31
"""
# the same expression pdi uses to read the list of postponed items from the cut's PR description (pdi: src/pdi/pr_loop.py, _outside_plan)
PDI_PARKED = re.compile(r"^## (?:Postponed for a decision|Odłożone do decyzji)\s*\n([\s\S]*?)(?=^## |\Z)", re.MULTILINE)


def sh(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=project, capture_output=True, text=True, timeout=60)


def git(project: Path, *args: str) -> str:
    r = sh(project, "git", *args)
    assert r.returncode == 0, (args, r.stdout, r.stderr)
    return r.stdout


def script(project: Path, cfg: Path, name: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "CLAUDE_PROJECT_DIR": str(project), "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(SCRIPTS / name), *args], cwd=project, capture_output=True, text=True,
                          env=env, timeout=120)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p, cfg = Path(t) / "proj", Path(t) / "cfg"
        chg = p / CHANGES / "CHG-12"
        chg.mkdir(parents=True)
        (chg / "plan.md").write_text(PLAN_MD, encoding="utf-8")
        (chg / "intent.md").write_text(INTENT_MD, encoding="utf-8")
        (chg / "release.yaml").write_text(RELEASE, encoding="utf-8")
        (p / "src").mkdir()
        (p / "src" / "retry.py").write_text("def retry():\n    return False\n", encoding="utf-8")
        git(p, "init", "-q", "-b", "main")
        for k, v in (("user.name", "t"), ("user.email", "t@t"), ("commit.gpgsign", "false")):
            git(p, "config", k, v)
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "docs: plan zmiany CHG-12")
        git(p, "switch", "-q", "-c", "pdi/CHG-12-delivery")
        git(p, "switch", "-q", "-c", "story/tsk-57-ponowienie-platnosci")

        # start: a cut task instead of the .tf/runs/cuts/ directory
        r = script(p, cfg, "run_report.py", "start", "--task", "TSK-57", "--change", "CHG-12")
        run_dir, doc = p / ".tf" / "runs" / "CHG-12-TSK-57", p / CHANGES / "CHG-12-TSK-57"
        check(r.returncode == 0 and r.stdout.strip() == ".tf/runs/CHG-12-TSK-57" and run_dir.is_dir()
              and not (p / ".tf" / "runs" / "cuts").exists(),
              f"C-1: start --task creates the working directory of the cut task, without .tf/runs/cuts/: {r.returncode} {r.stdout} {r.stderr}")
        check(all((doc / n).is_file() for n in ("task.json", "ticket.md", "plan.md")) and not (run_dir / "story.md").exists(),
              f"C-2: the cut's persistent files in docs/project/changes/CHG-12-TSK-57/: {sorted(x.name for x in doc.iterdir()) if doc.is_dir() else '—'}")
        task = json.loads((doc / "task.json").read_text(encoding="utf-8")) if (doc / "task.json").is_file() else {}
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8")) if (run_dir / "run.json").is_file() else {}
        check(task.get("change") == "CHG-12" and task.get("cut") == "TSK-57" and meta.get("key") == "CHG-12-TSK-57"
              and meta.get("task_dir") == "docs/project/changes/CHG-12-TSK-57" and meta.get("change") == "CHG-12"
              and meta.get("task") == "TSK-57" and meta.get("flag") == "payment-retry",
              f"C-3: task.json and run.json point to the change, the cut and the flag: {task} {meta}")
        ticket = (doc / "ticket.md").read_text(encoding="utf-8") if (doc / "ticket.md").is_file() else ""
        check("Cut TSK-57 of the change CHG-12" in ticket and "klient ponawia nieudaną płatność" in ticket
              and "Klient nie może ponowić" in ticket and "`Change: TSK-57`" in ticket and "`Flag: payment-retry`" in ticket,
              f"C-4: ticket.md from the cut's row and the change intent, with commit footers: {ticket[:500]}")
        flag = task.get("flag") or {}
        check(flag.get("key") == "payment-retry" and flag.get("remove_by") == "2026-12-31",
              f"C-5: the flag from the release plan saved in the task (key and removal date): {flag}")
        check(not (p / CHANGES / "INDEX.md").exists(), "C-6: a cut task does not create INDEX.md")
        status = git(p, "status", "--porcelain")
        check(status.split() == ["??", "docs/project/changes/CHG-12-TSK-57/"],
              f"C-7: after the start the repository has only the new task directory: {status!r}")
        r = script(p, cfg, "run_report.py", "start", "--task", "TSK-57", "--change", "CHG-12")
        check(r.returncode == 2 and "already exists" in r.stdout, f"C-8: a repeated start -> code 2: {r.returncode} {r.stdout}")
        r = script(p, cfg, "intake.py", "resolve", "--json", "TSK-57 --auto --change CHG-12")
        try:
            out = json.loads(r.stdout)
        except ValueError:
            out = {}
        check(out.get("kind") == "resume" and out.get("key") == "CHG-12-TSK-57" and ".tf/runs/CHG-12-TSK-57" in out.get("next", ""),
              f"C-9: /tf TSK-57 with an existing cut task resumes it: {r.stdout[:400]} {r.stderr[-200:]}")

        # a cut without a flag in the release plan: an explicit no-flag with a reason, without asking a human
        r = script(p, cfg, "run_report.py", "start", "--task", "TSK-59", "--change", "CHG-12")
        t59 = json.loads((p / CHANGES / "CHG-12-TSK-59" / "task.json").read_text(encoding="utf-8")) if r.returncode == 0 else {}
        check("CHG-12" in ((t59.get("flag") or {}).get("none") or "") and "TSK-59" in ((t59.get("flag") or {}).get("none") or ""),
              f"C-10: a cut without a flag in the release plan -> 'no flag' with a reason: {t59.get('flag')} {r.stdout} {r.stderr}")
        import shutil
        shutil.rmtree(p / CHANGES / "CHG-12-TSK-59")
        shutil.rmtree(p / ".tf" / "runs" / "CHG-12-TSK-59")

        # run commands work for a cut as for a task
        d = str(run_dir)
        r = script(p, cfg, "run_state.py", "stage", d, "intake", "--auto")
        task = json.loads((doc / "task.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and task.get("mode") == "auto" and task.get("weight") == "full",
              f"C-11: --auto records Auto mode also for a cut of full weight (payments): {r.returncode} {r.stdout} {r.stderr} "
              f"{task.get('mode')} {task.get('weight')}")
        r = script(p, cfg, "run_state.py", "spec", d, "new")
        check(r.returncode == 0 and (doc / "spec.md").is_file(), f"C-12: the cut's specification template: {r.returncode} {r.stdout} {r.stderr}")
        (doc / "spec.md").write_text(
            "# Spec\n\n## Acceptance criteria\n\n- AC-1: Given nieudaną płatność, when klient wybiera ponowienie, then "
            "płatność jest ponawiana raz.\n\n## Unchanged\n\n- Udana płatność nie jest ponawiana.\n\n## Out of scope\n\n"
            "- Płatności cykliczne.\n", encoding="utf-8")
        r = script(p, cfg, "run_state.py", "spec", d)
        check(r.returncode == 0, f"C-13: the cut's specification passes the check: {r.returncode} {r.stdout} {r.stderr}")
        (doc / "plan.md").write_text("# Plan: TSK-57\n\n- [ ] S1 — ponowienie płatności · criteria: AC-1 · files: src/retry.py, "
                                     "tests/test_retry.py · verify: `pytest -k retry`\n", encoding="utf-8")
        r = script(p, cfg, "run_state.py", "stage", d, "plan")
        r2 = script(p, cfg, "run_state.py", "step", d, "S1", "R1", "test", "run")
        check(r.returncode == 0 and r2.returncode == 0,
              f"C-14: a full-weight cut in Auto mode goes from the plan to a slice without human consent: "
              f"{r.returncode} {r.stdout} {r.stderr} | {r2.returncode} {r2.stdout} {r2.stderr}")

        # slice: a commit with footers, verification evidence, ticking off
        (p / "src" / "retry.py").write_text("def retry():\n    return True\n", encoding="utf-8")
        (p / "tests").mkdir()
        (p / "tests" / "test_retry.py").write_text("def test_ac_1_retry():   # AC-1\n    assert True\n", encoding="utf-8")
        git(p, "add", "src/retry.py", "tests/test_retry.py")
        git(p, "commit", "-q", "-m", "feat(payments): retry a failed payment\n\nSlice S1: ponowienie płatności\n\n"
                                     "Change: TSK-57\nFlag: payment-retry")
        r = script(p, cfg, "run_state.py", "verify", d, "S1", "--files", "src/retry.py,tests/test_retry.py", "--command", OK)
        ev = sorted((doc / "evidence").glob("S1-*.json")) if (doc / "evidence").is_dir() else []
        check(r.returncode == 0 and len(ev) == 1, f"C-15: verification evidence of the cut's slice: {r.returncode} {r.stdout} {r.stderr}")
        script(p, cfg, "run_state.py", "step", d, "S1", "R1", "scope", "pass")   # scope review before tick
        r = script(p, cfg, "run_state.py", "tick", d, "S1")
        check(r.returncode == 0 and "- [x] S1" in (doc / "plan.md").read_text(encoding="utf-8"),
              f"C-16: tick ticks off a slice with evidence: {r.returncode} {r.stdout} {r.stderr}")
        r = script(p, cfg, "run_state.py", "trace", d, "--base", "pdi/CHG-12-delivery")
        check(r.returncode == 0 and "AC-1" in r.stdout, f"C-17: the cut's criteria trace: {r.returncode} {r.stdout} {r.stderr}")

        # finish: the report in the task directory and the same one in the place pdi reads it from
        r = script(p, cfg, "run_state.py", "park", d, "limit prób ponowienia — src/retry.py:2 — brak limitu — dodać limit 3 — do decyzji")
        r = script(p, cfg, "run_report.py", "finish", d)
        kept = chg / "runs" / "TSK-57.md"
        text = kept.read_text(encoding="utf-8") if kept.is_file() else ""
        own = (doc / "report.md").read_text(encoding="utf-8") if (doc / "report.md").is_file() else ""
        check(r.returncode == 2 and text.startswith("# Run report TSK-57 (CHG-12)\n\n") and own
              and text == "# Run report TSK-57 (CHG-12)\n\n" + own,
              f"C-18: the cut report where pdi looks for it, with the same content as the task's report.md: {r.returncode} {text[:200]}")
        m = PDI_PARKED.search(text)
        items = [ln.strip()[2:] for ln in (m.group(1) if m else "").splitlines() if ln.strip().startswith("- ")]
        check(len(items) == 1 and "limit prób ponowienia" in items[0] and "- Plan: 1/1" in text,
              f"C-19: pdi will read the postponed items from the report; plan progress from commits with the Change footer: {items} {text[:400]}")
        check("git add docs/project/changes/CHG-12-TSK-57 docs/project/changes/CHG-12/runs/TSK-57.md" in r.stdout
              and "INDEX.md" not in r.stdout and "docs(task): record CHG-12-TSK-57" in r.stdout and "Change: TSK-57" in r.stdout,
              f"C-20: finish gives one final commit: the task directory and the cut report, without INDEX.md, with a footer: {r.stdout[-500:]}")
        git(p, "add", "docs/project/changes/CHG-12-TSK-57", "docs/project/changes/CHG-12/runs/TSK-57.md")
        git(p, "commit", "-q", "-m", "docs(task): record CHG-12-TSK-57\n\nChange: TSK-57")
        subjects = git(p, "log", "--reverse", "--format=%s", "pdi/CHG-12-delivery..HEAD").splitlines()
        check(subjects[:1] == ["feat(payments): retry a failed payment"] and git(p, "status", "--porcelain") == "",
              f"C-21: the first commit of the cut branch is the slice (the PR title in pdi), clean tree: {subjects}")
        body = git(p, "show", "story/tsk-57-ponowienie-platnosci:docs/project/changes/CHG-12/runs/TSK-57.md")
        check(body == text, "C-22: the cut report is on the cut branch at the path pdi reads")

    # a run in the old layout (without a task) is no longer created or continued
    with tempfile.TemporaryDirectory() as t:
        p, cfg = Path(t) / "proj", Path(t) / "cfg"
        old = p / ".tf" / "runs" / "cuts" / "2026-11-01-tsk-1"
        old.mkdir(parents=True)
        (old / "run.json").write_text(json.dumps({"slug": "tsk-1", "started_at": "2026-11-01T10:00:00+00:00",
                                                  "change": "CHG-1", "task": "TSK-1"}), encoding="utf-8")
        r = script(p, cfg, "run_state.py", "verify", str(old), "S1", "--files", "a.py")
        check(r.returncode != 0 and "start the cut again" in r.stdout + r.stderr and "/tf-task TSK-1" in r.stdout + r.stderr,
              f"C-23: a run without a task -> the 'start the cut again' message: {r.returncode} {r.stdout} {r.stderr}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} cut run tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
