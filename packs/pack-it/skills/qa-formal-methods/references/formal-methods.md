# Formal methods as an oracle

> **Contents:** 1. When it pays off · 2. The cost ladder (from the cheapest) · 3. The flow · 4. Limits of the result · 5. Example: discount rules (Z3, run) · 6. Example: a retry after a lost response (TLA+, TLC, run) · 7. Example: permissions through nested groups (Alloy, run)

## 1. When it pays off
A model checked by a tool pays off where examples and random generation are not enough and a failure is expensive:
- **concurrency and retries** — two reservations of the last seat, a double charge after a timeout, a race
  on an optimistic lock (integration tests only hit the interleavings that happened to occur);
- **protocols and state machines** — synchronization, a charging session, the lifecycle of an invoice, a migration with two writes;
- **combinatorial rules with a limit** — discounts, credit limits, permissions combined from several sources.

It does not pay off for data mapping, UI, integration with an external API, or rules that can be reviewed
with a table. "Let's formally verify the whole module" → pick 1–3 properties with the highest cost of failure, the rest with tests.

## 2. The cost ladder (from the cheapest)
1. Assertions and contracts in code (preconditions and postconditions, aggregate invariants).
2. Property tests (Hypothesis, fast-check) — random generation; it misses a threshold and a rare interleaving.
3. An SMT solver (Z3) — a proof or a counterexample for rules over numbers and logical conditions.
4. Model checking (TLA+/PlusCal with TLC or Apalache, Alloy) — all interleavings of a small protocol model.
5. Program verification (Dafny) and proof assistants — a guarantee on the code itself, the most expensive to maintain.

You go one rung higher only when the lower one cannot express the property or does not find it.

## 3. The flow
1. **The property in words, with a criterion.** "Never two confirmed reservations of the same seat" — with the identifier of the
   `AC-n` criterion from the task specification (`tf spec`) it follows from.
2. **A model, not code.** Only the state and steps that concern the property; environment events as a nondeterministic choice
   (a lost response, a delay, a restart, a retry).
3. **The negation of the requirement for the tool.** The solver or checker looks for a state that violates the property.
4. **A counterexample → a test.** You turn every trace found into an acceptance test with the `AC-n` identifier in the name
   (then `tf trace` links it to the criterion); the test must be red on the current code before you fix it.
5. **The fix first in the model.** The checker with no counterexample on the fixed model, only then a code change.
6. **The model next to the code.** The model file in the repository, in the module's directory, with a line saying
   which code commit it describes; a protocol change in code without a model change is a finding in review
   (qa-change-review).

## 4. Limits of the result
- **"No counterexample" concerns only the model.** In the report always: the number of processes, messages, the range of numbers, the search
  depth ("TLC: 2 services, 1 seat, up to 2 retries — no violation"). Without these limits the result sounds like proof
  for production, and it is not.
- **The model simplifies arithmetic.** Real numbers in a solver are not grosze and not `float` — model amounts with
  integers in grosze or add a rounding step the way the code does it; the order of applying rules as in the code.
- **The model drifts from the code.** Without step 6 of the flow, in half a year it checks a protocol that does not exist.
- **A model that is too small gives a false "OK".** A bug that needs three participants will not appear in a model with two.
  Widen the scope when the checking time allows it.

## 5. Example: discount rules (Z3, run)
Three discount rules combined by conditions, the requirement: the total discount ≤ 30% and the price not negative. Random carts in the typical
range (50–500 PLN) found nothing.

```python
from z3 import Real, Bool, If, Solver, Or, sat

cart = Real("cart")
code, loyal = Bool("code"), Bool("loyal")

def discount(with_limit):
    r = If(cart >= 200, 0.10 * cart, 0)      # R1: cart threshold
    r = r + If(code, 0.15 * cart, 0)             # R2: promo code
    r = r + If(loyal, 20, 0)                    # R3: loyalty, a fixed amount
    return If(r > 0.30 * cart, 0.30 * cart, r) if with_limit else r

for with_limit in (False, True):
    s = Solver()
    s.add(cart > 0)
    r = discount(with_limit)
    s.add(Or(r > 0.30 * cart, cart - r < 0))  # negation of the requirement
    result = s.check()
    print(f"limit in code={with_limit}: {result}", end="")
    if result == sat:
        m = s.model()
        print(f" -> cart={m[cart]}, code={m[code]}, loyal={m[loyal]}", end="")
    print()
```

