---
name: core-skill-authoring
description: Use when adding or changing a skill — evaluation scenarios first, then concise content with examples, the gate, the audit.
metadata:
  review: "2027-10-09"
  catalog: "Use when you add a new skill to the factory, change an existing one, a skill does not trigger or you have to prove that a skill adds something — the order of work from evaluation scenarios, a baseline without the skill, description and structure rules, the quality gate .tf/factory/skill_gate.py, evaluation on models and the results register. Not for combining existing skills in one task (core-skill-composition) or tests of the application's code (the testing skill, pack-it)."
  keywords: "nowy skill, dodaj skill, napisz skill, zmień skill, skill się nie uruchamia, model nie wczytuje skilla, ewaluacja skilla, scenariusze, bramka jakości, skill_gate, czy skill działa, baseline, skill procesowy, skill w CI, skill bez człowieka, claude -p, jak działa ten skill, przegląd skilla, dystrybucja skilli w zespole, paczka ze skillami, dodać skill do fabryki, nowy skill w fabryce, od czego zacząć nowy skill, sprawdzić, że skill naprawdę działa, zanim oddam skill, skill procesowy, skill działający w CI, skill dla claude -p, zaprojektować skill przewidywalny, skrypt w scripts/ skilla, wpiąć skrypt do SKILL.md, skrypt liczy metryki dla agentów, liczby ze skryptu do raportów, widoczność skilla, skille widoczne w każdej sesji, odchudzić skille, za długie skille, new skill, write a skill, change a skill, the skill does not trigger, the model does not load the skill, skill evaluation, quality gate, does the skill work, process skill, skill in CI, review a skill, distribute skills in a team, slim down skills, skills too long"
---

# Adding and changing a skill — evidence first, content after

A skill is ready only when it has been measured that:
- the model loads it for the right question and does not load it for someone else's;
- the answer with it is better than without it.

The content of SKILL.md alone proves nothing.

## Procedure
1. **The gap.** First check whether the area is not covered by a skill built into Claude Code (e.g. `claude-api` — a reference
   for the Claude API and SDK, updated by Anthropic) or an installed plugin: then you write at most the project's agreements
   and point to it. Then give the model 2–3 real tasks from the skill's area **without the skill**. Write down
   what is missing: knowledge, steps, the format or boundaries. If the model copes well, the skill is not needed.
   **A skill that creates an artifact** (a PRD, a report, a plan) you start from the best existing result, not from a list
   of steps: you list the decisions a general template does not know (the order of sections for the reader, uneven depth,
   constraints stated outright), and 2–3 questions the skill asks before writing. That becomes the content and the scenarios.
2. **The skeleton.** `python3 .tf/factory/build.py new-skill <prefiks-nazwa> "<pełny opis z granicami>"` creates SKILL.md
   with a review date and a `keywords` field and a skeleton of scenarios `tests/skill_evals/<nazwa>.json` (in a project:
   `.claude/tests/skill_evals/`). `--role <rola>` adds the skill to a role, `--name-only` sets `visibility: name`.
   Choose the prefix from the dimensions in `.tf/config/config.yaml → facets`.
3. **Scenarios before content** (≥3):
   - **2× `trigger`** — questions from the gap in step 1, asked in a human's words, not the skill description's. Plus `checks.all`:
     ≥2 groups of expressions checking knowledge the model does not have without the skill; `none` for a typical error.
   - **1× `no-trigger`** with a `neighbor` field — a borderline question that belongs to a neighbouring skill. It guards the boundaries.
   - **1× edge case** (`trigger`, id `edge-…`), when the skill processes input data: missing, too long or
     ambiguous data. Expected is a question or "I don't know" with what is missing — `checks.none` catches
     a made-up answer (platform.claude.com, "Define success criteria and build evaluations", 2026-10-20).
   - The format and examples: `tests/skill_evals/README.md`.
