#!/usr/bin/env python3
"""
Control bands on PROD metrics from ShipScope (mode-pdi, F5): a point beyond 3σ is a `metric.breached` event to pdi.

  python3 .claude/skills/pdi-decisions/scripts/metric_watch.py check [--csv file] [--days 120] [--baseline 30] \\
      [--recent 7] [--send]
      JSON {window, metrics: [{metric, side, tier, mean, sd, points, violations | note}], breaches, sent}
  python3 .claude/skills/pdi-decisions/scripts/metric_watch.py workflow install [--force]
      template .github/workflows/metric-watch.yml (once a day: check --send)

Series: `--csv` or ShipScope `GET $SHIPSCOPE_URL/api/service/v1/metrics?from&to&format=csv` with the service token
`$SHIPSCOPE_TOKEN` (shps_…). The levels are computed by `control_band.py` from the core-delivery-lifecycle skill. Rule 1 (a point beyond
3σ, level act) in the last `--recent` days of the series → `metric.breached` (pdi contract 0.9.0, ID
`tf-metric-<metric>-<day>`); `--send` sends them signed to `$PDI_EVENTS_URL/events/tf` (`PDI_TF_SIGNING_SECRET`).
Metrics: METRICS below; override in .claude/pdi-metrics.json ({"baseline", "recent", "service", "metrics"}).
Exit code: 0 — computed (and sent), 1 — error (with a hint), 2 — bad invocation.
"""
import argparse
import csv
import datetime as dt
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True  # bez __pycache__ w .claude/skills
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase_run import CONTRACT_VERSION, LOCAL_HOSTS, Refused, post_event  # noqa: E402

CONFIG = Path(".claude") / "pdi-metrics.json"
TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "metric-watch.yml"
WORKFLOW = Path(".github") / "workflows" / "metric-watch.yml"
BAND = Path(__file__).resolve().parents[2] / "core-delivery-lifecycle" / "scripts" / "control_band.py"
MAX_DAYS = 400  # ShipScope returns at most 400 days
# ShipScope series column → the side on which an increase is bad (dbqm45/evdt-service-shipscope server/lib/service-api.js).
METRICS = {
    "rollbacks": {"side": "upper"},
    "failed_deployments": {"side": "upper"},
    "lead_time_days_median": {"side": "upper"},
    "deployments": {"side": "lower"},
}
DEFAULTS = {"baseline": 30, "recent": 7, "service": None}


def control_band():
    if not BAND.is_file():
        raise Refused(f"{BAND} is missing — the core-delivery-lifecycle skill is part of the core; reinstall the factory")
    spec = importlib.util.spec_from_file_location("control_band", BAND)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def settings(a) -> dict:
    cfg = dict(DEFAULTS, metrics=METRICS)
    if CONFIG.is_file():
        try:
            custom = json.loads(CONFIG.read_text(encoding="utf-8"))
        except ValueError as e:
            raise Refused(f"{CONFIG}: bad JSON ({e})") from e
        if not isinstance(custom, dict):
            raise Refused(f"{CONFIG}: expected a JSON object")
        cfg.update({k: v for k, v in custom.items() if k in ("baseline", "recent", "service", "metrics")})
    for name in ("baseline", "recent"):
        override = getattr(a, name)
        if override is not None:
            cfg[name] = override
        if not isinstance(cfg[name], int) or cfg[name] < (2 if name == "baseline" else 1):
            raise Refused(f"{name} must be an integer (baseline ≥ 2, recent ≥ 1)")
    if not isinstance(cfg["metrics"], dict) or not cfg["metrics"]:
        raise Refused(f"{CONFIG}: metrics — an object {{column: {{\"side\": \"upper\"}}}}")
    for column, spec in cfg["metrics"].items():
        if not isinstance(spec, dict) or spec.get("side", "both") not in ("both", "upper", "lower"):
            raise Refused(f"{CONFIG}: metrics.{column}.side — both, upper or lower")
    return cfg


