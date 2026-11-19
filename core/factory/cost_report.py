#!/usr/bin/env python3
"""
Token usage report per agent and model, based on .tf/logs/usage.jsonl.

  python3 .tf/factory/cost_report.py            # everything
  python3 .tf/factory/cost_report.py --days 7   # last 7 days
  python3 .tf/factory/cost_report.py --delegation   # delegation cost by task class (delegation.jsonl)

Also shows tier selection: which executors were escalated to a stronger model or reported in the report
„Tier: za niski/za wysoki” (tier too low/too high) — with a hint where to change the default tier.

Set prices in .tf/config/config.yaml → prices_usd_per_mtok (without them the report shows tokens only).
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from pathlib import Path

try:
    import yaml
except ImportError:  # bundled PyYAML copy (.tf/factory/_vendor)
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
    import yaml

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / ".tf" / "logs" / "usage.jsonl"
DELEG_LOG = ROOT / ".tf" / "logs" / "delegation.jsonl"



def _tf_config(root: Path) -> dict:
    """Factory configuration: the engine default with project overrides (.tf/config/config.yaml) — packs.load_config."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_packs_cfg", root / ".tf" / "factory" / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_config(root)

def family(model: str) -> str:
    m = model.lower()
    for f in ("haiku", "sonnet", "opus", "fable", "mythos"):
        if f in m:
            return f
    return model


RANK = {"haiku": 0, "sonnet": 1, "opus": 2, "fable": 3, "mythos": 3}


def dominant(models: dict) -> str | None:
    return family(max(models, key=models.get)) if models else None


def where_tier(agent: str, cfg: dict) -> str:
    """Where to change an agent's default tier: a persona role or a shared agent."""
    if agent in (cfg.get("shared_agents") or {}):
        return f".tf/config/config.yaml → shared_agents.{agent}.tier"
    if "-" in agent:
        role = agent.split("-", 1)[1]
        if (ROOT / ".tf" / "config" / "roles" / f"{role}.yaml").exists():
            return f".tf/config/roles/{role}.yaml → tier (or the model parameter when delegating)"
    return ".tf/config/config.yaml → tiers / persona model_tier"


def tier_advice(records: list[dict], cfg: dict) -> list[str]:
    """Team self-assessment from the data: escalations (the same agent in one session on a stronger model) and lines
    „Tier: za niski/za wysoki” from executor reports."""
    stats = defaultdict(lambda: {"runs": 0, "escalated": 0, "low": 0, "high": 0})
    last: dict[tuple, int] = {}
    for r in sorted(records, key=lambda r: r.get("ts", "")):
        if r.get("event") != "SubagentStop":
            continue
        agent, fam = r["agent"], dominant(r.get("models") or {})
        s = stats[agent]
        s["runs"] += 1
        fb = r.get("tier_feedback")
        s["low"] += fb == "niski"
        s["high"] += fb == "wysoki"
        key = (r.get("session"), agent)
        if fam in RANK:
            if key in last and RANK[fam] > last[key]:
                s["escalated"] += 1
            last[key] = RANK[fam]
    out = []
    for agent, s in sorted(stats.items()):
        if s["runs"] < 3:
            continue
        up = (s["escalated"] + s["low"]) / s["runs"]
        down = s["high"] / s["runs"]
        if up >= 0.3:
            out.append(f"• {agent}: in {s['escalated'] + s['low']}/{s['runs']} tasks the model was too weak (escalations: "
                       f"{s['escalated']}, „Tier: too low”: {s['low']}) — raise the default tier: {where_tier(agent, cfg)}.")
        elif down >= 0.3:
            out.append(f"• {agent}: in {s['high']}/{s['runs']} tasks the executor rated the model as too strong — lower the tier: "
                       f"{where_tier(agent, cfg)}.")
    return out


def record_cost(r: dict, prices: dict) -> float | None:
    p = prices.get(dominant(r.get("models") or {}) or "")
    if not p:
        return None
    return sum((r.get(k) or 0) * p.get(k, 0) for k in ("input", "output", "cache_read", "cache_write")) / 1e6


def delegation_summary(deleg: list[dict], usage: list[dict], prices: dict) -> list[dict]:
    """Delegations by task class (the brief's „Klasa: …” line): count, how many were joined with executor usage
    (agent_id from SubagentStop), medians of tokens, cost, brief length and report. Class None = brief without a class."""
    by_id = {r["agent_id"]: r for r in usage if r.get("event") == "SubagentStop" and r.get("agent_id")}
    groups: dict = defaultdict(list)
    for d in deleg:
        groups[d.get("klass")].append(d)

    def med(xs):
        xs = [x for x in xs if x is not None]
        return statistics.median(xs) if xs else None

    rows = []
    for klass, ds in groups.items():
        used = [by_id[d["agent_id"]] for d in ds if d.get("agent_id") in by_id]
        costs = [record_cost(u, prices) for u in used]
        rows.append({
            "klass": klass, "n": len(ds), "joined": len(used),
            "median_tokens": med([sum(u.get(k) or 0 for k in ("input", "output", "cache_read", "cache_write"))
                                  for u in used]),
            "median_usd": med(costs), "total_usd": sum(c for c in costs if c is not None) if used else None,
            "median_brief": med([d.get("brief_chars") for d in ds]),
            "median_result": med([d.get("result_chars") for d in ds]),
        })
    return sorted(rows, key=lambda r: (r["klass"] is None, -r["n"]))


