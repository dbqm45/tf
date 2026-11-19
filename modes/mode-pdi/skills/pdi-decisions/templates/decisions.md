# Decisions of change {CHG}

Entries are added by `decision_record.py decision add {CHG} …` (after a human approves the draft). The `id` is assigned by the pdi
register (`record_decision` through MCP) and written in by `decision mark`; without the pdi server it stays empty, and `sent: no` — you send it
later (`decision pending`). Do not invent numbers.

<!-- Entry pattern:
## <what was decided, one sentence>
- ref: {CHG}/Dn (assigned by decision add)
- id:
- sent: no
- date: YYYY-MM-DD
- by: <the person or role that decided>
- kind: product | technical | process | triage | intent | gate | other
- why: <1–5 sentences, only from the conversation>
- source: claude-cli | claude-ai | slack | confluence | jira | manual | console | ci_for_sdlc | meeting
- drafted_by: ai | human
- finding: <only an answer to a ci_for_sdlc finding, e.g. DES-001:TSK-1>
- effect: <optional with a finding: resolve | accept_risk | dismiss | confirm>
- origin: <only a decision from the pdi register: pdi (decision import)>
- question: <a question from "Gate questions" that the human answered (decision gate --answers)>
- answer: <their answer; question/answer pairs may repeat>
-->
