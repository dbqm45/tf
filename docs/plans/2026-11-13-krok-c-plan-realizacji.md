# Krok C: plan realizacji — jedno miejsce na zadanie

Data: 2026-11-13. Podstawa: `2026-11-12-plan-zmian-os-fabryki.md` (pozycje 4, 5 i część 14; sekcje 4b, 4c, 4e, 4f)
i `2026-11-12-os-fabryki-od-zadania-do-wdrozenia.md` §5. Decyzje człowieka: D1 (pliki zadania w gicie), D5 (folder
zostaje, archiwizacja po 90 dniach). Status: plan zapisany przed kodem; każdy kawałek to osobny PR, kod metodą TDD.

## Cel

Jedno zadanie ma jeden trwały katalog `docs/project/changes/<KEY>/` w gicie i jeden roboczy `.tf/runs/<KEY>/` poza
gitem. Stan zadania czyta i pisze wyłącznie skrypt. Przerwaną pracę da się wznowić z plików, a „zrobione” znaczy
„jest dowód”.

## Co zastajemy (sprawdzone w repo 2026-11-13)

- Talos pisze wszystko do `.tf/runs/talos/<data>-<slug>/` (`run.json`, `story.md`, `plan.md`, `parked.md`,
  `report.md`); stan trzyma `run_state.py`, raport `run_report.py`. Ścieżka jest w `PUBLIC_API.md`.
- Tryb pdi używa już `docs/project/changes/CHG-n/` z plikami `intent.md`, `plan.md`, `decisions.md`, `release.yaml`
  i `runs/TSK-n.md`; nagłówki tych plików sprawdza `decision_record.py check` względem kontraktu pdi.
- Dashboard Talosa (`run_state.py dashboard`) otwiera się przy starcie przebiegu i ma panel plików.

## Decyzja projektowa D14 — przyjęta przez człowieka 2026-11-13

Dokument osi mówi, że każdy plik etapu ma własny nagłówek ze stanem i skrótami wejść. **Proponuję trzymać ten stan
w `task.json`, a nie w nagłówkach plików.** Powody: pliki `plan.md` i `intent.md` mają już nagłówki sprawdzane przez
kontrakt pdi, więc dopisywanie własnych pól groziłoby jego złamaniem; jeden plik stanu ma jednego pisarza; pliki dla
ludzi zostają czyste. Nazwy pól w `task.json` biorę z OKF (`generated`, `verified`, `status`, `stale_after`).
Zatwierdza tylko człowiek (`tf task approve --by human:<id>`).

## Kawałki

