#!/usr/bin/env python3
"""Testy minimalnego WebSocketu dla OCPP (skill dom-ev-simulation-testing): handshake z podprotokołem, ramki, maska, ping, close."""
import asyncio
import importlib.util
import struct
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "dom-ev-simulation-testing" / "scripts" / "ocpp_ws.py"


def load():
    spec = importlib.util.spec_from_file_location("ocpp_ws", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


async def scenario(m, check):
    seen = {}

    async def echo(ws):
        seen["path"], seen["sub"] = ws.path, ws.subprotocol
        while (msg := await ws.recv()) is not None:
            await ws.send(msg)

    server = await m.serve(echo, "127.0.0.1", 0, subprotocols=["ocpp1.6"])
    port = server.sockets[0].getsockname()[1]
    url = f"ws://127.0.0.1:{port}/ocpp/CP-1"
    try:
        ws = await m.connect(url, subprotocols=["ocpp2.0.1", "ocpp1.6"])
        check(ws.subprotocol == "ocpp1.6", f"HS-1: negocjacja podprotokołu → ocpp1.6: {ws.subprotocol}")
        await ws.send('[2,"1","Heartbeat",{}]')
        check(await ws.recv() == '[2,"1","Heartbeat",{}]', "ECHO-1: krótka ramka tekstowa")
        check(seen == {"path": "/ocpp/CP-1", "sub": "ocpp1.6"}, f"HS-2: serwer widzi ścieżkę z ID stacji: {seen}")
        for n in (126, 70000):
            text = "ł" * (n // 2) + "x" * (n % 2)
            await ws.send(text)
            check(await ws.recv() == text, f"ECHO-2: ramka {n} bajtów (rozszerzona długość) z UTF-8")
        rtt = await ws.ping(b"hb")
        check(isinstance(rtt, float) and rtt >= 0, f"PING-1: ping → pong, czas w sekundach: {rtt}")
        await ws.close()
        check(ws.closed, "CLOSE-1: klient zamknięty po close()")

        try:
            await m.connect(url, subprotocols=["ocpp2.0.1"])
            check(False, "HS-3: brak wspólnego podprotokołu → HandshakeError")
        except m.HandshakeError as e:
            check("400" in str(e) or "podprotok" in str(e), f"HS-3: komunikat błędu: {e}")

        try:
            await m.connect("wss://127.0.0.1:1/x")
            check(False, "URL-1: wss:// → ValueError")
        except ValueError:
            check(True, "URL-1")
    finally:
        server.close()
        await server.wait_closed()

    # Zamknięcie przez serwer: recv() klienta zwraca None
    async def bye(ws):
        await ws.close(1000)

    server = await m.serve(bye, "127.0.0.1", 0, subprotocols=["ocpp1.6"])
    port = server.sockets[0].getsockname()[1]
    try:
        ws = await m.connect(f"ws://127.0.0.1:{port}/CP2", subprotocols=["ocpp1.6"])
        check(await asyncio.wait_for(ws.recv(), 2) is None and ws.closed, "CLOSE-2: close od serwera → recv() zwraca None")
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

    m = load()

    # Kodowanie ramek: długości 7/16/64 bity i maska klienta (RFC 6455 §5.2–5.3)
    f = m.encode_frame(0x1, b"abc", None)
    check(f == b"\x81\x03abc", f"FR-1: ramka tekstowa bez maski: {f!r}")
    f = m.encode_frame(0x1, b"abc", b"\x01\x02\x03\x04")
    check(f[:2] == b"\x81\x83" and f[2:6] == b"\x01\x02\x03\x04" and f[6:] == bytes([0x60, 0x60, 0x60]),
          f"FR-2: maska XOR i bit MASK: {f!r}")
    f = m.encode_frame(0x2, b"x" * 300, None)
    check(f[1] == 126 and struct.unpack("!H", f[2:4])[0] == 300, "FR-3: długość 16-bitowa")
    f = m.encode_frame(0x2, b"x" * 70000, None)
    check(f[1] == 127 and struct.unpack("!Q", f[2:10])[0] == 70000, "FR-4: długość 64-bitowa")
    check(m.accept_key("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=",
          "HS-0: Sec-WebSocket-Accept z przykładu RFC 6455")

    asyncio.run(scenario(m, check))

    if fails:
        print(f"✗ {len(fails)}/{total} testów WebSocketu OCPP nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów WebSocketu OCPP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
