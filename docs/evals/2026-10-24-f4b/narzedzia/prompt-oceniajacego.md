# Prompt ślepej oceny (F4, v2–v4)

Jeden oceniający (Sonnet) na repozytorium; dokumenty obu narzędzi w katalogach A i B w losowej kolejności, nazwy narzędzi
zastąpione (`tool`, `evidence-check`, `cards-render`, `repo-scan`), karty JSON i `raw/` pominięte. `<repo>` i `<katalog>`
podstawiasz.

```text
Jesteś niezależnym oceniającym w benchmarku. Dwa narzędzia (A i B, nie wiesz które jest które i nie próbuj zgadywać)
wygenerowały dokumentację projektu z samego kodu. Oceń je wobec złotego standardu i kodu. Tylko odczyt; niczego nie
uruchamiaj i nie edytuj poza plikiem wyniku.

Pliki:
- złoty standard: gold/<repo>.json (20 faktów z dowodami w kodzie)
- dokumenty A: <katalog>/<repo>/A/ (wszystkie pliki .md)
- dokumenty B: <katalog>/<repo>/B/
- kod repozytorium: repos/<repo>/

Zadanie 1 — pokrycie: dla każdego faktu ze złotego standardu oceń A i B osobno: "tak" (fakt podany poprawnie,
merytorycznie, nie tylko słowo kluczowe), "częściowo" (wspomniany niepełnie), "nie" (brak), "błędnie" (dokument
twierdzi coś sprzecznego). Podaj krótki cytat lub plik dokumentu jako uzasadnienie.
Zadanie 2 — poprawność: z każdego zestawu (A, B) wybierz losowo 10 konkretnych twierdzeń o projekcie (nie ogólników;
rozłóż je na różne pliki) i sprawdź każde w kodzie repozytorium: "prawda", "fałsz", "nieweryfikowalne". Podaj
plik:linia kodu, na którym opierasz ocenę.

Zapisz wynik do <katalog>/<repo>/verdict.json: {"coverage": [{"id", "A", "B", "why_A", "why_B"}],
"precision": {"A": [{"claim", "verdict", "code"}], "B": [...]}, "summary": {...}}. Odpowiedz krótko podsumowaniem liczb.
```

Punktacja: tak = 1, częściowo = 0,5; kategorie wg pola `category` w złotym standardzie.
