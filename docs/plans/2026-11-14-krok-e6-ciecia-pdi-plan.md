# Krok E6: cięcia pdi w nowym układzie — plan realizacji

Data: 2026-11-14. Kawałek E6 planu kroku E (`docs/plans/2026-11-13-krok-e-plan-realizacji.md`). Plan powstał po
przeczytaniu kodu pdi (`dbqm45/pdi`, commit `b40dbe8`), trybu pdi fabryki (`modes/mode-pdi`) i bramki ShipScope
(`dbqm45/ci_for_sdlc`, commit `a81a64c`).

## Po co

Dziś przebieg cięcia (`/tf TSK-57`, tak woła pętlę faza realizacji pdi) idzie starą drogą: jeden katalog roboczy
`.tf/runs/cuts/…`, bez zadania, specyfikacji, dowodów weryfikacji i śladu kryteriów. Zwykłe zadanie ma to wszystko
od kroków C i D. Po E6 cięcie przechodzi tę samą drogę co zwykłe zadanie, a pdi dostaje to samo co dotąd.

## Czego pdi oczekuje od pętli (sprawdzone w kodzie)

| Co | Gdzie w pdi | Po E6 |
|---|---|---|
| gałąź `story/tsk-<n>-…` odgałęziona od `pdi/CHG-n-delivery`, z commitami | `dispatch_local.py`, `_publish_cuts` | bez zmian |
| tytuł PR = temat pierwszego commitu na gałęzi cięcia | `dispatch_local.py`, `_cut_pr_text` | bez zmian: pierwszy commit to nadal pierwszy kawałek, pliki zadania idą ostatnim commitem |
| opis PR = plik `docs/project/changes/<CHG>/runs/<TSK>.md` z gałęzi cięcia | `dispatch_local.py`, `_cut_pr_text` | bez zmian: ta sama ścieżka, ten sam nagłówek i sekcje |
| skaner pętli w `.claude/skills/tf/scripts/security_scan.py` | `phase_sandbox.py` | bez zmian |
| wywołanie `/tf <TSK> --auto --change CHG-n` | `modes/mode-pdi/…/phase_run.py` | bez zmian |

Plików roboczych pętli (`.tf/runs/…`, `run.json`) pdi nie czyta — to można zmienić swobodnie.

## Ustalenia, które kształtują rozwiązanie

1. **Katalog `docs/project/changes/` czytają też inni.** Bramka ShipScope w CI produktu
   (`change-check.yml` → `npm run analyze`) traktuje każdy folder o nazwie `LITERY-liczba` jako zmianę i czerwieni
   się, gdy nie ma w nim `intent.md` (`packages/core/src/connectors/repo.ts`, wzorzec `KEY` i komunikat „a change
   needs its intent.md”). Folder `TSK-57` pasuje do tego wzorca, folder `CHG-12-TSK-57` nie.
2. **`decision_record.py check` bez `--change`** sprawdza nagłówek każdego pliku `.md` w każdym folderze
   `docs/project/changes/*/` — pliki zadania (bez nagłówka pdi) zgłosiłby jako błąd.
3. **Spis `docs/project/changes/INDEX.md`** przepisuje każdy zapis zadania. Cięcia jednej zmiany powstają na
   osobnych gałęziach z tej samej bazy, więc każde dopisałoby swój wiersz w tym samym miejscu — drugi PR cięcia
   miałby konflikt.
4. **Silnik liczy katalog zadania z klucza** (`docs/project/changes/<KEY>/`) w około 40 miejscach w 8 plikach
   silnika i pętli (najwięcej w `task_state.py`, `spec_check.py` i `run_report.py`), a hook `guard_paths` poznaje
   pliki zadania po wzorcu ścieżki. Zagnieżdżenie zadania cięcia w folderze zmiany wymagałoby przepisania ich
   wszystkich.
5. **Faza realizacji pdi rusza dopiero po bramce planu zmiany** (artefakt poprzedniej fazy musi być na gałęzi —
   `dispatch_local.py`), a pętla biegnie w niej bez człowieka (`--auto`).

