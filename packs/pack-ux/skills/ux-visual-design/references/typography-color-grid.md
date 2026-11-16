# Typografia, kolor, siatka, ikony

## Typografia
- **Skala:** baza 16 px × stosunek 1,2 (mała tercja, gęste UI) lub 1,25 (większa, strony treściowe). Przy 1,25:
  16 → 20 → 25 → 31 → 39. Mniej stopni = spójniej; ponad 7 to sygnał bałaganu. Wartości zaokrąglaj do całych px.
- **Długość linii:** 45–75 znaków, sufit 80 (WCAG 1.4.8, poziom AAA). Szerokość w `ch` (np. `max-width: 66ch`) liczysz
  dla kroju i rozmiaru, nie na oko. Kolumny węższe niż 30 znaków dają rwane akapity.
- **Interlinia:** tekst ciągły 1,4–1,6; nagłówki 1,1–1,3; im dłuższa linia, tym większa interlinia. Układ musi znosić
  nadpisanie wg WCAG 1.4.12: interlinia 1,5, odstęp akapitów 2× rozmiar, litery +0,12 em, wyrazy +0,16 em — bez
  ucinania i nakładania (żadnych sztywnych wysokości na tekście).
- **Krój:** jeden, najwyżej dwa; sprawdź polskie znaki (ą ć ę ł ń ó ś ź ż) we wszystkich grubościach oraz cyfry
  tabelaryczne w tabelach. Pogrubienie i wielkość niosą hierarchię; kapitaliki i `uppercase` tylko dla krótkich etykiet.
- **Typowe błędy:** hierarchia samym szarym kolorem; tekst wyjustowany bez dzielenia wyrazów; nagłówek bliżej
  poprzedniego akapitu niż swojego; ponad 3 grubości w jednym widoku.

## Kontrast — jak liczyć
1. Wzór WCAG: (L1 + 0,05) / (L2 + 0,05), gdzie L to luminancja względna sRGB, L1 jaśniejszego koloru.
2. Progi: tekst 4,5:1; duży tekst 3:1; elementy interfejsu i fokus 3:1 (SC 1.4.11); tekst nieaktywny jest zwolniony,
   ale i tak zostaw czytelny odpowiednik.
3. Zaokrąglenie w górę nie jest dozwolone: 4,49:1 nie przechodzi.
4. Tekst na zdjęciu lub gradiencie: licz w najgorszym punkcie albo dodaj półprzezroczystą warstwę.
5. Stany (hover, wciśnięty, zaznaczony) liczysz osobno; wskaźnik fokusu nie może być zasłonięty przez przypięte
   elementy (SC 2.4.11).
- **Poprawka koloru:** zmieniaj jasność (L w OKLCH lub HSL), zachowaj odcień. Zestaw 10–12 tonów na rodzinę:
  tony 50–200 tła, 500–600 akcent, 700–900 tekst.
- **Tryb ciemny:** nie odwracaj jasnego; powierzchnie rozjaśniaj wraz z wysokością, akcent rozjaśnij i zdesaturuj,
  czystą czerń i czystą biel na dużych powierzchniach zastąp tonami pośrednimi.
- **Kolor semantyczny:** sukces, ostrzeżenie, błąd, informacja + ikona i tekst. Żółć rzadko przejdzie jako tekst
  na bieli — użyj ciemnego brązu na żółtym tle.

## Siatka i odstępy
- Skala 4 px: 4, 8, 12, 16, 24, 32, 48, 64, 96. Wewnątrz komponentu 4–16, między komponentami 16–32, między sekcjami
  48–96. Zasada bliskości: odstęp wewnątrz grupy ≤ połowa odstępu między grupami.
- Strona treściowa: 12 kolumn, rynna 16–24 px, margines 16 px na telefonie. Aplikacja: elastyczne obszary
  z minimalnymi szerokościami. Punkty zwrotu wybieraj według treści (kiedy układ się psuje), nie według urządzeń.
- Wysokość kontrolek spójna (np. 32/40/48 px); wewnętrzny odstęp poziomy ≥ pionowego.

## Ikony i obrazy
- Jedna rodzina, jedna siatka (24 px, pole bezpieczne 2 px), jedna grubość obrysu; wypełnione ikony tylko dla stanu
  „aktywny”. Ikona bez etykiety tylko dla powszechnych znaczeń (zamknij, szukaj); reszta z tekstem.
- Rozmiar ikony w linii z tekstem: wysokość kapitalika do wysokości interlinii; obszar dotyku niezależny od rysunku.
- Zdjęcia: stałe proporcje (16:9, 4:3, 1:1), zdefiniowany punkt ostrości; ilustracje w jednej palecie z marką.
  Eksport WebP/AVIF z wymiarami (CLS ≤ 0,1) — szczegóły wdrożenia w fe-css.
