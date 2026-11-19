#!/usr/bin/env python3
"""
Cost statistics per day, week or month from .tf/logs/usage.jsonl (the log_usage hook) and the git history.

  python3 .tf/factory/cost_stats.py                       # weeks (last 8)
  python3 .tf/factory/cost_stats.py --period day --last 14
  python3 .tf/factory/cost_stats.py --period month --json
  python3 .tf/factory/cost_stats.py --usd-pln 3.65        # rate set manually (e.g. offline)
  --log <usage.jsonl> · --repo-root <repository to count changes in> · --config <config.yaml>

Per period: sessions and runs, tokens (input, output, cache read and write), model share in % of tokens, cost
in USD (`prices_usd_per_mtok` prices from .tf/config/config.yaml; an exact model identifier takes precedence over the family)
and in PLN at the **NBP average rate from table A** at the time of calculation (api.nbp.pl; remembered per day in
~/.cache/claude-team-factory/, offline the last known rate, marked as such). A record's input and cache tokens are split
between models in proportion to their output tokens (the log records output per model) — an approximation.

Effectiveness: changes (feat/fix commits in the repository), cost per change, rework (a fix of a file that a feat
added in the same period), cache share of input, „Tier: za niski” per 100 executor runs.
Expensive or cheap (objectively, no hourly rates): cost per change against its own history (band median ± 3·MAD,
from 4 periods) and a comparison with the “everything on Opus” (what model selection gave) and “no cache” (what the cache gave) variants.
With a subscription (Pro/Max) the cost is equivalent to API prices, not actual spend. Log gaps (commits after the
last entry, e.g. a session without hooks) are marked — the cost is then understated.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import statistics
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # engine in .tf/factory/ without __pycache__ (like node_modules — code only)
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NBP_URL = "https://api.nbp.pl/api/exchangerates/rates/a/usd/?format=json"
FAMILIES = ("haiku", "sonnet", "opus", "fable", "mythos")
TYPES = ("input", "output", "cache_read", "cache_write")



def _tf_config(root: Path) -> dict:
    """Factory configuration: the engine default with project overrides (.tf/config/config.yaml) — packs.load_config."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_packs_cfg", root / ".tf" / "factory" / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_config(root)

def family(model: str) -> str:
    m = model.lower()
    f = next((f for f in FAMILIES if f in m), "?")
    return "fable" if f == "mythos" else f


def ts(v) -> dt.datetime | None:
    try:
        t = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def period_key(t: dt.datetime, period: str) -> str:
    if period == "day":
        return t.date().isoformat()
    if period == "month":
        return f"{t.year:04d}-{t.month:02d}"
    y, w, _ = t.isocalendar()
    return f"{y:04d}-W{w:02d}"


def price(model: str, prices: dict) -> dict | None:
    return prices.get(model) or prices.get(family(model))


def record_cost(r: dict, prices: dict) -> dict:
    models = {m: v for m, v in (r.get("models") or {}).items() if v} or {"?": 1}
    tot = sum(models.values())
    out = {"usd": 0.0, "usd_opus": 0.0, "usd_no_cache": 0.0, "tokens": defaultdict(float)}
    opus = prices.get("opus") or {}
    for m, v in models.items():
        share = v / tot
        p = price(m, prices) or {}
        n = {k: (r.get(k) or 0) * share for k in TYPES}
        out["tokens"][family(m)] += sum(n.values())
        out["usd"] += sum(n[k] * p.get(k, 0) for k in TYPES) / 1e6
        out["usd_opus"] += sum(n[k] * opus.get(k, 0) for k in TYPES) / 1e6
        out["usd_no_cache"] += ((n["input"] + n["cache_read"] + n["cache_write"]) * p.get("input", 0)
                                + n["output"] * p.get("output", 0)) / 1e6
    out["tokens"] = dict(out["tokens"])
    return out