Result (z3-solver 4.15.4):
```
limit in code=False: sat -> cart=1/2, code=False, loyal=True
limit in code=True: unsat
```
The counterexample: a cart of PLN 0.50 and a PLN 20 loyalty discount → a negative price. It becomes the test
`AC-2: cart of PLN 0.50 with loyalty → price PLN 0.35` (red before the fix). After adding the limit in the code, `unsat`
means: in this model (real numbers, three rules) no combination violates the requirement — you put the limits of the result
from §4 in the report.

## 6. Example: a retry after a lost response (TLA+, TLC, run)
A client reserves a seat, the response may get lost in the network, after a timeout the client retries the request. The property with a criterion:
one client request yields at most one reservation. Integration tests pass because a lost response
does not occur in them.

```tla
---- MODULE Reservation ----
\* A client reserves a seat; the response may get lost, after a timeout the client retries the request.
EXTENDS Naturals, FiniteSets
CONSTANTS Clients, Seats, MaxRetries, Idempotency
VARIABLES free, reservations, state, retries, network
vars == <<free, reservations, state, retries, network>>

Init == /\ free = Seats
        /\ reservations = {}
        /\ state = [c \in Clients |-> "start"]
        /\ retries = [c \in Clients |-> 0]
        /\ network = {}

Send(c) == /\ state[c] = "start"
           /\ network' = network \cup {[type |-> "req", c |-> c]}
           /\ state' = [state EXCEPT ![c] = "waiting"]
           /\ UNCHANGED <<free, reservations, retries>>

Handle(m) == /\ m.type = "req"
             /\ IF Idempotency /\ \E r \in reservations : r.c = m.c
                  THEN UNCHANGED <<free, reservations>>          \* the same request: return the existing one
                  ELSE \E s \in free :
                         /\ reservations' = reservations \cup {[c |-> m.c, seat |-> s]}
                         /\ free' = free \ {s}
             /\ network' = (network \ {m}) \cup {[type |-> "resp", c |-> m.c]}
             /\ UNCHANGED <<state, retries>>

Receive(m) == /\ m.type = "resp"
              /\ network' = network \ {m}
              /\ state' = [state EXCEPT ![m.c] = "ok"]
              /\ UNCHANGED <<free, reservations, retries>>

Lose(m) == /\ m.type = "resp"                                  \* loss of the response in the network
           /\ network' = network \ {m}
           /\ UNCHANGED <<free, reservations, state, retries>>

Retry(c) == /\ state[c] = "waiting"
            /\ ~\E m \in network : m.c = c                       \* timeout: nothing in transit
            /\ retries[c] < MaxRetries
            /\ retries' = [retries EXCEPT ![c] = @ + 1]
            /\ network' = network \cup {[type |-> "req", c |-> c]}
            /\ UNCHANGED <<free, reservations, state>>

Next == \/ \E c \in Clients : Send(c) \/ Retry(c)
        \/ \E m \in network : Handle(m) \/ Receive(m) \/ Lose(m)

Spec == Init /\ [][Next]_vars

\* AC-1: one client request yields at most one reservation.
OneReservationPerClient == \A c \in Clients : Cardinality({r \in reservations : r.c = c}) <= 1
====
```

The configuration `Reservation.cfg` (two variants, differing only in `Idempotency`):
```
CONSTANTS Clients = {a, b}  Seats = {m1, m2, m3}  MaxRetries = 1  Idempotency = FALSE
SPECIFICATION Spec
INVARIANT OneReservationPerClient
```
Running: `java -cp tla2tools.jar tlc2.TLC -config Reservation.cfg -deadlock -workers 1 Reservation.tla`
(`-deadlock` turns off reporting final states as deadlocks — a client does nothing after `ok`).