## Decyzje projektowe

| # | Decyzja | Dlaczego |
|---|---|---|
| 1 | Zadanie cięcia ma klucz `<CHG>-<TSK>`, np. `CHG-12-TSK-57`: katalog trwały `docs/project/changes/CHG-12-TSK-57/`, roboczy `.tf/runs/CHG-12-TSK-57/` | bez zmian w silniku (ustalenie 4); nie myli bramki ShipScope (1); ten sam TSK w dwóch zmianach nie koliduje; w spisie folderów stoi obok swojej zmiany |
| 2 | `task.json` cięcia ma pola `change` i `cut` | po nich skrypty poznają cięcie; człowiek widzi, do której zmiany należy |
| 3 | Zadań cięć nie ma w `INDEX.md`; `tf task list` je pokazuje | brak konfliktów między PR-ami cięć (3); spisem cięć jest plan zmiany |
| 4 | `decision_record.py check` pomija foldery zadań (te z `task.json`) | ustalenie 2; dotyczy też zwykłych zadań w produkcie z trybem pdi |
| 5 | Zgodę człowieka na plan cięcia zastępuje bramka planu zmiany: cięcie o wadze pełnej nie zatrzymuje przebiegu `--auto`; obowiązkowy przegląd `security-reviewer` zostaje | ustalenie 5 — inaczej każda zmiana dotykająca np. płatności stawałaby w fazie bez człowieka; plan zmiany człowiek już zatwierdził |
| 6 | Flagę zapisuje `start`: z planu wydania (`Flaga` w planie cięć albo `release.yaml`), a gdy jej tam nie ma — „bez flagi” z powodem | flaga cięcia jest decyzją planu wydania, pętla jej nie wymyśla i o nią nie pyta |
| 7 | Raport: `report.md` w katalogu zadania i ta sama treść w `docs/project/changes/<CHG>/runs/<TSK>.md`; jeden commit końcowy `docs(task): record CHG-12-TSK-57` ze stopką `Change: TSK-57` obejmuje oba | pdi dostaje opis PR tam, gdzie go szuka; jeden commit zamiast dwóch |
| 8 | Stary układ znika bez warstwy zgodności: `.tf/runs/cuts/` nie powstaje, a polecenia przebiegu, które potrzebują zadania, dla katalogu bez klucza zadania odpowiadają „zacznij cięcie od nowa”; sam raport kosztu (`finish`, `status`) nadal czyta dowolny katalog z `run.json` | przebieg cięcia trwa jedną fazę, więc nie ma czego przenosić; mniej kodu |
| 9 | `/tf TSK-57`, gdy zadanie cięcia już istnieje, wznawia je | tak jak zwykłe zadanie |

Decyzja 5 zmienia regułę „waga pełna = zgoda człowieka na plan” dla jednego przypadku. Jeśli właściciel woli
zatrzymanie także w cięciach, wystarczy ją wycofać — reszta planu od niej nie zależy.

## Kawałki

