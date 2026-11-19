# The AI-native lifecycle — a loop with artifacts and gates

> **Contents:** 1. What changes · 2. The chain of artifacts in the factory · 3. Six stages — what the agent does, what the human does,… · 4. Build and Test stage practices · 5. Continuous evaluations of the agent configuration · 6. The Deploy stage — the agent up to the production gate… · 7. The Maintain stage — control bands instead of constant… · 8. The source of truth with existing tools · 9. Managed settings in regulated organisations · 10. The rollout order in a team · 11. AI-DLC (AWS) — glossary and rituals · 12. Anti-patterns · 13. Refinement, judgement and autonomy measures

Based on "The AI-Native SDLC Playbook" (Anthropic, 21.08.2026) and the Anthropic Academy course of the same title, and
"AI-Driven Development Life Cycle" (AWS, 31.07.2025). Described in our own words and mapped to the factory's mechanisms.

## 1. What changes
- **The bottleneck moves.** When agents write code in hours, the stages around building become the slowest: planning,
  review and tests, deployment, maintenance. You improve those, not the writing of code itself.
- **Controls built for people stop fitting.** A manual review of every line cannot keep up with a diff written by
  agents. The goals of the controls stay, the way they are enforced changes: layers of review by agents, hooks and rules
  acting at the moment the agent acts, and a human at critical and regulated code.
- **The line becomes a loop.** Every stage ends with **an artifact saved in the repository**, and the next one starts by
  reading it. The sequence of commits is at the same time the audit trail: who asked for what, what the agent produced,
  who approved.
- **The human stays above the loop.** They are accountable for every decision that needs judgement; their attention
  moves to the gates and to what the agent flagged, instead of starting every stage from scratch.

## 2. The chain of artifacts in the factory
| Stage (playbook) | Artifact in the playbook | Equivalent in the factory | Who approves |
|---|---|---|---|
| Plan — intent | `intent.md`: what, what for, constraints, success criteria | `01-discovery/brief.md` (a project) or a short change brief; the project plan `project-plan.md` | the product owner (B1) |
| Design — requirements and design together | `spec.md` with the organisation's rules as skills; reservations flagged for the policy owners | `03-requirements/requirements.md` + `04-architecture/` (ADR, threat model, `privacy.md`) | the product owner, the policy owners (B2, B3) |
| Build — a plan before the code | `plan.md`: files, order, tests — before the code | `05-plan/plan.md` (slices) + the **Step plan** section in `06-delivery/NNN-*.md`, approved before the code | the engineer / the human |
| Test — the verification loop | a diff with tests, evidence in the transcript | TDD (`tdd_guard`), verification commands in the roles, the step report with the commands' output | automatically + review |
| Deploy — review and the gate | a PR with the review findings | the PR, `/code-review`, security-reviewer, `07-review/` | the human (B4, B5) |
| Maintain — closing the loop | an incident record → a new `intent.md` | `08-operations/` → a new change brief goes back to the Plan stage | the service owner (B6) |

The playbook's rule: **nothing is implemented without an accepted plan.** When delivery departs from the plan, you
update the plan in the same commit as the code.

