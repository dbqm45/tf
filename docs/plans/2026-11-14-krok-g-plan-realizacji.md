# Krok G: wejście i wyjście — plan realizacji

Data: 2026-11-14. Krok G planu zmian (`docs/plans/2026-11-12-plan-zmian-os-fabryki.md`, pozycje 16, 17 i 18).
Efekt dla człowieka: **podaje numer zgłoszenia z Jiry, a fabryka prowadzi zadanie do PR z opisem „jak sprawdzono,
ryzyko, jak cofnąć”, pilnuje sprawdzenia po wdrożeniu i zamyka zadanie.**

Decyzje właściciela z 2026-11-14: **D4 — pierwszy tracker to Jira**; **D6 — tryb Auto nie scala sam, nie teraz**
(zapisane na przyszłość jako dobry kierunek).

## Stan dziś (sprawdzone w kodzie)

| Obszar | Co jest | Czego brakuje |
|---|---|---|
| wejście z trackera | `intake.py resolve` rozpoznaje numer zgłoszenia i mówi modelowi: odczytaj narzędziem podłączonym w sesji albo poproś o wklejenie treści (`ticket_next`) | pobrania zgłoszenia skryptem, bez modelu |
| opis PR | pętla składa go sama z listy w SKILL.md (historyjka, kawałki, ślad kryteriów, odłożone, triaż ryzyka) | stałych pól „jak sprawdzono”, „ryzyko”, „jak cofnąć”; opis pisze model, więc bywa różny |
| karta operacyjna | `.tf/config/operations.json` ma sekcje `tracker` i `flags` (zakłada je `tf onboard` i `intake.py tracker`) | części o wdrożeniu: jak cofnąć, test dymny, co zatwierdza człowiek |
| po scaleniu | zadanie ma w `task.json` etapy `wdrozenie` i `zamkniecie` | pętla kończy na etapie `pr`; nikt nie zapisuje wyniku wdrożenia ani zamknięcia |
| ustalenia przeglądu | etykiety `[ważne]` / `[drobne]` / `[zastane]` (krok F2); drobne i zastane trafiają do odłożonych | zapisu, jaka kontrola złapie ważne ustalenie następnym razem |

## Kawałki

| # | Kawałek | Co powstaje | Testy (najpierw) |
|---|---|---|---|
| G1 | zgłoszenie z Jiry skryptem (poz. 16) | `run_report.py start --key EBO-1236 --from-tracker`: skrypt czyta zgłoszenie przez Jira REST (tylko odczyt) i zapisuje `ticket.md` ze źródłem, adresem i datą; dane dostępu i adres Jiry wyłącznie ze zmiennych środowiska; bez danych dostępu — jasny komunikat i dotychczasowa droga (wklejenie). `intake.py resolve` dla numeru z Jiry podaje to polecenie jako następną czynność | atrapa serwera Jiry na `localhost` (bez sieci): poprawne zgłoszenie → `ticket.md` z tytułem, opisem i kryteriami; brak zmiennych, błąd 401/404, przekroczony czas → kod 2 z komunikatem i bez pliku; treść dłuższa niż limit jest ucinana; adres spoza `https://` (poza `localhost`) odrzucony; token nie pojawia się w pliku ani na wyjściu |
| G2 | opis PR z trzema polami (poz. 17) | `run_state.py pr-body <katalog> --base <gałąź>` składa opis PR z plików zadania: historyjka, kawałki i commity, ślad kryteriów, **Jak sprawdzono** (dowody weryfikacji i skany), **Ryzyko** (triaż ryzyka i waga), **Jak cofnąć** (z karty operacyjnej; domyślnie `git revert` i wyłączenie flagi), odłożone sprawy, założenia. Pętla podaje go przez `--body-file` | pola obecne zawsze, także bez karty i bez flagi; treść z dowodów i z karty; kawałek bez dowodu jest w opisie nazwany wprost |
| G3 | karta wdrożenia i sprawdzenie po scaleniu (poz. 17) | sekcja `deploy` karty operacyjnej (jak cofnąć i ile to trwa, test dymny, co zatwierdza człowiek, polecenie logów) — pyta o nią `tf onboard`; `tf task deployed <KEY> [--version X]` uruchamia test dymny z karty, zapisuje wynik i etap `wdrozenie`; wynik czerwony → komunikat z pytaniem „wycofać?” i krokiem cofnięcia z karty. Produkcję zatwierdza człowiek; bez karty fabryka kończy na scaleniu i mówi to wprost | karta zakładana i uzupełniana bez nadpisywania; zielony i czerwony test dymny; brak karty → komunikat, nie błąd; `tf status` pokazuje zadanie czekające na decyzję o wycofaniu |
| G4 | zamknięcie zadania (poz. 18) | `tf task close <KEY>`: sprawdza, że zmiana jest scalona, przypomina o dacie usunięcia flagi, wymaga dla każdego ważnego ustalenia przeglądu zapisu „kontrola, która to złapie” (test, hook, reguła albo powód jej braku), dopisuje lekcję do `docs/project/lessons.md`, ustawia etap `zamkniecie` | odmowa zamknięcia niescalonej zmiany i ustalenia bez kontroli; lekcja dopisana raz; zamknięte zadanie znika z listy „w toku” |

