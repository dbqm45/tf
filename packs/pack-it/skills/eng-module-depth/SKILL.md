---
name: eng-module-depth
description: Use for designing a module interface — deep modules, the deletion test, seams and adapters, shallow modules.
metadata:
  review: "2027-10-17"
  catalog: "Use when designing a module interface and reviewing the architecture for shallow modules — the vocabulary (module, interface, depth, seam, adapter), the deletion test, dependency categories, \"design it twice\", a report of candidates for deepening. Not for a map of the whole repo (eng-codebase-mapping) or a debt audit (eng-tech-debt-audit)."
  keywords: "interfejs modułu, projektuję interfejs nowego modułu, jak wybrać interfejs, publiczne API modułu, nikt nie importuje wnętrza modułu, import wnętrza modułu, płytki moduł, głęboki moduł, spoina, adapter, test usunięcia, module interface, I am designing the interface of a new module, how to choose an interface, public API of a module, nobody imports the module's internals, importing the module's internals, shallow module, deep module, seam, deletion test"
---

# Deep modules

Goal: a lot of behaviour behind a small interface, in a well-chosen place, testable through that interface. The callers gain
(leverage), so do the maintainers (locality) and the tests. This is a vocabulary and a review procedure — the skill itself refactors nothing.

## Vocabulary (use exactly these words)
| Term | Meaning | Avoid |
|---|---|---|
| **module** | anything that has an interface and an implementation: a function, a class, a package, a slice across layers | component, service (in this sense) |
| **interface** | everything a caller must know: the signature **and** the invariants, the call order, the error modes, the required configuration, performance | "API", "signature" (too narrow) |
| **depth** | how much behaviour can be triggered per unit of interface that has to be learned; shallow = an interface almost as complex as the implementation | a ratio of lines of code (rewards padding) |
| **seam** (Feathers) | a place where you change behaviour without editing in that place — that is where the interface lies | "boundary" (clashes with the context boundary in DDD) |
| **adapter** | a concrete thing satisfying the interface at a seam (a Postgres repository and an in-memory fake are both adapters) | — |
| **leverage** | what the caller gets: more capabilities per unit of interface | — |
| **locality** | what the maintainer gets: the change, the bug and the verification in one place | — |
You take domain terms from the project glossary (`docs/project/02-domain/glossary.md`): "the Order intake module",
not "OrderHandler".

## Principles
0. **First: whether to modularize at all.** A prototype or a one-off solution, a system known in advance to be a single module, or no
   complexity is a reason not to split — the initial assessment is in ddd-discovery-intake (questions about the lifecycle and the complexity).
1. **Depth is a property of the interface.** A module can have small interchangeable parts inside and its own internal seams — you do not
   expose them outside just because the tests use them.
2. **The deletion test.** Imagine that the module disappears. The complexity disappears with it → it was a pass-through. The complexity comes back
   at N callers → it earns its keep.
3. **The interface is the test surface.** Callers and tests go through the same seam. You want to test "behind"
   the interface → the module has the wrong shape.
4. **One adapter = a hypothetical seam, two = a real one.** Do not introduce a port until something varies in it
   (usually: production + test). A seam with one adapter is only indirection (eng-design-principles, YAGNI).
Questions when designing: can the number of methods be reduced, the parameters simplified, more hidden inside? Accept
dependencies instead of creating them; return a result instead of producing side effects.

## Dependency categories — how to test a deepened module
| Category | Example | Strategy |
|---|---|---|
| in-process | pure computation, in-memory state | merge the modules, test through the new interface, no adapter |
| locally substitutable | a database with a lightweight substitute (a test container, PGlite), an in-memory file system | the substitute in tests, an internal seam |
| remote, but ours | our own service over the network | a port at the seam; an HTTP/queue adapter in production, in-memory in tests |
| truly external | a payment gateway, SMS | an injected port, a mock adapter in tests |
**Replace, do not add:** once there are tests on the interface of the deepened module, you delete the old tests of the shallow modules.
Tests check the result observable through the interface; if a test has to change when the implementation changes, it tests too
deep (eng-testing).

## Procedure A — review: candidates for deepening
1. **Scope before the scan.** A direction from the human (a module, a pain) takes precedence. Without it — hotspots from the history
   (`git log --since=6.months --name-only`, as in eng-tech-debt-audit): deepening pays off where the code changes.
   Read the domain glossary and the ADRs from this area.
