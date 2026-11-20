# Principal / Distinguished Engineer / Fellow — Frontend

> **Contents:** Technology vision and platforms at extreme scale · The frontend/backend/infrastructure boundary · Influence on industry standards · Career sponsorship and technical culture · Summary — how to use this file

Level: the horizon of decisions goes beyond one company — technology vision, platforms at extreme scale,
the frontend/infrastructure boundary, influence on industry standards, developing the technical staff. Lens: **the whole
company and/or the industry**.

## Technology vision and platforms at extreme scale

At this level the problem is not "how to build this feature" but "which architecture will remain right in 3–5
years, when the scale (users, teams, code) grows by an order of magnitude". Practical implications:

- **Reversible vs irreversible decisions** — a Principal recognizes which architectural decisions are easy
  to reverse later (the choice of a UI library in one module) and which are practically irreversible after
  rollout at scale (the data model in a shared API, the choice of a framework for hundreds of teams, the contract of a
  Design System used by the whole ecosystem) — and applies disproportionately more decision rigour
  to the second category, consciously sparing that rigour on the first (so as not to freeze the organization in
  analysis-paralysis over decisions that can be changed anyway).
- **The platform as a product for other engineers** — at this scale the frontend stops being "a website" and becomes
  a **platform** (Design System, component library, internal SDKs, standards) treated with the
  same rigour as an external product: it has its own roadmap, versioning, a migration path for internal
  users (other teams), and a measured level of adoption.
- **A technical anchor (north star)** — a Principal formulates and communicates a long-term architectural
  vision (e.g. "in 2 years every new product starts from this one platform template"), against which
  individual teams can assess on their own whether their local decision is heading in the right direction, without
  the need for central approval of every decision — this scales decision-making without scaling bureaucracy.

## The frontend/backend/infrastructure boundary

At the Principal level the boundary between "frontend" and "non-frontend" blurs — decisions require an understanding
of the infrastructure the frontend actually runs on.

### Edge Computing

Running code (usually lightweight, request-scoped) on network nodes **geographically closest**
to the user, instead of in one central data center — it reduces network latency (RTT) for logic that
would previously have required a round-trip to a central server. Typical frontend uses: personalization/
A-B testing without content flicker (the decision is made on the edge, before the HTML is sent to the client, instead of on
the client side with a visible jump), geographic/localization redirects, lightweight authorization
before reaching the origin. Limitation: the edge environment usually has a **smaller** set of available APIs/
execution time than a full server (no long-lived connections, memory/CPU time limits) — a Principal must
recognize which logic **qualifies** for the edge (fast, stateless or with little state) and which must
stay in the traditional backend.

### CDN (Content Delivery Network)

A network of servers caching static (and increasingly partly dynamic) resources close to the user.
At the Principal level the key decisions are not "whether to use a CDN" (that is already the baseline) but: the cache
invalidation strategy on deployment (how a new version of the application reaches all points of presence without
a window in which different users get incompatible JS/CSS versions — a problem especially relevant with
frequent deployments by many independent teams, see Micro-frontends in `staff.md`), and the boundary between
what the CDN can cache aggressively (assets with a hash in the name, safe to cache "forever") and
what requires revalidation (HTML, personalized data).

### Serverless

An execution model in which the infrastructure (scaling, machine provisioning) is managed entirely by
the provider — code runs as short-lived functions invoked on demand, billed for the actual execution
time, not for a maintained server. Trade-offs relevant at the Principal level: **cold start** (the latency of
the first invocation after a period of inactivity, when the environment must initialize from scratch) as
a real risk for paths requiring low, predictable latency; no long-lived local state
(every invocation may hit a different instance), forcing state to be moved to an external
store; and the benefit: no need to manage capacity/scaling for highly
variable traffic (sudden peaks), which directly reduces the team's operational load (a DevEx cost, see
`devex.md`, "toil").

