# The Configurator archetype — mapper (options, rules, process, solver)

> **Contents:** Fit test · Model (the essence) · Questions · Mapping steps · Decisions to check (R/A/X) · Result format · Patterns and pitfalls · Quality check · Example (shortened)

It turns requirements in which the customer **assembles a product from options** (a car, a computer, an insurance package, a subscription), and the options
have dependencies ("not together", "only together", "one of", "if A, then one of B/C", "if A, then not D"), into a model of
declarative rules, a configuration process and a solver. Coded with `if`s in the UI and the backend, they quickly stop agreeing,
and checking whether a combination is possible at all becomes hard. The effect: rules are added as **data**, every
unavailable option can be **explained**. The common protocol: `SKILL.md` → "Mapper — the common protocol".

## Fit test
**The core question:** *does choosing one option change which other options are allowed or required?*
Yes → it fits. The options are independent (any combination) → product features are enough.

| Signal in the requirements | Fits? |
|---|---|
| "X cannot be chosen together with Y", "Z requires W" | ✅ |
| "choose exactly one / at least one of" | ✅ |
| a step-by-step wizard with greyed-out options | ✅ |
| "why can't I choose this option?" | ✅ |
| "how much does this configuration cost?" | ❌ → Pricing (next to the Configurator) |
| "is this variant in stock / free on a date?" | ❌ → Product / Availability |
| "variant = size × colour, all combinations allowed" | ❌ → Product (features with constraints) |
| "assign resources to tasks by requirements" | ❌ → General assignment |
| "form validation: required field, format" | ⚠️ borderline |

**Borderline cases:**
- *Form validation* — do the rules **connect many fields with dependencies** that change and cannot be checked
  individually? No → ordinary validation; yes → Configurator.
- *Numeric rules* ("total power ≤ 750 W", "max 4 modules") — pure yes/no logic is SAT; numbers → CSP (the same archetype,
  a stronger engine). Record it as a decision.
- *Commercial packages* ("the Sport package contains A+B") — this is a "requires" rule or a separate composite product (Product); the deciding question is
  whether the package has its own price and identity.

## Model (the essence)
| Element | Essence |
|---|---|
| **Configuration definition** | for a product/model: a set of **options** and **rules**; product/marketing changes it; **versioned** |
| **Option** | a selectable element (e.g. "2.0 engine", "tow hitch"), may belong to a group (e.g. "colour") |
| **Rule** | a declarative constraint — the table below |
| **Default value** | the option selected at the start if the customer does not decide otherwise; must not break the rules |
| **Configuration process** | a separate object with its own ID; the customer creates it: a start with the definition, successive **choices** (and undos), a list of **unselected** ones, a query about the **missing** options for a valid configuration |
| **Resolution** | rules + choices → a logical formula (clauses); a **SAT solver** (e.g. DPLL) or **CSP** checks whether a valid **completion** exists, and which options are still possible |
| **Explanation** | for an unavailable option: which rules and which choices block it (a minimal conflict set) |
| **Saved configuration** | the result of the process + the version of the definition under which it was valid |

**Kinds of rules**
| Rule | Meaning | Clause (idea) |
|---|---|---|
| requires (must be together) | A → B | ¬A ∨ B |
| excludes (not together) | ¬(A ∧ B) | ¬A ∨ ¬B |
| one of (exactly one) | exactly 1 from the group | at least 1 + pairwise excluded |
| at least one of | ≥ 1 from the list | A ∨ B ∨ C |
| must be selected | A always | A |
| conditional inclusion | if A → one of the list | ¬A ∨ B ∨ C |
| conditional exclusion | if A → none of the list | (¬A ∨ ¬B) ∧ (¬A ∨ ¬C) |

Separate **the definition** (product/marketing) from **the process** (the customer). The solver is an engine behind the archetype's interface — the model says
"options and rules", not "boolean variables".

## Questions
**A — standard decisions:**
- What are the options and what dependencies are there between them? **Who defines them and how often do they change?**
- Should the customer see **why** an option is unavailable?
- Does the configuration have a **price** (Pricing) and **availability** (Availability/Product)?
- Must saved configurations remain **valid after the rules change**?
- Process: successive steps in a fixed order or freely? May a choice be **undone**?
- A choice contradicting an earlier one: **reject** it or propose an **automatic change** (remove the conflicting ones)?

