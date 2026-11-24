#!/usr/bin/env python3
"""Tests of the factory tool `tools/bench.py` (tf bench: an A/B of the factory on reference tasks) with the fake claude
(tools/bench/fake_claude.py) — no model is called: the fixture install, result collection and parsing, the comparison and
regression flagging, the sensitive task's full weight from the collected run.json, and the proposals in
docs/proposals.md (an entry per regression, updated by id, nothing for a clean run). python3 tests/test_bench.py"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from argparse import Namespace
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
SCRIPT = ROOT / "tools" / "bench.py"
FAKE = ROOT / "tools" / "bench" / "fake_claude.py"


def load():
    spec = importlib.util.spec_from_file_location("tf_bench", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bench(*args, fake_env=None, cwd=None):
    env = {k: v for k, v in os.environ.items() if k not in ("TF_BENCH_FAKE", "CLAUDECODE")}
    if fake_env is not None:
        env["TF_BENCH_FAKE"] = json.dumps(fake_env)
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd or ROOT, capture_output=True, text=True,
                          env=env, stdin=subprocess.DEVNULL, timeout=600)


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    b = load()
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)

        # B-1: the fixture in a fresh repository, the factory installed with the normal installer
        proj = b.prepare_project(t / "inst" / "shop")
        inst = b.install_factory(ROOT, proj, "none", "default")
        check(inst["ok"], f"B-1 the install succeeds: {(t / 'inst' / 'install.log').read_text()[-500:]}")
        check((proj / ".claude" / "skills" / "tf-task" / "SKILL.md").is_file(), "B-1 /tf-task is installed in .claude/")
        check((proj / ".tf" / "factory" / "task_weight.py").is_file(), "B-1 the engine is installed in .tf/factory/")
        gate = json.loads((proj / ".claude" / "quality-gate.json").read_text())
        check(gate.get("command") == ["python3", "run_tests.py"] and "{files}" in gate.get("related"),
              f"B-1 the fixture's gate config: {gate}")
        check(inst["tree_clean"], "B-1 the working tree is clean after the install (the loop starts from a clean tree)")
        check(subprocess.run([sys.executable, "run_tests.py"], cwd=proj, capture_output=True).returncode == 0,
              "B-1 the fixture's tests are green before the task")
        check(not (proj / "_quality-gate.json").exists(), "B-1 the gate config moved to .claude/")

        # B-2: the headless command: the flags of an unattended run
        o = Namespace(layout="default", budget=3.0, permission_mode="acceptEdits", permission_prompts=True, model="sonnet")
        argv = b.agent_command(["claude"], "Do X", proj, o)
        check(argv[argv.index("-p") + 1].startswith("/tf-task Do X") and "--auto --budget 3" in argv[argv.index("-p") + 1],
              f"B-2 the prompt is /tf-task with --auto and the budget: {argv}")
        for flag, value in (("--output-format", "json"), ("--permission-mode", "acceptEdits"), ("--max-budget-usd", "3"),
                            ("--permission-prompts", "none"), ("--model", "sonnet")):
            check(flag in argv and argv[argv.index(flag) + 1] == value, f"B-2 {flag} {value}: {argv}")
        check("--strict-mcp-config" in argv, "B-2 no MCP servers from the configuration")
        o.layout, o.permission_prompts, o.model = "plugin", False, None
        argv = b.agent_command(["claude"], "Do X", proj, o)
        check("--plugin-dir" in argv and argv[argv.index("-p") + 1].startswith("/tf:tf-task") and
              "--permission-prompts" not in argv and "--model" not in argv, f"B-2 the plugin layout: {argv}")

        # B-3: parsing the result and the report
        res = b.parse_result('{"type":"result","num_turns":7,"total_cost_usd":0.5,"duration_ms":61000}')
        check(res.get("num_turns") == 7, f"B-3 a JSON result: {res}")
        res = b.parse_result('warning: x\n{"type":"result","num_turns":3}\n')
        check(res.get("num_turns") == 3, f"B-3 the last JSON line wins over text around it: {res}")
        res = b.parse_result('[{"type":"system"},{"type":"result","num_turns":4}]')
        check(res.get("num_turns") == 4, f"B-3 a message list: the result message: {res}")
        check(b.parse_result("not json") == {}, "B-3 no JSON: an empty result")
        rep = b.report_numbers("# r\n\n- Time: 87 min 3 s (x)\n- Model requests: 66 · models: m\n\n## Where the time went\n\n"
                               "- Verification commands: 1 min\n\n## Next\n")
        check(rep.get("report_time_s") == 87 * 60 + 3 and rep.get("requests") == 66
              and rep.get("time_went", "").startswith("- Verification"), f"B-3 report.md numbers: {rep}")

        # B-4: collecting a run (the fake claude in the installed fixture)
        env = {k: v for k, v in os.environ.items() if k != "TF_BENCH_FAKE"}
        env.update(TF_BENCH_TASK="medium", TF_BENCH_SIDE="ref")
        agent = b.run_agent([sys.executable, str(FAKE), "-p", "/tf-task x --auto"], proj, env, 60)
        m = b.collect(proj, agent, t / "out" / "medium", "medium")
        check(m["turns"] == 45 and m["cost_usd"] == 3.5 and m["time_s"] == 900.0, f"B-4 the JSON result: {m}")
        check(m["weight"] == "normal" and m["approach"] == "normal" and m["slices"] == 2 and m["slices_done"] == 2,
              f"B-4 weight, approach and slices from task.json and plan.md: {m}")
        check(m["verify_s"] == 8.0 and m["verify_runs"] == 2 and m["gate_s"] == 2.0 and m["gate_runs"] == 1,
              f"B-4 verify evidence and gate log: {m}")
        check(m["requests"] == 48 and m["report"], f"B-4 model requests from report.md: {m}")
        check(m["commits"] == 2 and m["committed"] and m["tests_green"] and m["accepted"],
              f"B-4 commits, tests and the hidden check: {m}")
        check({"quality-gate", "verify", "scope-review"} <= set(m["gates"]), f"B-4 the gates that fired: {m['gates']}")
        for name in ("run.json", "task.json", "plan.md", "report.md", "quality-gate-runs.jsonl", "claude.json",
                     "metrics.json"):
            check((t / "out" / "medium" / name).is_file(), f"B-4 collected {name}")
        check(b.misses(b.load_tasks()["medium"], m) == [], f"B-4 medium meets its expectation: {b.misses(b.load_tasks()['medium'], m)}")

        # B-5: a clean comparison (git ref vs path): exit 0, no proposals file
        props = t / "proposals.md"
        r = bench("run", "--ref", "HEAD", "--cand", str(ROOT), "--task", "simple", "--fake-claude", str(FAKE),
                  "--out", str(t / "clean"), "--proposals", str(props), fake_env={})
        check(r.returncode == 0, f"B-5 a clean comparison exits 0: {r.stdout[-1500:]}{r.stderr[-1500:]}")
        reports = list((t / "clean").glob("bench-*.md"))
        check(len(reports) == 1 and "no regression" in reports[0].read_text(), "B-5 bench-<date>.md says no regression")
        check("Proposals: none" in (reports[0].read_text() if reports else ""), "B-5 one line about proposals in the report")
        check(not props.exists(), "B-5 a clean comparison writes no proposals")
        data = json.loads((t / "clean" / "bench.json").read_text())
        check(data["tasks"]["simple"]["ref"]["weight"] == ["quick"] and data["tasks"]["simple"]["cand"]["slices"] == 1,
              f"B-5 bench.json holds the summaries: {data['tasks']['simple']['ref']}")

        # B-6: a slower candidate with more turns: regressions flagged, proposals written, then deduplicated
        knobs = {"cand": {"slow": 1.5, "turns": 1.5, "gate_s": 120}}
        props.write_text("# Factory proposals\n\n## P-1 — a project entry\n\nStatus: open\nDate: 2026-11-01\n"
                         "Project: demo\nFactory version: 24.0.0\nEvidence: x\nProposed change: y\n")
        r = bench("run", "--ref", str(ROOT), "--cand", str(ROOT), "--task", "simple", "--runs", "2", "--fake-claude",
                  str(FAKE), "--out", str(t / "slow"), "--proposals", str(props), fake_env=knobs)
        check(r.returncode == 1, f"B-6 a regression exits 1: {r.stdout[-1500:]}{r.stderr[-800:]}")
        md = next((t / "slow").glob("bench-*.md")).read_text()
        for word in ("wall time (s): 300 → 450", "model turns: 20 → 30", "gate hook time (s)"):
            check(word in md, f"B-6 the verdict names {word!r}")
        check("| wall time (s) | 300 | 450 | +50% | **regression** |" in md, "B-6 the table marks the row")
        text = props.read_text()
        ids = [ln.split(" ")[1] for ln in text.splitlines() if ln.startswith("## BENCH-")]
        check(len(ids) == 3, f"B-6 one entry per regression: {ids}")
        check(text.startswith("# Factory proposals\n\n> Entries come from projects and bench runs; review before acting.\n"),
              f"B-6 the header note is added once: {text[:200]!r}")
        check("## P-1 — a project entry\n\nStatus: open\nDate: 2026-11-01\nProject: demo\nFactory version: 24.0.0\n"
              "Evidence: x\nProposed change: y\n" in text, "B-6 the project's entry stays byte for byte")
        for line in ("Status: open", "Date: ", "Ref: ", "Cand: ", "Task: simple", "Metric: wall time (s): 300 → 450",
                     "Evidence: ", "Proposed change: "):
            check(f"\n{line}" in text, f"B-6 the entry has {line!r}")
        check(str(t / "slow") in text and "bench-" in text, "B-6 the entry points to the report and the run dirs")
        check("suspected cause: unknown" in text, "B-6 a path side without a commit range: the cause is unknown")
        props.write_text(text.replace("Status: open\nDate: " + data["date"] + "\nRef", "Status: accepted\nDate: "
                                      + data["date"] + "\nRef", 1))
        r = bench("run", "--ref", str(ROOT), "--cand", str(ROOT), "--task", "simple", "--runs", "2", "--fake-claude",
                  str(FAKE), "--out", str(t / "slow2"), "--proposals", str(props), fake_env=knobs)
        text2 = props.read_text()
        ids2 = [ln.split(" ")[1] for ln in text2.splitlines() if ln.startswith("## BENCH-")]
        check(r.returncode == 1 and ids2 == ids, f"B-6 a re-run updates the same ids, no duplicates: {ids2}")
        check("(updated)" in r.stdout and "(added)" not in r.stdout, "B-6 the re-run reports updates")
        check(text2.count("Status: accepted") == 1, "B-6 a status the owner changed is kept")
        check(str(t / "slow2") in text2 and str(t / "slow") + "/" not in text2.replace(str(t / "slow2"), ""),
              "B-6 the updated entry points to the new run")
        check(text2.count("review before acting") == 1 and text2.count("## P-1") == 1, "B-6 nothing else duplicated")

        # B-7: --no-proposals, and `compare` with other thresholds recomputes from bench.json
        before = props.read_text()
        r = bench("compare", str(t / "slow"), "--no-proposals")
        check(r.returncode == 1 and "not written (--no-proposals)" in r.stdout and props.read_text() == before,
              "B-7 --no-proposals writes nothing")
        r = bench("compare", str(t / "slow"), "--max-slower", "0.6", "--max-more-turns", "0.6", "--min-seconds", "500",
                  "--proposals", str(props))
        check(r.returncode == 0 and "no regression" in r.stdout, f"B-7 looser thresholds: clean: {r.stdout[-800:]}")
        check(props.read_text() == before, "B-7 a clean compare adds nothing")

        # B-8: the sensitive task: the full weight from the collected run.json/task.json, and a candidate without the gate
        r = bench("run", "--ref", str(ROOT), "--cand", str(ROOT), "--task", "sensitive", "--fake-claude", str(FAKE),
                  "--out", str(t / "sens"), "--proposals", str(props),
                  fake_env={"cand": {"weight": "normal", "no_gate": True}})
        check(r.returncode == 1, f"B-8 a missing gate is a regression: {r.stdout[-1500:]}{r.stderr[-800:]}")
        ref = json.loads((t / "sens" / "sensitive" / "ref-r1" / "metrics.json").read_text())
        run_json = json.loads((t / "sens" / "sensitive" / "ref-r1" / "run.json").read_text())
        check(ref["weight"] == "full" and run_json.get("stop_code") == "plan-approval" and ref["commits"] == 0
              and "stop:plan-approval" in ref["gates"], f"B-8 ref: full, stopped for plan approval, no code: {ref}")
        check(b.misses(b.load_tasks()["sensitive"], ref) == [], "B-8 ref meets the sensitive expectation")
        cand = json.loads((t / "sens" / "sensitive" / "cand-r1" / "metrics.json").read_text())
        check(cand["weight"] == "normal" and cand["commits"] == 1, f"B-8 cand changed the code at a normal weight: {cand}")
        md = next((t / "sens").glob("bench-*.md")).read_text()
        check("a required gate did not fire on cand" in md and "weight normal outside the task's expectation" in md,
              "B-8 the verdict names the missing gate and the wrong weight")
        check(sum(1 for ln in props.read_text().splitlines() if "— sensitive:" in ln) == 2,
              "B-8 two sensitive entries (gate, weight)")

        # B-9: a red candidate: fewer green tests and accepted results are regressions
        r = bench("run", "--ref", str(ROOT), "--cand", str(ROOT), "--task", "simple", "--fake-claude", str(FAKE),
                  "--out", str(t / "red"), "--no-proposals", fake_env={"cand": {"red": True}})
        md = next((t / "red").glob("bench-*.md")).read_text()
        check(r.returncode == 1 and "tests green: 1/1 → 0/1" in md, f"B-9 red tests flagged: {md[-800:]}")

        # B-10: the real claude costs tokens: without --yes and without a terminal the bench refuses
        r = bench("run", "--ref", str(ROOT), "--cand", str(ROOT), "--task", "simple", "--claude", "false",
                  "--out", str(t / "no"))
        check(r.returncode == 2 and "--yes" in r.stdout and not (t / "no").exists(),
              f"B-10 no consent, no run: {r.stdout[-400:]}")
        r = bench("run", "--ref", "no-such-ref-xyz", "--cand", str(ROOT), "--fake-claude", str(FAKE), "--out",
                  str(t / "bad"))
        check(r.returncode != 0 and "no-such-ref-xyz" in (r.stdout + r.stderr), "B-10 an unknown ref is refused")
        r = bench("tasks")
        check(r.returncode == 0 and [ln.split(":")[0] for ln in r.stdout.splitlines() if not ln.startswith(" ")]
              == ["simple", "medium", "sensitive"], f"B-10 the task list: {r.stdout}")

    print(f"{total - len(fails)}/{total} checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
