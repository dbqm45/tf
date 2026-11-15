---
name: qa-formal-methods
description: Użyj przy weryfikacji formalnej — kiedy warto, Z3, TLA+/TLC, Alloy, kontrprzykład jako test AC-n, granice modelu.
metadata:
  przeglad: "2027-11-15"
  katalog: "Użyj, gdy przykłady i losowanie nie wystarczą jako wyrocznia — współbieżność i ponowienia, protokoły i maszyny stanów, reguły kombinatoryczne z limitem; wybór szczebla (kontrakty, testy właściwości, solver SMT Z3, model checking TLA+/TLC lub Alloy, Dafny), kontrprzykład jako test akceptacyjny z AC-n, granice modelu w raporcie, model obok kodu. Nie do projektowania agregatów i ich niezmienników (ddd-tactical-design) ani składni Hypothesis (tool-pytest)."
  slowa: "weryfikacja formalna, metody formalne, zweryfikować formalnie, TLA+, PlusCal, TLC, Alloy, Z3, solver SMT, model checking, udowodnić, że żadna kombinacja, wyścig przy rezerwacji, podwójna rezerwacja, protokół synchronizacji, kontrprzykład, poprawność protokołu, projekt protokołu, przeploty, blokada optymistyczna, ponowienie po timeoucie"
---

# Metody formalne jako wyrocznia

Współbieżność i ponowienia, protokoły i maszyny stanów, reguły kombinatoryczne z limitem: wyrocznią jest solver
(Z3) albo model checker (TLA+/TLC, Alloy), a nie losowanie. Nie cały moduł — 1–3 właściwości o najwyższym koszcie błędu.

## Procedura
1. Właściwość z kryterium `AC-n`; model tylko ze stanu i kroków, które jej dotyczą; narzędzie szuka negacji.
2. **Kontrprzykład → test akceptacyjny z `AC-n`** (czerwony przed poprawką, widoczny w `tf trace`); poprawka najpierw
   w modelu, potem w kodzie.
3. „Brak kontrprzykładu” raportujesz **z granicami modelu** (liczba procesów, zakres liczb, głębokość) — to nie dowód
   dla produkcji. Kwoty w groszach albo z zaokrągleniem jak w kodzie.
4. Model w repozytorium obok kodu; zmiana protokołu bez zmiany modelu to ustalenie w przeglądzie.

## Przykład
Kiedy który szczebel, granice wyniku i uruchomiony przykład Z3 (rabat ujemny przy koszyku 0,50 zł):
`references/metody-formalne.md`.

## Źródła
- Z3 (`z3-solver` 4.15.4) — przykład uruchomiony 2026-11-15.
Opisane własnymi słowami.
