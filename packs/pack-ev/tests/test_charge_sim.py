#!/usr/bin/env python3
"""Testy symulatora ładowarki OCPP 1.6J (skill dom-ev-simulation-testing): scenariusze, awarie, log dla analizatora, kody wyjścia."""
import asyncio
import importlib.util
import json
import socket
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPTS = ROOT / ".claude" / "skills" / "dom-ev-simulation-testing" / "scripts"
SIM = SCRIPTS / "charge_sim.py"
ANALYZER = ROOT / ".claude" / "skills" / "dom-ev-diagnostics" / "scripts" / "ocpp_log_analyze.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class StubCsms:
    """Atrapa CSMS: przyjmuje wszystko; stacja REJ — Boot Rejected, MUTE — brak odpowiedzi, idTag BAD — Invalid."""

    def __init__(self, ws_mod):
        self.ws_mod, self.calls, self.connections = ws_mod, [], {}

    async def handler(self, ws):
        cp = ws.path.rsplit("/", 1)[-1]
        self.connections[cp] = self.connections.get(cp, 0) + 1
        while (msg := await ws.recv()) is not None:
            frame = json.loads(msg)
            if frame[0] != 2:
                continue
            _, mid, action, payload = frame
            self.calls.append((cp, self.connections[cp], mid, action, payload))
            if cp == "MUTE":
                continue
            bad = payload.get("idTag") == "BAD"
            res = {
                "BootNotification": {"status": "Rejected" if cp == "REJ" else "Accepted",
                                     "currentTime": "2026-10-20T08:00:00Z", "interval": 300},
                "Authorize": {"idTagInfo": {"status": "Invalid" if bad else "Accepted"}},
                "StartTransaction": {"transactionId": 7, "idTagInfo": {"status": "Accepted"}},
                "StopTransaction": {"idTagInfo": {"status": "Accepted"}},
                "Heartbeat": {"currentTime": "2026-10-20T08:00:00Z"},
            }.get(action, {})
            await ws.send(json.dumps([3, mid, res]))


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def scenario(sim, ws_mod, an, check, tmp: Path):
    stub = StubCsms(ws_mod)
    server = await ws_mod.serve(stub.handler, "127.0.0.1", 0, subprotocols=["ocpp1.6"])
    base = f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}"

    def ups(res):
        return [json.loads(x)["frame"][2] for x in res["log"]
                if json.loads(x)["dir"] == "cp>csms" and json.loads(x)["frame"][0] == 2]

    def codes(res):
        return sorted(f["code"] for f in an.analyze(res["log"])["findings"])

    try:
        r = await sim.simulate(f"{base}/CP1", meter_steps=3, energy_wh=12000, timeout=5)
        check(r["code"] == 0, f"S-1: sesja → kod 0: {r['code']} {r['message']}")
        check(ups(r) == ["BootNotification", "StatusNotification", "Authorize", "StatusNotification", "StatusNotification",
                         "StartTransaction", "MeterValues", "MeterValues", "MeterValues", "StopTransaction",
                         "StatusNotification"], f"S-2: kolejność komunikatów sesji: {ups(r)}")
        check(codes(r) == [], f"S-3: log symulatora bez ustaleń analizatora: {codes(r)}")
        mine = [c for c in stub.calls if c[0] == "CP1"]
        start = next(c[4] for c in mine if c[3] == "StartTransaction")
        stop = next(c[4] for c in mine if c[3] == "StopTransaction")
        statuses = [c[4]["status"] for c in mine if c[3] == "StatusNotification"]
        check(stop["meterStop"] - start["meterStart"] == 12000 and stop["transactionId"] == 7,
              f"S-4: energia 12000 Wh i transactionId z CSMS: {start} {stop}")
        check(statuses == ["Available", "Preparing", "Charging", "Available"], f"S-5: statusy złącza: {statuses}")
        mv = [c[4] for c in mine if c[3] == "MeterValues"]
        sv = mv[0]["meterValue"][0]["sampledValue"][0]
        check(all(m["transactionId"] == 7 for m in mv) and sv["unit"] == "Wh"
              and sv["measurand"] == "Energy.Active.Import.Register", f"S-6: MeterValues z transactionId i jednostką: {mv[0]}")

        r = await sim.simulate(f"{base}/CP2", scenario="boot", timeout=5)
        check(r["code"] == 0 and ups(r) == ["BootNotification", "StatusNotification"], f"S-7: scenariusz boot: {ups(r)}")

        # Awarie: każda daje ustalenie analizatora, które opisuje skill
        r = await sim.simulate(f"{base}/F1", fault="drop-stop", timeout=5)
        check(r["code"] == 0 and "StopTransaction" not in ups(r) and codes(r) == ["open-transaction"],
              f"F-1: drop-stop → open-transaction: {r['code']} {codes(r)}")
        r = await sim.simulate(f"{base}/F2", fault="duplicate-message", timeout=5)
        dup = [c[2] for c in stub.calls if c[0] == "F2" and c[3] == "MeterValues"]
        check(r["code"] == 0 and codes(r) == ["duplicate-message-id"] and len(dup) != len(set(dup)),
              f"F-2: duplicate-message → ten sam messageId dwa razy: {codes(r)} {dup}")
        r = await sim.simulate(f"{base}/F3", fault="clock-skew", timeout=5)
        check(r["code"] == 0 and "clock-skew" in codes(r), f"F-3: clock-skew → ustalenie clock-skew: {codes(r)}")
        r = await sim.simulate(f"{base}/F4", fault="offline-replay", meter_steps=2, timeout=5, offline_s=0.3)
        after = [c[3] for c in stub.calls if c[0] == "F4" and c[1] == 2]
        check(r["code"] == 0 and stub.connections.get("F4") == 2 and after[:3] == ["MeterValues", "MeterValues", "StopTransaction"]
              and "BootNotification" not in after and codes(r) == [],
              f"F-4: offline-replay → kolejka wysłana po ponownym połączeniu, bez Boot: {r['code']} {after} {codes(r)}")

        # Odrzucenia i brak odpowiedzi → kod 1
        r = await sim.simulate(f"{base}/CP3", id_tag="BAD", timeout=5)
        check(r["code"] == 1 and "Invalid" in r["message"] and "StartTransaction" not in ups(r),
              f"E-1: Authorize Invalid → kod 1 bez StartTransaction: {r['code']} {r['message']}")
        r = await sim.simulate(f"{base}/REJ", timeout=5)
        check(r["code"] == 1 and "Rejected" in r["message"], f"E-2: Boot Rejected → kod 1: {r['message']}")
        r = await sim.simulate(f"{base}/MUTE", timeout=0.5)
        check(r["code"] == 1 and "BootNotification" in r["message"], f"E-3: brak odpowiedzi → kod 1: {r['message']}")
        r = await sim.simulate(f"ws://127.0.0.1:{free_port()}/X", timeout=2)
        check(r["code"] == 2, f"E-4: brak serwera → kod 2: {r['code']} {r['message']}")

        # Wiersz poleceń: plik logu czytany przez analizator
        log = tmp / "sim.jsonl"
        p = await asyncio.create_subprocess_exec(sys.executable, str(SIM), f"{base}/CLI", "--fault", "drop-stop",
                                                 "--log", str(log), "--meter-steps", "2",
                                                 stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await asyncio.wait_for(p.communicate(), 30)
        lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        check(p.returncode == 0 and [f["code"] for f in an.analyze(lines)["findings"]] == ["open-transaction"],
              f"CLI-1: --log zapisuje JSON Lines dla analizatora: {p.returncode} {out[-200:]!r} {err[-300:]!r}")
    finally:
        server.close()
        await server.wait_closed()


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    sim = load("charge_sim", SIM)
    ws_mod = load("ocpp_ws", SCRIPTS / "ocpp_ws.py")
    an = load("ocpp_log_analyze", ANALYZER)
    with tempfile.TemporaryDirectory() as t:
        asyncio.run(scenario(sim, ws_mod, an, check, Path(t)))

    import subprocess
    for args, name in ((["wss://127.0.0.1:1/X"], "wss://"), (["ws://127.0.0.1:1/X", "--fault", "nieznany"], "zły --fault"),
                       ([], "brak URL")):
        p = subprocess.run([sys.executable, str(SIM), *args], capture_output=True, text=True, timeout=30)
        check(p.returncode == 2, f"CLI-2: {name} → kod 2: {p.returncode} {p.stderr[-200:]}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów symulatora ładowarki nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów symulatora ładowarki")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
