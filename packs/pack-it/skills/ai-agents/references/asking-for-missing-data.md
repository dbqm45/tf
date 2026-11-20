# Asking for missing information

An agent that guesses missing data makes errors that look like correct work: the address from a previous order,
a deadline of "in a week". An agent that asks about everything shifts the work onto the human and teaches them to click "yes" without
reading. Both errors come from the same thing: the lack of a rule for when to search, when to assume and when to ask.

## 1. When to ask

| Situation | What the agent does |
|---|---|
| The information can be found: in the context, in files, in the CRM, in the order history, through an API | **searches** with a tool; does not ask |
| The gap is cheap and reversible (report format, order of sections, a minor value) | **assumes** a reasonable default value, records the assumption in the result and goes on |
| A human decision is needed: a preference, a trade-off, consent to a cost or a risk | **asks** |
| Data is missing that cannot be filled in (conflicting sources, no permissions, an empty field in the system) and the result depends on it | **asks** |
| The action is irreversible or costly, and the data is uncertain | **asks before the action** (approval: `references/executors-and-gates.md`, step 6 of SKILL.md) |

The rule "always ask when you are not sure" is too broad: there is almost never certainty. Ask when an error would be
expensive, and the answer cannot be obtained on your own.

## 2. Tools first
- Before the agent asks, it checks the places where the information may be. You write their list in the tool prompt
  or in code: the CRM, previous orders, account settings, case documents.
- In the question it shows what it checked ("there is no delivery address in the order or in the customer profile"). The human then does not
  have to repeat it, and the evaluation sees whether the agent really searched.

## 3. The form of the question
- **One concrete question** or all independent questions at once, not a series one at a time.
- **Options with a recommendation and an effect** ("A: the headquarters address — delivery tomorrow; B: the warehouse address from the previous
  order — confirm it is current; I recommend A, because…"). Free text only when options cannot be given.
- **A default value if there is no answer**, if it is safe, with a deadline ("with no answer by 14:00
  I am holding the shipment"). For an irreversible action no answer means no action, not consent.
- The question goes to the right person through the channel they use (a ticket, chat, email), with the run
  identifier.

## 4. Pause and resumption
- **A checkpoint before the question:** the goal, the steps done with their results, the question, the run identifier. A pause must not
  hold a process or a context window: the answer arrives after hours or days.
- **Resumption from the checkpoint**, with the answer as a new input, not from zero.
- LangGraph (checked in `langgraph` 1.2.20, `langgraph/types.py`):
  - `interrupt(value)` in a node stops the graph and passes `value` (e.g. a question with options) to the client;
  - resumption through `Command(resume=answer)`;
  - a checkpointer is required;
  - **after resumption the node runs from the beginning**, so the code before `interrupt` (a write, a send, a payment)
    must be idempotent or moved to a separate node after the question.
- The same principle without a framework: state in the database with the run identifier, the status "waiting for a human",
  an event with the answer resumes the run (durable execution: `references/memory-and-durable-execution.md`).
- An unanswered question has a deadline and an escalation. A run does not hang forever in the "waiting" state.

## 5. Anti-patterns
- Asking about something the agent has in its tools or in the context.
- A series of questions one at a time, each after another step.
- Guessing on an irreversible decision or someone else's decision (delivery address, amount, recipient).
- A question with no options and no recommendation ("what should I do?").
- A pause without saving the state: the answer arrives, and the run starts again and repeats the side effects.
- A question asked but invisible in the run trace (tracing, step 8 of SKILL.md), so it cannot be measured.

## 6. Measures and evaluation
- **Unnecessary questions:** the share of questions whose answer was available through a tool.
- **Guessing:** the share of runs in which the agent assumed a value when it should have asked. You detect it from
  the human's corrections and complaints.
- **Waiting time** for an answer and the share of questions without an answer by the deadline.
- The evaluation set has both kinds of cases (ai-evals, pack-it):
  - "must ask": a gap that cannot be filled in;
  - "need not": the data is in the tools or the gap is cheap to assume.
  The first kind alone rewards an agent that asks about everything.
