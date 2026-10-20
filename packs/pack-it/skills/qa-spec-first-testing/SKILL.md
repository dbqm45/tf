---
name: qa-spec-first-testing
description: Użyj, gdy testy mają sprawdzać wymaganie, nie implementację — niezależna wyrocznia, clean-room, ATDD, mutacje.
metadata:
  przeglad: 2027-10-09
  katalog: "Użyj przy każdym pisaniu testów — jak sprawić, by test sprawdzał WYMAGANIE, a nie powielał implementację (wyrocznia niezależna od kodu, TDD/ATDD, clean-room, protokół rozbieżności, testy charakteryzujące, mutacyjne i oparte na właściwościach). Nie do technik wyboru przypadków (qa-test-design) ani składni narzędzi (tool-*)."
  slowa: "test ze specyfikacji pada, zmienić oczekiwaną wartość w teście, poprawić test pod kod, test czy kod, wyrocznia testu"
---

# Testy od specyfikacji, nie od implementacji

## Problem
Test napisany przez **czytanie istniejącej metody** koduje jej zachowanie — razem z błędami. Taki test („lustrzany”)
przechodzi zawsze i niczego nie dowodzi: jeśli metoda liczy rabat od `> 10` zamiast od `>= 10`, test wygenerowany z kodu
sprawdzi `11` i utrwali błąd.

## Zasada: niezależna wyrocznia
**Oczekiwany wynik testu pochodzi spoza kodu produkcyjnego**, zawsze ze wskazanym źródłem:
1. kryteria akceptacji (Given/When/Then) i reguły biznesowe z `docs/project/03-requirements/`,
2. przykłady od eksperta (Example Mapping, ddd-deep-modeling) — konkretne liczby i daty,
3. wartości policzone **ręcznie lub inną metodą** niż kod (tabela w teście, arkusz, model referencyjny),
4. przepisy, standardy, kontrakty API (OpenAPI, typy publiczne),
5. właściwości i niezmienniki („suma rat = kwota”, „nigdy dwie rezerwacje na ten sam przedział”).

**Nigdy:** uruchomienie kodu i przepisanie wyniku jako „expected”; ta sama formuła w teście co w produkcji;
mock zwracający to, co potem jest asertowane.

## Przepływy pracy
### Nowa funkcja — test najpierw (TDD / ATDD)
1. Tester z kryteriów akceptacji pisze **testy akceptacyjne** (e2e/API) — przed implementacją.
2. Programista w cyklu TDD: test jednostkowy **czerwony z właściwego powodu** → minimalny kod → zielony → refaktor (eng-testing).
3. Każdy nowy test **musi najpierw nie przejść** — test, który od razu jest zielony, nic nie udowodnił (sprawdź, czy w ogóle wykonuje asercję).

### Kod istniejący bez testów
Dwa różne rodzaje testów — nigdy ich nie mieszaj:
- **Testy ze specyfikacji** (projektowane w clean-room, patrz niżej). Porażka = defekt albo luka w specyfikacji — **nie poprawka testu**.
- **Testy charakteryzujące** — tylko jako siatka bezpieczeństwa przed refaktoryzacją; utrwalają obecne zachowanie, nie jego
  poprawność. Oznacz je (`describe('[charakteryzujący] …')`, tag `@characterization`) i nie licz jako dowodu działania.
  Przy przepisywaniu takich testów na wyższy poziom prowadź **rejestr asercji** (co nowa asercja przestała rozróżniać i dlaczego to OK),
  a zmianę, która „przy okazji” naprawia błąd, zgłoś jako ukryty defekt (eng-behavior-preserving-refactoring).

### Clean-room (rozdzielenie ról)
- **Projektant testów** (`*-qa-analyst`) widzi specyfikację, kontrakty i istniejące testy, **nie widzi implementacji** —
  wymusza to hook `cleanroom_guard.py`. Produkuje przypadki testowe z oczekiwanymi wynikami i ich źródłem.
- **Automatyk** (`*-qa-automation`) może czytać kod, żeby podpiąć testy (selektory, API), ale **oczekiwane wartości bierze
  wyłącznie z przypadków testowych** — nie z kodu.

### Clean-room poza testami
Ta sama zasada działa przy generowaniu wymagań do testu obciążeniowego modelu (ddd-model-stress-test): agent w profilu `blind`
czyta wyłącznie brief biznesowy — wymagania pisane ze znajomością architektury pasują do niej z konstrukcji.

## Protokół rozbieżności (test ze specyfikacji nie przechodzi)
1. Sprawdź test względem specyfikacji: czy dobrze odczytałeś wymaganie i dane wejściowe?
2. Test zgodny ze specyfikacją → **zgłoszenie defektu** (qa-exploratory-manual: format zgłoszenia) z ID przypadku i cytatem ze źródła.
   Test zostaje czerwony albo oznaczony jako znany błąd (`test.fails` / `test.fixme` z linkiem do zgłoszenia) — **nigdy
   nie zmieniaj oczekiwanej wartości, żeby „przeszło”**.
3. Specyfikacja niejednoznaczna → otwarte pytanie do właściciela produktu (core-project-record); test oznaczony jako oczekujący.
4. Zmiana oczekiwanej wartości tylko z nowym źródłem (zaktualizowane kryterium) — w commicie podaj źródło.

