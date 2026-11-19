#!/usr/bin/env python3
"""
Measure Jev on the factory's data — BEFORE you enable it (requires TYPESAFE_API_KEY; cost on the order of cents).

  python3 .tf/factory/jev_calibration.py --routing [--limit 300] [--shuffle] [--target 0.9]
  python3 .tf/factory/jev_calibration.py --judge docs/evals/2026-10-02-sonnet.jsonl [--limit 100]

--routing  skill hinting on all evaluation scenarios: words only (the default hook) versus two-stage Jev
           (TypeSafe cookbook “skill suggestion”). Measures as in the cookbook: correct, wrong (a different skill hinted),
           unnecessary (a hint on a question that does not need that skill), missed. “no-trigger” questions
           expect a neighbor (the neighbor field) or no hint.
--judge    replays the saved answers from evaluation and compares the Jev grade (each requirement separately, uncertainty band
           0.30–0.70) with the grade the run already has. Shows agreement of confident grades and the share of uncertain ones (those in the cascade
           graded by haiku).
Thresholds tuned separately for each decision point (never the default 0.5): routing — the lowest “fits” threshold with precision
≥ --target; judge — the narrowest uncertainty band with confident-grade agreement ≥95% (labels: runs in which all
or none of the requirements were met). --shuffle: option order test (reversed skill list).
Recommendation: enable CLAUDE_SKILL_HINT_JEV=1 when Jev has fewer wrong and unnecessary hints than words at a similar
number of correct ones; `--judge jev` when agreement of confident grades is ≥95%. TypeSafe documentation: English works best,
other languages worse — hence measuring on Polish questions is necessary.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # engine in .tf/factory/ without __pycache__ (like node_modules — code only)
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"
TESTS = ROOT / "tests" if (ROOT / "tests" / "run_skill_evals.py").exists() else ROOT / ".claude" / "tests"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scenarios() -> list[dict]:
    out = []
    for f in sorted((TESTS / "skill_evals").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for s in d["scenarios"]:
            out.append({**s, "skill": d["skill"]})
    return out


def fit_band(points: list[tuple[float, bool]], target: float = 0.95, step: float = 0.05) -> dict:
    """Uncertainty band tuned on its own labels (instead of a fixed 0.30–0.70): the narrowest band [low, high] at
    which grades outside the band agree with the label in at least `target` cases. Without data or without a band
    meeting the goal → the client's default band (jev_client.LOW/HIGH)."""
    sys.path.insert(0, str(HOOKS))
    import jev_client as jev
    best = {"low": jev.LOW, "high": jev.HIGH, "agreement": None, "unsure": None, "n": len(points), "fitted": False}
    if not points:
        return best
    grid = [round(i * step, 4) for i in range(int(round(1 / step)) + 1)]
    for low in [g for g in grid if g <= 0.5]:
        for high in [g for g in grid if g >= 0.5]:
            sure = [(p > high, y) for p, y in points if p > high or p < low]
            if not sure:
                continue
            agree = sum(v == y for v, y in sure) / len(sure)
            unsure = len(points) - len(sure)
            if agree >= target and (best["unsure"] is None or unsure < best["unsure"]
                                    or (unsure == best["unsure"] and high - low < best["high"] - best["low"])):
                best = {"low": low, "high": high, "agreement": agree, "unsure": unsure, "n": len(points), "fitted": True}
    return best


def fit_threshold(points: list[tuple[float, bool]], target: float = 0.9, step: float = 0.05) -> dict:
    """One-sided threshold (routing: hint when p ≥ threshold): the lowest threshold at which correct hints
    make up at least `target` of the hinted ones. Coverage = the share of questions on which we hint anything."""
    out = {"threshold": None, "precision": None, "coverage": 0.0, "n": len(points)}
    cands = sorted({round(p, 4) for p, _ in points} | {round(i * step, 4) for i in range(int(round(1 / step)) + 1)})
    for th in cands:
        sel = [(p, y) for p, y in points if p >= th]
        hit = [y for _, y in sel]
        if hit and sum(hit) / len(hit) >= target:
            return {"threshold": min(p for p, _ in sel), "precision": sum(hit) / len(hit),
                    "coverage": len(hit) / len(points), "n": len(points)}
    return out


def order_sensitivity(pick, prompts: list[str], options: list) -> dict:
    """Option order test: the same choice after reversing the option list? `pick(prompt, options)` returns the chosen option
    (or a list). A changed choice = the model judges the position, not the content."""
    changed = 0
    for pr in prompts:
        a, b = pick(pr, list(options)), pick(pr, list(reversed(options)))
        changed += a != b
    return {"checked": len(prompts), "changed": changed}


def outcome(picked: list[str], expected: set[str]) -> str:
    if picked and set(picked) & expected:
        return "correct"
    if picked:
        return "unneeded" if not expected else "wrong"
    return "correct" if not expected else "missed"


