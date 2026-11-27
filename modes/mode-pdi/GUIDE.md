# pdi — decisions in one source

The `mode-pdi` mode adds to the factory decision recording consistent with the pdi register. Without it the factory works as before.
Install: `tf add mode-pdi`, remove: `tf remove mode-pdi`.

## What it gives
- **Change log:** `python3 .claude/skills/pdi-decisions/scripts/decision_record.py change new CHG-12 --source PRB-34`
  creates `docs/project/changes/CHG-12/` with `intent.md`, `plan.md` and `decisions.md`; the headers follow pdi contract
  0.3.0 (`contract/change.schema.json`). `decision_record.py check` checks the headers.
- **Decisions:** the `pdi-decisions` skill (shared by all personas), after a human approves the draft, records
  the decision about a change in `decisions.md` (`decision add`) and — when the pdi MCP server is connected — in the pdi register:
  a draft (`present_decision_draft`) that a human approves in the pdi console, then `record_decision`, which assigns the
  number `DEC-n` (`decision mark`). Gates, inbox items and triage are decided only with buttons in the pdi console. Unsent: `decision pending`; all
  in JSON: `decision export`.

- **Phases run by pdi (F4):** after a decision at a gate the pdi inbox calls the `sdlc-phase.yml` workflow in the repo
  (`python3 .claude/skills/pdi-decisions/scripts/phase_run.py workflow install`). The workflow records the decision in
  `decisions.md` (`decision_record.py decision gate`), runs the phase persona without interaction (`phase_run.py run`:
  `intent` — maja, `requirements` — ewa, `architecture` — tomasz, `design` — natalia, `delivery` — tf (the factory loop); another
  persona in `.claude/pdi-phases.json`), opens the phase PR on the branch `pdi/CHG-n-<phase>` and sends pdi a request for the
  next gate (`phase_run.py gate request`, a signed `gate.requested` to `PDI_EVENTS_URL/events/tf`).
  Needed: the secrets `ANTHROPIC_API_KEY` and `PDI_TF_SIGNING_SECRET` (the same in the pdi receiver), the variable
  `PDI_EVENTS_URL`; in pdi `PDI_DISPATCH_REPO` points to this repo. When approving a gate, merge the phase PR too — the next
  phase starts from the default branch. Every run costs money (the model); the phase limit is `PDI_PHASE_BUDGET_USD` in pdi.
  Accepting a report in pdi (F3) runs the `intent` phase with the inputs `source` (PRB) and `problem` (the report's content):
  the workflow creates `docs/project/changes/CHG-n/` with the source and the report date (`source_reported_at`, from which
  ShipScope counts lead time from the report), and the persona writes `intent.md` from the reporter's problem.
  The change templates are in English (`## Gate questions`, the plan columns `Slice | Kind | Release | Flag | …`,
  `## Options considered`, `## Change targets`); the readers still accept the Polish forms of older changes.

- **Runs on the DI Team board (contract 0.15.0):** the hook `run_report.py` reports every Claude Code session to pdi as
  one agent run: `run.started` at start (who: `git config user.name`; how: `manual`, or `pdi` for a phase run, which
  also carries the change and phase), `run.progress` after each turn (the goal of the active `.tf/wip/` checkpoint as
  the activity) and `run.finished` at the end (with the duration). It sends only when `PDI_EVENTS_URL` and
  `PDI_TF_SIGNING_SECRET` are set in the session's environment (the same as for phases); `TF_RUN_REPORT=0` turns it off.
  No prompt, code or file content leaves the machine; a refused or unreachable pdi never blocks the session (the error
  goes to `.tf/logs/hook-errors.jsonl`). pdi keeps the runs in `agent-runs/`.
- **Decisions in the suite index (D3, contract 0.17.0):** the hook `decision_publish.py` (session start and end) sends
  the project's decisions to pdi as `decision.recorded`: accepted rows of `docs/project/decisions.md` (D-NNN) and
  accepted ADRs in `04-architecture/adr/`. Each carries its origin (app `tf`, the repo, `D-012` / `ADR-0003`, the file,
  its last commit, a GitHub link), so pdi shows it next to the decisions of other apps and links back here; the files in
  the repo do not change. Proposals, rejected and superseded rows are not sent; decisions of a change keep
  `decision pending`. Same switches as above (`PDI_EVENTS_URL`, `PDI_TF_SIGNING_SECRET`; `TF_DECISION_PUBLISH=0` turns
  it off). Resending is idempotent; what pdi accepted is kept in `.tf/cache/decision-publish/sent.json`, an unreachable
  pdi is retried next session. `python3 .claude/hooks/decision_publish.py --dry-run` prints what would be sent.
- **A local copy of the suite decisions (D8):** at session start the hook `decision_cache.py` refreshes a read-only
  copy of the pdi index in `.tf/cache/suite-decisions/` (outside git) with `pdi-records changes` — set
  `TF_DECISION_CACHE_CMD` (e.g. `uv run --directory ~/pdi pdi-records`) or `PDI_REGISTRY_PATH`; `TF_DECISION_CACHE=0`
  turns it off. It adds one line to the session context: how many decisions are binding, how many superseded, how old
  the copy is. `decision_cache.py search <words>` searches the copy and the project's own decisions together. Decisions
  of this repo published by the factory are not copied (they are here); a copy edited by hand is fetched again; without
  pdi the last copy stays and is marked stale.
- **The approval is pinned to the artifact version (contract 0.21.0):** `gate request` sends the artifact's SHA-256
  (`artifact_sha256`, the file's bytes) and the commit (`artifact_commit`); pdi refuses an approval when the artifact
  changed after the request, and its `gate.decided` carries the approved hash back. The phase workflow writes it into
  the gate entry (`decision gate --artifact-sha256`, input `artifact_sha256`), and `phase_run.py run` does not start
  the next phase when its input artifact (e.g. `plan.md` for delivery, approved at B3) changed since the approval.
- **Change risk at the gate (DV2, contract 0.20.0):** `phase_run.py gate request` adds `risk` to `gate.requested`
  — the same deterministic score as `tf risk` in the PR description (`level`, the items with file and reason), counted
  without the change artifacts in `docs/project/`; a gate whose branch changed only artifacts goes without it. Advisory:
  every change still passes every gate.
- **An open gate question does not stop the whole delivery (N4, contract 0.19.0):** a question in `## Gate questions`
  may end with markers `[local|broad|one_way; default: <option>; blocks: TSK-n, …]`. Before delivery, an unanswered
  question that is easy to undo (`local`, `broad`) and has a `default` becomes a provisional decision — the loop builds
  with that option and writes `Tymczasowo: …` in the cut's PR, the question stays open in pdi; one with `blocks` stops
  only those cuts; any other unanswered question stops delivery as before. The phase result lists `provisional` and
  `skipped_tasks`; `gate.requested` carries `reversibility` (the strictest) when every question is marked.

- **Security scan on every PR (Z8c-2):** `phase_run.py workflow install --workflow change-check` installs
  `change-check.yml`: the same scan as in the factory's piece loop (`security_scan.py scan` from the tf skill — semgrep
  with the OWASP Top 10 rules and the product's `.semgrep.yml` on the files changed since the PR base, `npm audit` / `pip-audit` when
  a manifest or lockfile changes), and ci_for_sdlc checks the SARIF from `reports/security` (`--sarif`, SEC-001…003) together
  with the change definitions. A scan error (no scanner, an audit that did not run) turns the PR red. In the `delivery` phase
  `sdlc-phase.yml` installs semgrep and pip-audit before the persona, so the factory loop can scan the pieces. The
  `p/owasp-top-ten` rules are fetched from `semgrep.dev` — in the persona's sandbox the host is on the allowlist (Z8a,
  `sandbox_settings.py`) and it works without logging in (a narrower set than after `semgrep login` — the product's own patterns
  in `.semgrep.yml`); in CI without network set the repository variable `TF_SEMGREP_CONFIG` to a rules file in the repo.
  The scan is part of the factory core (the tf skill).

