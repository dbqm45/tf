# Factory Method

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: creational. The essence: the base class has the shared logic, and **which collaborating object is created** is decided by
an overridable method — subclasses replace the product without touching the logic.

## Problem
A reminder service has non-trivial logic (retries, logging, limits), but the delivery channel varies: e-mail,
SMS, push. When `new EmailChannel()` sits inside the logic, every new channel means editing that logic or a `switch`
on the channel type scattered across the code.

## Solution and participants
- **Product** — an interface (`Channel`); **concrete products** — `EmailChannel`, `SmsChannel`.
- **Creator** — a base class with logic that uses the product and an abstract method `createChannel()`.
- **Concrete creators** — subclasses returning a concrete product.
A factory method can also return an object from a pool/cache instead of a new one — the caller does not see it.

## When to use
- A library/framework is to let its users extend internal components through a subclass.
- The creator's logic is **non-trivial in itself** and is to be inherited together with the point of replacing the product.
- The creator hierarchy already exists (you are not building it just for the pattern).

## Costs
Every new product is a new creator subclass; inheritance binds the variants statically.

## Relations
- Often a starting point: it grows into an Abstract Factory (families), a Builder (complex construction) or
  a Prototype (cloning instead of subclasses).
- It is a special case of Template Method — "create an object" is one of the steps of the skeleton.
- A collection can return its iterator with a factory method.
- In DDD an aggregate factory is a different thing (a guarantee of a valid state) — ddd-tactical-design.

## Idiomatic form in TS
Without inheritance: pass a **creating function** (`createChannel: () => Channel`) to the constructor or use an ordinary
factory function (below, in the pitfalls). The class version makes sense when replacing the product goes hand in hand with other
overrides.

## Example (TS)
```ts
interface Channel {
  deliver(to: string, text: string): Promise<void>;
}

class EmailChannel implements Channel {
  async deliver(to: string, text: string): Promise<void> {
    console.log(`e-mail → ${to}: ${text}`);
  }
}

class SmsChannel implements Channel {
  async deliver(to: string, text: string): Promise<void> {
    console.log(`SMS → ${to}: ${text.slice(0, 160)}`);
  }
}

/** Creator: shared retry logic + a factory method for the channel. */
abstract class ReminderService {
  protected abstract createChannel(): Channel;

  async remind(to: string, bookingId: string, attempts = 3): Promise<boolean> {
    const channel = this.createChannel();
    for (let attempt = 1; attempt <= attempts; attempt++) {
      try {
        await channel.deliver(to, `Reminder about booking ${bookingId}`);
        return true;
      } catch (error) {
        console.warn(`attempt ${attempt} failed`, error);
      }
    }
    return false;
  }
}

class EmailReminderService extends ReminderService {
  protected createChannel(): Channel {
    return new EmailChannel();
  }
}

class SmsReminderService extends ReminderService {
  protected createChannel(): Channel {
    return new SmsChannel();
  }
}

const services: readonly ReminderService[] = [new EmailReminderService(), new SmsReminderService()];
for (const service of services) void service.remind('customer@example.com', 'B-17');
```

## When NOT to use / pitfalls
- **One variant and no signal that more will come** — a plain `new` is enough; do not build `Creator`/`ConcreteCreator`
  ahead of need.
- **Choosing the variant is simple and does not require inheritance** — a factory function with a `switch` on a parameter is
  more readable than a class hierarchy (`critique-and-pitfalls.md`, point 1):
  ```ts
  interface Notifier { send(msg: string): void; }
  class EmailNotifier implements Notifier { send(msg: string) { console.log('e-mail', msg); } }
  class SmsNotifier implements Notifier { send(msg: string) { console.log('SMS', msg); } }

  function createNotifier(kind: 'email' | 'sms'): Notifier {
    switch (kind) {
      case 'email': return new EmailNotifier();
      case 'sms': return new SmsNotifier();
    }
  }
  ```
- The class version pays for itself only when the logic in the creator's base class is non-trivial and inherited —
  not in order to "have a named pattern".
