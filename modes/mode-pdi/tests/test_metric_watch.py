#!/usr/bin/env python3
"""Testy pasm kontrolnych na metrykach z ShipScope (tryb mode-pdi, skill pdi-decisions, scripts/metric_watch.py):
poziomy z control_band.py, zdarzenie metric.breached zgodne z kontraktem pdi, odczyt z ShipScope i wysyłka do pdi
(lokalne serwery HTTP), konfiguracja i szablon workflow. python3 .claude/tests/test_metric_watch.py"""
import datetime as dt
import hashlib
import hmac
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REL = Path(".claude") / "skills" / "pdi-decisions" / "scripts" / "metric_watch.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL).is_file()), None)
SCRIPT = ROOT / REL if ROOT else None
FIX = Path(__file__).resolve().parent / "fixtures" / "pdi-contract"
SECRET = "sekret-tf"
TOKEN = "shps_test_token"
HEADER = "date,deployments,failed_deployments,rollbacks,lead_time_days_median,lead_time_count"
START = dt.date(2026, 9, 1)


def series(n: int = 40, **override) -> str:
    """CSV jak z ShipScope: n dni od 2026-09-01; kolumny ze zmiennością w linii bazowej, override: {kolumna: {dzień: v}}."""
    rows = [HEADER]
    for i in range(n):
        day = {"deployments": 4 + i % 3, "failed_deployments": i % 2, "rollbacks": i % 2,
               "lead_time_days_median": "" if i % 5 == 4 else 2 + i % 3, "lead_time_count": 0 if i % 5 == 4 else 1}
        for col, values in override.items():
            if i in values:
                day[col] = values[i]
        rows.append(",".join([(START + dt.timedelta(days=i)).isoformat()] +
                             [str(day[c]) for c in HEADER.split(",")[1:]]))
    return "\n".join(rows) + "\n"


def run(args, cwd, **env):
    base = {k: v for k, v in os.environ.items() if not k.startswith(("SHIPSCOPE_", "PDI_"))}
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=60,
                          env={**base, "PYTHONDONTWRITEBYTECODE": "1", **env})


def jl(r):
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


