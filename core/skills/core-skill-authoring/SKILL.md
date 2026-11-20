---
name: core-skill-authoring
description: Use when adding, changing, reviewing or slimming a factory skill, or when a skill does not trigger - find the gap, scenarios first, then content and skill_gate.
metadata:
  review: "2027-11-20"
  catalog: "Use when a skill is added to the factory or a project, changed, reviewed before adoption, slimmed down, made to run unattended (CI, claude -p) or shared across repositories, and when you must prove that it helps: a trial without the skill, scenarios before content (trigger, no-trigger against a neighbour, held-out), minimal content with examples and scripts, a description that works as a selection rule, the free skill_gate and the paid model evaluation with consent. Not for combining several existing skills in one task (core-skill-composition), writing CLAUDE.md rules (core-agent-instructions) or testing application code (the testing skills of a pack)."
  keywords: "nowy skill, dodać skill, napisać skill, skill do fabryki, jak napisać skill, skill się nie uruchamia, model nie wczytuje skilla, skill nie działa, opis skilla, description skilla, słowa kluczowe skilla, scenariusze ewaluacji, ewaluacja skilla, skill_gate, run_skill_evals, baseline bez skilla, holdout, przeuczenie na scenariuszach, odchudzić skill, za długi SKILL.md, 900 linii, references, przykład w skillu, skrypt w skillu, skill w CI, skill bez człowieka, disable-model-invocation, widoczność skilla, sama nazwa, rzadko używany skill, lista skilli się przepełnia, przegląd skilla, obcy skill, udostępnić skille między repo, skill od wzorcowego wyniku, płaski generyczny wynik, write a skill, new skill, skill does not trigger, skill evaluation, eval scenarios, skill gate, held-out scenarios, slim down skills, skill review, unattended skill, share skills across repositories"
---

# Writing and changing skills - evidence first

A skill is finished when three things are measured: it loads for the questions it is meant for, it stays out of a
neighbour's questions, and the answer with it is better than without it. Well-written text proves none of this.
Work in this order: gap -> scenarios -> content -> gate -> (with consent) model evaluation.

## 1. Is there a gap at all
- Check what already covers the area: a built-in skill (e.g. the Claude API reference skill), an installed plugin,
  an existing factory skill. If one does, write only the project-specific agreements, as a short skill or a CLAUDE.md line.
- Run 2-3 realistic tasks **without** the new skill and note what was missing: knowledge, steps, output format,
  boundaries. Nothing missing -> no skill. The notes become your first scenarios.
