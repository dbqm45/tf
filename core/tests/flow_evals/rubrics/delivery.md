# Rubryka: delivery

Oceniany efekt: cięcia `story/*` powstałe nad `pdi/CHG-n-delivery`, ich commity, PR-y i komunikaty persony
(`detail`). Sędzia dostaje: wynik `phase_run.py run` (JSON `out`), listę gałęzi cięć, krótki opis zmiany.

## correctness (1–5)

Cięcia robią to, co plan.md zapowiada; każde ma commit z `Change: <TSK>` i PR.

- **1** — cięcia nie powstały albo powstały bez commitów.
- **3** — cięcia są, ale brak dopisku `Change: <TSK>` i PR-ów (zabraknie śladu w planie).
- **5** — każde cięcie zamknięte PR, slice ma dowód sprawdzalności (test, metryka).

## decision_adherence (1–5)

- **1** — persona dopisuje nowe pomysły do plan.md zamiast realizować cięcia (odstąpienie od Z1).
- **3** — cięcia zgodne z planem, ale persona nie cytuje decyzji w commitach spornych.
- **5** — każde cięcie wnosi dokładnie to, co plan zapowiada, bez dopisków.

## style (1–5)

- **1** — commity w WIP, brak Conventional Commits, PR bez opisu.
- **3** — commity zgrupowane po końcu, bez pojedynczych kroków.
- **5** — commity drobne, Conventional Commits, PR z krótkim „co i dlaczego".

Kontrola długości (N17): NIE stosujemy dla delivery (artefakt to komunikat persony, nie dokument).

## Dodatkowo (automatycznie, bez sędziego)

- Z8c-2: po delivery (happy) `npm run analyze -- --repo` (ci_for_sdlc) **nie zwraca** blockera. Jeśli
  `ci_for_sdlc` niedostępne → runner oznacza `skipped_no_cifs` w raporcie, zadanie nie pada z tego powodu.
