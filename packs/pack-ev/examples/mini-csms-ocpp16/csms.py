#!/usr/bin/env python3
"""
Mini-CSMS OCPP 1.6J — przykład dydaktyczny i cel testów end-to-end, nie produkcja. Tylko biblioteka standardowa
(+ ocpp_ws.py ze skilla dom-ev-simulation-testing).

  python3 examples/mini-csms-ocpp16/csms.py [--host 127.0.0.1] [--port 9000] [--tokens TAG1,TAG2] [--sessions plik.jsonl]

Stacje łączą się pod ws://host:port/<dowolna-ścieżka>/<ID_STACJI> z podprotokołem ocpp1.6.
Obsługuje: BootNotification (Accepted), Heartbeat, StatusNotification, Authorize (lista tokenów), StartTransaction
(nadaje transactionId), MeterValues, StopTransaction. Inne akcje → CALLERROR NotImplemented.
Idempotencja: powtórzony messageId tej samej stacji dostaje zapamiętaną odpowiedź bez drugiego skutku; pamięć
czyszczona przy BootNotification (stacja po restarcie numeruje komunikaty od nowa).
Czego brakuje do produkcji: TLS i profile bezpieczeństwa, trwały magazyn, domykanie sesji osieroconych, komendy
do stacji, OCPP 2.0.1 — patrz README.md.
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

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
_spec = importlib.util.spec_from_file_location(
    "ocpp_ws", ROOT / ".claude" / "skills" / "dom-ev-simulation-testing" / "scripts" / "ocpp_ws.py")
ocpp_ws = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ocpp_ws)

ENERGY = "Energy.Active.Import.Register"
CACHE_PER_STATION = 1000


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _energy_wh(meter_value: list) -> int | None:
    """Ostatni odczyt rejestru energii w Wh (brak measurand = rejestr energii wg OCPP 1.6; kWh przeliczane)."""
    wh = None
    for mv in meter_value:
        for sv in mv.get("sampledValue", []):
            if sv.get("measurand", ENERGY) == ENERGY:
                value = float(sv["value"])
                wh = round(value * 1000 if sv.get("unit") == "kWh" else value)
    return wh


class MiniCsms:
    def __init__(self, tokens: set[str], store: Path | None = None):
        self.tokens, self.store = set(tokens), store
        self.stations: dict[str, dict] = {}
        self.sessions: dict[int, dict] = {}
        self.log: list[str] = []
        self._tx = itertools.count(1)
        self._cache: dict[str, dict[str, list]] = {}

    async def start(self, host: str, port: int):
        return await ocpp_ws.serve(self.handle, host, port, subprotocols=["ocpp1.6"])

    def _record(self, cp: str, direction: str, frame: list) -> None:
        self.log.append(json.dumps({"ts": _now(), "cp": cp, "dir": direction, "frame": frame}, ensure_ascii=False))

    async def handle(self, ws) -> None:
        cp = ws.path.rstrip("/").rsplit("/", 1)[-1]
        while (msg := await ws.recv()) is not None:
            try:
                frame = json.loads(msg)
                kind, mid = frame[0], frame[1]
            except (json.JSONDecodeError, IndexError, KeyError, TypeError):
                continue
            self._record(cp, "cp>csms", frame)
            if kind != 2:
                continue
            reply = self._answer(cp, mid, frame)
            self._record(cp, "csms>cp", reply)
            await ws.send(json.dumps(reply))

    def _answer(self, cp: str, mid: str, frame: list) -> list:
        action = frame[2] if len(frame) > 2 else None
        payload = frame[3] if len(frame) > 3 and isinstance(frame[3], dict) else None
        if action == "BootNotification":
            self._cache[cp] = {}
        cache = self._cache.setdefault(cp, {})
        if mid in cache:
            return cache[mid]
        handler = getattr(self, f"on_{action}", None)
        if payload is None:
            reply = [4, mid, "FormationViolation", "payload nie jest obiektem JSON", {}]
        elif handler is None:
            reply = [4, mid, "NotImplemented", f"akcja {action} nieobsługiwana w mini-CSMS", {}]
        else:
            try:
                reply = [3, mid, handler(cp, payload)]
            except (KeyError, TypeError, ValueError) as e:
                reply = [4, mid, "PropertyConstraintViolation", f"{action}: {e}", {}]
        if len(cache) >= CACHE_PER_STATION:
            cache.pop(next(iter(cache)))
        cache[mid] = reply
        return reply

    # --- akcje OCPP 1.6 ---
    def on_BootNotification(self, cp, p):
        self.stations[cp] = {"vendor": p["chargePointVendor"], "model": p["chargePointModel"],
                             "firmware": p.get("firmwareVersion"), "status": None, "booted_at": _now()}
        return {"status": "Accepted", "currentTime": _now(), "interval": 300}

    def on_Heartbeat(self, cp, p):
        return {"currentTime": _now()}

    def on_StatusNotification(self, cp, p):
        self.stations.setdefault(cp, {})["status"] = p["status"]
        return {}

    def _token(self, id_tag: str) -> dict:
        return {"status": "Accepted" if id_tag in self.tokens else "Invalid"}

    def on_Authorize(self, cp, p):
        return {"idTagInfo": self._token(p["idTag"])}

    def on_StartTransaction(self, cp, p):
        info = self._token(p["idTag"])
        tx = next(self._tx)
        if info["status"] == "Accepted":
            self.sessions[tx] = {"transaction_id": tx, "cp": cp, "connector_id": p["connectorId"], "id_tag": p["idTag"],
                                 "meter_start": p["meterStart"], "meter_stop": None, "last_wh": p["meterStart"],
                                 "energy_wh": 0, "meter_values": 0, "started_at": p["timestamp"], "stopped_at": None,
                                 "status": "open"}
            self._save()
        return {"transactionId": tx, "idTagInfo": info}

    def on_MeterValues(self, cp, p):
        s = self.sessions.get(p.get("transactionId"))
        wh = _energy_wh(p["meterValue"])
        if s and s["cp"] == cp and wh is not None:
            s["meter_values"] += 1
            s["last_wh"] = wh
            s["energy_wh"] = wh - s["meter_start"]
        return {}

    def on_StopTransaction(self, cp, p):
        s = self.sessions.get(p["transactionId"])
        if s and s["cp"] == cp and s["status"] == "open":
            s.update(meter_stop=p["meterStop"], last_wh=p["meterStop"], energy_wh=p["meterStop"] - s["meter_start"],
                     stopped_at=p["timestamp"], status="closed")
            self._save()
        return {"idTagInfo": self._token(p["idTag"])} if "idTag" in p else {}

    def _save(self) -> None:
        if self.store:
            self.store.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in self.sessions.values()),
                                  encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Mini-CSMS OCPP 1.6J (przykład, tylko ws://).")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--tokens", default="TAG1", help="dozwolone idTag, po przecinku")
    ap.add_argument("--sessions", help="plik JSON Lines z sesjami (nadpisywany przy każdej zmianie)")
    args = ap.parse_args(argv)
    csms = MiniCsms({t for t in args.tokens.split(",") if t}, Path(args.sessions) if args.sessions else None)

    async def run():
        server = await csms.start(args.host, args.port)
        print(f"mini-CSMS nasłuchuje na ws://{args.host}:{args.port}/ocpp/<ID_STACJI>", flush=True)
        async with server:
            await server.serve_forever()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