def aggregate(records: list[dict], prices: dict, period: str) -> list[dict]:
    agg: dict[str, dict] = {}
    for r in records:
        t = ts(r.get("ts"))
        if not t:
            continue
        k = period_key(t, period)
        a = agg.setdefault(k, {"period": k, "sessions": set(), "runs": 0, "subagent_runs": 0, "tier_low": 0,
                               **{x: 0 for x in TYPES}, "fam": defaultdict(float),
                               "usd": 0.0, "usd_all_opus": 0.0, "usd_no_cache": 0.0})
        a["sessions"].add(r.get("session"))
        a["runs"] += 1
        a["subagent_runs"] += r.get("event") == "SubagentStop"
        a["tier_low"] += "niski" in str(r.get("tier_feedback") or "")
        for x in TYPES:
            a[x] += r.get(x) or 0
        c = record_cost(r, prices)
        for f, n in c["tokens"].items():
            a["fam"][f] += n
        a["usd"] += c["usd"]
        a["usd_all_opus"] += c["usd_opus"]
        a["usd_no_cache"] += c["usd_no_cache"]
    rows = []
    for k in sorted(agg):
        a = agg[k]
        tot = sum(a["fam"].values())
        inp = a["input"] + a["cache_read"] + a["cache_write"]
        rows.append({**{x: a[x] for x in ("period", "runs", "subagent_runs", "tier_low", *TYPES)},
                     "sessions": len(a["sessions"]),
                     "models_pct": {f: 100 * n / tot for f, n in sorted(a["fam"].items())} if tot else {},
                     "cache_pct": 100 * a["cache_read"] / inp if inp else 0.0,
                     "usd": a["usd"], "usd_all_opus": a["usd_all_opus"], "usd_no_cache": a["usd_no_cache"]})
    return rows


def parse_nbp(data: dict) -> tuple[float, str, str]:
    r = (data.get("rates") or [{}])[-1]
    return float(r["mid"]), str(r.get("no", "")), str(r.get("effectiveDate", ""))


def _fetch_nbp() -> dict:
    req = urllib.request.Request(NBP_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def usd_pln(cache_dir: Path, now: dt.datetime | None = None, fetch=None, override: float | None = None) -> dict | None:
    """Average USD/PLN rate from NBP table A: from memory (same day), fetched, or the last known (stale)."""
    if override:
        return {"rate": float(override), "source": "manual", "table": None, "date": None}
    now = now or dt.datetime.now(dt.timezone.utc)
    f = cache_dir / "nbp-usd.json"
    try:
        cached = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cached = None
    if cached and str(cached.get("fetched_at", ""))[:10] == now.date().isoformat():
        return {**cached, "source": "NBP, table A", "stale": False}
    try:
        rate, table, date = parse_nbp((fetch or _fetch_nbp)())
    except Exception:
        return {**cached, "source": "NBP, table A", "stale": True} if cached else None
    rec = {"rate": rate, "table": table, "date": date, "fetched_at": now.isoformat()}
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(rec), encoding="utf-8")
    except OSError:
        pass
    return {**rec, "source": "NBP, table A", "stale": False}


def band(values: list[float]) -> list[str]:
    """Control band: median ± 3·(1.4826·MAD) — values outside the band are “expensive” / “cheap” against its own history."""
    if len(values) < 4:
        return ["too little data"] * len(values)
    med = statistics.median(values)
    sigma = max(1.4826 * statistics.median(abs(v - med) for v in values), 0.05 * abs(med), 1e-12)
    return ["expensive" if v > med + 3 * sigma else "cheap" if v < med - 3 * sigma else "normal" for v in values]


