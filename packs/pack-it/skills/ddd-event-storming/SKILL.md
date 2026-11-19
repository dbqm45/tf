---
name: ddd-event-storming
description: Use for Event Storming (Big Picture, Process, Design Level) — preparation, facilitation, write-up.
metadata:
  review: "2027-10-17"
  catalog: "Use when planning, running and writing up an Event Storming session — Big Picture, Process Level, Design Level — and when moving from the session's results to architecture. Not for techniques of working with people and language (ddd-facilitation) or details of implementing aggregates (ddd-tactical-design)."
---

# Event Storming

Event Storming is joint modelling of domain events on a timeline. The events are the "pizza dough":
the rest of the notation are toppings that you add only when they help answer the session's question.
It is a variant of ModelStorming — the goal is shared understanding, not a pretty diagram.

## 1. Before you start: what is this session for?
Settle one question the session is to answer, and choose the format:

| Format | Session question | Whom to invite | What comes out |
|---|---|---|---|
| **Big Picture** | How does the whole business / a large area work? Where does it hurt? Where are the boundaries? | broadly: business + IT; "those who have questions and those who have answers" | a timeline, pivotal events, hot spots, context candidates, problem priorities |
| **Process Level** | How exactly does this one process work? | process experts + the team | the process in full grammar (commands, policies, read models), rules, questions |
| **Design Level** | How do we build this in this context? | the team + a domain expert | aggregates/constraints, events, commands → ready for implementation |
| Value Driven | Where is value created and lost? | business | value +/- on the timeline, value stream |
| UX Driven | What does the user see and feel? | product, UX | read models / screens on the timeline, moments of frustration |
| Retro | What really happened (an incident, a project)? | the team | an event timeline, causes, opportunities |
| Onboarding | How do we introduce new people to the domain? | newcomers + veterans | a shared map as starting material |

Do **Big Picture** first if you do not know where you are (see ddd-strategic-analysis → Cynefin).

## 2. Notation — colours and grammar

| Element | Colour | Notation |
|---|---|---|
| Domain event | orange | past tense, business language: "Order was paid" |
| Hot spot | pink/purple (neon) | a question, conflict, risk, "we do not know" |
| Actor | small yellow | a person/role/department |
| External system | wide pink | an IT system, a supplier |
| Opportunity | green | an idea for an improvement |
| Value | small red/green | loss / gain of value |
| Command | blue | an intention/decision: "Pay for the order" |
| Policy | lilac | "When X, then Y" — a reaction to an event |
| Read model | green | information needed to make a decision |
| Aggregate / constraint | large yellow | a rule that can reject a command |

**Process Level grammar** (every step must "close"):
`Actor + Read model → Command → System/Aggregate → Event → Policy → Command → …`
Every event either triggers a policy, or ends a path, or updates a read model. A gap in the chain = a hot spot.

**Design Level**: `Command → Aggregate (invariants) → Event(s)`; a rejection event is also an event.

**Introduce the notation gradually** — at the start only orange events and hot spots. Add actors and systems
after ordering the timeline, commands/policies/read models only at the process level. The legend hangs on the
wall and grows with the session. The whole notation at once = participants discuss colours instead of the business.

## 3. Big Picture — the flow
1. **Chaotic exploration** — everyone writes events on their own (past tense) and sticks them roughly in time order. No discussion, no correcting others. Quantity > quality.
2. **Enforcing the timeline** — we remove duplicates, merge synonyms (but synonyms are a signal about language — write them down!), set the order, mark parallel paths.
3. **Pivotal events** — see §4. They split the timeline into chapters.
4. **Swimlanes** — horizontal lanes, when processes run in parallel or when responsibility passes between departments/actors. A lane = "whose story this is". A branching process → separate lanes from the decision point.
5. **People and systems** — who/what causes the events; where responsibility passes.
6. **Walkthrough** — one of the participants narrates the flow from left to right; every "uhh… it depends" is a hot spot. **Reading from the end** (reverse narrative) also helps: "what must have happened for this event to occur?" — it catches missing events.
7. **Problems and opportunities** — hot spots and green notes; then **dot voting** on the most important problems.
8. **Emerging contexts** — outline areas with a coherent language and responsibility (see ddd-strategic-analysis).

### Key (branching) questions
Collect the questions the business asks **in many places of the process** and on which depends which way the process goes
("Is the customer verified?", "Do we have free resources on this date?", "Has the limit been exceeded?").
Each such question is a candidate for: a read model, a policy, a separate capability or a separate context
that "owns the answer". List them with the places where they come up.

