# Krok F: płynność i podgląd — plan realizacji

Data: 2026-11-14. Krok F planu zmian (`docs/plans/2026-11-12-plan-zmian-os-fabryki.md`, pozycje 11, 13 i 14;
pozycja 15 czeka na decyzję D9). Efekt dla człowieka: **pytanie nie zatrzymuje całości i od razu widać, co czeka na
niego.**

## Stan dziś (sprawdzone w kodzie)

| Obszar | Co jest | Czego brakuje |
|---|---|---|
| co czeka na człowieka | przebieg zapisuje zatrzymanie z kodem i komunikatem (`run_state.py stage … needs`); podgląd ma kolumnę „Czeka na człowieka” i licznik w pasku | osobnej listy z pytaniem, opcjami i rekomendacją; `tf status` w ogóle nie mówi, że zadanie czeka |
| pliki w podglądzie | pliki zadania, robocze, dowody, skany | plików kodu zmienionych w kawałku |
| kawałek zablokowany | `tf task slice <KEY> K2 blocked --reason` zapisuje blokadę; bramka etapu `przeglad` nie przepuszcza zadania z takim kawałkiem | pętla nie używa tej blokady: każde pytanie to STOP całego przebiegu; kawałki nie mają zależności; nie ma zapisu pytań i odpowiedzi |
| przegląd zakresu | `scope-reviewer` daje werdykt „w zakresie / spoza zakresu”; reguła „najwyżej 2 próby na bramkę” jest w treści skilla | etykiet ustaleń (każda uwaga wymusza dziś rundę); limitu rund nie pilnuje skrypt |

## Kawałki

| # | Kawałek | Co powstaje | Testy (najpierw) | Zmiana zachowania pętli |
|---|---|---|---|---|
| F1 | „Czeka na Ciebie” (poz. 14) | `tf status` pod zadaniem: na co czeka, jakie jest pytanie i która opcja jest rekomendowana; w podglądzie wyróżniona lista „Czeka na Ciebie” nad tablicą (zadanie, pytanie, opcje, od kiedy); panel plików pokazuje pliki kodu każdego kawałka (z dowodu weryfikacji); `tf status --open` buduje i otwiera podgląd w dowolnej chwili | `test_task_state.py`: lista z zadaniem czekającym na plan i na STOP; `test_run_state.py`: dane podglądu mają listę oczekujących i pliki kawałka; szablon rysuje listę | nie |
| F2 | przegląd, który się kończy (poz. 13) | `scope-reviewer` oznacza każde ustalenie: **ważne** (do poprawy), **drobne**, **zastane** (było przed zmianą); tylko ważne zaczyna nową rundę, reszta trafia do odłożonych; druga runda ogląda tylko nowy diff; `run_state.py step` odmawia trzeciej rundy kawałka i podaje, co dalej (STOP z kodem) | `test_steps.py` i test konfiguracji agenta: etykiety w prompcie; `test_run_state.py`: trzecia runda → odmowa z podpowiedzią; scenariusz skilla przed zmianą treści | tak, mała: mniej rund; limit był już w treści skilla |
| F3 | kawałek zablokowany zamiast STOP (poz. 11) | zależności w planie (`· po: K1`); `run_state.py block <katalog> K2 --question "…"` zapisuje pytanie i blokuje tylko ten kawałek, a skrypt mówi, który kawałek można robić dalej; gdy nie ma żadnego niezależnego — STOP z listą pytań; `run_state.py answer <katalog> K2 "…"` odblokowuje; pytania i odpowiedzi w `events.jsonl` w katalogu zadania (kto, kiedy, co) | nowy `test_work_events.py`: blokada, wybór następnego kawałka wg zależności, STOP gdy nic niezależnego, odpowiedź, zapis zdarzeń; `test_run_state.py`: lista „Czeka na Ciebie” pokazuje pytanie zablokowanego kawałka | tak — **za przełącznikiem** `loop.blocked_slices` (domyślnie wyłączony), do czasu pomiaru |

Kolejność: F1 → F2 → F3. Każdy kawałek to osobny PR. F1 nie zmienia zachowania pętli, więc idzie pierwszy.

## Decyzje projektowe

- **Źródło listy „Czeka na Ciebie”** to pliki, które już są: `run.json` przebiegu (zatrzymanie, kod, powód)
  i `task.json` (kawałek zablokowany). `tf status` czyta `run.json` wprost — to zwykły JSON w `.tf/runs/<KEY>/`.
- **`events.jsonl` zapisuje decyzje, nie steruje przebiegiem** (korekta 4a planu zmian): stan zostaje w `task.json`
  i `run.json`. Plik leży w katalogu zadania, więc trafia do gita razem z nim.
- **`parked.md` zostaje jak jest.** Plan zmian przewidywał zrobienie z niego widoku zdarzeń; nie robię tego, bo
  dzisiejszy plik działa, czyta go raport cięcia dla pdi, a zamiana nie daje człowiekowi nic nowego.
- **Zależności kawałków są opcjonalne.** Plan bez dopisku `po:` znaczy „kawałki po kolei” — wtedy pytanie w K2
  blokuje K3 i dalsze, czyli jak dziś.
- **Limit rund pilnuje skrypt**, bo reguła bez czujnika jest sugestią (dokument osi, §7). Limit zostaje taki, jaki
  jest dziś w treści skilla: dwie próby na kawałek.
- **`SKILL.md` ma limit 15 000 znaków** i jest na granicy — nowe szczegóły idą do `references/`.

## Poza krokiem F

- Pozycja 15 (podgląd i pytania jako mod w oknie Claude Code) — po decyzji D9.
- Linia stanu w Claude Code („PROJ-123 · etap 4 z 8 · czeka na Ciebie: 1”) — zmienia wygląd sesji każdemu
  użytkownikowi, więc proponuję ją jako opcję włączaną przez człowieka; do decyzji właściciela.
- Powiadomienia (pulpit, telefon) i drugi model potwierdzający ustalenia przeglądu.
- Otwieranie podglądu przy każdym użyciu fabryki poza `/tf` (np. `tf onboard`) — F1 daje `tf status --open`;
  automatyczne otwieranie w innych miejscach dołożę, gdy będzie wiadomo, że nie przeszkadza.

## Pomiar

F2 i F3 zmieniają zachowanie pętli. Po F3 potrzebny jest płatny pomiar na tym samym zestawie historyjek co dotąd
(z włączonym przełącznikiem) — **wymaga osobnej zgody właściciela**. Do tego czasu przełącznik F3 zostaje wyłączony.

## Stan realizacji (2026-11-14)

- F1 w PR tf#247 (z poprawką opisu zatrzymania na karcie podglądu: podwójna kropka i zlane zdania).
- F2 gotowe lokalnie. Limit to dwie rundy kawałka bez decyzji człowieka (tak liczy je dotychczasowy werdykt „próba
  k/2”); po zatrzymaniu i decyzji człowieka kawałek dostaje dwie kolejne. Wznowienie przez `step` czyści teraz cały
  zapis zatrzymania (wcześniej w `run.json` zostawał kod).
- Ryzyko zauważone przy okazji, niezmienione: spis `docs/project/changes/INDEX.md` jest w gicie i przepisuje go
  każdy zapis zadania, więc dwa otwarte naraz PR-y zwykłych zadań mogą mieć w nim konflikt. Zadań cięć to nie
  dotyczy (nie mają wiersza). Usunięcie spisu z gita zmienia układ ustalony w kroku C — do decyzji właściciela.
