---
artifact: delivery
phase: delivery
status: proposed
version: 1
author: <agent>
created: <RRRR-MM-DD>
updated: <RRRR-MM-DD>
inputs: [docs/project/05-plan/plan.md]
---
# Realizacja kroku #<n>: <nazwa>

## TL;DR
<Co dostarczono, czy kryteria spełnione, co zostało.>

## Plan kroku (zatwierdzony przed kodem)
Zatwierdził: <kto, data>. Odstępstwo od planu = aktualizacja tej sekcji w tym samym commicie co kod.

### Stan końcowy
<Co jest prawdą po kroku i jak to sprawdzić — zachowanie, nie istnienie plików.>
### Poza zakresem
- <co świadomie NIE jest robione w tym kroku>
### Kluczowe decyzje
| Decyzja | Wybór | Dlaczego (1 zdanie) | Źródło (badanie / przeramowanie / plan) |
|---|---|---|---|
### Faza 1: <nazwa>
- `<ścieżka/plik>` — **Intencja:** po co zmiana (1–2 zdania). **Kontrakt:** sygnatura, pole schematu, trasa albo
  niezmiennik, którego nie wolno złamać. Fragment kodu tylko przy zmianie nieoczywistej.
- Kryteria automatyczne: `<polecenie>`
- Kryteria ręczne: <co ogląda człowiek>
### Ryzyka i otwarte pytania
<Puste przed startem realizacji — pytania rozstrzyga się przed kodem albo jawnie przyjmuje jako ryzyko.>
### Postęp
> `- [ ]` do zrobienia, `- [x]` zrobione; po commicie fazy dopisz ` — <sha>`. Numerów i tytułów nie zmieniasz.
#### Faza 1: <nazwa>
- [ ] 1.1 <kryterium automatyczne>
- [ ] 1.2 <kryterium ręczne> (ręczne)

## Zmiany
<commity / PR, najważniejsze pliki>
## Weryfikacja
<testy, lint, build — polecenia i wynik>
## Odstępstwa od planu i decyzje
## Decyzje człowieka vs propozycje AI
| Propozycja agenta | Decyzja człowieka | Dlaczego |
|---|---|---|
## Otwarte pytania
## Przekazanie
- **Dla:** <kolejny krok / przegląd>
