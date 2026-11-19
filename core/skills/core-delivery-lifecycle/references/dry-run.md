# A dry run — how to check whether the factory delivers a project

The goal: to measure on a small, real project whether the factory takes it from an idea to a state ready for
deployment, how much it costs and where it needs a human. The result is a report with numbers and a list of fixes to
the factory, not only a working application.

A ready kit (an idea with the product owner's decisions, step-by-step commands, a measurement sheet) is in the factory
repository: `docs/pilot/`.

## Choosing the project
- Small but complete: a few use cases, login, a database, one integration or a background job, deployment to a test
  environment. Example: booking rooms in an office (a room calendar, a booking with a conflict check, cancelling, an
  e-mail notification, an administrator panel).
- From the stack the factory knows best (TypeScript or Java, PostgreSQL, Docker, CI).
- Without production data and without real outside users. The test environment in containers or a local cluster, mail
  through a local test server (e.g. Mailpit).
- A new, empty repository with the factory installed (the factory README, "Installing in a project").

## The course
1. **Phase 0**: the pack's dispatcher (pack-it: `claude --agent maja`) with a description of the idea in 3–5 sentences.
   Answer the questions as the product owner. The dispatcher chooses the path (shortened or full for this example;
   record which one and why).
2. **Phases 1–5**: start the personas from the Handoff. At the gates read the TL;DR and accept or send back with remarks.
3. **Phase 6**: delivery step by step; after every step check the step report and the green CI.
4. **Phase 7**: the readiness review in the full version (`production-readiness.md`), including a rehearsed rollback
   and backup restore in the test environment.
5. **Phase 8**: deployment to the test environment as if it were production: a gradual strategy, observation, a retrospective.

## What to measure (record along the way in `docs/project/07-review/<data>-dry-run.md`)
| Measure | How |
|---|---|
| time per phase | from the start of the session to the `proposed` artifact |
| cost | tokens or the amount from the dashboard, broken down by personas and models |
| human interventions | number and kind: an answer to a question, a substantive correction, a technical correction, unblocking (an account, a secret) |
| send-backs at the gates | how many times an artifact went back for a correction and why |
| defects | found by the factory's tests, by the review, by the human, after deployment (the last ones matter most) |
| compliance with the requirements | how many acceptance criteria met at B4 |
| readiness points | met / not met / accepted risks |
| continuity | whether every session started from the record without repeating the previous one's work |

## Assessment
- **The factory delivers** when: all "must" criteria are met, the readiness review has no unmet *(minimum)* points, the
  rollback and the restore worked, the human did not have to write or fix code, and the interventions concerned
  decisions, not repairing the agents' work.
- **It delivers with help** when the human had to fix artifacts or code, but the project reached B4.
- **It does not deliver** when the project got stuck before B4 or the defects after deployment concern "must" requirements.
Turn every technical intervention and every send-back into a conclusion: which phase, persona or skill it concerns and
what to change in it.

## Conclusions for the factory
- The project's lessons (core-project-record, `lessons.md`) concern this project. Record fixes to the factory (skills,
  roles, personas, hooks) separately as a list of proposals for the human, because changes in `.tf/factory/` and
  `.claude/hooks/` need their consent (CLAUDE.md).
- Repeat the run after the fixes on another small project, so as not to fit the factory to one example.
