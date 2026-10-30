---
name: ux-visual-design
description: Użyj przy wyglądzie interfejsu — hierarchia, typografia, kontrast WCAG, siatka, ruch, marka, Figma, zgodność wdrożenia z projektem.
metadata:
  przeglad: "2027-10-17"
  katalog: "Użyj przy projekcie wizualnym interfejsu i jego ocenie — hierarchia wizualna, skala typograficzna, długość linii i interlinia, system kolorów z obliczeniem kontrastu WCAG, siatka i skala odstępów, ikony i obrazy, zasady ruchu (cel, czas, reduced motion), nałożenie marki, praktyka w Figmie (komponenty, warianty, auto layout, zmienne), przegląd zgodności wdrożenia z projektem i krytyka projektu wizualnego. Nie do przepływów, stanów ekranu i testów z użytkownikami (ux-feature-design), audytu dostępności i deklaracji (ux-accessibility), kodu CSS i tokenów w kodzie (fe-css) ani budowy biblioteki komponentów, nazewnictwa tokenów i ich wersjonowania (ux-design-systems)."
  slowa: "wygląd, UI, ładne, brzydkie, nieczytelne, hierarchia wizualna, font, krój pisma, skala typograficzna, kolory, paleta, kontrast, kontrast WCAG, siatka, odstępy, ikony, animacja, czas animacji, reduced motion, brand, księga znaku, Figma, auto layout, warianty, makieta wizualna, zgodność z projektem, pixel perfect, przegląd wizualny, krytyka projektu"
---

# Projekt wizualny interfejsu — decyzje z liczbami

Cel: wygląd, który prowadzi wzrok, jest czytelny i da się go wiernie wdrożyć. Zasady podstawowe (jedna główna akcja,
stany, mikrointerakcje) są w **ux-feature-design** (`.claude/skills/ux-feature-design/references/ui-wizualny-i-ruch.md`) — tu je pogłębiasz procedurą
i liczysz. Wdrożenie w CSS i tokenach w kodzie: **fe-css**; budowa i utrzymanie biblioteki: **ux-design-systems**.

## Procedura
1. **Wejście.** Ustal: platformy i szerokości, tryby (jasny, ciemny), markę (księga znaku, kolory, krój) oraz istniejący
   system projektowy. Jest system — jego tokeny i komponenty mają pierwszeństwo przed nowym pomysłem. Brak marki
   → zapytaj, nie wymyślaj logo ani palety.
2. **Hierarchia.** Wypisz elementy ekranu w kolejności ważności dla zadania użytkownika (1 = główne, max 3 poziomy).
   Każdy poziom różnisz co najmniej dwoma środkami: rozmiar, grubość, kontrast, odstęp. Test: rozmycie ekranu —
   nadal widać poziom 1? Szczegóły i typowe błędy: `references/typografia-kolor-siatka.md`.
3. **Typografia.** Skala modularna (stosunek 1,2–1,25) z 5–7 stopni na tokenach; tekst ciągły 16 px, interlinia
   1,4–1,6, nagłówki 1,1–1,3; linia 45–75 znaków (twardy sufit 80). Nagłówek lepiej oddzielać odstępem niż kolorem.
4. **Kolor i kontrast — liczysz, nie oceniasz na oko.** Role (tło, powierzchnia, tekst, akcent, stany) zamiast barw.
   Dla każdej pary tekst/tło podaj współczynnik i próg: tekst ≥ 4,5:1 (SC 1.4.3); duży tekst (≥ 18 pt = 24 px albo
   ≥ 14 pt pogrubiony ≈ 18,7 px) ≥ 3:1; ramki pól, ikony niosące znaczenie, fokus ≥ 3:1 względem tła (SC 1.4.11).
   Obie palety (jasna i ciemna) liczysz osobno. Kolor nigdy jedynym nośnikiem znaczenia. Poprawka: ściemnij ton, nie
   pogrubiaj tekstu.
5. **Siatka i odstępy.** Skala odstępów 4 px (4, 8, 12, 16, 24, 32, 48, 64) z tokenów; bliskość ma znaczenie:
   odstęp wewnątrz grupy mniejszy niż między grupami (min. dwukrotnie). Siatka 12 kolumn dla treści, elastyczna dla
   aplikacji. Cele dotyku ≥ 24×24 px (SC 2.5.8), zalecane 44×44 px.
6. **Ikony i obrazy.** Jedna rodzina ikon, jedna siatka (np. 24 px, obrys 1,5–2 px), wyrównanie optyczne; ikona
   niosąca znaczenie ma etykietę. Obrazy: proporcje z góry, fokus kadru, tekst na zdjęciu tylko na warstwie
   zapewniającej kontrast; alternatywy tekstowe ustala treść, nie projektant od wyglądu.
