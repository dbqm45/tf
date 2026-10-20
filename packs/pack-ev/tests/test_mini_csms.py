#!/usr/bin/env python3
"""Test end-to-end przykładu examples/mini-csms-ocpp16: symulator → mini-CSMS → analizator logów. Pomija się w projekcie bez examples/."""
import asyncio
import importlib.util
import json
import socket
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
EXAMPLE = ROOT / "examples" / "mini-csms-ocpp16"
SIM = ROOT / ".claude" / "skills" / "dom-ev-simulation-testing" / "scripts" / "charge_sim.py"
ANALYZER = ROOT / ".claude" / "skills" / "dom-ev-diagnostics" / "scripts" / "ocpp_log_analyze.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def scenario(csms_mod, sim, an, check, tmp: Path):
    csms = csms_mod.MiniCsms(tokens={"TAG1"})
    server = await csms.start("127.0.0.1", 0)
    base = f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}/ocpp"

    def codes(lines):
        return sorted(f["code"] for f in an.analyze(lines)["findings"])

    def session(cp):
        return [s for s in csms.sessions.values() if s["cp"] == cp]

    try:
        r = await sim.simulate(f"{base}/CP1", energy_wh=12000, meter_steps=3, timeout=5)
        s = session("CP1")
        check(r["code"] == 0, f"E2E-1: sesja przez mini-CSMS → kod 0: {r['message']}")
        check(len(s) == 1 and s[0]["status"] == "closed" and s[0]["energy_wh"] == 12000 and s[0]["meter_values"] == 3
              and s[0]["id_tag"] == "TAG1", f"E2E-2: sesja zamknięta, 12000 Wh, 3 odczyty: {s}")
        check(codes(r["log"]) == [] and codes(csms.log) == [],
              f"E2E-3: log stacji i log CSMS bez ustaleń: {codes(r['log'])} {codes(csms.log)}")
        check(csms.stations["CP1"]["status"] == "Available" and csms.stations["CP1"]["vendor"] == "EVTF",
              f"E2E-4: stan stacji z Boot i StatusNotification: {csms.stations.get('CP1')}")

        r = await sim.simulate(f"{base}/CP2", fault="duplicate-message", meter_steps=2, timeout=5)
        s = session("CP2")
        check(r["code"] == 0 and s[0]["meter_values"] == 2 and "duplicate-message-id" in codes(r["log"]),
              f"E2E-5: duplikat CALL bez drugiego skutku (idempotencja po messageId): {s}")

        r = await sim.simulate(f"{base}/CP3", fault="drop-stop", timeout=5)
        s = session("CP3")
        check(r["code"] == 0 and s[0]["status"] == "open" and codes(csms.log).count("open-transaction") == 1,
              f"E2E-6: brak StopTransaction → sesja otwarta, analizator CSMS: open-transaction: {s}")

        r = await sim.simulate(f"{base}/CP4", fault="offline-replay", meter_steps=2, timeout=5, offline_s=0.3)
        s = session("CP4")
        check(r["code"] == 0 and s[0]["status"] == "closed" and s[0]["energy_wh"] == 10000,
              f"E2E-7: zaległe ramki po offline domykają sesję: {s}")

        r = await sim.simulate(f"{base}/CP5", id_tag="OBCY", timeout=5)
        check(r["code"] == 1 and "Invalid" in r["message"] and session("CP5") == [],
              f"E2E-8: nieznany token → Invalid, kod 1, brak sesji: {r['message']}")
        ids = [s["transaction_id"] for s in csms.sessions.values()]
        check(len(ids) == len(set(ids)), f"E2E-9: unikalne transactionId: {ids}")
    finally:
        server.close()
        await server.wait_closed()

    # Wiersz poleceń: CSMS jako proces, symulator jako proces, sesje w pliku
    port, store = free_port(), tmp / "sessions.jsonl"
    p = await asyncio.create_subprocess_exec(sys.executable, str(EXAMPLE / "csms.py"), "--port", str(port),
                                             "--tokens", "TAG1", "--sessions", str(store),
                                             stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        for _ in range(50):
            try:
                _, w = await asyncio.open_connection("127.0.0.1", port)
                w.close()
                break
            except OSError:
                await asyncio.sleep(0.1)
        q = await asyncio.create_subprocess_exec(sys.executable, str(SIM), f"ws://127.0.0.1:{port}/ocpp/CLI",
                                                 stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await asyncio.wait_for(q.communicate(), 30)
        rows = [json.loads(x) for x in store.read_text(encoding="utf-8").splitlines()] if store.exists() else []
        check(q.returncode == 0 and any(x["cp"] == "CLI" and x["status"] == "closed" for x in rows),
              f"CLI-1: procesy CSMS i symulatora, sesja zapisana w --sessions: {q.returncode} {out!r} {err[-300:]!r} {rows}")
    finally:
        p.terminate()
        await p.wait()


def main() -> int:
    if not EXAMPLE.is_dir():
        print("✓ 0/0 testów mini-CSMS (pominięte: brak examples/ — przykład nie jest instalowany w projekcie)")
        return 0
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    csms_mod = load("csms", EXAMPLE / "csms.py")
    sim, an = load("charge_sim", SIM), load("ocpp_log_analyze", ANALYZER)
    with tempfile.TemporaryDirectory() as t:
        asyncio.run(scenario(csms_mod, sim, an, check, Path(t)))

    if fails:
        print(f"✗ {len(fails)}/{total} testów mini-CSMS nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów mini-CSMS (end-to-end)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
