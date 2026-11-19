---
name: ai-product-management
description: Use for deciding on an AI feature in a product — whether AI, acceptance criteria as evals, cost per task, risks, uncertainty UX, staged rollout.
metadata:
  review: "2027-04-17"
  catalog: "Use when as a product manager or product owner you plan a feature based on AI (LLM, ML) — whether AI is the right tool (a rule, classical ML or an LLM; the cost of errors and who bears it), framing by outcome and acceptance criteria written as evals (a quality bar, tolerance per error type, examples of good and bad results), quality, latency and cost-per-task goals with unit economics, buy, build or use an API, data needs, a risk register (hallucinations, bias, safety, privacy, prompt injection), uncertainty UX and human in the loop, staged rollout (offline, dogfooding, beta, A/B), product versus model metrics, monitoring after launch, communication with stakeholders, a PRD section for an AI feature. Not for discovering the outcome and prioritization (proc-product-discovery), the PRD and MVP (proc-requirements-shaping), the evaluation method (ai-evals), interface copy (ux-content-design), the legal AI Act classification (ai-governance-compliance) or choosing the technical architecture (arch-ai-solutions)."
  keywords: "funkcja AI, czy użyć AI, product manager AI, AI PM, wymagania dla AI, kryteria akceptacji AI, koszt na zapytanie, unit economics, koszt tokenów, kup czy zbuduj model, halucynacje ryzyko, człowiek w pętli, niepewność modelu, pokazać pewność, wdrożenie funkcji AI, beta AI, dogfooding, model się myli, asystent AI w produkcie, copilot, PRD funkcji AI, czy reguły wystarczą, komunikacja z zarządem o AI, czy warto użyć AI, AI czy zwykłe reguły, funkcja AI sama zatwierdza, kiedy AI ma sens, bezpiecznie wypuścić funkcję AI, wypuścić AI do klientów, model może się mylić, pokazać użytkownikom błędy modelu, prototyp AI, wdrożyć asystenta, AI feature, whether to use AI, requirements for AI, AI acceptance criteria, cost per request, token cost, buy or build a model, hallucination risk, human in the loop, model uncertainty, show confidence, rolling out an AI feature, the model is wrong, AI assistant in the product, AI feature PRD, are rules enough, communicating with the board about AI, is it worth using AI, AI or plain rules, the AI feature approves by itself, when AI makes sense, safely release an AI feature, release AI to customers, the model can be wrong, show users the model's errors, AI prototype, roll out an assistant"
---

# Product management with AI

An AI feature differs from an ordinary one in that **the answer is sometimes wrong by nature**, and quality is a distribution, not a value.
The PM's job: establish whether AI is justified here, write down "good enough" in a measurable way, compute the cost and
design life with errors. What this skill does **not** do: the outcome and priorities are **proc-product-discovery**, the PRD skeleton
and the MVP budget are **proc-requirements-shaping**, the evaluation method (datasets, graders, CI) is given by **ai-evals**.

## Procedure
1. **Whether AI?** Start with the simplest tool that closes the problem (`references/decisions-and-economics.md`):
   a deterministic rule, when the logic can be written down; classical ML, when there are labels and a fixed data shape; an LLM,
   when the input is open text, and the output requires understanding or generation. Test: "what happens when
   the model is wrong, and **who bears it**?" — the customer, an employee or the company. A high cost of error without the possibility
   of verification = not AI, or AI only as a proposal for a human.
2. **The outcome, not the model.** Write down the business outcome with a measure (proc-product-discovery) and the user's task; the model is
   a means. Show what the user does today and how much it costs — that is the reference point for the model.
3. **Acceptance criteria as evals.** Instead of "the model answers correctly" write down:
   - **an evaluation set** (N cases from real tickets, including edge and adversarial ones) and the owner of the set;
   - **a quality bar** per metric, e.g. "≥ 90% of answers consistent with the source";
   - **tolerance per error type**: errors are unequal (a false approval of a refund ≠ a false rejection); each type has
     its own limit, including "0 in category X";
   - **3–5 examples each of a good and a bad result** and of a borderline result, agreed with a domain expert.
   How to build the set, the graders and the gate — **ai-evals**. Without a set the feature does not go into scope.
4. **Quality, latency and cost goals.** Set them together: quality (step 3), latency (p50/p95 to the first and last
   token, the user's time budget) and **cost per successful task** (not per request: include retries, context,
   the judge, the human checking). Compare with the revenue or the cost of today's process (unit economics:
   `references/decisions-and-economics.md`). The goals conflict — write down which one gives way.
