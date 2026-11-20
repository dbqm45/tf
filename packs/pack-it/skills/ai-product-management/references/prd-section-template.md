# PRD section template for an AI feature

Paste into `docs/project/03-requirements/requirements.md` or `ai-feature-brief.md`. An empty field = an open question with an addressee.

```
## AI feature: <name>
Outcome and measure: <outcome, baseline value → target, check date>
User and task: <role, situation, what they do today and how much it costs>
Why AI: <rule/ML/LLM — justification>; alternative without AI: <what>
Cost of errors: <error type → effect → who bears it → limit>
Autonomy mode: <suggestion | approval | reversible | automatic>, fallback: <description>
Acceptance criteria (evals): set <source, N, owner>; bars <metric ≥ x>; good/bad/borderline examples <link>
Goals: quality <..>, latency p50/p95 <..>, cost per successful task <..> (price list date), what gives way <..>
Data: <needed, do we have it?, owner, legal basis for use>
Approach: <ready | API | fine-tuning | own> (technical decision: arch-ai-solutions)
Risks: <link to the register>, regulatory class: <from ai-governance-compliance>
Uncertainty UX: <expectations, confidence/sources, correction, signal collection>
Rollout: offline <threshold> → dogfooding <threshold> → beta <group, kill switch> → A/B <metric, threshold>
Metrics: product <..>; model <..>; guardrail <..>
Monitoring: <samples, alerts, review cadence, owner>
Message for stakeholders: can <..> / cannot <..> / we do not know yet <..>
Open questions: <question → addressee>
```
