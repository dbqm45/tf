#!/usr/bin/env python3
"""
A probe of an ES simulation scenario without a human and without a host: ready facilitator utterances from a trial file, rounds
through es_sim.py, participants as separate model calls without tools (`claude -p`), the coach at the end. It checks whether the
scenario works: whether hidden knowledge comes out, whether deliberate contradictions yield hot spots, whether the persona cards behave
as described, how many answers are invalid JSON. Paid — run only with the human's consent.

  es_probe.py --variant pelna|oszczedna [--scenario veterinary] [--probe <trial.json>] [--id <id>]
              [--coach full|light|none] [--budget-usd 2.5]

Trial file (default scenarios/<scenario>/trial.json):
  {"lines": ["<facilitator's utterance>", {"invite": "<persona id>"}, …],
   "expect": {"hidden": [{"fact": "…", "any": ["word", …]}],
              "contradictions": [{"name": "…", "hot_spot_any": ["word", …]}],
              "behaviour": [{"round": 1, "persona": "<id>", "speaks": true | "max_sentences": 1, "why": "…",
                             "skip_variants": [<variant-of-the-day no. from 0>, …]}]}}

Model: the ES_PROBE_CMD variable (a JSON list, e.g. a stub in tests) replaces `claude -p` without tools and without MCP; the script
adds `--model` and `--system-prompt`. Result: docs/training/es-sim/<id>/probe-report.md (+ the coach's debrief.md).
Exit code: 0 — all expectations met, 1 — not all, 2 — bad invocation, 3 — budget exceeded.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ES_SIM = HERE / "es_sim.py"
DEFAULT_CMD = ["claude", "-p", "--tools", "", "--strict-mcp-config", "--no-session-persistence", "--output-format", "json"]
MODELS = {"pelna": "sonnet", "oszczedna": "haiku"}
PARTICIPANT_SYS = ("You are a participant in a simulated Event Storming workshop. Play the person (or people) described in the "
                   "message exactly as the card and the rules say. Reply only with a JSON block in the given shape. "
                   "Do not comment on the simulation.")
COACH_SYS = ("You assess how the session was RUN, not the domain content. Input: the transcript, statistics (JSON from the "
             "script), the scenario brief (deliberate contradictions, expected pivotal events, who trains which anti-pattern). "
             "Light mode: only dominance, silent participants, unchecked language. Full mode: 10 facilitation anti-patterns, each "
             "green/yellow/red with evidence (round, quote). Participants react to the echo with a one-round delay. Do not start "
             "with praise. Format: a 3-sentence summary · an anti-pattern table · 3 strong moments and 3 things to work on · "
             "whether the facilitator confronted the deliberate contradictions · one quote. Also, because this is a scenario "
             "trial: whether the persona cards and the contradictions worked as the brief describes. Return only the debrief "
             "in Markdown.")
WRITE_FILE = re.compile(r"\n*Save (?:this JSON|the array) to the file `[^`]+` and reply(?: with one word)?: ok\.\s*$")
BAD_JSON = "missing or invalid JSON"


def sim(env: dict, *args: str) -> str:
    r = subprocess.run([sys.executable, str(ES_SIM), *args], capture_output=True, text=True, env=env)
    if r.returncode:
        sys.exit(f"✗ es_sim.py {args[0]}: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def call_model(system: str, prompt: str, model: str) -> tuple[str, float]:
    base = json.loads(os.environ["ES_PROBE_CMD"]) if os.environ.get("ES_PROBE_CMD") else DEFAULT_CMD
    with tempfile.TemporaryDirectory() as cwd:   # outside the project: no hooks and no project files
        r = subprocess.run([*base, "--model", model, "--system-prompt", system], input=prompt, capture_output=True,
                           text=True, cwd=cwd, timeout=600)
    try:
        out = json.loads(r.stdout)
        return str(out.get("result") or ""), float(out.get("total_cost_usd") or 0)
    except (ValueError, TypeError):
        return r.stdout, 0.0


def sentences(text: str) -> int:
    return len([s for s in re.split(r"[.!?…]+", text or "") if s.strip()])


def usd(x: float) -> str:
    return f"{x:.2f} USD"


def evaluate(st: dict, transcript: str, expect: dict) -> list[tuple[bool | None, str, str]]:
    low = transcript.lower()
    hs = " ".join(h["text"] for h in st.get("hot_spots", [])).lower()
    out = []
    for h in expect.get("hidden", []):
        ok = any(k.lower() in low for k in h["any"])
        out.append((ok, "hidden knowledge", h["fact"]))
    for c in expect.get("contradictions", []):
        ok = any(k.lower() in hs for k in c["hot_spot_any"])
        out.append((ok, "contradiction (hot spot)", c["name"]))
    rounds = {r["n"]: r for r in st.get("rounds", [])}
    for b in expect.get("behaviour", []):
        var = st.get("day_variant", {}).get(b["persona"])
        what = f"round {b['round']}, {b['persona']} (day variant {'—' if var is None else var + 1}): {b.get('why', '')}"
        if var in b.get("skip_variants", []):   # the card's variant of the day changes the temperament — the behaviour may differ
            out.append((None, "persona card", what + " (skipped for this day variant)"))
            continue
        d = (rounds.get(b["round"], {}).get("replies", {}).get(b["persona"], {}) or {}).get("dialogue", "")
        ok = bool(d.strip()) if b.get("speaks") else sentences(d) <= b.get("max_sentences", 0)
        out.append((ok, "persona card", what))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["pelna", "oszczedna"], required=True)
    ap.add_argument("--scenario", default="veterinary")
    ap.add_argument("--probe")
    ap.add_argument("--id")
    ap.add_argument("--coach", choices=["full", "light", "none"], default="full")
    ap.add_argument("--budget-usd", type=float, default=2.5)
    a = ap.parse_args()
    probe_path = Path(a.probe) if a.probe else SKILL / "scenarios" / a.scenario / "trial.json"
    try:
        probe = json.loads(probe_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"✗ trial file: {e}", file=sys.stderr)
        return 2
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    init = ["init", "--variant", a.variant, "--scenario", a.scenario] + (["--id", a.id] if a.id else [])
    sid = json.loads(sim(env, *init).splitlines()[0])["id"]
    sd = root / "docs" / "training" / "es-sim" / sid
    model, cost, calls, stopped = MODELS[a.variant], 0.0, 0, False
    for line in probe.get("lines", []):
        if isinstance(line, dict) and line.get("invite"):
            sim(env, "invite", "--id", sid, "--persona", line["invite"])
            continue
        plan = json.loads(sim(env, "round-begin", "--id", sid, "--text", str(line)))

        def one(c):
            pf = root / c["prompt_file"]
            prompt = WRITE_FILE.sub("\n\nReply with this JSON block only.", pf.read_text(encoding="utf-8"))
            text, usd_ = call_model(PARTICIPANT_SYS, prompt, model)
            (pf.parent / pf.name.replace(".prompt.md", ".reply.json")).write_text(text, encoding="utf-8")
            return usd_

        with ThreadPoolExecutor(max_workers=8) as ex:
            spent = list(ex.map(one, plan["calls"]))
        cost, calls = cost + sum(spent), calls + len(spent)
        sim(env, "round-end", "--id", sid)
        if cost > a.budget_usd:
            stopped = True
            break
    st = json.loads((sd / "state.json").read_text(encoding="utf-8"))
    transcript = (sd / "transcript.md").read_text(encoding="utf-8")
    if a.coach != "none" and not stopped:
        stats = sim(env, "stats", "--id", sid, "--json")
        brief = (SKILL / "scenarios" / st["scenario"] / "brief.md").read_text(encoding="utf-8")
        debrief, c_usd = call_model(COACH_SYS, f"Mode: {a.coach} (final).\n\n## Scenario brief\n{brief}\n\n"
                                               f"## Statistics\n{stats}\n\n## Transcript\n{transcript}", "sonnet")
        cost, calls = cost + c_usd, calls + 1
        (sd / "debrief.md").write_text(debrief, encoding="utf-8")
    checks = evaluate(st, transcript, probe.get("expect", {}))
    bad_json = transcript.count(BAD_JSON)
    silent = [p for p in st["present"]
              if not any((r.get("replies", {}).get(p, {}) or {}).get("dialogue", "").strip() for r in st["rounds"])]
    counted = [ok for ok, _, _ in checks if ok is not None]
    met = sum(counted)
    L = [f"# Scenario trial \"{st['scenario']}\": {sid}", "",
         f"Variant {a.variant} (participant model: {model}), rounds {st['round']}, model calls {calls}, "
         f"cost {usd(cost)}{'; stopped: budget exceeded' if stopped else ''}.",
         f"Events {len(st['events'])}, hot spots {len(st['hot_spots'])}, rejected stickies {len(st['rejected'])}, "
         f"invalid JSON: {bad_json}, people who never spoke: {', '.join(silent) or '—'}.", "",
         f"## Expectations ({met}/{len(counted)})", "| | Kind | Expectation |", "|---|---|---|"]
    L += [f"| {'—' if ok is None else '✓' if ok else '✗'} | {kind} | {what} |" for ok, kind, what in checks]
    L += ["", "Transcript: `transcript.md` · board: `board.md`" + (" · coach debrief: `debrief.md`" if (sd / "debrief.md").exists() else "")]
    (sd / "probe-report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:4] + [ln for ln in L[6:] if ln.startswith("| ✗")] + [f"Report: {sd / 'probe-report.md'}"]))
    if stopped:
        print(f"⚠ budget {usd(a.budget_usd)} exceeded; trial stopped after round {st['round']}")
        return 3
    return 0 if met == len(counted) else 1


if __name__ == "__main__":
    raise SystemExit(main())
