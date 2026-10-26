#!/usr/bin/env python3
"""
Pasma kontrolne na metrykach PROD z ShipScope (tryb mode-pdi, F5): punkt poza 3σ to zdarzenie `metric.breached` do pdi.

  python3 .claude/skills/pdi-decisions/scripts/metric_watch.py check [--csv plik] [--days 120] [--baseline 30] \\
      [--recent 7] [--send]
      JSON {window, metrics: [{metric, side, tier, mean, sd, points, violations | note}], breaches, sent}
  python3 .claude/skills/pdi-decisions/scripts/metric_watch.py workflow install [--force]
      szablon .github/workflows/metric-watch.yml (raz dziennie: check --send)

Szereg: `--csv` albo ShipScope `GET $SHIPSCOPE_URL/api/service/v1/metrics?from&to&format=csv` z tokenem usługi
`$SHIPSCOPE_TOKEN` (shps_…). Poziomy liczy `control_band.py` ze skilla core-delivery-lifecycle. Reguła 1 (punkt poza
3σ, poziom act) w ostatnich `--recent` dniach szeregu → `metric.breached` (kontrakt pdi 0.4.0, ID
`tf-metric-<metryka>-<dzień>`); `--send` wysyła je podpisane na `$PDI_EVENTS_URL/events/tf` (`PDI_TF_SIGNING_SECRET`).
Metryki: METRICS niżej; nadpisanie w .claude/pdi-metrics.json ({"baseline", "recent", "service", "metrics"}).
Kod wyjścia: 0 — policzone (i wysłane), 1 — błąd (z podpowiedzią), 2 — złe wywołanie.
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
MAX_DAYS = 400  # ShipScope oddaje najwyżej 400 dni
# Kolumna szeregu ShipScope → strona, po której wzrost jest zły (dbqm45/evdt-service-shipscope server/lib/service-api.js).
METRICS = {
    "rollbacks": {"side": "upper"},
    "failed_deployments": {"side": "upper"},
    "lead_time_days_median": {"side": "upper"},
    "deployments": {"side": "lower"},
}
DEFAULTS = {"baseline": 30, "recent": 7, "service": None}


def control_band():
    if not BAND.is_file():
        raise Refused(f"brak {BAND} — skill core-delivery-lifecycle jest w rdzeniu; zainstaluj fabrykę ponownie")
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
            raise Refused(f"{CONFIG}: zły JSON ({e})") from e
        if not isinstance(custom, dict):
            raise Refused(f"{CONFIG}: oczekiwany obiekt JSON")
        cfg.update({k: v for k, v in custom.items() if k in ("baseline", "recent", "service", "metrics")})
    for name in ("baseline", "recent"):
        override = getattr(a, name)
        if override is not None:
            cfg[name] = override
        if not isinstance(cfg[name], int) or cfg[name] < (2 if name == "baseline" else 1):
            raise Refused(f"{name} musi być liczbą całkowitą (baseline ≥ 2, recent ≥ 1)")
    if not isinstance(cfg["metrics"], dict) or not cfg["metrics"]:
        raise Refused(f"{CONFIG}: metrics — obiekt {{kolumna: {{\"side\": \"upper\"}}}}")
    for column, spec in cfg["metrics"].items():
        if not isinstance(spec, dict) or spec.get("side", "both") not in ("both", "upper", "lower"):
            raise Refused(f"{CONFIG}: metrics.{column}.side — both, upper albo lower")
    return cfg


def fetch_csv(days: int) -> tuple[str, dict]:
    base = (os.environ.get("SHIPSCOPE_URL") or "").rstrip("/")
    token = os.environ.get("SHIPSCOPE_TOKEN") or ""
    if not base:
        raise Refused("brak SHIPSCOPE_URL — adres ShipScope (np. https://shipscope.example.com) albo plik: --csv metryki.csv")
    url = urllib.parse.urlsplit(base)
    if url.username or url.password or not (
            url.scheme == "https" or (url.scheme == "http" and url.hostname in LOCAL_HOSTS)):
        raise Refused("SHIPSCOPE_URL musi być https:// (http tylko dla localhost), bez loginu w adresie")
    if not token:
        raise Refused("brak SHIPSCOPE_TOKEN — token usługi shps_… z ShipScope: Settings → General → Service tokens")
    to = dt.datetime.now(dt.UTC).date()
    window = {"from": (to - dt.timedelta(days=min(days, MAX_DAYS) - 1)).isoformat(), "to": to.isoformat()}
    query = urllib.parse.urlencode({**window, "format": "csv"})
    req = urllib.request.Request(f"{base}/api/service/v1/metrics?{query}",
                                 headers={"authorization": f"Bearer {token}", "accept": "text/csv"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 — adres sprawdzony wyżej
            return resp.read().decode("utf-8"), window
    except urllib.error.HTTPError as e:
        raise Refused(f"ShipScope odpowiedział {e.code} na metryki — sprawdź SHIPSCOPE_TOKEN i jego workspace") from e
    except OSError as e:
        raise Refused(f"brak połączenia z ShipScope ({getattr(e, 'reason', e)})") from e


def read_rows(text: str) -> list[dict]:
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "date" not in rows[0]:
        raise Refused("szereg bez kolumny date — oczekiwany CSV z ShipScope (date,deployments,…)")
    return sorted(rows, key=lambda r: r["date"])


def evaluate_metric(band, rows: list[dict], column: str, side: str, baseline: int) -> dict:
    points = [(r["date"], float(r[column])) for r in rows if (r.get(column) or "").strip()]
    out = {"metric": column, "side": side, "tier": None, "points": len(points)}
    if len(points) <= baseline:
        return {**out, "note": f"za mało punktów: {len(points)}, linia bazowa potrzebuje {baseline} i co najmniej "
                               f"jednego punktu po niej"}
    try:
        result = band.evaluate([v for _, v in points], baseline, side)
    except ValueError as e:
        return {**out, "note": f"brak zmienności w linii bazowej — {e}" if "odchylenie" in str(e) else str(e)}
    violations = [{"date": points[v["index"]][0], "rule": v["rule"], "value": v["value"], "z": v["z"],
                   "opis": v["opis"]} for v in result["violations"]]
    return {**out, "tier": result["tier"], "mean": result["mean"], "sd": result["sd"], "violations": violations,
            "baseline": {"from": points[0][0], "to": points[baseline - 1][0]}}


def breach_event(m: dict, last_date: str, recent: int, service: str | None) -> dict | None:
    """Najnowszy punkt poza 3σ z ostatnich `recent` dni szeregu jako `metric.breached`, albo None."""
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
        "window": f"{v['date']} (linia bazowa {m['baseline']['from']}–{m['baseline']['to']})",
        "diagnosis": (f"reguła 1 (punkt poza 3σ): {value} wobec średniej {m['mean']} i σ {m['sd']} linii bazowej; "
                      f"poziom {m['tier']}, strona {m['side']}. Wykryte przez tf metric_watch.py na danych ShipScope."),
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
            raise Refused(f"nie da się przeczytać {a.csv} ({e.strerror})") from e
        window = None
    else:
        text, window = fetch_csv(a.days)
    rows = read_rows(text)
    missing = [c for c in cfg["metrics"] if c not in rows[0]]
    if missing:
        raise Refused(f"kolumny {', '.join(missing)} nie ma w szeregu (jest: {', '.join(k for k in rows[0] if k != 'date')}) "
                      f"— popraw metrics w {CONFIG}")
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
        raise Refused(f"{WORKFLOW} już istnieje — nie nadpisuję (--force, jeśli to celowe)")
    WORKFLOW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, WORKFLOW)
    print(f"✓ {WORKFLOW} — ustaw sekrety SHIPSCOPE_TOKEN i PDI_TF_SIGNING_SECRET oraz zmienne SHIPSCOPE_URL i "
          f"PDI_EVENTS_URL")
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
