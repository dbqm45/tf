# Mediator

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: behavioral. The essence: components do not call each other — **they report events to an intermediary**, which
knows how to react. The "everyone with everyone" network of dependencies turns into a star.

## Problem
A room booking form: choosing the dates refreshes the list of free rooms, choosing a room recalculates the price, the price and the completeness of the data
decide whether the "Book" button is active. When the dates field knows the room list, the room list knows the price label, and the label knows
the button, no component can be used in another form, and a change of a rule requires editing several classes.

## Solution and participants
- **Components** — know only the mediator's interface; they report "something has changed".
- **Mediator** — the `notify(event)` interface.
- **Concrete mediator** — holds references to the components and encodes the rules of their collaboration.

## When to use
- Changing one class requires changes in many others because of tangled dependencies.
- A component cannot be reused because it knows its concrete neighbours.
- You create subclasses of components only to change their collaboration with their surroundings.

## Costs
The mediator easily becomes a "god object" — all the collaboration logic in one class.

## Relations
- **Facade** — the subsystem does not know about it; the components know about the mediator.
- **Observer** — a mediator is sometimes implemented through subscriptions (the components publish, the mediator listens).
- **Chain, Command, Observer** — alternative ways of connecting senders with receivers.
- At the system level the role of the mediator is played by an event broker/bus; between contexts — events and policies
  (ddd-tactical-design, be-messaging-outbox).

## Idiomatic form in TS
In the UI the role of the mediator is often played by **a container component or a store** of the form state (fe-architecture): presentational
components emit events upwards, the container decides. Write your own mediator when the framework does not provide this.

## Example (TS)
```ts
type FormEvent = 'datesChanged' | 'roomChanged';

interface FormMediator {
  notify(event: FormEvent): void;
}

class DatesField {
  nights: number | undefined;
  readonly #mediator: FormMediator;
  constructor(mediator: FormMediator) {
    this.#mediator = mediator;
  }
  choose(from: Date, to: Date): void {
    this.nights = Math.round((to.getTime() - from.getTime()) / 86_400_000);
    this.#mediator.notify('datesChanged');
  }
}

class RoomSelect {
  options: readonly string[] = [];
  selected: string | undefined;
  readonly #mediator: FormMediator;
  constructor(mediator: FormMediator) {
    this.#mediator = mediator;
  }
  select(room: string): void {
    this.selected = room;
    this.#mediator.notify('roomChanged');
  }
}

class PriceLabel {
  text = '—';
}
class SubmitButton {
  enabled = false;
}

/** Concrete mediator: the only place that knows the rules of the fields' collaboration. */
class BookingForm implements FormMediator {
  readonly dates = new DatesField(this);
  readonly room = new RoomSelect(this);
  readonly price = new PriceLabel();
  readonly submit = new SubmitButton();
  readonly #ratesPerNight: ReadonlyMap<string, number>;

  constructor(ratesPerNight: ReadonlyMap<string, number>) {
    this.#ratesPerNight = ratesPerNight;
  }

  notify(event: FormEvent): void {
    if (event === 'datesChanged') {
      this.room.options = [...this.#ratesPerNight.keys()];
      if (this.room.selected !== undefined && !this.room.options.includes(this.room.selected)) {
        this.room.selected = undefined;
      }
    }
    const rate = this.room.selected === undefined ? undefined : this.#ratesPerNight.get(this.room.selected);
    const nights = this.dates.nights;
    const complete = rate !== undefined && nights !== undefined && nights > 0;
    this.price.text = complete ? `${((rate * nights) / 100).toFixed(2)} PLN` : '—';
    this.submit.enabled = complete;
  }
}

const form = new BookingForm(new Map([['Room A', 90_000], ['Room B', 60_000]]));
form.dates.choose(new Date('2026-10-01'), new Date('2026-10-03'));
form.room.select('Room B');
console.log(form.price.text, form.submit.enabled);
```

## When NOT to use / pitfalls
- **Two or three objects with one, stable relation** — a direct call or a callback is simpler.
- Watch the growth: `notify()` as a big `switch` on event names → split the mediator per area or move to
  more fine-grained subscriptions (Observer).
- The framework's store/container already coordinates the components — do not duplicate it with a manual mediator.
- Complex business rules (pricing, availability) should not live in a UI mediator — the mediator calls the domain/a service;
  in the example multiplying the rate stayed in the mediator only for brevity.