| # | Co powstaje | Testy (najpierw, czerwone) |
|---|---|---|
| E6a | silnik: `tf task start --change CHG-n --cut TSK-n`; spis bez cięć; bramka wagi i trybu dla cięcia (decyzja 5); `decision_record.py check` pomija foldery zadań | `test_task_state.py`: pola w `task.json`, `INDEX.md` bez wiersza cięcia i bez zmiany treści, `list` z cięciem; `test_task_weight.py` i `test_task_mode.py`: cięcie pełne w `--auto` przechodzi do realizacji bez zgody, zwykłe zadanie nadal nie; test trybu pdi: `check` z folderem zadania obok zmiany kończy się kodem 0 |
| E6b | przebieg: `run_report.py start --task` zakłada zadanie cięcia (`ticket.md` z wiersza cięcia i zamiaru zmiany, `plan.md`, flaga, waga); `finish` zapisuje raport w obu miejscach; polecenia `run_state.py` działają dla cięcia (koniec odmów „stary układ”); `intake.py` wznawia istniejące cięcie; podgląd pokazuje cięcie jak zadanie | `test_run_report.py`: przypadki `--task` w nowym układzie (ścieżki, treść `ticket.md`, flaga, PRB-33); nowy `test_cut_run.py`: cały przebieg cięcia skryptami na repozytorium testowym — raport cięcia ma nagłówek `# Raport przebiegu TSK-n (CHG-n)` i sekcję „Odłożone do decyzji” w tym samym kształcie co przed zmianą, `INDEX.md` nietknięty, pierwszy commit gałęzi to kawałek, `spec`, `verify`, `tick`, `trace` i `flag` działają; `test_run_state.py`, `test_intake.py`, `test_plan_drift.py`: przypadki cięcia |
| E6c | treść: `references/ciecia-pdi.md` od nowa (różnice cięcia: źródło zadania, baza gałęzi, stopki, commit końcowy, zgoda z bramki zmiany), odwołania w `SKILL.md` (limit 15 000 znaków), `references/waga.md`, `PETLA.md`, `PUBLIC_API.md`, przewodnik trybu pdi | scenariusz ewaluacji skilla dla cięcia przed zmianą treści; bramka skilla `tf`; `test_tf_skill.py` |

Dwa PR-y: pierwszy z tym planem i E6a, drugi z E6b i E6c (treść skilla opisuje zachowanie skryptów, więc idzie razem
z nimi).

## Jak sprawdzę, że pdi działa nie gorzej

- Testy trybu pdi i testy pętli w wariantach `none`, `mode-pdi` i `all` (`tools/workspace.py check`).
- `test_cut_run.py` porównuje pliki, które czyta pdi (ścieżka i kształt raportu, pierwszy commit, nazwa gałęzi).
- Raport z nowego układu podam jednorazowo funkcji pdi, która czyta listę „Odłożone do decyzji” — wynik zapiszę
  w opisie PR.
- Testy repozytorium pdi uruchomię bez zmian (`uv run pytest -q`) — E6 nie zmienia kodu pdi.

## Czego E6 nie obejmuje i co zostaje otwarte

- **Koszt przebiegu cięcia wzrośnie** — dochodzi specyfikacja, dowody i ślad kryteriów. O ile, nie wiem: przebiegów
  cięć nikt dotąd nie mierzył. Pomiar jest płatny i wymaga osobnej zgody właściciela.
- **Zwykłe zadanie z kluczem z trackera w produkcie z trybem pdi** (`docs/project/changes/PROJ-123/`) czerwieni
  bramkę ShipScope z ustalenia 1. To błąd istniejący od kroku C, poza cięciami. Poprawka należy do `ci_for_sdlc`:
  folder z `task.json` to zadanie, nie zmiana. Do decyzji właściciela, bo to inne repozytorium.
- Kodu pdi, kontraktu pdi i polecenia w `phase_run.py` E6 nie zmienia.

## Stan realizacji (2026-11-14)

- E6a scalone (tf#245). E6b i E6c w drugim PR.
- Zmiany względem planu: podgląd (dashboard) nadal pokazuje stare katalogi `.tf/runs/cuts/` jako historię; waga
  cięcia liczy się z wiersza cięcia, bez zamiaru całej zmiany (inaczej jedno słowo w zamiarze podnosiłoby wagę
  każdego cięcia).
- Sprawdzenie po stronie pdi: funkcja `pr_loop._outside_plan` wyczytała z raportu nowego układu obie odłożone sprawy
  (zwykłą i z dopiskiem `[założenie]`); testy repozytorium pdi bez zmian: 1132 zaliczone (`uv run pytest -q`,
  commit `b40dbe8`).
- Niezmierzone: koszt przebiegu cięcia w nowym układzie i zachowanie modelu w całej fazie pdi — testy sprawdzają
  skrypty i pliki, nie przebieg z modelem.
