# Szablony: brief wykonawcy i raport audytu

## Brief dla wykonawcy (etap 1)
```
Audyt kodu — wymiar: <wymiar>. Głębokość: <szybki|standard|pełny>.
Zakres: <moduły / katalogi>; poza zakresem: <vendor/, kod generowany, …>.
Inwentarz (przeczytaj najpierw, nie skanuj repo od nowa): docs/project/07-review/<data>-audyt-inwentarz.md
Wczytaj skille: <skill-1>, <skill-2>.
Pytanie: <jedno pytanie, np. „Które miejsca pozwalają użytkownikowi odczytać cudze dane?”>
Nie zmieniaj kodu. Nie uruchamiaj skanów wobec działających systemów.
Wynik (≤ <N> ustaleń, najważniejsze pierwsze; „nic istotnego” jest poprawnym wynikiem):
| ID | plik:linia | ryzyko (1–4) | zasięg (1–3) | koszt naprawy (S/M/L) | dowód | propozycja |
Na końcu: czego nie sprawdziłeś i dlaczego (1–3 punkty).
```

## Raport (`docs/project/07-review/<data>-audyt-kodu.md`)
```markdown
---
artifact: review
phase: review
status: proposed
version: 1
author: <kto>
created: <data>
updated: <data>
inputs: [docs/project/07-review/<data>-audyt-inwentarz.md]
---
# Audyt kodu — <system>, <data>

## TL;DR
- Zakres: <wymiary>, głębokość <…>, budżet <…>.
- Blokery: <liczba> (niżej).
- Najważniejsze 3 ustalenia: <…>.

## Blokery (poza rankingiem, do decyzji od razu)
| ID | wymiary | plik:linia | dowód | propozycja |
|---|---|---|---|---|

## Ranking
Priorytet = ryzyko × zasięg ÷ koszt (S = 1, M = 2, L = 4).
| # | ID | wymiary | plik:linia | ryzyko | zasięg | koszt | priorytet | opis | propozycja | przekazanie |
|---|---|---|---|---|---|---|---|---|---|---|

## Top 10 — szkic zmiany
<!-- dla każdego: co zmienić, w skrócie diff albo kroki; nie wykonujesz -->

## Szybkie wygrane
<!-- koszt S przy ryzyku ≥ 2 -->

## Hipotezy do sprawdzenia (bez dowodu, poza rankingiem)

## Sprzeczności i decyzje dla człowieka
<!-- kto co rekomenduje, kompromis, proponowany ADR -->

## Czego nie sprawdzono
<!-- wymiary pominięte, brakujące narzędzia, moduły poza zakresem, ograniczenia środowiska -->

## Koszt audytu
| Etap | Wykonawcy | Modele | Koszt |
|---|---|---|---|
Razem: <kwota> z budżetu <kwota> (źródło: `python3 factory/cost_report.py --days 1`).

## Porównanie z poprzednim audytem (jeśli był)
| ID | status (ROZWIĄZANE / NOWE / ZMIENIONE) | uwagi |
|---|---|---|

## Przekazanie
- **Dla:** <człowiek / persona realizująca poprawki>.
- **Zadanie:** decyzje o blokerach i sprzecznościach, potem poprawki wg rankingu (osobne zadania).
- **Przeczytaj:** TL;DR, Blokery, Ranking.
```

Plik inwentarza (`<data>-audyt-inwentarz.md`) leży w tym samym katalogu, więc ma ten sam nagłówek (bez `inputs`
z inwentarza: `inputs: []`) oraz sekcje TL;DR i Przekazanie. Po zapisie: `python3 .claude/hooks/project_record.py check`.
