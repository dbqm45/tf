---
name: ddd-strategic-analysis
description: Use for splitting a domain into subdomains (core, supporting, generic) and context boundaries, Cynefin.
metadata:
  review: "2027-10-17"
  catalog: "Use when choosing the analysis strategy (Cynefin, top-down vs bottom-up), splitting a domain into subdomains (core, supporting, generic) and drawing context boundaries (bounded contexts). Not for the relationships between contexts (ddd-context-mapping) or running a workshop (ddd-event-storming)."
---

# Strategic analysis

## Does DDD make sense here?
It is worth it when the domain is complex by nature (**essential complexity**, which cannot be removed without losing functionality),
there is access to experts and the team can iteratively "crunch" knowledge. It is not worth it when the challenge is
scale or ergonomics, not business rules (e.g. a simple blog) — then keep it simple.
Watch out for **accidental complexity** (from the chosen solutions): a new framework, protocol or buzzword will not fix a bad model.

The formal initial assessment ("whether to modularize?" — three questions, the human's verdict) and business areas based on evidence
are prepared by ddd-discovery-intake. An area from intake is **input** to this analysis, not a ready context.

## Step 1: Big Picture, to see where we are
Before you choose a method, run a Big Picture Event Storming (ddd-event-storming): what the high-level processes are,
which **key questions** come up in many places and branch the process. On this basis assess the areas per Cynefin.

## Step 2: Cynefin — choosing the way of analysis
| Side | Domain | You recognize it by | How to analyse |
|---|---|---|---|
| **Right (ordered)** | Clear, Complicated | experts agree, there are procedures/regulations, cause → effect can be established (sometimes through an expert) | the business is usually **process-driven** → **top-down analysis**: first the processes, then the design |
| **Left (unordered)** | Complex, Chaotic | experts disagree, a new product/market, a lot of "we do not know", effects are visible only after the fact | **do and check** (probe → sense → respond) → **bottom-up analysis** |

Different parts of one domain can lie on different sides — choose the approach per area, not for the whole system.
Business archetypes (ddd-archetypes) work best on the right side.

### Top-down (the right side)
1. Big Picture → a list of high-level processes and pivotal events.
2. Process Level for the key processes (start with the core domain and with the biggest problems from the vote).
3. Draw the contexts and the relationships between them (ddd-context-mapping).
4. Design Level in the selected contexts → design (ddd-tactical-design).

### Bottom-up (the left side)
1. Start with **concrete cases** and examples, not with the general process.
2. Build a small model for one case, check it in practice (a prototype, a spike, a test with a user).
3. Generalize only when further cases confirm the pattern; keep decisions reversible.
4. In an existing system: read the code and the data — a glossary from class/table names, "status" fields, "god classes",
   repeated conditions; reconstruct the events from the code and verify them with an expert.

## Step 3: Distillation — subdomains
| Type | Recognizing question | Investment |
|---|---|---|
| **Core** | Does this give a competitive advantage? If we bought it, would we lose what sets us apart? | the best people, full DDD, a deep model, continuous care (like a bonsai) |
| **Supporting** | Needed to operate, but does not set us apart | simpler, a lower bar, a candidate for outsourcing |
| **Generic** | Every company has the same (invoicing, authentication) | buy/use a ready one, integrate through an ACL |

## Step 4: Context boundaries — heuristics
A context is a boundary within which the model and the language are consistent. Draw it on the basis of **behaviour and language**, not nouns.
- **Language**: the same word means something else → different contexts.
- **Pivotal events** and a change of swimlane → natural cuts.
- **Autonomy**: can this part make decisions and deploy changes without asking others?
- **A different pace of change and different actors/departments** → separate contexts.
- **Key questions**: the context that "owns the answer" to a question asked in many places.
- **A capability instead of a product**: extract a general capability (e.g. "resource availability"), not a product variant
  ("car booking", "room booking") — products change, the capability stays.
- **The problem class**: CRUD, computation, integration and competition for resources usually want different models (ddd-deep-modeling).
- **Consistency**: rules that must be consistent immediately cannot cross a context boundary.
- **The algorithm underneath** (ddd-algorithm-recognition): the same algorithm in several areas → a candidate for merging or for a shared kernel;
  the same words, different algorithms → a seam, that is a likely boundary; no known algorithm → a candidate for core, bottom-up analysis.

Anti-patterns: context = entity (a "Customer Service" with every customer behaviour), context = technical layer,
context = team regardless of the language, mixing contexts "because it is faster".

## Recording the result
`docs/project/02-domain/strategic.md`: areas with the Cynefin assessment and the chosen method, subdomains with the type and the justification, contexts
(name, responsibility, key concepts, input/output events, owner), open questions.
Decisions about boundaries → ADR (docs-tech-writing).

## Checking the boundaries before the decision
- **A stress test with a business metric** (ddd-model-stress-test): the same frozen set of requirements, generated without insight
  into the architecture, run against two variants of the split — compare the distribution of local/distributed/new-module changes.
- **Measuring the couplings** of key pairs (ddd-connascence-analysis) — for an existing system or a context map.
Attach the results to the ADR as evidence.