## Czy testy w ogóle łapią błędy?
- **Testy mutacyjne** (Stryker dla JS/TS, PIT dla Javy) na logice domenowej: narzędzie wprowadza drobne błędy (`>=` → `>`,
  `+` → `-`). Mierz *mutation score* krytycznych modułów, nie pokrycie linii: pokrycie pokazuje kod bez testu, wynik
  mutacyjny — testy ślepe (agent rzadko zostawia kod niepokryty, częściej pokryty, ale nieobroniony).
  Wynik 0% albo podejrzane 100% na starcie = najpierw sprawdź, czy narzędzie w ogóle aktywuje mutanty (tool-vitest).
  Zakres: moduły z mapy ryzyk lub bieżącej zmiany, zawężone do pliku albo zakresu linii — nie całe repo po każdym commicie.
- **Testy oparte na właściwościach** (fast-check, jqwik) dla obliczeń i niezmienników — wyrocznią jest właściwość, nie kod.
- **Wartości brzegowe** z qa-test-design — tam najczęściej chowają się błędy „o jeden”.

### Przeżyły mutant — decyzja, nie automat
Dla każdego pytasz: „czy realny błąd tego kształtu zabolałby użytkownika lub biznes?”
1. **Tak — realna luka** → dopisz asercję zachowania (nie szczegółu implementacji). Typowo: `>=` → `>` na progu,
   `||` → `&&` w obsłudze błędu, usunięty warunek.
2. **Mutant równoważny** (zmiana nie zmienia obserwowalnego zachowania) → pomiń; żaden test go nie zabije.
3. **Zmiana realna, ale asercja byłaby krucha** (treść komunikatu, nagłówek, kosmetyka odpowiedzi) → pomiń świadomie,
   z jednym zdaniem uzasadnienia w raporcie.

Nie gonisz 100% — zabijanie mutantów kosmetycznych produkuje testy lustrzane. Testy, które nie zabijają żadnego mutanta,
a powielają inny test (ta sama asercja, inny setup), scal w jeden sparametryzowany albo usuń.

### Celowe psucie — czy asercja w ogóle pilnuje? (ręczna mutacja)
Gdy test powstał po kodzie, agent pracował bez nadzoru albo chroni ryzyko z mapy ryzyk:
1. Dodaj pliki kroku do indeksu (`git add <pliki>`), żeby przywrócenie było dokładne.
2. W kodzie produkcyjnym odwróć lub osłab dokładnie chronione zachowanie (zawęź filtr, odwróć gałąź, usuń zapis) —
   zmiana tylko w drzewie roboczym.
3. Uruchom ten test. Ma być **czerwony** (najlepiej tylko on) — to wynik pozytywny.
4. Zawsze przywróć: `git checkout -- <plik>`, także gdy coś poszło nie tak; przed commitem sprawdź `git diff`.
5. Zielony na zepsutym kodzie = asercja niczego nie chroni → wzmocnij asercję; nigdy nie osłabiaj kodu ani nie pomijaj kroku.

W raporcie: co zepsuto, który test zrobił się czerwony, że plik przywrócono.

### Testy do istniejącego pliku bez pełnego cyklu (runner już jest)
1. Z wymagań i stacku (nie z kodu) wypisz zachowania pliku ważne dla użytkownika i biznesu — przed testami. Źródła nie
   rozstrzygają oczekiwanego wyniku → pytania, nie zgadywanie.
2. Na każde zachowanie test behawioralny i co najmniej jeden przypadek brzegowy z ryzyka (null, puste, błąd zależności,
   złe wejście). Bez niemal identycznych kopii — każdy test łapie inną regresję.
3. Raport: | Test | Jaką regresję łapie | Jaka zmiana w kodzie by go zaczerwieniła | Źródło oczekiwania |. Wiersz bez
   kolumny 2 lub 3 → „niepewny” i pytanie do człowieka.

## Sygnały testu lustrzanego (odrzucaj w review)
oczekiwana wartość liczona tą samą formułą co w kodzie · asercje na wywołania wewnętrznych metod zamiast na wynik ·
cały wynik jako snapshot zaakceptowany bez przeglądu · nazwa testu = nazwa metody (`test calculate()`) zamiast zachowania ·
brak odwołania do wymagania · test napisany po kodzie, który nigdy nie był czerwony (→ celowe psucie) ·
`toEqual(await f(x))` — wynik funkcji porównany z nim samym · tylko ścieżki szczęśliwe, zero przypadków brzegowych
z ryzyka · seria testów różniących się tylko setupem przy tej samej asercji.

## Śledzenie
Nazwa lub tag testu zawiera ID kryterium/przypadku (`H1-AC2`, `TC-014`). Pokrycie mierzymy **wymaganiami** (każde kryterium ma test),
nie procentem linii.

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 3, lekcja 2 (testy jednostkowe z agentem, testy mutacyjne) i moduł 5 (kontrola
  „celowego zepsucia” w pracy bez nadzoru) — materiał szkoleniowy (dostęp 2026-10-09).
- Stryker 10.0 `stryker run --help` — zawężenie `--mutate` do pliku lub zakresu linii (sprawdzone 2026-10-10).
Opisane własnymi słowami.
