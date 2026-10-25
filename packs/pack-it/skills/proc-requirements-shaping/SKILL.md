---
name: proc-requirements-shaping
description: Użyj, gdy z pomysłu trzeba zrobić wymagania (PRD) — MVP w budżecie, pusty CRUD, reguła biznesowa.
metadata:
  przeglad: 2027-10-10
  katalog: "Użyj, gdy pomysł albo większą zmianę w istniejącym systemie trzeba zamienić w kontrakt wymagań (PRD) przed architekturą — sesja pytań w fazach (problem, dostęp, MVP, wymagania FR, wyzwanie dla każdego wymagania, reguła biznesowa jednym zdaniem, ramy i „poza zakresem”), próg „MVP za duże” jako budżet czasu z briefu, wykrywanie pustego CRUD, wymagania jakości bez mechanizmu, otwarte pytania zamiast domysłów, tryb greenfield i brownfield (delta), skrypt requirements_lint.py. Nie do decyzji, czy i co warto budować (proc-product-discovery), mechaniki rund pytań (core-plan-interview), kryteriów akceptacji jako testów (qa-spec-first-testing) ani planu projektu z kosztem dla sponsora (proc-project-planning)."
  slowa: "PRD, wymagania produktu, spisz wymagania, dokument wymagań, zakres MVP, pierwsza wersja, za duże MVP, pusty CRUD, reguła biznesowa, kształtowanie zakresu, wymagania funkcjonalne, FR, historyjki, poza zakresem, wymagania zmiany, mam pomysł na aplikację, product requirements, to nie są wymagania, przepisać wymagania, wymaganie z technologią, wymagania jakości, recenzent PRD"
---

# Kształtowanie wymagań (PRD) — od pomysłu do kontraktu

Agent **prowadzi rozmowę, ale nie jest autorem**. Nie dopisuje wizji, wymagań ani reguł, których człowiek nie
powiedział. Wartość skilla to kolejność i kształt pytań. Pytanie bez odpowiedzi trafia do „Otwartych pytań”
z adresatem — nigdy do treści jako domysł. Wynik to kontrakt bez decyzji technicznych, z którego korzysta
architektura (B2 w core-delivery-lifecycle).

## Kiedy
- Pomysł na produkt albo większa zmiana w działającym systemie, zanim powstanie architektura lub plan.
- Na ścieżce skróconej (core-delivery-lifecycle) ta sesja zastępuje fazy 1 i 3 w jednym dokumencie.
- Przy każdej późniejszej większej zmianie zakresu wykonaj **mini-sesję** tej procedury dla samej delty.

Czy w ogóle warto to budować (wynik, szanse, eksperymenty) — najpierw proc-product-discovery.

## Ustawienie: budżet czasu MVP
Jedyny próg „MVP za duże” to **budżet czasu z briefu**, nie stała z tego skilla. Na początku sesji zapytaj
człowieka i zapisz w `01-discovery/brief.md`, sekcja „Ograniczenia”:
```
- Budżet czasu MVP: 3 tygodnie            # ustala człowiek (np. 4 tygodnie po godzinach, 2 sprinty zespołu)
- Szacunek przepływu MVP: 5 tygodni       # po fazie 3, z uzasadnieniem
- Koszt potwierdzony: 2026-10-10, właściciel produktu przyjmuje 5 tygodni   # tylko gdy szacunek > budżet
```
Podawaj obie wartości w tej samej konwencji (dni robocze, tygodnie, miesiące). Liczba kroków użytkownika
i liczba integracji przed pierwszą wartością to **sygnały do rozmowy**, nie progi.

## Tryb
Sprawdź repozytorium: historia gita albo lockfile → **brownfield** (wymagania jako delta); sam manifest bez
historii → niejednoznaczne, zapytaj; nic → **greenfield**. Potwierdź z człowiekiem i zapisz w briefie
(„Typ projektu”). Różnice brownfield w każdej fazie: `references/przyklady.md`.

## Fazy sesji
Każda faza: jedno pytanie otwarte → 3–5 **szarych stref** jako opcje z rekomendacją (plus „nie wiem”) →
potwierdzenie → zapis. Rundy pytań prowadzisz wg core-plan-interview (tylko pytania niezależne w jednej rundzie).

1. **Problem.** Ból, konkretna osoba (rola, nie „użytkownicy”), moment, w którym boli, i koszt dziś.
   Wyzwanie: „co musiałoby być prawdą, żeby to był zły problem do rozwiązania?”.
   Brownfield: co istnieje, kto tego używa, co boli i **co nie może się zepsuć**.
2. **Dostęp.** Logowanie, profil lokalny, klucz albo brak; role i kto co widzi.
   Brownfield: obecny model dostępu i czy zmiana go dotyka.
