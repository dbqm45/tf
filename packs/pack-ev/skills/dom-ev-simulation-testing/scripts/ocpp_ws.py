#!/usr/bin/env python3
"""
Minimalny WebSocket (RFC 6455) dla OCPP-J na asyncio. Tylko biblioteka standardowa. Sieć: wyłącznie adres podany
w wywołaniu (ws://, bez TLS).

  ws = await connect("ws://localhost:9000/CP1", subprotocols=["ocpp1.6"])
  server = await serve(handler, "127.0.0.1", 9000, subprotocols=["ocpp1.6"])   # handler(ws) — ws.path, ws.subprotocol

WebSocket: `await send(text)`, `await recv()` → tekst albo None po zamknięciu, `await ping()` → czas odpowiedzi (s),
`await close(code)`, pola `subprotocol`, `path`, `closed`. Ramki tekstowe i binarne, fragmentacja przy odbiorze,
maskowanie po stronie klienta, automatyczny pong. Bez rozszerzeń (permessage-deflate) i bez TLS — do testów lokalnych.
Serwer bez wspólnego podprotokołu odpowiada HTTP 400 (stacja OCPP musi dostać wybraną wersję w handshake'u).
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import struct
import time
from urllib.parse import urlsplit

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
TEXT, BINARY, CLOSE, PING, PONG, CONT = 0x1, 0x2, 0x8, 0x9, 0xA, 0x0
MAX_MESSAGE = 16 * 1024 * 1024


class HandshakeError(Exception):
    pass


def accept_key(key: str) -> str:
    return base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()


def encode_frame(opcode: int, payload: bytes, mask_key: bytes | None) -> bytes:
    head = bytes([0x80 | opcode])
    mask_bit = 0x80 if mask_key else 0
    n = len(payload)
    if n < 126:
        head += bytes([mask_bit | n])
    elif n < 65536:
        head += bytes([mask_bit | 126]) + struct.pack("!H", n)
    else:
        head += bytes([mask_bit | 127]) + struct.pack("!Q", n)
    if not mask_key:
        return head + payload
    return head + mask_key + bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))


class WebSocket:
    def __init__(self, reader, writer, client: bool, subprotocol: str | None, path: str):
        self.reader, self.writer, self.client = reader, writer, client
        self.subprotocol, self.path, self.closed = subprotocol, path, False
        self._pongs: dict[bytes, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def _write(self, opcode: int, payload: bytes) -> None:
        async with self._lock:
            self.writer.write(encode_frame(opcode, payload, os.urandom(4) if self.client else None))
            await self.writer.drain()

    async def send(self, text: str) -> None:
        if self.closed:
            raise ConnectionError("WebSocket zamknięty")
        await self._write(TEXT, text.encode("utf-8"))

    async def _read_frame(self) -> tuple[bool, int, bytes]:
        b1, b2 = await self.reader.readexactly(2)
        n = b2 & 0x7F
        if n == 126:
            n = struct.unpack("!H", await self.reader.readexactly(2))[0]
        elif n == 127:
            n = struct.unpack("!Q", await self.reader.readexactly(8))[0]
        if n > MAX_MESSAGE:
            raise ConnectionError(f"ramka {n} B przekracza limit {MAX_MESSAGE} B")
        key = await self.reader.readexactly(4) if b2 & 0x80 else None
        data = await self.reader.readexactly(n)
        if key:
            data = bytes(b ^ key[i % 4] for i, b in enumerate(data))
        return bool(b1 & 0x80), b1 & 0x0F, data

    async def recv(self) -> str | None:
        """Następna wiadomość (tekst; binarna dekodowana jako UTF-8) albo None po zamknięciu połączenia."""
        parts: list[bytes] = []
        while not self.closed:
            try:
                fin, op, data = await self._read_frame()
            except (asyncio.IncompleteReadError, ConnectionError, OSError):
                await self._shutdown()
                return None
            if op == PING:
                await self._write(PONG, data)
            elif op == PONG:
                fut = self._pongs.pop(data, None)
                if fut and not fut.done():
                    fut.set_result(time.monotonic())
            elif op == CLOSE:
                if not self.closed:
                    try:
                        await self._write(CLOSE, data[:2])
                    except (ConnectionError, OSError):
                        pass
                await self._shutdown()
                return None
            else:
                parts.append(data)
                if fin:
                    return b"".join(parts).decode("utf-8")
        return None

    async def ping(self, data: bytes = b"", timeout: float = 10) -> float:
        """Wysyła ping i czeka na pong (odbiór pongów robi recv(), więc ktoś musi czytać; bez czytelnika — czeka sam)."""
        data = data or os.urandom(4)
        fut = asyncio.get_running_loop().create_future()
        self._pongs[data] = fut
        start = time.monotonic()
        await self._write(PING, data)
        while not fut.done():
            fin, op, payload = await asyncio.wait_for(self._read_frame(), timeout)
            if op == PONG and payload == data:
                return time.monotonic() - start
            if op == PING:
                await self._write(PONG, payload)
        return fut.result() - start

    async def close(self, code: int = 1000) -> None:
        if self.closed:
            return
        try:
            await self._write(CLOSE, struct.pack("!H", code))
        except (ConnectionError, OSError):
            pass
        await self._shutdown()

    async def _shutdown(self) -> None:
        self.closed = True
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except (ConnectionError, OSError):
            pass


async def _read_headers(reader) -> tuple[str, dict[str, str]]:
    raw = await reader.readuntil(b"\r\n\r\n")
    lines = raw.decode("latin-1").split("\r\n")
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return lines[0], headers


async def connect(url: str, subprotocols: list[str] | tuple[str, ...] = ("ocpp1.6",), timeout: float = 10,
                  headers: dict[str, str] | None = None) -> WebSocket:
    u = urlsplit(url)
    if u.scheme != "ws":
        raise ValueError(f"obsługiwany jest tylko ws:// (jest {u.scheme}://)")
    host, port = u.hostname or "localhost", u.port or 80
    path = (u.path or "/") + (f"?{u.query}" if u.query else "")
    reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    key = base64.b64encode(os.urandom(16)).decode()
    extra = "".join(f"{k}: {v}\r\n" for k, v in (headers or {}).items())
    writer.write((f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                  f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
                  f"Sec-WebSocket-Protocol: {', '.join(subprotocols)}\r\n{extra}\r\n").encode())
    await writer.drain()
    try:
        status, h = await asyncio.wait_for(_read_headers(reader), timeout)
    except (asyncio.IncompleteReadError, asyncio.LimitOverrunError) as e:
        writer.close()
        raise HandshakeError(f"przerwany handshake: {e}") from e
    if " 101 " not in status + " ":
        writer.close()
        raise HandshakeError(f"serwer odrzucił handshake: {status}")
    if h.get("sec-websocket-accept") != accept_key(key):
        writer.close()
        raise HandshakeError("zły Sec-WebSocket-Accept")
    chosen = h.get("sec-websocket-protocol")
    if chosen not in subprotocols:
        writer.close()
        raise HandshakeError(f"serwer wybrał podprotokół {chosen!r}, oferowane: {list(subprotocols)}")
    return WebSocket(reader, writer, True, chosen, u.path or "/")


async def serve(handler, host: str, port: int, subprotocols: list[str] | tuple[str, ...] = ("ocpp1.6",)):
    """Serwer WebSocket; handler(ws) dostaje połączenie po udanym handshake'u. Zwraca asyncio.Server."""

    async def on_client(reader, writer):
        try:
            request, h = await _read_headers(reader)
        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError, ConnectionError):
            writer.close()
            return
        parts = request.split(" ")
        path = parts[1] if len(parts) > 1 else "/"
        offered = [p.strip() for p in h.get("sec-websocket-protocol", "").split(",") if p.strip()]
        chosen = next((p for p in offered if p in subprotocols), None)
        if h.get("upgrade", "").lower() != "websocket" or "sec-websocket-key" not in h or chosen is None:
            reason = "no common subprotocol" if chosen is None else "not a WebSocket upgrade"
            writer.write(f"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\nX-Reason: {reason}\r\n\r\n".encode())
            await writer.drain()
            writer.close()
            return
        writer.write((f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                      f"Sec-WebSocket-Accept: {accept_key(h['sec-websocket-key'])}\r\n"
                      f"Sec-WebSocket-Protocol: {chosen}\r\n\r\n").encode())
        await writer.drain()
        ws = WebSocket(reader, writer, False, chosen, path.split("?")[0])
        try:
            await handler(ws)
        finally:
            await ws.close()

    return await asyncio.start_server(on_client, host, port)
