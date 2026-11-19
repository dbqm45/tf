#!/usr/bin/env python3
"""Tests of the run report (skill tf, scripts/run_report.py).
python3 .claude/tests/test_run_report.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "run_report.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL


PLAN_MD = """---
artifact: plan
phase: plan
status: accepted
version: 1
created: 2026-10-25
updated: 2026-10-25
change: CHG-12
tasks: [TSK-57, TSK-58]
---
# Plan zmiany CHG-12

| Slice | Release | Flag | Value | Files | Verification |
|---|---|---|---|---|---|
| TSK-57 | R1 | payment-retry | klient ponawia nieudaną płatność | src/payments/retry.ts | `npm test -- retry` |
| TSK-58 | R1 | payment-retry | brak podwójnego obciążenia | src/payments/charge.ts | `npm test -- charge` |
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

## Out of scope
- płatności cykliczne
"""


def run(args, cwd, cfg):
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "TF_DASHBOARD_OPEN": "0"}   # tests do not open a browser
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, env=env,
                          timeout=60)


def assistant(ts, mid, model, **usage):
    u = {"input_tokens": usage.get("i", 0), "output_tokens": usage.get("o", 0),
         "cache_read_input_tokens": usage.get("cr", 0),
         "cache_creation_input_tokens": usage.get("w5", 0) + usage.get("w1", 0),
         "cache_creation": {"ephemeral_5m_input_tokens": usage.get("w5", 0),
                            "ephemeral_1h_input_tokens": usage.get("w1", 0)}}
    return {"type": "assistant", "timestamp": ts, "message": {"id": mid, "model": model, "usage": u}}


def write_jsonl(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()

        # start (step C4): the task has a durable directory docs/project/changes/<KEY>/ (ticket.md, plan.md, task.json — committed to git)
        # and a working directory .tf/runs/<KEY>/ (run.json, parked.md — outside git; not `.claude/runs/`, which Claude Code protects);
        # key T-<YYYYMMDD>-<slug>, slug without Polish characters; a new run no longer appears in .tf/runs/cuts/
        r = run(["start", "Import rozliczeń CDR", "--story", "Jako operator chcę importować CDR."], proj, cfg)
        runs = sorted((proj / ".tf" / "runs").glob("T-*-import-rozliczen-cdr"))
        old = sorted((proj / ".tf" / "runs" / "cuts").glob("*-import-rozliczen-cdr"))
        check(r.returncode == 0 and len(runs) == 1 and not old and not (proj / ".claude" / "runs").exists()
              and r.stdout.strip() == f".tf/runs/{runs[0].name if runs else '?'}",
              f"R-1: start creates .tf/runs/<KEY>/ and prints its path, no .tf/runs/cuts/<slug>: {r.stdout} {r.stderr}")
        if runs:
            d = runs[0]
            doc = proj / "docs" / "project" / "changes" / d.name
            check(all((d / f).is_file() for f in ("run.json", "parked.md"))
                  and all((doc / f).is_file() for f in ("ticket.md", "plan.md", "task.json"))
                  and not (doc / "spec.md").exists()      # the spec template is created only when it is filled in
                  and not (d / "plan.md").exists() and not (d / "story.md").exists(),
                  f"R-2: working and durable files: {sorted(x.name for x in d.iterdir())} "
                  f"{sorted(x.name for x in doc.iterdir()) if doc.is_dir() else '—'}")
            check(doc.is_dir() and "importować CDR" in (doc / "ticket.md").read_text(encoding="utf-8"),
                  "R-3: story text saved in ticket.md")
            check(re.fullmatch(r"T-\d{8}-import-rozliczen-cdr", d.name) is not None, f"R-4: key with date and slug: {d.name}")
            meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
            index = proj / "docs" / "project" / "changes" / "INDEX.md"
            check(meta.get("key") == d.name and meta.get("task_dir") == f"docs/project/changes/{d.name}"
                  and not index.exists(),
                  f"R-4a: run.json points to the task; start does not create the INDEX.md listing (tf status gives the list): {meta}")
        # PRB-32 — a product clone without `.tf/runs/cuts/` in .gitignore shows "?? tmp/" in status after the first start, and the hook
        # "clean working tree" of the loop (SKILL §0.1) and dispatch_local pdi treat the clone as dirty. The script creates
        # `.tf/runs/cuts/.gitignore` with `*`, as docs/plugins.md describes for standalone mode installs.
        gi = proj / ".tf" / "runs" / ".gitignore"
        check(gi.is_file() and gi.read_text(encoding="utf-8").strip() == "*",
              f"R-1a: start creates .tf/runs/.gitignore with `*`: exists={gi.is_file()}, "
              f"content={gi.read_text(encoding='utf-8') if gi.is_file() else '—'!r}")
        import subprocess as _sp
        _sp.run(["git", "init", "-q", "-b", "main", str(proj)], check=True, capture_output=True)
        for _k, _v in (("user.name", "t"), ("user.email", "t@t"), ("commit.gpgsign", "false")):
            _sp.run(["git", "-C", str(proj), "config", _k, _v], check=True, capture_output=True)
        porcelain = _sp.run(["git", "-C", str(proj), "status", "--porcelain", ".tf/runs/"],
                            capture_output=True, text=True).stdout
        check(porcelain == "", f"R-1b: after start git status is empty in .tf/runs/: {porcelain!r}")

        # tracker key, repeated start, bad key; finish in the new layout writes the report into the task directory
        r = run(["start", "Limit dobowy", "--key", "PROJ-123", "--story", "x"], proj, cfg)
        pdoc = proj / "docs" / "project" / "changes" / "PROJ-123"
        check(r.returncode == 0 and r.stdout.strip() == ".tf/runs/PROJ-123" and (pdoc / "task.json").is_file(),
              f"R-25: --key sets the tracker key: {r.stdout} {r.stderr}")
        r = run(["start", "Limit dobowy", "--key", "PROJ-123", "--story", "x"], proj, cfg)
        check(r.returncode == 2 and "already exists" in r.stdout + r.stderr, f"R-26: repeated start with the same key: {r.stdout}")
        r = run(["start", "Zły klucz", "--key", "proj 1", "--story", "x"], proj, cfg)
        check(r.returncode == 2 and not (proj / ".tf" / "runs" / "proj 1").exists(),
              f"R-27: key outside the pattern rejected, nothing is created: {r.returncode} {r.stdout}")
        (pdoc / "plan.md").write_text("# Plan\n- [x] S1 — limit\n- [ ] S2 — druga doba\n", encoding="utf-8")
        prun = proj / ".tf" / "runs" / "PROJ-123"
        r = run(["finish", str(prun)], proj, Path(t) / "cfg-pusty")
        rep = (pdoc / "report.md").read_text(encoding="utf-8") if (pdoc / "report.md").is_file() else ""
        check(r.returncode == 2 and "1/2" in rep and not (prun / "report.md").exists(),
              f"R-28: finish reads the plan from the task directory and writes the report there: {r.returncode} {rep[:200]}")
        check("docs(task): record PROJ-123" in r.stdout and "docs/project/changes/PROJ-123" in r.stdout,
              f"R-29: finish suggests one commit of the task files: {r.stdout[-300:]}")

        # finish: session and subagent transcripts since the start (run in .tf/runs/cuts/)
        run_dir = proj / ".tf" / "runs" / "cuts" / "2026-10-21-test"
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps({"slug": "test", "started_at": "2026-10-21T10:00:00+00:00"}))
        (run_dir / "plan.md").write_text("# Plan\n- [x] S1 import\n- [x] S2 walidacja\n- [ ] S3 raport\n")
        (run_dir / "parked.md").write_text("# Odłożone\n- duplikaty CDR — do decyzji\n- strefy czasowe — do decyzji\n")
        slug = re.sub(r"[^A-Za-z0-9]", "-", str(proj.resolve()))
        sess = cfg / "projects" / slug / "S1.jsonl"
        write_jsonl(sess, [
            assistant("2026-10-21T09:59:00Z", "m0", "claude-opus-5-5", i=100, o=100),     # before the start
            {"type": "user", "timestamp": "2026-10-21T10:00:05Z", "message": {"content": "story"}},
            assistant("2026-10-21T10:01:00Z", "m1", "claude-opus-5-5", i=10, o=5, cr=1000, w1=200),
            assistant("2026-10-21T10:01:01Z", "m1", "claude-opus-5-5", i=10, o=50, cr=1000, w1=200),  # complete write
            assistant("2026-10-21T10:02:00Z", "m2", "claude-haiku-5-5", i=20, o=10),
        ])
        sub = cfg / "projects" / slug / "S1" / "subagents" / "agent-x.jsonl"
        write_jsonl(sub, [assistant("2026-10-21T10:05:00Z", "s1", "claude-haiku-5-5", i=30, o=15, w5=100)])
        (sub.parent / "agent-x.meta.json").write_text(json.dumps({"agentType": "scout"}))

        r = run(["finish", str(run_dir), "--json"], proj, cfg)
        try:
            rep = json.loads(r.stdout)
        except json.JSONDecodeError:
            rep = {}
            fails.append(f"R-5: finish --json returns JSON: {r.stdout[-500:]} {r.stderr[-500:]}")
        if rep:
            opus, haiku = rep["models"].get("opus", {}), rep["models"].get("haiku", {})
            check((opus.get("input"), opus.get("output"), opus.get("cache_read"), opus.get("cache_write_1h")) == (10, 50, 1000, 200),
                  f"R-6: opus — without the entry from before the start, last stream write: {opus}")
            check((haiku.get("input"), haiku.get("output"), haiku.get("cache_write_5m")) == (50, 25, 100),
                  f"R-7: haiku — session and subagent together: {haiku}")
            # opus: 10×4 + 50×20 + 1000×0.20 + 200×8 (1 h write = 2× input); haiku: 50×0.10 + 25×0.50 + 100×0.125
            check(abs(rep["cost_usd"] - (2840 + 30) / 1e6) < 1e-9, f"R-8: total cost: {rep.get('cost_usd')}")
            check(rep.get("duration_s") == 300, f"R-9: time from the start to the last entry: {rep.get('duration_s')}")
            check(rep.get("agents", {}).get("scout", {}).get("output") == 15 and "main" in rep.get("agents", {}),
                  f"R-10: split by agent (type from the subagent meta): {rep.get('agents')}")
            check(rep.get("plan") == {"done": 2, "total": 3} and rep.get("parked") == 2,
                  f"R-11: plan progress and number of parked items: {rep.get('plan')} {rep.get('parked')}")
        md = (run_dir / "report.md").read_text(encoding="utf-8") if (run_dir / "report.md").exists() else ""
        check("opus" in md and "haiku" in md and "USD" in md and "2/3" in md, f"R-12: report.md: {md[:400]}")
        check("- Tokens: " in md and "input" in md.split("- Tokens: ", 1)[-1].split("\n", 1)[0],
              f"R-12b: report.md gives the total tokens with the split: {md[:600]}")
        check("## Security" in md and "no scan result" in md, f"R-14: without a scan the section says it is missing: {md[-300:]}")

        # R-11a: a slice with a commit counts as done even when the loop did not tick it in plan.md (CHG-4, 2026-11-07:
        # "Plan: 0/1" with a finished commit). Base: the phase branch pdi/<CHG>-delivery when the run has a change, otherwise main.
        def git(*a: str) -> None:
            _sp.run(["git", "-C", str(proj), *a], check=True, capture_output=True)
        (proj / "README.md").write_text("x\n")
        git("add", "README.md")
        git("commit", "-q", "-m", "chore: base")
        git("switch", "-q", "-c", "pdi/CHG-90-delivery")
        (proj / "decisions.md").write_text("d\n")
        git("add", "decisions.md")
        git("commit", "-q", "-m", "docs(CHG-90): decisions before delivery (pdi)")
        git("switch", "-q", "-c", "story/k")
        (proj / "a.py").write_text("a = 1\n")
        git("add", "a.py")
        git("commit", "-q", "-m", "feat: a\n\nChange: TSK-90")
        cut_dir = proj / ".tf" / "runs" / "cuts" / "2026-10-21-cut"
        cut_dir.mkdir(parents=True)
        (cut_dir / "run.json").write_text(json.dumps({"slug": "cut", "started_at": "2026-10-21T10:00:00+00:00",
                                                      "change": "CHG-90", "task": "TSK-90"}))
        (cut_dir / "plan.md").write_text("# Plan\n- [ ] S1 a\n- [ ] S2 b\n")
        r = run(["finish", str(cut_dir), "--json"], proj, cfg)
        try:
            got = json.loads(r.stdout).get("plan")
        except json.JSONDecodeError:
            got = r.stdout[-300:]
        check(got == {"done": 1, "total": 2},
              f"R-11a: a slice commit counts despite no tick, a pdi decisions commit does not: {got}")
        git("switch", "-q", "main")
        import shutil as _sh
        _sh.rmtree(proj / "docs" / "project" / "changes" / "CHG-90", ignore_errors=True)

        # the "Security" section from the slice scans' summary.md (security_scan.py --out <run>/security/S<n>)
        sec = run_dir / "security" / "S2"
        sec.mkdir(parents=True)
        (sec / "summary.md").write_text("## Security\n\nScan: PASS (blocking: 0, below the threshold: 1, scan errors: 0).\n\n"
                                        "Below the threshold:\n- r.note src/a.py:3 (note) — nitpick\n", encoding="utf-8")
        run(["finish", str(run_dir)], proj, cfg)
        md = (run_dir / "report.md").read_text(encoding="utf-8")
        check(md.count("## Security") == 1 and "### S2" in md and "r.note src/a.py:3" in md
              and "no scan result" not in md, f"R-15: security section from the scan result: {md[-400:]}")
        # every slice attempt (security/S<n>/attempt-<k>/summary.md): FAIL with findings, then PASS — in attempt order
        for k, body in ((1, "Scan: FAIL (blocking: 1, below the threshold: 0, scan errors: 0).\n\nBelow the threshold: none.\n\n"
                            "Blocking and errors:\n- node-sqlite-sql-from-string src/deployments.js:14 (CWE-89, warning)\n"),
                        (2, "Scan: PASS (blocking: 0, below the threshold: 0, scan errors: 0).\n\nBelow the threshold: none.\n")):
            (sec.parent / "S1" / f"attempt-{k}").mkdir(parents=True)
            (sec.parent / "S1" / f"attempt-{k}" / "summary.md").write_text("## Security\n\n" + body, encoding="utf-8")
        (sec.parent / "S1" / "feedback.md").write_text("# Security scan\n\n- no blocking findings\n", encoding="utf-8")
        run(["finish", str(run_dir)], proj, cfg)
        md = (run_dir / "report.md").read_text(encoding="utf-8")
        i = {k: md.find(k) for k in ("### S1", "#### Attempt 1", "node-sqlite-sql-from-string src/deployments.js:14",
                                     "#### Attempt 2", "### S2")}
        check(all(v >= 0 for v in i.values()) and list(i.values()) == sorted(i.values()) and md.count("## Security") == 1
              and md.count("### S1") == 1 and "Scan: FAIL" in md, f"R-15a: all slice attempts in the report: {i} {md[-900:]}")

        # status: one line for the budget check after every slice (little context), without writing report.md
        (run_dir / "report.md").unlink()
        r = run(["status", str(run_dir)], proj, cfg)
        line = r.stdout.strip()
        check(r.returncode == 0 and line.count("\n") == 0 and "0.0029 USD" in line and "2/3" in line
              and not (run_dir / "report.md").exists(), f"R-14: status on one line: {line!r}")

        # F1: a run from the change's slice key (TSK from plan.md in docs/project/changes/CHG-n/), report in the repo
        chg = proj / "docs" / "project" / "changes" / "CHG-12"
        chg.mkdir(parents=True)
        (chg / "plan.md").write_text(PLAN_MD, encoding="utf-8")
        (chg / "intent.md").write_text(INTENT_MD, encoding="utf-8")
        r = run(["start", "--task", "TSK-58"], proj, cfg)
        tr = proj / ".tf" / "runs" / "CHG-12-TSK-58"                    # step E6: a slice is the task <CHG>-<TSK>
        cut_doc = proj / "docs" / "project" / "changes" / "CHG-12-TSK-58"
        meta = json.loads((tr / "run.json").read_text(encoding="utf-8")) if (tr / "run.json").is_file() else {}
        story = (cut_doc / "ticket.md").read_text(encoding="utf-8") if (cut_doc / "ticket.md").is_file() else ""
        check(r.returncode == 0 and meta.get("change") == "CHG-12" and meta.get("task") == "TSK-58"
              and meta.get("flag") == "payment-retry" and meta.get("key") == "CHG-12-TSK-58"
              and not list((proj / ".tf" / "runs" / "cuts").glob("*tsk-58*")),
              f"R-15: start --task — run directory of the slice task, run.json with change/task/flag: {r.stdout} {r.stderr} {meta}")
        check("TSK-58" in story and "brak podwójnego obciążenia" in story and "R1" in story
              and "Klient nie może ponowić" in story and "docs/project/changes/CHG-12" in story,
              f"R-16: ticket.md from the plan row and the change intent: {story[:600]}")
        # R-16b: a second change from the plan template (mode-pdi) — the columns `Flag` and `Value` give the flag and the title.
        chg_en = proj / "docs" / "project" / "changes" / "CHG-14"
        chg_en.mkdir(parents=True)
        (chg_en / "plan.md").write_text(PLAN_MD.replace("change: CHG-12", "change: CHG-14").replace("TSK-57, TSK-58", "TSK-61")
                                        .split("| Slice")[0] + "| Slice | Release | Flag | Value | Files | Verification |\n"
                                        "|---|---|---|---|---|---|\n| TSK-61 | R1 | card-retry | the customer retries a card | "
                                        "src/card.ts | `npm test` |\n", encoding="utf-8")
        r = run(["start", "--task", "TSK-61"], proj, cfg)
        tr_en = proj / ".tf" / "runs" / "CHG-14-TSK-61"
        meta_en = json.loads((tr_en / "run.json").read_text(encoding="utf-8")) if (tr_en / "run.json").is_file() else {}
        check(r.returncode == 0 and meta_en.get("flag") == "card-retry" and "the customer retries a card" in str(meta_en),
              f"R-16b: plan in English — flag from the Flag column, title from Value: {r.stdout} {r.stderr[-300:]} {meta_en}")
        import shutil as _sh_en
        for leftover in (chg_en, tr_en, proj / "docs" / "project" / "changes" / "CHG-14-TSK-61"):
            _sh_en.rmtree(leftover, ignore_errors=True)
        r = run(["start", "--task", "TSK-99"], proj, cfg)
        check(r.returncode == 2 and "TSK-99" in r.stdout + r.stderr and "Traceback" not in r.stderr,
              f"R-17: TSK outside the change plans → code 2 with a message: {r.returncode} {r.stdout} {r.stderr[-300:]}")

        # PRB-33: the same TSK in two changes → error with a list of changes; --change decides; bad --change → error
        chg2 = proj / "docs" / "project" / "changes" / "CHG-13"
        chg2.mkdir(parents=True)
        plan2 = (PLAN_MD.replace("change: CHG-12", "change: CHG-13")
                 .replace("# Plan zmiany CHG-12", "# Plan zmiany CHG-13")
                 # a different value in CHG-13 so the slug does not collide with the directory from R-15
                 .replace("brak podwójnego obciążenia", "ponowienie w CHG-13"))
        (chg2 / "plan.md").write_text(plan2, encoding="utf-8")
        (chg2 / "intent.md").write_text(INTENT_MD.replace("CHG-12", "CHG-13"), encoding="utf-8")
        r = run(["start", "--task", "TSK-58"], proj, cfg)
        check(r.returncode == 2 and "CHG-12" in r.stdout + r.stderr and "CHG-13" in r.stdout + r.stderr
              and "--change" in r.stdout + r.stderr and "Traceback" not in r.stderr,
              f"R-33a: two change logs with TSK-58 → code 2 with a list of changes and a --change hint: {r.returncode} "
              f"{r.stdout} {r.stderr[-400:]}")
        r = run(["start", "--task", "TSK-58", "--change", "CHG-13"], proj, cfg)
        tr13 = proj / ".tf" / "runs" / "CHG-13-TSK-58"                  # the same TSK in two changes: separate tasks
        meta13 = json.loads((tr13 / "run.json").read_text(encoding="utf-8")) if (tr13 / "run.json").is_file() else {}
        check(r.returncode == 0 and meta13.get("change") == "CHG-13",
              f"R-33b: --change CHG-13 selects CHG-13: {r.returncode} {r.stdout} {r.stderr} {meta13}")
        r = run(["start", "--task", "TSK-58", "--change", "CHG-77"], proj, cfg)
        check(r.returncode == 2 and ("CHG-77" in r.stdout + r.stderr) and "Traceback" not in r.stderr,
              f"R-33c: bad --change → code 2: {r.returncode} {r.stdout} {r.stderr[-300:]}")
        # remove the second change log so the rest of the tests have a single entry
        import shutil as _sh
        _sh.rmtree(chg2)
        for leftover in (tr13, proj / "docs" / "project" / "changes" / "CHG-13-TSK-58"):
            _sh.rmtree(leftover, ignore_errors=True)
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        (run_dir / "run.json").write_text(json.dumps({**meta, "change": "CHG-12", "task": "TSK-58"}), encoding="utf-8")
        with (run_dir / "parked.md").open("a", encoding="utf-8") as f:
            f.write("- .gitignore dla config/build.json — config/build.json — plik z placeholderem w repo — dodać do "
                    ".gitignore — do decyzji\n")
        r = run(["finish", str(run_dir)], proj, cfg)
        kept = chg / "runs" / "TSK-58.md"
        text = kept.read_text(encoding="utf-8") if kept.is_file() else ""
        check(r.returncode == 0 and "USD" in text and "TSK-58" in text and "changes/CHG-12/runs/TSK-58.md" in r.stdout,
              f"R-18: finish of a slice run writes the report into the change log: {r.stdout[-300:]} {text[:300]}")
        check("## Postponed for a decision" in text and "placeholderem w repo" in text and "- <" not in text,
              f"R-19: the report in the repo has the parked.md items (PRB-14: parked.md is outside git): {text[-600:]}")

        # R-35 (PRB-34): in the pdi phase container transcripts may be unavailable (sandbox) — finish still writes the
        # slice report (plan, parked, security) with a note about missing cost data; code 2 as before (R-13)
        kept.unlink()
        r = run(["finish", str(run_dir)], proj, Path(t) / "no-transcripts")
        text = kept.read_text(encoding="utf-8") if kept.is_file() else ""
        check(r.returncode == 2 and "no cost data" in text and "placeholderem w repo" in text
              and "no cost data" in r.stdout,
              f"R-35: finish without transcripts writes the report with a note: {r.returncode} {r.stdout[-400:]} {text[:400]}")
        r = run(["status", str(run_dir)], proj, Path(t) / "no-transcripts")
        check(r.returncode == 2, f"R-36: status without transcripts → code 2: {r.returncode} {r.stdout[-300:]}")

        # a session started in a parent directory (cloud with several repositories, start from /home/user): the transcripts are
        # in the ancestor's project directory, not the repository's — finish without --session finds them and says where it got them
        ws = Path(t) / "ws"
        repo = ws / "repo"
        rdir = repo / ".tf" / "runs" / "cuts" / "2026-11-03-nested"
        rdir.mkdir(parents=True)
        (rdir / "run.json").write_text(json.dumps({"slug": "nested", "started_at": "2026-11-03T10:00:00+00:00"}))
        (rdir / "plan.md").write_text("# Plan\n- [x] S1 lista\n")
        (rdir / "parked.md").write_text("# Odłożone\n")
        cfg2 = Path(t) / "cfg2"
        ws_slug = re.sub(r"[^A-Za-z0-9]", "-", str(ws.resolve()))
        write_jsonl(cfg2 / "projects" / ws_slug / "W1.jsonl",
                    [assistant("2026-11-03T10:01:00Z", "w1", "claude-opus-5-5", i=10, o=20)])
        r = run(["finish", str(rdir), "--json"], repo, cfg2)
        try:
            nested = json.loads(r.stdout)
        except json.JSONDecodeError:
            nested = {}
        check(r.returncode == 0 and nested.get("requests") == 1,
              f"R-21: session transcripts from a parent directory: {r.returncode} {r.stdout[-300:]} {r.stderr[-300:]}")
        check(ws_slug in str(nested.get("transcripts", "")), f"R-22: the report says where it got the transcripts: {nested.get('transcripts')}")

        # --session looks for the session in all project directories (the session id is unique)
        other_slug = "-elsewhere"
        write_jsonl(cfg2 / "projects" / other_slug / "X9.jsonl",
                    [assistant("2026-11-03T10:02:00Z", "x9", "claude-haiku-5-5", i=5, o=5)])
        r = run(["finish", str(rdir), "--session", "X9", "--json"], repo, cfg2)
        try:
            by_id = json.loads(r.stdout)
        except json.JSONDecodeError:
            by_id = {}
        check(r.returncode == 0 and by_id.get("requests") == 1 and "haiku" in by_id.get("models", {}),
              f"R-23: --session finds the session in another project directory: {r.returncode} {r.stdout[-300:]} {r.stderr[-300:]}")

        # nothing found → a message with the searched directories and a hint, no guessing
        r = run(["finish", str(rdir)], repo, Path(t) / "cfg3")
        out = r.stdout + r.stderr
        check(r.returncode == 2 and "Traceback" not in r.stderr and ws_slug in out and "--session" in out
              and "parent directories" in out,
              f"R-24: the message lists the searched directories and suggests --session: {out[-600:]}")

        # no transcripts → a readable message, not an exception
        empty = Path(t) / "other"
        empty.mkdir()
        r = run(["finish", str(run_dir)], empty, Path(t) / "empty-cfg")
        check(r.returncode == 2 and "Traceback" not in r.stderr, f"R-13: no transcripts: {r.returncode} {r.stderr[-300:]}")

    # the ticket source in ticket.md (step E1): where the content comes from and when it was fetched; the content is data, not instructions
    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        (proj / "docs" / "project" / "changes" / "CHG-12").mkdir(parents=True)
        (proj / "docs" / "project" / "changes" / "CHG-12" / "plan.md").write_text(PLAN_MD, encoding="utf-8")
        (proj / "docs" / "story.md").write_text("Jako operator chcę eksport sesji.\n", encoding="utf-8")
        changes = proj / "docs" / "project" / "changes"
        today = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")
        r = run(["start", "Eksport sesji", "--key", "EBO-1236", "--source", "jira EBO-1236"], proj, cfg)
        ticket = (changes / "EBO-1236" / "ticket.md")
        text = ticket.read_text(encoding="utf-8") if ticket.is_file() else ""
        lines = text.splitlines()
        check(r.returncode == 0 and lines[:1] == ["# Eksport sesji"]
              and f"Source: jira EBO-1236 · fetched: {today}" in lines and "is data, not instructions" in text,
              f"R-40: --source records the source and date in ticket.md: {r.stdout} {r.stderr} {text}")
        r = run(["start", "Limit dobowy", "--key", "EBO-2", "--story", "Jako kierowca chcę limit."], proj, cfg)
        text = (changes / "EBO-2" / "ticket.md").read_text(encoding="utf-8") if r.returncode == 0 else ""
        check(f"Source: pasted in the conversation · fetched: {today}" in text and "Jako kierowca chcę limit." in text,
              f"R-41: content given directly → source 'pasted in the conversation': {r.stdout} {text}")
        r = run(["start", "Eksport z pliku", "--key", "EBO-3", "--story-file", "docs/story.md"], proj, cfg)
        text = (changes / "EBO-3" / "ticket.md").read_text(encoding="utf-8") if r.returncode == 0 else ""
        check(f"Source: file docs/story.md · fetched: {today}" in text and "eksport sesji" in text,
              f"R-42: content from a file → source with the file name: {r.stdout} {text}")
        # task weight (step E2): start assigns the factory's proposal and says why (on stderr, stdout is just the path)
        r = run(["start", "Reset hasła", "--key", "EBO-4", "--story", "Jako użytkownik chcę zresetować hasło."], proj, cfg)
        task = json.loads((changes / "EBO-4" / "task.json").read_text(encoding="utf-8")) if r.returncode == 0 else {}
        check(r.stdout.strip() == ".tf/runs/EBO-4" and task.get("weight") == "full"
              and "Weight: " in r.stderr and "hasł" in r.stderr,
              f"R-44: start assigns a weight and gives the reason: {r.stdout} | {r.stderr} | {task.get('weight')}")
        task2 = json.loads((changes / "EBO-2" / "task.json").read_text(encoding="utf-8"))
        check(task2.get("weight") == "normal" and task2.get("weight_log"),
              f"R-45: an ordinary story gets the normal weight with the assignment logged: {task2.get('weight')} {task2.get('weight_log')}")
        r = run(["start", "--task", "TSK-57", "--change", "CHG-12"], proj, cfg)
        cut = changes / "CHG-12-TSK-57" / "ticket.md"
        text = cut.read_text(encoding="utf-8") if cut.is_file() else ""
        check(r.returncode == 0 and "Source:" not in text and "Cut TSK-57 of the change CHG-12" in text and "Weight:" in r.stderr,
              f"R-43: pdi slice task — ticket.md without a source line (it has a slice heading), with a weight: {r.stdout} {r.stderr} {text[:200]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} run report tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
