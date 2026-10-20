---
name: qa-change-review
description: Użyj przy przeglądzie planu przed kodem albo kodu względem planu — dryf, waga, triaż, werdykt.
metadata:
  przeglad: 2027-10-10
  katalog: "Użyj, gdy trzeba sprawdzić plan kroku, zanim agent zacznie kodować (spójność, ugruntowanie w repo, weryfikacja ryzykownych twierdzeń, wymiary, werdykt), albo implementację względem zatwierdzonego planu po fazie lub przed scaleniem (trzy zbiory plików, dryf, nadmiar i braki, bezpieczeństwo i wzorce, kryteria), a potem przejść ustalenia z człowiekiem (macierz waga × wpływ, triaż z decyzjami, zapis jako lekcja). Nie do procesu PR i konfiguracji przeglądu przez usługę lub CI (core-git-workflow), samego bezpieczeństwa (agent security-reviewer), czytelności kodu bez planu (eng-clean-code) ani przepytywania człowieka przed planem (core-plan-interview)."
  slowa: "przegląd planu, sprawdź plan, review planu, czy plan zadziała, przegląd implementacji, zgodność z planem, dryf od planu, implementacja vs plan, przed scaleniem, ustalenia przeglądu, triaż ustaleń, co naprawić teraz, werdykt przeglądu, agent zrobił coś innego niż w planie, pliki spoza planu"
---

# Przegląd zmiany względem planu

Zły plan kosztuje godziny pracy, przegląd planu — minuty. **Przegląd planu** pyta „czy ten plan zadziała?”,
**przegląd implementacji** — „czy zbudowaliśmy to, co zaplanowaliśmy, i czy da się to bezpiecznie scalić?”.
Agent przygotowuje raport i prowadzi triaż; werdykt i decyzje należą do człowieka. Ustaleń nie szuka się na siłę:
dobry plan lub kod daje krótki raport.

## Wejście
- Raport kroku `docs/project/06-delivery/NNN-*.md` z planem (stan końcowy, poza zakresem, fazy, kryteria)
  i sekcją „Postęp” (szablon `delivery` w core-project-record).
- Badanie lub przeramowanie obok raportu kroku, jeśli powstały.
- `docs/project/lessons.md` — ustalenie łamiące zapisaną lekcję ma wyższą wagę.
- Wcześniejszy raport przeglądu → wznów od triażu (ustalenia z decyzją `OCZEKUJE`).

## Tryb A — przegląd planu (przed kodem)
1. **Spójność wewnętrzna** (tu jest najwięcej trafień):
   - sprzeczność — ograniczenie opisane na górze, a ignorowane w fazach; punkt „poza zakresem” wraca w fazie;
   - obietnica bez fazy — kryterium stanu końcowego, którego żadna faza nie buduje;
   - złamany kontrakt — faza B potrzebuje identyfikatora lub pola, którego wynik fazy A nie zwraca; decyzja,
     którą wykonawca musiałby zgadnąć;
   - „Postęp” ↔ fazy — każde kryterium ma swój wiersz, pola wyboru są tylko w „Postępie”.
2. **Ugruntowanie** (sam, bez wykonawców): istnienie co najmniej 5 ścieżek z planu, `grep` nazw funkcji i kluczy,
   zgodność TL;DR z treścią. Wynik jedną linią, np. `Ugruntowanie: 5/5 ścieżek, 3/3 symbole, TL;DR zgodne z planem`.
3. **Weryfikacja w kodzie** (pomijana w trybie szybkim): 3–5 najbardziej ryzykownych twierdzeń planu → jeden
   wykonawca (np. `scout`) z trzema zadaniami: potwierdź lub obal każde twierdzenie z `plik:linia`; znajdź innych
   wywołujących zmieniane funkcje (zasięg, którego plan nie zna); sprawdź, czy istniejący kod już rozwiązuje to,
   co plan buduje od nowa.
