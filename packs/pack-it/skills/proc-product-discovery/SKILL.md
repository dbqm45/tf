---
name: proc-product-discovery
description: Use when deciding what to build and why — outcomes, opportunities, assumptions and cheap tests, priorities and metrics, buy vs build for internal tools, outcome roadmaps.
metadata:
  review: "2027-11-20"
  catalog: "Use when deciding WHAT to build and why before building — a measurable outcome with a baseline, evidence, the opportunity solution tree, problem statement, JTBD and how-might-we framing, at least three solutions, an assumption map over value, usability, feasibility and viability, cheap tests with criteria written in advance, prioritisation (RICE, MoSCoW, Kano, WSJF) and success metrics (HEART, OKR, guardrails, an event plan), A/B experiments and launch readiness, qualifying internal tools (buy, extend, build or wait), a press release and FAQ before a big initiative, an epic as a hypothesis, a now/next/later outcome roadmap, business model and market tools. Not for team rituals and delivery process (proc-agile) or designing the interface (ux-feature-design)."
  keywords: "co budować, czy to budować, klienci o to proszą, szef chce funkcję, prośba o funkcję, eksport do Excela, discovery produktowe, odkrywanie produktu, wynik zamiast funkcji, outcome, drzewo szans, opportunity solution tree, JTBD, problem użytkownika, założenia do sprawdzenia, mapa założeń, tani test, prototyp, test concierge, fake door, priorytetyzacja, uszeregować pomysły, lista pomysłów na funkcje, RICE, MoSCoW, Kano, WSJF, metryki sukcesu, metryki po wydaniu, HEART, OKR, metryki ochronne, plan zdarzeń analitycznych, test A/B, eksperyment, gotowość do wydania, czy jesteśmy gotowi do startu, narzędzie wewnętrzne, zbudować własne narzędzie, kupić czy zbudować, raport dla kierownika z kilku narzędzi, automatyzacja raportu, komunikat prasowy przed budową, FAQ, epik jako hipoteza, roadmapa wyników, roadmapa to lista funkcji z datami, teraz następnie później, model biznesowy, lean canvas, analiza konkurencji, what to build, is it worth building, customers are asking for it, feature request, product discovery, outcome over output, opportunity tree, jobs to be done, assumption mapping, cheap experiment, prioritise features, RICE scoring, success metrics, guardrail metrics, event tracking plan, A/B experiment plan, launch readiness, internal tool, build vs buy, extend existing tools, press release before building, PR FAQ, epic hypothesis, outcome roadmap, now next later, business model canvas, competitor analysis"
---

# Product discovery — decide what to build before building it

Discovery and delivery run side by side: small tests every week, not one research phase up front. Product decisions
belong to a human; the agent prepares the evidence, the options with a recommendation, and the open questions. No
product, users or outcome given ("what should we build next?") → ask for them; invent nothing.

## Procedure
0. **Internal tool or automation?** ("let's build a dashboard / an agent that collects …") — it is a proposed solution, not a
   signal. Qualify it first: buy, extend, build or wait — `references/buy-extend-build.md`.
1. **Outcome.** A measurable product result the team can influence, with a baseline and a target — e.g. "the share of new
   customers who send their first invoice within 7 days: 35% → 50%". A feature request is a solution hypothesis: ask
   which problem or outcome stands behind it.
2. **Evidence.** Interviews about specific recent events (`.claude/skills/ddd-discovery-intake/references/user-research.md`),
   analytics, support tickets. Without evidence, opportunities are assumptions — mark them as such.
3. **Opportunity solution tree.** Outcome → opportunities (needs, problems, desires) → solutions → assumption tests.
   An opportunity that can be solved only one way is a disguised solution. One tree per team per outcome.
4. **Choose the target opportunity** by size (how many customers, how often, how painful), market factors and strategy —
   not by effort yet.
5. **Frame it:**
   - problem statement — who, in what situation, what they need, why it matters, how we will know it improved; no solution;
   - JTBD — "When [situation], I want [motivation], so that [expected outcome]";
   - how might we — rooted in the evidence, aimed at the outcome, neither so broad it means nothing nor hiding a solution.
6. **At least 3 solutions** for the chosen opportunity, each with a value proposition: for whom, which pain it removes,
   what it adds, how it differs from today.
7. **Assumption map over four risks:** value (will they want it), usability (can they use it), feasibility (engineering,
   API limits, data, performance), viability (cost, law, sales, support). Place each assumption on importance × strength of
   evidence; test the important, weakly evidenced ones first.
8. **Tests, cheapest first:** existing conversations and data → a paper or clickable prototype → a concierge test done by
   hand → a version for a narrow group behind a flag → an A/B test (`references/experiments-and-release.md`). Write the
   success criterion and the decision for each result **before** the test. A fake-door test only with an honest message
   after the click.
9. **A large initiative:** write the launch-day press release and FAQ first, and the epic as a hypothesis with a measure and
   a stopping criterion (`references/working-backwards.md`). If the press release cannot be written so that a customer
   would read it, the problem or the customer is unclear.
10. **Priorities and metrics:** `references/priorities-and-metrics.md` — RICE, MoSCoW, Kano, WSJF; success and guardrail
    metrics; an event plan before implementation; a date to check after release.
11. **Record** in `docs/project/01-discovery/` (core-project-record): the decision, the chosen and rejected solutions with
    reasons, the test results. Cut the first version vertically (working before polished). Scope and the requirements
    contract for the MVP: proc-requirements-shaping.

**Roadmap:** replace a feature list with dates by an outcome roadmap — Now / Next / Later, each item a problem or
opportunity with its outcome metric; dates only for external commitments (`references/working-backwards.md`).
**Business model and market:** canvases, competitors, SWOT, five forces — `references/business-model-and-market.md`.

## Rules
- An outcome without a measure is not an outcome; a metric nobody checks after release is decoration.
- Personal data in research and analytics needs consent and minimisation (arch-privacy-compliance).
- Showing the change to stakeholders and how it will be measured: pm-stakeholders.

## Example
**Situation:** "My boss wants an Excel export because customers ask for it."
**Result:**
- Behind the request (three support tickets, 2 calls): accountants re-type invoice data into their own system each month.
- Outcome: time from month end to closed books for customers on the Pro plan, median 6 days → 3 days.
- Solutions: (A) Excel export; (B) a direct integration with the 2 most used accounting systems; (C) a scheduled e-mail
  with a CSV to the accountant.
- Riskiest assumption: "accountants will import the file without manual fixes" (value, weak evidence).
- Test: send a hand-made CSV to 5 accountants this week; criterion — at least 4 import it without changes; otherwise drop
  A and C and explore B.

## Checklist
- [ ] a measurable outcome with a baseline
- [ ] opportunities from evidence, assumptions marked
- [ ] at least 3 solutions and the four-risk map
- [ ] a test of the weakest important assumption with the criterion written first
- [ ] success and guardrail metrics, an event plan, a date to check after release

## Sources
- T. Torres, *Continuous Discovery Habits*, 2021; Product Talk, "Opportunity Solution Trees".
- M. Cagan, *Inspired*, 2nd ed., 2017 (the four product risks).
- C. Christensen et al., *Competing Against Luck*, 2016 (jobs to be done).
- Nielsen Norman Group, "Using 'How Might We' Questions to Ideate on the Right Problems" [unverified: date].
- Strategyzer, Value Proposition Canvas.
- roadmap.sh, "Product Design" roadmap (accessed 2026-11-20).