def calibrate_routing(limit: int, shuffle: bool = False, target: float = 0.9) -> int:
    hint = load(HOOKS / "skill_hint.py", "skill_hint")
    items = hint.load_index()
    cases = scenarios()[:limit]
    routed, order = [], {"checked": 0, "changed": 0}
    stats = {"words": {}, "jev": {}}
    t0, spent = time.time(), 0.0
    for s in cases:
        if s["expect"] == "trigger":
            expected = {s["skill"], *(s.get("accept") or [])}
        else:
            expected = {s.get("neighbor"), *(s.get("accept") or [])} - {None, "brak"}
        words = [it["name"] for _, it in hint.select(s["prompt"], items)][:1]
        j = hint.jev_suggest(s["prompt"], items)
        if j is None:
            print("✗ Jev does not answer — check TYPESAFE_API_KEY and the network (python3 .claude/hooks/jev_client.py --check)")
            return 1
        jev_pick = [it["name"] for _, it in j]
        if j:   # the winner's score = p(„pasuje”) × 20; hints below the current threshold are discarded by the hook, so they are not visible
            routed.append((j[0][0] / 20, j[0][1]["name"] in expected))
        if shuffle:
            jr = hint.jev_suggest(s["prompt"], list(reversed(items)))
            if jr is not None:
                order["checked"] += 1
                order["changed"] += [it["name"] for _, it in jr] != jev_pick
        for k, picked in (("words", words), ("jev", jev_pick)):
            o = outcome(picked, expected)
            stats[k][o] = stats[k].get(o, 0) + 1
    log = ROOT / ".tf" / "logs" / "jev.jsonl"
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("ts", "") >= time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t0)):
                spent += r.get("cost") or 0
    n = len(cases)
    print(f"Skill hint on {n} scenarios (1st choice):")
    for k in ("words", "jev"):
        st = stats[k]
        print(f"  {k:<6} " + ", ".join(f"{o} {st.get(o, 0)} ({100 * st.get(o, 0) / max(n, 1):.0f}%)"
                                       for o in ("correct", "wrong", "unneeded", "missed")))
    th = fit_threshold(routed, target)
    if th["threshold"] is not None:
        print(f"Routing „fits” threshold fitted on labels: {th['threshold']:.2f} (precision {th['precision']:.0%}"
              f" at target {target:.0%}, hint on {th['coverage']:.0%} of questions; current JEV_FITS {hint.JEV_FITS:.2f})")
    else:
        print(f"No threshold gives precision {target:.0%} — keep words (the default hook)")
    if shuffle:
        print(f"Option order test: the choice changed in {order['changed']}/{order['checked']} questions after reversing "
              "the skill list (each change = rating the position, not the content)")
    print(f"Jev cost ≈ ${spent:.4f}, time {time.time() - t0:.0f} s")
    return 0


def calibrate_judge(jsonl: Path, limit: int, jev, ev) -> int:
    scen = {(s["skill"], s["id"]): s for s in scenarios()}
    rows = [json.loads(l) for l in jsonl.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("expect") == "trigger" and r.get("answer") and (r["skill"], r["id"]) in scen][:limit]
    agree = sure = unsure = 0
    cost = 0.0
    points = []
    for r in rows:
        s = scen[(r["skill"], r["id"])]
        groups = (s.get("checks") or {}).get("all") or []
        if not groups:
            continue
        reqs = s.get("rubric") if s.get("rubric") and len(s["rubric"]) == len(groups) else [ev.requirement(g) for g in groups]
        regex = [any(re.search(rx, r["answer"], re.I | re.S) for rx in g) for g in groups]
        qs = {f"w{i}": {"type": "noul", "instructions": "Does `answer` state the following, literally, in other words "
                        f"or with a synonym (the answer may be in Polish): {q}"} for i, q in enumerate(reqs)}
        a = jev.decide({"answer": r["answer"][:40000]}, qs, timeout=15)
        if not a:
            print(f"✗ no Jev answer for {r['skill']}#{r['id']} — stopping")
            return 1
        cost += a["_usage"]["cost"]
        ps = [jev.p_yes(a[f"w{i}"]) for i in range(len(reqs))]
        if r.get("checks_ok") or not (r.get("groups_met") or 0):   # confident label: everything met or nothing
            points += [(p, bool(r.get("checks_ok"))) for p in ps]
        verdicts = [jev.noul_verdict(p) for p in ps]
        if any(v is None for v in verdicts):
            unsure += 1
            continue
        sure += 1
        agree += all(v or rx for v, rx in zip(verdicts, regex)) == bool(r.get("checks_ok"))
    n = len(rows)
    print(f"Content rating: {n} answers; sure {sure} ({100 * sure / max(n, 1):.0f}%), agree with the run's rating "
          f"{agree}/{sure} ({100 * agree / max(sure, 1):.0f}%); unsure → haiku: {unsure}. Jev cost: ${cost:.4f}")
    band = fit_band(points)
    if band["fitted"]:
        print(f"Judge uncertainty band fitted on labels ({band['n']} requirements): {band['low']:.2f}–{band['high']:.2f}"
              f" (agreement {band['agreement']:.0%}, unsure {band['unsure']}); default {jev.LOW:.2f}–{jev.HIGH:.2f}")
    else:
        print(f"Too little data or no band gives 95% agreement — keeping {jev.LOW:.2f}–{jev.HIGH:.2f}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judge", type=Path)
    ap.add_argument("--routing", action="store_true")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--shuffle", action="store_true", help="order test: each routing question a second time with the reversed skill list (2× cost)")
    ap.add_argument("--target", type=float, default=0.9, help="target hint precision when fitting the routing threshold")
    args = ap.parse_args(argv[1:])
    sys.path.insert(0, str(HOOKS))
    import jev_client as jev
    if not jev.enabled():
        print("Set TYPESAFE_API_KEY (an environment variable, not a file in the repository).")
        return 2
    rc = 0
    if args.routing:
        rc |= calibrate_routing(args.limit, args.shuffle, args.target)
    if args.judge:
        rc |= calibrate_judge(args.judge, args.limit, jev, load(TESTS / "run_skill_evals.py", "run_skill_evals"))
    if not (args.judge or args.routing):
        print(__doc__)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