## 3. Six stages — what the agent does, what the human does, what to measure
| Stage | Agent | Human | Factory mechanism | Leading measure | Lagging measure |
|---|---|---|---|---|---|
| Plan | asks (scope, users, constraints, success criteria) and records the intent | approves the intent | core-plan-interview, core-problem-routing; project planning (pack-it: proc-project-planning) | time from the first conversation to an approved brief | the share of briefs that moved on without rework |
| Design | writes the requirements and the design with the organisation's rules (skills), flags reservations | settles the reservations with the policy owners | domain, architecture, privacy and spec-first test skills (pack-it: ddd-*, arch-*, arch-privacy-compliance, qa-spec-first-testing) | time from the brief to approved requirements | requirement changes after delivery started |
| Build | in plan mode reads the code without changes, proposes a plan; after acceptance delivers; parallel sessions in separate worktrees | approves the plan, steers | `CLAUDE.md`, skills, hooks, executors (subagents) | the share of changes merged on the first attempt; time from the plan to the merge | the number of fixes per change; agreement of the diff with the plan |
| Test | checks its own work (tests, build, screenshots) and iterates until it passes | judges the behaviour | `tdd_guard`, one verification command, evaluations | the share of the agent's changes green in CI the first time | PR review time; the change failure rate |
| Deploy | reviews the PR per `REVIEW.md`, addresses remarks on its PRs; in CI tasks that need judgement (triage of a build failure, a changelog draft) | approves the merge and the deployment | core-git-workflow, CI/CD and release skills (pack-it: ops-ci-cd, ops-release-engineering), branch protection | time to the first review; remarks resolved without a manual code change | defects and vulnerabilities that reached production |
| Maintain | diagnoses a control band violation, writes a change brief with evidence | triage and approval | `scripts/control_band.py`, SRE and issue triage skills (pack-it: ops-sre-incidents, proc-issue-triage) | time from the violation to a brief in the queue | repeated incidents of the same class |

DORA measures (deployment frequency, lead time for changes, change failure rate, time to restore): the continuous
delivery skill (pack-it: eng-continuous-delivery).

## 4. Build and Test stage practices
- **Plan mode as the start.** The agent reads the code and proposes a plan without changing files; the plan should be
  clear enough for someone who does not know the code to carry out.
