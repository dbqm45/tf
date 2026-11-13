# Krok D: plan realizacji — specyfikacja, ślad i flagi

Data: 2026-11-13. Podstawa: `2026-11-12-plan-zmian-os-fabryki.md` (pozycje 6, 7, 8, 22) i
`2026-11-12-os-fabryki-od-zadania-do-wdrozenia.md` §6 i §6a. Krok nie wymaga nowej decyzji człowieka. Status: plan
zapisany przed kodem; każdy kawałek to osobny PR, kod metodą TDD.

## Cel

Zadanie ma specyfikację, którą sprawdza skrypt, a nie model: kryteria `AC-n` w formie Zakładając / Gdy / Wtedy, to,
co ma zostać bez zmian, i otwarte pytania. Każde kryterium ma test, a test — commit i dowód. W trakcie realizacji
agent nie zmienia specyfikacji ani zatwierdzonych testów. Nowe zachowanie jest za flagą, której stan poza
środowiskiem testowym zmienia tylko człowiek.

## Co zastajemy (sprawdzone w repo 2026-11-13)

- Stan zadania: `core/factory/task_state.py` (etapy, kawałki z dowodami, pliki zadania z wejściami i zatwierdzeniem).
  Plik zmieniony po zatwierdzeniu blokuje etap `przeglad` i dalsze.
- Lint historyjek `requirements_lint.py` (AC-001…004, STORY-001…003) jest w `packs/pack-it`, a rdzeń nie może
  odwoływać się do nakładek. Talos uruchamia go tylko wtedy, gdy nakładka jest zainstalowana.
- `core/hooks/guard_paths.py` chroni sekrety i konfigurację zabezpieczeń; o plikach zadania nic nie wie.
- `core/hooks/tdd_guard.py` trzyma bieżący stan w `.tf/logs/tdd-state.json`; trwałego dziennika „test był czerwony”
  nie ma.
- Talos zna stopkę `Flag:` i pole `flag`, ale tylko dla cięć pdi. `tf onboard` nie pyta o flagi ani środowiska.

## Kawałki

| # | Kawałek | Co powstaje | Testy (najpierw) | Wielkość |
|---|---|---|---|---|
| D1 | specyfikacja sprawdzana skryptem (poz. 6) | `core/factory/spec_check.py` i `tf spec new <KEY>` (szablon `spec.md` z historyjki), `tf spec check <KEY> [--json]`; reguły: są kryteria `AC-n`, identyfikatory się nie powtarzają, każde ma Zakładając/Gdy/Wtedy (albo Given/When/Then) z jednym „Gdy”, sekcje „Poza zakresem” i „Bez zmian” są wypełnione (albo „brak” z powodem), brak pytań oznaczonych `[blokuje]`; `tf task stage <KEY> plan` i dalsze etapy odrzucone, gdy `spec.md` istnieje i nie przechodzi; Talos pisze `spec.md` przed planem | poprawna specyfikacja → kod 0; brak `Wtedy`, powtórzony `AC-2`, dwa „Gdy”, pusta sekcja, pytanie `[blokuje]` → kod 1 z numerem linii; etap `plan` odrzucony przy błędzie i przepuszczony po poprawce; zadanie bez `spec.md` działa jak dotąd | M |
| D2 | ochrona specyfikacji i testów (poz. 8) | `guard_paths.py`: zapis narzędziem Edit/Write do pliku zadania zatwierdzonego przez człowieka albo do `spec.md` zadania w etapie `realizacja` i dalszych → pytanie o zgodę człowieka z podpowiedzią; `tf task reopen <KEY> <plik> --by human:<id> --reason "…"` zdejmuje zatwierdzenie i zapisuje powód („zmiana wymagań”) | zapis do `spec.md` w etapie `plan` przechodzi, w etapie `realizacja` → `ask`; zatwierdzony plik testu → `ask`; po `reopen` zapis przechodzi, a plan zależny od pliku staje się nieaktualny; plik spoza zadania bez zmian | S |
| D3 | ślad kryterium (poz. 7) | `core/factory/trace_check.py`, `tf trace <KEY> [--md] [--base <gałąź>]`: kryteria z `spec.md` → testy z identyfikatorem `AC-n` w plikach testów zmienionych na gałęzi → commit, który dodał test → kawałek i stan jego dowodu; kod 1, gdy kryterium nie ma testu albo test wskazuje kryterium spoza specyfikacji; etapy `przeglad` i dalsze odrzucone przy błędzie śladu; Talos wkleja tabelę do opisu PR | kryterium bez testu → kod 1; test z `AC-9` spoza specyfikacji → kod 1; pełny ślad → tabela z commitem i stanem dowodu; test poza plikami kawałka → ostrzeżenie „bez dowodu”; zadanie bez `spec.md` → kod 0 z informacją | M |
| D4 | flaga funkcji na historyjkę (poz. 22) | `tf task flag <KEY> set <klucz> [--remove-by <data>]` albo `tf task flag <KEY> none --reason "bez flagi, bo…"`; karta operacyjna w `tf onboard` (`.tf/config/operations.json`: plik konfiguracji flag, środowiska, które jest testowe); `core/factory/flag_check.py`, `tf flag check <KEY> [--base <gałąź>]`: w diffie pliku flag zmiana stanu na środowisku innym niż testowe bez zapisanej decyzji człowieka → kod 1; `tf task flag <KEY> allow <środowisko> --by human:<id>` zapisuje decyzję; Talos: flaga w pierwszym kawałku, testy w obu stanach, stopka `Flag:` | flaga wyłączona wszędzie → kod 0; włączenie na teście → kod 0; włączenie na `prod` bez decyzji → kod 1, po `allow` → kod 0; brak karty albo nieobsługiwany mechanizm → informacja „sprawdź ręcznie”, kod 0; zadanie z `none` i powodem nie wymaga flagi; etap `pr` odrzucony, gdy zadanie nie ma ani flagi, ani powodu | M |