Kolejność: G1 → G2 → G3 → G4. Każdy kawałek to osobny PR.

## G2 — plan realizacji (zapisany przed kodem)

Polecenie `run_state.py pr-body <katalog> [--base <gałąź>]` zapisuje opis w `.tf/runs/<KEY>/pr-body.md` (poza gitem)
i drukuje ścieżkę z podpowiedzią `--body-file`. Skrypt niczego nie wypycha i nie zakłada PR.

| Sekcja opisu | Skąd |
|---|---|
| Historyjka | tytuł i klucz zadania, wiersz „Źródło” z `ticket.md`, katalog zadania |
| Kawałki | `plan.md` + stan kawałka z `tf task` + commit ze stopką „Kawałek K<n>” (`git log <baza>..HEAD`) |
| Ślad kryteriów | `trace_check.py --md`; zadanie bez `spec.md` → jedno zdanie zamiast tabeli |
| **Jak sprawdzono** | ostatni dowód każdego kawałka (`evidence/K<n>-<m>.json`: polecenie, kod wyjścia, data); kawałek bez dowodu albo z czerwonym dowodem nazwany wprost; werdykt skanu bezpieczeństwa; wynik `plan_drift` |
| **Ryzyko** | waga zadania i wynik `risk_triage.py --md` |
| **Jak cofnąć** | `deploy.rollback` z karty operacyjnej, gdy jest (sekcję zakłada G3); zawsze `git revert` commita scalenia; flaga zadania: „wyłącz flagę” albo zapisany powód jej braku |
| Odłożone do decyzji | `parked.md` |
| Założenia | wiersze planu i specyfikacji z `[założenie` |

- Pliki: `core/skills/tf/scripts/run_state.py` (funkcje w istniejącym skrypcie — nowy plik wymagałby nowej reguły
  uprawnień), `core/tests/test_pr_body.py`, `core/tests/skill_evals/tf.json`, `core/skills/tf/SKILL.md` (§4, krok 3 —
  krócej niż dziś), `core/guide/PETLA.md`.
- Kolejność: scenariusz ewaluacji → test (czerwony) → kod → treść skilla → bramka skilla → pełne sprawdzenie.
- Koszt przebiegu zostaje w `report.md` (powstaje po PR); w opisie PR jest jedna linia z `run.json`, gdy koszt jest
  już policzony.
- Treść z plików zadania i z karty to dane: trafia do opisu jako tekst, skrypt niczego z niej nie uruchamia.

## Decyzje projektowe

- **Skrypt, nie model, czyta tracker** (dokument osi, §9): model dostaje gotowy plik. Treść zgłoszenia to dane —
  `ticket.md` ma tę samą linię ostrzeżenia co dziś, a skrypt niczego z treści nie wykonuje.
