# TDD z agentem — pionowe plasterki na uzgodnionych spoinach

Uzupełnienie cyklu z SKILL.md dla pracy agenta. Słownik (moduł, interfejs, spoina, adapter): eng-module-depth.

## Bramka przed fazą planu — TDD czy nie?
1. **Czy kod tej fazy już istnieje** (choćby częściowo)? Tak → to nie TDD. Nie dopisujesz testów „po fakcie” pod
   etykietą TDD: albo zwykła implementacja z testem i celowym psuciem (qa-spec-first-testing), albo test
   charakteryzujący przed refaktoryzacją.
2. **Czy umiesz nazwać pierwszy czerwony test jednym zdaniem o obserwowalnym wyniku?** („zwraca 401, gdy użytkownik
   nie ma dostępu do kursu”, „resetuje interwał do 1 dnia przy ocenie 0”). Nie → wróć do analizy, nie zgaduj.

| Dobre dla TDD | Słabe dla TDD |
|---|---|
| parsery, walidatory, przekształcenia; reguły z wejściem i wyjściem; kontrakt API (status, ciało, autoryzacja); reduktory i maszyny stanów; bugfix (najpierw test odtwarzający); strażnik regresji dla ryzyka | rusztowanie katalogów, konfiguracja narzędzi, CI i zmiennych środowiska, dokumentacja, kosmetyka UI bez asercji, cienki klej (test przepisałby kod), spike szukający kontraktu |

- Faza mieszana: TDD dla części z logiką, reszta zwykłą implementacją — jawnie w raporcie.
- Budżet: 2–5 testów na fazę, wybranych pod regresje, nie test na getter.
- RED pokazujesz uruchomieniem **jednego pliku testu**; czerwony z właściwego powodu = asercja albo brak modułu lub
  funkcji, którą zaraz napiszesz — nie błąd składni, zły import czy „No test files found” w samym teście.
- GREEN: padły inne testy → naprawiasz kod, nie testy.
- Commit tylko na zielonym pełnym zestawie; czerwony stan to punkt kontrolny dla człowieka, nie granica commita.
- Jeden plan może mieszać tryby per faza (środowisko → TDD kontraktu → E2E ścieżki → przepisy w strategii testów),
  ze stanem postępu w jednym miejscu.

## Zanim powstanie pierwszy test
- **Nazwij spoiny** (publiczne interfejsy, przez które obserwujesz zachowanie) i **zatrzymaj się na potwierdzenie**.
  Testu w niepotwierdzonej spoinie nie piszesz. Wszystkiego nie przetestujesz — uzgodnienie spoin kieruje wysiłek na
  krytyczne ścieżki i złożoną logikę, nie na każdy przypadek brzegowy. Spoiny zwykle ustala się już przy specyfikacji
  (qa-spec-first-testing) albo w briefie zadania.
- Nazwy testów i interfejsów — słowami ze słownika domeny; szanuj ADR z obszaru.
- Gdy niejasny jest sam kształt interfejsu — najpierw eng-module-depth, potem testy.

## Pętla
1. **Jeden plasterek na cykl:** jedna spoina, jeden test, minimalna implementacja. Pierwszy cykl to **pocisk smugowy** —
   jedna ścieżka od początku do końca, która dowodzi, że całość się łączy.
2. Red → green; nie przewiduj kolejnych testów, nie dodawaj funkcji „na zapas”.
3. Następny test wynika z tego, czego nauczył poprzedni cykl.
4. **Refaktoryzacja osobno** — po zielonym, jako osobny krok lub commit, zwykle przy review. Agenci w praktyce pomijają
   ją w pętli, więc wpisz ją jawnie w plan albo w listę przeglądu, zamiast zakładać, że „sama się zrobi”.

## Trzy anty-wzorce
| Anty-wzorzec | Sygnał | Zapobieganie |
|---|---|---|
| **test związany z implementacją** | test pada po zmianie nazwy funkcji wewnętrznej, choć zachowanie się nie zmieniło; mocki własnych modułów, liczenie wywołań, sprawdzanie przez zapytanie do bazy zamiast przez interfejs | testuj tylko przez interfejs; zapisany obiekt sprawdzasz, odczytując go publiczną metodą |
| **test tautologiczny** | oczekiwana wartość liczona tak samo jak w kodzie (`expect(suma(a, b)).toBe(a + b)`), migawka wyprowadzona tym samym sposobem | oczekiwana wartość ze specyfikacji, znanego literału albo przeliczonego ręcznie przykładu (`toBe(15)`) |
| **cięcie poziome** | najpierw paczka testów, potem cały kod | testy sprawdzają wyobrażone zachowanie i kształt, a nie to, czego potrzebuje użytkownik → pionowe plasterki |

## Mocki tylko na granicy systemu
- Mockujesz: zewnętrzne API (płatności, e-mail), czas, losowość; czasem system plików i bazę (lepiej baza testowa).
- Nie mockujesz: własnych klas i modułów, wewnętrznych współpracowników — niczego, nad czym masz kontrolę.
- Zależności zewnętrzne **wstrzykuj** (nie twórz klienta w środku funkcji).
- Klient zewnętrznego API w stylu SDK — osobna funkcja na operację (`pobierzUzytkownika`, `utworzZamowienie`) zamiast
  jednego ogólnego `fetch(endpoint, opcje)`: mock zwraca jeden kształt, bez warunków w konfiguracji testu, z typami.

## Pętla w większym przepływie
- Kolejność: przesłuchanie → specyfikacja (tu uzgadniasz spoiny) → zadania → TDD w każdym zadaniu → review.
- **Review sprawdza spoiny:** czy testy powstały tylko w uzgodnionych spoinach, czy nazwy opisują zachowanie, czy są mocki
  własnych modułów. Refaktoryzację robi się przy review, nie w pętli.
- Agent nie widzi innych zadań: do zadania dołącz specyfikację (link), nie sam opis zadania; zadania tnij tak, żeby każde
  dało się domknąć jedną pętlą.
- Niejasny wybór spoiny → poproś agenta o porównanie 2–3 wariantów (co każdy pozwala testować, co ukrywa), zanim
  potwierdzisz.
- Agenci bez pilnowania czasem piszą kod przed testem. W fabryce kolejność wymusza hook `tdd_guard`: kod produkcyjny
  dopiero po edycji testu i czerwonym uruchomieniu. Przy kluczowych plasterkach sprawdź w raporcie, czy czerwony wynik
  był z właściwego powodu.

## Działa dobrze, gdy
Agent nazywa spoiny i czeka przed pierwszym plikiem testów; testy pojawiają się po jednym (pada → minimalny kod → następny);
nazwy testów opisują możliwość użytkownika („zamówienie z poprawnym koszykiem zostaje potwierdzone”), nie wnętrze
(„wywołuje paymentService.process”); zmiana nazw wewnętrznych nie psuje żadnego testu; mocki są tylko na granicy.
Wolne testy E2E/przeglądarkowe uruchamiasz na końcu (zapisz to w `CLAUDE.md` projektu).
Praca bez określonego zachowania (konfiguracja, klej, proste CRUD) — TDD ma tu małą wartość; wystarczy test integracyjny
ścieżki.

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 3, lekcja 2 (TDD z agentem, bramka przed fazą) — materiał szkoleniowy (dostęp 2026-10-09).
- [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), skill `tdd` (z plikami o dobrych testach i mockowaniu);
opis: [aihero.dev](https://www.aihero.dev/skills-tdd). Opisane własnymi słowami.