**B — gaps** (examples):
- default values and changing them after another option is chosen? · automatically adding required options (A → B adds itself)?
- numeric rules (a sum, a quantity limit)? · rules depending on the channel/market/date? · saving an unfinished process and coming back?
- the configuration as the basis of an order (freezing the definition version)? · a definition test: is every option reachable at all?

## Mapping steps
1. **Options and groups** — the list of options, "one of" groups, mandatory options.
2. **Rules** — write each dependency from the requirements as a rule from the kinds table; name it in the language of the business (for explanations).
3. **Default values** — which ones, and are they valid against the rules (check with the solver).
4. **Process** — steps (fixed/free order), choice, undo, conflict handling (reject / propose a change), missing options.
5. **Engine** — SAT (yes/no only) or CSP (numbers, sums); what it returns: possible options, missing ones, an explanation.
6. **Versioning** — the definition in versions; what happens to processes in progress and saved configurations when the rules change.
7. **Boundaries** — price (Pricing), stock/availability (Product/Availability), permissions (who sees the options) outside the archetype.

## Decisions to check (R/A/X)
the kind of each rule · "one of" vs "at least one" groups · default values · the order of steps · undoing choices ·
conflict handling (reject / auto-change) · automatically adding required options · SAT vs CSP · the scope of explanations ·
versioning of the definition and the fate of saved configurations · who edits the definition.

## Result format
```markdown
# Configurator model: <area>
## Concept mapping    — | Domain concept | Archetype element | Justification |
## Unmapped concepts
## Options and groups — | Option | Group | Mandatory | Default |
## Rules              — | Name (business) | Kind | Options | Source |
## Configuration process — steps, undo, conflict handling, missing options
## Engine             — SAT/CSP, queries: possible / missing / explanation
## Versioning         — | Definition change | Processes in progress | Saved configurations |
## Decisions (R/A/X)  — | Decision | Source |
## Notes              — assumptions (X), variable policy parameters, boundaries with Pricing/Product/Availability
```

## Patterns and pitfalls
- The same rules written with `if`s in the UI and the backend drift apart — **one definition**, the UI asks the solver for possible options.
- Checking rules only in pairs will not detect a dead end (valid choices, but it cannot be completed) — you need a check
  of **possible completions** with the solver.
- A greyed-out option with no reason frustrates the customer — rules have **business names**, the explanation points to the rule and the choice.
- Default values contradicting the rules after a definition change — test the definition (every option reachable, defaults valid).
- Changing the rules "in place" invalidates orders — **version** them; a saved configuration points to a version.
- A price written into an option → mixing archetypes; an option's price is a Pricing calculator.
- **Outside the archetype:** "may this customer order the fleet version?" is authorization/policy (the application layer), which
  supplies the allowed set of options or additional rules as a **parameter** of the definition; the Configurator computes mechanically.

## Quality check
- [ ] every dependency from the requirements is a rule with a kind and a business name
- [ ] every option reachable, default values satisfy the rules
- [ ] the process has: choice, undo (or an explicit "no"), conflict, missing options
- [ ] the engine (SAT/CSP) matched to the kind of rules; explanations defined
- [ ] versioning of the definition and the fate of saved configurations settled
- [ ] the mapping table and "Unmapped concepts" present; no material (X)

## Example (shortened)
**Input:** "A camper van: a short or a long conversion. The long one requires the 2.2 engine. A solar panel requires an extra battery.
An awning does not fit with a roof rack. The short conversion is standard."

```markdown
## Options and groups
| short / long | conversion (one of) | yes | short |
| engine 2.0 / 2.2 | engine (one of) | yes | 2.0 (X → A) |
| solar_panel, extra_battery, awning, roof_rack | — | no | — |
## Rules
| Long conversion only with the strong engine | requires | long → 2.2 | R |
| The panel needs a battery | requires | panel → battery | R |
| The awning collides with the roof rack | excludes | awning, roof rack | R |
## Process — any order; choosing "long" with the 2.0 engine: propose a change to 2.2 (A)
## Decisions
| auto-adding the battery to the panel | "It depends" → parameter `auto_add_required` per channel (showroom/online) (A) |
| saved configurations after a rule change | X → hot spot |
```