The result without idempotency (an abridged TLC trace, 6 states, 83 distinct states examined; the action names at states 3, 4 and 6
read from the state change — TLC gives `<Next …>` there, because the actions are invoked inside `\E m \in network`):
```
Error: Invariant OneReservationPerClient is violated.
State 2: <Send(a)>    network = {[c |-> a, type |-> "req"]}
State 3: <Handle>       reservations = {[c |-> a, seat |-> m1]}, network = {[c |-> a, type |-> "resp"]}
State 4: <Lose>         network = {}
State 5: <Retry(a)>     network = {[c |-> a, type |-> "req"]}
State 6: <Handle>       reservations = {[c |-> a, seat |-> m1], [c |-> a, seat |-> m2]}
```
With `Idempotency = TRUE`: `Model checking completed. No error has been found.` — 719 states generated,
382 distinct, depth 13. The trace becomes the test `AC-1: the response to a reservation gets lost, the client retries → one
reservation` (an injected loss of the response; red before adding the idempotency key). The report with the limits:
"TLC: 2 clients, 3 seats, 1 retry, a set of messages without duplicates and without order — no violation".
The model does not cover duplicates in the network (a set instead of a multiset) or key expiry — those are separate extensions.

## 7. Example: permissions through nested groups (Alloy, run)
An invoice shared with a group; a group may contain subgroups. The write rules from the code guard the tenant of the members and invoices,
but not of the subgroups.

```alloy
-- Access to invoices through groups that may contain other groups.
sig Tenant {}
sig User { tenant: one Tenant }
sig Group { groupTenant: one Tenant, members: set User, subgroups: set Group }
sig Invoice { owner: one Tenant, sharedWith: set Group }

-- a user sees an invoice when they belong to the sharing group or to its subgroup (at any depth)
fun sees[u: User]: set Invoice {
  { f: Invoice | some g: f.sharedWith | u in g.*subgroups.members }
}

-- a rule from the code: the group's members and an invoice shared with the group belong to the same tenant
fact WriteRules {
  all g: Group | g.members.tenant in g.groupTenant
  all f: Invoice | f.sharedWith.groupTenant in f.owner
}

-- AC-3: nobody sees another tenant's invoice
pred Isolation { all u: User | sees[u].owner in u.tenant }
-- the fix: a subgroup belongs to the same tenant as its parent group
pred SubgroupsOfSameTenant { all g: Group | g.subgroups.groupTenant in g.groupTenant }

check WithoutFix { Isolation } for 4
check WithFix { SubgroupsOfSameTenant implies Isolation } for 4
```

Running: `java -jar alloy.jar exec -f Permissions.als` (counterexamples in the `Permissions/` directory,
`receipt.json`). The result:
```
00. check WithoutFix              0    1/1     SAT
01. check WithFix                0       UNSAT
```
`SAT` for a `check` is a counterexample. The smallest (scope 2): an invoice of tenant A shared with group G1 of tenant A;
G1 has a subgroup G0 of tenant B; a member of G0 (tenant B) sees invoice A. The test: `AC-3: a subgroup of another tenant in the sharing
group → no access to the invoice`. `UNSAT` after the fix concerns the scope `for 4` (up to 4 objects of each type).

## Sources
- Z3 (`z3-solver` 4.15.4 from PyPI) — the example from §5 run 2026-11-15.
- TLA+: `tla2tools.jar` from release `v1.8.0` of the tlaplus/tlaplus repository (TLC identifies itself as "TLC2 Version
  2026.11.15.002146, rev bc1b506"), OpenJDK 21 — the example from §6 run 2026-11-15.
- Alloy 6.2.0 (`org.alloytools.alloy.dist.jar` from the AlloyTools/org.alloytools.alloy release), the `exec` command —
  the example from §7 run 2026-11-15.
- Apalache and Dafny — the names and roles of the tools from general knowledge [unverified: not run].
Described in our own words.