def fetch_csv(days: int) -> tuple[str, dict]:
    base = (os.environ.get("SHIPSCOPE_URL") or "").rstrip("/")
    token = os.environ.get("SHIPSCOPE_TOKEN") or ""
    if not base:
        raise Refused("SHIPSCOPE_URL is not set — the ShipScope address (e.g. https://shipscope.example.com) or a file: --csv metrics.csv")
    url = urllib.parse.urlsplit(base)
    if url.username or url.password or not (
            url.scheme == "https" or (url.scheme == "http" and url.hostname in LOCAL_HOSTS)):
        raise Refused("SHIPSCOPE_URL must be https:// (http only for localhost), with no login in the address")
    if not token:
        raise Refused("SHIPSCOPE_TOKEN is not set — a shps_… service token from ShipScope: Settings → General → Service tokens")
    to = dt.datetime.now(dt.UTC).date()
    window = {"from": (to - dt.timedelta(days=min(days, MAX_DAYS) - 1)).isoformat(), "to": to.isoformat()}
    query = urllib.parse.urlencode({**window, "format": "csv"})
    req = urllib.request.Request(f"{base}/api/service/v1/metrics?{query}",
                                 headers={"authorization": f"Bearer {token}", "accept": "text/csv"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 — address checked above
            return resp.read().decode("utf-8"), window
    except urllib.error.HTTPError as e:
        raise Refused(f"ShipScope answered {e.code} to the metrics request — check SHIPSCOPE_TOKEN and its workspace") from e
    except OSError as e:
        raise Refused(f"cannot connect to ShipScope ({getattr(e, 'reason', e)})") from e


def read_rows(text: str) -> list[dict]:
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "date" not in rows[0]:
        raise Refused("the series has no date column — expected a CSV from ShipScope (date,deployments,…)")
    return sorted(rows, key=lambda r: r["date"])


def evaluate_metric(band, rows: list[dict], column: str, side: str, baseline: int) -> dict:
    points = [(r["date"], float(r[column])) for r in rows if (r.get(column) or "").strip()]
    out = {"metric": column, "side": side, "tier": None, "points": len(points)}
    if len(points) <= baseline:
        return {**out, "note": f"too few points: {len(points)}, the baseline needs {baseline} and at least "
                               f"one point after it"}
    try:
        result = band.evaluate([v for _, v in points], baseline, side)
    except ValueError as e:
        return {**out, "note": f"no variation in the baseline — {e}" if "standard deviation" in str(e) else str(e)}
    violations = [{"date": points[v["index"]][0], "rule": v["rule"], "value": v["value"], "z": v["z"],
                   "description": v["description"]} for v in result["violations"]]
    return {**out, "tier": result["tier"], "mean": result["mean"], "sd": result["sd"], "violations": violations,
            "baseline": {"from": points[0][0], "to": points[baseline - 1][0]}}


def breach_event(m: dict, last_date: str, recent: int, service: str | None) -> dict | None:
    """The newest point beyond 3σ from the last `recent` days of the series as `metric.breached`, or None."""
    since = (dt.date.fromisoformat(last_date) - dt.timedelta(days=recent - 1)).isoformat()
    hits = [v for v in m.get("violations", []) if v["rule"] == 1 and v["date"] >= since]
    if not hits:
        return None
    v = hits[-1]
    sign = 1 if v["z"] > 0 else -1
    threshold = round(m["mean"] + sign * 3 * m["sd"], 6)
    value = int(v["value"]) if float(v["value"]).is_integer() else v["value"]
    payload = {
        "metric": m["metric"],
        "value": value,
        "threshold": threshold,
        "window": f"{v['date']} (baseline {m['baseline']['from']}–{m['baseline']['to']})",
        "diagnosis": (f"rule 1 (point outside 3σ): {value} against the baseline mean {m['mean']} and σ {m['sd']}; "
                      f"tier {m['tier']}, side {m['side']}. Detected by tf metric_watch.py on ShipScope data."),
    }
    if service:
        payload["service"] = service
    slug = re.sub(r"[^A-Za-z0-9._-]", "-", m["metric"])
    return {"id": f"tf-metric-{slug}-{v['date']}", "type": "metric.breached",
            "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": "tf",
            "contract_version": CONTRACT_VERSION, "payload": payload}


def cmd_check(a) -> int:
    cfg = settings(a)
    band = control_band()
    if a.csv:
        try:
            text = Path(a.csv).read_text(encoding="utf-8")
        except OSError as e:
            raise Refused(f"cannot read {a.csv} ({e.strerror})") from e
        window = None
    else:
        text, window = fetch_csv(a.days)
    rows = read_rows(text)
    missing = [c for c in cfg["metrics"] if c not in rows[0]]
    if missing:
        raise Refused(f"the series has no column {', '.join(missing)} (it has: {', '.join(k for k in rows[0] if k != 'date')}) "
                      f"— fix metrics in {CONFIG}")
    window = window or {"from": rows[0]["date"], "to": rows[-1]["date"]}
    metrics = [evaluate_metric(band, rows, c, s.get("side", "both"), cfg["baseline"]) for c, s in cfg["metrics"].items()]
    breaches = [e for e in (breach_event(m, rows[-1]["date"], cfg["recent"], cfg["service"]) for m in metrics
                            if m.get("tier") == "act") if e]
    sent = [{"id": e["id"], "status": post_event(e)} for e in breaches] if a.send else []
    print(json.dumps({"window": window, "metrics": metrics, "breaches": breaches, "sent": sent}, ensure_ascii=False,
                     indent=2))
    return 0


def cmd_workflow_install(a) -> int:
    if WORKFLOW.exists() and not a.force:
        raise Refused(f"{WORKFLOW} already exists — not overwriting it (use --force if that is intended)")
    WORKFLOW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, WORKFLOW)
    print(f"✓ {WORKFLOW} — set the SHIPSCOPE_TOKEN and PDI_TF_SIGNING_SECRET secrets and the SHIPSCOPE_URL and "
          f"PDI_EVENTS_URL variables")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--csv")
    c.add_argument("--days", type=int, default=120)
    c.add_argument("--baseline", type=int)
    c.add_argument("--recent", type=int)
    c.add_argument("--send", action="store_true")
    wf = sub.add_parser("workflow").add_subparsers(dest="action", required=True)
    wf.add_parser("install").add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    try:
        return {"check": cmd_check, "workflow": cmd_workflow_install}[a.cmd](a)
    except Refused as e:
        print(f"✗ {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
