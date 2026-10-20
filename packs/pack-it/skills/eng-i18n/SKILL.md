---
name: eng-i18n
description: Użyj przy wielu językach i rynkach — ICU i liczba mnoga, Intl, strefy IANA, kwoty, przepływ tłumaczeń, RTL, pseudolokalizacja.
metadata:
  przeglad: 2027-10-20
  katalog: "Użyj, gdy produkt ma działać w wielu językach, krajach lub strefach czasowych — na froncie i backendzie: komunikaty w ICU MessageFormat (liczba mnoga, rodzaj, polskie kategorie one/few/many/other), MessageFormat 2, formatowanie przez Intl (daty, liczby, kwoty, listy, sortowanie), locale użytkownika i najemcy, czas w UTC i strefy IANA (spotkania w przyszłości, zmiana czasu, Temporal), kwoty pieniężne (miejsca po przecinku wg ISO 4217, zaokrąglenia), teksty z backendu (e-maile, PDF, powiadomienia, błędy API), przepływ tłumaczeń i klucze, pseudolokalizacja, RTL i CSS logical properties, testy i18n. Nie do pisania samych tekstów i tonu (ux-content-design), szczegółów API przeglądarki (fe-web-platform) ani stylów (fe-css)."
  slowa: "i18n, internacjonalizacja, l10n, lokalizacja aplikacji, wiele języków w aplikacji, ICU, MessageFormat, liczba mnoga, 1 plik 2 pliki 5 plików, plural, PluralRules, Intl, DateTimeFormat, NumberFormat, format daty, format kwoty, ISO 4217, locale, strefa czasowa, UTC, IANA, zmiana czasu, spotkanie przesuwa się o godzinę, Temporal, RTL, arabski, hebrajski, prawej do lewej, logical properties, pseudolokalizacja, klucze tłumaczeń, e-mail w języku użytkownika, Accept-Language"
---

# Internacjonalizacja (i18n) w całym systemie

**Rola agenta:** projektuje system tak, żeby nowy język, kraj lub strefa czasowa wymagały tłumaczeń i konfiguracji,
a nie zmian w kodzie — na froncie, w backendzie, w e-mailach i w danych. Szczegóły API przeglądarki (`Intl`, RTL
w CSS, SSR): fe-web-platform, `i18n.md`. Fakty i źródła: `references/fakty-i-zrodla.md`.

## 1. Locale — skąd i gdzie
- Locale użytkownika (język + region, np. `pl-PL`, `en-US`) z profilu, potem z `Accept-Language` / `navigator.languages`;
  zapisany w profilu i w URL publicznych stron. Domyślne locale najemcy dla kont bez wyboru (arch-multi-tenancy).
- Locale przechodzi przez każdą ścieżkę, która tworzy tekst: żądanie, zadanie w tle, e-mail, PDF, push. Zadanie
  w tle bierze locale **odbiorcy**, nie tego, kto zdarzenie wywołał.
- Osobno: język tekstów, format liczb i dat (region), strefa czasowa, waluta. To cztery ustawienia, nie jedno.

## 2. Komunikaty — ICU MessageFormat
- Teksty poza kodem, z kluczami opisującymi miejsce (`invoice.list.empty`), parametrami i kontekstem dla tłumacza.
- Liczba mnoga i rodzaj w komunikacie (`{count, plural, one {# plik} few {# pliki} many {# plików} other {# pliku}}`),
  nigdy sklejanie fragmentów. Polski ma kategorie `one`, `few`, `many`, `other` — nie zakładaj „1 vs reszta”.
- MessageFormat 2 jest stabilny jako specyfikacja (CLDR 47), ale implementacje bywają w fazie podglądu — w nowym
  projekcie sprawdź bibliotekę, zanim go wybierzesz; ICU MessageFormat 1 pozostaje bezpiecznym wyborem.
- Backend: te same pliki komunikatów i ta sama biblioteka ICU (lub zgodna) dla e-maili, PDF i błędów API.
  Błąd API zwraca kod i parametry (be-api-design); tekst dla człowieka powstaje w locale odbiorcy.

## 3. Formatowanie — zawsze przez bibliotekę locale
- Daty, liczby, waluty, listy, czas względny, sortowanie: `Intl.*` w JS, ICU / CLDR w innych językach
  (`java.text`/ICU4J, Babel w Pythonie). Żadnych ręcznych formatów „dd.MM.yyyy” w kodzie.
- Formatowanie na samym końcu (widok, szablon e-maila). API i baza trzymają wartości surowe: ISO 8601, liczby,
  kody walut i krajów (ISO 4217, ISO 3166).