4. **Wymiary:**
   - zgodność ze stanem końcowym — czy wszystkie kryteria mogą przejść, a cel mimo to nie zostać osiągnięty?
   - oszczędność — czy cel jest osiągalny bez tej fazy; abstrakcja „na zapas”; zmiany „przy okazji”;
   - dopasowanie do architektury — nowy wzorzec obok istniejącego, kierunek zależności, „refaktoruj według potrzeb”;
   - ślepe plamy — ścieżki błędów, wycofanie, koszt, zmiana wartości domyślnych, testy, granice bezpieczeństwa;
   - wykonalność — konkretne ścieżki i polecenia weryfikacji, brak TODO.
5. **Werdykt:** **gotowy** / **do poprawy** (konkretne poprawki planu) / **do przemyślenia** (problem z podejściem —
   wróć do badania lub przeramowania).

## Tryb B — przegląd implementacji (po fazie albo przed scaleniem)
1. **Zakres z gita:** commity od zatwierdzenia planu (`git log --since`, `git diff <baza>...HEAD --stat`) i trzy
   zbiory plików: w planie i w diffie (sprawdź treść) · w diffie bez planu (**NADMIAR** — zmiana nieplanowana) ·
   w planie bez diffu (**BRAK**). Główna sesja trzyma plan i listę plików, nie ich treść.
2. **Dwa niezależne przebiegi** (równolegle, w osobnych kontekstach):
   - **dryf** — dla każdej planowanej zmiany: ZGODNE / DRYF / BRAK / NADMIAR, z cytatem planu i `plik:linia`;
   - **bezpieczeństwo, jakość, wzorce** — wstrzyknięcia, sekrety, autoryzacja na granicach; N+1 i brak
     stronicowania; obsługa błędów na granicach zewnętrznych, wyścigi; destrukcyjne operacje na danych bez ścieżki
     migracji; porównanie z 1–2 podobnymi plikami w repo (tylko istotne różnice; przy ≤ 3 plikach krótko).
3. **Kryteria:** uruchom polecenia automatyczne z planu i pokaż wynik dosłownie. Kryterium ręczne odhaczone
   w „Postępie” bez śladu w diffie → ustalenie „odhaczone bez sprawdzenia”.
4. **Kolejność czytania diffu dla człowieka:** zakres → granice ryzyka (auth, zapis danych, migracje, API
   zewnętrzne, konfiguracja) → lokalne wzorce → testy (czy test złapałby błąd, którego chcemy uniknąć; zielony test
   agenta to informacja, nie dowód — qa-spec-first-testing).
5. **Wymiary:** zgodność z planem · dyscyplina zakresu · bezpieczeństwo i jakość · architektura · spójność wzorców
   · kryteria sukcesu. Plan definiuje, co znaczy „przetestowane” — nie oceniasz tego, czego nie obiecał, a jego
   „poza zakresem” nie jest rozrostem zakresu.
6. **Werdykt:** **zatwierdzone** / **wymaga uwagi** / **odrzucone** (każde krytyczne niezaliczenie wymiaru).

## Ustalenie
`ID · waga · wpływ · wymiar · miejsce · szczegół z dowodem · poprawka`
- **Waga** — jak źle, jeśli zignorujemy: krytyczne / ostrzeżenie / obserwacja.
- **Wpływ** — jak trudna decyzja: niski (poprawka oczywista i lokalna) / średni (prawdziwy kompromis) /
  wysoki (szeroki zasięg: dane, kontrakt, produkt). Waga i wpływ są niezależne.
- **Miejsce** — `plik:linia` albo sekcja planu.
- Domyślnie jedna poprawka. Dwie tylko przy prawdziwym kompromisie; wtedy każda ma: podejście · mocną stronę ·
  koszt · pewność · czego nie sprawdzono, i dokładnie jedna jest rekomendowana.
- Najwyżej 10 ustaleń — podobne scal („6 plików łamie konwencję nazw” = jedno ustalenie). Sekret opisujesz bez
  wartości.

## Macierz waga × wpływ (heurystyka)
| Waga \ wpływ | niski | średni | wysoki |
|---|---|---|---|
| krytyczne | napraw teraz | napraw ostrożnie | zatrzymaj się, zawęź poprawkę |
| ostrzeżenie | napraw albo pomiń | zależy od kontekstu | zwykle wymaga planowania |
| obserwacja | zwykle pomiń | notatka albo lekcja | sprawdź, czy problem nie występuje w wielu miejscach |

