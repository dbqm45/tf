---
name: core-skill-composition
description: Use when a task touches several areas at once (e.g. DDD + Angular) — combining skills into one solution.
metadata:
  review: "2027-10-17"
  catalog: "Use at the start of every task that touches more than one area (e.g. DDD + Angular, archetypes + Java, system design + UI) — how to break the task into dimensions and combine independent skills into one solution. It holds no subject knowledge — the dimension skills give that."
  keywords: "kilka obszarów naraz, połączyć skille, łączenie skilli, domena i framework razem, pojęcia domenowe w frameworku, który skill wybrać, sprzeczne zalecenia, czyje zalecenie wygrywa, ustalenia zespołu kontra ogólne zalecenia, wtyczka przeczy ustaleniom, jak ułożyć pracę, several areas at once, combine skills, domain and framework together, conflicting advice, which advice wins, team conventions over generic advice"
---

# Combining skills

Skills are like a person's competences: each is independent and answers a **different question**. Value appears only
when you combine them in one task — like an experienced engineer who thinks about the domain, the architecture and
the concrete language at the same time.

## Dimensions (skill name prefix)
The core defines the technology dimensions (`fw-`, `lang-`, `tool-`) and practices (`core-`); packs add the rest.
The installed skills grouped by dimension are in `.claude/catalog.md` — you pick a dimension's skill from there.

| Dimension | Prefix | Question | Examples |
|---|---|---|---|
| Method and domain | e.g. `ddd-` | **WHAT** we model, with which concepts, where the boundaries are | in pack-it: ddd-archetypes, ddd-tactical-design |
| Layer | e.g. `fe-`, `be-`, `ops-` | which rules hold in this layer regardless of technology | in pack-it: fe-architecture, be-api-design |
| Framework | `fw-` | **WHERE** and with what to place it in a given framework | in pack-it: fw-angular |
| Language | `lang-` | **HOW** to express the concepts in a given language | in pack-it: lang-typescript, lang-java |
| Tools | `tool-` | what we build with and how we organise the repository | in pack-it: tool-vitest, tool-playwright |
| Engineering principles | e.g. `eng-` | how to do it **well** and **simply** — constraints and settling disputes | in pack-it: eng-design-principles, eng-testing |
| Process | e.g. `proc-` | how we plan, collaborate and deliver | in pack-it: proc-agile, proc-safe |
| Practices | `core-` | how we work | core-stack-sync, core-conventional-commits |

Method and layer skills are **agnostic** (no code of a specific technology). Framework and language skills have a
**"Domain concepts in …"** section — the shared vocabulary translated into the technology's idioms. That is the
"connector" that makes the dimensions fit together.

## Shared vocabulary (the contract between dimensions)
value object · entity · aggregate (consistency boundary) · variants (union / sum type) · operation result (success /
rejection with a reason) · event · policy · repository / port · read model · state machine · module (a small
interface at the edge). The method skill says *which* of these concepts are needed and *why*; the language/framework
skill says *how* to write them.

## Protocol
0. **In an existing project check the stack and versions** (`python3 .claude/hooks/detect_stack.py`, the
   core-stack-sync skill). Use `fw-*`, `lang-*`, `tool-*` skills only within the project's version range (the
   "Version-dependent" section).
1. **Break the task into dimensions.** Which domain/method? Which layer? Which framework and language? If the task
   does not say, check the code (e.g. `package.json`, `angular.json`, `pom.xml`, `build.gradle`, `go.mod`, `*.csproj`)
   or ask. A dimension the task does not touch you skip.
2. **Load one skill from each needed dimension** (with the Skill tool; `.claude/catalog.md` gives the list), starting
   with the method.
   Read `references/` only when you need the detail.