def changes(repo: Path, period: str) -> dict[str, dict]:
    """Changes (feat/fix commits) and rework (a fix of a file added by a feat in the same period) per period."""
    try:
        r = subprocess.run(["git", "-C", str(repo), "log", "--reverse", "--format=\x1e%cI\x1f%s", "--name-only"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if r.returncode != 0:
        return {}
    out: dict[str, dict] = {}
    feat_files: dict[str, set] = defaultdict(set)
    for block in r.stdout.split("\x1e")[1:]:
        head, *files = block.strip("\n").split("\n")
        when, _, subject = head.partition("\x1f")
        t = ts(when)
        m = re.match(r"(feat|fix)(\([^)]*\))?!?:", subject)
        if not t or not m:
            continue
        k = period_key(t, period)
        o = out.setdefault(k, {"changes": 0, "rework": 0})
        o["changes"] += 1
        files = [f for f in files if f.strip()]
        if m.group(1) == "feat":
            feat_files[k].update(files)
        elif any(f in feat_files[k] for f in files):
            o["rework"] += 1
    return out


def last_commit(repo: Path) -> dt.datetime | None:
    r = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%cI"], capture_output=True, text=True)
    return ts(r.stdout.strip()) if r.returncode == 0 else None


def pl(x: float | None, nd: int = 2) -> str:
    return "—" if x is None else f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


def render(rep: dict) -> str:
    rate = rep["rate"]
    if not rate:
        kurs = "Rate: none (no network and no saved rate) — PLN not computed; pass --usd-pln."
    elif rate["source"] == "manual":
        kurs = f"Rate: 1 USD = {pl(rate['rate'], 4)} PLN (set by hand)."
    else:
        kurs = (f"Rate: 1 USD = {pl(rate['rate'], 4)} PLN — NBP average rate, table A no. {rate['table']} of {rate['date']}"
                + (" (last known — no network)" if rate.get("stale") else "") + ".")
    out = [f"# Cost statistics ({rep['period_name']}, periods: {len(rep['periods'])})", "", kurs,
           f"Prices: as of {rep['prices_checked']} (.tf/config/config.yaml → prices_usd_per_mtok). With a subscription (Pro/Max) "
           "this is a cost equal to API prices, not real spending.", ""]
    if rep.get("gap"):
        out += [f"**Incomplete data:** last log entry {rep['gap']['last_log'][:16]}, last commit "
                f"{rep['gap']['last_commit'][:16]} — part of the work has no trace in the logs (e.g. a session without factory hooks); "
                "costs are too low.", ""]
    out += ["## Tokens and cost", "| Period | Sessions | Runs | Input | Output | Cache read | Cache write | USD | PLN |",
            "|---|---|---|---|---|---|---|---|---|"]
    for p in rep["periods"]:
        out.append(f"| {p['period']} | {p['sessions']} | {p['runs']} | {pl(p['input'], 0)} | {pl(p['output'], 0)} | "
                   f"{pl(p['cache_read'], 0)} | {pl(p['cache_write'], 0)} | {pl(p['usd'])} | {pl(p.get('pln'))} |")
    fams = sorted({f for p in rep["periods"] for f in p["models_pct"]})
    out += ["", "## Model share (% of tokens)", "| Period | " + " | ".join(fams) + " |", "|---|" + "---|" * len(fams)]
    for p in rep["periods"]:
        out.append(f"| {p['period']} | " + " | ".join(f"{pl(p['models_pct'].get(f, 0), 0)}%" for f in fams) + " |")
    out += ["", "## Effectiveness", "| Period | Changes (feat/fix) | PLN per change | Rework | Cache in input | "
            "„Tier too low” per 100 runs |", "|---|---|---|---|---|---|"]
    for p in rep["periods"]:
        tier = 100 * p["tier_low"] / p["subagent_runs"] if p["subagent_runs"] else None
        out.append(f"| {p['period']} | {p['changes']} | {pl(p.get('pln_per_change'))} | "
                   f"{pl(p.get('rework_pct'), 0) + '%' if p['changes'] else '—'} | {pl(p['cache_pct'], 0)}% | {pl(tier, 1)} |")
    cur = "PLN" if rep["rate"] else "USD"
    out += ["", f"## Expensive or cheap ({cur})", "| Period | Cost per change | Against history | All on Opus | Without cache | "
            "Savings from model choice | Savings from cache |", "|---|---|---|---|---|---|---|"]
    k = rep["rate"]["rate"] if rep["rate"] else 1.0
    for p in rep["periods"]:
        out.append(f"| {p['period']} | {pl(p['usd_per_change'] * k if p.get('usd_per_change') else None)} | {p['band']} | "
                   f"{pl(p['usd_all_opus'] * k)} | {pl(p['usd_no_cache'] * k)} | {pl((p['usd_all_opus'] - p['usd']) * k)} | "
                   f"{pl((p['usd_no_cache'] - p['usd']) * k)} |")
    out += ["", "How to read: „Against history” compares the cost per change with the band median ± 3·MAD of the periods shown "
                "(from 4) — „expensive” is a signal for a retrospective (core-agent-retro), not a verdict. The variants show what "
                "the same work would cost on Opus only and without cache; a small saving from model choice means that "
                "most of the work ran on the most expensive model."]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv[1:])
    for a in it:
        if a in ("--period", "--last", "--log", "--repo-root", "--usd-pln", "--config"):
            opts[a] = next(it, "")
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    period = opts.get("--period") or "week"
    if period not in ("day", "week", "month"):
        print("✗ --period day|week|month")
        return 2
    log = Path(opts.get("--log") or ROOT / ".tf" / "logs" / "usage.jsonl")
    repo = Path(opts.get("--repo-root") or ROOT)
    try:
        try:
            import yaml
        except ImportError:  # bundled PyYAML copy (.tf/factory/_vendor)
            sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
            import yaml
        cfg = (yaml.safe_load(Path(opts["--config"]).read_text(encoding="utf-8")) or {}) if opts.get("--config") \
            else _tf_config(ROOT)
    except ImportError:
        print("✗ PyYAML is missing (pip install pyyaml) — it is needed for the prices in .tf/config/config.yaml.")
        return 2
    prices = cfg.get("prices_usd_per_mtok") or {}
    records = []
    if log.is_file():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    if not records:
        print(f"No entries in {log} — the statistics come from the log_usage hook (a session started in the repository directory).")
        return 0
    periods = aggregate(records, prices, period)
    n = int(opts.get("--last") or {"day": 14, "week": 8, "month": 6}[period])
    periods = periods[-n:]
    ch = changes(repo, period)
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "claude-team-factory"
    try:
        override = float(str(opts["--usd-pln"]).replace(",", ".")) if opts.get("--usd-pln") else None
    except ValueError:
        print("✗ --usd-pln: a number, e.g. 3.65")
        return 2
    rate = usd_pln(base, override=override)
    k = rate["rate"] if rate else None
    for p in periods:
        c = ch.get(p["period"], {"changes": 0, "rework": 0})
        p["changes"], p["rework"] = c["changes"], c["rework"]
        p["rework_pct"] = 100 * c["rework"] / c["changes"] if c["changes"] else None
        p["usd_per_change"] = p["usd"] / c["changes"] if c["changes"] else None
        p["pln"] = p["usd"] * k if k else None
        p["pln_per_change"] = p["usd_per_change"] * k if k and p["usd_per_change"] else None
    last_log = max((t for t in (ts(r.get("ts")) for r in records) if t), default=None)
    lc = last_commit(repo)
    gap = {"last_log": last_log.isoformat(), "last_commit": lc.isoformat()} \
        if last_log and lc and lc > last_log + dt.timedelta(hours=1) else None
    for p in periods:      # from the period of the last log entry the cost is understated, while changes are counted in full
        p["incomplete"] = bool(gap) and p["period"] >= period_key(last_log, period)
        if p["incomplete"]:
            p["band"] = "incomplete data"
    with_change = [p for p in periods if p["usd_per_change"] and not p["incomplete"]]
    for p, lab in zip(with_change, band([p["usd_per_change"] for p in with_change])):
        p["band"] = lab
    for p in periods:
        p.setdefault("band", "no changes")
    rep = {"period": period, "period_name": {"day": "day", "week": "week", "month": "month"}[period],
           "prices_checked": str(cfg.get("prices_checked") or "?"), "rate": rate, "gap": gap, "periods": periods}
    print(json.dumps(rep, ensure_ascii=False, indent=1) if opts.get("--json") else render(rep), end="\n" if opts.get("--json") else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