4. **A baseline (optional, paid):** `run_skill_evals.py --skills <nazwa> --models sonnet --baseline`
   shows how much of the content the model passes without the factory's skills.
   - **The held-out set** (`tests/skill_evals/holdout/<skill>.json`) measures, it does not tune: its failures do not lead to
     changes of the description, keywords or content for those questions. Otherwise the result measures fit to the exam, not the skill.
     The author of the change (a human or an agent) does not read the holdout files. You accept a change when it improves the tuning set
     and does not worsen the holdout; a big "tuning − holdout" gap in the report (`--per-skill N`) you treat as a signal
     of learning the exam.
5. **Minimal content** that closes the gaps:
   - **one skill, one task** — a description listing several independent tasks is a signal to split it;
   - a procedure (steps, order, decision points, the output format), not a lecture; assume the model is smart —
     write only what it does not know;
   - **examples matter more than rules:** an `## Example` section (input → result, specific names and numbers),
     further ones in `<skill>/references/examples.md`;
   - **code where it fits:** sorting, parsing, counting, validation → a script in `scripts/` (deterministic,
     cheaper, its content takes no context); write whether to run the script or read it; it handles errors itself,
     without "magic" constants; a network connection you declare with the line "Network: …" in SKILL.md; a script agents
     take numbers from is written with TDD and before being wired into SKILL.md is checked on a real repo against
     a reference counted independently — the agent usually does not verify its result, so a script error goes into every report;
   - SKILL.md up to ~300 lines (Anthropic: below 500), part of the rules fits on a phone screen; details
     in `references/` — **one level from SKILL.md** (every file named in SKILL.md, a file from another skill by its full
     path `.claude/skills/<skill>/…`), a table of contents in files longer than 100 lines;
   - one term for one concept across the whole skill; paths with a slash `/`;
   - refer to other skills by name, do not copy their content;
   - external facts with a source and a date (core-grounding), at the end a **Sources** section.
   - **separate criteria from mechanics:** the knowledge "how to assess / what is good" in `references/` without assumptions about the tool
     and the environment; SKILL.md carries the flow (where the data comes from, where the result goes) and points to the criteria — the same criteria
     will serve in CI, in another AI tool and as a checklist for a human;
   - **a machine-checkable output contract:** a fixed marker in the first line and fixed fields (e.g. `Verdict: …`),
     so the next step checks them with a script instead of assuming the model kept to the format.
