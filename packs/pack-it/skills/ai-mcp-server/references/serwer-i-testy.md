# Serwer MCP z testami bez modelu — przetestowany przykład (Python)

Sprawdzone 2026-10-23: Python SDK `mcp` 1.29.0 (protokół 2025-11-25), `pytest` — 6 testów: migawka kontraktu
narzędzi, wynik strukturalny, błąd narzędzia z następnym krokiem, odrzucenie wejścia przez schemat, prawdziwy
proces po stdio, surowy stdout tylko z JSON-RPC. Kontrola odwrotna: dopisanie `print()` w narzędziu wywala ostatni
test (klient Python SDK pomija obce linie, więc test sesją tego nie wykrywa). Pliki skopiowane bez zmian.
Zależności: `pip install mcp pytest anyio`.

## Spis treści
- booking_mcp.py — serwer: dwa narzędzia, schematy z ograniczeniami, adnotacje, `ToolError`, logi na stderr
- test_booking_mcp.py — testy w CI
- Rejestracja w Claude Code

## booking_mcp.py
```python
"""Serwer MCP rezerwacji sal: dwa narzędzia, transport stdio. Logi tylko na stderr — stdout należy do protokołu."""
import logging
import sys
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("booking-mcp")

mcp = FastMCP("booking")

ROOMS = {"sala-1": {"name": "Sala Wisła", "seats": 8, "blocked_by": None},
         "sala-2": {"name": "Sala Odra", "seats": 20, "blocked_by": None}}


class Room(BaseModel):
    id: str
    name: str
    seats: int
    free: bool


class FindResult(BaseModel):
    rooms: list[Room]
    total: int = Field(description="Liczba wszystkich pasujących sal, także poza limitem")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def find_rooms(
    min_seats: Annotated[int, Field(ge=1, le=500, description="Minimalna liczba miejsc, np. 10")] = 1,
    limit: Annotated[int, Field(ge=1, le=50, description="Ile sal zwrócić")] = 10,
) -> FindResult:
    """Znajdź sale z co najmniej `min_seats` miejscami. Zwraca listę z informacją, czy sala jest wolna."""
    hits = [Room(id=k, name=v["name"], seats=v["seats"], free=v["blocked_by"] is None)
            for k, v in sorted(ROOMS.items()) if v["seats"] >= min_seats]
    return FindResult(rooms=hits[:limit], total=len(hits))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True,
                                      openWorldHint=False))
def block_room(
    room_id: Annotated[str, Field(pattern=r"^sala-\d+$", description="Identyfikator z find_rooms, np. sala-1")],
    by: Annotated[str, Field(min_length=2, max_length=50, description="Kto blokuje salę")],
) -> str:
    """Zablokuj salę dla osoby `by`. Ponowne wywołanie przez tę samą osobę niczego nie zmienia."""
    room = ROOMS.get(room_id)
    if room is None:
        raise ToolError(f"Nie ma sali {room_id}. Użyj find_rooms, żeby poznać identyfikatory.")
    if room["blocked_by"] not in (None, by):
        raise ToolError(f"Sala {room_id} jest zajęta przez {room['blocked_by']}. Wybierz inną salę z find_rooms.")
    room["blocked_by"] = by
    log.info("room %s blocked by %s", room_id, by)
    return f"Sala {room_id} zablokowana dla {by}."


if __name__ == "__main__":
    mcp.run()  # domyślnie stdio
```

## test_booking_mcp.py
```python
"""Testy serwera MCP bez modelu: sesja w pamięci (kontrakt i zachowanie) oraz prawdziwy proces po stdio."""
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

import booking_mcp

pytestmark = pytest.mark.anyio

# Migawka kontraktu: nazwa narzędzia, wymagane parametry, adnotacje. Zmiana = świadoma decyzja o wersji.
CONTRACT = {
    "find_rooms": {"required": [], "readOnlyHint": True},
    "block_room": {"required": ["by", "room_id"], "readOnlyHint": False},
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def fresh_rooms():
    for room in booking_mcp.ROOMS.values():
        room["blocked_by"] = None


async def test_tool_contract_snapshot():
    async with create_connected_server_and_client_session(booking_mcp.mcp._mcp_server) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
    got = {name: {"required": sorted(t.inputSchema.get("required", [])),
                  "readOnlyHint": t.annotations.readOnlyHint} for name, t in tools.items()}
    assert got == CONTRACT
    assert all(t.description for t in tools.values())


async def test_find_returns_structured_content():
    async with create_connected_server_and_client_session(booking_mcp.mcp._mcp_server) as client:
        result = await client.call_tool("find_rooms", {"min_seats": 10})
    assert not result.isError
    assert result.structuredContent["total"] == 1
    assert result.structuredContent["rooms"][0]["id"] == "sala-2"


async def test_conflict_is_tool_error_with_next_step():
    async with create_connected_server_and_client_session(booking_mcp.mcp._mcp_server) as client:
        ok = await client.call_tool("block_room", {"room_id": "sala-1", "by": "anna"})
        again = await client.call_tool("block_room", {"room_id": "sala-1", "by": "anna"})
        conflict = await client.call_tool("block_room", {"room_id": "sala-1", "by": "jan"})
    assert not ok.isError and not again.isError
    assert conflict.isError
    assert "find_rooms" in conflict.content[0].text


async def test_invalid_input_is_rejected_by_schema():
    async with create_connected_server_and_client_session(booking_mcp.mcp._mcp_server) as client:
        result = await client.call_tool("block_room", {"room_id": "../etc", "by": "anna"})
    assert result.isError


async def test_real_stdio_process_handshake():
    # stdout zanieczyszczony print() zepsułby ten test — protokół idzie po stdout
    params = StdioServerParameters(command=sys.executable, args=[str(Path(booking_mcp.__file__))])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            tools = await session.list_tools()
    assert init.serverInfo.name == "booking"
    assert {t.name for t in tools.tools} == set(CONTRACT)


def test_stdout_carries_only_jsonrpc():
    # Specyfikacja: serwer stdio nie może pisać na stdout nic poza wiadomościami MCP. Klient Python SDK pomija
    # obce linie, więc test sesją tego nie wykryje — czytamy surowy stdout procesu.
    import json
    import subprocess

    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "block_room", "arguments": {"room_id": "sala-1", "by": "anna"}}},
    ]
    proc = subprocess.run([sys.executable, booking_mcp.__file__], input="\n".join(map(json.dumps, messages)) + "\n",
                          capture_output=True, text=True, timeout=30)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert len(lines) == 2
    assert all(json.loads(line)["jsonrpc"] == "2.0" for line in lines)
```

## Rejestracja w Claude Code
Sprawdzone `claude` 2.1.309: nazwa serwera przed `-e` (opcja `-e` przyjmuje wiele wartości i połknie nazwę).
```
claude mcp add --scope project booking -e BOOKING_ENV=dev -- python3 booking_mcp.py
```
Zakres `project` zapisuje do repozytorium `.mcp.json`:
```json
{
  "mcpServers": {
    "booking": {
      "type": "stdio",
      "command": "python3",
      "args": ["booking_mcp.py"],
      "env": {"BOOKING_ENV": "dev"}
    }
  }
}
```
Sekretów nie wpisujesz do `.mcp.json` (trafia do repozytorium). Zakres `local` (domyślny) zapisuje konfigurację
w `~/.claude.json` użytkownika, w sekcji danego projektu — sprawdzone tym samym CLI; tam albo w zmiennych
środowiskowych użytkownika trzymasz tokeny.