**The overriding rule for this section:** a Principal does not have to be able to configure edge/CDN/serverless
infrastructure on their own (that is usually the role of the platform team — proc-team-topologies; tools — ops-*) — they must be able to **talk with
that team as an equal**, understand the trade-offs deeply enough to make a joint decision
about where the frontend/infrastructure responsibility boundary lies for a particular problem.

## Influence on industry standards

### Open Source

At the Principal/Distinguished level participation in open source stops being a hobby and becomes a strategic
tool: maintaining/releasing an internal tool under a free licence builds the company's reputation as a
technical employer (recruitment), lets external contributors fix bugs instead of the
internal team (reducing the maintenance cost), and creates pressure on API quality (code used publicly
must have a clear, stable contract, which in itself is often healthy for internal users too).
Trade-off: a public API requires a formal deprecation/versioning process (SemVer, see
core-conventional-commits), which an internal tool might not require.

### TC39

The committee standardizing **the JavaScript/ECMAScript language** — new language features (e.g. optional chaining,
`Array.prototype.toSorted`, decorators — lang-javascript, lang-typescript) go through a formal
process (Stage 0 "idea" → Stage 1 "formal proposal" → Stage 2 "syntax draft" → Stage 2.7 "approved
in principle, waiting for test262 tests" (a stage added in 2024) → Stage 3 "candidate, implementations in engines" →
Stage 4 "finished, goes into the next ECMAScript edition"). A Principal
at the Distinguished/Fellow level can really **participate** in this process (propose, review
proposals) — even without that, tracking the stage of a particular proposal is a practical competency:
production code should not depend on language features below Stage 3/4 without transpilation and explicit acceptance of the
risk of a syntax change before finalization.

### W3C

The consortium standardizing **the web platform** (HTML, CSS, accessibility/WCAG — see `staff.md`, browser
APIs) through Working Groups. As with TC39, influence at this level consists in real participation
in working groups (reporting use cases from the company's real production scale, reviewing specifications)
— a company using the web platform at large scale has a real interest in new standards (e.g. new
CSS selectors, new accessibility APIs) matching its actual needs before they become an irreversible
standard.

## Career sponsorship and technical culture

At the Principal level influence on people goes beyond direct mentoring (the domain of a Senior, see
`senior.md`) — it is **shaping the technical culture of the whole organization**:

- **Sponsorship vs mentoring** — mentoring is developing a person's competencies in conversation with them; **sponsorship**
  is actively using one's own position/visibility to open opportunities for that person that they have no
  access to on their own (a recommendation for a difficult, visible project, putting them in a meeting with decision-makers) — the difference
  is a frequent point at which career growth at higher levels stalls, because good mentoring without
  sponsorship does not translate into real promotion opportunities.
- **A culture of code review and standards as a cultural artifact, not only a process** — at the Principal level,
  how the organization **treats** production errors (looking for someone to blame vs a blameless postmortem), how it treats
  differences of technical opinion (open discussion with a clear resolution mechanism vs political
  wrangling), and whether it documents architectural decisions in a reproducible way (e.g. Architecture Decision
  Records — docs-tech-writing) — all of this is the result of conscious shaping by the most influential engineers in
  the organization, not of chance.
- **Recognizing and developing future Staff/Principal engineers** — identifying which engineers in the organization
  have the potential to move to a higher lens (from one repo to many teams, from many teams to
  the whole company/industry) and actively giving them opportunities to practise that lens **before** a formal promotion
  (e.g. asking a Staff engineer to represent the company in an external Working Group) — this is the
  practical difference between an organization that **has** further Principal engineers when it needs them and
  an organization that has to look for them on the market.

## Summary — how to use this file

The content of this file is by nature more strategic/organizational than technical — unlike
`senior.md`/`staff.md`, which can be applied directly to a particular piece of code, this file serves
mainly for: (a) assessing whether a given problem really requires this lens (see `SKILL.md`, "Which lens
to apply" — not every large code change is a Principal decision), and (b) providing the language/frameworks to
justify decisions at this level to someone outside the engineering team.