3. **MVP.** Pierwszy przepływ krok po kroku, powtórzony człowiekowi jako lista numerowana, i szacunek.
   Szacunek ponad budżet czasu → **nazwij drogie elementy** i zaproponuj cięcia:
   - usuń element X z pierwszej wersji (do „Poza zakresem”);
   - integrację zastąp czynnością ręczną albo importem pliku;
   - jeden użytkownik zamiast zespołów i ról;
   - jedna platforma zamiast webu i aplikacji mobilnej.
   Dłuższy termin jest dozwolony tylko jako świadoma decyzja: linia „Koszt potwierdzony” z datą i osobą.
   Brownfield: najmniejsza zmiana, która dowodzi poprawy, i zasięg rażenia (co jeszcze dotyka).
4. **Wymagania.** Każde w formacie `FR-NNN: <aktor> może <zdolność>. Priorytet: must|nice`
   (brownfield dodatkowo `Zmiana: nowe|zmienione|zachowane`). Każda historyjka `US-NN` ma co najmniej jeden
   scenariusz `AC-n` w Given/When/Then (Zakładając, że / Gdy / Wtedy) i **jedną akcję**: czasownik z obiektem
   w kroku Gdy, a warianty danych idą do Zakładając. Więcej akcji (spójnik między czasownikami, kilku aktorów,
   różne akcje w scenariuszach) albo tytuł od warstwy (BE:, API:) → podział przed zapisem wg proc-agile
   (`.claude/skills/proc-agile/references/mapa-i-dzielenie.md`):
   ```
   ### US-02: Klient stosuje kod rabatowy
   Jako klient chcę użyć kodu rabatowego, aby zapłacić mniej.
   - AC-1: Zakładając, że kod RABAT10 jest aktywny
     Gdy klient zastosuje kod RABAT10
     Wtedy widzi cenę obniżoną o 10%
   ```
5. **Wyzwanie dla każdego FR** (osobna runda). Dla każdego wymagania: „co musiałoby być prawdą, żeby to
   wymaganie szkodziło?” — 2–4 kontrargumenty z domeny, „bez kontrargumentu” jako ostatnia opcja. Wynik zapisz
   pod wymaganiem (kolumna lub linia „Wyzwanie”).
6. **Reguła biznesowa jednym zdaniem** — decyzja, którą aplikacja podejmuje sama i która odróżnia ją od listy
   rekordów. Gdy z odpowiedzi wychodzi „użytkownik dodaje, edytuje i usuwa rekordy”, nazwij to wprost
   **pustym CRUD** i pokaż kształty reguły do wyboru:
   rekomendacja · priorytetyzacja · klasyfikacja · walidacja · ocena (scoring) · przepływ stanów · obliczenie.
   Człowiek może świadomie zostać przy CRUD — wtedy zapis „brak reguły domenowej” w „Otwartych pytaniach”.
   Brownfield, zmiana czysto techniczna (migracja, wydajność): zapisz „bez zmiany reguły domenowej” i pomiń ten test.
7. **Wymagania jakości i ramy.** Jakość jako własność mierzalna z zewnątrz, bez mechanizmu:
   | Zamiast (mechanizm) | Zapisz (zachowanie) |
   |---|---|
   | „limit per IP w Redisie po stronie serwera” | „jeden klient nie wyśle więcej niż 100 żądań na minutę; nadmiar dostaje czytelny komunikat” |
   | „spinner podczas zapisu” | „użytkownik w ciągu 1 s widzi, że zapis trwa, i nie może go wysłać drugi raz” |
   | „hasła w bcrypt” | „wyciek bazy nie ujawnia haseł w postaci jawnej” (mechanizm: arch-threat-modeling) |
   Do tego typ produktu, skala, termin i **„Poza zakresem”** — funkcjonalne i jakościowe (np. „bez trybu
   offline”). Preferencje technologiczne człowieka zapisz w osobnym bloku „Do decyzji o stacku”
   (arch-tech-selection), nie w wymaganiach.

## Bramka miękka (przed zapisem)
Sprawdź i nazwij każdą lukę razem z jej konsekwencją:
- [ ] dostęp ustalony;
- [ ] reguła biznesowa jednym zdaniem (albo świadomie zapisany CRUD);
- [ ] przepływ MVP w budżecie czasu albo zapisane „Koszt potwierdzony”;
- [ ] „Poza zakresem” ma co najmniej jedną pozycję;
- [ ] (brownfield) zapisane, jakie zachowanie zostaje bez zmian.
Człowiek może przyjąć lukę — trafia wtedy do „Otwartych pytań” z adresatem i informacją „blokuje: tak/nie”.

## Zapis
- `01-discovery/brief.md` (szablon core-project-record): problem, persona, cele z miarą (**główne**,
  **drugorzędne**, **ochronne** — czego nie wolno pogorszyć), zakres i „Poza zakresem”, typ projektu, budżet czasu.
