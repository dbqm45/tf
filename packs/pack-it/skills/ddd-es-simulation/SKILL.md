---
name: ddd-es-simulation
description: Use only on explicit request — a simulated Event Storming workshop with AI participants and a coach (facilitation training).
metadata:
  review: "2027-10-17"
  catalog: "Use ONLY on the user's explicit request (\"simulated workshop\", \"Event Storming facilitation training\") — a simulation of a Big Picture session with participants played by AI and a coach assessing the facilitation; a full or lean version, always chosen by the human after a cost warning. Not for real domain analysis (ddd-event-storming, ddd-discovery-intake)."
disable-model-invocation: true
argument-hint: "[pelna|oszczedna] [scenario]"
---

# Simulated Event Storming workshop (facilitator training)

> **Only on the human's command** (`/ddd-es-simulation`). If you are reading this file for another reason (e.g. looking for information), do not carry out the steps — you can quote what the skill does and propose running it with the command.

The human practises **facilitating** a Big Picture session with simulated participants; the coach assesses the facilitation, not the substance.
This is training — the results are never knowledge about a real domain (they do not go into `docs/project/`, the evidence bank or the model).

## 0. Cost gate — always, before you run anything
Do not start without the **human's explicit choice**, also when the version was given in the argument (then only confirm it with a warning).
Ask the question (`AskUserQuestion`, without a default option) with this table:

| | **Full** (as in the original) | **Lean** |
|---|---|---|
| Who speaks in a round | the whole room: each participant is a separate agent in a separate context, in parallel | 3–4 people chosen by the script (addressed by name, matching the topic, silent the longest); "everyone" = the whole room |
| Participants' model | `es-participant` — std (Sonnet), the full persona card | `es-room` — fast (Haiku), one agent plays several people from short cards |
| Independence of the people | full (separate contexts) | partial (one context plays several roles) |
| Coach | full: 10 anti-patterns | light: 3 key ones (dominance, silence, language); full on request |
| **Cost in this conversation** (host = the current persona, Sonnet) | **about $0.30 per round → $3–4 per session of 10–12 rounds** | **about $0.20 per round → about $2–2.50 per session** |
| **Cost in a separate session `claude --agent es-host`** (host on Haiku) | estimate about $0.12–0.18 per round | estimate about $0.05–0.10 per round — the cheapest option |

Most of the cost is the **host**, not the participants: in the current conversation every round re-reads the persona's large context on Sonnet.
That is why you always also propose a separate session `claude --agent es-host` (a small prompt, Haiku). The cost grows with the length of the session.
Answer options: "Full — I accept the cost" · "Lean" · "Lean in a separate es-host session (cheapest)" · "I give up".
No answer / work without a human → **do not start**.

## 1. Roles
- **The human = the facilitator.** Writes what they would say in the room (questions, requests, parking, marking pivotal events).
- **You = the scribe and orchestrator.** You never play any person and never add stickies on behalf of participants. You do not prompt the facilitator,
  unless they ask for the coach.
