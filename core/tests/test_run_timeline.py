#!/usr/bin/env python3
"""The run's timeline and the human's waits (skill tf): `run_state.py stage`/`step`/`done` stamp each transition in
run.json `timeline`, `run_report.py finish` prints a "Timeline" table (waits subtracted, shown apart; old runs without
stamps are tolerated), the `log_usage.py` hook times each AskUserQuestion question into the active run's `waits` (the
header only, never the answer), and `verify` hints at the narrowest command when the command names none of the slice's
files.
python3 .claude/tests/test_run_timeline.py"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "run_state.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL
REPORT = SCRIPT.with_name("run_report.py")
HOOK = ROOT / ".claude" / "hooks" / "log_usage.py"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'3 passed\')"'
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci kartą, then opłata "
        "wynosi 45 zł.\n\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")
PLAN = "# Plan\n\n- [ ] S1 — płatność kartą · criteria: AC-1 · files: pay.py\n"


def env(project: Path) -> dict:
    return {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
            "TF_DASHBOARD_OPEN": "0", "TF_DASHBOARD": "0"}


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True,
                          env=env(project), timeout=120)


def hook(project: Path, payload) -> subprocess.CompletedProcess:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(HOOK)], input=text, cwd=project, capture_output=True, text=True,
                          env=env(project), timeout=30)


def load_report():
    spec = importlib.util.spec_from_file_location("tf_run_report_tl", REPORT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ask(event: str, tid: str = "toolu_1", answer: str = "SECRET-ANSWER-TEXT") -> dict:
    q = [{"question": "Do you accept the plan?", "header": "Plan", "multiSelect": False,
          "options": [{"label": "Accept (Recommended)", "description": "go on"}, {"label": "Change", "description": "x"}]}]
    data = {"hook_event_name": event, "tool_name": "AskUserQuestion", "tool_use_id": tid, "session_id": "s1",
            "tool_input": {"questions": q}}
    if event != "PreToolUse":
        data["tool_input"]["answers"] = {"Do you accept the plan?": answer}
        data["tool_response"] = {"answers": {"Do you accept the plan?": answer}, "text": f"User answered: {answer}"}
    return data


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    rr = load_report()
    since = datetime(2026, 11, 25, 9, 0, tzinfo=timezone.utc)
    last = datetime(2026, 11, 25, 9, 30, tzinfo=timezone.utc)

    # T-1: the table from stamps — stage rows, slice rows with their steps, waits subtracted and shown apart
    meta = {"started_at": "2026-11-25T09:00:00+00:00",
            "timeline": [{"at": "2026-11-25T09:01:00+00:00", "stage": "intake"},
                         {"at": "2026-11-25T09:03:00+00:00", "stage": "spec"},
                         {"at": "2026-11-25T09:05:00+00:00", "stage": "plan"},
                         {"at": "2026-11-25T09:06:00+00:00", "stage": "needs"},
                         {"at": "2026-11-25T09:10:00+00:00", "slice": "S1", "step": "test", "state": "run"},
                         {"at": "2026-11-25T09:12:00+00:00", "slice": "S1", "step": "test", "state": "pass"},
                         {"at": "2026-11-25T09:15:00+00:00", "slice": "S1", "step": "verify", "state": "run"},
                         {"at": "2026-11-25T09:20:00+00:00", "slice": "S1", "step": "verify", "state": "pass"},
                         {"at": "2026-11-25T09:21:00+00:00", "slice": "S1", "step": "commit", "state": "pass"},
                         {"at": "2026-11-25T09:24:00+00:00", "slice": "PR", "step": "pr", "state": "run"},
                         {"at": "2026-11-25T09:28:00+00:00", "stage": "done"}],
            "waits": [{"from": "2026-11-25T09:06:00+00:00", "to": "2026-11-25T09:10:00+00:00", "needs": "plan"},
                      {"from": "2026-11-25T09:07:00+00:00", "to": "2026-11-25T09:09:00+00:00", "question": "Plan"},
                      {"from": "2026-11-25T09:22:00+00:00", "to": "2026-11-25T09:23:00+00:00", "question": "Commit"}]}
    rows = rr.timeline_rows(meta, since, last) or []
    by = {r["stage"]: r for r in rows}
    check([r["stage"] for r in rows] == ["start", "intake", "spec", "plan", "needs", "S1", "pr", "done"],
          f"T-1: rows in the run's order, start → intake → spec → plan → slices → pr → done: {rows}")
    check(by.get("start", {}).get("s") == 60 and by.get("intake", {}).get("s") == 120,
          f"T-1a: the start row lasts until the first stamp: {by.get('start')} {by.get('intake')}")
    check(by.get("needs", {}).get("wait") == 240 and by.get("needs", {}).get("s") == 0,
          f"T-1b: overlapping waits (needs and a question) count once: {by.get('needs')}")
    s1 = by.get("S1", {})
    check(s1.get("s") == 13 * 60 and s1.get("wait") == 60,
          f"T-1c: the slice's time without the commit question's minute, the minute shown apart: {s1}")
    steps = dict(s1.get("steps") or [])
    check(steps.get("test") == 120 and steps.get("code") == 180 and steps.get("verify") == 300
          and steps.get("scan") == 60 and steps.get("commit") == 120,
          f"T-1d: the slice's steps (a pass hands over to the next step): {s1.get('steps')}")
    md = "\n".join(rr.timeline_md(meta, since, last))
    check("## Timeline" in md and "| S1 |" in md and "test 2:00" in md and "verify 5:00" in md and md.count("\n|") <= 12,
          f"T-1e: a small markdown table: {md}")

    # T-2: an old run without stamps, and broken entries — no crash, one line
    old = rr.timeline_md({"started_at": "2026-11-25T09:00:00+00:00"}, since, last)
    check(len(old) <= 4 and any("no stage times" in ln for ln in old), f"T-2: an old run — one line: {old}")
    bad = {"timeline": [{"at": "nonsense", "stage": "plan"}, "x", 5, {"stage": "intake"}], "waits": "x"}
    check(any("no stage times" in ln for ln in rr.timeline_md(bad, since, last)),
          "T-2a: entries without a valid time are skipped")
    br = rr.time_breakdown(Path(tempfile.gettempdir()), Path(tempfile.gettempdir()) / "nope", meta, since, last)
    check(br.get("wait_s") == 5 * 60 and br.get("question_waits") == 2,
          f"T-2b: the time breakdown merges overlapping waits and counts the questions: {br}")

    # T-7: foreground subagents (the log_usage delegation log) — a part of the rest, by agent type, this run only
    with tempfile.TemporaryDirectory() as t:
        logs = Path(t) / ".tf" / "logs"
        logs.mkdir(parents=True)
        rows = [{"ts": "2026-11-25T09:12:00+00:00", "agent": "scope-reviewer", "duration_ms": 90000, "background": False},
                {"ts": "2026-11-25T09:20:00+00:00", "agent": "scope-reviewer", "duration_ms": 30000, "background": False},
                {"ts": "2026-11-25T09:05:00+00:00", "agent": "scout", "duration_ms": 60000, "background": False},
                {"ts": "2026-11-25T09:06:00+00:00", "agent": "mcp-runner", "duration_ms": 50000, "background": True},
                {"ts": "2026-11-24T09:06:00+00:00", "agent": "scout", "duration_ms": 60000, "background": False},
                {"ts": "2026-11-25T09:07:00+00:00", "agent": "scout", "duration_ms": "x", "background": False}]
        (logs / "delegation.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\nnot json\n", encoding="utf-8")
        br = rr.time_breakdown(Path(t), Path(t) / "nope", {}, since, last)
        check(br.get("agent_s") == 180 and br.get("agent_runs") == 3 and br.get("agents") == {"scope-reviewer": 120, "scout": 60},
              f"T-7: foreground subagents of this run are timed by type: {br}")
        md = rr.report_md("x", {"duration_s": 1800, "cost_usd": 0, "models": {}, "agents": {}, "requests": 1,
                                "model_ids": [], "plan": {"done": 0, "total": 0}, "parked": 0, "time": br})
        check("subagents (foreground, 3): 3 min 0 s" in md and "scope-reviewer 2:00" in md,
              f"T-7a: the report names the subagents' time: {md[-500:]}")

    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        p.mkdir()
        # T-3: the hook without a run records nothing and creates nothing; bad input never fails
        r = hook(p, ask("PreToolUse"))
        check(r.returncode == 0 and not (p / ".tf" / "runs").exists() and not r.stdout.strip(),
              f"T-3: no run — nothing recorded, exit 0, silent: {r.returncode} {r.stdout} {r.stderr}")
        for junk in ("", "{not json", "[1, 2]", json.dumps({"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion",
                                                             "tool_input": "x"})):
            r = hook(p, junk)
            check(r.returncode == 0 and not r.stdout.strip(), f"T-3a: junk input → exit 0: {junk!r} {r.stderr}")

        call(p, REPORT, "start", "Płatność kartą", "--key", "IMP-1", "--story", "Jako kierowca chcę zapłacić kartą.")
        d = p / ".tf" / "runs" / "IMP-1"
        doc = p / CHANGES / "IMP-1"
        run_json = d / "run.json"
        check(run_json.is_file(), "T-4: the run exists")

        # T-4: stage and step stamp the timeline
        call(p, SCRIPT, "stage", str(d), "intake")
        call(p, SCRIPT, "spec", str(d), "new")
        (doc / "spec.md").write_text(SPEC, encoding="utf-8")
        (doc / "plan.md").write_text(PLAN, encoding="utf-8")
        call(p, SCRIPT, "flag", str(d), "none", "--reason", "no flag, because the change is approved by a human in the plan")
        call(p, SCRIPT, "stage", str(d), "plan")
        call(p, SCRIPT, "mode", str(d), "normal")     # the human's mode: the delivery goes on after the plan
        call(p, SCRIPT, "approve", str(d))
        call(p, SCRIPT, "step", str(d), "S1", "R1", "test", "run")
        tl = json.loads(run_json.read_text(encoding="utf-8")).get("timeline") or []
        kinds = [e.get("stage") or f"{e.get('slice')} {e.get('step')} {e.get('state')}" for e in tl]
        check(kinds[:3] == ["intake", "spec", "plan"] and "S1 test run" in kinds and all(rr.parse_ts(e.get("at", "")) for e in tl),
              f"T-4a: stamps for intake, spec, plan and the slice step: {kinds}")

        # T-5: a question: the start and the end into waits, the header only, never the answer
        r1 = hook(p, ask("PreToolUse"))
        mid = json.loads(run_json.read_text(encoding="utf-8"))
        r2 = hook(p, ask("PostToolUse"))
        text = run_json.read_text(encoding="utf-8")
        after = json.loads(text)
        qw = [w for w in after.get("waits") or [] if w.get("question")]
        check(r1.returncode == 0 and r2.returncode == 0 and isinstance(mid.get("ask_open"), dict)
              and len(qw) == 1 and qw[0]["question"] == "Plan" and qw[0].get("from") and qw[0].get("to")
              and "ask_open" not in after, f"T-5: the question's wait recorded with its header: {after.get('waits')} {mid}")
        check("SECRET-ANSWER-TEXT" not in text and "Accept (Recommended)" not in text,
              "T-5a: neither the answer nor the options are stored")
        # a deferred question fires PreToolUse twice for the same call: the first start stays
        hook(p, ask("PreToolUse", tid="toolu_2"))
        first = json.loads(run_json.read_text(encoding="utf-8")).get("ask_open")
        hook(p, ask("PreToolUse", tid="toolu_2"))
        again = json.loads(run_json.read_text(encoding="utf-8")).get("ask_open")
        hook(p, ask("PostToolUseFailure", tid="toolu_2"))
        after2 = json.loads(run_json.read_text(encoding="utf-8"))
        check(first == again and len([w for w in after2.get("waits") or [] if w.get("question")]) == 2
              and "ask_open" not in after2, f"T-5b: a repeated PreToolUse keeps the start; a failure ends it: {after2}")
        r = hook(p, ask("PostToolUse", tid="toolu_9"))
        check(r.returncode == 0 and len([w for w in json.loads(run_json.read_text(encoding="utf-8")).get("waits") or []
                                         if w.get("question")]) == 2, "T-5c: an end without a start records nothing")
        # an unreadable run.json is left as it is, exit 0
        good = run_json.read_text(encoding="utf-8")
        run_json.write_text("{broken", encoding="utf-8")
        r = hook(p, ask("PreToolUse"))
        check(r.returncode == 0 and run_json.read_text(encoding="utf-8") == "{broken",
              f"T-5d: a broken run.json — untouched, exit 0: {r.stderr}")
        run_json.write_text(good, encoding="utf-8")
        # a finished run is not active: nothing recorded
        done = json.loads(good)
        done["stage"] = "done"
        run_json.write_text(json.dumps(done), encoding="utf-8")
        hook(p, ask("PreToolUse", tid="toolu_3"))
        check("ask_open" not in json.loads(run_json.read_text(encoding="utf-8")), "T-5e: a done run records no question")
        run_json.write_text(good, encoding="utf-8")

        # T-6: the verify hint — a command that names none of the slice's files
        (p / "pay.py").write_text("FEE = 45\n", encoding="utf-8")
        (p / "test_pay.py").write_text("def test_ac1_card_fee():  # AC-1\n    assert True\n", encoding="utf-8")
        r = call(p, SCRIPT, "verify", str(d), "S1", "--files", "pay.py,test_pay.py", "--command", OK)
        hint = [ln for ln in r.stdout.splitlines() if ln.startswith("ℹ") and "related" in ln]
        check(len(hint) == 1 and "narrowest" in hint[0], f"T-6: one ℹ hint about the narrowest command: {r.stdout}")
        r = call(p, SCRIPT, "verify", str(d), "S1", "--files", "pay.py,test_pay.py", "--command", f"{OK} test_pay.py",
                 "--force")
        check(not [ln for ln in r.stdout.splitlines() if ln.startswith("ℹ") and "narrowest" in ln],
              f"T-6a: a command with a slice file — no hint: {r.stdout}")
        r = call(p, SCRIPT, "verify", str(d), "S1", "--files", "pay.py,test_pay.py", "--command", f"{OK} {{files}}",
                 "--force")
        check(not [ln for ln in r.stdout.splitlines() if ln.startswith("ℹ") and "narrowest" in ln],
              f"T-6b: a command with a placeholder — no hint: {r.stdout}")
        check(rr.timeline_md(json.loads(run_json.read_text(encoding="utf-8")), since, last), "T-6c: the live run renders")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} run timeline tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
