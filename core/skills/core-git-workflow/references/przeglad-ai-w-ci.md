# Przegląd PR przez AI w CI — wzorzec operacyjny
> przeglądzie względem planu · 6. Publikacja i bramka · 7. Pętla uczenia się · 8. Podział skilla przeglądu

Kryteria przeglądu względem planu i triaż z człowiekiem: skill przeglądu zmiany (pack-it: qa-change-review).
Bezpieczeństwo workflow (uprawnienia, SHA akcji, `env:` zamiast interpolacji): skill CI/CD (pack-it: ops-ci-cd). Ten plik opisuje, jak przegląd AI działa **jako krok CI**.

## 1. Kiedy uruchamiać
- Na zdarzenie, które coś znaczy: otwarcie i aktualizacja PR — nie „co godzinę na wszelki wypadek”.
- Etykieta (np. `ai-review`) albo filtr ścieżek, żeby PR z samą dokumentacją nie płacił za przegląd.
- **Triaż przed przeglądem:** tani krok (liczba i ścieżki plików, rozmiar diffu, etykiety) nadaje PR poziom ryzyka.
  Niski → szybki, tani przebieg; ścieżki krytyczne (auth, płatności, migracje, `infra/`, `.github/`) → mocniejszy
  model i zawsze człowiek. Zapisuj poziom, żeby liczyć koszt per poziom (core-cost-control).
- PR z forka: job się nie uruchamia (warunek `github.event.pull_request.head.repo.full_name == github.repository`),
  bo nie wolno mu dać sekretów ani prawa zapisu (core-agent-security).

## 2. Wejście agenta
- Diff względem bazy z trzema kropkami (`git diff origin/<baza>...HEAD` — tylko zmiany PR). Wymaga
  `actions/checkout` z `fetch-depth: 0`; przy płytkim klonie diff jest pusty, a agent „zatwierdza” nic.
- Tytuł i opis PR przez `env:`, nigdy przez `${{ … }}` w `run:`.
- Z diffu odfiltruj lockfile, kod generowany i zrzuty — koszt i szum.
- Przegląd względem planu: plan wskazuje konwencja (plik raportu kroku zmieniony w PR) z nadpisaniem linią
  `Plan: <ścieżka>` w opisie PR. **Brak planu = neutralny komentarz i kod 0**, nie czerwony check.

## 3. Kontrakt wyjścia
- Raport w stałym kształcie: stały znacznik na początku (np. `<!-- AI-REVIEW-REPORT -->`) i linia
  `- **Werdykt**: …`. Następny krok workflow sprawdza znacznik i werdykt deterministycznie. Model, który
  „improwizuje format”, ma zapalić czerwony check, a nie przejść po cichu.
- Zamiast parsowania tekstu można wymusić JSON: `claude-code-action` z `--json-schema` w `claude_args` zwraca wynik
  w wyjściu kroku `structured_output` (odczyt `fromJSON(steps.<id>.outputs.structured_output).werdykt`).
- Werdykt trzystopniowy:
  - **ZATWIERDZONE** — wszystkie wymiary zaliczone albo najwyżej 2 drobne ostrzeżenia;
  - **WYMAGA UWAGI** — kilka ostrzeżeń lub jedno niekrytyczne niezaliczenie; status zielony z opisem „do triażu”;
  - **ODRZUCONE** — luka bezpieczeństwa, duży dryf od planu, zagrożenie danych, padające albo brakujące obiecane testy.
- Agent w CI nie wysyła formalnego „approve” ani „request changes” — tylko komentarze. Decyduje człowiek.

## 4. Ustalenia
Format, waga (krytyczne / ostrzeżenie / obserwacja), wpływ (niski / średni / wysoki), limit 10 ustaleń i zasada
jednej poprawki — jak w skillu przeglądu zmiany (pack-it: qa-change-review, „Ustalenie”). W CI dodatkowo: sekret znaleziony w kodzie opisujesz bez
wartości (`<UKRYTE: token pasujący do wzorca X>`), bo komentarz PR czyta każdy z dostępem do repo.