6. **Description and search:**
   - You write the skill's content (description, catalog, instructions, references) **in English**; the model answers the human in their
     language. The gate recognises the content's language itself (step 5: Polish content goes through the Polish linter).
   - `description` ≤170 characters as **a selection rule**: "Use when/for <situation> — <key concepts>.", without ": "
     (it breaks YAML). Only this is what the model sees at the start; Claude Code skips the `metadata` field. Not "Helps with documents".
   - `metadata.catalog`: the full description with boundaries ("Not for … (skill)"; the old "Nie do …" works too).
   - `metadata.keywords`: the words people describe the problem with — **in Polish and in English** (phrases from questions, not
     from the skill's content). The `skill_hint` hook indexes them without a model: a Polish question hits an English skill through
     the Polish keywords, and for a skill translated from Polish also through `hint.pl.txt` (the old Polish text,
     `python3 tools/hint_pl_index.py <skill>` in the factory repo after translating); the gate (step 3) and the holdout scenarios show what is missing.
   - You do not use the `paths` field: with it the skill loads automatically only for matching files, and a design
     question usually comes before the files exist. `when_to_use` is appended to the description in the skill list and eats
     the description budget — you write the boundaries in `metadata.catalog`.
   - No `model` or `effort` in the skill's header: a model other than the session's is a model change in a turn — the next
     request reads the whole history without cache (code.claude.com, "Skills" and "Prompt caching", 2026-10-20).
   - `context: fork` (the skill works in a separate subagent, the result comes back to the conversation) only for a skill that reads a lot,
     returns a short result and does not ask the human along the way — and the session after it lasts long or is close to the context limit.
     A measurement of 2026-11-16 (`eng-codebase-mapping` from pack-it): the main session's context −37%, the cost +33%, quality unchanged — a fork
     does not save money, it gives room in the context (`docs/evals/2026-11-16-context-fork.md`). Conditions:
     `background: false` (otherwise the result arrives in the background), at the top of the content `**Zadanie:** $ARGUMENTS` with the rule "an empty
     task → answer BRAK ZADANIA" (the subagent does not see the conversation, and the model calls the skill without `args`), `argument-hint`
     and the format of a short result. A skill with an "agree with the human" step will not work in a fork.
   - A rarely needed skill: `metadata.visibility: name` — only the name in the list (it takes no description budget),
     and the `skill_hint` hook suggests it with its description for a matching instruction (`.tf/factory/skill_profile.py`).
   - A skill run only by hand: `disable-model-invocation: true` and only `no-trigger` scenarios.
   - A skill without an advantage in measurement (the model without the skill answers the same): disable it, do not delete it —
     `disable-model-invocation: true` and `metadata.status: "inactive"`; move the `trigger` scenarios to
     `tests/skill_evals/inactive/<skill>.json`. `build.py` then removes the skill from roles, personas and the catalog. Remove references to it
     in other skills (`build.py check` lists them). Write the reason and the results in `docs/inactive-skills.md`
     of the factory repository.
   - `metadata.review`: the content review date (YYYY-MM-DD). It is set by `python3 .tf/factory/freshness.py --reviewed
     <nazwa>` after checking the facts in the sources (today + an interval: versions 3 months, regulations 3–6, methods 12).
7. **Wiring in:** add the skill to a role (`.tf/config/roles/*.yaml`) or a persona and run `python3 .tf/factory/build.py`.
8. **The quality gate** (free, mandatory): `python3 .tf/factory/skill_gate.py <nazwa>`. It checks:
   - the structure;
   - the scenarios;
   - whether the hook suggests the skill for its questions, and does not put it first for a neighbour's question;
   - **a hint regression of all skills** (a new skill must not steal other skills' questions);
   - the content language;
   - references;
   - **the audit** (`.tf/factory/skill_audit.py`): security and Anthropic's recommendations (a selection rule in the description, examples,
     existing files, a network declaration) — high and medium severity block the gate.

   The result and the content fingerprint go to the register. `build.py check` warns when a skill was changed after the gate.
9. **Evaluation on a model** (paid, **with the human's consent**, ~$0.10–0.30 per scenario and model):
   `python3 .tf/factory/skill_gate.py <nazwa> --model haiku,sonnet --budget 2`.
   - All scenarios must pass. Haiku checks whether the instructions are enough for a weaker model, and Sonnet
     whether they are concise.
   - Add `opus` for skills used by agents on the deep tier.
   - The report goes to `docs/evals/` (in a project `.tf/logs/evals/`).
10. **Record:** a CHANGELOG entry (what, the result of the gate and the evaluation with the cost).

## Process skills and skills for work without a human
- **Two types:** a process skill (called explicitly, reads a file → writes a file, `disable-model-invocation: true`) and an advisory one
  (loaded by its description, without an artifact). Design important steps as process skills — automatic loading is a help, not a guarantee.
- **A precondition:** the skill checks whether the input file exists on disk; missing → a refusal in one sentence with the name of the
  skill that creates it. The conversation does not replace the file.
- **Three gates:** before (the input file, a clean tree, green tests), during (permissions), after (a report on disk
  with the status of each phase: passed / warned / failed / skipped). A hard stop only when there is no basis for further work;
  for the rest warn and continue, leave the decision to the human.
- **No chaining:** the skill ends with the write and gives the name of the next step, it does not run it itself. An existing output file
  → a question: overwrite / save as `-vN` / abort.
- **Internal labels stay internal:** you do not show the human the step numbers and field names of the skill.
- **Work without a human** (CI, `claude -p`): no questions to the user; ambiguity → the conservative option
  (fewer files, a smaller change of behaviour, closest to the letter of the plan) written in the report; every gate prints a verdict
  line, because the evaluator sees only the transcript.
- Design evaluations for the boundaries of the contract and edge cases (a missing file, a write collision), not only for the happy path.
- Analysing someone else's or your own skill ("how does it work, how to make a similar one"): `references/skill-review.md`.
  Sharing skills with several repositories and tools: `references/team-distribution.md`.

## Changing an existing skill
- The same cycle in short:
  1. add a scenario that reproduces the problem;
  2. check that it **does not pass** (`run_skill_evals.py --skills <nazwa>` or step 3 of the gate);
  3. fix the content;
  4. the gate, and for a change of substantive content also an evaluation on a model.
- **You do not remove knowledge when tidying up.** You move it to `references/` and leave a link.
- Fewer tokens (a "no-op" test sentence by sentence, positive instructions, concepts by name, the cost of all skills'
  descriptions): `references/skill-review.md` §"Slimming down".
- The `skill_change_guard` hook reminds about the gate after every edit of a skill, and at the end of the session lists skills without
  a passed gate.

## Diagnosis: the skill does not trigger
| Symptom | Cause | Fix |
|---|---|---|
| gate step 3: the hook does not suggest it | the user's words ≠ the description's words | `metadata.keywords`, the description closer to the language of the questions; `skill_hint.py --explain "<pytanie>"`; a phrase proposal: `skill_gate.py --suggest <skill>` |
| the hook suggests it, the model ignores it | a general topic, the model "knows by itself" | in the description a specific gap ("the procedure…", "version pitfalls…"), a scenario with that gap |
| the skill triggers on other people's questions | the description is too broad | boundaries in `metadata.catalog`, a `no-trigger` with a neighbour, a narrowed description |
| "Unknown skill" | the `paths` field | remove `paths` |
| the content does not pass, although the skill loaded | the instruction is too general or too long | specific steps and examples; details to `references/` |
| the model does not reach for the skill despite the hint | a slogan description without "when" | the description as a selection rule "Use when …" |

## Checklist
- [ ] the gap measured without the skill; scenarios (2× trigger, 1× no-trigger with a neighbour) written before the content
- [ ] content in English, the description as a selection rule "Use when/for …" (≤170 characters), the catalog with boundaries, `metadata.keywords` PL+EN, no `paths`
- [ ] one task; an `## Example` section; scripts for deterministic operations; the network declared
- [ ] SKILL.md concise, `references/` one level from SKILL.md with a table of contents, sources with a date, `metadata.review`
- [ ] a process skill: an input file precondition, a report with phase statuses, no chaining; in CI no questions, with a verdict line
- [ ] `python3 .tf/factory/skill_gate.py <nazwa>` passes (also the regression of all skills)
- [ ] the evaluation on haiku and sonnet passed (with the human's consent), the result and the cost in CHANGELOG

## Sources
- Anthropic: "Skill authoring best practices" (platform.claude.com, as of 2026-10-03):
  - evaluations before documentation;
  - a baseline without the skill;
  - minimal instructions;
  - a test on Haiku, Sonnet and Opus;
  - content below 500 lines;
  - observing how the model uses the skill.
  - a description in the third person with "what" and "when", references one level from SKILL.md, a table of contents above 100 lines,
    scripts instead of generated code, examples instead of abstractions (as of 2026-10-04).
- Anthropic: "Agent Skills — overview", the "Security considerations" section (trusted sources, auditing all files,
  the risk of external addresses) and Claude Code "Skills" (the list of descriptions in 1% of the context window, `allowed-tools` without a trust
  gate, commands inserted into the content and executed on loading), accessed 2026-10-04.
- The factory's evaluation results (`docs/evals/2026-10-02-*`): without a hint models rarely load skills, and the `paths` field
  hides the skill.

- The 10xDevs course, ed. 3 (2026), module 1, lesson 2 (skill types, activation), module 5, lessons 3–4 (a skill in CI,
  distributing AI artifacts in a team) — training material (accessed 2026-10-09).

Described in our own words.
