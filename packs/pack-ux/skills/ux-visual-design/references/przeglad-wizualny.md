# Przegląd zgodności wdrożenia i krytyka projektu

## Zgodność wdrożenia z projektem
1. **Zakres:** ekrany, szerokości (375, 768, 1280), motywy, stany (domyślny, hover, fokus, błąd, pusty, ładowanie).
2. **Materiał:** zrzut ze środowiska testowego w stałych warunkach (ta sama przeglądarka, skala 100%, ta sama
   treść) i ramka z Figmy w tej samej szerokości. Nakładka (overlay, tryb różnicy) albo zestawienie obok siebie.
3. **Sprawdź kolejno:** (a) tokeny — wartości z systemu, nie surowe (kolor, odstęp, promień, cień); (b) typografia —
   rozmiar, grubość, interlinia, zawijanie; (c) odstępy i wyrównania; (d) stany i fokus; (e) ruch; (f) ciemny motyw;
   (g) skrajne treści (długie, puste).
4. **Tolerancje:** odstępy i rozmiary ±1 px (wynik zaokrągleń), kolor 0 (wartość tokenu), czcionka — ten sam krój
   i grubość. Różnice poniżej tolerancji nie są uwagami. Różnica spowodowana błędem projektu (np. 7 px poza
   skalą) wraca do projektanta, nie do programisty.
5. **Wynik:** tabela `Nr | Ekran/stan | Oczekiwane (token) | Zastane | Waga | Właściciel`. Waga: blokuje
   (dostępność, kontrast, fokus), poprawić w tym wydaniu, kosmetyka. Regresję wizualną powtarzalnych komponentów
   automatyzuje się testami zrzutowymi (ux-design-systems).

## Krytyka projektu wizualnego
- Zaczynasz od celu i pytania autora; potem trzy kategorie: hierarchia (co widać najpierw), czytelność (kontrast,
  skala, linia), spójność (system, marka). Każda uwaga: obserwacja → skutek dla użytkownika → propozycja.
- Format: „Przycisk drugorzędny ma 2,6:1 względem tła, nie spełnia SC 1.4.11; ściemnij obrys do ≥ 3:1”, a nie
  „jest za blady”. Rozdziel to, co mierzalne (próg), od preferencji (oznacz „gust”, decyduje autor).
- Zamykasz listą ustaleń z właścicielami; nie przerabiasz cudzego projektu w trakcie krytyki.
