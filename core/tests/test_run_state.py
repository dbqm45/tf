#!/usr/bin/env python3
"""Run state and dashboard tests (the tf skill, scripts/run_state.py).
python3 .claude/tests/test_run_state.py"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "run_state.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL
REPORT = SCRIPT.with_name("run_report.py")
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'8 passed\')"'
SPEC = ("# Spec\n\n## Acceptance criteria\n\n- AC-1: Given postój 12 godzin, when kierowca płaci, then opłata wynosi 45 zł.\n"
        "\n## Unchanged\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Out of scope\n\n- Abonamenty.\n")
RED = f'{sys.executable} -c "print(\'FAILED test_x\'); raise SystemExit(3)"'


def run(script, args, cwd, cfg, extra_env=None):
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "TF_DASHBOARD_OPEN": "0", **(extra_env or {})}
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True, env=env,
                          timeout=60)


def review_pass(run_dir: Path, slice_id: str) -> None:
    """State after a passed scope review of a slice (the `step … zakres pass` write), written straight into run.json."""
    f = run_dir / "run.json"
    meta = json.loads(f.read_text(encoding="utf-8"))
    meta["current"] = {"k": slice_id, "rounds": [{"test": "pass", "code": "pass", "verify": "pass", "scan": "pass",
                                                  "scope": "pass"}]}
    f.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def runs_json(html: str) -> list:
    m = re.search(r"const RUNS = (\[.*?\]);\n", html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</")) if m else []


def main() -> int:
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        r = run(REPORT, ["start", "Sortowanie listy", "--story", "Jako admin chcę sortować."], proj, cfg)
        d = next((proj / ".tf" / "runs").glob("T-*-sortowanie-listy"), None)
        check(r.returncode == 0 and d is not None, f"S-0: preparing the run: {r.stdout} {r.stderr}")
        check("Tip:" not in r.stderr, f"S-0b: a fresh session — no tip about /clear: {r.stderr}")
        proj2 = Path(t) / "proj2"
        proj2.mkdir()
        tdir = cfg / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(proj2.resolve()))
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "s1.jsonl").write_text('{"x": "run_report.py start A"}\n{"x": "run_report.py start B"}\n', encoding="utf-8")
        r2 = run(REPORT, ["start", "Druga w tej sesji", "--story", "x"], proj2, cfg)
        check("Tip:" in r2.stderr and "/clear" in r2.stderr,
              f"S-0c: the session already holds another task — the tip to start a fresh one: {r2.stderr}")
        if d is None:
            print("✗ no run directory")
            return 1
        doc = proj / CHANGES / d.name          # the task's persistent directory (step C4): plan, ticket and report
        (doc / "spec.md").write_text(SPEC, encoding="utf-8")      # a finished spec (step D1) — without it there is no plan
        run(SCRIPT, ["flag", str(d), "none", "--reason", "run-state test, nothing to hide"], proj, cfg)   # step D4
        dash = proj / ".tf" / "runs" / "dashboard.html"

        def one():
            html = dash.read_text(encoding="utf-8")
            rs = runs_json(html)
            return rs[0] if rs else {}

        # S-1: stage from plan.md — a template without slices is still intake
        r = run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        check(r.returncode == 0 and dash.is_file() and r.stdout.strip().startswith("file://"),
              f"S-1a: the dashboard builds the file and prints the address: {r.stdout} {r.stderr}")
        o = one()
        check(o.get("stage") == "intake" and o.get("slices") == [] and o.get("title") == "Sortowanie listy",
              f"S-1b: without a plan the intake stage: {o.get('stage')} {o.get('slices')}")

        # S-2: plan with slices → plan stage, then ticking → slices
        (doc / "plan.md").write_text("# Plan\n- [ ] S1 — sortowanie rosnące · criteria: t\n- [ ] S2 — malejące · criteria: t\n"
                                   "- [ ] S3 — po dacie · criteria: t\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        o = one()
        check(o.get("stage") == "plan" and [s["id"] for s in o["slices"]] == ["S1", "S2", "S3"],
              f"S-2a: plan with slices → plan stage: {o.get('stage')}")
        (proj / "sort.py").write_text("ASC = True\n", encoding="utf-8")     # a ticked slice has evidence (step C4)
        run(SCRIPT, ["verify", str(d), "S1", "--files", "sort.py", "--command", OK], proj, cfg)
        (doc / "plan.md").write_text("# Plan\n- [x] S1 — sortowanie rosnące · criteria: t\n- [ ] S2 — malejące · criteria: t\n"
                                   "- [ ] S3 — po dacie · criteria: t\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        o = one()
        check(o.get("stage") == "slices" and [s["state"] for s in o["slices"]] == ["done", "cur", "todo"],
              f"S-2b: ticked S1 → slices, S2 current: {o.get('stage')} {[s['state'] for s in o['slices']]}")

        # S-3: step records rounds; earlier stages get pass, a new round after a failed gate
        r = run(SCRIPT, ["step", str(d), "S2", "R1", "verify", "fail"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and meta["current"]["rounds"][0] == {"test": "pass", "code": "pass", "verify": "fail",
                                                                  "scan": "todo", "scope": "todo"},
              f"S-3a: R1 verify fail, test and code pass by default: {r.stdout} {r.stderr} {meta.get('current')}")
        run(SCRIPT, ["step", str(d), "S2", "R2", "code", "run"], proj, cfg)
        run(SCRIPT, ["step", str(d), "S2", "R2", "scan", "run"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        r2 = meta["current"]["rounds"][1]
        check(len(meta["current"]["rounds"]) == 2 and r2["test"] == "pass" and r2["code"] == "pass"
              and r2["verify"] == "pass" and r2["scan"] == "run" and r2["scope"] == "todo",
              f"S-3b: R2 counted from the start, verify before scan = pass: {r2}")
        check(meta.get("stage") == "slices" and "updated_at" in meta, f"S-3c: step ustawia stage slices: {meta.get('stage')}")
        o = one()
        check(o.get("cur", {}).get("k") == "S2" and len(o["cur"]["rounds"]) == 2
              and o["cur"]["rounds"][0]["verify"] == "fail",
              f"S-3d: dashboard after step (no manual refresh): {o.get('cur')}")

        # S-4: a new slice starts from R1
        run(SCRIPT, ["step", str(d), "S3", "R1", "test", "run"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(meta["current"]["k"] == "S3" and len(meta["current"]["rounds"]) == 1,
              f"S-4: a new slice resets the rounds: {meta['current']}")

        # S-5: invalid input → code 2 and a message, run.json unchanged
        before = (d / "run.json").read_text(encoding="utf-8")
        bad = [["step", str(d), "S2", "R1", "verify", "zielony"], ["step", str(d), "S2", "R1", "lint", "run"],
               ["step", str(d), "S2", "verify", "run"], ["stage", str(d), "needs"], ["stage", str(d), "nie-ma"],
               ["stage", str(d), "slices", "--needs", "stop"]]
        codes = [run(SCRIPT, a, proj, cfg).returncode for a in bad]
        check(all(c == 2 for c in codes)
              and (d / "run.json").read_text(encoding="utf-8") == before,
              f"S-5: invalid input rejected without a write: {codes}")

        # S-6: STOP — needs stage with a reason; current slice = fail, STOP file in the panel
        (d / "security" / "S2" / "proba-2").mkdir(parents=True)
        (d / "security" / "S2" / "proba-2" / "summary.md").write_text("## Security\nVerdict: FAIL\n", encoding="utf-8")
        run(SCRIPT, ["step", str(d), "S2", "R2", "scan", "fail"], proj, cfg)
        r = run(SCRIPT, ["stage", str(d), "needs", "--needs", "stop", "--code", "scan", "--reason", "Scan red after 2 attempts (S2)."],
                proj, cfg)
        o = one()
        names = [i["name"] for g in o.get("files", []) for i in g["items"]]
        check(r.returncode == 0 and o.get("stage") == "needs" and o.get("needs") == "stop"
              and "red" in (o.get("stopText") or "") and "STOP" in names
              and "security/S2/proba-2/summary.md" in names,
              f"S-6a: STOP with a reason and the files in the panel: {o.get('stage')} {o.get('needs')} {names}")
        check([s["state"] for s in o["slices"]][1] == "fail", f"S-6b: slice S2 in STOP = fail: {o['slices']}")
        # after the human's decision the next step resumes the run
        run(SCRIPT, ["step", str(d), "S2", "R3", "test", "run"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(meta.get("stage") == "slices" and "needs" not in meta and "stop_text" not in meta
              and len(meta["current"]["rounds"]) == 3,
              f"S-6c: step after STOP returns to slices and clears the reason: {meta.get('stage')}")

        # S-7: PR i koniec
        run(SCRIPT, ["step", str(d), "PR", "plan_drift", "pass"], proj, cfg)
        o = one()
        check(o.get("stage") == "pr" and o.get("prSteps") == {"drift": "pass", "pr": "todo"},
              f"S-7a: plan_drift → pr stage: {o.get('stage')} {o.get('prSteps')}")
        run(SCRIPT, ["stage", str(d), "done", "--pr", "41", "--auto", "--effort", "high"], proj, cfg)
        (doc / "report.md").write_text("# Raport\nok\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        o = one()
        check(o.get("stage") == "done" and o.get("pr") == 41 and o.get("auto") is True and o.get("effort") == "high"
              and any(i["name"] == "report.md" for g in o["files"] for i in g["items"]),
              f"S-7b: done z PR, auto, effort i raportem: {o.get('stage')} {o.get('pr')}")

        # S-7c: the visual check (screenshots in screens/) goes to the dashboard data; a run without screens has no block
        check("visual" not in one(), f"S-7c: a run without screens/ has no visual data: {one().get('visual')}")
        scr = d / "screens"
        for label, files in (("before", ("index@1280x800.png", "login@1280x800.png")),
                             ("after", ("index@1280x800.png", "login@1280x800.png"))):
            (scr / label).mkdir(parents=True)
            for f in files:
                (scr / label / f).write_bytes(b"\x89PNG\r\n\x1a\n" + label.encode() + (b"x" if f.startswith("login") and label == "after" else b""))
            (scr / label / "index.json").write_text(json.dumps({"label": label, "shots": [
                {"route": "/" if f.startswith("index") else "/login", "viewport": "1280x800", "file": f}
                for f in files]}), encoding="utf-8")
        (scr / "compare.md").write_text("# Visual comparison\n\n| route | viewport | result | before | after |\n|---|---|---|---|---|\n"
                                        "| / | 1280x800 | changed | screens/before/index@1280x800.png | screens/after/index@1280x800.png |\n"
                                        "| /login | 1280x800 | identical | screens/before/login@1280x800.png | screens/after/login@1280x800.png |\n",
                                        encoding="utf-8")
        (scr / "check.md").write_text("# Visual check\n\n- AC-1 · / @1280x800 — the heading is blue — **matches**\n"
                                      "- AC-2 · /login @1280x800 — the button is missing — **does not match**\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        v = one().get("visual") or {}
        items = {(i["route"], i["viewport"]): i for i in v.get("items", [])}
        check(v.get("state") == "done" and v.get("counts", {}).get("changed") == 1 and v.get("mismatches") == 1
              and items.get(("/", "1280x800"), {}).get("verdict") == "matches"
              and items.get(("/login", "1280x800"), {}).get("verdict") == "does not match"
              and items.get(("/", "1280x800"), {}).get("status") == "changed",
              f"S-7d: visual data: totals, status and verdict per screen: {v}")
        html = dash.read_text(encoding="utf-8")
        check(f"{d.name}/screens/before/index@1280x800.png" in html and f"{d.name}/screens/after/login@1280x800.png" in html
              and ".." not in " ".join(i["before"] for i in v.get("items", [])),
              "S-7e: the page carries relative image paths inside the runs directory")
        r = run(SCRIPT, ["stage", str(d), "done", "--no-visual"], proj, cfg)
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and meta.get("visual") == "off" and "visual" not in one(),
              f"S-7g: --no-visual is recorded and removes the dashboard block: {r.stdout}{r.stderr}")
        meta.pop("visual", None)
        (d / "run.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        (scr / "check.md").write_text("Skipped: no browser here\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        v = one().get("visual") or {}
        check(v.get("state") == "skipped" and v.get("reason") == "no browser here", f"S-7f: a skipped visual check: {v}")
        shutil.rmtree(scr)

        # S-8: cost from transcripts, remembered in run.json (dashboard without --no-cost); missing transcripts do no harm
        r = run(SCRIPT, ["dashboard"], proj, cfg)
        check(r.returncode == 0, f"S-8a: dashboard without transcripts works: {r.stdout} {r.stderr}")
        started = json.loads((d / "run.json").read_text(encoding="utf-8"))["started_at"]
        slug = re.sub(r"[^A-Za-z0-9]", "-", str(proj.resolve()))
        sess = cfg / "projects" / slug / "S1.jsonl"
        sess.parent.mkdir(parents=True, exist_ok=True)
        ts = started.replace("+00:00", "Z")[:19] + "Z"
        year = int(ts[:4]) + 1                       # reply after the start, regardless of the clock
        later = f"{year}{ts[4:]}"
        sess.write_text(json.dumps({"type": "assistant", "timestamp": later, "message": {
            "id": "m1", "model": "claude-sonnet-5-5", "usage": {"input_tokens": 1000, "output_tokens": 500}}}) + "\n",
                        encoding="utf-8")
        (d / "run.json").write_text(json.dumps({**json.loads((d / "run.json").read_text(encoding="utf-8")),
                                                "stage": "slices"}, ensure_ascii=False), encoding="utf-8")
        run(SCRIPT, ["dashboard"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        o = one()
        check(isinstance(meta.get("usage"), dict) and "sonnet" in meta["usage"]["models"]
              and o.get("models") == ["sonnet"] and o.get("cost") is not None,
              f"S-8b: cost and models from transcripts saved in run.json: {meta.get('usage')}")
        check((meta["usage"].get("tokens") or {}).get("total") == 1500 and (o.get("tokens") or {}).get("output") == 500
              and o.get("min") is not None,
              f"S-8b2: tokens (total, per kind) and time in run.json and the dashboard: {meta.get('usage')} {o.get('tokens')}")
        html = dash.read_text(encoding="utf-8")
        check('class="tok"' in html and "fmtTok" in html, "S-8b3: the dashboard template shows tokens next to cost and time")
        run(SCRIPT, ["step", str(d), "S2", "R1", "test", "run"], proj, cfg)   # refresh without computing cost
        check(one().get("cost") == o.get("cost"), "S-8c: a refresh after step keeps the remembered cost")

        # S-9: HTML safety — file content with </script> does not escape the data block
        (doc / "ticket.md").write_text("# s\n</script><b>x</b>\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        html = dash.read_text(encoding="utf-8")
        check(html.count("</script>") == 1 and "</script><b>" not in html,
              f"S-9: </script> in file content does not break the page: {html.count('</script>')}")

    # S-10: run start builds the dashboard (on by default), and options in .claude/tf.json and variables turn it off
    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        dash = proj / ".tf" / "runs" / "dashboard.html"
        r = run(REPORT, ["start", "Pierwsza historyjka", "--story", "x"], proj, cfg)
        check(r.returncode == 0 and dash.is_file() and "Dashboard: file://" in r.stderr
              and r.stdout.strip().startswith(".tf/runs/T-"),
              f"S-10a: start builds the dashboard, the address on stderr, stdout unchanged: {r.stdout!r} {r.stderr!r}")
        dash.unlink()
        (proj / ".claude").mkdir()
        (proj / ".claude" / "tf.json").write_text('{"dashboard": false}', encoding="utf-8")
        r = run(REPORT, ["start", "Druga historyjka", "--story", "x"], proj, cfg)
        check(r.returncode == 0 and not dash.exists() and "Dashboard" not in r.stderr,
              f"S-10b: {{\"dashboard\": false}} — start builds nothing: {r.stderr!r}")
        (proj / ".claude" / "tf.json").write_text('{"dashboard_open": false}', encoding="utf-8")
        r = run(REPORT, ["start", "Trzecia historyjka", "--story", "x"], proj, cfg)
        check(dash.is_file(), "S-10c: dashboard_open=false — it builds but does not open (the file exists)")
        dash.unlink()
        (proj / ".claude" / "tf.json").unlink()
        # S-10c2: opening — no browser is a reason in a message, not silence and not an exception
        sys.path.insert(0, str(SCRIPT.parent))
        import run_state as rs
        real_open, real_name = rs.webbrowser.open, rs.os.name
        try:
            rs.webbrowser.open = lambda uri: False
            why = rs.open_file(proj / "x.html") if os.name != "nt" and sys.platform != "darwin" else "skip"
            check(bool(why), f"S-10c2: webbrowser without a browser → the reason: {why!r}")
            rs.webbrowser.open = lambda uri: (_ for _ in ()).throw(OSError("boom"))
            why = rs.open_file(proj / "x.html") if os.name != "nt" and sys.platform != "darwin" else "boom"
            check("boom" in why, f"S-10c2: an exception → the reason: {why!r}")
        finally:
            rs.webbrowser.open, rs.os.name = real_open, real_name
        r = run(REPORT, ["start", "Czwarta historyjka", "--story", "x"], proj, cfg, {"TF_DASHBOARD": "0"})
        check(r.returncode == 0 and not dash.exists(), "S-10d: TF_DASHBOARD=0 disables it without a file")
        # corrupt options file → defaults (enabled), the run does not crash
        (proj / ".claude" / "tf.json").write_text("{nie json", encoding="utf-8")
        r = run(REPORT, ["start", "Piata historyjka", "--story", "x"], proj, cfg)
        check(r.returncode == 0 and dash.is_file(), f"S-10e: corrupt tf.json → default options: {r.stderr!r}")

    # one action per command: ticking a slice and parking an item via the script (no sed, >> or heredoc in the shell)
    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        run(REPORT, ["start", "Limit dobowy", "--story", "Jako operator chcę limit."], proj, cfg)
        d = next((proj / ".tf" / "runs").glob("T-*-limit-dobowy"), None)
        run(SCRIPT, ["stage", str(d), "intake", "--auto"], proj, cfg)     # an unattended run: a plan without approval (step E3)
        doc = proj / CHANGES / d.name
        plan = doc / "plan.md"
        head = plan.read_text(encoding="utf-8")
        plan.write_text(head + "- [ ] S1 — limit 45 zł · criteria: AC1 · files: fees.py\n"
                               "- [ ] S2 — druga doba · criteria: AC3 · files: fees.py\n", encoding="utf-8")
        (proj / "fees.py").write_text("LIMIT = 45\n", encoding="utf-8")

        def task():
            return json.loads((doc / "task.json").read_text(encoding="utf-8"))

        # spec before the plan (step D1): the template is created only on the `spec <dir> new` command (after an early
        # STOP no empty file is left in the repository); without spec.md or with an unfilled one there is no plan stage
        check(not (doc / "spec.md").exists(), "P-0a: start does not create spec.md")
        r = run(SCRIPT, ["stage", str(d), "plan"], proj, cfg)
        check(r.returncode == 2 and "spec" in r.stdout and " new" in r.stdout and task().get("stage") == "intake",
              f"P-0b: the plan stage rejected when there is no spec yet: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["spec", str(d), "new"], proj, cfg)
        check(r.returncode == 0 and (doc / "spec.md").is_file(), f"P-0c: spec new creates the template: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["spec", str(d)], proj, cfg)
        check(r.returncode == 1 and "SPEC-007" in r.stdout, f"P-1a: spec on the template → code 1 with the rule: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["stage", str(d), "plan"], proj, cfg)
        check(r.returncode == 2 and json.loads((d / "run.json").read_text(encoding="utf-8")).get("stage") != "plan"
              and task().get("stage") == "intake" and "spec" in r.stdout,
              f"P-1b: the plan stage rejected without a finished spec: {r.returncode} {r.stdout}")
        (doc / "spec.md").write_text(SPEC, encoding="utf-8")
        r = run(SCRIPT, ["spec", str(d)], proj, cfg)
        check(r.returncode == 0 and "AC-1" in r.stdout, f"P-2: finished spec → code 0: {r.returncode} {r.stdout}{r.stderr}")

        # evidence before ticking (step C4): tick passes only for a slice verified by `verify`
        r = run(SCRIPT, ["tick", str(d), "S1"], proj, cfg)
        check(r.returncode != 0 and "verify" in r.stdout + r.stderr and plan.read_text(encoding="utf-8").count("[x]") == 0,
              f"V-1: tick without evidence rejected, plan unchanged: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["verify", str(d), "S1", "--files", "fees.py", "--command", RED], proj, cfg)
        check(r.returncode == 1 and "FAILED test_x" in r.stdout, f"V-2: verify with a red command → code 1 and output: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["verify", str(d), "S1", "--files", "fees.py", "--command", OK], proj, cfg)
        check(r.returncode == 0 and (doc / "evidence" / "S1-2.json").is_file(),
              f"V-3: verify saves evidence in the task directory: {r.returncode} {r.stdout}{r.stderr}")
        review_pass(d, "S1")   # scope review result before tick (without changing the stage that later tests check)
        r = run(SCRIPT, ["tick", str(d), "S1"], proj, cfg)
        text = plan.read_text(encoding="utf-8")
        check(r.returncode == 0 and "- [x] S1 — limit 45 zł" in text and "- [ ] S2 — druga doba" in text
              and text.startswith(head), f"T-1: tick ticks only the given slice, the rest of the file unchanged: {r.stdout}{r.stderr}{text[-200:]}")
        r = run(SCRIPT, ["tick", str(d), "S1"], proj, cfg)
        check(r.returncode == 0 and plan.read_text(encoding="utf-8") == text, f"T-2: a repeated tick changes nothing: {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["tick", str(d), "S7"], proj, cfg)
        check(r.returncode != 0 and "S7" in (r.stdout + r.stderr) and plan.read_text(encoding="utf-8") == text,
              f"T-3: unknown slice → error with its name, file unchanged: {r.returncode} {r.stdout}{r.stderr}")
        parked = d / "parked.md"
        before = parked.read_text(encoding="utf-8")
        r = run(SCRIPT, ["park", str(d), "Strefy czasowe w znacznikach — do decyzji"], proj, cfg)
        run(SCRIPT, ["park", str(d), "Pliki > 50 MB"], proj, cfg)
        after = parked.read_text(encoding="utf-8")
        check(r.returncode == 0 and after.startswith(before.rstrip("\n")) and after.rstrip().endswith("- Pliki > 50 MB")
              and "- Strefy czasowe w znacznikach — do decyzji\n" in after,
              f"T-4: park appends items at the end of parked.md, each on its own line: {after[-200:]}")
        r = run(SCRIPT, ["park", str(d), "  "], proj, cfg)
        check(r.returncode != 0 and parked.read_text(encoding="utf-8") == after, f"T-5: empty item → error, file unchanged: {r.returncode}")
        rep = run(REPORT, ["status", str(d)], proj, cfg)
        check("2" in rep.stdout or "postponed" in rep.stdout.lower(), f"T-6: the run report sees the postponed items: {rep.stdout[-300:]}")

        # criteria trace (step D3): outside a git repository the script says outright that it cannot compute the trace
        r = run(SCRIPT, ["trace", str(d)], proj, cfg)
        check(r.returncode == 2 and "git" in r.stdout, f"TRC-1: trace outside git → code 2 with an explanation: {r.returncode} {r.stdout}{r.stderr}")

        # changing a file after the evidence invalidates it; the run stage goes to task.json; to PR only with verified slices
        run(SCRIPT, ["verify", str(d), "S2", "--files", "fees.py", "--command", OK], proj, cfg)
        (proj / "fees.py").write_text("LIMIT = 50\n", encoding="utf-8")
        r = run(SCRIPT, ["tick", str(d), "S2"], proj, cfg)
        check(r.returncode != 0 and "- [ ] S2" in plan.read_text(encoding="utf-8"),
              f"V-4: file changed after the evidence → tick rejected: {r.returncode} {r.stdout}{r.stderr}")
        run(SCRIPT, ["stage", str(d), "plan"], proj, cfg)
        check(task().get("stage") == "plan", f"V-5a: stage plan trafia do task.json: {task().get('stage')}")
        inputs = sorted((task().get("artifacts", {}).get("plan.md", {}).get("inputs") or {}))
        check(inputs == ["spec.md", "ticket.md"], f"P-3: stage plan records what the plan was built from: {inputs}")
        run(SCRIPT, ["step", str(d), "S2", "R1", "test", "run"], proj, cfg)
        check(task().get("stage") == "implementation", f"V-5b: first step → implementation: {task().get('stage')}")
        r = run(SCRIPT, ["stage", str(d), "pr"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(r.returncode == 2 and meta.get("stage") != "pr" and task().get("stage") == "implementation" and "S2" in r.stdout,
              f"V-6a: pr stage rejected with an unverified slice: {r.returncode} {r.stdout} {meta.get('stage')}")
        r = run(SCRIPT, ["step", str(d), "PR", "plan_drift", "pass"], proj, cfg)
        check(r.returncode == 2 and json.loads((d / "run.json").read_text(encoding="utf-8")).get("stage") != "pr",
              f"V-6b: step PR also does not enter the pr stage without evidence: {r.returncode} {r.stdout}")
        for k in ("S1", "S2"):
            run(SCRIPT, ["verify", str(d), k, "--files", "fees.py", "--command", OK], proj, cfg)
        # feature flag (step D4): a task with a spec does not enter the pr stage without a flag or a reason for its absence
        r = run(SCRIPT, ["stage", str(d), "pr"], proj, cfg)
        check(r.returncode == 2 and "flag" in r.stdout, f"FL-1: the pr stage rejected without a flag decision: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["flag", str(d), "mode"], proj, cfg)
        check(r.returncode == 0 and r.stdout.strip().startswith("auto"), f"FL-0a: the flag mode is auto by default: {r.stdout}{r.stderr}")
        (proj / ".tf" / "config").mkdir(parents=True, exist_ok=True)
        (proj / ".tf" / "config" / "config.yaml").write_text("feature_flags:\n  auto: false\n", encoding="utf-8")
        r = run(SCRIPT, ["flag", str(d), "mode"], proj, cfg)
        check(r.returncode == 0 and r.stdout.strip().startswith("manual"), f"FL-0b: feature_flags.auto: false → manual mode: {r.stdout}{r.stderr}")
        (proj / ".tf" / "config" / "config.yaml").unlink()
        r = run(SCRIPT, ["flag", str(d), "none"], proj, cfg)
        check(r.returncode == 2, f"FL-2: “bez flagi” requires a reason: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["flag", str(d), "set", "limit_dobowy", "--remove-by", "2027-01-31"], proj, cfg)
        check(r.returncode == 0 and task().get("flag", {}).get("key") == "limit_dobowy",
              f"FL-3: flag set via the run script reaches task.json: {r.returncode} {r.stdout}{r.stderr}")
        # spec change after the plan: the plan is stale until the loop goes through the plan stage again
        (doc / "spec.md").write_text(SPEC.replace("45 zł", "50 zł"), encoding="utf-8")
        r = run(SCRIPT, ["stage", str(d), "pr"], proj, cfg)
        check(r.returncode == 2 and "plan.md" in r.stdout and task().get("stage") == "implementation",
              f"P-4a: spec changed after the plan → pr stage rejected (plan stale): {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d), "plan"], proj, cfg)
        check(r.returncode == 0, f"P-4b: a repeated plan stage refreshes the plan inputs: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d), "pr"], proj, cfg)
        check(r.returncode == 0 and task().get("stage") == "pr"
              and json.loads((d / "run.json").read_text(encoding="utf-8")).get("stage") == "pr",
              f"V-6c: after the evidence the pr stage passes in run.json and task.json: {r.returncode} {r.stdout} {task().get('stage')}")

        # old run (.tf/runs/cuts/<date>-<slug>/, no task) works as before and is on the same page
        old = proj / ".tf" / "runs" / "cuts" / "2026-10-01-stary"
        old.mkdir(parents=True)
        (old / "run.json").write_text(json.dumps({"slug": "stary", "title": "Stary przebieg",
                                                  "started_at": "2026-10-01T10:00:00+00:00"}), encoding="utf-8")
        (old / "plan.md").write_text("# Plan\n- [ ] S1 — stara lista · files: a.py\n", encoding="utf-8")
        r = run(SCRIPT, ["tick", str(old), "S1"], proj, cfg)
        check(r.returncode == 0 and "- [x] S1" in (old / "plan.md").read_text(encoding="utf-8"),
              f"V-7a: old run — tick without evidence as before: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["trace", str(old)], proj, cfg)
        check(r.returncode == 2 and "old layout" in r.stdout, f"TRC-2: trace in an old run → code 2: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["verify", str(old), "S1", "--files", "fees.py", "--command", OK], proj, cfg)
        check(r.returncode == 2 and not (old / "evidence").exists(),
              f"V-7b: verify in an old run → code 2 with an explanation: {r.returncode} {r.stdout}")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        rs = runs_json((proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8"))
        slugs = {x.get("slug") for x in rs}
        new = next((x for x in rs if x.get("slug") != "stary"), {})
        check("stary" in slugs and len(rs) == 2 and [s["id"] for s in new.get("slices", [])] == ["S1", "S2"]
              and any(i["name"] == "ticket.md" for g in new.get("files", []) for i in g["items"]),
              f"V-8: an old and a new run on one page, the new one with a plan and ticket.md: {slugs} {new.get('slices')}")

        # task preview (step C5): task stage, persistent and working directory, evidence, a separate state for a slice without evidence
        key = d.name
        grp = {g["grp"]: [i["name"] for i in g["items"]] for g in new.get("files", [])}
        durable = next((v for k, v in grp.items() if f"docs/project/changes/{key}" in k), [])
        working = next((v for k, v in grp.items() if f".tf/runs/{key}" in k), [])
        check(new.get("dir") == f".tf/runs/{key}" and new.get("taskDir") == f"docs/project/changes/{key}"
              and new.get("taskStage") == "pr" and new.get("key") == key,
              f"D-1: the card knows the directories and the task stage: {new.get('dir')} {new.get('taskDir')} {new.get('taskStage')}")
        check("ticket.md" in durable and "plan.md" in durable and "parked.md" in working,
              f"D-2: the files panel splits files into persistent and working directory: {grp}")
        check(any(n.startswith("evidence/S1-") for v in grp.values() for n in v),
              f"D-3: the slice's latest evidence in the files panel: {grp}")
        old_o = next((x for x in rs if x.get("slug") == "stary"), {})
        check(old_o.get("dir") == ".tf/runs/cuts/2026-10-01-stary" and not old_o.get("taskDir"),
              f"D-4: an old run points to its own directory: {old_o.get('dir')}")
        review_pass(d, "S2")
        run(SCRIPT, ["tick", str(d), "S2"], proj, cfg)
        (proj / "fees.py").write_text("LIMIT = 55\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        html = (proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8")
        new = next((x for x in runs_json(html) if x.get("slug") != "stary"), {})
        st = {s["id"]: s["state"] for s in new.get("slices", [])}
        check(st == {"S1": "stale", "S2": "stale"} and all(s.get("proof") == "unverified" for s in new["slices"]),
              f"D-5: a ticked slice with a changed file has state stale: {new.get('slices')}")
        check(".chip.stale" in html and "r.slices.map" in html and "r.dir" in html,
              "D-6: the template draws the slice bar, stale state and directory from run data")

        # a task created by `tf task` (no run, e.g. a fresh clone) also has a card
        ts = ROOT / ".tf" / "factory" / "task_state.py"
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj)}
        subprocess.run([sys.executable, str(ts), "start", "PROJ-7", "--title", "Eksport faktur"], cwd=proj, env=env,
                       capture_output=True, text=True, timeout=60)
        subprocess.run([sys.executable, str(ts), "verify", "PROJ-7", "S1", "--files", "fees.py", "--command", OK],
                       cwd=proj, env=env, capture_output=True, text=True, timeout=60)
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        rs = runs_json((proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8"))
        bare = next((x for x in rs if x.get("key") == "PROJ-7"), {})
        check(len(rs) == 3 and bare.get("title") == "Eksport faktur" and bare.get("stage") == "intake"
              and bare.get("taskStage") == "intake" and [(s["id"], s["state"]) for s in bare.get("slices", [])] == [("S1", "done")],
              f"D-7: a task without a run has a card with stage and slices: {len(rs)} {bare.get('stage')} {bare.get('slices')}")

    # task weight in the loop (step E2): the factory assigns a weight and says why; the script enforces the effects
    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        ts = ROOT / ".tf" / "factory" / "task_state.py"
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj)}
        run(REPORT, ["start", "Reset hasła", "--key", "LOG-1", "--story",
                     "Jako użytkownik chcę zresetować hasło linkiem z maila. AC1: link ważny 30 minut."], proj, cfg)
        d = proj / ".tf" / "runs" / "LOG-1"
        r = run(SCRIPT, ["weight", str(d)], proj, cfg)
        data = json.loads((proj / CHANGES / "LOG-1" / "task.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and data.get("weight") == "full" and "full" in r.stdout and "hasł" in r.stdout
              and "human" in r.stdout,
              f"W-1: run_state weight assigns full weight, gives the reason and effect: {r.returncode} {r.stdout}{r.stderr}")
        (proj / CHANGES / "LOG-1" / "spec.md").write_text(SPEC, encoding="utf-8")
        (proj / CHANGES / "LOG-1" / "plan.md").write_text("# Plan\n- [ ] S1 — reset · files: reset.py\n", encoding="utf-8")
        r = run(SCRIPT, ["stage", str(d), "plan", "--auto"], proj, cfg)
        check(r.returncode == 0, f"W-2: a plan for a full-weight task can be saved: {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["step", str(d), "S1", "R1", "test", "run"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(r.returncode == 2 and "approve LOG-1 plan.md" in r.stdout and "STOP" in r.stdout
              and meta.get("stage") == "plan",
              f"W-3: full weight with --auto — slice loop rejected with an explanation, stage unchanged: {r.returncode} {r.stdout}")
        subprocess.run([sys.executable, str(ts), "approve", "LOG-1", "plan.md", "--by", "human:anna"], cwd=proj, env=env,
                       capture_output=True, text=True, timeout=60)
        r = run(SCRIPT, ["step", str(d), "S1", "R1", "test", "run"], proj, cfg)
        check(r.returncode == 0, f"W-4: after the human approves the plan the loop starts: {r.stdout}{r.stderr}")

        run(REPORT, ["start", "Literówka w README", "--key", "TYP-1", "--story",
                     "Popraw literówkę w README: instlacja na instalacja."], proj, cfg)
        d2 = proj / ".tf" / "runs" / "TYP-1"
        r = run(SCRIPT, ["weight", str(d2)], proj, cfg)
        check(r.returncode == 0 and "light" in r.stdout and "no spec.md" in r.stdout,
              f"W-5: typo → light weight with effect: {r.stdout}{r.stderr}")
        (proj / CHANGES / "TYP-1" / "plan.md").write_text("# Plan\n- [ ] S1 — literówka · files: README.md\n", encoding="utf-8")
        r = run(SCRIPT, ["stage", str(d2), "plan"], proj, cfg)
        check(r.returncode == 0 and not (proj / CHANGES / "TYP-1" / "spec.md").exists(),
              f"W-6: light weight — the run's plan stage without spec.md: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["weight", str(d2), "--set", "normal"], proj, cfg)
        r2 = run(SCRIPT, ["stage", str(d2), "plan"], proj, cfg)
        check(r.returncode == 0 and r2.returncode == 2 and "spec" in r2.stdout,
              f"W-7: after raising the weight to normal the spec is required again: {r.stdout} | {r2.returncode} {r2.stdout}")
        r = run(SCRIPT, ["weight", str(d2), "--set", "light"], proj, cfg)
        check(r.returncode != 0 and "human:" in r.stdout, f"W-8: lowering the weight from the loop → refusal: {r.returncode} {r.stdout}")
        run(REPORT, ["start", "Limit dobowy", "--key", "REG-1", "--story",
                     "Jako operator chcę podnieść limit dobowy opłaty z 40 zł do 45 zł. AC1: 12 h = 45 zł."], proj, cfg)
        d3 = proj / ".tf" / "runs" / "REG-1"
        (proj / CHANGES / "REG-1" / "spec.md").write_text(SPEC, encoding="utf-8")
        (proj / CHANGES / "REG-1" / "plan.md").write_text(
            "# Plan\n- [ ] S1 — limit · files: fees.py, db/migrations/0008_limit.sql\n", encoding="utf-8")
        r = run(SCRIPT, ["stage", str(d3), "plan"], proj, cfg)
        w = json.loads((proj / CHANGES / "REG-1" / "task.json").read_text(encoding="utf-8")).get("weight")
        check(r.returncode == 0 and w == "full" and "full" in r.stdout and "db/migrations/0008_limit.sql" in r.stdout,
              f"W-10: the plan stage repeats the assignment — a plan with a migration raises the weight and says why: {w} {r.stdout}{r.stderr}")
        subprocess.run([sys.executable, str(ts), "weight", "REG-1", "--set", "normal", "--by", "human:anna", "--reason",
                        "the migration only adds an index"], cwd=proj, env=env, capture_output=True, text=True, timeout=60)
        r = run(SCRIPT, ["stage", str(d3), "plan"], proj, cfg)
        w = json.loads((proj / CHANGES / "REG-1" / "task.json").read_text(encoding="utf-8")).get("weight")
        check(r.returncode == 0 and w == "normal", f"W-11: a weight lowered by a human stays at the next stage: {w} {r.stdout}")
        # modes (step E3): Plan ends at the plan, normal waits for the human's approval, Auto goes on
        run(REPORT, ["start", "Eksport sesji", "--key", "EXP-1", "--story", "Jako operator chcę eksport sesji do pliku."],
            proj, cfg)
        d4 = proj / ".tf" / "runs" / "EXP-1"

        def t4():
            return json.loads((proj / CHANGES / "EXP-1" / "task.json").read_text(encoding="utf-8"))

        r = run(SCRIPT, ["stage", str(d4), "intake", "--plan", "--auto"], proj, cfg)
        check(r.returncode == 2, f"T-1: --plan and --auto together → code 2: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d4), "intake", "--plan"], proj, cfg)
        check(r.returncode == 0 and t4().get("mode") == "plan", f"T-2: stage --plan records Plan mode: {r.stdout} {t4().get('mode')}")
        (proj / CHANGES / "EXP-1" / "spec.md").write_text(SPEC, encoding="utf-8")
        (proj / CHANGES / "EXP-1" / "plan.md").write_text("# Plan\n- [ ] S1 — eksport · files: export.py\n", encoding="utf-8")
        run(SCRIPT, ["stage", str(d4), "plan"], proj, cfg)
        r = run(SCRIPT, ["step", str(d4), "S1", "R1", "test", "run"], proj, cfg)
        check(r.returncode == 2 and "Plan" in r.stdout and json.loads((d4 / "run.json").read_text(encoding="utf-8")).get("stage") == "plan",
              f"T-3: Plan mode does not enter the slice loop: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["mode", str(d4), "normal"], proj, cfg)
        r2 = run(SCRIPT, ["step", str(d4), "S1", "R1", "test", "run"], proj, cfg)
        check(r.returncode == 0 and t4().get("mode") == "normal" and r2.returncode == 2 and "approve" in r2.stdout,
              f"T-4: after switching to normal mode the loop waits for the human's approval: {r.stdout} | {r2.returncode} {r2.stdout}")
        r = run(SCRIPT, ["approve", str(d4)], proj, cfg, {"GIT_AUTHOR_NAME": "Anna Nowak"})
        art = (t4().get("artifacts") or {}).get("plan.md") or {}
        who = (art.get("verified") or [{}])[-1].get("by", "")
        r2 = run(SCRIPT, ["step", str(d4), "S1", "R1", "test", "run"], proj, cfg)
        check(r.returncode == 0 and art.get("status") == "approved" and who.startswith("human:") and r2.returncode == 0,
              f"T-5: approve records the human's approval of the plan and the loop starts: {r.stdout}{r.stderr} {who} | {r2.stdout}")
        # criterion identifier in the test already at slice verification (measurement after E3: appended in a separate commit)
        (proj / "export.py").write_text("ROWS = 1\n", encoding="utf-8")
        (proj / "tests").mkdir(exist_ok=True)
        (proj / "tests" / "test_export.py").write_text("def test_export():\n    assert True\n", encoding="utf-8")
        r = run(SCRIPT, ["verify", str(d4), "S1", "--files", "export.py,tests/test_export.py", "--command", OK], proj, cfg)
        check(r.returncode == 0 and "⚠" in r.stdout and "AC-" in r.stdout and "tests/test_export.py" in r.stdout
              and "before the slice's commit" in r.stdout,
              f"A-1: verify warns when the slice's test has no criterion identifier: {r.returncode} {r.stdout}")
        (proj / "tests" / "test_export.py").write_text("def test_ac1_export():  # AC-1\n    assert True\n", encoding="utf-8")
        r = run(SCRIPT, ["verify", str(d4), "S1", "--files", "export.py,tests/test_export.py", "--command", OK], proj, cfg)
        check(r.returncode == 0 and "⚠" not in r.stdout, f"A-2: with an identifier in the test, no warning: {r.stdout}")
        r = run(SCRIPT, ["verify", str(d4), "S1", "--files", "export.py", "--command", OK], proj, cfg)
        check(r.returncode == 0 and "⚠" in r.stdout and "no test file" in r.stdout,
              f"A-3: verify warns when there is no test among the slice's files: {r.stdout}")
        r = run(SCRIPT, ["verify", str(d2), "S1", "--files", "README.md", "--command", OK], proj, cfg)
        check("⚠" not in r.stdout, f"A-4: a task without a spec (light weight) — no criteria warning: {r.stdout}")

        run(REPORT, ["start", "Import sesji", "--key", "IMP-1", "--story", "Jako operator chcę import sesji z pliku."],
            proj, cfg)
        d5 = proj / ".tf" / "runs" / "IMP-1"
        r = run(SCRIPT, ["stage", str(d5), "intake", "--auto"], proj, cfg)
        mode = json.loads((proj / CHANGES / "IMP-1" / "task.json").read_text(encoding="utf-8")).get("mode")
        r2 = run(SCRIPT, ["approve", str(d5)], proj, cfg)
        check(r.returncode == 0 and mode == "auto" and r2.returncode == 2 and "human" in r2.stdout,
              f"T-6: --auto records Auto mode; plan approval cannot be recorded without a human: {mode} | {r2.returncode} {r2.stdout}")
        r = run(SCRIPT, ["stage", str(d), "intake", "--auto"], proj, cfg)        # LOG-1: full weight
        mode = json.loads((proj / CHANGES / "LOG-1" / "task.json").read_text(encoding="utf-8")).get("mode")
        check(r.returncode == 0 and mode == "normal" and "full-weight" in r.stdout,
              f"T-7: --auto at full weight — normal mode stays, with an explanation: {mode} {r.stdout}")

        # closed list of stop codes: a missing code or one outside the list is an error; the preview shows the cause
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "stop", "--reason", "No criteria."], proj, cfg)
        check(r.returncode == 2 and "question" in r.stdout and "budget" in r.stdout,
              f"T-8: STOP without a code → code 2 with the code list: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "stop", "--code", "zmeczenie", "--reason", "x"], proj, cfg)
        check(r.returncode == 2 and "question" in r.stdout, f"T-9: code outside the list → code 2: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "stop", "--code", "question", "--reason",
                         "No acceptance criteria."], proj, cfg)
        meta = json.loads((d5 / "run.json").read_text(encoding="utf-8"))
        card = next((x for x in runs_json((proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8"))
                     if x.get("key") == "IMP-1"), {})
        check(r.returncode == 0 and meta.get("stop_code") == "question" and card.get("stopCode") == "question"
              and card.get("stopLabel") and "No acceptance criteria." in (card.get("stopText") or "")
              and "r.stopLabel" in (proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8"),
              f"T-10: STOP with a code — code in run.json, code, description and reason in the preview: {r.stdout} {card.get('stopCode')} {card.get('stopLabel')}")
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "plan", "--code", "question"], proj, cfg)
        check(r.returncode == 2, f"T-11: --code only for --needs stop: {r.returncode} {r.stdout}")

        # stop message in plain language (step E4): what happened, what is needed, a question with options
        r = run(SCRIPT, ["message", "question"], proj, cfg)
        check(r.returncode == 0 and all(s in r.stdout for s in ("What happened:", "What is needed:", "Question:", "Then:"))
              and r.stdout.count("(recommended)") == 1 and "  1. " in r.stdout and "  2. " in r.stdout,
              f"K-1: message <code> prints a message with fixed fields and one recommendation: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["message", "zmeczenie"], proj, cfg)
        check(r.returncode == 2 and "question" in r.stdout, f"K-2: message with a code outside the list → code 2: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["message", "budget", "--json"], proj, cfg)
        msg = json.loads(r.stdout) if r.returncode == 0 else {}
        check(msg.get("code") == "budget" and msg.get("question", "").endswith("?") and len(msg.get("opcje", [])) >= 2,
              f"K-3: message --json: {r.stdout[:200]}")
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "stop", "--code", "tests", "--reason",
                         "pytest: 2 failed (test_fees.py)"], proj, cfg)
        check(r.returncode == 0 and "The tests fail" in r.stdout and "pytest: 2 failed (test_fees.py)" in r.stdout
              and "Question:" in r.stdout and "AskUserQuestion" in r.stdout,
              f"K-4: recording STOP prints a message for the human with the run reason: {r.stdout}")
        html = (proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8")
        card = next((x for x in runs_json(html) if x.get("key") == "IMP-1"), {})
        stop_file = next((i for g in card.get("files", []) for i in g.get("items", []) if i.get("name") == "STOP"), {})
        check(card.get("stopNeed") and card.get("stopQuestion", "").endswith("?") and len(card.get("stopOptions") or []) >= 2
              and "What is needed" in stop_file.get("text", "") and "r.stopQuestion" in html,
              f"K-5: the preview shows what is needed and a question with options: {card.get('stopNeed')} {card.get('stopQuestion')}")

        old = proj / ".tf" / "runs" / "cuts" / "2026-10-01-stary"
        old.mkdir(parents=True)
        (old / "run.json").write_text(json.dumps({"slug": "stary", "title": "Stary przebieg",
                                                  "started_at": "2026-10-01T10:00:00+00:00"}), encoding="utf-8")
        r = run(SCRIPT, ["stage", str(old), "needs", "--needs", "stop", "--code", "tests", "--reason", "czerwone"], proj, cfg)
        check(r.returncode == 0, f"T-12: a cut run also records STOP with a code: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["weight", str(old)], proj, cfg)
        check(r.returncode == 2 and "cut" in r.stdout, f"W-9: a cut run has no weight: {r.returncode} {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} run-state tests: {'all passed' if not fails else len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