- **Tylko odczyt i tylko adres ze zmiennej.** Skrypt woła wyłącznie adres z `JIRA_BASE_URL`, przez HTTPS, jednym
  żądaniem `GET`. Adres z karty operacyjnej nie decyduje, dokąd idzie token — to wniosek z przeglądu bezpieczeństwa:
  plik w repozytorium może zmienić cudzy pull request. Niczego w Jirze nie zmienia (komentarz i status to osobny, późniejszy moduł ze zgodą
  na każdą akcję).
- **Dane dostępu:** `JIRA_BASE_URL` oraz `JIRA_EMAIL` z `JIRA_API_TOKEN` (Jira Cloud) albo sam `JIRA_TOKEN`
  (Data Center). Fabryka ich nie zapisuje; `.env*` nadal nie czyta. [założenie: nazwy zmiennych — do zmiany, jeśli
  w firmie obowiązują inne]
- **Fabryka niczego nie instaluje.** Droga przez wklejenie treści i przez serwer MCP podłączony w sesji zostaje;
  skrypt jest trzecią drogą, pierwszą wybieraną, gdy są zmienne.
- **Opis PR składa skrypt**, bo to mechanizm zamiast instrukcji: te same pola w każdym PR i mniej pracy modelu.
- **Po czerwonym teście dymnym fabryka pyta, nie cofa sama** — zgodnie z D6 (bez samodzielnych działań na
  produkcji).
- **Przegląd bezpieczeństwa przed scaleniem G1** (sieć, dane dostępu): agent `security-reviewer`.

## Poza krokiem G

- Zapis do Jiry (komentarz z linkiem do PR, zmiana statusu) i inne trackery (GitHub Issues, Linear).
- Wiedza o projekcie z Confluence (`tf po setup`).
- Obserwacja pipeline'u wydania w CI projektu — G3 zapisuje wynik testu dymnego uruchomionego poleceniem z karty.
- Zapadki jakości i zbiór „incydent → test recenzenta” z pozycji 18 — osobny kawałek po G4, gdy będą pierwsze
  zamknięte zadania.
- Automatyczne scalanie zmian niskiego ryzyka (D6).

## Czego nie da się sprawdzić bez Ciebie

- Prawdziwej Jiry: testy używają atrapy. Pierwsze pobranie z Twojej instancji trzeba zrobić u Ciebie, ze zmiennymi
  środowiska — podam jedno polecenie do sprawdzenia.
- Pola „kryteria akceptacji”: w Jirze bywa polem własnym o innej nazwie w każdej firmie. Skrypt weźmie je z opisu,
  a nazwę pola własnego da się wpisać w karcie operacyjnej.

## Stan realizacji (2026-11-14)

- G1 gotowe. Przegląd `security-reviewer` znalazł jedno ważne ustalenie i trzy mniejsze; wszystkie poprawione
  i pokryte testami: dane dostępu idą tylko pod adres ze zmiennej środowiska (karta z innym adresem → odmowa), nagłówki
  z treści zgłoszenia nie stają się nagłówkami `ticket.md`, adres lokalny nie idzie przez proxy, błędy połączenia
  i niepoprawne dane dostępu kończą się komunikatem zamiast śladu wyjątku, a ucinany jest opis, nie kryteria.
- Niezweryfikowane: pobranie z prawdziwej Jiry (Cloud i Data Center) — testy używają atrapy serwera.
- G1 scalone (tf#252).
- G2 gotowe: `run_state.py pr-body` (22 testy w `test_pr_body.py`). Dodatek względem planu: tekst z zewnątrz (tytuł
  zgłoszenia, karta, sprawy odłożone) nie powiadamia ludzi przez `@nazwa` i nie osadza obrazów w opisie PR. Test
  treści skilla T-12 sprawdza teraz polecenie `pr-body` zamiast ręcznego `risk_triage.py --md` — triaż w opisie
  sprawdza test PB-8. Niezweryfikowane: jak model używa polecenia w prawdziwym przebiegu (wymaga płatnego pomiaru).
