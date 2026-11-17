# Decyzje zmiany {CHG}

Wpisy dodaje `decision_record.py decision add {CHG} …` (po zatwierdzeniu szkicu przez człowieka). `id` nadaje rejestr
pdi (`record_decision` przez MCP) i wpisuje `decision mark`; bez serwera pdi zostaje puste, a `sent: no` — wyślesz
później (`decision pending`). Nie wymyślaj numerów.

<!-- Wzór wpisu:
## <co zdecydowano, jedno zdanie>
- ref: {CHG}/Dn (nadaje decision add)
- id:
- sent: no
- date: RRRR-MM-DD
- by: <osoba lub rola, która zdecydowała>
- kind: product | technical | process | triage | intent | gate | other
- why: <1–5 zdań, tylko z rozmowy>
- source: claude-cli | claude-ai | slack | confluence | jira | manual | console | ci_for_sdlc | meeting
- drafted_by: ai | human
- finding: <tylko odpowiedź na ustalenie ci_for_sdlc, np. DES-001:TSK-1>
- effect: <opcjonalnie przy ustaleniu: resolve | accept_risk | dismiss | confirm>
- origin: <tylko decyzja z rejestru pdi: pdi (decision import)>
- question: <pytanie z „Pytania do bramki”, na które odpowiedział człowiek (decision gate --answers)>
- answer: <jego odpowiedź; pary pytanie/odpowiedz mogą się powtarzać>
-->
