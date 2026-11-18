# Idioms for implementing domain logic and the transitions between them

## Catalogue
| Idiom | You recognize it by | When it is good | When it hurts |
|---|---|---|---|
| **Anemic model + service** | entities with fields only, logic in services | CRUD, simple validations | rules scattered across services, repeated `if` |
| **Rich aggregate (mutable)** | private state, command methods check invariants, mutate state and return/register events; the ORM saves changes | competition for resources, many rules, the team knows OOP | harder to test without infrastructure; side effects mixed with the decision |
| **Decider (functional core, imperative shell)** | immutable state; `decide(state, command) → decision` (a new state and/or events or a rejection); I/O only in the shell | testability, pure rules, the prospect of event sourcing | simple CRUD; a team without FP experience |
| **Strict decider (event-sourced)** | `decide(state, command) → events` + `evolve(state, event) → state` | event sourcing, audit | requires events carrying the full state of the change — often changes the event contract |

Changing the idiom is not a goal in itself — justify it (testability, separating the decision from the effects, future event sourcing).

## Recipe: rich aggregate → decider (the variant without changing the event contract)
1. The state becomes immutable (a record/read-only object); the **version field** for optimistic locking carries over unchanged.
2. Every command gets its own type (preferably a closed set — a union/sealed).
3. Use the **existing** events without new fields.
4. Move the rejection conditions **verbatim**, keeping the kind of rejection.
5. The core is pure: no repository, clock (time as a command parameter), publisher.
6. The shell (an application service): **load → decide → save (explicitly!) → publish**, within the same transaction boundary as before.
7. Switch the tests' domain driver to `decide`.
The strict variant (`evolve`) — only with consent, because it usually requires enriching the events (a contract change).
Syntax in a specific language: lang-* (e.g. unions/sealed, records).

## Structural rewriting with ast-grep (changing the shape of calls in many places)
- A preview without writing: `ast-grep run -p '<pattern>' -r '<target>' -l <language> <directory>` prints the diff and changes
  nothing; with `-i` (`--interactive`) you approve change by change, with `-U` (`--update-all`) you apply all of them.
- A repeatable rewrite: a YAML rule with a `fix` field, run with `ast-grep scan`; the rule goes into the repo together
  with the commit.
- In the commit message the number of matches: the source pattern before = N, after = 0; the target pattern after = N. You confirm the zeros
  with `rg`, because a pattern that is not valid code in the given language also gives zero.
- Unlike `sed`, ast-grep distinguishes `save(` from `saveMultiple(` and skips comments and strings
  (checked on ast-grep 0.50.0, 2026-10-10). Run the `ast-grep` binary — on Linux `sg` is usually the
  change-group command.