| # | Kawałek | Co powstaje | Testy (najpierw) | Wielkość |
|---|---|---|---|---|
| C1 | stan zadania | `core/factory/task_state.py`: `start <KEY>`, `stage`, `status [--json]`; `task.json` (schemat 1: klucz, tytuł, etap, waga, tryb, daty, wersja schematu); indeks `docs/project/changes/INDEX.md` odświeżany przy każdym zapisie; polecenie `tf task …` | `core/tests/test_task_state.py`: start tworzy katalog i indeks; powtórny start nie nadpisuje; nieznany etap to błąd; etap nie cofa się bez `--force`; indeks ma jeden wiersz na zadanie; klucz spoza wzorca odrzucony | M |
| C2 | kawałki i dowody | `slice <KEY> K1 planned\|implemented\|blocked`, `verify <KEY> K1 --files … [--command …]` samo uruchamia polecenie (domyślnie to z bramki jakości) i zapisuje `evidence/K1-<n>.json` (polecenie, prawdziwy kod wyjścia, SHA, czas, skróty plików); kodu wyjścia nie da się zadeklarować; stan kawałka wyliczany: zweryfikowany / niezweryfikowany / czerwony | brak dowodu → niezweryfikowany; kod ≠ 0 → czerwony; zmiana pliku po dowodzie → niezweryfikowany; `stage` do `przeglad` odrzucony, gdy któryś kawałek nie jest zweryfikowany | M |
| C3 | wejścia i nieaktualność | `artifact <KEY> <plik> --stage … --inputs …` zapisuje w `task.json` skróty wejść i kto wygenerował lub zatwierdził; `check <KEY>` oznacza plik jako nieaktualny, gdy wejście się zmieniło | zmiana `spec.md` po zatwierdzeniu planu → plan nieaktualny; zatwierdzenie tylko przez `human:<id>`; plik pdi z własnym nagłówkiem zostaje nietknięty | M |
| C4 | Talos w nowym układzie | `run_report.py start` zakłada zadanie przez `task_state.py`; trwałe pliki (`story.md` jako `ticket.md`, `plan.md`, `report.md`) w `docs/project/changes/<KEY>/`, robocze w `.tf/runs/<KEY>/`; stara ścieżka czytana dalej przez jedno wydanie MINOR; `PUBLIC_API.md`, `GUIDE.md`, wpis `Deprecated` | testy Talosa na nowym układzie; stary przebieg nadal widoczny w dashboardzie i raporcie; przebieg cięcia pdi (`CHG-n`) bez zmian | M |
| C5 | podgląd | dashboard czyta `task.json` i `INDEX.md`; panel plików pokazuje katalog trwały i roboczy; kawałek niezweryfikowany ma osobny kolor; `tf status` | karta zadania z etapem i stanem kawałków; stary i nowy przebieg na jednej stronie | S–M |

Kolejność: C1 → C2 → C3 → C4 → C5. Po C2 warto powtórzyć pomiar z `docs/evals/2026-11-13-pomiar-bazowy-e0.md`
dopiero wtedy, gdy Talos zacznie używać nowego stanu (po C4).

## Ustalenia

- **Klucz:** numer z trackera (`PROJ-123`), klucz pdi (`CHG-12`, `TSK-57`) albo `T-<RRRRMMDD>-<slug>`; wzorzec
  `[A-Z][A-Z0-9]*-[A-Za-z0-9-]+`.
- **Etapy:** `przyjecie`, `specyfikacja`, `plan`, `realizacja`, `przeglad`, `pr`, `wdrozenie`, `zamkniecie` — w tej
  kolejności; skrypt nie pozwala przeskoczyć do `przeglad` z niezweryfikowanym kawałkiem.
- **Jeden pisarz:** `task.json` i `INDEX.md` zmienia tylko `task_state.py` (zapis przez plik tymczasowy i zamianę).
- **Współistnienie z pdi:** istniejący katalog `CHG-n` nie jest przebudowywany; `task_state.py start CHG-n` dokłada
  do niego `task.json`. Plików pdi skrypt nie zmienia.
- **Zgodność wstecz:** stare przebiegi w `.tf/runs/talos/` są czytane dalej; nowy zapis idzie tylko do nowego układu
  (C4). Zmiana ścieżki to wydanie MINOR z aliasem, nie MAJOR.
- **Poza zakresem kroku C:** zdarzenia (`events.jsonl`, pozycja 11), jeden plik `task.md` dla wagi lekkiej i tryby
  (pozycja 9), specyfikacja Given/When/Then jako bramka (pozycja 6), archiwizacja po 90 dniach (z pozycją 18).

## Ryzyka

| Ryzyko | Ograniczenie |
|---|---|
| złamanie kontraktu pdi przez dopisanie pól do plików zmiany | stan tylko w `task.json`; test z katalogiem `CHG-n` z prawdziwymi nagłówkami |
| dwa układy plików Talosa naraz | jeden skrypt czyta oba; test „stary i nowy przebieg na jednej stronie” |
| rozrost repozytorium projektu o pliki zadań | w gicie tylko małe pliki; surowe logi w `.tf/runs/`; archiwizacja po 90 dniach (D5) |
| skrypt stanu staje się wąskim gardłem pętli | polecenia bez sieci i bez modelu; każde kończy się w ułamku sekundy |
