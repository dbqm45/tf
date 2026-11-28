#!/usr/bin/env python3
"""
tf stress: a load and edge-case test of the factory — where it is slow, where it is wrong, where it breaks.

A library of declarative scenarios (tools/stress/library/*.yaml) with categories, tags (suites), injected faults and
thresholds; every scenario ends PASS / FAIL with the exact reason; the report ranks the hotspots — where the time goes
and what to improve.

Two engines:
  mech   no model, no cost, seconds: the factory's scripts and hooks driven with corpora of edge-case inputs
         (tools/stress/corpus/: task weight, input recognition, guard hooks, TDD sequences) and load patterns
         (hook chains per action, concurrent hooks, the loop's script calls, status at scale, tf work races,
         install and update, the context every session loads).
  model  one unattended /tf-task per scenario (the same flags as `tf work --once`, with stream-json), in a fresh
         copy of the fixture with the scenario's faults (dirty tree, red main, slow or flaky tests, no scanner,
         no quality gate, a big repository, …). Every hook is wrapped by a timing probe; the profiler turns the
         stream into a timeline and a breakdown: model time, factory scripts, tests, scan, git, subagents, hooks,
         wasted calls (refusals, denials, errors) — per category, per call and per loop phase. A hidden acceptance
         check (tools/stress/checks/) judges the result. It costs tokens: it asks first (--yes skips).

  python3 tools/stress.py list [--suite S] [--engine mech|model]
  python3 tools/stress.py check                                   # validate the library (unknown keys are errors)
  python3 tools/stress.py run [--suite smoke|edge|load|model|all|<tag>|<category>] [--scenario ID …]
                              [--engine mech|model|all] [--concurrency N] [--repeat N] [--out DIR]
                              [--model M] [--timeout MIN] [--claude CMD] [--yes]
  python3 tools/stress.py capacity --scenario ID --sizes 1,2,4 [--out DIR] [--yes]   # N copies at once → breaking point
  python3 tools/stress.py compare <a/result.json> <b/result.json>                   # regressions, exit 1
  python3 tools/stress.py report <out-dir>                                           # rebuild report.md and junit.xml
  python3 tools/stress.py rescore <out-dir>          # re-profile and re-judge saved model runs (no model calls)

Results in <out> (default .work/stress/<date-time>/): result.json, report.md, junit.xml and per model scenario
the project copy with .stress/stream.jsonl and .stress/hooks.jsonl. Exit code 1 when a scenario failed.
Standard library only (plus the factory's vendored PyYAML).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "stress" / "lib"))
from common import ROOT, load_library, run, select, stats  # noqa: E402
import mech  # noqa: E402
import model  # noqa: E402
import report  # noqa: E402


def meta(o) -> dict:
    sha = run(["git", "rev-parse", "--short", "HEAD"], ROOT).stdout.strip()
    ver = (ROOT / "core/factory/VERSION").read_text().strip() if (ROOT / "core/factory/VERSION").exists() else "?"
    return {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "factory_version": ver, "factory_sha": sha,
            "cpus": os.cpu_count(), "model": getattr(o, "model", None) or "default",
            "concurrency": getattr(o, "concurrency", 1), "python": sys.version.split()[0]}


def judge_mech(sc: dict, res: dict) -> dict:
    cases = res.get("cases", [])
    exp = sc.get("expect") or {}
    fails = []
    acc = sum(c["ok"] for c in cases) / len(cases) if cases else 0
    if "min_accuracy" in exp:
        if acc < float(exp["min_accuracy"]):
            fails.append(f"accuracy {acc:.0%} < {float(exp['min_accuracy']):.0%}")
    elif not all(c["ok"] for c in cases):
        fails.append(f"{sum(not c['ok'] for c in cases)} of {len(cases)} cases failed")
    mt = res.get("metrics") or {}
    for key, metric in (("max_under", "under"), ("max_false_deny", "false_deny")):
        if key in exp and mt.get(metric, 0) > exp[key]:
            fails.append(f"{metric} {mt.get(metric)} > {exp[key]}")
    if "max_p95_ms" in exp:
        p95 = stats([c["ms"] for c in cases if c.get("ms") is not None]).get("p95")
        if p95 and p95 > exp["max_p95_ms"]:
            fails.append(f"p95 {p95} ms > {exp['max_p95_ms']} ms")
    return {"verdict": "PASS" if not fails else "FAIL", "accuracy": round(acc, 3), "threshold_fails": fails}


def run_one(sc: dict, work: Path, o) -> dict:
    t = time.time()
    base = {"id": sc["id"], "name": sc.get("name", ""), "category": sc["category"], "engine": sc["engine"],
            "tags": sc["tags"], "description": sc.get("description", "")}
    if sc["engine"] == "mech":
        res = mech.run_mech(sc, work)
        base.update(res)
        base.update(judge_mech(sc, res))
    else:
        try:
            base.update(model.run_model(sc, work, o))
        except Exception as e:
            import traceback
            base.update({"verdict": "ERROR", "checks": [{"name": "runner", "ok": False, "actual": repr(e),
                                                         "expected": traceback.format_exc()[-300:]}]})
    base["wall_s"] = base.get("wall_s") or round(time.time() - t, 1)
    base["why"] = report.why(base)
    icon = {"PASS": "✓", "FAIL": "✗"}.get(base["verdict"], "!")
    extra = ""
    if base.get("profile"):
        p = base["profile"]
        extra = f" {p['wall_s']}s ${p.get('cost_usd') or 0:.2f}"
    print(f"{icon} {sc['id']} {base['verdict']}{extra} {sc.get('name', '')}", flush=True)
    for w in base["why"][:3]:
        print(f"    {w}", flush=True)
    return base


def consent(o, n: int, budget: float) -> bool:
    if o.yes or n == 0:
        return True
    print(f"{n} model run(s), up to ${budget:.0f} in tokens. Continue? [y/N] ", end="", flush=True)
    return sys.stdin.readline().strip().lower() in ("y", "yes", "t", "tak")


def cmd_run(o) -> int:
    errors = []
    lib = load_library(errors)
    if errors:
        print("✗ library errors:\n  " + "\n  ".join(errors))
        return 2
    chosen = select(lib, o.suite, o.scenario, o.engine)
    if not chosen:
        print("✗ no scenario matches")
        return 2
    mech_s = [s for s in chosen if s["engine"] == "mech"]
    model_s = [s for s in chosen if s["engine"] == "model"] * max(1, o.repeat)
    if not consent(o, len(model_s), sum(float(s.get("budget", 3)) for s in model_s)):
        return 2
    out = Path(o.out or ROOT / ".work" / "stress" / datetime.now().strftime("%Y%m%d-%H%M%S")).resolve()
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)
    results = []
    for sc in mech_s:                       # first and alone: they measure latency
        results.append(run_one(sc, work, o))
    if model_s:
        mech.template(model_s[0].get("fixture", "node-tasks"), work)     # build templates before the parallel runs
        for s in model_s:
            mech.template(s.get("fixture", "node-tasks"), work, s.get("layout", "default"),
                          "pack-it" if s.get("fixture", "node-tasks") == "node-tasks" else "none")
        reps = {}

        def go(sc):
            ns = argparse.Namespace(**vars(o))
            reps[sc["id"]] = reps.get(sc["id"], -1) + 1
            ns._rep = reps[sc["id"]]
            r = run_one(sc, work, ns)
            r["repeat"] = ns._rep
            return r

        with ThreadPoolExecutor(max(1, o.concurrency)) as ex:
            results += list(ex.map(go, model_s))
    data = {"meta": meta(o), "scenarios": results, "hotspots": report.hotspots(results)}
    report.write_all(out, data)
    print("\n" + report.console(results))
    print(f"\nReport: {out / 'report.md'} · {out / 'result.json'} · {out / 'junit.xml'}")
    return 0 if all(r["verdict"] == "PASS" for r in results) else 1


def cmd_capacity(o) -> int:
    lib = {s["id"]: s for s in load_library()}
    sc = lib.get(o.scenario.upper())
    if not sc or sc["engine"] != "model":
        print("✗ capacity needs a model scenario id")
        return 2
    sizes = [int(x) for x in o.sizes.split(",")]
    if not consent(o, sum(sizes), sum(sizes) * float(sc.get("budget", 3))):
        return 2
    out = Path(o.out or ROOT / ".work" / "stress" / ("cap-" + datetime.now().strftime("%Y%m%d-%H%M%S"))).resolve()
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)
    mech.template(sc.get("fixture", "node-tasks"), work, sc.get("layout", "default"),
                  "pack-it" if sc.get("fixture", "node-tasks") == "node-tasks" else "none")
    rows, allres, base = [], [], None
    for n in sizes:
        def go(i, n=n):
            ns = argparse.Namespace(**vars(o))
            ns._rep = n * 100 + i
            return run_one(sc, work, ns)

        t0 = time.time()
        with ThreadPoolExecutor(n) as ex:
            res = list(ex.map(go, range(n)))
        wall = time.time() - t0
        allres += res
        walls = [r["profile"]["wall_s"] for r in res if r.get("profile")]
        # capacity counts delivered work (outcome and hidden check), not the time or cost targets
        ok = sum(all(c["ok"] for c in r.get("checks", []) if c["name"] in ("outcome", "hidden acceptance check"))
                 and r["verdict"] != "ERROR" for r in res)
        st = stats(walls)
        row = {"size": n, "ok": ok, "batch_wall_s": round(wall, 1), "wall_p50": st.get("p50"), "wall_max": st.get("max"),
               "cost": round(sum((r.get("profile") or {}).get("cost_usd") or 0 for r in res), 2),
               "tasks_per_hour": round(3600 * ok / wall, 1) if wall else 0}
        base = base or row
        rows.append(row)
        print(f"{n:3}× ok {ok}/{n} · p50 {row['wall_p50']} s · max {row['wall_max']} s · {row['tasks_per_hour']} tasks/h", flush=True)
    limited = [r for r in allres if any(c["name"] == "environment" for c in r.get("checks", []))]
    if limited:
        print(f"⚠ {len(limited)} run(s) hit the account's usage limit — the capacity numbers are not valid")
    breaking = next((r["size"] for r in rows if r["ok"] < r["size"] or
                     (base["wall_p50"] and r["wall_p50"] and r["wall_p50"] > 1.5 * base["wall_p50"])), None)
    cap = [{"scenario": sc["id"], "rows": rows, "breaking": breaking}]
    data = {"meta": meta(o), "scenarios": allres, "capacity": cap, "hotspots": report.hotspots(allres, cap)}
    report.write_all(out, data)
    print(f"Breaking point: {breaking or 'not reached'} · {out / 'result.json'}")
    return 0


def cmd_list(o) -> int:
    errors = []
    lib = select(load_library(errors), o.suite, None, o.engine)
    for s in lib:
        print(f"{s['id']:10} {s['engine']:5} {s['category']:14} {s.get('name', ''):38} [{', '.join(s['tags'])}]")
    print(f"\n{len(lib)} scenarios" + (f" · {len(errors)} library errors (tools/stress.py check)" if errors else ""))
    return 0


def cmd_check(o) -> int:
    errors = []
    lib = load_library(errors)
    for e in errors:
        print(f"✗ {e}")
    if not errors:
        print(f"✓ {len(lib)} scenarios")
    return 1 if errors else 0


def cmd_compare(o) -> int:
    a, b = json.loads(Path(o.a).read_text()), json.loads(Path(o.b).read_text())
    regs = report.compare(a, b)
    for r in regs:
        print(f"🔴 {r}")
    print(f"{len(regs)} regression(s)" if regs else "✓ no regressions")
    return 1 if regs else 0


def cmd_rescore(o) -> int:
    """Re-profile and re-evaluate every model scenario of a finished run from its saved project copy (no model)."""
    out = Path(o.dir)
    data = json.loads((out / "result.json").read_text())
    lib = {s["id"]: s for s in load_library()}
    for r in data["scenarios"]:
        if r["engine"] != "model" or r["id"] not in lib:
            continue
        proj = Path(r.get("project") or out / "work" / "model" / r["id"] / f"r{r.get('repeat', 0)}")
        if not (proj / ".stress" / "stream.jsonl").exists():
            continue
        r.update(model.score(lib[r["id"]], proj, r.get("proc"), r.get("faults"), r.get("model")))
        r["why"] = report.why(r)
    data["hotspots"] = report.hotspots(data["scenarios"], data.get("capacity"))
    report.write_all(out, data)
    print(report.console(data["scenarios"]))
    return 0


def cmd_report(o) -> int:
    out = Path(o.dir)
    data = json.loads((out / "result.json").read_text())
    data["hotspots"] = report.hotspots(data["scenarios"], data.get("capacity"))
    report.write_all(out, data)
    print(report.console(data["scenarios"]))
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tools/stress.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list")
    l.add_argument("--suite")
    l.add_argument("--engine")
    sub.add_parser("check")
    for name in ("run", "capacity"):
        r = sub.add_parser(name)
        r.add_argument("--out")
        r.add_argument("--model")
        r.add_argument("--timeout", type=float, default=30.0, help="minutes per model run")
        r.add_argument("--claude", default="claude")
        r.add_argument("--yes", action="store_true")
        r.add_argument("--concurrency", type=int, default=1)
        if name == "run":
            r.add_argument("--suite")
            r.add_argument("--scenario", nargs="*")
            r.add_argument("--engine", default="all")
            r.add_argument("--repeat", type=int, default=1)
        else:
            r.add_argument("--scenario", required=True)
            r.add_argument("--sizes", default="1,2,4")
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    rp = sub.add_parser("report")
    rp.add_argument("dir")
    rs = sub.add_parser("rescore")
    rs.add_argument("dir")
    o = ap.parse_args(argv)
    return {"run": cmd_run, "capacity": cmd_capacity, "list": cmd_list, "check": cmd_check, "compare": cmd_compare,
            "report": cmd_report, "rescore": cmd_rescore}[o.cmd](o)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