7. **Ruch.** Najpierw cel (związek, zmiana stanu, kierunek, uwaga), potem czas: mikro 100–150 ms, panele i okna
   200–300 ms, duże przejścia ≤ 500 ms; wyjście ok. 70–80% czasu wejścia; wejście ease-out, wyjście ease-in.
   `prefers-reduced-motion`: przesunięcia i skalowanie zamień na przenikanie lub brak ruchu (nie usuwaj samej
   informacji o zmianie). Szczegóły: `references/ruch-i-marka.md`.
8. **Marka.** Marka daje kolor akcentu, krój, ton ilustracji i zdjęć; nie nadpisuje progów kontrastu ani rozmiarów
   dotyku. Kolor marki nie przechodzi kontrastu → ciemniejszy wariant do tekstu i przycisków, oryginał do dużych
   powierzchni. Wiele marek: `ux-design-systems`.
9. **Figma.** Zasady pracy (komponenty, warianty vs właściwości, auto layout, zmienne, nazwy warstw, przekazanie)
   w `references/figma.md`.
10. **Przegląd zgodności wdrożenia i krytyka.** Procedura nakładki, tolerancje i format uwag:
    `references/przeglad-wizualny.md`. Uwagi pisz wobec celu i progu („kontrast 3,45:1 < 4,5:1”), nie gustu.

## Przykład
Wejście: tekst pomocniczy `#8A8A8A` na `#FFFFFF`, przycisk `#3B82F6` z białym napisem 14 px.
Wynik:

| Para | Kontrast | Próg | Werdykt |
|---|---|---|---|
| `#8A8A8A` / `#FFFFFF`, tekst 14 px | 3,45:1 | 4,5:1 | nie przechodzi; zamień na `#767676` (4,54:1) lub ciemniejszy `#6B6B6B` (5,33:1) |
| `#FFFFFF` / `#3B82F6`, tekst 14 px | 3,68:1 | 4,5:1 | nie przechodzi; użyj `#2563EB` (5,17:1) |

Dodatkowo: odstęp wewnątrz karty 8 px, między kartami 24 px (trzykrotnie), skala typograficzna 14/16/20/25/31 (×1,25).
Panel boczny: wejście 250 ms ease-out, wyjście 200 ms ease-in; przy reduced motion samo przenikanie 100 ms.

## Checklista
- [ ] hierarchia w 3 poziomach, każdy różni się co najmniej dwoma środkami
- [ ] skala typograficzna i odstępów z tokenów; linia ≤ 75 znaków (sufit 80), interlinia ≥ 1,4 dla tekstu
- [ ] kontrast policzony dla każdej pary w obu motywach: 4,5:1 / 3:1 / 3:1 dla elementów UI
- [ ] kolor nie jest jedynym nośnikiem znaczenia; cele dotyku ≥ 24 px
- [ ] ruch ma cel, czasy z progów, wariant reduced motion
- [ ] marka nie łamie progów; przegląd wdrożenia z tolerancjami i listą różnic

## Materiały dodatkowe
- `references/typografia-kolor-siatka.md` — skala, długość linii, kontrast i jego poprawki, siatka, odstępy, ikony.
- `references/ruch-i-marka.md` — czasy i krzywe, reduced motion, nałożenie marki.
- `references/figma.md` — komponenty, warianty, auto layout, zmienne, przekazanie.
- `references/przeglad-wizualny.md` — zgodność wdrożenia z projektem i krytyka.

## Źródła
- W3C, WCAG 2.2: Understanding SC 1.4.3 Contrast (Minimum), 1.4.12 Text Spacing, 2.4.11 Focus Not Obscured (Minimum),
  2.5.8 Target Size (Minimum), 2.3.3 Animation from Interactions (dostęp 2026-10-17). SC 1.4.11 Non-text Contrast
  (3:1), 2.2.2 i 2.3.1 [niezweryfikowane w tej sesji, wartości z WCAG 2.1].
- Material Design 3 — tokeny ruchu (`md.motion.duration.short1` = 50 ms); pozostałe czasy w skillu to praktyka,
  nie wartości z Material [niezweryfikowane] (dostęp 2026-10-17).
- Figma Help Center: Guide to variables, Explore component properties (dostęp 2026-10-17).
- Bringhurst, *The Elements of Typographic Style* (45–75 znaków w linii, za wtórnym źródłem [niezweryfikowane]).
Opisane własnymi słowami; współczynniki kontrastu policzone wzorem WCAG (luminancja względna sRGB).
