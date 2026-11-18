---
name: ai-mcp-server
description: Use for building your own MCP server — whether MCP, transport, the tool contract, security and auth, CI tests without a model, versions, registering in Claude Code.
metadata:
  review: "2027-01-23"
  catalog: "Use when you build your own MCP (Model Context Protocol) server for agents — the decision: an MCP server or a skill with a script, the transport (stdio, Streamable HTTP) and its rules, tools as a contract (names, schemas with constraints, readOnly/destructive/idempotent annotations, errors with a next step), security (stdout only for the protocol, the tool result as untrusted data, confirmation of destructive operations, OAuth 2.1 authorization with a token audience, no passing the token on, Origin and localhost), CI tests without a model (an in-memory session, a contract snapshot, a stdio process, raw stdout), tool versioning, registration in Claude Code (.mcp.json, scopes). Not for designing the agent loop and choosing tools on the agent side (ai-agents), assessing and connecting third-party MCP servers (core-agent-security), LLM application threats in general (sec-llm-security) or quality evaluation on a model (ai-evals)."
  keywords: "serwer MCP, MCP server, Model Context Protocol, własny serwer mcp, wystawić API jako MCP, narzędzia dla agentów, FastMCP, mcp python sdk, typescript sdk mcp, stdio, streamable http, testy serwera mcp, MCP Inspector, .mcp.json, claude mcp add, autoryzacja mcp, oauth mcp, token mcp, readOnlyHint, destructiveHint, skill czy serwer mcp, 2026-07-28, mcp-session-id, bezstanowy mcp, sampling przestarzały, mrtr, mcp app, mcp apps, interfejs w czacie, przycisk zatwierdź, ui://, own mcp server, expose an API as MCP, tools for agents, mcp server tests, mcp authorization, skill or mcp server, stateless mcp, sampling deprecated, interface in the chat, approve button"
---

# Your own MCP server

The build process and the SDK guides (Python, TypeScript) are provided by the official Anthropic skill `mcp-builder`
(github.com/anthropics/skills, Apache 2.0) — audit it before installing (core-agent-security). This skill adds what
is not there: the decision, security, CI tests, versions and registration in Claude Code. Designing tools on the
agent side: ai-agents.

## Procedure
1. **An MCP server?** A server, when **many clients** use the same tools (Claude Code, other agents,
   an application) or when you need state, a connection or authentication that cannot be safely given to
   a script. One team in Claude Code and a simple API call → a skill with a script (core-skill-authoring): less
   code, no process to maintain.
2. **Transport**: stdio for a local server (a process of the client), Streamable HTTP for a remote one. Rules:
   - stdio — on stdout **only** MCP messages (the specification: "MUST NOT"); logs on stderr. The Python SDK client
     skips foreign lines, other clients may drop the connection — the raw stdout test checks this;
   - HTTP — validation of the `Origin` header (403 for an unknown one), locally listen only on `127.0.0.1`.
3. **Tools as a contract**: a name of a verb + a thing, a description "what and when", an input schema with constraints
   (range, pattern, length), a structured result, `readOnlyHint` / `destructiveHint` /
   `idempotentHint` / `openWorldHint` annotations that tell the truth. An error is a tool result with a next step ("use
   find_rooms"), not a protocol exception. A list with pagination and a limit.
4. **Security**:
   - a tool result is data for the model, not instructions — mark content from external systems as foreign,
     do not execute instructions from data (sec-llm-security);
   - destructive operations: a separate tool with `destructiveHint`, confirmation on the client side, idempotency;
   - a remote server with authorization: OAuth 2.1, the server accepts only tokens issued **for it** (the audience,
     RFC 8707), an invalid token → 401; **it does not pass the client's token on** to the API behind it (the
     "confused deputy" problem) — for the API it uses its own credentials with minimal permissions;
     client registration through Client ID Metadata Documents (DCR deprecated), PKCE, `iss` (RFC 9207),
     `application_type` for CLI and desktop clients — the state of the `2026-07-28` specification: be-auth-security,
     `.claude/skills/be-auth-security/references/tokens-sessions-oauth.md` §7;
   - secrets from environment variables, never in `.mcp.json` in the repository.
   - an interface for a human (MCP App): an action only for a human with `_meta.ui.visibility: ["app"]`, approval
     with the object's ID and version, authorization and validation on the server — `references/spec-2026-07-28-and-apps.md` §3–4;
5. **CI tests without a model** (a template in `references/server-and-tests.md`): an in-memory session
   (`create_connected_server_and_client_session`) — a contract snapshot (names, required parameters, annotations),
   a structured result, errors, rejection of bad input by the schema; a real process over stdio; raw stdout
   with JSON-RPC only. Manually: MCP Inspector. The quality of use by a model — evaluation (ai-evals, 10 questions according to
   `mcp-builder`).
6. **Specification version:** `2026-07-28` is stateless (no `initialize` and `Mcp-Session-Id`, `server/discover`,
   the `Mcp-Method`/`Mcp-Name` headers, MRTR instead of Sampling and server-initiated requests). A server with a session moves its state to explicit
   handles — `references/spec-2026-07-28-and-apps.md` §1–2.
7. **Versions**: the tool contract is the server's public API — removing a tool, renaming it or a new required
   parameter is MAJOR; a new tool or an optional parameter is MINOR (core-semver). You introduce an incompatible change
   with a new tool and the deprecation of the old one; the contract snapshot in the test forces a deliberate decision.
8. **Registration in Claude Code**: `claude mcp add --scope project <name> -e KEY=value -- <command>`
   (the name before `-e`) writes `.mcp.json` to the repository; the `local` scope — the user's configuration with secrets.
   Permissions for the server's tools in the settings as for any tool (`mcp__<server>__<tool>`).

## Example
The `booking` server (Python, `mcp` 1.29.0): `find_rooms(min_seats, limit)` — read-only, a structured result
with `total`; `block_room(room_id, by)` — `room_id` with the pattern `^room-\d+$`, idempotent for the same person,
a conflict → `ToolError("Room room-1 is taken by jan. Choose another room from find_rooms.")`. Six tests
in CI without a model; the raw stdout test detected an added `print()` that the session test did not notice. Code, tests
and `.mcp.json`: `references/server-and-tests.md`.

## Checklist
- [ ] a justification "a server, not a skill" (clients, state, authentication)
- [ ] stdout only JSON-RPC (a test), logs on stderr; with HTTP `Origin` and localhost
- [ ] schemas with constraints, annotations consistent with the behaviour, errors with a next step
- [ ] tokens only for this server, not passed on; secrets outside the repository
- [ ] a contract snapshot in CI, a contract change = a decision about the version

## Sources
- The MCP specification 2026-07-28 (changelog) and MCP Apps 2026-01-26 — checked 2026-11-01, details in the references.
- The MCP specification 2025-11-25: "Transports", "Authorization", "Security Best Practices"
  (github.com/modelcontextprotocol/modelcontextprotocol, commit dae694f, accessed 2026-10-23).
- Python SDK `mcp` 1.29.0 (PyPI), Claude Code 2.1.309 (`claude mcp add --help`) — checked in operation 2026-10-23.
- Anthropic, the `mcp-builder` skill (github.com/anthropics/skills, commit dbd4588, Apache 2.0) — a reference, no content was taken over.
Described in our own words.
