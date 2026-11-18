# An MCP server with tests without a model — a tested example (Python)

> **Contents:** booking_mcp.py · test_booking_mcp.py · Registration in Claude Code

Checked 2026-10-23: Python SDK `mcp` 1.29.0 (protocol 2025-11-25), `pytest` — 6 tests: a snapshot of the tool
contract, a structured result, a tool error with a next step, rejection of input by the schema, a real
process over stdio, raw stdout with JSON-RPC only. Reverse check: adding a `print()` in a tool breaks the last
test (the Python SDK client skips foreign lines, so the session test does not detect it). The files were copied unchanged.
Dependencies: `pip install mcp pytest anyio`.

## Contents
- booking_mcp.py — the server: two tools, schemas with constraints, annotations, `ToolError`, logs on stderr
- test_booking_mcp.py — the tests in CI
- Registration in Claude Code

## booking_mcp.py
```python
"""Room booking MCP server: two tools, stdio transport. Logs only on stderr — stdout belongs to the protocol."""
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

ROOMS = {"room-1": {"name": "Vistula Room", "seats": 8, "blocked_by": None},
         "room-2": {"name": "Oder Room", "seats": 20, "blocked_by": None}}


class Room(BaseModel):
    id: str
    name: str
    seats: int
    free: bool


class FindResult(BaseModel):
    rooms: list[Room]
    total: int = Field(description="The number of all matching rooms, also beyond the limit")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def find_rooms(
    min_seats: Annotated[int, Field(ge=1, le=500, description="The minimum number of seats, e.g. 10")] = 1,
    limit: Annotated[int, Field(ge=1, le=50, description="How many rooms to return")] = 10,
) -> FindResult:
    """Find rooms with at least `min_seats` seats. Returns a list with information on whether the room is free."""
    hits = [Room(id=k, name=v["name"], seats=v["seats"], free=v["blocked_by"] is None)
            for k, v in sorted(ROOMS.items()) if v["seats"] >= min_seats]
    return FindResult(rooms=hits[:limit], total=len(hits))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True,
                                      openWorldHint=False))
def block_room(
    room_id: Annotated[str, Field(pattern=r"^room-\d+$", description="An identifier from find_rooms, e.g. room-1")],
    by: Annotated[str, Field(min_length=2, max_length=50, description="Who is blocking the room")],
) -> str:
    """Block the room for the person `by`. Calling it again by the same person changes nothing."""
    room = ROOMS.get(room_id)
    if room is None:
        raise ToolError(f"There is no room {room_id}. Use find_rooms to learn the identifiers.")
    if room["blocked_by"] not in (None, by):
        raise ToolError(f"Room {room_id} is taken by {room['blocked_by']}. Choose another room from find_rooms.")
    room["blocked_by"] = by
    log.info("room %s blocked by %s", room_id, by)
    return f"Room {room_id} blocked for {by}."


if __name__ == "__main__":
    mcp.run()  # stdio by default
```

## test_booking_mcp.py
```python
"""Tests of the MCP server without a model: an in-memory session (contract and behaviour) and a real process over stdio."""
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

import booking_mcp

pytestmark = pytest.mark.anyio

# Contract snapshot: the tool name, required parameters, annotations. A change = a deliberate decision about the version.
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
    assert result.structuredContent["rooms"][0]["id"] == "room-2"


async def test_conflict_is_tool_error_with_next_step():
    async with create_connected_server_and_client_session(booking_mcp.mcp._mcp_server) as client:
        ok = await client.call_tool("block_room", {"room_id": "room-1", "by": "anna"})
        again = await client.call_tool("block_room", {"room_id": "room-1", "by": "anna"})
        conflict = await client.call_tool("block_room", {"room_id": "room-1", "by": "jan"})
    assert not ok.isError and not again.isError
    assert conflict.isError
    assert "find_rooms" in conflict.content[0].text


async def test_invalid_input_is_rejected_by_schema():
    async with create_connected_server_and_client_session(booking_mcp.mcp._mcp_server) as client:
        result = await client.call_tool("block_room", {"room_id": "../etc", "by": "anna"})
    assert result.isError


async def test_real_stdio_process_handshake():
    # stdout polluted by print() would break this test — the protocol goes over stdout
    params = StdioServerParameters(command=sys.executable, args=[str(Path(booking_mcp.__file__))])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            tools = await session.list_tools()
    assert init.serverInfo.name == "booking"
    assert {t.name for t in tools.tools} == set(CONTRACT)


def test_stdout_carries_only_jsonrpc():
    # The specification: a stdio server must not write anything to stdout except MCP messages. The Python SDK client skips
    # foreign lines, so a session test will not detect it — we read the raw stdout of the process.
    import json
    import subprocess

    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "block_room", "arguments": {"room_id": "room-1", "by": "anna"}}},
    ]
    proc = subprocess.run([sys.executable, booking_mcp.__file__], input="\n".join(map(json.dumps, messages)) + "\n",
                          capture_output=True, text=True, timeout=30)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert len(lines) == 2
    assert all(json.loads(line)["jsonrpc"] == "2.0" for line in lines)
```

## Registration in Claude Code
Checked with `claude` 2.1.309: the server name before `-e` (the `-e` option accepts many values and will swallow the name).
```
claude mcp add --scope project booking -e BOOKING_ENV=dev -- python3 booking_mcp.py
```
The `project` scope writes `.mcp.json` to the repository:
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
You do not put secrets into `.mcp.json` (it goes into the repository). The `local` scope (the default) writes the configuration
to the user's `~/.claude.json`, in the section of the given project — checked with the same CLI; you keep tokens there or in the user's
environment variables.
