#!/usr/bin/env python3
"""Tests of the ai-evals/scripts/eval_gate.py script — the eval gate for CI: a threshold from the baseline spread,
regression tasks, a budget (docs/plans/2026-11-19-bramka-ewaluacji-i-zatwierdzone-modele.md in the factory repository).

The script runs no model. It reads the results of a product eval run (JSON Lines, one line per trial: `id`, `passed`,
optionally `layer`, `cost_usd`, `trial`), computes the spread and the threshold from several baseline runs, and judges
a candidate run: release / investigate / hold. Expected values in these tests are computed by hand.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "ai-evals" / "scripts" / "eval_gate.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, timeout=60,
                          encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)


def write_run(path: Path, passed: int, total: int = 20, **extra) -> Path:
    """A run: `total` tasks with one trial each, the first `passed` of them pass (t01…)."""
    lines = [json.dumps({"id": f"t{i:02d}", "passed": i <= passed, **extra}) for i in range(1, total + 1)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_lines(path: Path, rows: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return path


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    r = run("--help")
    check(r.returncode == 0 and "baseline" in r.stdout and "check" in r.stdout and "exit code" in r.stdout.lower(),
          f"EG-1: --help describes the commands and exit codes: {r.returncode} {r.stdout[:200]} {r.stderr[-200:]}")

    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        # Baseline: three runs of 20 tasks, 14, 15, 16 passed → 0.70 / 0.75 / 0.80; margin 0.04 → threshold 0.66.
        runs = [write_run(d / f"base{i}.jsonl", n) for i, n in enumerate((14, 15, 16), 1)]
        base = d / "baseline.json"
        r = run("baseline", *runs, "--margin", "0.04", "--out", base)
        data = json.loads(base.read_text(encoding="utf-8")) if base.is_file() else {}
        s = data.get("success", {})
        check(r.returncode == 0 and data.get("runs") == 3 and abs(s.get("min", 0) - 0.70) < 1e-9
              and abs(s.get("max", 0) - 0.80) < 1e-9 and abs(s.get("mean", 0) - 0.75) < 1e-9,
              f"EG-2: baseline from three runs: min 0.70, max 0.80, mean 0.75: rc={r.returncode} {data} {r.stderr[-200:]}")
        check(abs(data.get("threshold", 0) - 0.66) < 1e-9 and abs(data.get("margin", 0) - 0.04) < 1e-9,
              f"EG-2b: threshold = lower bound of the spread − margin = 0.66: {data.get('threshold')}")
        check(data.get("stable_tasks") == [f"t{i:02d}" for i in range(1, 15)],
              f"EG-2c: stable tasks = passed in every baseline run (t01–t14): {data.get('stable_tasks')}")

        # A candidate inside the baseline spread → release
        r = run("check", write_run(d / "ok.jsonl", 15), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("verdict") == "release" and abs(out.get("success", 0) - 0.75) < 1e-9,
              f"EG-3: 0.75 with a baseline of 0.70–0.80 → release, exit 0: rc={r.returncode} {r.stdout[:300]} {r.stderr[-200:]}")

        # Below the lower bound of the spread but inside the margin → investigate (exit 0; with --strict exit 1).
        # 13 of 20 passed = 0.65 < 0.66 would already be a hold, so the run has 50 tasks and 0.68.
        r = run("check", write_run(d / "edge.jsonl", 34, 50), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("verdict") == "investigate" and abs(out.get("success", 0) - 0.68) < 1e-9,
              f"EG-4: 0.68 (below min 0.70, above the threshold 0.66) → investigate, exit 0: rc={r.returncode} {r.stdout[:300]}")
        r = run("check", d / "edge.jsonl", "--baseline", base, "--strict")
        check(r.returncode == 1, f"EG-4b: --strict turns investigate into exit 1: rc={r.returncode}")

        # Below the threshold → hold
        r = run("check", write_run(d / "bad.jsonl", 12), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("verdict") == "hold" and any("threshold" in x for x in out.get("reasons", [])),
              f"EG-5: 0.60 below the threshold 0.66 → hold, exit 1, a reason naming the threshold: rc={r.returncode} {r.stdout[:300]}")
        check(out.get("regressions") == ["t13", "t14"],
              f"EG-5b: regressions = tasks stable in the baseline that now fail: {out.get('regressions')}")

        # A task of the regression layer must not fail even when the overall result is fine
        rows = [{"id": f"t{i:02d}", "passed": i <= 16} for i in range(1, 21)]
        rows[17] = {"id": "t18", "passed": False, "layer": "regression"}
        r = run("check", write_lines(d / "reg.jsonl", rows), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("verdict") == "hold" and out.get("regression_layer_failures") == ["t18"],
              f"EG-6: a failed regression-layer task → hold despite 0.80: rc={r.returncode} {r.stdout[:300]}")

        # Budget
        r = run("check", write_run(d / "cost.jsonl", 15, cost_usd=0.16), "--baseline", base, "--budget-usd", "3", "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("verdict") == "hold" and abs(out.get("cost_usd", 0) - 3.2) < 1e-9
              and any("budget" in x for x in out.get("reasons", [])),
              f"EG-7: cost 3.20 USD with a budget of 3 → hold: rc={r.returncode} {r.stdout[:300]}")
        r = run("check", d / "cost.jsonl", "--baseline", base, "--budget-usd", "4", "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("verdict") == "release", f"EG-7b: cost inside the budget → release: {r.stdout[:200]}")
        r = run("check", d / "ok.jsonl", "--baseline", base, "--budget-usd", "4", "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("verdict") == "investigate" and out.get("cost_usd") is None
              and any("cost" in x for x in out.get("reasons", [])),
              f"EG-7c: a budget given but results without cost → investigate (not \"inside the budget\"): rc={r.returncode} {r.stdout[:300]}")

        # pass^k and pass@k: 4 tasks × 3 trials: a 3/3, b 2/3, c 0/3, d 1/3 → success 6/12 = 0.5; pass^3 = 1/4; pass@3 = 3/4
        trials = {"a": [1, 1, 1], "b": [1, 0, 1], "c": [0, 0, 0], "d": [0, 1, 0]}
        rows = [{"id": k, "passed": bool(v), "trial": i + 1} for k, vs in trials.items() for i, v in enumerate(vs)]
        one = d / "k-base.json"
        run("baseline", write_lines(d / "k.jsonl", rows), "--out", one)
        r = run("check", d / "k.jsonl", "--baseline", one, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(out.get("k") == 3 and out.get("tasks") == 4 and out.get("attempts") == 12
              and abs(out.get("success", 0) - 0.5) < 1e-9 and abs(out.get("pass_all_k", 0) - 0.25) < 1e-9
              and abs(out.get("pass_any_k", 0) - 0.75) < 1e-9,
              f"EG-8: success 0.5, pass^3 0.25, pass@3 0.75: {r.stdout[:300]} {r.stderr[-200:]}")

        # A baseline from one run works but warns about the spread
        r = run("baseline", runs[0], "--out", d / "single.json")
        check(r.returncode == 0 and (d / "single.json").is_file() and "3" in r.stdout and "spread" in r.stdout.lower(),
              f"EG-9: a baseline from one run → a warning about the spread (3–5 repetitions): rc={r.returncode} {r.stdout[:300]}")

        # A task set different from the baseline → the comparison is uncertain
        r = run("check", write_run(d / "other.jsonl", 20, 25), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(out.get("verdict") == "investigate" and any("task set" in x for x in out.get("reasons", [])),
              f"EG-10: a task set different from the baseline → investigate with a reason: {r.stdout[:300]}")

        # Bad data → exit 2, no verdict (an empty file is not "0 failures")
        (d / "empty.jsonl").write_text("", encoding="utf-8")
        (d / "broken.jsonl").write_text('{"id": "t01", "passed": true}\nthis is not json\n', encoding="utf-8")
        (d / "nofield.jsonl").write_text('{"id": "t01"}\n', encoding="utf-8")
        for name, what in (("empty.jsonl", "an empty file"), ("broken.jsonl", "a non-JSON line"), ("nofield.jsonl", "no passed field"),
                           ("missing.jsonl", "no file")):
            r = run("check", d / name, "--baseline", base, "--json")
            check(r.returncode == 2 and "verdict" not in r.stdout,
                  f"EG-11: {what} → exit 2 without a verdict: rc={r.returncode} {r.stdout[:120]} {r.stderr[:160]}")
        r = run("check", d / "ok.jsonl", "--baseline", d / "no-baseline.json")
        check(r.returncode == 2, f"EG-11b: no baseline file → exit 2: rc={r.returncode}")

        # Text report and the report file
        report = d / "report.md"
        r = run("check", d / "bad.jsonl", "--baseline", base, "--report", report)
        text = report.read_text(encoding="utf-8") if report.is_file() else ""
        check("Verdict: hold" in r.stdout and "60" in r.stdout and "70" in r.stdout and "80" in r.stdout,
              f"EG-12: text: the verdict, the result and the baseline spread in percent: {r.stdout[:400]}")
        check("hold" in text and "t13" in text and "t14" in text,
              f"EG-12b: --report writes a report with the verdict and the regressions: {text[:300]}")

    print(f"test_eval_gate: {total - len(fails)}/{total} OK")
    for f in fails:
        print(f"  ✗ {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
