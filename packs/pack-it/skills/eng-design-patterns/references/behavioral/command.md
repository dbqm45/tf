# Command

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: behavioral. The essence: a request becomes **a value object** with an execute method — it can be passed,
queued, saved, logged and undone.

## Problem
A booking calendar in the reception panel: the same actions (book, move, release) are triggered by a button, a context
menu, a keyboard shortcut and an import from a file; the reception wants "undo" and a change log. When every UI element calls
the logic directly, there is no single place for the history, and undoing requires knowledge of every action in many places.

## Solution and participants
- **Command** — the `execute()` interface (and `undo()`, if needed).
- **Concrete commands** — store the parameters and what is needed to undo; delegate the work to the receiver.
- **Receiver** — the object with the actual logic.
- **Invoker** — runs the commands, keeps the history/queue; does not know the details of the actions.
- **Client** — creates the commands and passes them to the invoker.

## When to use
- Parameterizing the UI with actions (buttons, menus, shortcuts, a command palette).
- Queuing, scheduling, remote execution — a command can be serialized.
- Undo/redo, an operation log, macros (a command composed of commands).

## Costs
An extra layer; a correct `undo()` can be hard (side effects on the outside, e.g. a sent e-mail).

## Relations
- **Memento** — the command saves the state before execution, in order to undo.
- **Strategy** also parameterizes an object with an object, but replaces the *way* of computing; a Command represents an *action*.
- **Prototype** — copies of commands in the history; **Chain** — a command as a request travelling through the links.
- **A command in CQRS/decider** (ddd-tactical-design) is an intent-value without an `execute()` method; a handler executes it.
  The same name, a different role — do not mix them.

## Idiomatic form in TS
A function/closure (`() => void`) in an array or a `Map<string, () => void>` is enough when neither serialization nor
undo is needed. A serializable command is often a **discriminated union** of data + an interpreter.

## Example (TS)
```ts
type Calendar = Map<string, string>; // slot → person

interface Command {
  readonly label: string;
  execute(): void;
  undo(): void;
}

class BookSlot implements Command {
  readonly label: string;
  readonly #calendar: Calendar;
  readonly #slot: string;
  readonly #owner: string;
  #previousOwner: string | undefined;

  constructor(calendar: Calendar, slot: string, owner: string) {
    this.#calendar = calendar;
    this.#slot = slot;
    this.#owner = owner;
    this.label = `booking ${slot} for ${owner}`;
  }

  execute(): void {
    this.#previousOwner = this.#calendar.get(this.#slot);
    this.#calendar.set(this.#slot, this.#owner);
  }

  undo(): void {
    if (this.#previousOwner === undefined) this.#calendar.delete(this.#slot);
    else this.#calendar.set(this.#slot, this.#previousOwner);
  }
}

class CommandHistory {
  readonly #done: Command[] = [];
  readonly #limit: number;
  constructor(limit = 50) {
    this.#limit = limit;
  }
  run(command: Command): void {
    command.execute();
    this.#done.push(command);
    if (this.#done.length > this.#limit) this.#done.shift();
  }
  undo(): string | undefined {
    const command = this.#done.pop();
    command?.undo();
    return command?.label;
  }
}

const calendar: Calendar = new Map();
const history = new CommandHistory();
history.run(new BookSlot(calendar, 'Mon 10:00', 'Anna'));
history.run(new BookSlot(calendar, 'Mon 10:00', 'Piotr'));
console.log(calendar.get('Mon 10:00'), '→ undone:', history.undo(), '→', calendar.get('Mon 10:00'));
```

## When NOT to use / pitfalls
- **No queuing, serialization or undo** — a function/closure (`Map<string, () => void>`) is enough instead of classes.
- A full class pays off when the command carries its own parameters and state for undoing, or must be saved and replayed.
- Not everything can be undone: for external effects (a payment, an e-mail) a **compensating action** is needed
  (saga — ddd-tactical-design), not `undo()`.
- Limit the history (a limit of N) — an unbounded list of commands with state is a memory leak.
