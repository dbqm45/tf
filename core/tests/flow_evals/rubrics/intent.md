# Rubryka: intent

Oceniany artefakt: `docs/project/changes/<CHG-n>/intent.md`. Sędzia dostaje: artefakt, treść zgłoszenia PRB
(gdy jest), fragment `decisions.md` ze wszystkimi wiążącymi decyzjami tej zmiany, zapytanie o ocenę na 3 osiach
w JSON.

## correctness (1–5)

Zgodność z faktami ze zgłoszenia PRB i decyzjami zmiany.

- **1** — persona wymyśla problem albo dane wsparcia (koszty, metryki), których nie ma w PRB ani decisions.md.
- **3** — fakty na ogół zgodne, ale kilka twierdzeń bez odwołania do źródła (PRB, DEC-n).
- **5** — każde twierdzenie ma odwołanie do zgłoszenia, decyzji albo jest wyraźnie oznaczone jako otwarte pytanie.

## decision_adherence (1–5)

Odwołania do wiążących decyzji CHG-n/Dk w częściach, których te decyzje dotyczą.

- **1** — decyzje pominięte, persona idzie na własnym pomyśle.
- **3** — kilka decyzji wymienionych, ale bez wyjaśnienia, jak ograniczają zamiar.
- **5** — zamiar wpisuje się w decyzje; alternatywy odrzucone z wyraźnym odwołaniem do decyzji.

## style (1–5)

Czytelność, zwięzłość, brak wypełniania.

- **1** — żargon korporacyjny, listy bez treści, powtórzenia.
- **3** — treść zrozumiała, ale sekcje nierówne; jedno-dwa puste akapity.
- **5** — każda sekcja niesie informację; wypunktowania mają po jednym faktach zdaniu.

Kontrola długości (N17): artefakt dłuższy niż `length_control_ratio` × średnia bazowa z tej fazy dostaje auto
**-1** w `style`. Baseline średniej: `tmp/flow-evals/baselines/<model>-<sha>.json` pole `phase_avg_chars.intent`.