- **Second review before gates B2 and B3 (N1, DZ12):** `second_review.py artifact --change CHG-n --phase P`
  after the `requirements`/`architecture` phase and before the gate request reads the artifact together with the change's decisions and
  (for architecture) `requirements.md` and lists gaps (missing error states, criteria without an example, contradictions
  with a decision, cuts without proof of verifiability, places where an implementer would have to guess) as JSON with a schema and a "Second-model review" section
  in the artifact. Provider: `PDI_SECOND_MODEL` (`openai:<model>` → `OPENAI_API_KEY`, `claude:<model>` →
  `ANTHROPIC_API_KEY`); without `PDI_SECOND_MODEL` or without the provider's key — the fallback
  `claude:claude-sonnet-5-5` marked as a same-vendor review (`same_vendor: true`).
  `phase_run.py gate request` adds the blocking findings (`blocker` and `major`) to the gate questions with the prefix
  `[second review]` (a place to guess: `[would have to guess]`, the question itself), and lists contradictions with decisions with a reference `[contradicts <ref>]`. The second model being
  unavailable shows in the gate request as `second_review: {status: unavailable, reason: …}`. In Actions
  only this step gets `OPENAI_API_KEY` (the key does not reach the persona's container — Z8g). The cost recorded
  in the sidecar (`docs/project/changes/CHG-n/.review/<phase>.json`) counts towards the phase budget (`PDI_PHASE_BUDGET_USD`)
  next to the persona's cost. The second subcommand `comments` checks the reviewer's comments from a PR (N2, A5).

- **PR loop (N2):** after the `delivery` phase in local mode pdi takes every cut PR through rounds:
  an AI review by the product's `REVIEW.md` (`pr_loop.py review`, in the phase container; without the file — the tf template, and
  `pr_loop.py scaffold` adds it to the product) → validation of the comments by the second model (`second_review.py comments`, N1) →
  the `tf` agent fixes only confirmed `critical`/`important` comments and red checks (`pr_loop.py fix`, the CI log as
  quoted data) → a re-review; at most 2 rounds (as DZ6). Unconfirmed comments, those with the second model
  unavailable and those contradicting a change decision go to the human as questions; minor ones (`minor`) — as a list in the PR. **Green**
  = at least one CI check on the PR head and all `pass`/`skipping`; that is why `change-check.yml` has a mandatory
  product verification step (N3, `./verify.sh`). A PR without checks is not green: pdi then runs
  `pr_loop.py verify` in the container and ends with the reason `no_ci_checks`. The PR description gets a completion guide
  section (what is done, what remains, decisions outside the plan, risks), updated after every round. In Actions
  (`sdlc-phase.yml`) there is no loop: a push with the `github.token` token does not run CI on the cut branches.