- `03-requirements/requirements.md`: sekcje „Wymagania funkcjonalne” (FR z wyzwaniem), historyjki, „Reguła
  biznesowa” (pierwsza linia = jedno zdanie), atrybuty jakości, dostęp, „Poza zakresem”, „Do decyzji o stacku”.
  Brownfield dodatkowo: „Obecny system” i „Zachowane zachowanie”; treść opisuje deltę.
- Bez frameworków, dostawców, schematu bazy i protokołów w wymaganiach — należą do architektury.
- Przed zapisem **uruchom** kontrolę (gotowość 0–4, wyciek techniki, próg MVP z briefu):
  `python3 .claude/skills/proc-requirements-shaping/scripts/requirements_lint.py docs/project/03-requirements/requirements.md --brief docs/project/01-discovery/brief.md`
  Kod 1 = wyciek techniki albo szacunek ponad budżet bez potwierdzenia kosztu; gotowość < 2 to ostrzeżenie.
  Kształt historyjek (AC-001…004, STORY-001…003, brak `AC-n`) to ostrzeżenia z `US-NN` i regułą; `--strict`
  zamienia je w kod 1. Pojedynczą historyjkę sprawdza `--story <plik>`.
- Sesja dłuższa niż jedna rozmowa: punkt kontrolny w `docs/project/wip/` z postępem faz (core-project-record).

## Kontrola po zapisie (zadaj człowiekowi)
Czy to jeden konkretny użytkownik? Czy przepływ zmieści się w budżecie czasu? Czy reguła to decyzja domenowa,
a nie opis ekranu? Czy „Poza zakresem” jest jawne? Czy otwarte pytania są naprawdę otwarte?

## Przykład
**Wejście:** „Aplikacja do fiszek z AI — wklejam notatki, dostaję fiszki do powtórek. Mam 3 tygodnie po godzinach.”
**Wynik (fragment `requirements.md`):**
```
## Wymagania funkcjonalne
- FR-001: Uczący się może wkleić tekst do 10 tys. znaków i dostać propozycje fiszek. Priorytet: must
  Wyzwanie: propozycje z długiego tekstu są zbyt ogólne → limit długości i podgląd źródła przy fiszce.
- FR-002: Uczący się może zaakceptować, poprawić albo odrzucić każdą propozycję. Priorytet: must
## Reguła biznesowa
Propozycja fiszki trafia do talii dopiero po akceptacji uczącego się, a zaakceptowane wchodzą do harmonogramu powtórek.
## Poza zakresem
- import PDF · współdzielenie talii · własny algorytm powtórek
## Cele ochronne
- tekst źródłowy nie zostaje w logach
```
Szacunek „logowanie + mobilna aplikacja” wyszedł 6 tygodni przy budżecie 3 → cięcia: tylko web, profil lokalny
zamiast kont. Kontrola skryptem: gotowość 4/4, brak wycieku. Więcej (brownfield, wyzwania): `references/przyklady.md`.

## Checklista
- [ ] budżet czasu MVP ustalony przez człowieka i zapisany w briefie; szacunek obok
- [ ] tryb (greenfield / brownfield) potwierdzony
- [ ] każde FR w formacie `FR-NNN` z priorytetem i wynikiem wyzwania
- [ ] każda `US-NN`: ≥ 1 scenariusz `AC-n` w GWT i jedna akcja (więcej → podział)
- [ ] reguła biznesowa jednym zdaniem albo świadomie zapisany pusty CRUD
- [ ] wymagania jakości jako zachowanie widoczne z zewnątrz; technika w „Do decyzji o stacku”
- [ ] „Poza zakresem” niepuste; luki w „Otwartych pytaniach” z adresatem
- [ ] `requirements_lint.py --strict` kończy się kodem 0 (albo człowiek przyjął nazwane ostrzeżenia)

## Źródła
- Kurs 10xDevs, ed. 3 (2026), prework (lekcje 4.1–4.3) i moduł 1, lekcja 1 (kształtowanie zakresu i PRD) — materiał
  szkoleniowy (dostęp 2026-10-09). Kurs podaje niespójne progi MVP (raz ok. tydzień i 4 akcje, raz 3 tygodnie
  i 6 akcji) — tu zastąpione ustawieniem z briefu.
- M. Cagan, *Inspired* (2018) — wymagania jako problem i wynik, nie lista funkcji; Mike Cohn, *User Stories Applied*
  (2004); Gherkin Given/When/Then — cucumber.io/docs/gherkin (dostęp 2026-10-10); reguły kształtu historyjek
  i słownik — kontrakt pdi 0.4.0 (`contract/fixtures/story-shape/`, 2026-10-25).
Opisane własnymi słowami.