- **Participants** — `es-participant` / `es-room` agents; they see only their own round prompts (hook `cleanroom_guard.py`, profile `es-sim`
  — they will not read `brief.md`, other people's cards or the project files).
- **Coach** — the `es-coach` agent, only on request ("coach", "how am I doing?", end of the session).

## 2. Flow (everything mechanical is done by the script — zero tokens)
Script: `python3 .claude/skills/ddd-es-simulation/scripts/es_sim.py` (session directory `docs/training/es-sim/<id>/`).
1. **Start:** `es_sim.py init --variant pelna|oszczedna [--scenario veterinary]` → session id, the present, the absent (they join on invitation).
   The script prints a ready introduction (domain, the present, commands) after the marker `=== POKAŻ DOSŁOWNIE ===` ("show verbatim") — show it unchanged.
   **Do not read `brief.md` or the persona cards** — they contain hidden knowledge and deliberate contradictions; only the coach reads them.
2. **Round** (every utterance of the facilitator):
   - `es_sim.py round-begin --id <id> --text "<utterance>"` → JSON with a list of calls (`agent`, `prompt_file`).
   - **Full:** call `es-participant` for EACH entry **in parallel, in one message**; the agent's prompt = only
     "Carry out the instructions from the file <prompt_file>." (do not paste the content — it saves tokens).
   - **Lean:** one `es-room` call with the same short command.
   - `es_sim.py round-end --id <id>` → the utterances, the new stickies and a meta line (added / rejected / silent).
     **Your answer = exactly the text after `=== POKAŻ DOSŁOWNIE ===`**, nothing more: no summaries, no "Your move", no hints,
     no references to the scenario. Hints spoil the training (the facilitator is to notice the contradiction and the silent participant on their own)
     and cost tokens. Hints are given only by the coach — on request.
3. `invite <name>` / `zaproś <imię>` → `es_sim.py invite --id <id> --persona <id>`. `pivotal ev_012` / `przełomowe ev_012` → `es_sim.py pivotal …`. `board` / `tablica` → `es_sim.py board`.
4. **Coach:** `es_sim.py stats --id <id> --json` → call `es-coach` with: the transcript path, the stats output, the path of `brief.md`,
   the mode (`light` by default in the lean version, `full` in the full version or on request; `midsession` = 5–7 sentences during the session).
   The coach writes the debrief to `docs/training/es-sim/<id>/debrief.md`.
5. **End:** the coach (final mode) + a summary: the number of rounds, the board, the cost (`python3 .tf/factory/cost_report.py --days 1`, if it exists).

## 3. Simulation mechanics (script + persona cards)
- **Persona card** (`scenarios/<s>/personas/<id>.md`): character · knowledge (knows well / superficially / **does not know**) · pains · event
  anchors · "stimulus → reaction" behaviours · metaprograms · 8 variants of the day · anecdotes (each one once) · voice (not to be quoted) ·
  short card (≤ 500 characters, the lean version). Each person **trains one facilitation anti-pattern**.
- **Variant of the day** — deterministic from the session id: it changes the temperament, not the knowledge; every session is a little different.
- **Memory** — the last 5 one-sentence summaries **in the person's own words** (not verbatim quotes, so that they do not repeat them).
- **Room echo** — 3 utterances of others from the previous round (a reaction delayed by one round — the coach takes this into account).
- **Stickies:** only `event` and `hot_spot`; the script rejects and counts any other type (a signal of mixing levels for the coach).
  No valid JSON = silence of that person (we add nothing on their behalf).
- **Deliberate contradictions** in the scenario: several people remember the same event differently — a hot spot appears only when the facilitator confronts them.
- **Router of the lean version** (script): people addressed (the name in any form) → matched by keywords → silent the longest.
- Order in the prompts: the fixed part (rules, card) before the variable part (board, echo) — the prompt cache works.

## 4. Your own scenario
Copy `scenarios/veterinary/` and change: `brief.md` (domain, hidden knowledge, deliberate contradictions, what not to reveal,
expected pivotal events, a "who trains what" table) and the persona cards (the same layout of sections; `obecna_od_startu: nie` (present from the start: no) = joins
on invitation; `formy_imienia` = the forms of the name for the router). The scenario is fictional — do not describe real people or companies.

## 5. Scenario trial (without a human, paid — with consent)
You check a new or changed scenario with an automaton before anyone trains on it:
`python3 .claude/skills/ddd-es-simulation/scripts/es_probe.py --variant pelna|oszczedna [--scenario <s>] [--budget-usd 2.5]`.
- The ready utterances of the facilitator and the expectations are in `scenarios/<s>/trial.json`: hidden knowledge (words in the transcript),
  deliberate contradictions (hot spot), behaviours from the cards (e.g. "asked by name → answers").
- Without a host: the script runs the rounds through `es_sim.py`, and a participant is a separate model call without tools (`claude -p`).
- Result: `probe-report.md` (✓/✗ for every expectation, the cost, invalid JSON, people without utterances) and the coach's debrief.
- Code 1 = the scenario does not work as in the brief (fix the card or the utterance in the trial), 3 = stopped after exceeding the budget.
- The variant of the day changes the person's temperament: an expectation that a given variant does not have to meet gets `skip_variants`.

## Measured costs
| Version | Rounds | Cost | Notes |
|---|---|---|---|
| full, host Ewa (Sonnet) | start + 3 rounds + coach | $1.30 (start $0.13; rounds $0.29 / $0.31 / $0.33; coach $0.24) | 6 people per round, each a separate agent; the participants are only ~25% of the cost |
| lean, host Ewa (Sonnet) | start + 3 rounds | $0.76 (start $0.14; rounds $0.17 / $0.19 / $0.25) | the room (Haiku) is ~10% of the cost of a round — the host eats the rest |
| scenario trial, full (`es_probe.py`, without a host) | 9 rounds + coach | $1.44 (57 calls, 378 s) | 2026-10-25, the veterinary scenario: 10/10 expectations (hidden knowledge 6/6, both contradictions as hot spots) |
| both, host `es-host` (Haiku) | — | not measured (the organization's spending limit on the day of the test) | an estimate from the proportions above; measure it: `python3 .tf/factory/cost_report.py --days 1` |
Measured before the "show verbatim" fix (the host added comments) — now every round has fewer output tokens.
