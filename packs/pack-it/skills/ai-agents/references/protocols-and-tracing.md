# Agent protocols and standard tracing

Contents: 1. Map of protocols · 2. Security at protocol junctions · 3. Tracing per the OpenTelemetry GenAI convention

## 1. Map of protocols
| Protocol | Who with whom | What it carries | When |
|---|---|---|---|
| **MCP** (Model Context Protocol) | agent ↔ tools and data | tools, resources, server prompts | the agent is to use the company's systems; many clients of the same tools (ai-mcp-server) |
| **A2A** (Agent2Agent) | agent ↔ agent, also across vendors and frameworks | **Agent Card** (name, description, version, interfaces, capabilities, security schemes, skills, optional signatures; at `/.well-known/agent-card.json`), tasks with a lifecycle | you delegate a task to an agent you do not control (a partner, another team), not just call a function |
| **ACP** (Agent Client Protocol) | editor ↔ coding agent (modelled on LSP) | JSON-RPC 2.0; locally stdio (the agent as a subprocess of the editor), remotely HTTP/WebSocket — support in progress; JSON types from MCP where possible, plus its own (e.g. diff), text in Markdown; the agent asks for consent through `session/request_permission` | you embed your own coding agent in an editor or an editor in an agent |

- The protocols **complement each other**: the same agent can be an MCP client (tools), an A2A server (for other agents)
  and an ACP agent (in the editor).
- **A2A task states** (`TASK_STATE_…`): `SUBMITTED`, `WORKING`; interrupted: `INPUT_REQUIRED`, `AUTH_REQUIRED`;
  terminal: `COMPLETED`, `FAILED`, `CANCELED`, `REJECTED`. You design the interrupted states like an approval point,
  not like an error. A task in a terminal state does not accept further messages.
- **Receiving updates:** polling (`GetTask`), an SSE stream (`SendStreamingMessage`, `SubscribeToTask`; requires
  `capabilities.streaming`) or a push webhook (requires `capabilities.pushNotifications`). `SendMessage` by default
  waits until a terminal or interrupted state; `returnImmediately: true` returns at once.
- **Results in artifacts, not in messages:** messages serve conversation and status and are not a guaranteed delivery
  channel; the task result is an `Artifact`.
- **Version:** the client sends `A2A-Version` (Major.Minor, e.g. `1.0`) in every request; the server treats a missing header
  as `0.3`. Version 1.0 removed the `kind` field (the type follows from the field name, e.g. `{"text": …}`, `{"statusUpdate": …}`)
  and moved `extendedAgentCard` to `capabilities` — a 0.3 client and a 1.0 server without support for both formats will not
  understand each other.
- Before you add A2A between your own agents in one process, check whether an ordinary subagent call is not
  enough. The protocol pays off at an ownership boundary (another team, another vendor).

## 2. Security at protocol junctions
- **An Agent Card and another agent's result are untrusted input:** a skill description can contain instructions, and a task
  result — an injection. You treat them like a tool result: a schema, limits, no executing commands from the content
  (sec-llm-security, `references/agent-design-patterns.md` §6). You check card signatures when the partner
  publishes them.
- You set authentication and permissions separately for every junction. A token from one protocol does not pass to
  another (the agent does not pass an MCP token to an A2A agent).
- **A2A directly:**
  - the server authenticates every request and narrows `ListTasks`/`GetTask` to the tasks visible to the caller; it does not
    reveal the existence of other parties' tasks (404 instead of 403);
  - `AUTH_REQUIRED` by itself **is not an authorization** of any operation; the credential is best out of band.
    If it passes in band through a chain of agents, it is bound to the agent that asked for it (a2a §7.6);
  - push webhook: the agent validates the URL (rejects private addresses, localhost, link-local — protection against SSRF), and the client
    checks the authentication of the notification, the expected `taskId`, and processes repetitions idempotently;
  - **Agent Card signature:** JWS (RFC 7515) on the card canonicalized per JCS (RFC 8785), the key through `kid`/`jku`
    over HTTPS; the client should check at least one signature before it trusts the card;
  - the extended card (`GetExtendedAgentCard`) only after authentication and without internal addresses or secrets.
- In ACP consent to a write and to a terminal command is in the editor, but the boundary is still the environment (core-agent-security).

## 3. Tracing per the OpenTelemetry GenAI convention
- **One trace per task** (`trace_id` as the correlation identifier across systems). Model calls
  (`chat`, `generate_content`), tools (`execute_tool`) and the agent (`invoke_agent`, `invoke_workflow`) are child
  spans. A retry is a new span in the same trace, and a fork or background work — `links`.
- **Attributes:**
  - `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`;
  - `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.usage.cache_read.input_tokens`;
  - `gen_ai.conversation.id`, `gen_ai.agent.name`, `gen_ai.tool.name`, `gen_ai.tool.call.id`.

  The convention does not define a cost attribute. You compute the cost from tokens and the price list in the pipeline, and put your own attributes (the guardrails
  result, cost) in your own namespace, not in `gen_ai.*`.
- **The content of prompts and replies** does not go into traces by default; the convention provides for explicit enabling. You enable it
  only with masking of personal data and with a retention set for sensitive data.
- There are also separate conventions for MCP and A2A. Thanks to them the trace crosses the protocol boundary.
- **Status:** the conventions have the status *Development*, so attribute names and types may change. You pin the version
  in the instrumentation, and compute SLOs and reports from your own end-of-task record (ops-observability, "Agent AI
  i dochodzenie po incydencie" (AI agent and incident investigation)), not from span names.
- From traces you build offline evaluation (ai-evals, `references/measurement-pitfalls.md` §7) and cost analysis
  (core-cost-control, ops-finops).

Sources (checked 2026-11-01 in the GitHub repositories; the pages a2a-protocol.org, agentclientprotocol.com
and opentelemetry.io unavailable from the session network):
- A2A: github.com/a2aproject/A2A — release 1.0.1 (2026-05-26, protocol version 1.0), a Linux Foundation project,
  `specification/a2a.proto`; the specification text from a2a-protocol.org/latest/specification passed on by a human
  2026-11-01 (§3, §7.6, §8.4, §13, appendices A–B);
- ACP: github.com/agentclientprotocol/agent-client-protocol — stable protocol version 1, schema release 1.14.0
  (2026-10-30), `docs/protocol/v1/transports.mdx` (stdio, Streamable HTTP in preparation), `tool-calls.mdx`; the introduction from agentclientprotocol.com passed on by a human 2026-11-01;
- OpenTelemetry: github.com/open-telemetry/semantic-conventions-genai (commit 2026-10-31), `docs/gen-ai/gen-ai-spans.md`,
  `gen-ai-agent-spans.md`, `mcp.md`, `a2a.md` — status Development;
- articles: "Agentic Communication Protocols" (0s & 1s, 2026-05-28), D. Biswas, "Observability for the Agentic
  Harness" (2026-08-04).