2. **Look for friction** (usually a cheap `scout`): understanding one concept requires jumping across many small modules;
   an interface almost like the implementation; pure functions extracted "for the tests", while the bugs sit in the way of calling them; modules
   leaking through seams; code untestable through the current interface. On each suspect — the deletion test.
3. **The report** `docs/project/07-review/<date>-deep-dives.md` (or an HTML page per docs-tech-writing, if the human wants one).
   A candidate card: files/modules · the problem (friction) · the solution in plain language · the benefit in terms of locality
   and leverage and what happens to the tests · a before/after diagram · strength: **Strong** (the deletion test passes, real friction) /
   **Worth exploring** / **Speculative**. At the end: which one to start with and why.
4. **No interfaces and no code changes** at this stage. You ask: "Which candidate do we explore?". One candidate per session.
5. A candidate contradicting an ADR — you show it only when the friction justifies revisiting the decision, with a clear warning.
6. After the choice: an interview (core-plan-interview) — constraints, dependencies, the shape of the module, what is behind the seam, which tests
   survive. A new term → into the glossary at once. A rejection with a lasting reason → propose an ADR (the threshold is in docs-tech-writing),
   so that the next review does not suggest the same thing. The result is **a decision**, not a diff.
7. Decision → specification → tasks (core-project-record); record the remaining candidates as separate tasks, instead of
   pulling them into the same session (the report, the interview, the glossary and the code at once overflow the context).

**Review notes**
- **The best starting question** points to the direction of development: "we are going into <a feature from the specification> — what do we do so that this
  change is easy?". A scan without a direction suits a periodic review (e.g. once a sprint).
- A review tends to always find something. "No strong candidates" is a correct result; you usually skip
  `Speculative` candidates.
- **Badly neglected code:** first a shared glossary (ddd-facilitation: a glossary in an existing repo), then the review —
  without names for the concepts, candidates get invented names and explain nothing.
- **Code without tests:** the review points to the seams where characterization tests can be attached
  (eng-behavior-preserving-refactoring), before you change anything.
- An HTML report without scripts from a CDN: styles in the file, diagrams as ready SVGs — it works offline and without a supply chain.

## How to enforce depth in the code
Depth described in an ADR will blur anyway if every file can be imported from anywhere. Choose a mechanism:
| Stack | Mechanism | Cost |
|---|---|---|
| TS in Nx | a library with a public `index.ts`; the `@nx/enforce-module-boundaries` rule with tags (`scope:`, `type:`) blocks deep imports and forbidden directions | configuring the tags |
| TS outside a monorepo | the `exports` field in the package's `package.json`; `no-restricted-imports` or dependency-cruiser for internal paths | the rules must be maintained |
| TS in one file | a class or a closure with one public function | large files, poor navigation |
| Java | a package with package-private classes and one public class; JPMS modules (`exports`); ArchUnit tests | package discipline |
A rule in the linter or an architecture test is better than a note in the documentation — breaking a seam shows up in CI.

## Procedure B — design it twice
The first idea is rarely the best (Ousterhout). When an interface has to be chosen:
1. Describe the problem space to the human: constraints, dependencies (the category from the table), a code sketch only as an illustration.
2. Run in parallel (one message) 3 cheap subagents, each with a different constraint: (a) a minimal interface, 1–3
   entry points; (b) flexibility and extensibility; (c) the simplest typical case. Optionally a fourth: ports and adapters.
   Each gets the same technical brief and both glossaries.
3. Each returns: the interface (with invariants, order, errors), a usage example, what it hides, the dependency strategy,
   where the leverage is large and where it is thin.
4. Compare in prose by depth, locality and the place of the seam. Give your own recommendation (also a hybrid) — not just a menu.

## The result is good when
The conversation uses the words "module, interface, seam"; every proposed seam has a named second adapter; the discussion of the interface
covers invariants and errors; the candidates lie in recently changed code and carry the names of domain concepts; nothing was
refactored without the human's decision.

## Source
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT): `codebase-design` (with DEEPENING, DESIGN-IT-TWICE)
and `improve-codebase-architecture`; descriptions: [aihero.dev/skills-codebase-design](https://www.aihero.dev/skills-codebase-design), [aihero.dev/skills-improve-codebase-architecture](https://www.aihero.dev/skills-improve-codebase-architecture). Described in our own
words and adapted to the project log; J. Ousterhout, *A Philosophy of Software Design*; M. Feathers,
*Working Effectively with Legacy Code*.