5. **Buy, build or API.** The order of attempts: a ready product → a model API with your own prompt and context → fine-tuning
   → your own model. Each next rung makes sense only after a measured gap on the previous one. The technical decision
   and the architecture come from **arch-ai-solutions**; the PM supplies the criteria: data, cost, latency, vendor dependency.
6. **Data.** What data is needed (examples, labels, content for retrieval), whether we have it, who
   owns it, whether it may be used for this purpose, how fresh it is. Missing data for the evaluation set is a blocker, not a risk.
7. **Risk register** (`references/risks-and-ux.md`): hallucinations, bias, content safety, privacy,
   prompt injection, vendor dependency, drift. Each: a scenario, an effect, a probability, a measure, an owner.
   The regulatory class (AI Act) and the obligations are established by **ai-governance-compliance**; the PM enters the result in the register.
8. **Uncertainty UX and human in the loop** (`references/risks-and-ux.md`): set expectations ("this is a proposal"), show
   sources or confidence only where it is calibrated, design an emergency exit (a fallback without AI), easy
   correction and collecting signals from corrections into the evaluation set. Copy: **ux-content-design**.
9. **Staged rollout.** Offline evaluation (a gate) → internal dogfooding → a beta with a narrow group and a kill switch →
   A/B or shadow on part of the traffic → full rollout. Gradually increasing traffic alone does not replace A/B or shadow:
   a comparison with a control group on a product metric is needed. A transition requires a criterion written down in advance. The kill switch and
   the rollback plan are ready before the beta (ops-release-engineering).
10. **Metrics.** Two layers: **product** (task completion, retention, time saved, escalations to a human —
    these decide) and **model** (consistency, refusal rate, hallucinations per the evaluation — diagnostics). A good model
    metric without a movement of the product metric is not a success. Add guardrail metrics: cost, complaints, safety.
11. **After launch.** Monitor traffic with samples and alerts (ai-evals, ops-observability), review failures every week,
    add new failures to the set, and treat a change of the model or the prompt as a release through the same gate.
12. **Communication.** Tell stakeholders plainly: what the model does well, what it does not do, how often it is wrong
    (a number from the evaluation with a date), what happens on an error, what it costs. No promises of "100%" and no "AI will
    handle everything". One page with three blocks: can / cannot / we do not know yet.
13. **Record.** The AI feature section in `docs/project/03-requirements/requirements.md` or `ai-feature-brief.md`
    (template: `references/prd-section-template.md`; core-project-record). A human makes the rollout decision.

## Example
**Input:** a shop wants AI to approve returns without the support team (3,000 tickets/month, 4 min of work each).
**Result (a brief section):**
- Whether AI: rules cover 60% (a return within 14 days, no signs of use); the rest are text descriptions → an LLM only for that part;
- the cost of an error: a false approval = loss of goods (the company), a false rejection = a complaint (the customer); limits:
  false approvals ≤ 1%, rejections ≤ 5% [example];
- mode: the model proposes, a human approves returns > 200 PLN, below that — automatic after a trial period;
- set: 300 tickets from the archive + 30 adversarial ones, 4 good/bad/borderline examples each;
- goals: p95 < 6 s, cost ≤ 0.15 PLN per ticket against 4 min of work [example];
- stages: offline → dogfooding (the support team, 2 weeks) → a beta at 10% of traffic with a kill switch → A/B; product metric: the
  handling time, the share of repeat contacts; guardrail: the value of wrongly approved returns.

## Checklist
- [ ] justified why not a rule; the cost of an error and who bears it named
- [ ] acceptance criteria as evals: a set, a bar, tolerance per error type, good and bad examples
- [ ] quality, latency and cost per successful task together; stated which one gives way
- [ ] data: availability, the right to use it, the owner; a risk register with owners; the regulatory class from ai-governance-compliance
- [ ] UX: expectations, a fallback without AI, user corrections go back into the set
- [ ] stages with transition criteria, a kill switch; product metrics above model metrics
- [ ] a message for stakeholders: can / cannot / we do not know; a record in docs/project/

## Sources
- Microsoft, "Guidelines for Human-AI Interaction" (HAX Toolkit, microsoft.com/en-us/haxtoolkit/ai-guidelines, read 2026-10-17):
  18 guidelines in four phases (initially, during interaction, when AI is wrong, over time). The full list of titles was not
  read [unverified].
- Google PAIR, "People + AI Guidebook" (pair.withgoogle.com/guidebook, the home page unreachable from this environment
  2026-10-17; the chapters Mental Models, Explainability + Trust, Feedback + Control, Errors + Graceful Failure confirmed
  by a search that day; the content of the Explainability and Feedback chapters [unverified]).
- The rollout stages, the structure of the risk register and the PRD section template are the practice of the skill's authors [assumption].
Described in our own words.