- Skill that produces a document or other artifact (PRD, ADR, report): start from the best real output you have, not from a
  list of steps. Write down the decisions in it that a generic template would not make (section order for this reader,
  uneven depth, what was left out and why) and 2-3 questions the author must answer before writing ("who reads it and what do
  they decide?", "what must be true for this to be accepted?"). A bare step list produces flat, generic results.

## 2. Scenarios before content
Create `tests/skill_evals/<name>.json` (in a project: `.claude/tests/skill_evals/`; format in `tests/skill_evals/README.md`):
- **2+ `trigger` scenarios** written in the words a user would type, not in the description's words. Each has at least two
  `checks.all` groups for knowledge the model lacks without the skill, and a `checks.none` regex for the typical wrong answer.
- **1+ `no-trigger` scenario** with `neighbor` set to the skill that should answer instead (or `brak`).
- **An edge case** (id starting `edge-`) when the skill processes input: missing file, empty input, contradiction. Expected:
  the answer asks or says what is missing; `none` catches an invented answer.
- Rules the gate enforces: `skill` equals the file stem, at least 3 scenarios, unique ids, prompts of 15+ characters, no
  literal `TODO`.
- Optional paid baseline, `run_skill_evals.py --skills <name> --models sonnet --baseline` (`--per-skill N` to limit): a
  scenario that passes without the skill does not measure the skill - rewrite it.
- **Held-out set** `tests/skill_evals/holdout/<skill>.json` (trigger scenarios with checks): it measures, it never tunes.
  The author does not read it. Accept a change when the tuning scenarios improve and the held-out result does not get worse.
  A big gap between the two (95% on your own scenarios, much less on held-out) means the skill was fitted to the exam.

## 3. Content
- **One skill, one task.** If the description lists several independent jobs, split the skill.
- **Procedure, not lecture.** Write only what the model would not do by default; every sentence should change behaviour.
- **Examples beat rules.** Include an `## Example` with concrete names, numbers and output; more cases go to a
  separate examples file under references.
- **Deterministic work goes to `scripts/`** (sorting, parsing, counting, validating). Say whether the model runs or reads the
  script; handle errors inside it; no unexplained constants; a script that opens connections needs a line in SKILL.md
  starting `Network:` (or `Sieć:`) saying where it connects - otherwise the audit blocks the gate.
- **A script whose numbers agents copy into reports** is written test-first (a failing test first, then code) and checked on a real
  repository against a reference computed independently (by hand or another tool) before SKILL.md mentions it. Agents
  rarely re-verify a script's output, so one wrong count propagates into every report built on it.
- **Separate criteria from mechanics.** "What a good result is" (tool-agnostic, reusable by CI and humans) lives apart from
  "how this flow runs". When output is checked by a script, fix the first line and the field names.
- **Size.** In this repository SKILL.md stays at 15000 characters / about 300 lines (vendor guidance: under 500 lines; after
  compaction Claude Code re-attaches only the first 5000 tokens of each invoked skill). Detail goes to `references/`, one level
  from SKILL.md; a reference over 100 lines starts with a table of contents. One term per concept, forward-slash paths, other
  skills named by name. External facts carry a source and date (core-grounding) in a `## Sources` section with
  `accessed YYYY-MM-DD` lines.
- Content is English; the model answers in the user's language.

## 4. Description and discovery
- `description`: a third-person selection rule starting "Use when ...", at most 170 characters, no `: ` inside (it breaks
  YAML). It is the only text the model sees at session start, so it names the situation, not the topic.
- `metadata.catalog`: the full text, ending with boundaries "Not for X (skill-a), Y (skill-b)".
- `metadata.keywords`: Polish and English, in users' own words (symptoms, error messages). The `skill_hint` hook indexes them;
  Polish questions also reach English skills through `hint.pl.txt` (regenerate with `python3 tools/hint_pl_index.py <skill>`).
- `metadata.review`: a quoted date for the next content review (`python3 .tf/factory/freshness.py --reviewed <name>`).
- Leave out `paths` (the skill is invisible until a matching file is opened, which shows up as "Unknown skill"),
  `when_to_use` (it shares the description's listing budget) and `model`/`effort` (switching model mid-session invalidates the
  prompt cache; choose cost in core-cost-control instead).
- `context: fork` only for a skill that reads a lot, returns a short result, never asks the human and runs in long sessions. It
  needs `background: false`, `argument-hint`, a task line with `$ARGUMENTS`, a refusal for an empty task and a short result
  format. Factory measurement 2026-11-16 (`docs/evals/2026-11-16-context-fork.md`): main context -37%, cost +33%, same
  quality - a fork buys room, not savings.
- Rarely needed skill: `metadata.visibility: name` - only the name is listed, the hook still suggests it when a question fits.
- Manual-only skill: `disable-model-invocation: true`; its scenario file holds only `no-trigger` scenarios.
- Skill with no measured advantage: disable, do not delete - `metadata.status: "inactive"`, `disable-model-invocation: true`,
  trigger scenarios moved to `tests/skill_evals/inactive/<skill>.json`, reason in `docs/inactive-skills.md`. `build.py` then
  drops it from roles, personas and the catalog; fix the references `build.py check` lists.

## 5. Skills that run without a human (CI, `claude -p`, schedules)
- Invoked explicitly (`disable-model-invocation: true`, called by name), never picked up by chance.
- **Input precondition**: name the input file; if it is missing, answer with one sentence that names the skill producing it,
  and stop.
- Check before, during and after the work, and write a status line for each phase. Stop hard only when there is no basis to
  continue.
- No questions: take the conservative option and log it in the output.
- Do not chain into the next skill automatically; name the next step.
- Existing output: decide up front - overwrite, versioned copy, or abort.
- Print a verdict line (e.g. `Verdict: PASS | FAIL`) first or last: the evaluator sees only the transcript.
- Scenarios test the contract edges: missing input, write collision, empty result.

## 6. Gate, wiring, model evaluation
- Scaffold: `python3 .tf/factory/build.py new-skill <prefix-name> "<full description>"` (`--role <role>`, `--name-only`). The
  name matches the directory and starts with a facet prefix from `.tf/config/config.yaml -> facets`.
- Wire it in: add to a role in `.tf/config/roles/*.yaml` or a persona, then run `python3 .tf/factory/build.py`.
- **Free and mandatory**: `python3 .tf/factory/skill_gate.py <name>` (structure, scenarios, hint, language, references,
  audit). Also `--changed`, `--status`, `--fast`, `--suggest <skill>`. A foreign skill first goes through
  `python3 .tf/factory/skill_audit.py <dir>`.
- **Paid, with the human's consent** (about $0.10-0.30 per scenario per model): `skill_gate.py <name> --model haiku,sonnet
  --budget 2`. Haiku shows whether the content is sufficient, Sonnet whether it is concise; Opus only for deep-tier skills.
  Every scenario must pass; record result and cost in the CHANGELOG. Reports go to `docs/evals/` (project: `.tf/logs/evals/`).

## 7. Changing and slimming an existing skill
- Change: add a scenario that reproduces the problem, confirm it fails, fix, run the gate (plus model evaluation for
  substantive changes). The `skill_change_guard` hook reminds you after edits and at session end.
- Tidying never deletes knowledge: move it to `references/` and link it.
- Slimming a long skill (e.g. 900 lines): test every sentence - "does it change default behaviour?"; drop no-op sentences;
  turn bans into positive instructions; name a concept the model knows instead of explaining it; move details one level down
  with a table of contents; keep the examples. Factory measurement 2026-10-30: two pack-it skills lost 5-12% of words with no
  drop in results. Every cut goes through the scenarios and the gate.
- All visible skills' descriptions are a fixed cost on every request. Make rarely auto-invoked skills name-only or manual
  only - decided from hint-hit data, not intuition.
- Specifications do not quote project file paths or code: they age faster than the skill.
- Review of a skill (own or foreign): checklist in `references/skill-review.md`. Sharing skills across repositories:
  `references/team-distribution.md`.

## Diagnosis
| Symptom | Fix |
|---|---|
| Hook does not suggest the skill | Keywords and description in users' words; `skill_hint.py --explain "<question>"`, `skill_gate.py --suggest <skill>` |
| Hook suggests, model ignores it | Description names the specific gap the skill fills |
| Fires on other skills' questions | Narrower description, "Not for" boundaries in catalog, a `no-trigger` scenario |
| "Unknown skill" | Remove `paths` |
| Loaded but answer still wrong | More specific steps and an example; an edge scenario |
| Gate: no "when" wording | Rewrite the description as a "Use when ..." rule |

## Example
Request: "I want a skill for writing release notes." Not the first move: drafting SKILL.md.

```
1. Trial: 3 recent releases written without the skill -> missing: grouping by user impact, migration notes,
   links to issues. Gap confirmed.
2. tests/skill_evals/eng-release-notes.json:
   - trigger "notes-from-tags": "Write release notes for v2.4 from the merged PRs"
       all: [["breaking|migration"], ["user impact|for users"]]   none: ["commit list as is"]
   - trigger "notes-hotfix": "Hotfix 2.4.1 is out, what do we tell customers?"
   - no-trigger "commit-message", neighbor core-conventional-commits
   - edge "edge-no-tag": "Release notes please" (no tag, no range) -> asks for the range
3. SKILL.md: 60 lines, one worked example, a PR-collecting script with a Network: line.
4. python3 .tf/factory/skill_gate.py eng-release-notes -> pass; model evaluation after consent.
```

## Sources
- Anthropic, "Skill authoring best practices", platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices - accessed 2026-11-20 (concise content, under 500 lines, progressive disclosure, evaluations first).
- Claude Code docs, "Skills", code.claude.com/docs/en/skills - accessed 2026-11-20 (front-matter fields, `paths`, `when_to_use`, `context: fork`, 5000-token re-attachment after compaction).
- Claude Code docs, "Prompt caching", code.claude.com/docs/en/prompt-caching - accessed 2026-11-20 (model change invalidates the cache).
- Anthropic, "Define success criteria and build evaluations", platform.claude.com/docs/en/test-and-evaluate/develop-tests - accessed 2026-11-20 (edge cases in test sets).
- Claude Code docs, "Run Claude Code programmatically", code.claude.com/docs/en/headless - accessed 2026-11-20 (unattended runs).
- Factory measurements: `docs/evals/2026-11-16-context-fork.md`; slimming measurement 2026-10-30 (pack-it).