## 5. Wymiary przy przeglądzie względem planu
Z planu wyciągnij: pliki z faz, polecenia weryfikacji automatycznej, kryteria ręczne, „Poza zakresem”, kluczowe decyzje.
| Wymiar | Niezaliczone, gdy | Ostrzeżenie, gdy |
|---|---|---|
| Zgodność z planem | zaplanowanej zmiany brak w diffie; duży dryf znaczenia | mały dryf |
| Dyscyplina zakresu | zmiany sprzeczne z „Poza zakresem” | nieszkodliwe dodatki (helper dla zaplanowanego kodu) |
| Bezpieczeństwo i jakość | dowolne ustalenie krytyczne | tylko ostrzeżenia |
| Architektura | złamane granice modułów lub kierunek zależności | — |
| Spójność z sąsiednim kodem | rzadko (gdy coś psuje) | istotne odstępstwo od 1–2 podobnych plików |
| Testy | test obiecany w planie nie istnieje albo pada | nowe zachowanie bez testu, test płytki |
| Kryteria sukcesu | pada lint, build lub typecheck z planu | kryterium ręczne odhaczone bez śladu w kodzie |
Plan definiuje, co znaczy „przetestowane”; nie oceniasz tego, czego plan nie obiecał.

## 6. Publikacja i bramka
- **Bramka żyje w workflow, nie w agencie.** Krok agenta kończy się kodem 0 nawet przy ODRZUCONE; następny krok
  (`if: always()`) czyta werdykt i ustawia status commita o stałym kontekście (np. `ai-review/verdict`), który
  kolejne przebiegi nadpisują. Ochrona gałęzi wymaga tego statusu. Gdy agent padnie, komentarze zostają.
- **Świadome obejście:** etykieta (np. `ai-review-override`) dodana przez człowieka zmienia status na zielony
  z opisem „obejście”. Zdarzenia `labeled`/`unlabeled` uruchamiają tylko tani krok werdyktu, bez nowego przeglądu.
- **Commit raportu przez bota** (gdy raport ma żyć w repo):
  - temat z `[skip ci]`, sprawdzony przed push (`git log -1 --format=%s | grep -F '[skip ci]'`, inaczej przerwij) —
    bez znacznika workflow uruchamia się na własnym commicie w pętli;
  - zawsze nowy commit, nigdy `--amend` (historia przeglądów = ślad audytowy);
  - po commicie z `[skip ci]` check wisi na starym SHA — status ustawiasz jawnie na SHA commita bota.
- **Krok-strażnik na początku:** ostatni commit autorstwa bota albo z `[skip ci]` → pomiń przegląd.
- **Komentarze inline tylko na liniach dodanych w diffie** (hunki `+`) — sprawdź to deterministycznie przed wysłaniem.
  Wysyłaj komentarze pojedynczo, żeby błąd pozycji był głośny; ustalenia bez linii w diffie idą do komentarza
  zbiorczego. [niezweryfikowane: zbiorcze utworzenie review przez API ma według kursu po cichu pomijać komentarze
  z błędną pozycją — sprawdź w dokumentacji REST GitHub przed oparciem się na tym]
- **Deduplikacja:** każdy komentarz bota kończy ukryty znacznik; najpierw publikujesz nowe, potem kasujesz stare
  ze znacznikiem i datą sprzed startu przebiegu. Gdy nowe nie wyszły, stare zostają — nigdy zero informacji.
- Komentarz zbiorczy: werdykt, tabela wymiarów, link do raportu (`blob/<SHA>/<ścieżka>`), najwyżej 5 ustaleń
  po jednej linii.
- `claude-code-action`: limity i narzędzia podajesz w `claude_args` (np. `--model`, `--max-turns`, `--allowedTools`);
  akcję przypinasz do pełnego SHA. Szkielet workflow (pack-it): `.claude/skills/ops-ci-cd/references/przyklady.md`, przykład 4.

## 7. Pętla uczenia się
Co miesiąc: gdzie człowiek tylko przyklepał werdykt AI (zmarnowana uwaga → można poluzować triaż), a gdzie błąd
przeszedł przez zielony przegląd (luka w kryteriach → nowy przypadek w zestawie ewaluacji i poprawka `REVIEW.md`).
Ewaluacja promptu przeglądu: `.claude/skills/core-delivery-lifecycle/references/ai-native-sdlc.md` §5. Koszt i czas per PR i per
poziom triażu na wspólnym panelu.

## 8. Podział skilla przeglądu
Kryteria oceny (co porównać, jak oceniać, kształt ustaleń) trzymaj w osobnym pliku niezależnym od narzędzia,
a mechanikę (skąd diff, gdzie wynik, jak komentować) — w skillu lub workflow. Ten sam plik kryteriów czyta wtedy
`claude-code-action`, własny agent na SDK i człowiek jako checklistę.

Źródła: kurs 10xDevs, ed. 3 (2026), moduł 5, lekcja 3 (przegląd AI w CI) — materiał szkoleniowy (dostęp 2026-10-09);
`anthropics/claude-code-action`, `action.yml` na gałęzi `main` (wejścia `claude_args`, `classify_inline_comments`,
wyjście `structured_output`; dostęp 2026-10-10). Opisane własnymi słowami.
