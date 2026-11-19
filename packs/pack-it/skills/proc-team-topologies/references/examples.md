# Examples: Team Topologies

## 1. A "Backend" team swamped with requests
**Situation:** An online shop has the teams "Frontend" (6 people), "Backend" (8 people) and "DevOps" (3 people). Every
feature needs the work of all three; Backend has 40 open requests from others, and releasing a feature takes
several weeks of waiting in queues.

**How:**
1. Conway's law: teams divided by layers → the architecture and the flow of work are also divided by layers.
2. The context boundaries from ddd-strategic-analysis: Catalog, Orders, Payments, Pricing (discount rules).
3. The inverse Conway maneuver: stream-aligned teams around the contexts, one context → one owner.
4. Cognitive load: Pricing requires specialist knowledge → a separate complicated-subsystem team.
5. Infrastructure is provided by a platform as X-as-a-Service, not through tickets.

**Result:**

| Before | After | Type | Collaboration mode |
|---|---|---|---|
| Frontend + Backend (14 people) | Catalog team (5) | stream-aligned | uses the platform as X-as-a-Service |
| | Orders and Payments team (6) | stream-aligned | as above; with Pricing through an API |
| | Pricing team (3) | complicated-subsystem | X-as-a-Service (the pricing API) |
| DevOps (3) | Platform team (3) | platform | X-as-a-Service: a service template, a pipeline, monitoring |

The measure of change: the number of dependencies between teams per feature (before: 3 teams for every feature; the goal: one
stream-aligned team + platform services). Each remaining dependency is waiting.

## 2. Long-lasting "collaboration" as a signal of a wrong boundary
**Situation:** The Orders and Payments teams have had joint planning and a joint daily for half a year, and weekly
conflicts in the same code. "We collaborate great, it is just that everything takes long".

**How:**
1. Collaboration is expensive and is meant to be short — for the duration of discovery.
2. Half a year of collaboration → you look for a wrong boundary: both sides change the same model (the order's payment status).
3. You establish the context owner and the interface between the teams (the context map — ddd-context-mapping).
4. You announce the change of mode as a conscious decision with a date.

**Result:**

| | Before | After |
|---|---|---|
| Owner of the payment status | both teams | the Payments team |
| Interface | shared code, shared tables | a "payment accepted/rejected" event published by Payments |
| Collaboration mode | collaboration without end | collaboration for 2 more sprints to separate it out, then X-as-a-Service |
| Meetings | joint planning and daily | separate; a joint interface review once a quarter |

## 3. Introducing an internal developer platform
**Situation:** The Platform team wants all 7 teams to deploy only through the new portal from next month. The
stream-aligned teams were not asked.

**How:**
1. The platform as a product: the users are the stream-aligned teams; their feedback and adoption are the measure of success.
2. Imposing it from above risks "ShadowOps" — teams bypass the platform.
3. Start with one pilot team, then a voluntary move of the others.
4. Instead of rules in a wiki — a golden path with security, cost tags and observability built in.

**Result (a rollout plan):**

| Stage | Scope | Criterion for moving on |
|---|---|---|
| Pilot | the Catalog team, a service template + a pipeline | Catalog deploys a new service on its own, with no requests to Platform |
| Expansion | willing teams (the next 2–3) | adoption grows, user feedback collected and taken into account |
| Default path | all teams; the old paths phased out | no workarounds outside the platform |

An enabling team (2 people from Platform) teaches the teams for several weeks to use the golden path
(facilitating), and then leaves.
