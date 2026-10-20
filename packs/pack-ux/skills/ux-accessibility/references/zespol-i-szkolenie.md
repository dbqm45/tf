# Dostępność w zespole — DoD, role, szkolenie

Spis treści: 1. Definicja ukończenia · 2. Role · 3. Plan szkolenia · 4. Metryki

## 1. Definicja ukończenia (DoD) komponentu i zadania
- Komponent: działa z samą klawiaturą, ma nazwę dostępną i rolę, kontrasty z tokenów, stany fokus/błąd/wyłączony, test
  z czytnikiem na jednej parze, adnotacje w dokumentacji komponentu.
- Zadanie: kryteria akceptacji zawierają zachowanie z klawiatury i komunikaty; automat w CI bez nowych błędów.
- Wydanie: lista kontrolna ścieżek kluczowych; nowe ustalenia trafiają do rejestru z wagą.

## 2. Role
| Rola | Odpowiada za |
|---|---|
| Projektant | kontrast, hierarchia, adnotacje (nagłówki, landmarki, kolejność fokusu), cele dotykowe |
| Autor treści | nagłówki, linki, alternatywy, prosty język (ux-content-design) |
| Programista | semantyka HTML, klawiatura, ARIA tylko gdy trzeba (fe-web-platform) |
| QA | ścieżki z klawiaturą i czytnikiem (qa-exploratory-manual) |
| Specjalista ds. dostępności | audyt, raport, plan, szkolenie, kontakt z prawnikiem |
| Właściciel produktu | priorytety napraw, deklaracja, budżet |

## 3. Plan szkolenia (3 sesje po 90 minut)
1. **Doświadczenie**: godzina bez myszy; nawigacja serwisu czytnikiem ekranu (NVDA lub VoiceOver) z nagraniem osoby
   korzystającej na co dzień; cel — zrozumieć, nie zaliczyć.
2. **Rola**: ćwiczenia dla ról z p. 2 na własnym produkcie (naprawa 3 realnych ustaleń).
3. **Proces**: DoD, zgłaszanie ustaleń, gdzie szukać pomocy; wyznaczenie „championa” w każdym zespole.
Powtarzaj dla nowych osób; część materiałów w onboardingu.

## 4. Metryki
Liczba otwartych ustaleń wg wagi i trend; odsetek ścieżek kluczowych przetestowanych czytnikiem w tym wydaniu; czas od
zgłoszenia do naprawy krytycznych; liczba zgłoszeń od użytkowników. Nie mierz wyłącznie wynikiem automatu.