def read_jsonl(path: Path, since: datetime | None) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines() if path.exists() else []:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if since and r.get("ts") and datetime.fromisoformat(r["ts"]) < since:
            continue
        out.append(r)
    return out


def print_delegation(rows: list[dict]) -> None:
    def fmt(v, spec):
        return format(v, spec) if v is not None else "—"
    print(f"{'class':<14}{'n':>4}{'with log':>9}{'tok. (med.)':>13}{'USD (med.)':>12}{'USD sum':>10}{'brief':>7}{'report':>8}")
    print("─" * 77)
    for r in rows:
        print(f"{r['klass'] or '(no class)':<14}{r['n']:>4}{r['joined']:>9}{fmt(r['median_tokens'], ',.0f'):>13}"
              f"{fmt(r['median_usd'], '.3f'):>12}{fmt(r['total_usd'], '.2f'):>10}{fmt(r['median_brief'], '.0f'):>7}"
              f"{fmt(r['median_result'], '.0f'):>8}")
    print("─" * 77)
    print("Classes per core-cost-control §0; „with log” = joined with the executor's usage (SubagentStop by agent_id).\n"
          "Compare the cost of a class with what the session would pay itself (reading these files in its own context) — "
          "an expensive class with a short report and a small brief is a candidate to do yourself.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0)
    ap.add_argument("--log", type=Path, default=LOG)
    ap.add_argument("--delegation", action="store_true", help="delegation cost by task class")
    ap.add_argument("--delegation-log", type=Path, default=DELEG_LOG)
    args = ap.parse_args()

    if args.delegation:
        if not args.delegation_log.exists():
            print(f"No log {args.delegation_log} — it appears after the first Agent tool call with the log_usage hook.")
            return 0
        cfg = _tf_config(ROOT)
        since = datetime.now(timezone.utc) - timedelta(days=args.days) if args.days else None
        print_delegation(delegation_summary(read_jsonl(args.delegation_log, since), read_jsonl(args.log, since),
                                            cfg.get("prices_usd_per_mtok") or {}))
        return 0

    if not args.log.exists():
        print(f"No log {args.log} — run a few sessions with the log_usage hook.")
        return 0
    cfg = _tf_config(ROOT)
    prices = cfg.get("prices_usd_per_mtok") or {}
    since = datetime.now(timezone.utc) - timedelta(days=args.days) if args.days else None

    agg = defaultdict(lambda: {"runs": 0, "input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "models": defaultdict(int)})
    records = []
    for line in args.log.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if since and datetime.fromisoformat(r["ts"]) < since:
            continue
        records.append(r)
        a = agg[r["agent"]]
        a["runs"] += 1
        for k in ("input", "output", "cache_read", "cache_write"):
            a[k] += r.get(k, 0)
        for m, out in (r.get("models") or {}).items():
            a["models"][family(m)] += out or 1

    def cost(a) -> float | None:
        fam = max(a["models"], key=a["models"].get) if a["models"] else None
        p = prices.get(fam) if fam else None
        if not p:
            return None
        return (a["input"] * p.get("input", 0) + a["output"] * p.get("output", 0)
                + a["cache_read"] * p.get("cache_read", 0) + a["cache_write"] * p.get("cache_write", 0)) / 1e6

    rows = sorted(agg.items(), key=lambda kv: -(kv[1]["input"] + kv[1]["output"] + kv[1]["cache_read"]))
    print(f"{'agent':<24}{'model':<9}{'runs':>5}{'input':>11}{'output':>10}{'cache rd':>11}{'hit%':>6}{'USD':>9}")
    print("─" * 85)
    total_usd, tips = 0.0, []
    for name, a in rows:
        fam = max(a["models"], key=a["models"].get) if a["models"] else "?"
        read_total = a["input"] + a["cache_read"] + a["cache_write"]
        hit = 100 * a["cache_read"] / read_total if read_total else 0
        c = cost(a)
        total_usd += c or 0
        print(f"{name:<24}{fam:<9}{a['runs']:>5}{a['input']:>11,}{a['output']:>10,}{a['cache_read']:>11,}{hit:>5.0f}%"
              f"{(f'{c:.2f}' if c is not None else '—'):>9}")
        avg_out = a["output"] / max(a["runs"], 1)
        if fam in ("opus", "fable", "mythos") and avg_out < 1500 and a["runs"] >= 3:
            tips.append(f"• {name}: expensive model, but on average only {avg_out:.0f} output tokens/task — consider tier std/fast.")
        if read_total > 200_000 and hit < 50:
            tips.append(f"• {name}: low cache hit ({hit:.0f}%) — check that the prompt/skills do not change between calls.")
        if a["runs"] >= 3 and read_total / a["runs"] > 150_000:
            tips.append(f"• {name}: ~{read_total / a['runs'] / 1000:.0f}k input tokens per task — narrower briefs, more work for scout.")
    print("─" * 85)
    print(f"Estimated cost: {'$%.2f' % total_usd if prices else '— (fill in prices_usd_per_mtok in config.yaml)'}")
    if tips:
        print("\nTips:")
        print("\n".join(tips))
    advice = tier_advice(records, cfg)
    if advice:
        print("\nTier choice (escalations and executor self-assessment):")
        print("\n".join(advice))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
