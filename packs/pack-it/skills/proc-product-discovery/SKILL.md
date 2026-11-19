---
name: proc-product-discovery
description: Use when deciding what to build and why — outcome over features, the opportunity tree, JTBD, assumption tests, RICE.
metadata:
  review: "2027-10-09"
  catalog: "Use when you must decide WHAT to build and why — outcome over features, the opportunity solution tree, the problem and JTBD, 'how might we' questions, at least three solutions, an assumption map and its tests, priorities (RICE, MoSCoW, Kano), success metrics (HEART, OKR), A/B experiments, launch readiness, qualifying an internal tool (buy, extend, build, wait), a press release and FAQ before building, an epic as a hypothesis, an outcome-based roadmap. Not for team rituals (proc-agile) or interface design (ux-feature-design)."
  keywords: "narzędzie wewnętrzne, budować czy kupić gotowe, zbudować własne narzędzie, raport dla kierownika, komunikat prasowy, press release, working backwards, PR/FAQ, zanim zaczniemy budować, przed pierwszą linią kodu, epik jako hipoteza, roadmapa, roadmapa funkcji z datami, roadmapa według wyników, teraz dalej później, internal tool, build or buy, build our own tool, report for a manager, before we start building, before the first line of code, epic as a hypothesis, roadmap, feature roadmap with dates, outcome-based roadmap, now next later"
---

# Product discovery

The goal: do not build things nobody needs, and know how we will tell that they worked. Discovery
and delivery run in parallel — small tests every week, not one "research" phase before the project.

## Procedure
0. **An internal tool or automation for a team?** First the "buy / extend / build / wait" qualification
   with an opportunity map — `references/buy-extend-build.md`. "Let's make a dashboard / an agent" is a solution, not a signal.
1. **An outcome, not a feature.** Start from a measurable product outcome the team can influence ("the share of new
   customers who issued their first invoice within 7 days: 35% → 50%"). A request for a feature ("let's add an export to Excel")
   is a solution hypothesis — ask what problem and what outcome stand behind it.
2. **Evidence from users**: interviews about specific, recent events, analytics data, tickets
   (ddd-discovery-intake, `user-research.md`). Without evidence, opportunities are guesses — mark them as assumptions.
3. **The opportunity solution tree**: outcome → opportunities (customer needs, problems, desires)
   → solutions → assumption tests. The opportunity test: "can it be solved in more than one way?" — if not, it is a
   solution disguised as an opportunity. A tree for one team and one outcome, not for the whole company.
4. **Choosing the target opportunity**: size (how many customers, how often, how much it hurts), market factors, company strategy.
   You do not count effort at this stage — many opportunities have surprisingly simple solutions.
5. **Framing the problem**:
   - **the problem statement**: who, in what situation, what they need, why it matters, how we will know it improved —
     with no solution in the text;
   - **the job to be done (JTBD)**: "When [situation], I want [motivation], so that [expected outcome]" — it describes the progress
     a person is seeking, regardless of the product;
   - **"How might we…?"**: based on discovery, aimed at the outcome, positive, neither too broad nor with a ready-made
     solution inside ("…make the customer sure that the invoice is correct?", not "…add a PDF preview?").
6. **At least three solutions** for the chosen opportunity (a comparison leads to better decisions than judging a single idea);
   each with a value proposition — for whom, which pain it removes, which gain it gives, how it differs from the current way.
7. **The assumption map**: for each solution list what must be true — across four risks: **value** (will they
   want it), **usability** (can they use it), **feasibility** (can we build it — with engineering, API constraints, data,
   performance), **viability** (does it work for the business: cost, law, sales, support). Place them on an
   *importance × strength of evidence* matrix; you test the important and weakly proven ones first.
8. **Assumption tests from the cheapest**: a conversation and data that already exist → a paper or clickable prototype (ux-feature-design)
   → a "by hand instead of automation" test (concierge) → a version for a narrow group behind a flag → A/B
   (`references/experiments-and-release.md`). Before the test, write down the success criterion and the decision you will make
   for each result. A "fake door" test (a button for a feature that does not exist yet) only with an honest message
   after the click.
8a. **A large initiative before building** (a new module, an epic spanning several sprints): a launch-day press release
   and FAQ (working from the customer backwards), the epic written as a hypothesis with a measure and a stopping criterion —
   `references/working-backwards.md`. If the press release cannot be written so that a customer would want to read it,
   the problem or the customer is still unclear.
9. **Decision and record**: the chosen solution, the rejected ones with the reason, test results → `docs/project/01-discovery/`
   (core-project-record). Cut the scope of the first version vertically (proc-agile) — a working feature before a polished one.
   The MVP scope and the requirements contract before the architecture (a time budget, an empty CRUD, a challenge for every requirement):
   proc-requirements-shaping.

## Priorities and metrics
Details and formulas: `references/priorities-and-metrics.md` — RICE, MoSCoW, Kano, value/effort,
HEART with goals, signals and metrics, OKR, a north star metric with guardrail metrics, product-market fit,
an analytics event plan.

An outcome-based roadmap (now / next / later instead of a list of features with dates): `references/working-backwards.md`.

The business model, the market and competition (the business model canvas, Lean Canvas, competitor analysis, SWOT with actions,
Porter's five forces, the customer experience map): `references/business-model-and-market.md`.

## Rules
- Product decisions (what we build, what we cut, whether we release) are made by a human. The agent prepares evidence,
  options with a recommendation and questions (core-plan-interview).
- Personal data in research and analytics: consent, minimization, no sending to external tools without the organization's
  consent (GDPR).
- An outcome that has no measure is not an outcome. A measure nobody will check after the release is decoration.

## Checklist
- [ ] a measurable outcome, with a baseline value
- [ ] opportunities based on evidence, with assumptions marked
- [ ] ≥ 3 solutions, an assumption map across four risks
- [ ] a test of the weakest important assumption with the success criterion written before the test
- [ ] success and guardrail metrics + an event plan; a date for checking after the release

## Sources
- T. Torres, [Opportunity Solution Trees](https://www.producttalk.org/opportunity-solution-trees), *Continuous Discovery Habits* (2021)
- M. Cagan, *Inspired* (2018) — the four risks; NN/g, [How Might We questions](https://www.nngroup.com/articles/how-might-we-questions/)
- C. Christensen et al., *Competing Against Luck* (2016) — JTBD; Strategyzer — the value proposition
- [roadmap.sh — Product Design](https://roadmap.sh/product-design)
- 10xDevs course, ed. 3 (2026), module 5, lesson 1 (buy, extend or build) — training material (accessed 2026-10-09)
Described in our own words.
