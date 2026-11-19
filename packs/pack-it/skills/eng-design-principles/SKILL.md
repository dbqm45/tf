---
name: eng-design-principles
description: Use for design decisions and review — KISS, YAGNI, DRY, SOLID, Demeter, composition, conflicts between principles.
metadata:
  review: "2027-10-17"
  catalog: "Use for every design decision and code review — KISS, YAGNI, DRY (and when not to apply it), SOLID, separation of concerns, the Law of Demeter, tell-don't-ask, composition over inheritance, component principles (REP/CCP/CRP, ADP/SDP/SAP), fail fast, the principle of least surprise — and resolving conflicts between them. Not for the style of names and functions (eng-clean-code)."
---

# Design principles

Principles are **heuristics, not laws**. They serve to choose the simpler of two solutions and to justify comments in a review.
Always name the principle and the concrete cost we avoid ("YAGNI: this abstraction has one implementation and no plan for a second").

## Principles and how to apply them
| Principle | Check question | Violation signal |
|---|---|---|
| **KISS** — the simplest solution that works | Will a new person understand this in 5 minutes? | layers "for the future", generic frameworks for one case |
| **YAGNI** — do not build it before it is needed | Is there a requirement *now*? | unused parameters and interfaces, configurability nobody asked for |
| **DRY** — one piece of knowledge, one place | Is this *the same business knowledge*, or accidentally similar code? | a business rule copied to 3 places (e.g. a discount in the UI and in the service) |
| **AHA / rule of three** — avoid hasty abstractions | Do I see a third case? | an abstraction with `if (typeA)` flags inside |
| **S**ingle Responsibility | How many reasons to change does this class/module have? | changes from different departments land in one file |
| **O**pen/Closed | Does a new variant require editing existing code? | a `switch` on type repeated in many places → a policy/variants |
| **L**iskov | Can a subtype replace the type without surprises? | a subclass throws "not supported" |
| **I**nterface Segregation | Does a client depend on methods it does not use? | "fat" service interfaces |
| **D**ependency Inversion | Does the domain depend on infrastructure? | a framework/ORM import in the domain model → a port + an adapter |
| **Separation of concerns** | Are the UI, the logic and data access separated? | HTTP/SQL queries in components or entities |
| **Law of Demeter** | Do I talk only to direct collaborators? | `a.getB().getC().doX()` |
| **Tell, don't ask** | Do I pull data out of an object to make a decision it could make itself? | `if (account.getBalance() >= amount) account.setBalance(…)` instead of `account.debit(amount)`; but queries (getters) for reading and presentation are fine — the rule does not require removing all getters (Fowler) |
| **Hollywood principle** ("don't call us, we'll call you") | Who controls the flow: high-level code or a detail? | a low-level module polls or calls the higher-level code; solution: inversion of control (DI, events, template method, framework lifecycle hooks) |
| **Encapsulate what varies** | Which part changes more often than the rest? | a variable fragment (a tariff, a format, a provider) spread over many classes → behind an interface; only when the variability is real (YAGNI) |
| **Composition > inheritance** | Do I inherit behaviour, or only code? | deep hierarchies, base classes with `protected` state |
| **Fail fast** | Does the error show up closest to its cause? | validation "somewhere later", silent default values |
| **Least surprise** | Do the name and the behaviour match? | `get…()` with side effects |
| **Boy scout rule** | Do I leave the code a bit better? | but: no refactoring "by the way" in the same commit as the feature |

Component level (libraries, packages): the REP/CCP/CRP and ADP/SDP/SAP principles, stability metrics, policy and detail,
the framework at a distance, a structure that screams the domain, boundaries — `references/components-and-boundaries.md`.

## When principles conflict
- **KISS/YAGNI > DRY** for accidental similarity of code — duplication is cheaper than a wrong abstraction.
- **DRY > KISS** for **business knowledge** (rules, prices, permissions) — one source of truth, even at the cost of a layer.
- **SOLID at the module boundary, KISS inside** — interfaces and dependency inversion at the edges, simple functions in the middle.
- The conventions of the existing project take precedence over a "nicer" pattern — propose a deviation separately.
- On a tie choose the solution that is **easier to remove** (reversibility).

## The minimalism ladder (before you add code)
Understand the flow and all callers (grep), then stop at the first rung that is enough:
1. Is it needed now at all? (YAGNI)
2. Is it already in the repository?
3. Does the standard library do it (JDK, `Array`/`Intl`/`structuredClone`)?
4. Does the platform or framework do it (Angular: signals, `HttpClient`, forms, pipes; Spring)?
5. Does a dependency we already have do it?
6. Is one line enough?
7. Only now — the smallest code that works.
- You fix a bug at the source (in the shared function), not in every caller.
- Forbidden without a second case: an interface with one implementation, a factory of one product, configuration for a constant,
  "scaffolding for later". Removing is better than adding.
- **You never simplify at the expense of:** validation at the trust boundary, handling of errors that risk data loss,
  security, accessibility or what the human explicitly asked for. Non-trivial logic leaves at least one test.
- You mark a deliberate shortcut with a comment `debt: <limitation>, <when to come back>` (eng-tech-debt-audit collects it).
- In the report after the code at most 3 lines "I skipped X, add it when Y".
- A review for excess: one line per comment `L<line>: <remove|stdlib|platform|yagni|shorten> <what> → <what to replace it with>`,
  a line balance at the end; you assess correctness and security separately.
- **Rules in text alone hardly work** on an agent (pasted principles and the slogan "be brief" in F. Khan's measurement gave
  code of almost the same length as without them). What has an effect: the ladder above, a one-time stop of the first
  "done" when code was added without any check, and a review for excess after finishing. The review for excess cuts
  structure; **cutting a safeguard** (a parameterized query, a constant-time comparison, escaping, rejecting
  input, an expiry check, alternative text) requires a separate justification. You keep a rule for the agent
  when an ablation shows a benefit; a tie means it does not go in (F. Khan, "Fixing Over-Engineering in LLM Coding
  Agents", 2026-10-12, numbers [unverified]).
Inspiration: [ponytail](https://github.com/DietrichGebert/ponytail) — described in our own words, without its fixed hooks.

## In review
A comment = a principle + a concrete problem + a proposal. No "because it is nicer". Automate stylistic comments (linter, formatter).

The concrete shape of the solution (GoF patterns, their lighter forms and when NOT to use them).

## Example
**Situation:** a review of a PR for export to CSV: a `ReportExporter` interface, an `ExporterFactory`, one implementation, its own
date formatting.
**Result:**
```text
L12: yagni interface ReportExporter (1 implementation) → function exportCsv(rows)
L31: remove ExporterFactory → a direct call
L58: stdlib formatDate() → Intl.DateTimeFormat("pl-PL")
Balance: −96 / +18 lines. Row validation stays — trust boundary.
```
More examples: `references/examples.md`.
