#!/usr/bin/env python3
"""
The eval gate for CI: a threshold from the baseline spread, regression tasks, a budget. Runs no model.

  python3 .claude/skills/ai-evals/scripts/eval_gate.py baseline base1.jsonl base2.jsonl base3.jsonl \\
          [--margin 0.02] [--out evals/baseline.json]
  python3 .claude/skills/ai-evals/scripts/eval_gate.py check results.jsonl --baseline evals/baseline.json \\
          [--budget-usd 5] [--strict] [--json] [--report report.md]

Input: the results of a product eval run as JSON Lines, one line per trial:
  {"id": "refund-17", "passed": true, "layer": "regression", "cost_usd": 0.012, "trial": 2}
`id` and `passed` are required; `layer` equal to `regression` marks a task of the regression dataset; `cost_usd` is
the cost of the trial; several lines with the same `id` are repeated trials (k).

`baseline` computes, from several runs of the current version (3–5), the spread of the success rate (min, max, mean),
the threshold = the lower bound of the spread − the margin (the team sets the margin; default 0) and the stable tasks
(passed in every run). `check` judges a candidate run:
  hold         success below the threshold, a failed task of the regression layer, or cost over the budget
  investigate  success below the lower bound of the spread (inside the margin), a task stable in the baseline failed,
               the task set differs from the baseline, or a budget was given and the results carry no cost
  release      everything else
Metrics: success (passed trials / trials), pass^k (tasks passed in all k trials), pass@k (passed in at least one), cost.

Exit code: 0 — release or investigate; 1 — hold (with --strict also investigate); 2 — a usage or data error (an empty
results file is an error, not "0 failures"). Standard library only, no network.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

REGRESSION_LAYERS = {"regression"}
MIN_BASELINE_RUNS = 3


class DataError(Exception):
    pass


def load_run(path: Path) -> list[dict]:
    """Trials from a JSON Lines file; DataError on a missing or empty file, a bad line, or a missing `id`/`passed`."""
    if not path.is_file():
        raise DataError(f"no results file: {path}")
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise DataError(f"{path}:{n}: the line is not valid JSON ({e.msg})") from None
        if not isinstance(row, dict) or "id" not in row or not isinstance(row.get("passed"), bool):
            raise DataError(f"{path}:{n}: the fields `id` and `passed` (true/false) are required")
        cost = row.get("cost_usd")
        if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0):
            raise DataError(f"{path}:{n}: `cost_usd` must be a non-negative number")
        rows.append(row)
    if not rows:
        raise DataError(f"{path}: no results — an empty run is not evidence of quality")
    return rows


def metrics(rows: list[dict]) -> dict:
    by_task: dict[str, list[bool]] = {}
    layers: dict[str, str] = {}
    for r in rows:
        tid = str(r["id"])
        by_task.setdefault(tid, []).append(r["passed"])
        if r.get("layer"):
            layers[tid] = str(r["layer"]).strip().lower()
    costs = [r["cost_usd"] for r in rows if r.get("cost_usd") is not None]
    attempts = len(rows)
    tasks = len(by_task)
    return {
        "attempts": attempts, "tasks": tasks, "k": max(len(v) for v in by_task.values()),
        "success": sum(r["passed"] for r in rows) / attempts,
        "pass_all_k": sum(all(v) for v in by_task.values()) / tasks,
        "pass_any_k": sum(any(v) for v in by_task.values()) / tasks,
        "cost_usd": sum(costs) if costs else None,
        "cost_known_attempts": len(costs),
        "task_ids": sorted(by_task),
        "all_passed": sorted(t for t, v in by_task.items() if all(v)),
        "failed": sorted(t for t, v in by_task.items() if not all(v)),
        "regression_layer_failures": sorted(t for t, v in by_task.items() if not all(v) and layers.get(t) in REGRESSION_LAYERS),
    }


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def cmd_baseline(a) -> int:
    runs = [metrics(load_run(Path(p))) for p in a.runs]
    rates = [m["success"] for m in runs]
    stable = set(runs[0]["all_passed"])
    for m in runs[1:]:
        stable &= set(m["all_passed"])
    low = min(rates)
    data = {
        "version": 1, "created": dt.date.today().isoformat(), "runs": len(runs),
        "success": {"min": low, "max": max(rates), "mean": sum(rates) / len(rates)},
        "margin": a.margin, "threshold": low - a.margin,
        "tasks": sorted(set().union(*(m["task_ids"] for m in runs))),
        "stable_tasks": sorted(stable), "k": max(m["k"] for m in runs),
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Baseline: {len(runs)} runs, success {pct(low)}–{pct(max(rates))} (mean {pct(data['success']['mean'])}), "
          f"margin {pct(a.margin)}, threshold {pct(data['threshold'])}; {len(data['tasks'])} tasks, {len(stable)} stable → {out}")
    if len(runs) < MIN_BASELINE_RUNS:
        print(f"⚠ A baseline from {len(runs)} run(s): the spread is unreliable — repeat the baseline {MIN_BASELINE_RUNS}–5 times "
              f"before the threshold starts blocking.")
    if a.margin == 0:
        print("· Margin 0: the threshold is the lower bound of the spread. The team sets the margin (--margin) and records who and why.")
    return 0


def judge(m: dict, base: dict, budget: float | None) -> tuple[str, list[str], list[str]]:
    """(verdict, reasons, regressions of stable tasks)."""
    stop, look = [], []
    success, low, threshold = m["success"], base["success"]["min"], base["threshold"]
    if success < threshold:
        stop.append(f"success {pct(success)} is below the threshold {pct(threshold)} (baseline {pct(low)}–{pct(base['success']['max'])}, "
                    f"margin {pct(base.get('margin', 0))})")
    elif success < low:
        look.append(f"success {pct(success)} is below the lower bound of the baseline spread {pct(low)} but inside the margin "
                    f"(threshold {pct(threshold)})")
    if m["regression_layer_failures"]:
        stop.append(f"tasks of the regression layer failed: {', '.join(m['regression_layer_failures'])}")
    regressions = sorted(set(base.get("stable_tasks") or []) & set(m["failed"]))
    if regressions:
        look.append(f"tasks stable in the baseline failed: {', '.join(regressions)}")
    if set(base.get("tasks") or []) != set(m["task_ids"]):
        missing = sorted(set(base.get("tasks") or []) - set(m["task_ids"]))
        new = sorted(set(m["task_ids"]) - set(base.get("tasks") or []))
        look.append(f"the task set differs from the baseline ({len(missing)} missing, {len(new)} new) — compute the baseline on the same set")
    if budget is not None:
        if m["cost_usd"] is None:
            look.append("a budget was given but the results have no cost_usd field — the cost of the run is unknown")
        elif m["cost_usd"] > budget:
            stop.append(f"cost {m['cost_usd']:.2f} USD is over the budget {budget:.2f} USD")
        elif m["cost_known_attempts"] < m["attempts"]:
            look.append(f"cost is known for only {m['cost_known_attempts']} of {m['attempts']} trials — the sum is too low")
    verdict = "hold" if stop else ("investigate" if look else "release")
    return verdict, stop + look, regressions


def report_text(out: dict) -> str:
    b = out["baseline"]
    cost = "unknown" if out["cost_usd"] is None else f"{out['cost_usd']:.2f} USD"
    budget = "" if out["budget_usd"] is None else f" (budget {out['budget_usd']:.2f} USD)"
    lines = [
        f"Verdict: {out['verdict']}",
        f"Result: success {pct(out['success'])} vs baseline {pct(b['min'])}–{pct(b['max'])} (mean {pct(b['mean'])}, "
        f"{b['runs']} runs) | threshold {pct(out['threshold'])}",
        f"Trials: {out['attempts']} on {out['tasks']} tasks, k = {out['k']} | pass^k {pct(out['pass_all_k'])} | "
        f"pass@k {pct(out['pass_any_k'])}",
        f"Cost: {cost}{budget}",
    ]
    if out["reasons"]:
        lines.append("Reasons:")
        lines += [f"- {r}" for r in out["reasons"]]
    if out["regressions"]:
        lines.append(f"Regressions (stable in the baseline, now failing): {', '.join(out['regressions'])}")
    if out["regression_layer_failures"]:
        lines.append(f"Failures of the regression layer: {', '.join(out['regression_layer_failures'])}")
    return "\n".join(lines)


def cmd_check(a) -> int:
    m = metrics(load_run(Path(a.results)))
    base_path = Path(a.baseline)
    if not base_path.is_file():
        raise DataError(f"no baseline file: {base_path} (create it: eval_gate.py baseline <runs…> --out {base_path})")
    try:
        base = json.loads(base_path.read_text(encoding="utf-8"))
        float(base["threshold"]), float(base["success"]["min"]), float(base["success"]["max"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        raise DataError(f"{base_path}: this is not a baseline file from eval_gate.py baseline") from None
    verdict, reasons, regressions = judge(m, base, a.budget_usd)
    out = {
        "verdict": verdict, "success": m["success"], "threshold": base["threshold"],
        "baseline": {"min": base["success"]["min"], "max": base["success"]["max"], "mean": base["success"].get("mean"),
                     "runs": base.get("runs"), "margin": base.get("margin", 0), "created": base.get("created")},
        "pass_all_k": m["pass_all_k"], "pass_any_k": m["pass_any_k"], "k": m["k"], "tasks": m["tasks"],
        "attempts": m["attempts"], "cost_usd": m["cost_usd"], "budget_usd": a.budget_usd,
        "regressions": regressions, "regression_layer_failures": m["regression_layer_failures"], "reasons": reasons,
    }
    text = report_text(out)
    if a.report:
        rp = Path(a.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text("## Eval gate\n\n" + text.replace("\n", "  \n") + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2) if a.json else text)
    return 1 if verdict == "hold" or (a.strict and verdict == "investigate") else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="The eval gate for CI (runs no model). Exit code: 0 release or investigate, "
                                             "1 hold (with --strict also investigate), 2 a usage or data error.",
                                 epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baseline", help="the spread and the threshold from several runs of the current version")
    b.add_argument("runs", nargs="+", help="result files of the baseline runs (JSON Lines)")
    b.add_argument("--margin", type=float, default=0.0, help="margin below the lower bound of the spread, a fraction (e.g. 0.02)")
    b.add_argument("--out", default="evals/baseline.json", help="the baseline file (default evals/baseline.json)")
    c = sub.add_parser("check", help="judge a candidate run against the baseline")
    c.add_argument("results", help="the candidate's results file (JSON Lines)")
    c.add_argument("--baseline", default="evals/baseline.json", help="the baseline file from the baseline command")
    c.add_argument("--budget-usd", type=float, default=None, help="the budget of the run in USD (the sum of cost_usd)")
    c.add_argument("--strict", action="store_true", help="exit 1 also for the verdict investigate")
    c.add_argument("--json", action="store_true", help="the result as JSON")
    c.add_argument("--report", help="write a Markdown report (e.g. for a PR comment)")
    try:
        a = ap.parse_args(argv)
        if a.cmd == "baseline" and not 0 <= a.margin < 1:
            raise DataError("--margin must be a fraction in [0, 1), e.g. 0.02")
        return cmd_baseline(a) if a.cmd == "baseline" else cmd_check(a)
    except DataError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