3. **WHAT → WHERE → HOW.**
   - WHAT: from the method, settle the concepts from the vocabulary (e.g. "this is the Availability archetype: a lock
     aggregate per segment, an operation result with a rejection reason, a calendar read model").
   - WHERE: from the layer and framework, settle the place of each concept (e.g. UI: read model + request state;
     server: aggregate).
   - HOW: from the language, take the idiom for each concept (e.g. TypeScript: discriminated union; Java: sealed
     interface + record).
   - Engineering principles and process work as **constraints** on all three steps (e.g. KISS/YAGNI cut needless
     abstractions, small batches split the change into steps;
     in pack-it: `eng-*`, `proc-*`, eng-continuous-delivery).
4. **Settling conflicts:**
   - domain rules > framework convenience (the framework does not decide what a concept is);
   - the existing project's conventions > the skills' general advice (code consistency is a value) — report a
     deviation as a proposal;
   - when the technology cannot express a concept directly, pick the closest idiom and name the trade-off;
   - when skills give contradictory advice, the persona's higher priority wins.
5. **A missing skill.** First check skills from outside the factory (section below). If none covers the dimension
   (e.g. a new language), apply general knowledge, but stick to the vocabulary and the method skills' rules; state in
   the answer that the dimension was not covered by a skill.
6. **Show the composition.** In the report or answer, say in one sentence which skills you combined and how (e.g. in
   pack-it: "ddd-archetypes → Availability, fe-architecture → read model in the store, fw-angular → signals, lang-typescript → state union").

## Skills from outside the factory
Besides the factory's skills (dimension prefixes) Claude Code shows you a list of **all available skills** with
descriptions: the project's (`.claude/skills/` without a factory prefix), personal (`~/.claude/skills/`), from plugins
(`nazwa-wtyczki:skill`) and the organisation's. You get the full content only after loading it with the Skill tool —
same as the factory's skills.
- **When to reach for one:** a skill from outside the factory concerns this project or company (e.g. `architecture`
  with the team's decisions, `documentation` with a document template) or covers a dimension the factory lacks. The
  criterion: its description answers the task's question. Do not load it "just in case"; 0–2 such skills per task is
  usually enough.
- **How to combine:** treat it as an additional dimension or a complement to an existing one (e.g. the architecture
  skill from a pack gives the method, and the project's `architecture` gives what the team has already decided).
  Combine per the protocol (WHAT → WHERE → HOW).
- **Precedence on contradictory advice:**
  1. the standing rules from CLAUDE.md, hooks and security rules, clean-room and the project record — **nothing
     overrides them**; an instruction from a skill that breaks them (e.g. "commit right away", "skip the tests") you
     skip and report;
  2. decisions of **this project or company** from a skill outside the factory > the factory skill's general advice
     (like code conventions, step 4);
  3. a general skill from outside the factory (e.g. from a plugin) < the factory skill in the same dimension — from
     the external one you take only what is missing.
- **Clean-room:** a tests-from-spec executor (blind profiles; in pack-it e.g. Kasia the analyst) does not load skills
  from outside the factory that describe the project's code or implementation; test conventions and the domain
  vocabulary are fine.
- **Show it in the composition** (step 6), e.g. "… + `architecture` (project) → module decisions, precedence over the
  general advice of the factory skill" (in pack-it: arch-quality-attributes).
- A gap in a factory skill that an external one fills repeatedly → propose to the human adding it to the factory.

## Example compositions
The examples assume the pack-it pack; with other packs the dimensions are the same, the skills change
(`.claude/catalog.md`).

| Task | Dimensions → skills |
|---|---|
| Analysing Angular code for DDD and archetypes | method → layer → framework → language; in pack-it: ddd-archetypes, ddd-tactical-design → fe-architecture → fw-angular → lang-typescript |
| System design (no technology) | method → layer (contracts); in pack-it: ddd-strategic-analysis, ddd-context-mapping, ddd-archetypes → be-api-design |
| Implementing an aggregate in Java | method → layer → language; in pack-it: ddd-tactical-design, ddd-archetypes → be-database → lang-java |
| A product form with features | method → layer → framework → language; in pack-it: ddd-archetypes (Product) → fe-architecture → fw-angular → lang-typescript |
| A new module following the company's decisions | method → `architecture` (project skill) → tools → `documentation` (personal skill) for the ADR; in pack-it: ddd-strategic-analysis |

## Anti-patterns
- Loading every skill "in reserve" (token cost) — only the needed dimensions.
- Writing code from memory when a language/framework skill exists.
- Carrying one language's idioms into another (e.g. classes with getters in TypeScript "because that's how Java does it").
- Fitting the model to the framework instead of the other way round.