class Server(BaseHTTPRequestHandler):
    got: list = []
    status = 200
    body = b""

    def _record(self, body: bytes = b"") -> None:
        Server.got.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "body": body})
        self.send_response(Server.status)
        self.end_headers()
        self.wfile.write(Server.body)

    def do_GET(self):  # noqa: N802
        self._record()

    def do_POST(self):  # noqa: N802
        self._record(self.rfile.read(int(self.headers["content-length"])))

    def log_message(self, *a):
        pass


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if SCRIPT is None:
        print(f"✗ brak skryptu {REL}")
        return 1
    example = json.loads((FIX / "event-metric.breached.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as t:
        repo = Path(t)
        csv = repo / "metryki.csv"

        # --- poziomy i zdarzenie ---
        csv.write_text(series(rollbacks={39: 9}), encoding="utf-8")
        r = run(["check", "--csv", str(csv)], repo)
        out = jl(r) or {}
        by = {m["metric"]: m for m in out.get("metrics", [])}
        check(r.returncode == 0 and set(by) == {"rollbacks", "failed_deployments", "lead_time_days_median",
                                                 "deployments"}, f"M-1: cztery metryki domyślne: {r.stdout}{r.stderr}")
        rb = by.get("rollbacks", {})
        check(rb.get("tier") == "act" and rb.get("side") == "upper"
              and any(v["rule"] == 1 and v["date"] == "2026-10-10" for v in rb.get("violations", [])),
              f"M-2: skok rollbacków → act, naruszenie z datą: {rb}")
        breaches = out.get("breaches", [])
        ev = breaches[0] if breaches else {}
        check(len(breaches) == 1 and set(ev) == set(example) and ev.get("type") == "metric.breached"
              and ev.get("source") == "tf" and ev.get("contract_version") == example["contract_version"]
              and ev.get("id") == "tf-metric-rollbacks-2026-10-10",
              f"M-3: jedno zdarzenie w kopercie kontraktu, stałe ID: {ev}")
        p = ev.get("payload", {})
        check(p.get("metric") == "rollbacks" and p.get("value") == 9 and isinstance(p.get("threshold"), float)
              and p["threshold"] < 9 and "3σ" in p.get("diagnosis", "") and "2026-10-10" in p.get("window", "")
              and set(p) <= {"metric", "value", "threshold", "window", "service", "change", "diagnosis"},
              f"M-4: treść zdarzenia: wartość, próg średnia + 3σ, okno, diagnoza: {p}")
        check(out.get("sent") == [], f"M-5: bez --send nic nie wysłane: {out.get('sent')}")

        csv.write_text(series(rollbacks={i: 0 for i in range(40)}), encoding="utf-8")
        r = run(["check", "--csv", str(csv)], repo)
        rb = {m["metric"]: m for m in (jl(r) or {}).get("metrics", [])}.get("rollbacks", {})
        check(r.returncode == 0 and rb.get("tier") is None and "zmienno" in rb.get("note", ""),
              f"M-6: same zera w linii bazowej → uwaga, nie błąd: {rb} {r.stdout}")
        csv.write_text(series(n=20), encoding="utf-8")
        r = run(["check", "--csv", str(csv)], repo)
        notes = [m.get("note", "") for m in (jl(r) or {}).get("metrics", [])]
        check(r.returncode == 0 and notes and all("punkt" in n for n in notes),
              f"M-7: za mało punktów → uwaga przy każdej metryce: {r.stdout}")
        csv.write_text(series(n=50, rollbacks={32: 9}), encoding="utf-8")
        r = run(["check", "--csv", str(csv)], repo)
        out = jl(r) or {}
        rb = {m["metric"]: m for m in out.get("metrics", [])}.get("rollbacks", {})
        check(rb.get("tier") == "act" and out.get("breaches") == [],
              f"M-8: naruszenie sprzed ostatnich 7 dni → widoczne, bez zdarzenia: {out.get('breaches')}")
        csv.write_text(series(deployments={39: 0}), encoding="utf-8")
        r = run(["check", "--csv", str(csv)], repo)
        evs = [e for e in (jl(r) or {}).get("breaches", []) if e["payload"]["metric"] == "deployments"]
        check(len(evs) == 1 and evs[0]["payload"]["value"] == 0 and evs[0]["payload"]["threshold"] > 0,
              f"M-9: spadek wdrożeń (lower) → próg średnia − 3σ: {r.stdout}")

        # --- konfiguracja ---
        cfg = repo / ".claude" / "pdi-metrics.json"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps({"service": "sklep", "metrics": {"rollbacks": {"side": "upper"}}}), encoding="utf-8")
        csv.write_text(series(rollbacks={39: 9}), encoding="utf-8")
        r = run(["check", "--csv", str(csv)], repo)
        out = jl(r) or {}
        check([m["metric"] for m in out.get("metrics", [])] == ["rollbacks"]
              and out["breaches"][0]["payload"].get("service") == "sklep",
              f"M-10: konfiguracja wybiera metryki i nazywa usługę: {r.stdout}{r.stderr}")
        cfg.write_text(json.dumps({"metrics": {"drift": {"side": "upper"}}}), encoding="utf-8")
        r = run(["check", "--csv", str(csv)], repo)
        check(r.returncode == 1 and "drift" in r.stdout and "pdi-metrics.json" in r.stdout,
              f"M-11: kolumna spoza CSV → błąd z podpowiedzią: {r.stdout}")
        cfg.write_text(json.dumps({"metrics": {"rollbacks": {"side": "w bok"}}}), encoding="utf-8")
        r = run(["check", "--csv", str(csv)], repo)
        check(r.returncode == 1 and "side" in r.stdout, f"M-12: zła strona → błąd: {r.stdout}")
        cfg.unlink()

        # --- odczyt z ShipScope ---
        srv = HTTPServer(("127.0.0.1", 0), Server)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        try:
            Server.got, Server.status, Server.body = [], 200, series(rollbacks={39: 9}).encode()
            r = run(["check", "--days", "40"], repo, SHIPSCOPE_URL=url, SHIPSCOPE_TOKEN=TOKEN)
            got = Server.got[0] if Server.got else {}
            today = dt.datetime.now(dt.UTC).date()
            frm = (today - dt.timedelta(days=39)).isoformat()
            check(r.returncode == 0 and got.get("path") == f"/api/service/v1/metrics?from={frm}&to={today}&format=csv"
                  and got["headers"].get("authorization") == f"Bearer {TOKEN}" and len((jl(r) or {})["breaches"]) == 1,
                  f"M-13: szereg z ShipScope (ścieżka, okno, Bearer): {got.get('path')} {r.stdout}{r.stderr}")
            check(TOKEN not in r.stdout + r.stderr, "M-14: token ShipScope nie trafia do wyjścia")
            Server.got, Server.status, Server.body = [], 401, b'{"error":"Unauthorized"}'
            r = run(["check"], repo, SHIPSCOPE_URL=url, SHIPSCOPE_TOKEN=TOKEN)
            check(r.returncode == 1 and "401" in r.stdout and TOKEN not in r.stdout + r.stderr,
                  f"M-15: 401 z ShipScope → błąd bez tokenu: {r.stdout}")
            r = run(["check"], repo)
            check(r.returncode == 1 and "SHIPSCOPE_URL" in r.stdout and "--csv" in r.stdout,
                  f"M-16: bez SHIPSCOPE_URL → błąd z podpowiedzią: {r.stdout}")
            r = run(["check"], repo, SHIPSCOPE_URL="http://shipscope.example.com", SHIPSCOPE_TOKEN=TOKEN)
            check(r.returncode == 1 and "https" in r.stdout, f"M-17: http poza localhost → błąd: {r.stdout}")
            r = run(["check"], repo, SHIPSCOPE_URL=url)
            check(r.returncode == 1 and "SHIPSCOPE_TOKEN" in r.stdout, f"M-18: bez tokenu → błąd: {r.stdout}")

            # --- wysyłka do pdi ---
            Server.got, Server.status, Server.body = [], 202, b'{"status": "created"}'
            r = run(["check", "--csv", str(csv), "--send"], repo, PDI_EVENTS_URL=url, PDI_TF_SIGNING_SECRET=SECRET)
            got = Server.got[0] if Server.got else {}
            h = got.get("headers", {})
            body = got.get("body", b"")
            ts = h.get("x-pdi-timestamp", "")
            sig = "v1=" + hmac.new(SECRET.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
            check(r.returncode == 0 and got.get("path") == "/events/tf" and h.get("x-pdi-event") == "metric.breached"
                  and h.get("x-pdi-signature") == sig and json.loads(body or b"{}").get("id") == "tf-metric-rollbacks-2026-10-10"
                  and (jl(r) or {}).get("sent") == [{"id": "tf-metric-rollbacks-2026-10-10", "status": 202}],
                  f"M-19: --send → podpisane metric.breached na /events/tf: {got.get('path')} {r.stdout}{r.stderr}")
            check(SECRET not in r.stdout + r.stderr, "M-20: sekret nie trafia do wyjścia")
            r = run(["check", "--csv", str(csv), "--send"], repo, PDI_EVENTS_URL=url)
            check(r.returncode == 1 and "PDI_TF_SIGNING_SECRET" in r.stdout, f"M-21: --send bez sekretu → błąd: {r.stdout}")
            Server.got, Server.status = [], 400
            r = run(["check", "--csv", str(csv), "--send"], repo, PDI_EVENTS_URL=url, PDI_TF_SIGNING_SECRET=SECRET)
            check(r.returncode == 1 and "400" in r.stdout, f"M-22: odmowa pdi → błąd z kodem: {r.stdout}")
        finally:
            srv.shutdown()

        # --- szablon workflow ---
        r = run(["workflow", "install"], repo)
        wf = repo / ".github" / "workflows" / "metric-watch.yml"
        text = wf.read_text(encoding="utf-8") if wf.is_file() else ""
        check(r.returncode == 0 and "metric_watch.py check --send" in text and "schedule:" in text
              and "SHIPSCOPE_TOKEN" in text and "PDI_TF_SIGNING_SECRET" in text,
              f"M-23: workflow install kopiuje szablon: {r.stdout}")
        r = run(["workflow", "install"], repo)
        check(r.returncode == 1 and "--force" in r.stdout, f"M-24: bez nadpisania: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów pasm kontrolnych (metric_watch.py)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