Kolejność: D1 → D2 → D3 → D4. Po D3 warto powtórzyć pomiar (historyjki S1–S3), bo zmienia się pętla Talosa — płatne,
tylko za zgodą człowieka.

## Ustalenia

- **Reguły specyfikacji w rdzeniu** to budowa (trzy części kryterium, wypełnione sekcje) oraz — decyzją człowieka
  z 2026-11-13 — dwie reguły treści: wynik, którego nie da się sprawdzić (SPEC-008), i druga akcja w części Gdy
  (SPEC-004). Pozostałe reguły językowe (szczegół implementacji, kilka akcji w historyjce, pełny słownik) zostają
  w `requirements_lint.py` nakładki pack-it; Talos uruchamia je dodatkowo, gdy nakładka jest zainstalowana.
- **Format `spec.md`:** nagłówek `# Specyfikacja: <tytuł>`, sekcje `## Kryteria` (pozycje `- AC-n: Zakładając …, gdy
  …, wtedy …` albo trzy linie pod identyfikatorem), `## Bez zmian` (strażnicy: co ma działać jak dotąd), `## Poza
  zakresem`, `## Otwarte pytania` (pytanie blokujące ma znacznik `[blokuje]`). Plik bez nagłówka artefaktu — stan
  trzyma `task.json` (decyzja D14).
- **Test wskazuje kryterium identyfikatorem w nazwie albo komentarzu** (`AC-3`), w pliku rozpoznanym jako test
  (katalogi `tests/`, `__tests__/`, `e2e/`, nazwy `test_*.py`, `*.test.*`, `*.spec.*`, `*_test.go`, `*Test.java`).
  Ślad patrzy tylko na pliki zmienione na gałęzi względem bazy, więc `AC-3` innego zadania się nie miesza.
- **„Test był czerwony przed kodem”** trafia do śladu w D3 (decyzja człowieka z 2026-11-13): `tdd_guard` dopisuje
  czerwone uruchomienie do `.tf/logs/tdd-red.jsonl`, `tf task verify` przenosi wpisy plików kawałka do dowodu
  (w gicie), a `tf trace` pokazuje kolumnę „czerwony przed kodem: tak / brak zapisu”. Hook widzi tylko testy
  uruchomione w sesji Claude Code — test puszczony ręcznie w terminalu zostawia „brak zapisu”.
- **Ochrona pyta, nie blokuje na stałe.** Hook zwraca `ask`: człowiek przy klawiaturze może zezwolić, a przebieg bez
  nadzoru zostaje zatrzymany. Obejście przez powłokę (`sed`) wykrywa już `tf task check` (plik zmieniony po
  zatwierdzeniu blokuje etap `przeglad`).
- **Flaga:** kontrola diffu obsługuje plik JSON albo YAML w układzie `środowisko → flaga → stan` lub
  `flaga → środowisko → stan`. Inny mechanizm (zmienne środowiska, usługa) → skrypt mówi wprost, że sprawdzić trzeba
  ręcznie, i nie udaje kontroli. Testów „w obu stanach flagi” skrypt nie wymusza — to reguła w skillu Talosa.
- **Waga lekka i brak flagi:** zadanie bez `spec.md` działa jak dotąd (żadna bramka kroku D go nie dotyczy), dopóki
  pozycja 9 nie wprowadzi wag. Flaga jest wymagana dopiero wtedy, gdy zadanie ma `spec.md`.
- **Przebieg cięcia pdi** (`--task`) zostaje bez zmian, jak w kroku C.
- **Poza zakresem kroku D:** jedno polecenie `/tf` i wagi (pozycja 9), zdarzenia (11), wykonawca testów bez wglądu
  w implementację przy wadze pełnej (§6 pkt 3 — jest już `cleanroom_guard`), usuwanie flagi po wdrożeniu (z poz. 18).

## Ryzyka

| Ryzyko | Ograniczenie |
|---|---|
| dodatkowy etap podnosi koszt i czas przebiegu | `spec.md` z szablonu, sprawdzanie bez modelu; powtórka pomiaru po D3 |
| reguły specyfikacji odrzucają poprawny tekst po polsku lub angielsku | oba zestawy słów kluczowych; testy na obu językach; komunikat z numerem linii |
| ślad nie znajduje testów w nietypowym układzie repozytorium | wzorce plików testów jak w `plan_drift`; nierozpoznany plik to ostrzeżenie z nazwą, nie cicha zgoda |
| ochrona plików przeszkadza człowiekowi w poprawce specyfikacji | `ask` zamiast `deny`; `tf task reopen` w jednym poleceniu |
| kontrola flag daje fałszywe poczucie bezpieczeństwa przy mechanizmie, którego nie rozumie | brak karty albo nieobsługiwany układ → jawne „sprawdź ręcznie” |