- **`CLAUDE.md` as institutional knowledge.** Commands, conventions, architecture, frequent mistakes. `/init` gives a
  starting version, the team maintains it like code. **When the agent makes the same mistake a second time, the fix goes
  into `CLAUDE.md`** (with the human's consent; project lessons: core-project-record).
- **Skills and hooks.** Skills carry the rules (security, API conventions, the brand) and act while writing. Hooks are
  the deterministic layer: blocking protected paths, formatting and lint after an edit, secrets kept out of the diff.
- **The verification loop.** The agent has one checking command (e.g. `make test`), iterates until it passes, and the
  evidence (the literal test output, the build log, a screenshot diff) is in the transcript before the review.
- **A bug fix.** First a red test reproducing the bug, then the fix **without changing that test**. In the factory
  `tdd_guard` enforces this: rules A–B (code after a red test) and C (a warning or a block when a test is weakened: fewer
  assertions, a deleted test, an added skip; `CLAUDE_TDD_WEAKEN=warn|ask|deny|off`).
- **Parallel sessions and subagents.** Independent tasks in separate git worktrees; repeatable tasks as subagents with
  their own context (in the factory, the personas' executors).

## 5. Continuous evaluations of the agent configuration
A change of the model, `CLAUDE.md`, a skill or a hook can worsen the agent's work just as a code change worsens an
application.
- Collect **20–50 real tasks** with an expected result and record each as a scenario: a prompt + checks of acceptable
  behaviour.
- Run the set non-interactively on a schedule and at every change of `CLAUDE.md`, skills and hooks.
- **Every production incident becomes a permanent scenario** (next to the regression test in the code).
- Scenarios that stopped telling good and bad answers apart (because the models improved) you replace.
- In the factory: skills have scenarios in `tests/skill_evals/` (the `skill_gate.py` gate, a paid run only with the
  human's consent); the `team-factory` workflow runs the tests without a model on changes in `.claude/` and `.tf/factory/`.
- **Your own prompt or agent in the product or in CI** (PR review, issue triage) you evaluate with a *cases × candidates*
  matrix (prompts, models, configurations), e.g. with a tool like promptfoo: one file with prompts, candidates and cases
  with assertions. Three kinds of assertions:
  1. structural — the output is valid JSON matching the schema the gate relies on;
  2. an LLM judge — a second model judges the content per a described criterion ("points to an SQL injection on line X");
  3. code — a hard condition (e.g. a score ≤ 3 for a diff with a planted bug).
  In every cell of the matrix: passed/failed, cost and time.
- The cases are diffs with **planted, known bugs** and clean diffs (a false alarm check). By default one failed case = a
  red run; loosening the threshold only consciously and with a record.
- Every change of the prompt, the model and the criteria goes through the set — it catches a silent regression (it
  catches bug A better, it stopped catching B). You base the choice of a cheaper or more expensive model on the matrix,
  not on one PR.

## 6. The Deploy stage — the agent up to the production gate and not a step further
- **An AI review of the PR** (core-git-workflow): the review rules in `REVIEW.md` in the repository root, the passes
  "bugs and logic", "security", "agreement with the specification and the plan", a severity for every finding, monthly
  tuning (an assessment of accuracy, a limit on nitpicks, excluding generated code and what CI checks).
- **Separation of duties:** the agent does not approve its own code; merging into the main branch needs a human's
  approval (branch protection). The decisions stay in the PR history as the audit trail.
- **Hooks as approval gates:** a hook can ask the human and hold an action (e.g. a production deployment needs a named
  approval).
- **An agent in CI:** run non-interactively for tasks that need judgement, in a sandbox, with least-scope credentials
  (core-agent-security; pack-it: ops-ci-cd).

## 7. The Maintain stage — control bands instead of constant watching
- **Deterministic detection:** a script computes the mean and the standard deviation of a metric (e.g. the test failure
  rate, the 5xx rate, the PR cycle time) and applies the Western Electric rules — `scripts/control_band.py`.
- **Reaction levels in a configuration under version control** (the playbook's proposal):

  | Level | Condition (the script's default) | Reaction |
  |---|---|---|
  | log | 4 of 5 points beyond 1σ or 8 on one side of the mean | a record only |
  | diagnose | 2 of 3 points beyond 2σ | the agent diagnoses **read-only** |
  | act | a point beyond 3σ | the agent may act: open a PR or run a previously approved runbook |

- The agent writes **a change brief** with the evidence of the anomaly, the proposed outcome, the systems concerned and
  questions. The brief goes through the normal loop from the Plan stage, and the change — through the normal PR review.
- Periodic security scans: a narrow finding → a fix and a PR; a broad one → a change brief. Every released fix adds an
  evaluation scenario.
- Permissions and managed settings block the agent's unauthorised access to production; calls, findings and triage have
  a timestamp.

## 8. The source of truth with existing tools
When the company has Jira, ServiceNow or a requirements tool, name one source of truth:
- **the repository** — the markdown artifacts are binding, the external tool refers to commits;
- **the external tool** — the markdown is a working copy, and a connector (MCP) writes the findings back;
- **the minimum: a link** — both places keep references to each other (e.g. the issue key in the artifact's header).
Details for the project record: core-project-record.

## 9. Managed settings in regulated organisations
The platform team deploys non-negotiable controls through Claude Code managed settings (`managed-settings.json` via a
file, MDM or the console; they take precedence over user and project settings, except for a few security exceptions).
The playbook's categories:
- permission denials (secrets, arbitrary outbound traffic);
- an enforced sandbox (isolation of the file system and the network);
- approvals only through hooks for protected actions;
- managed MCP servers and an allowlist of plugins, skills and agents;
- minimum versions (refusing to start on an unapproved model).
You check the key names in the documentation (code.claude.com/docs/en/managed-settings) for your Claude Code version —
you do not guess them (core-grounding). The factory installs only locally in the project and does not change these settings.

## 10. The rollout order in a team
The playbook splits the change into 12 modular "plays" on five dependency levels. It starts with running every stage by
hand and ends with a loop in which an accepted artifact triggers the next gate.

| Level | Play | State in the factory |
|---|---|---|
| 1 (no dependencies) | recording the intent, `CLAUDE.md`, skills, the verification loop, hooks, plan mode | present: the brief, `CLAUDE.md`, core and pack skills, `tdd_guard` and the security hooks, core-plan-interview |
| 2 | subagents (needs `CLAUDE.md`), evaluations (need `CLAUDE.md` and the verification loop) | present: the personas' executors; skill evaluations; no set of project tasks |
| 3 | requirements and design (intent + skills), PR review (evaluations + subagents) | present: phases 2–4; PR review — `REVIEW.md` to be created in the project |
| 4 | CI/CD (PR review + hooks) | partly: the `team-factory` workflow, the CI/CD skill (pack-it: ops-ci-cd) |
| 5 | closing the loop (CI/CD + intent) | phase 9, `control_band.py`; starting the agent automatically — the human's decision |

## 11. AI-DLC (AWS) — glossary and rituals
- **The pattern:** the agent creates a plan → asks questions → the human validates → only then the agent delivers; the
  same at every activity of the cycle. In the factory: core-plan-interview and the gates.
- **Phases:** Inception (intent → requirements), Construction (architecture, domain model, code, tests), Operations
  (infrastructure as code, deployments under the team's supervision). The context passes from phase to phase through
  artifacts in the repository.
- **Mob Elaboration / Mob Construction:** the whole team in one session validates the agent's questions and proposals —
  requirements (Elaboration) or technical decisions (Construction). Good for a new product and decisions that are hard
  to reverse; in the factory: a facilitated workshop (pack-it: ddd-facilitation) and a plan review by several people.
- **Bolt** (a cycle of hours or days instead of a sprint) and **Unit of Work** (instead of an epic) — when working with
  agents, shorter cycles and smaller batches (pack-it: eng-continuous-delivery).

## 12. Anti-patterns
- Stages without a saved artifact — information gets lost between stages.
- A weak verification loop — unchecked code reaches the human's review.
- Evaluations that went stale and no longer tell good answers apart.
- Approval gates without an audit trail.
- Secrets in the agent's context (core-agent-security).
- An untuned AI review that buries the team in nitpicks.

## 13. Refinement, judgement and autonomy measures
- **The executor tells the solution back in their own words** before the implementation (the problem, the behaviour, the
  approach, the risks, the decisions made), and the owner checks it against the intent — the human is not just a relay
  between agents. Mock-ups from existing components and the design system before the code are a test of shared
  understanding (check that they do not smuggle in new product decisions).
- **Judgement does not escape into the steps:** refinement ends with an issue written by a human for a human, not a
  generated description or a prompt. If nobody can explain how the work will be done, refinement is not finished. A
  deeper review (testing together, walking through the solution with a group) only above thresholds of change size and
  risk area, not at every PR. Flow measures: PR size, time to the first review, the number of open PRs per person.
- **Autonomy measures** (the share of merged PRs authored by an agent, the human's review hours per change, the task time
  from start to end) are activity measures. As a target they are prone to Goodhart, because the agent will fill any
  counter. You report them only **paired with an outcome measure**: the share of defects that reached the user, the
  change failure rate, the cost of a change, the time from intent to production, the movement of a business metric. When
  only one of the pair improves, the goal is not met. Data from the source systems (repo, CI, incidents), not from
  self-assessment. A dashboard: pack-it: eng-continuous-delivery.
Sources: Pragmatic Coders, "Refinement with AI…" (2026-10-01); A. Honchar, "Agentic SDLC: Strategic Reading List"
(2026-05-27); J. Wąsowski, "SDD Factory OKRs" (2026-10-21); thresholds and shares from the articles [unverified].

## Sources
- Anthropic, L. Claxton, "The AI-Native SDLC Playbook", 21.08.2026 — claude.com/blog/the-ai-native-sdlc-playbook
- Anthropic Academy, the course "AI-Native SDLC Playbook" (14 lessons) — academy.claude.com/courses/ai-native-sdlc-playbook
- AWS, Raja SP, "AI-Driven Development Life Cycle: Reimagining Software Engineering", 31.07.2025 —
  aws.amazon.com/blogs/devops/ai-driven-development-life-cycle
- The 10xDevs course, ed. 3 (2026), module 5, lesson 3 (evaluations of a review agent) — training material (accessed
  2026-10-09); promptfoo (the npm package 0.124.1 checked 2026-10-10: the `promptfooconfig.yaml` file, the assertions
  `is-json`, `llm-rubric`, `javascript`, the threshold `PROMPTFOO_PASS_RATE_THRESHOLD`) — promptfoo.dev/docs
- Claude Code: managed settings, Code Review (`REVIEW.md`), GitHub Actions, hooks — code.claude.com/docs (accessed 2026-10-04)
