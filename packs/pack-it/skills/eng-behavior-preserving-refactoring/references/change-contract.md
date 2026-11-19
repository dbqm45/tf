# A change contract in an existing system

When a change in legacy **should** change behaviour (a bug fix, a small feature) while the rest stays, you describe the task for the agent
with a contract. A full inventory of the system at the start is not needed; the reach of the change is enough.

## Six fields
| Field | What you write |
|---|---|
| **Condition** | when the change applies (input data, state, role) |
| **Expected result** | an observable result, not "the bug is gone" |
| **Protected behaviours** | the table below, with a decision for every item |
| **Allowed file scope** | the paths that may be changed; going outside the scope is a report to a human, not the agent's decision |
| **Proof of the fix** | a test red on the base commit and green after the change |
| **Proof of no regression** | protective tests recorded on the base commit **before** the change (a separate stage and commit), green before and after |

## Protected behaviours — four sources within the reach of the change
1. **Callers and consumers** (grep, the import graph, API call logs, eng-codebase-mapping). Finding none
   is limited knowledge, not proof that there are none — record that.
2. **Incidents and tickets** concerning these files.
3. **Frequently changed files** within reach (`git_territory.py --hotspots`).
4. **Characterization tests** of the existing behaviour (the "Precondition" section in SKILL.md).

| Behaviour | Source | Decision | Who decided |
|---|---|---|---|
| `GET /invoices/{id}` returns 404 for someone else's invoice | consumer: the customer portal | commitment (protect) | J. Nowak, module owner |
| the order of items in the CSV export | characterization test | incidental (may change) | J. Nowak |
| VAT rounding per item | incident INC-88 | for the owner to decide | — (open question) |

- A **commitment** gets a protective test before the change. An **incidental** behaviour may change, with an entry in the report.
  **For the owner to decide** blocks the start until the owner (a person, not "the team") settles it.
- A change of behaviour visible to a consumer is no longer refactoring: a human's consent and an entry in `decisions.md`.
- When the change is closed, the approved guarantees go into the requirements as **added** (the first record of the requirement)
  together with their test (proc-requirements-shaping, `references/existing-specifications.md` §4).

Sources: J. Wąsowski, "Brownfield Spec and Preservation Contract" (2026-10-22); the numbers from the article (e.g. the share
of agentic PRs with a reverting commit) [unverified]. The sample table rows are an illustration.