## Triaż (po kolei, od krytycznych)
Dla każdego ustalenia człowiek wybiera decyzję:
- **napraw teraz** — pokaż przed/po, potwierdź, minimalna zmiana;
- **napraw inaczej** — podejście człowieka;
- **pomiń**;
- **akceptuj ryzyko** — z uzasadnieniem;
- **odrzuć** — ustalenie błędne, z uzasadnieniem;
- **zapisz jako lekcję** — wpis do `docs/project/lessons.md` wstępnie wypełniony z ustalenia (kontekst = miejsce,
  problem = szczegół); regułę i zakres uzupełnia człowiek (format lekcji: core-project-record). Potem **zawsze**
  pytanie „zastosować też poprawkę w kodzie?” — nie decydujesz za człowieka.
Nie każde ustalenie trzeba naprawić. Po każdej decyzji aktualizuj zapisany raport.

## Zapis
- `docs/project/07-review/<data>-przeglad-planu-<krok>.md` albo `…-przeglad-impl-<krok>[-fN].md`, szablon
  `review` (core-project-record) z kolumnami Wpływ i Decyzja oraz linią „Ugruntowanie”.
- Decyzje: `OCZEKUJE` / `NAPRAWIONE` / `POMINIĘTE` / `RYZYKO PRZYJĘTE` / `ODRZUCONE` / `LEKCJA`.
- Poprawki odłożone → „Otwarte pytania” raportu kroku.
- Większa zmiana: zapisz raport, daj człowiekowi przeczytać go spokojnie, triaż w kolejnej rozmowie.
- Ten sam wzorzec w CI (werdykt jako bramka workflow, komentarze inline): core-git-workflow,
  `.claude/skills/core-git-workflow/references/przeglad-ai-w-ci.md`.

## Przykład
**Sytuacja:** przegląd implementacji kroku „zapis zaakceptowanych fiszek”, faza 2. Trzy zbiory: 6 plików zgodnych,
NADMIAR `src/lib/format.ts` (helper dla zaplanowanego kodu), BRAK — żaden.
**Raport (fragment):**
```
Ugruntowanie: 6/6 ścieżek, 4/4 symbole, TL;DR zgodne z planem · npm test → 48 passed
| ID | Waga | Wpływ | Wymiar | Miejsce | Ustalenie | Decyzja |
| F1 | krytyczne | niski | bezpieczeństwo | api/cards/save.ts:18 | endpoint zapisu omija wspólny strażnik autoryzacji | NAPRAWIONE |
| F2 | obserwacja | wysoki | spójność | db/schema.ts:40 | nowa nazwa statusu w bazie (front, backend, dane historyczne) | POMINIĘTE (notatka) |
| F3 | ostrzeżenie | niski | wzorce | actions/deck.ts:12 | ręczne sprawdzanie userId zamiast strażnika | LEKCJA + NAPRAWIONE |
Werdykt: wymaga uwagi → po triażu zatwierdzone
```
Więcej (przegląd planu, dobry plan bez ustaleń): `references/przyklady.md`.

## Checklista
- [ ] tryb wybrany (plan / implementacja); wejście przeczytane, lekcje uwzględnione
- [ ] plan: spójność, ugruntowanie (linia z liczbami), ryzykowne twierdzenia sprawdzone w kodzie, wymiary
- [ ] implementacja: trzy zbiory plików, dryf i bezpieczeństwo osobno, kryteria uruchomione, wynik dosłownie
- [ ] każde ustalenie z wagą, wpływem, miejscem i dowodem; najwyżej 10
- [ ] triaż z decyzją człowieka przy każdym ustaleniu; lekcja zawsze z pytaniem o poprawkę
- [ ] raport w `07-review/`; werdykt należy do człowieka

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 2, lekcje 2–3 (przegląd planu, przegląd implementacji, triaż) i moduł 5,
  lekcja 3 (przegląd w CI) — materiał szkoleniowy (dostęp 2026-10-09).
- Google Engineering Practices, „What to look for in a code review” — google.github.io/eng-practices (dostęp 2026-10-10).
- Konwencje fabryki: core-project-record (raport kroku, „Postęp”, lekcje), core-git-workflow (PR, `REVIEW.md`).
Opisane własnymi słowami.
