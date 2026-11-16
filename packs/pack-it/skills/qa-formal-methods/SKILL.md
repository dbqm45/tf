---
name: qa-formal-methods
description: Użyj przy weryfikacji formalnej — kiedy warto, Z3, TLA+/TLC, Alloy, kontrprzykład jako test AC-n, granice modelu.
metadata:
  review: "2027-11-15"
  catalog: "Użyj, gdy przykłady i losowanie nie wystarczą jako wyrocznia — współbieżność i ponowienia, protokoły i maszyny stanów, reguły kombinatoryczne z limitem; wybór szczebla (kontrakty, testy właściwości, solver SMT Z3, model checking TLA+/TLC lub Alloy, Dafny), kontrprzykład jako test akceptacyjny z AC-n, granice modelu w raporcie, model obok kodu. Nie do projektowania agregatów i ich niezmienników (ddd-tactical-design) ani składni Hypothesis (tool-pytest)."
  keywords: "weryfikacja formalna, metody formalne, zweryfikować formalnie, TLA+, PlusCal, TLC, Alloy, Z3, solver SMT, model checking, udowodnić, że żadna kombinacja, wyścig przy rezerwacji, podwójna rezerwacja, protokół synchronizacji, kontrprzykład, poprawność protokołu, projekt protokołu, przeploty, blokada optymistyczna, ponowienie po timeoucie"
---

# Metody formalne jako wyrocznia

Współbieżność i ponowienia, protokoły i maszyny stanów, reguły kombinatoryczne z limitem: wyrocznią jest solver
(Z3) albo model checker (TLA+/TLC, Alloy), a nie losowanie. Nie cały moduł — 1–3 właściwości o najwyższym koszcie błędu.

## Procedura
0. **Najtańszy szczebel, który wyraża właściwość:** kontrakty i asercje → testy właściwości (Hypothesis, fast-check)
   → solver Z3 → model checking (TLA+/TLC, Alloy) → Dafny. Wyżej tylko wtedy, gdy niższy nie umie wyrazić właściwości
   albo nie trafia w próg lub przeplot. Zespół bez doświadczenia zaczyna od testów właściwości i Z3.
1. Właściwość z kryterium `AC-n`; model tylko ze stanu i kroków, które jej dotyczą; narzędzie szuka negacji.
2. **Kontrprzykład → test akceptacyjny z `AC-n`** (czerwony przed poprawką, widoczny w `tf trace`); poprawka najpierw
   w modelu, potem w kodzie.
3. „Brak kontrprzykładu” raportujesz **z granicami modelu** (liczba procesów, zakres liczb, głębokość) — to nie dowód
   dla produkcji. Kwoty w groszach albo z zaokrągleniem jak w kodzie.
4. Model w repozytorium obok kodu; zmiana protokołu bez zmiany modelu to ustalenie w przeglądzie.

## Przykład
Trzy uruchomione modele z wynikami: `references/formal-methods.md`.
- **Z3, reguły rabatowe:** `sat` → koszyk 0,50 zł z rabatem lojalnościowym 20 zł daje ujemną cenę; z limitem w kodzie `unsat`.
- **TLA+/TLC, ponowienie po zgubionej odpowiedzi:** ślad 6 stanów kończy się dwiema rezerwacjami jednego klienta;
  z kluczem idempotencji brak naruszenia w 382 stanach (2 klientów, 3 miejsca, 1 ponowienie).
- **Alloy, uprawnienia przez zagnieżdżone grupy:** podgrupa innego najemcy daje dostęp do cudzej faktury; z regułą
  dla podgrup `UNSAT` w zakresie 4.
Każdy kontrprzykład ma gotowy test `AC-n` i raport z granicami modelu.

## Źródła
- Z3 (`z3-solver` 4.15.4), TLA+ (`tla2tools.jar` z wydania v1.8.0, TLC rev bc1b506), Alloy 6.2.0 — przykłady
  uruchomione 2026-11-15; wersje i polecenia w `references/formal-methods.md` §Źródła.
Opisane własnymi słowami.