## 4. Pivotal events
A pivotal event is one after which "the world is different": responsibility changes, other rules apply,
new actors appear, the matter becomes hard to reverse.
Example: "Photo upload started", "Photo tagged", "Thumbnail generated" are steps; the pivotal one is
"**Photo was published**" — from that moment others see it, other rules apply (moderation, copyright).
Test: does the business celebrate / report this event? does the owner of the matter change after it? is it hard to undo?
Pivotal events are natural boundaries of the timeline's chapters and frequent boundaries of contexts.

## 5. As-is, to-be and the starting point
- **We know the process (we are not discovering anything anew)** — place two boundary events **Begin** and **End** (e.g. "Request
  received" … "Case closed") and fill the space between them with the **as-is** state. Then, as a separate layer
  (a different colour/lane), model the **to-be** and mark the differences. The boundaries keep the session from spilling over.
- **We know nothing — we are discovering, exploring** — do not force Begin/End. First settle a few **pivotal events**
  as scaffolding, and only then add the events between them.

## 6. From the session to architecture
| Element from the session | What usually follows from it |
|---|---|
| pivotal events, a change of language, swimlanes | context/module boundaries |
| a policy "when X, then Y" | an event handler, a saga / process manager (long processes) |
| read model | the read side (CQRS), a projection, a query |
| command | an application service method / an endpoint at the module edge |
| a constraint on a yellow note | an aggregate invariant → a consistency boundary |
| external system | an ACL or an Open Host Service (ddd-context-mapping) |
| hot spot | a question for an expert, a spike, a risk in the backlog |
| key question | a read model / a separate capability / a context that owns the answer |

## 6a. Formal process notation (BPMN, EPC)
Event Storming serves discovery; when a process must be handed over precisely (many roles and systems, audit requirements,
a process engine), write it down after the workshop:
- **BPMN 2.0**: events (start, intermediate, end), activities, gateways (exclusive XOR, parallel AND, inclusive OR,
  event-based), pools/lanes for roles and systems, message flow between participants. Mapping
  from the workshop: domain event → an event or the result of an activity, command → an activity, policy → a gateway or an
  intermediate event, actor → a lane.
- **EPC** (event-driven process chain): alternating event → function → event, with
  AND/OR/XOR connectors; found in organisations that use ARIS and SAP.
- A simple flow without many roles: Mermaid `flowchart` (docs-tech-writing, `diagrams-and-presentations.md`).
A process diagram does not replace the domain model — rules and invariants stay in aggregates and policies.

## 7. How you run it as an agent (without a physical wall)
You are the facilitator: **you ask and you write down**, while people provide the knowledge and decisions. The session goes through 5 phases:
session context → events → commands and policies → aggregates → contexts and map. You load the card **of the current
phase only** from `references/agent-phases.md`, where the turn protocol also is.
- **Board:** `python3 .claude/skills/ddd-event-storming/scripts/es_board.py init --id YYYY-MM-DD-<topic> --topic … --question …`,
  then `add`/`edit`/`move`/`undo`/`resolve`. The event log is in `docs/project/02-domain/event-storming/<id>/`,
  and `show` writes `board.md` according to `references/board-template.md`. The script rejects a note of a later phase
  (mixing levels).
- **One turn is one question or one small move.** You mark your own proposals **[proposal]** and add them after
  consent. **You do not invent business facts**: every assumption is a hot spot.
- **End of a phase:** `check` must be without gaps, and the gaps become questions or hot spots, not your guesses.
  The human decides about moving on to the next phase.
- **Aggregates and the context map:** in these late steps model errors accumulate. Before the human's consent, commission
  a review in a fresh context (a read-only implementer, details in the phase card). The context map is an ADR.
- As you go, you catch language signals (ddd-facilitation), ask modelling questions (ddd-deep-modeling)
  and update the glossary `docs/project/02-domain/glossary.md`.

## Additional materials
- `references/session-scripts.md` — minute-by-minute scripts of Big Picture / Process / Design sessions, room preparation, the remote version.
- `references/board-template.md` — a template for writing up the board in Markdown + Mermaid.
- `references/agent-phases.md` — a session run by the agent: the turn protocol and the cards of the 5 phases (exit criteria, gates).
- `scripts/es_board.py` — the session board: an event log with undo, a check of the phase structure, a Markdown write-up.

## Input from a board (a photo, an export)
When you get a photo or an export of the wall: read **the flow along the lanes** (numbered steps with the note type in brackets), pivotal
events and hot spots as indexes to the steps, uncertainty explicitly (`[illegible]`), a gate with a random sample of notes.
Procedure and format: ddd-discovery-intake → `.claude/skills/ddd-discovery-intake/references/board-reading.md`. At Big Picture only events and hot spots are allowed —
other note types are a signal of mixing levels (self-check in ddd-facilitation).
