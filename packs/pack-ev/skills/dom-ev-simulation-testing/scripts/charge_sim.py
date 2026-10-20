#!/usr/bin/env python3
"""
Symulator ładowarki OCPP 1.6J (jedno złącze) do testów CSMS bez sprzętu. Tylko biblioteka standardowa
(+ ocpp_ws.py z tego katalogu). Sieć: wyłącznie adres ws:// podany w wywołaniu.

  python3 .claude/skills/dom-ev-simulation-testing/scripts/charge_sim.py <ws://host:port/ID> [--scenario session|boot]
      [--id-tag T] [--energy-wh N] [--meter-steps K]
      [--fault none|offline-replay|duplicate-message|clock-skew|drop-stop] [--log plik.jsonl] [--timeout S]

Kod wyjścia: 0 — scenariusz przeszedł, 1 — CSMS odrzucił komunikat albo nie odpowiedział w czasie, 2 — błąd wywołania
lub połączenia. ID stacji to ostatni segment ścieżki URL.

session: BootNotification → StatusNotification Available → Authorize → Preparing → Charging → StartTransaction →
         MeterValues ×K → StopTransaction → Available.        boot: BootNotification → StatusNotification Available.
Awarie (--fault):
  drop-stop          bez StopTransaction (zanik zasilania lub błąd firmware) → analizator: open-transaction
  duplicate-message  pierwsze MeterValues wysłane drugi raz z tym samym messageId → duplicate-message-id
  clock-skew         znaczniki czasu w komunikatach cofnięte o godzinę (stacja bez RTC/NTP) → clock-skew
  offline-replay     po StartTransaction rozłączenie, MeterValues i StopTransaction w kolejce, wysłane po ponownym
                     połączeniu z czasem zdarzenia (bez ponownego BootNotification — stacja się nie restartowała)
Log (--log): JSON Lines {ts, cp, dir, frame} — wejście dla dom-ev-diagnostics/scripts/ocpp_log_analyze.py.
CALL od CSMS (np. TriggerMessage) dostaje CALLERROR NotSupported — symulator nie implementuje komend zdalnych.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import importlib.util
import itertools
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

_spec = importlib.util.spec_from_file_location("ocpp_ws", Path(__file__).with_name("ocpp_ws.py"))
ocpp_ws = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ocpp_ws)

FAULTS = ("none", "offline-replay", "duplicate-message", "clock-skew", "drop-stop")
METER_START = 1000


class Rejected(Exception):
    pass


def _iso(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class Station:
    def __init__(self, url: str, timeout: float, skew_s: int):
        self.url, self.timeout, self.skew = url, timeout, dt.timedelta(seconds=skew_s)
        self.cp = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1] or "CP"
        self.log: list[str] = []
        self.ids = itertools.count(1)
        self.ws = None
        self.pending: dict[str, asyncio.Future] = {}
        self.reader: asyncio.Task | None = None

    def now(self) -> str:
        """Czas stacji (z ewentualnym przesunięciem zegara)."""
        return _iso(dt.datetime.now(dt.timezone.utc) - self.skew)

    def _record(self, direction: str, frame: list) -> None:
        self.log.append(json.dumps({"ts": _iso(dt.datetime.now(dt.timezone.utc)), "cp": self.cp, "dir": direction,
                                    "frame": frame}, ensure_ascii=False))

    async def connect(self) -> None:
        self.ws = await ocpp_ws.connect(self.url, subprotocols=["ocpp1.6"], timeout=self.timeout)
        self.reader = asyncio.create_task(self._read())

    async def disconnect(self) -> None:
        if self.ws:
            await self.ws.close()
        if self.reader:
            await asyncio.wait([self.reader], timeout=self.timeout)

    async def _read(self) -> None:
        while (msg := await self.ws.recv()) is not None:
            try:
                frame = json.loads(msg)
            except json.JSONDecodeError:
                continue
            self._record("csms>cp", frame)
            if frame[0] == 2:
                err = [4, frame[1], "NotSupported", "symulator nie obsługuje tej komendy", {}]
                self._record("cp>csms", err)
                await self.ws.send(json.dumps(err))
            elif frame[0] in (3, 4) and (fut := self.pending.pop(frame[1], None)) and not fut.done():
                fut.set_result(frame)
        for fut in self.pending.values():
            if not fut.done():
                fut.set_exception(ConnectionError("CSMS zamknął połączenie"))

    async def call(self, action: str, payload: dict, mid: str | None = None) -> dict:
        mid = mid or str(next(self.ids))
        frame = [2, mid, action, payload]
        fut = asyncio.get_running_loop().create_future()
        self.pending[mid] = fut
        self._record("cp>csms", frame)
        await self.ws.send(json.dumps(frame))
        try:
            res = await asyncio.wait_for(fut, self.timeout)
        except asyncio.TimeoutError:
            self.pending.pop(mid, None)
            raise Rejected(f"{action}: brak odpowiedzi CSMS w {self.timeout} s") from None
        if res[0] == 4:
            raise Rejected(f"{action}: CALLERROR {res[2]} — {res[3]}")
        return res[2]

    async def status(self, status: str, error: str = "NoError") -> None:
        await self.call("StatusNotification", {"connectorId": 1, "errorCode": error, "status": status,
                                               "timestamp": self.now()})


def _meter(st: Station, tx: int, wh: int) -> dict:
    return {"connectorId": 1, "transactionId": tx, "meterValue": [{"timestamp": st.now(), "sampledValue": [
        {"value": str(wh), "context": "Sample.Periodic", "measurand": "Energy.Active.Import.Register",
         "location": "Outlet", "unit": "Wh"}]}]}


async def _session(st: Station, scenario: str, id_tag: str, energy_wh: int, steps: int, fault: str,
                   offline_s: float) -> None:
    boot = await st.call("BootNotification", {"chargePointVendor": "EVTF", "chargePointModel": "charge_sim",
                                              "firmwareVersion": "0.1"})
    if boot.get("status") != "Accepted":
        raise Rejected(f"BootNotification: status {boot.get('status')} — CSMS nie przyjął stacji")
    await st.status("Available")
    if scenario == "boot":
        return
    auth = (await st.call("Authorize", {"idTag": id_tag})).get("idTagInfo", {}).get("status")
    if auth != "Accepted":
        raise Rejected(f"Authorize: idTag {id_tag} ma status {auth}")
    await st.status("Preparing")
    await st.status("Charging")
    start = await st.call("StartTransaction", {"connectorId": 1, "idTag": id_tag, "meterStart": METER_START,
                                               "timestamp": st.now()})
    tx = start.get("transactionId")
    if start.get("idTagInfo", {}).get("status") != "Accepted" or tx is None:
        raise Rejected(f"StartTransaction: odrzucony ({start})")
    readings = [METER_START + energy_wh * (i + 1) // steps for i in range(steps)]
    stop = {"transactionId": tx, "idTag": id_tag, "meterStop": METER_START + energy_wh, "reason": "Local"}

    if fault == "offline-replay":
        await st.disconnect()
        queue = []
        for wh in readings:
            queue.append(("MeterValues", _meter(st, tx, wh)))
            await asyncio.sleep(offline_s / (steps + 1))
        queue.append(("StopTransaction", {**stop, "timestamp": st.now()}))
        await asyncio.sleep(offline_s / (steps + 1))
        await st.connect()
        for action, payload in queue:
            await st.call(action, payload)
        await st.status("Available")
        return

    for i, wh in enumerate(readings):
        payload = _meter(st, tx, wh)
        await st.call("MeterValues", payload, mid=f"mv-{tx}-{i}")
        if fault == "duplicate-message" and i == 0:
            await st.call("MeterValues", payload, mid=f"mv-{tx}-{i}")
    if fault == "drop-stop":
        return
    await st.call("StopTransaction", {**stop, "timestamp": st.now()})
    await st.status("Available")


async def simulate(url: str, scenario: str = "session", id_tag: str = "TAG1", energy_wh: int = 10000,
                   meter_steps: int = 3, fault: str = "none", timeout: float = 10, offline_s: float = 1.0) -> dict:
    """Uruchamia scenariusz. Wynik: {"code": 0|1|2, "message": str, "log": [linie JSON Lines]}."""
    try:
        if not urlsplit(url).scheme == "ws":
            raise ValueError(f"obsługiwany jest tylko ws:// ({url})")
        if fault not in FAULTS or scenario not in ("session", "boot") or meter_steps < 1 or energy_wh < 0:
            raise ValueError("zły argument scenariusza")
        st = Station(url, timeout, 3600 if fault == "clock-skew" else 0)
    except ValueError as e:
        return {"code": 2, "message": str(e), "log": []}
    try:
        await st.connect()
    except (OSError, asyncio.TimeoutError, ocpp_ws.HandshakeError) as e:
        return {"code": 2, "message": f"połączenie z {url}: {e}", "log": st.log}
    try:
        await _session(st, scenario, id_tag, energy_wh, meter_steps, fault, offline_s)
        return {"code": 0, "message": f"scenariusz {scenario} (awaria: {fault}) przeszedł", "log": st.log}
    except Rejected as e:
        return {"code": 1, "message": str(e), "log": st.log}
    except (OSError, ConnectionError, asyncio.TimeoutError, ocpp_ws.HandshakeError) as e:
        return {"code": 2, "message": f"połączenie przerwane: {e}", "log": st.log}
    finally:
        await st.disconnect()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Symulator ładowarki OCPP 1.6J do testów CSMS (tylko ws://).")
    ap.add_argument("url", help="ws://host:port/ścieżka/ID_STACJI")
    ap.add_argument("--scenario", choices=["session", "boot"], default="session")
    ap.add_argument("--id-tag", default="TAG1")
    ap.add_argument("--energy-wh", type=int, default=10000)
    ap.add_argument("--meter-steps", type=int, default=3)
    ap.add_argument("--fault", choices=FAULTS, default="none")
    ap.add_argument("--log", help="plik JSON Lines dla ocpp_log_analyze.py")
    ap.add_argument("--timeout", type=float, default=10, help="czas oczekiwania na odpowiedź CSMS (s)")
    args = ap.parse_args(argv)
    r = asyncio.run(simulate(args.url, args.scenario, args.id_tag, args.energy_wh, args.meter_steps, args.fault,
                             args.timeout))
    if args.log:
        Path(args.log).write_text("".join(x + "\n" for x in r["log"]), encoding="utf-8")
    print(("✓ " if r["code"] == 0 else "✗ ") + r["message"] + f" — {len(r['log'])} ramek")
    return r["code"]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
