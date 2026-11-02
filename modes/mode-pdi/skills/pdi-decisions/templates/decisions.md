# Decyzje zmiany {CHG}

Wpisy dodaje `decision_record.py decision add {CHG} …` (po zatwierdzeniu szkicu przez człowieka). `id` nadaje rejestr
pdi (`record_decision` przez MCP) i wpisuje `decision mark`; bez serwera pdi zostaje puste, a `wyslano: nie` — wyślesz
później (`decision pending`). Nie wymyślaj numerów.

<!-- Wzór wpisu:
## <co zdecydowano, jedno zdanie>
- ref: {CHG}/Dn (nadaje decision add)
- id:
- wyslano: nie
- kiedy: RRRR-MM-DD
- kto: <osoba lub rola, która zdecydowała>
- rodzaj: product | technical | process | triage | intent | gate | other
- dlaczego: <1–5 zdań, tylko z rozmowy>
- zrodlo: claude-cli | claude-ai | slack | confluence | jira | manual | console | ci_for_sdlc | meeting
- szkic: ai | human
- ustalenie: <tylko odpowiedź na ustalenie ci_for_sdlc, np. DES-001:TSK-1>
- skutek: <opcjonalnie przy ustaleniu: resolve | accept_risk | dismiss | confirm>
- pochodzenie: <tylko decyzja z rejestru pdi: pdi (decision import)>
- pytanie: <pytanie z „Pytania do bramki”, na które odpowiedział człowiek (decision gate --answers)>
- odpowiedz: <jego odpowiedź; pary pytanie/odpowiedz mogą się powtarzać>
-->