## 4. Czas i strefy
- Moment, który się wydarzył (utworzenie, płatność, log): UTC w bazie (`timestamptz`), strefa tylko do wyświetlania.
- Zdarzenie w przyszłości w czasie lokalnym (spotkanie, przypomnienie o 9:00, koniec okresu rozliczeniowego):
  zapisz **czas lokalny + identyfikator strefy IANA** (`Europe/Warsaw`, `America/New_York`), a UTC licz przy użyciu,
  bo reguły stref się zmieniają. Przesunięcie (`+02:00`) to nie strefa.
- Aktualizuj bazę stref (tzdata w systemie, JDK, bibliotece) — nieaktualna daje błędne godziny po zmianie przepisów.
- Testy na kontrolowanym zegarze: zmiana czasu wiosną i jesienią, dzień 23 i 25 godzin, przełom roku, strefy
  z przesunięciem o pół godziny. W JS do nowego kodu `Temporal` tam, gdzie jest dostępny (lang-javascript).

## 5. Pieniądze i waluty
- Kwota = wartość + kod waluty; liczba całkowita w najmniejszej jednostce albo typ dziesiętny, nigdy float.
  Liczba miejsc po przecinku zależy od waluty (JPY 0, PLN 2, KWD 3 — ISO 4217); bierz ją z danych, nie stałej 2.
- Wyświetlanie przez `NumberFormat` z `currency`; przeliczanie walut z kursem i datą kursu; zaokrąglenie w jednym
  miejscu (be-billing-subscriptions).

## 6. Przepływ tłumaczeń
- Jeden język źródłowy; nowe klucze trafiają do systemu tłumaczeń (TMS albo pliki w repo z przeglądem) automatycznie
  z CI; brakujące tłumaczenie = język zapasowy + ostrzeżenie w logach, nie pusty tekst ani klucz na ekranie.
- Kontekst dla tłumacza: opis, zrzut ekranu, limit długości. Proces i styl treści: ux-content-design.
- CI: walidacja składni ICU we wszystkich językach, nieużywane i brakujące klucze, zgodność parametrów.

## 7. Układ, RTL, długość
- `<html lang dir>`, CSS logical properties (`margin-inline-start` zamiast `margin-left`), odwracanie ikon
  kierunkowych, `dir="auto"` dla treści użytkownika — fe-web-platform, fe-css.
- Teksty bywają o 30–40% dłuższe; projekt bez sztywnych szerokości.
- **Pseudolokalizacja** w buildzie testowym (akcenty, wydłużenie, nawiasy; wariant RTL) — wyłapuje teksty
  zaszyte w kodzie, ucięte etykiety i sklejanie przed tłumaczeniem.

## Zasady
- Nowy język = nowe tłumaczenia i konfiguracja, bez zmian w kodzie.
- Wartości surowe w API i bazie, formatowanie na końcu w locale odbiorcy.
- Przeszłość w UTC; przyszłość w czasie lokalnym ze strefą IANA.
- Teksty z liczbą mnogą i rodzajem tylko przez ICU; testy na `pl` (cztery kategorie) i na RTL.

## Przykład
**Sytuacja:** „Spotkania na 9:00 w Nowym Jorku po zmianie czasu pokazują się o 8:00 albo 10:00; wchodzimy też na rynek
arabski.”
**Wynik (skrót):**
- Przyczyna: spotkanie zapisane jako UTC policzone w dniu utworzenia. Poprawka: `local_start = 09:00`, `tz =
  America/New_York`, UTC liczone przy wyświetlaniu i przypomnieniu; migracja istniejących wpisów ze strefą twórcy.
- Testy: spotkanie cykliczne przez zmianę czasu w USA i w UE (różne daty), uczestnik w innej strefie.
- Arabski: `dir="rtl"`, logical properties, odwrócone ikony strzałek, pseudolokalizacja RTL w CI, liczby i daty przez
  `Intl` z `ar`; komunikaty ICU z kategoriami arabskimi (zero, one, two, few, many, other; CLDR, `references/fakty-i-zrodla.md`).

## Checklista
- [ ] locale, region, strefa i waluta jako osobne ustawienia; przechodzą do zadań w tle i e-maili (locale odbiorcy)
- [ ] komunikaty w ICU, bez sklejania; polskie kategorie liczby mnogiej przetestowane
- [ ] formatowanie przez Intl/ICU na końcu; API i baza z wartościami surowymi
- [ ] przeszłość w UTC, przyszłość jako czas lokalny + strefa IANA; testy zmiany czasu; tzdata aktualizowana
- [ ] kwoty bez float, miejsca po przecinku z ISO 4217
- [ ] przepływ tłumaczeń z walidacją w CI; język zapasowy; pseudolokalizacja i RTL w testach

## Źródła
Opisane własnymi słowami; fakty z datą dostępu w `references/fakty-i-zrodla.md`.
