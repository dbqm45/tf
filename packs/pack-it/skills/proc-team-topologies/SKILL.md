---
name: proc-team-topologies
description: Use for team structure and their interactions — four team types, collaboration modes, Conway's law.
metadata:
  review: "2027-10-17"
  catalog: "Use when designing the structure of teams and their interactions — four team types, three collaboration modes, cognitive load, Conway's law and aligning teams with DDD context boundaries. Not for the rituals of a team's work (proc-agile) or SAFe scaling (proc-safe)."
  keywords: "jak ułożyć zespoły, przeprojektować zespół organizacyjnie, zespół zawalony prośbami, zespół platformowy, zespół produktowy, zespół strumieniowy, zespół wspierający, prawo Conwaya, architektura a struktura zespołów, obciążenie poznawcze zespołu, platforma wewnętrzna, how to arrange teams, reorganize a team, team swamped with requests, platform team, product team, stream-aligned team, enabling team, Conway's law, architecture and team structure, team cognitive load, internal platform"
---

# Team Topologies

## Team types
| Type | Role |
|---|---|
| **Stream-aligned** | delivers value end-to-end in one stream (a product, a context, a customer segment) — most teams |
| **Platform** | provides internal services as a product (self-service) to reduce the load on stream-aligned teams |
| **Enabling** | temporarily helps teams acquire a skill (e.g. testing, observability), then leaves |
| **Complicated-subsystem** | maintains a part that requires specialist knowledge (e.g. a pricing engine, an allocation algorithm) |

## Collaboration modes
- **Collaboration** — close cooperation for the duration of discovery (short, expensive).
- **X-as-a-Service** — consumption through a clear interface (the default goal for a platform).
- **Facilitating** — an enabling team teaches others.
A change of mode is a conscious decision; a long-lasting "collaboration" usually means a wrong boundary.

## Rules
- A team's **cognitive load** is limited — choose the boundaries of responsibility so that the team understands its part as a whole.
- **Conway's law** — the architecture mirrors the communication structure; the **inverse Conway maneuver**: arrange the teams
  the way you want the architecture to look.
- **Teams around context boundaries** (ddd-strategic-analysis): one context → one owning team; the relationships on the context
  map (ddd-context-mapping) correspond to the collaboration modes (e.g. Open Host Service ≈ X-as-a-Service).
- Measure the dependencies between teams — each one is waiting.

## The platform as a product
A platform team (e.g. an internal developer platform, IDP) works like a product team:
- it has a product manager and users (stream-aligned teams), collects their feedback and measures adoption;
- it starts with one pilot team before the platform becomes mandatory — imposed from above it breeds "ShadowOps";
- it provides **golden paths**: templates and modules with security, cost tags and observability built in,
  instead of rules in a wiki;
- the "build a portal (e.g. Backstage) or buy" decision counts the full cost: several full-time people for several months to a first
  useful version, plugin maturity, no built-in RBAC in the open-source version.
Sources (devops.com): [Tips for Managing Internal Developer Platforms](https://devops.com/tips-for-managing-internal-developer-platforms-idps/),
[Is Backstage the Right Internal Developer Portal for You?](https://devops.com/is-backstage-the-right-internal-developer-portal-for-you/) (a vendor's article),
[Policy as Code for Cost Control](https://devops.com/policy-as-code-for-cost-control-not-just-compliance/)

## Example
**Situation:** the teams "Frontend", "Backend" (40 open requests) and "DevOps"; a feature waits in three queues.
**Result (the inverse Conway maneuver):** a feature needs one stream-aligned team and services instead of three.

| Before | After | Type, mode |
|---|---|---|
| Frontend + Backend | Catalog; Orders and Payments | stream-aligned |
| | Pricing (discount rules) | complicated-subsystem, X-as-a-Service |
| DevOps | Platform | platform, X-as-a-Service |

More examples: `references/examples.md`.
