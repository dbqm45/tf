# Examples — outbox, inbox, guarantees

> **Contents:** 1. Orders → invoicing: an event through an outbox · 2. When not to distribute: an availability check · 3. An idempotent receiver with an inbox and a duplicate test

## 1. Orders → invoicing: an event through an outbox
**Situation.** "After an order is placed, the orders module synchronously calls `invoicing.issue_invoice(order)`.
When invoicing is down, an order cannot be placed. Let's make it asynchronous."

**How.**
1. **The excluding criteria** (section 1): orders do not use the result (the invoice number) in the same unit of work;
   the confirmation screen does not show the invoice → it can be distributed.
2. **Command or event**: the command `IssueInvoice` keeps the existing coupling; the event `OrderPlaced`
   fits the context boundary and will take further receivers (e.g. the warehouse). Choice: an event. The test
   "placing an order creates an invoice" stops working — I move it to the consumer test.
3. **Atomicity**: the order and the outbox in the same database and the same transaction → atomic.
4. **Outbox decisions**: the message id assigned at write time in the transaction, not by the relay; relay = a poller every 1 s;
   sink = an in-process bus (changing to a broker is the only change when splitting the processes).
5. **Ordering**: invoicing does not require it → no ordering key; at-least-once delivery → an idempotent receiver (example 3).

**Result** — writing the state and the message in one transaction (Python, `sqlite3` as the producer's transactional resource):
```python
import json
import sqlite3
import uuid
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, customer TEXT NOT NULL, amount_cents INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS outbox (
    message_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""


def place_order(db: sqlite3.Connection, customer: str, amount_cents: int) -> str:
    order_id = str(uuid.uuid4())
    with db:  # one transaction: the state + the outbox record or nothing
        db.execute("INSERT INTO orders VALUES (?, ?, ?)", (order_id, customer, amount_cents))
        db.execute(
            "INSERT INTO outbox (message_id, type, payload, created_at) VALUES (?, ?, ?, ?)",
            (
                str(uuid.uuid4()),  # the id assigned here, not in the relay
                "OrderPlaced",
                json.dumps({"orderId": order_id, "customer": customer, "amountCents": amount_cents}),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    return order_id


if __name__ == "__main__":
    connection = sqlite3.connect(":memory:")
    connection.executescript(SCHEMA)
    place_order(connection, "C-17", 129_900)
    print(connection.execute("SELECT type, status FROM outbox").fetchall())  # [('OrderPlaced', 'pending')]
```
The change report: it can be distributed (criteria 1–2) · the event `OrderPlaced` · atomic · an outbox in the orders database,
a poller of 1 s · ordering not guaranteed, not needed · logical coupling remains: invoicing depends on the `amountCents` and `customer` fields.

## 2. When not to distribute: an availability check
**Situation.** "A room booking calls `availability.block(room, period)` and only after `true` confirms the booking.
Let's turn it into an event, it will be looser."

**How.**
1. The first criterion: the caller **branches on the result** (`true` → confirmation, `false` → refusal).
2. The conversion would change correctness: the booking confirmed before it is known whether the room is free.
3. **Stop** — it stays synchronous or the flow is redesigned (the booking in a "pending" state), which is a business decision.

**Result** (the step report):

| Question | Answer |
|---|---|
| does the caller use the result? | yes — `if blocked:` decides on the confirmation |
| verdict | **do not distribute** in the current shape |
| option A | stays synchronous (the recommendation) |
| option B | a "pending" booking + the event `RoomBlocked` / `BlockRejected`; the customer sees the confirmation with a delay — the product owner's decision |
| note | asynchrony would remove the temporal coupling, the logical coupling remains in both options |

## 3. An idempotent receiver with an inbox and a duplicate test
**Situation.** "The relay sometimes sends `OrderPlaced` twice and the customer gets two invoices. Fix the receiver."

**How.**
1. At-least-once delivery is an assumption, not a relay bug → receiver idempotency.
2. The inbox record written **in the same transaction as the effect** (the invoice).
3. Deduplication through an **atomic claim** of the id (`INSERT … ON CONFLICT DO NOTHING`), not "check, then write".
4. A red test first: the same id delivered twice → exactly one invoice.

**Result** (Python, `sqlite3`):
```python
import json
import sqlite3

SCHEMA = """
CREATE TABLE inbox (message_id TEXT PRIMARY KEY);
CREATE TABLE invoices (order_id TEXT NOT NULL, amount_cents INTEGER NOT NULL);
"""


def handle_order_placed(db: sqlite3.Connection, message_id: str, payload: str) -> None:
    with db:  # the inbox and the effect in one unit of work
        claimed = db.execute(
            "INSERT INTO inbox (message_id) VALUES (?) ON CONFLICT DO NOTHING", (message_id,)
        ).rowcount
        if claimed == 0:
            return  # a duplicate — the effect already exists
        data = json.loads(payload)
        db.execute("INSERT INTO invoices VALUES (?, ?)", (data["orderId"], data["amountCents"]))


def test_the_same_id_twice_gives_one_invoice() -> None:
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    payload = json.dumps({"orderId": "O-1", "amountCents": 129_900})
    handle_order_placed(db, "msg-0001", payload)
    handle_order_placed(db, "msg-0001", payload)
    assert db.execute("SELECT COUNT(*) FROM invoices").fetchone()[0] == 1


if __name__ == "__main__":
    test_the_same_id_twice_gives_one_invoice()
    print("ok")
```
To complete section 6: a format contract test (a snapshot of the payload with the same serializer, fixed ids and times) and an
integration test on a real database with the same duplicate case.