- **Control bands from ShipScope (F5):** `metric_watch.py check` reads the daily PROD series from the ShipScope service API
  (rollbacks, failed deployments, lead time, number of deployments), computes the `control_band.py` bands and on a point outside 3σ
  in the last days sends pdi `metric.breached` (`--send`). Daily: `metric_watch.py workflow install`
  (`metric-watch.yml`). Needed: the secrets `SHIPSCOPE_TOKEN` (a service token from ShipScope) and `PDI_TF_SIGNING_SECRET`,
  the variables `SHIPSCOPE_URL` and `PDI_EVENTS_URL`; metrics and the baseline in `.claude/pdi-metrics.json`. No model, no
  cost. pdi must accept `metric.breached` from tf (reports, F3) — before that it answers 400.

## Requirement: the pdi MCP server
Recording to the register works only when the session has the `pdi` MCP server (the tools `present_decision_draft`,
`record_decision`, `find_decisions`, `get_decision`) and a human approves each draft in the pdi console (pdi 2026-11-27:
dbqm45/pdi#235, #236; a draft with `supersedes` replaces an earlier decision). The pdi repo describes the installation
(`integrations/claude-code/README.md`; registration `claude mcp add --scope user pdi …`). Without it decisions stay in `decisions.md` with an empty `id` and `sent: no` — nothing is lost.

## What it does not change
The factory core, the project's phase log (`docs/project/0N-*`), other packs and settings — unchanged. A project without
the `docs/project/changes/` directory sees no difference.

## Commands
`decision_record.py change new|check`, `decision add|pending|mark|export|gate`, `phase_run.py prompt|run|gate
request|workflow install`, `metric_watch.py check|workflow install` — full description: the scripts' `--help`.
