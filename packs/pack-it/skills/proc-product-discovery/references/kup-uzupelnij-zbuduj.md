# Kup, uzupełnij czy zbuduj — kwalifikacja narzędzia wewnętrznego

AI obniża koszt pierwszej wersji, ale nie koszt utrzymania: odpowiedzialność za dane, zmiany API dostawców,
tłumaczenie zespołowi, „dlaczego raport dziś milczy”. Pytanie nie brzmi „czy umiemy to zbudować”, tylko „czy chcemy
przejąć tę odpowiedzialność”. Pełny zamiennik SaaS przejmuje też uprawnienia, audyt, niezawodność, wdrażanie nowych
osób i ryzyko danych.

## Cztery kierunki
- **Kup albo użyj funkcji wbudowanej** — problem generyczny (podsumowanie zgłoszenia, etykiety, widok zaległości,
  panel CI).
- **Uzupełnij** (zwykle najlepszy start) — wartość bierze się z połączenia kilku systemów, których żaden SaaS osobno
  nie widzi. Cienka warstwa czyta, streszcza, **linkuje do źródeł** i nie udaje nowego źródła prawdy.
- **Zbuduj pełniejszy przepływ** — dopiero gdy uzupełnienie przetrwało zderzenie z rzeczywistością: ktoś go używa,
  oszczędza czas, ma właściciela i zakres.
- **Czekaj albo nie buduj** — sygnał słaby, problem rozwiązany gdzie indziej albo tarcie jest **istotne** (wynika
  z realnego ograniczenia lub decyzji), a nie przypadkowe.

## Mapa okazji
Jeden wiersz na sygnał tarcia — powtarzalny i obserwowalny („w poniedziałek kierownik 40 minut zbiera statusy z trzech
narzędzi”), a nie rozwiązanie („zróbmy dashboard”).
| Sygnał tarcia | Co dają istniejące narzędzia | Cienkie uzupełnienie | Pierwsza użyteczna wersja | Ryzyko danych | Kierunek, jeśli się sprawdzi |
|---|---|---|---|---|---|
Ryzyko danych: makiety, dane lokalne, tylko odczyt, dane niewrażliwe → można lekko; prawdziwe dane firmy lub klientów
→ dostęp, uprawnienia i audyt **przed** implementacją (arch-privacy-compliance).

## Wybór kandydata (najwyżej jeden)
Kandydat: powtarza się regularnie · łączy co najmniej 2 źródła albo 2 role · ma dziś ręczny koszt · da się go sprawdzić
na eksporcie albo w trybie tylko do odczytu · nie przejmuje odpowiedzialności platformy · ma jasny kierunek rozwoju.
Żaden sygnał nie przechodzi → rekomendacja „nie budować” z nazwanym istniejącym narzędziem do wypróbowania.
Lepiej 2–3 utrzymywane narzędzia niż 10 prototypów — ograniczeniem jest uwaga potrzebna do utrzymania, nie czas startu.

## Opis pierwszej wersji (5–8 zdań)
Czyta: [źródła] · Zwraca: [raport, widok, podsumowanie] · Nie robi: [świadome wykluczenia] · Ryzyko danych: […] ·
Kierunek: [produkt / funkcja / narzędzie wewnętrzne / usługa / czekaj].
Kolejność dojrzewania: makieta raportu w Markdown → skrypt na eksportach JSON lub CSV → statyczny HTML udostępniany
ręcznie → dopiero potem agent, harmonogram, aplikacja.

## Sygnały, że narzędzie stało się produktem
Zespół planuje dzień według jego wyniku; błędny raport wywołuje zamieszanie; pojawiają się prośby o nowe źródła,
kontrolę dostępu i działanie bez ręcznego uruchamiania → świadoma zmiana statusu: właściciel, obsługa błędów,
zachowanie przy braku danych, kto widzi wynik.

## Następny krok
Najtańszy: kilkuminutowa rozmowa z kierownikiem i zespołem (często znają powód tarcia). Potem walidacja pytaniami
o przeszłe zachowania (ddd-discovery-intake, `badania-uzytkownikow.md`), potem wymagania (proc-requirements-shaping)
albo — przy wąskim sygnale z jasną pierwszą wersją — od razu plan i realizacja.

## Przykład
**Sygnał:** „Kierownik co poniedziałek 40 minut składa status z Jiry, GitHuba i Slacka.”
**Mapa:** Jira i GitHub mają osobne raporty, żaden nie łączy zgłoszeń z PR i wątkami → uzupełnienie: skrypt czyta
eksporty (tylko odczyt), składa listę „zgłoszenie — PR — ostatni wątek” z linkami → pierwsza wersja: Markdown
z eksportów z ostatniego tygodnia → ryzyko danych: nazwy klientów w zgłoszeniach (tylko wewnętrznie) → kierunek:
narzędzie wewnętrzne, jeśli po 4 tygodniach kierownik z niego korzysta.
**Odrzucone:** własny dashboard z bazą i logowaniem („zbuduj”) — przejmuje uprawnienia i utrzymanie bez dowodu wartości.

Źródło: kurs 10xDevs, ed. 3 (2026), moduł 5, lekcja 1 (narzędzia wewnętrzne, mapa okazji) — materiał szkoleniowy
(dostęp 2026-10-09). Opisane własnymi słowami.
