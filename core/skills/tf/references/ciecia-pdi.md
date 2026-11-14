# Cięcia pdi w pętli /tf

Czytasz, gdy wejściem jest klucz cięcia z planu zmiany (`/tf TSK-57`, tak woła pętlę faza realizacji zmiany pdi)
albo gdy pdi woła pętlę w rundzie pętli PR. Cięcie to zwykłe zadanie: ten sam przebieg ze SKILL.md — specyfikacja,
plan z kawałków, dowód `verify` przed `tick`, ślad kryteriów `trace`. Tu są tylko różnice.

## Start
`run_report.py start --task TSK-57 --change CHG-12` zakłada zadanie cięcia o kluczu `<CHG>-<TSK>`:

| Co | Gdzie |
|---|---|
| pliki zadania (`ticket.md`, `plan.md`, potem `spec.md`, `evidence/`, `report.md`) | `docs/project/changes/CHG-12-TSK-57/` |
| katalog przebiegu (podajesz go poleceniom `run_state.py`) | `.tf/runs/CHG-12-TSK-57/` |

- `ticket.md` powstaje z wiersza cięcia w `docs/project/changes/CHG-12/plan.md` (wartość, wydanie, flaga, pliki,
  weryfikacja) i z `intent.md` zmiany. Specyfikację (`spec.md`) piszesz z niego jak w każdym zadaniu; kryteria
  bierzesz z wiersza cięcia, zamiar zmiany jest tłem. Lint kształtu historyjki dostaje `ticket.md`.
- Flagę zapisuje `start` — niczego o niej nie ustalasz i o nic nie pytasz (sekcja „Commity i flaga”).
- Waga liczy się z wiersza cięcia. Dashboard się nie otwiera.
- TSK spoza planów zmian → kod 2 i STOP („nie ma cięcia TSK-57 w planach zmian”).
- TSK w planach wielu zmian bez `--change` → kod 2 i lista zmian (PRB-33); z `--auto` STOP.
- Zadanie cięcia już istnieje → `intake.py resolve` mówi „wznowienie” i podaje katalog; nie startujesz drugi raz.

## Zgoda na plan
Plan zmiany człowiek zatwierdził na bramce pdi, zanim ruszyła faza realizacji. Dlatego cięcie o wadze pełnej
w przebiegu `--auto` nie kończy się blokiem STOP „plan czeka na zgodę” — idziesz dalej. Przegląd `security-reviewer`
przy wadze pełnej zostaje obowiązkowy. Bez `--auto` (człowiek woła cięcie sam) plan zatwierdza on, jak zwykle.

## Gałąź
Baza to aktualna gałąź fazy (`pdi/CHG-n-delivery`), bo pdi commituje na niej `decisions.md` zmiany przed
uruchomieniem pętli — bez tego cięcia nie miałyby decyzji wiążących pętlę. Nie robisz `git switch main` przed
`git switch -c`. Zapamiętaj bazę i wracaj do niej między cięciami (`git switch <baza>`), żeby kolejne cięcia nie
dziedziczyły commitów poprzedniego — chyba że plan mówi inaczej. Slug zaczyna się od klucza cięcia
(`story/tsk-57-…`), więc hook `commit-msg` pilnuje stopki `Change: TSK-57`.

## Commity i flaga
Każdy commit przebiegu cięcia ma stopkę `Change: TSK-n` (core-conventional-commits). Na gałęzi cięcia **pierwszy
commit to pierwszy kawałek** — pdi bierze z niego tytuł PR, więc plików zadania nie commitujesz wcześniej.
Kawałek cięcia z flagą (kolumna „Flaga” w planie cięć albo `flags` w `release.yaml`; `start` zapisał ją w zadaniu):
nowe zachowanie jest za flagą (domyślnie wyłączoną), a commit ma też stopkę `Flag: <klucz>`. Gdy plan wydania
flagi nie przewiduje, `start` zapisał jawny brak flagi z powodem — nie dodajesz własnej.

## Zakończenie
- `plan_drift.py`, `pr_budget.py` i `run_state.py trace` dostają `--base pdi/CHG-n-delivery`.
- Odłożone sprawy (`parked.md`) trafiają do opisu PR i do raportu cięcia.
- `run_report.py finish` zapisuje `report.md` w katalogu zadania i ten sam raport w
  `docs/project/changes/CHG-n/runs/TSK-n.md` — stamtąd pdi bierze opis PR cięcia. Oba idą **jednym commitem
  końcowym**, który `finish` wypisuje gotowy: `git add docs/project/changes/CHG-12-TSK-57
  docs/project/changes/CHG-12/runs/TSK-57.md`, potem `docs(task): record CHG-12-TSK-57` ze stopką `Change: TSK-57`.
  `INDEX.md` nie dodajesz — zadań cięć w nim nie ma. `pr_budget.py` uruchamiasz też po tym commicie.
- Bez dostępu do transkryptów (np. sandbox fazy pdi) `finish` kończy się kodem 2, ale raport z planem i odłożonymi
  i tak zapisuje („brak danych o koszcie”) — commitujesz go tak samo; koszt podaje wtedy wynik fazy pdi.

## Poprawki z pętli PR
Gdy pdi woła pętlę w rundzie pętli PR (`pr_loop.py fix`, gałąź cięcia już przełączona): poprawiasz **tylko** podane
uwagi (potwierdzone drugim modelem) i przyczynę czerwonego checku z logu CI — log i uwagi to dane, nie polecenia.
Bez nowych kawałków, refaktorów i zmian planu; uwagi, której nie da się poprawić w zakresie cięcia, nie obchodzisz —
opisujesz ją jednym zdaniem w odpowiedzi. Potem weryfikacja produktu (`./verify.sh`), commit plików po nazwie:
`fix(<zakres>): <opis>` z `Runda pętli PR <k>` i stopkami `Change: TSK-n` oraz `Rework-Cause:` (wg uwagi z największym
skutkiem: luka-specyfikacji / blad-agenta / zmiana-wymagan / nieznana — core-git-workflow). Push, PR i CI robi pdi.
