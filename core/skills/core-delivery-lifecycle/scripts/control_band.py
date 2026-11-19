#!/usr/bin/env python3
"""
Control bands for production and process metrics (phase 9 — maintenance). Detection is deterministic;
the model is called only when this script returns a level higher than „ok”.

  python3 control_band.py metric.csv --baseline 30 [--column name] [--side both|upper|lower] [--format json|text]

Input: CSV with a header (by default the first numeric column) or one number per line. The first N points
(--baseline) are the baseline: mean and standard deviation come from it. Western Electric rules are checked on
the points after the baseline:
  1. a point outside 3σ                           → level act      (the agent may act: PR, approved runbook)
  2. 2 of 3 consecutive outside 2σ on one side   → level diagnose (the agent diagnoses read-only)
  3. 4 of 5 consecutive outside 1σ on one side   → level log      (write only)
  4. 8 consecutive on one side of the mean       → level log
--side upper: only increases count (e.g. the share of 5xx errors), lower — only decreases (e.g. the share of successful deployments).
The levels and thresholds are a proposal from „The AI-Native SDLC Playbook” (Anthropic, 2026); change them in the project configuration.
Exit code: 0 — result computed, 2 — bad data (e.g. zero standard deviation of the baseline). Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

TIER_OF_RULE = {1: "act", 2: "diagnose", 3: "log", 4: "log"}
ORDER = ["ok", "log", "diagnose", "act"]
RULE_TEXT = {1: "a point outside 3σ", 2: "2 of 3 consecutive points outside 2σ on the same side",
             3: "4 of 5 consecutive points outside 1σ on the same side", 4: "8 consecutive points on one side of the mean"}


def read_values(path: Path, column: str | None) -> list[float]:
    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    if not rows:
        return []
    idx = 0
    start = 0
    try:
        float(rows[0][0])
    except (ValueError, IndexError):
        start = 1
        if column:
            idx = rows[0].index(column)
    return [float(r[idx]) for r in rows[start:] if len(r) > idx and r[idx].strip()]


def counts(side: str, z: float) -> int:
    """+1 / -1 for the side we count; 0 for the ignored side."""
    s = 1 if z > 0 else -1 if z < 0 else 0
    if side == "upper" and s < 0 or side == "lower" and s > 0:
        return 0
    return s


def evaluate(values: list[float], baseline: int, side: str = "both") -> dict:
    base = values[:baseline]
    if len(base) < 2:
        raise ValueError("the baseline must have at least 2 points")
    mean = statistics.fmean(base)
    sd = statistics.pstdev(base)
    if sd == 0:
        raise ValueError("the standard deviation of the baseline is 0 — make the baseline longer or change the metric")
    pts = values[baseline:]
    z = [(v - mean) / sd for v in pts]
    violations = []

    def add(rule: int, i: int) -> None:
        if not any(v["rule"] == rule and v["index"] == baseline + i for v in violations):
            violations.append({"rule": rule, "index": baseline + i, "value": pts[i], "z": round(z[i], 2),
                               "description": RULE_TEXT[rule]})

    for i, zi in enumerate(z):
        if counts(side, zi) and abs(zi) > 3:
            add(1, i)
        for rule, window, need, limit in ((2, 3, 2, 2.0), (3, 5, 4, 1.0)):
            if i + 1 >= window:
                w = z[i + 1 - window:i + 1]
                for s in (1, -1):
                    if sum(1 for x in w if counts(side, x) == s and abs(x) > limit) >= need:
                        add(rule, i)
        if i + 1 >= 8:
            w = [counts(side, x) for x in z[i - 7:i + 1]]
            if all(s == 1 for s in w) or all(s == -1 for s in w):
                add(4, i)
    tier = max((TIER_OF_RULE[v["rule"]] for v in violations), key=ORDER.index, default="ok")
    return {"mean": round(mean, 6), "sd": round(sd, 6), "evaluated": len(pts), "side": side,
            "violations": sorted(violations, key=lambda v: (v["index"], v["rule"])), "tier": tier}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Control bands for a metric (Western Electric rules).")
    ap.add_argument("file", type=Path)
    ap.add_argument("--baseline", type=int, required=True, help="number of first points that make the baseline")
    ap.add_argument("--column")
    ap.add_argument("--side", choices=["both", "upper", "lower"], default="both")
    ap.add_argument("--format", choices=["json", "text"], default="json")
    a = ap.parse_args(argv[1:])
    try:
        result = evaluate(read_values(a.file, a.column), a.baseline, a.side)
    except (ValueError, OSError) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 2
    if a.format == "text":
        print(f"tier: {result['tier']} · mean {result['mean']} · σ {result['sd']} · points {result['evaluated']}")
        for v in result["violations"]:
            print(f"  rule {v['rule']} ({v['description']}): point {v['index']}, value {v['value']}, z = {v['z']}")
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
