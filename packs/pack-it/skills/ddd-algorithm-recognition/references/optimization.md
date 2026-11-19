# Optimization and constraints

| id | Matching question | Signals | It is not this if… | Pitfalls |
|---|---|---|---|---|
| **knapsack** | choose the subset of greatest value within one limit? | a budget, a capacity, "what is worth taking" | there are several limits → `knapsack-multidim` | pseudo-polynomial; large values → approximation |
| **knapsack-multidim** | as above, but limits in many dimensions (people × competences × time × budget)? | "match projects to resources", many constraints at once | we assign elements to many "knapsacks" → GAP / `linear-programming` | grows fast; a MIP solver; the General assignment archetype |
| **bin-packing** | fit everything into as few containers as possible? | containers, vehicles, slots, "how many cars are needed" | the number of containers is fixed, the value counts → `knapsack` | NP-hard; FFD heuristics give good results |
| **set-cover** | the smallest set covering all requirements? | "so that every competence is staffed", a minimal team | — | greedy approximation; cost weights |
| **interval-scheduling** | the most non-colliding tasks in time / assigning rooms? | rooms, slots, "how many meetings will fit" | the intervals have values → the weighted version (DP) | greedy by the end of the interval works only for the unweighted version |
| **linear-programming / MIP** | maximize/minimize under linear (integer) constraints? | "the optimal mix", a schedule, budget allocation | logical, not numerical constraints → `csp` / `sat` | use a solver; model ≠ implementation |
| **csp** | assign values to variables under rules of the type "if… then not…"? | product configuration, a schedule with rules, compatibility | — | a CP solver; the Configurator archetype |
| **sat / maxsat** | satisfy (hard) logical rules / as many soft ones with weights as possible? | permissions, exclusions, "soft rules with a priority" | — | the weights of soft rules are a business decision (fairness) |

Principle: for NP-hard problems **do not write your own algorithm** — a solver behind a domain interface + a spike with an abandonment criterion
(arch-tech-selection). The domain model describes the constraints, the solver solves them.
