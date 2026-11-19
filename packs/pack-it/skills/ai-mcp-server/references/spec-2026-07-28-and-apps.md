# The `2026-07-28` specification and MCP Apps

Contents: 1. What `2026-07-28` changes · 2. Migrating a server with a session · 3. MCP Apps — when an App and when text ·
4. App security · 5. A boundary probe

## 1. What `2026-07-28` changes
- **A stateless core:** there is no longer `initialize`/`notifications/initialized` or the `Mcp-Session-Id` header. Every
  request carries the protocol version and the client's capabilities in `_meta` (`io.modelcontextprotocol/protocolVersion`,
  `…/clientCapabilities`); the client should give `…/clientInfo`, and the server `…/serverInfo` in the result's `_meta`.
  An incompatible version → `UnsupportedProtocolVersionError` (code `-32022`). The server **must** handle `server/discover`
  (versions, capabilities, identity); on stdio the client can use it to check whether the server knows the new version.
- **The `Mcp-Method` and `Mcp-Name` headers** are required in Streamable HTTP. A gateway routes and authorizes by them without
  parsing the body; a tool parameter can go into a header through `x-mcp-header`.
- **Multi Round-Trip Requests (MRTR)** replace server-initiated requests (`sampling/createMessage`,
  `elicitation/create`, `roots/list`). The server returns `resultType: "input_required"` with the `inputRequests` field, and the client
  retries the original request with `inputResponses`. The server encodes the state between attempts in `requestState`. Every result has
  `resultType`; the client treats a result from an older server without this field as `complete`.
- **Lists with `ttlMs` and `cacheScope`** (`public` — intermediaries may cache them, `private` — not); `tools/list`
  in a stable order (better prompt cache hits on the client side).
- **Authorization:** the client checks `iss` in the authorization response (RFC 9207), and the client credentials are bound
  to the authorization server that issued them (keyed by `iss`, re-registration when the server changes).
- `subscriptions/listen` instead of GET and `resources/subscribe`; no resuming of the SSE stream (the client retries a broken
  request as a new one).
- **Tasks** (`tasks`) moved from the core to the official extension `io.modelcontextprotocol/tasks`;
  extensions are declared in `extensions` in the capabilities.
- **Deprecated** (they work for at least 12 months): Roots, Sampling, Logging, the HTTP+SSE transport, Dynamic Client
  Registration (Client ID Metadata Documents instead). Removed: `ping`, `logging/setLevel`.
- The error code "resource does not exist": `-32602` (was `-32002`); the range `-32020`…`-32099` is reserved for the specification
  (`HeaderMismatch` `-32020`, `MissingRequiredClientCapability` `-32021`, `UnsupportedProtocolVersion` `-32022`).

## 2. Migrating a server with a session
1. You move the conversation state to **explicit handles** issued by the server (e.g. `cart_id`, `draft_id` returned
   from a tool and passed in the next calls), with a lifetime and authorization on every use. You do not assume
   a binding to the connection.
2. You replace Sampling with a call to the model API on the server side (with its own key and limit) or with MRTR, when
   the decision is to belong to the client. You replace Roots with a tool parameter or configuration; logs go to stderr or to
   OpenTelemetry.
3. You add `server/discover` and version handling from `_meta`. If you support older clients, you keep both paths
   and test them in CI (a contract snapshot for each version).
4. You teach the gateway rules based on `Mcp-Method`/`Mcp-Name` instead of the URL path.
5. A change of behaviour visible to clients is MAJOR in the server version (core-semver).

## 3. MCP Apps — when an App and when text
MCP Apps (the extension `io.modelcontextprotocol/ui`, SEP-1865, status Stable since 2026-01-26) lets a server give
the host an interface: a `ui://…` resource of type `text/html;profile=mcp-app`, rendered in a sandboxed iframe that
talks to the host over MCP JSON-RPC.
- **An App only when the interaction has structure:** an approval, a form, a panel with actions, a comparison of results.
  An answer that the human only reads stays text.
- **One App per domain**, not per tool.
- **The data in the tool result**, not written into the resource's HTML; the resource is a template.
- **Graceful fallback:** a host without the extension gets structured content from the same tool.

## 4. App security
- **Tool visibility:** `_meta.ui.visibility` (by default `["model", "app"]`). The host hides a tool with `["app"]`
  from the model, but the App can call it. An action that only a human is to perform (e.g. "Approve") has
  `visibility: ["app"]`, so the model will not call it by itself.
- **Approval by the object's ID and version:** the button sends `invoice_id` and `version`. The server rejects an approval
  of a stale card (the object changed after it was displayed).
- **The UI is not a trust boundary:** authorization, validation, idempotency and audit are on the server side, just as with
  any tool call. You treat the App as untrusted code: you declare a narrow CSP (`connect-src`,
  `frame-src 'none'`, if nesting is not needed).

## 5. A boundary probe
A path filter in the server's file tool (the resolved path, `..`, symbolic links) protects only that
tool. Before granting access you perform one needed operation and one excluded operation and record which layer
stopped it (the agent, the tool, the environment): core-agent-security, `references/permissions-and-production.md` §4b.

Sources (checked 2026-11-01 in the repositories): github.com/modelcontextprotocol/modelcontextprotocol —
`docs/specification/2026-07-28/changelog.mdx` (commit 2026-10-31); github.com/modelcontextprotocol/ext-apps —
`specification/2026-01-26/apps.mdx` (status Stable, commit 2026-10-29). modelcontextprotocol.io was unavailable from the session's
network, but the changelog content provided by a human on 2026-11-01 is consistent with the repo. An item in the TODO:
blog.modelcontextprotocol.io (2026-10-29).
