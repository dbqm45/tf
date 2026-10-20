#!/usr/bin/env python3
"""
Raport zużycia tokenów per agent i model na podstawie .claude/logs/usage.jsonl.

  python3 factory/cost_report.py            # całość
  python3 factory/cost_report.py --days 7   # ostatnie 7 dni
  python3 factory/cost_report.py --delegation   # koszt delegowania wg klasy zadania (delegation.jsonl)

Pokazuje też dobór tierów: którzy wykonawcy byli eskalowani na mocniejszy model albo zgłaszali w raporcie
„Tier: za niski/za wysoki” — z podpowiedzią, gdzie zmienić domyślny tier.

Ceny ustaw w factory/config.yaml → prices_usd_per_mtok (bez nich raport pokazuje same tokeny).
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / ".claude" / "logs" / "usage.jsonl"
DELEG_LOG = ROOT / ".claude" / "logs" / "delegation.jsonl"


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
    """Gdzie zmienić domyślny tier agenta: rola persony albo agent wspólny."""
    if agent in (cfg.get("shared_agents") or {}):
        return f"factory/config.yaml → shared_agents.{agent}.tier"
    if "-" in agent:
        role = agent.split("-", 1)[1]
        if (ROOT / "factory" / "roles" / f"{role}.yaml").exists():
            return f"factory/roles/{role}.yaml → tier (albo parametr model przy delegowaniu)"
    return "factory/config.yaml → tiers / persona model_tier"


def tier_advice(records: list[dict], cfg: dict) -> list[str]:
    """Samoocena zespołu z danych: eskalacje (ten sam agent w jednej sesji na mocniejszym modelu) i linie
    „Tier: za niski/za wysoki” z raportów wykonawców."""
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
            out.append(f"• {agent}: w {s['escalated'] + s['low']}/{s['runs']} zadań model był za słaby (eskalacje: "
                       f"{s['escalated']}, „Tier: za niski”: {s['low']}) — podnieś domyślny tier: {where_tier(agent, cfg)}.")
        elif down >= 0.3:
            out.append(f"• {agent}: w {s['high']}/{s['runs']} zadań wykonawca ocenił model jako za mocny — obniż tier: "
                       f"{where_tier(agent, cfg)}.")
    return out


def record_cost(r: dict, prices: dict) -> float | None:
    p = prices.get(dominant(r.get("models") or {}) or "")
    if not p:
        return None
    return sum((r.get(k) or 0) * p.get(k, 0) for k in ("input", "output", "cache_read", "cache_write")) / 1e6


def delegation_summary(deleg: list[dict], usage: list[dict], prices: dict) -> list[dict]:
    """Delegowania wg klasy zadania (linia „Klasa: …” briefu): liczba, ile połączono z zużyciem wykonawcy
    (agent_id z SubagentStop), mediany tokenów, kosztu, długości briefu i raportu. Klasa None = brief bez klasy."""
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
    print(f"{'klasa':<14}{'n':>4}{'z logiem':>9}{'tok. (med.)':>13}{'USD (med.)':>12}{'USD suma':>10}{'brief':>7}{'raport':>8}")
    print("─" * 77)
    for r in rows:
        print(f"{r['klass'] or '(bez klasy)':<14}{r['n']:>4}{r['joined']:>9}{fmt(r['median_tokens'], ',.0f'):>13}"
              f"{fmt(r['median_usd'], '.3f'):>12}{fmt(r['total_usd'], '.2f'):>10}{fmt(r['median_brief'], '.0f'):>7}"
              f"{fmt(r['median_result'], '.0f'):>8}")
    print("─" * 77)
    print("Klasy wg core-cost-control §0; „z logiem” = połączone z zużyciem wykonawcy (SubagentStop po agent_id).\n"
          "Porównuj koszt klasy z tym, co sesja zapłaciłaby sama (czytanie tych plików w jej kontekście) — "
          "klasa droga przy krótkim raporcie i małym briefie to kandydat do robienia samemu.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0)
    ap.add_argument("--log", type=Path, default=LOG)
    ap.add_argument("--delegation", action="store_true", help="koszt delegowania wg klasy zadania")
    ap.add_argument("--delegation-log", type=Path, default=DELEG_LOG)
    args = ap.parse_args()

    if args.delegation:
        if not args.delegation_log.exists():
            print(f"Brak logu {args.delegation_log} — pojawi się po pierwszym wywołaniu narzędzia Agent z hookiem log_usage.")
            return 0
        cfg = yaml.safe_load((ROOT / "factory" / "config.yaml").read_text(encoding="utf-8"))
        since = datetime.now(timezone.utc) - timedelta(days=args.days) if args.days else None
        print_delegation(delegation_summary(read_jsonl(args.delegation_log, since), read_jsonl(args.log, since),
                                            cfg.get("prices_usd_per_mtok") or {}))
        return 0

    if not args.log.exists():
        print(f"Brak logu {args.log} — uruchom kilka sesji z hookiem log_usage.")
        return 0
    cfg = yaml.safe_load((ROOT / "factory" / "config.yaml").read_text(encoding="utf-8"))
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
            tips.append(f"• {name}: drogi model, a średnio tylko {avg_out:.0f} tokenów wyjścia/zadanie — rozważ tier std/fast.")
        if read_total > 200_000 and hit < 50:
            tips.append(f"• {name}: niski cache hit ({hit:.0f}%) — sprawdź, czy prompt/skille nie zmieniają się między wywołaniami.")
        if a["runs"] >= 3 and read_total / a["runs"] > 150_000:
            tips.append(f"• {name}: ~{read_total / a['runs'] / 1000:.0f}k tokenów wejścia na zadanie — węższe briefy, więcej pracy dla scout.")
    print("─" * 85)
    print(f"Szacowany koszt: {'$%.2f' % total_usd if prices else '— (uzupełnij prices_usd_per_mtok w config.yaml)'}")
    if tips:
        print("\nWskazówki:")
        print("\n".join(tips))
    advice = tier_advice(records, cfg)
    if advice:
        print("\nDobór tierów (eskalacje i samoocena wykonawców):")
        print("\n".join(advice))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
