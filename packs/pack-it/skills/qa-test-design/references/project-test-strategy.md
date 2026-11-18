# The project test strategy — a living document

The file: `docs/project/05-plan/test-strategy.md` (template: `.claude/skills/qa-test-design/templates/test-strategy.md`).
The change's test plan (`test-plan.md`) draws on the strategy and updates it when it is done.

## When
A project with no tests, or with tests "where it is easy" — before the agent writes the first test. Without a strategy the agent covers
helpers and formatters, the coverage percentage grows, and the critical flow (payment, access to content) stays unprotected.
Tests start from risk, not from a file.

## Inputs — you read, you do not invent; every fact with a source path
- the requirements (users, flows, rules, exclusions), the roadmap (what will change → probability),
  closed changes, the stack and the existing test configuration, `CLAUDE.md`;
- the **test base profile** in one word: `brak` (none: no configuration, < 3 test files), `rzadki` (sparse: configuration, but
  a dozen or so files or all in one place), `znaczący` (significant: tests in many areas);
- **hot spots from git history** — the number of commits per directory over the last ~30 days, only hand-written code (no
  lockfiles, snapshots, generated code, `dist`). You show the human the scan scope. Fewer than ~5 commits
  in the window → skip the scan and record that the probability rests on the roadmap and the interview.

## The interview (one question at a time, with 2–3 sample answers, an echo of the answer in one line)
- W1. What are you most afraid of breaking — regardless of the documents?
- W2. Where have you been burned before (in this code or similar)?
- W3. What do you change most often and without certainty?
- W4. What is under-tested today? (profile `rzadki`: "which gap worries you most?"; profile `brak`: skip)
- W5. What do you NOT want to spend the test budget on? → the section "What we knowingly do not test".

Three skipped questions → you end the interview and note that the strategy rests solely on the documents.

## The risk map (5–7 rows)
A risk is a failure scenario felt by a user or the business — not the name of a module or a test.
Good: "a logged-in, paying user gets 403 on their own content". Bad: "test the login form".

| Rating | Impact | Probability |
|---|---|---|
| high | loss of access, data or money; a publicly visible failure | the area changes every week or there was an incident here |
| medium | a feature works worse, there is a workaround, it affects some users | changed from time to time, has been a source of bugs |
| low | cosmetics, easy to roll back, no effect on data | stable, rarely touched |

- The order: high × high first. High impact × low probability (a cloud provider outage) is usually
  monitoring and an alert, not a test (ops-observability) — record that instead of a row.
- The **Source** column: the evidence that raised the risk — a row of the requirements, a roadmap item, a closed change, an answer W1–W5,
  a directory with a commit count, a stack constraint. **Not** a file, `file:line`, a function or a module — that is settled only by
  the code analysis in the phase (eng-codebase-mapping). A row that loses its source without an anchor in the code, delete or back it
  with the interview.
- **The abuse lens** — mandatory for login, payments or any user input: at
  least one row from the classes: someone else's resource (an ownership check, not just being logged in), untrusted input
  (injections, server-side validation), a leak of secrets or personal data (logs, error content, the front-end
  bundle), resource abuse (bypassing a limit, an expensive operation in a loop). No such rows for these
  surfaces is a gap, not proof of security (arch-threat-modeling).
- The risk numbers are fixed; you add new ones at the end.

## The response to a risk (one row per risk)
| Risk | What will prove the protection (observable behavior) | The assumption to challenge | The context to settle in the code | The cheapest layer (hypothesis) | The anti-pattern to avoid |

Assumptions to challenge, e.g.: "a successful login = access to paid content", "200 = the write succeeded", "an empty
response = no data". You reject answers like "unit tests of module X", "cover the main path", "an assertion
on the current result". A risk for which the row cannot be filled, rephrase or delete.

## The check before writing (every risk)
1. A defect or a description of the implementation? A risk that requires a safeguard that does not exist ("no retry") is speculation —
   rephrase it to what exists ("a provider failure ends in a clean 5xx, does not pretend success, saves nothing").
2. Is there no anchor in the code in the source?
3. Will the response catch a real regression, or will it only raise coverage?

List the deleted or rephrased risks in one line, "Check results".

## The rollout phases (3–5)
| # | Phase | What protection it proves | Risks | Kinds of tests | State | Change folder |

The states (fixed words): `nie rozpoczęta` → `otwarta` → `zbadana` → `zaplanowana` → `w realizacji` → `zakończona`
(not started → open → studied → planned → in progress → completed).
You derive the state from files on disk (there is an analysis → `zbadana`, there is a plan → `zaplanowana`, progress ticked off →
`zakończona`), not from the memory of the conversation. Profile `brak`: phase 1 = setting up the runner and the first integration test for
risk #1. Every phase ends with updating the recipes.

## Quality gates
| Gate | The layer (edit / commit / push / CI) | Required from | What it catches |

Every row is either already wired in or points to the phase that will wire it ("from phase 2"). A gate without a phase is a wish.
Local layers: eng-local-quality-gates; CI: ops-ci-cd.

## Recipes (they grow with the phases)
At the start: `TBD — faza N (ochrona przed <zachowanie>)` (TBD — phase N, protection against <behavior>). After a phase, for each kind of test: location, naming,
the policy on doubles, a model test (the path), the run command. 3–6 recipes; a rare case = a link to a test.
After entering a recipe, update the tests section in the project's `CLAUDE.md` — otherwise every agent guesses the commands.

## What we knowingly do not test
The answers to W5 with a reason and a condition for reassessment. More than 5–6 points = the strategy is too broad.

## Freshness
The review date, tool versions and the date the references to AI tools were checked. A review when: a new risk in the top 3,
a tool date older than 3 months, a stack change, an exclusion stopped being true. A change to risks or phases goes
as a separate change; the exception — a fix to a risk's wording after the code analysis, with the human's consent.

## What is not in the document
Test code, CI YAML, hook scripts, anchors in the code in the risk map, new state words.

## Sources
- The 10xDevs course, ed. 3 (2026), module 3, lesson 1 (the project test plan) — training material (accessed 2026-10-09).
- ISTQB CTFL v4.0 — risk-based testing (impact × probability).
Described in our own words.
