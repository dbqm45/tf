# Jev (TypeSafe) in the factory

Jev is a **decision model** ("System One"). It does not write text or code. For a state (text or JSON) and questions it
returns probabilities and a confidence. Question types:
- **noul** — yes/no;
- **choice** — a choice among up to 255 options;
- **score** — a scale of 2–10 levels.

Parameters:
- time: ~0.1–0.5 s;
- price: $0.042 per 1M input tokens, output free;
- window: 64k tokens.

In the factory Jev **does not replace** Claude. It makes fast, cheap and repeatable decisions, and when uncertain
it hands the matter over to an ordinary model or a human.

## Where the factory uses it

Every use is optional and has a fallback: without a key, on a network error or an uncertain answer it works as
without Jev.

| Use | Pattern from the TypeSafe documentation | Enabling | What it improves |
|---|---|---|---|
| Skill hints | cookbook "Skill suggestion" | `CLAUDE_SKILL_HINT_JEV=1` | fewer wrong and unneeded skill loads |
| Verifying `file:line` references in documents | cookbook "Double-checking citations" | `grounding_check.py --jev` | detects references that do not support the sentence (hallucinations) |
| A shield for web content | cookbook "Guardrails for LLMs" | `CLAUDE_JEV_GUARD=1` | warns about instructions hidden in pages (ClickFix, prompt injection) |
| Checking executors' reports | cookbook "SDE cascade" (check → fix) | `CLAUDE_JEV_REPORT_CHECK=1` | an executor will not hand in a report "it works" without evidence or "done" with open points |
| Judging content in evaluations | "Confidence-gated routing" | `run_skill_evals.py --judge jev` | cheaper judging; haiku judges the uncertain cases |
| A model tier suggestion | "Composite scoring" | `jev_client.py --tier "<description>"` | a consistent assessment of task difficulty (the core-cost-control rubric) |

Details of how it works:
- **Skill hints.** Stage 1 is a choice among all skills plus 3 gate questions (design work? a specialised procedure?
  is a short answer enough?). Stage 2 is a choice among the best 3 with the full description and the start of SKILL.md,
  plus a "does it fit" question for each. The thresholds are 0.30 as in the cookbook. In the cookbook
  (182 skills, an agent on Haiku 4.5) there were 2.3 times fewer wrong loads.
- **Verifying references.** The verdict is "supports", "contradicts" or "says nothing". A confidence ≥0.8 gives an
  automatic verdict, a lower one means a review by a human.
- **The web content shield.** "strict" thresholds: from 0.35 a note, from 0.70 a warning.
- **Checking reports.** One request for a fix; after that the hook does not block (no loop).
- **The tier suggestion.** 5 noul questions, and code makes the decision. "UNCERTAIN" means the model decides.

## Configuration

Environment variables (the same names as in the official SDK). **Never** write the key in the repository's files.

```bash
export TYPESAFE_API_KEY=...                    # from console.typesafe.ai
# optional: TYPESAFE_BASE_URL (default https://api.typesafe.ai), TYPESAFE_DEFAULT_MODEL (default jev-latest)
python3 .claude/hooks/jev_client.py --check    # one cheap request: do the key and the service work
```

## Measure first, then enable

The TypeSafe documentation says English works best and other languages less well. The factory asks its questions in
English, and the state (prompts, documents) is in English or in the human's language. So before enabling it, measure
Jev on the factory's data:

```bash
python3 .tf/factory/jev_calibration.py --routing                                   # keywords vs Jev
python3 .tf/factory/jev_calibration.py --judge docs/evals/2026-10-02-sonnet.jsonl  # agreement of judgements
```

You can measure skill hints on all ~270 scenarios for a fraction of a cent. Enable:
- `CLAUDE_SKILL_HINT_JEV=1` when Jev has fewer wrong and unneeded hints than the keywords at a similar number of
  correct ones;
- `--judge jev` when the agreement of confident judgements is ≥95%.

Enable the guards (`CLAUDE_JEV_GUARD`, `CLAUDE_JEV_REPORT_CHECK`) for a few days and review their warnings:
- whether the report blocks were justified;
- whether the page warnings concerned suspicious content.

Jev usage goes to `.tf/logs/jev.jsonl` (without the content of the queries).

## Limitations

According to the "model jaggedness" documentation for jev-1.13, Jev:
- reads instructions literally;
- does not count reliably;
- compares dates badly;
- loses accuracy with a large state with irrelevant content;
- does not treat the state as hostile (instructions in the content can affect the result).

The factory:
- asks one question about one condition, and a high value always means "yes";
- sends only the fields needed for the decision;
- counts in code;
- treats the guards as an additional layer, not the only protection.

Privacy:
- the state goes to the TypeSafe service;
- the client strips known secret patterns, but do not send through it data that must not leave the company;
- zero data retention is available to enterprise customers.

Availability: the service launched on 15.09.2026, and sign-up in the console is sometimes paused. Limits: 100k tokens
and 80 requests per second ("may change without notice").

**Beware of fakes.** The domain jevtypesafeai.com and its "skill" do not belong to TypeSafe. The official skill for
agents (needed when **your project** is to use Jev in the application's code) you install with the commands:
`claude plugin marketplace add typesafe-ai/skills`, then `claude plugin install typesafe@typesafe-ai`.

## Sources (accessed 2026-10-03)
- docs.typesafe.ai: `introduction`, `models`, `api`, `confidence`, `concepts/state`, `introduction/coding-agents`,
  `model-jaggedness/jev-1.13`, `primitives/noul`, `patterns/confidence-routing`, `agent-skill`,
  `sdk/python/api/constants`.
- TypeSafe cookbooks: `skill_suggestion`, `citation_check`, `llm_guardrails`, `sde_cascade`,
  `consistency_noul_cookbook`, `parallel_questions`.

Described in our own words.
