# Event Storming run by the agent — phases and the turn protocol

The agent is the facilitator and scribe, while people provide the domain knowledge and decisions. You read **only the card of the current phase**:
fewer rules at once means fewer mistakes as the board grows. The board is kept by a script (zero tokens):
`python3 .claude/skills/ddd-event-storming/scripts/es_board.py <command> --id <session-id>`.

## Turn protocol (each of your replies during the session)
1. **Write down what the human said**: `add`, `edit`, `move`, `resolve`. In their words, without embellishing.
2. **Make one move:** one question or one small proposal. You do not lecture on theory and do not solve the model
   for people. You ask so as to draw out knowledge ("what must have happened earlier?", "who decides about this?").
3. **Mark your own proposal `[proposal]`** and add it to the board only after the human's consent.
   A business fact that no one has confirmed you write down as a hot spot, not as a note.
4. **Missing domain knowledge:** ask a domain expert, i.e. a read-only implementer (e.g. the persona's domain analyst,
   `specialist` with domain skills). Their answer is a proposal for the people, not a fact on the board.
5. **Every few turns show the state:** `show` (briefly: what was added, what is missing), not the whole board after every sentence.

## Phase 1 — session context
- **Goal:** one session question, the scope (what is outside), the format (Big Picture, Process, Design), actors and systems.
- **Notes:** `actor`, `system`, `hotspot`, `opportunity`.
- **Moves:** "What question should this session answer?", "Where does this process start and end?".
  You read the domain context (the glossary, `docs/project/02-domain/`) once, at the start.
- **Exit:** the session question and the boundaries are recorded (`init --question`), the human confirms the scope.

## Phase 2 — events
- **Goal:** as many domain events on the timeline as possible.
- **Notes:** `event` is added (`--pivotal` for pivotal events).
- **Moves:** "List 10–20 things that happen, in the past tense". Then ordering the timeline (`move`),
  synonyms as a signal for the glossary, and pivotal events. Finally a narrative from left to right and from the end.
- **Typical errors:** an event in the imperative mood ("Send the parcel" is a command), a technical event instead of
  a business one ("Record saved"), an early discussion about solutions.
- **Exit:** a timeline without obvious gaps, pivotal events marked, hot spots recorded, and the human says "next".

## Phase 3 — commands and policies
- **Goal:** what triggers each event and what happens automatically afterwards.
- **Notes:** `command` (`--causes`, `--actor`), `policy` (`--on`, `--issues`), `readmodel` (`--for`) are added;
  an event from outside: `edit E --by S`.
- **Moves:** for each event "what caused it?", "what did the actor need to know?", "what happens
  on its own afterwards?". Error and rejection paths are events too.
- **Check:** `check` → an event without a trigger, a command without an event, a policy without "when/then".
  A gap is a question for the people or a hot spot. You do not fill it yourself.
- **Exit:** `check` without gaps or the gaps turned into hot spots; the human accepts.

## Phase 4 — aggregates
- **Goal:** which part of the system guards the rules for each command (the consistency boundary).
- **Notes:** `aggregate` is added (`--handles`). A command to an external system: `edit C --to S`.
- **Moves:** "what rule can reject this command?", "what must be consistent immediately, and what may arrive later
  by an event?". Names come from commands and events, not from database tables.
- **Rules (ddd-tactical-design):** small aggregates; other aggregates are referenced only by identifier; reactions
  between aggregates go through events. `check` warns about an aggregate with more than 7 commands.
- **Human gate (mandatory):** in late steps model errors accumulate, so the aggregates are approved by
  the human. Before that, a review in a fresh context: `specialist` with ddd-tactical-design gets `board.md`
  and answers which aggregates are too large, too small or badly named.
- **Exit:** `check` without gaps, the review discussed, the human's consent.

## Phase 5 — contexts and map
- **Goal:** bounded contexts, their subdomain type and the relations between them.
- **Notes:** `context` (`--contains`, `--kind core|supporting|generic`) and `link` (`--from`, `--to`,
  `--pattern`) are added.
- **Moves:** you look for boundaries at pivotal events, a change of language and a change of owner. At every
  arrow you ask who is upstream, whether a protective layer (ACL) is needed and what the message format is.
  The patterns are described by ddd-context-mapping.
- **The subdomain type sets the effort:** core means the best people and full DDD; supporting is simpler; generic means buy
  or integrate through an ACL.
- **Typical errors:** boundaries from the org chart instead of from language and responsibility, one "universal" model of the
  same concept in several contexts, a shared kernel without need.
- **Human gate (mandatory):** the context map is a decision that is hard to reverse, so record it as an ADR.
  The review in a fresh context is done by `architect` or `specialist` with ddd-strategic-analysis and ddd-context-mapping.
- **Exit:** `check` without gaps, the map approved.

## After the session
- `show` writes `board.md` next to the log. You update the glossary in `docs/project/02-domain/glossary.md`,
  and decisions in the project record (core-project-record).
- Open hot spots are tasks with the owner of the question. The session is a starting point, not the final model: the boundaries
  are tested only by delivering code.
