---
name: be-messaging-outbox
description: Use for asynchronous communication — command or event, outbox/inbox, ordering, idempotency.
metadata:
  review: "2027-10-17"
  catalog: "Use when turning a synchronous call between modules into an asynchronous message and when designing an outbox/inbox — whether it may be distributed, command or event, atomicity, the relay, ordering, consumer idempotency, producer, contract and consumer tests. Not for choosing context relationships (ddd-context-mapping) or the database schema in general (be-database)."
  keywords: "outbox, inbox, komunikacja asynchroniczna, kolejka, broker, Kafka, RabbitMQ, zdarzenie czy komenda, idempotencja konsumenta, deduplikacja, wiadomość przyszła dwa razy, utrata zdarzeń, kolejność wiadomości, at-least-once, co najmniej raz, odtworzenie zdarzeń, replay, reset offsetu, odbudowa modelu odczytu, skutki uboczne przy odtwarzaniu, asynchronous communication, queue, event or command, consumer idempotency, deduplication, the message came twice, lost events, message ordering, event replay, offset reset, rebuilding a read model, side effects on replay, transactional outbox"
---

# Asynchronous communication: outbox, inbox, guarantees

## 1. Can this call be distributed at all?
Two excluding criteria — check them BEFORE the design:
- **The caller uses the result** (branches on it, returns it, uses it in the same unit of work) → the conversion changes
  correctness. **Stop** — it stays synchronous or the flow must be redesigned.
- **Someone reads the effect right after the call** (read-after-write, e.g. a screen after a save) → a business decision: accept the delay,
  keep it synchronous or give the reader its own projection.
Asynchrony removes **temporal** coupling, not **logical** coupling — the modules still depend on the meaning of the message.

## 2. Command or event?
- **An event** — a fact in the past tense, 0..N receivers, the reaction is the receiver's policy; it fits a context boundary.
- **A command** — the imperative mood, one addressee; it keeps the existing coupling, closer to what was there.
For a call being reworked show both options with their costs; an event that already flows stays an event.
The name reflects the business intent, not the mechanism. Point out the tests that will stop working after the change (those checking the effect in the other module).

## 3. Atomicity
Two questions: is the producer's state change in a transaction? does the outbox write go **to the same resource in the same transaction**?
| Verdict | Action |
|---|---|
| atomic | ok |
| atomic after a fix | add a transaction around the state change + the message write |
| non-atomic (different resources) | an outbox in the producer's store · CDC of your own state (listen-to-yourself) · documented best-effort |
**A silent loss of atomicity is worse than a synchronous call.** Publishing "after the commit" from memory (without an outbox) loses
messages on a failure between the commit and the send — name this risk, if you accept it.

## 4. The outbox — anatomy and decisions
The producer's transaction writes the state + an outbox record → the **relay** reads pending records, sends them to the sink and marks them as sent →
on the other side a **thin adapter** calls the receiver's public API.
| Decision | Options (the default in bold) |
|---|---|
| ready or your own | **the framework's/library's mechanism**, if there is one · your own table + a poller |
| interception | **behind the existing port/bus** (the producer unchanged) · a new sending port |
| store | always the producer's transactional resource |
| record | the message id, the type, the payload (serialized), the status, the creation time, possibly an ordering key |
| **the message id** | assigned **at write time in the transaction** — never by the relay (every retried attempt would get a new id and deduplication stops working) |
| relay | **a poller** (latency = the interval) · log tailing/CDC · the database's native stream |
| sink | an in-process bus (a skeleton) · a broker — changing the sink is the only change needed to split the processes |
| serializer | one, the same in the outbox and in the contract test |
Cleaning up sent records and an outbox backlog metric (ops-observability) belong to the design.

## 5. Ordering and retries
- Ordering **is not guaranteed** (a poller, retries, many workers). When the receiver requires it: an ordering key and one
  message per key "in flight" — at the cost of throughput.
- **At-least-once** delivery → the receiver must be idempotent:
  - the deduplication record (an inbox) written **in the same unit of work as the effect** — the handling must be synchronous in that
    transaction; handling "after the commit" or in a separate thread breaks the guarantee;
  - deduplication through an **atomic claim** of the id (an insert skipping on conflict, compare-and-set), not "check, then write".
- **Loss, duplicates and replay are three separate problems:**
  - loss → durability on the producer's and the broker's side (in Kafka `acks=all`, `min.insync.replicas` > 1, an idempotent
    producer — the last one does not replace deduplication at the consumer);
  - duplicates → an idempotent consumer; the deduplication record has a lifetime matched to the redelivery window, and does not
    grow forever. Without a natural id the producer assigns one at creation or you compute a hash of the immutable fields
    (the entity + the version);
  - **a deliberate replay of history** (an offset reset, a new consumer group, rebuilding a read model) → deterministic
    handling (the time from the event, not the current one; no reading of other services' state) and external effects (an email,
    charging a card) separated from rebuilding the state: a replay mode flag or a separate effects path. You also pass
    the idempotency key on to the payment provider.
- Many relay instances can send the same message twice — correct thanks to idempotency, but wasteful:
  `SKIP LOCKED`, a compare-and-set of the status or a lease.

## 6. Tests (the TDD order)
1. **Producer:** "the message is published" — the test ends at the transaction boundary; a publisher double is right here,
   because emitting the message IS the behaviour. Red first.
2. **Format contract:** a snapshot/approval of the serialization or a consumer contract / a schema registry; the same serializer as the outbox,
   fixed ids and times in the test data; check backwards compatibility (new fields optional).
3. **Consumer:** an adapter test (with a double of the receiver's API) and an integration test on real infrastructure, **with an idempotency case**:
   the same id delivered twice → exactly one effect.

## The change report (`docs/project/04-architecture/adr/…` or the step report)
the classification (criteria 1–2) · command/event with a justification · the atomicity verdict · the outbox decisions · the ordering guarantees ·
what remained logically coupled · the results of the three kinds of tests.

## Example
**Situation:** "Orders call `invoicing.issueInvoice()` synchronously; when invoicing is down, ordering is impossible."
**Result** (the change report):
- criteria 1–2: the result is not needed, nobody reads the invoice right after the order → it can be distributed;
- the event `OrderPlaced` (the warehouse will also take it), not a command; the test "an order creates an invoice" goes to the consumer;
- atomic: the order + the outbox record in one transaction, the message id assigned at write time; relay: a poller every 1 s;
- ordering not needed; the receiver: an inbox `INSERT … ON CONFLICT DO NOTHING` in the invoice's transaction;
- test: the same id twice → exactly one invoice.

More examples: `references/examples.md`.
