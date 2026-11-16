---
artifact: review
phase: review
status: draft
version: 1
author: kasia
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/05-plan/test-plan.md]
---
# Zgłoszenia defektów: wycena pozycji zamówienia — rabat ilościowy (H1)

## TL;DR
Automatyzacja planu TC-001..TC-014 (src/pricing.spec.ts) wykryła 2 defekty w src/pricing.ts: (1) próg rabatu 5%/10%
liczony jako `quantity > 10` zamiast `>= 10` (H1-AC2/AC3 mówią "od 10 sztuk włącznie") — dla qty=10 kod nie nalicza
rabatu (TC-003, TC-008); (2) brak walidacji całkowitości ilości (H1-AC4) — `orderTotal` odrzuca tylko qty<1, przepuszcza
wartości niecałkowite jak 2.5 czy 9.999999 (TC-012, TC-013). Testy dla obu grup zostawione jako `it.fails` w spec ze
wskazaniem oczekiwanej (poprawnej) wartości ze specyfikacji — nie zmieniano oczekiwań pod kod.

## Przekazanie
Do decyzji: poprawka `discountRate` (`>=` zamiast `>`) oraz dodanie walidacji `Number.isInteger(quantity)` w
`orderTotal` (z jednoznacznym mechanizmem błędu — patrz otwarte pytanie niżej). Po poprawce zdjąć `it.fails` →
`it` w `src/pricing.spec.ts` (TC-003, TC-008, TC-012, TC-013).

## DEFEKT-01: próg rabatu liczony jako `> 10` zamiast `>= 10`
- **Testy dotknięte:** TC-003, TC-008
- **Wymaganie:** H1-AC2 / H1-AC3 — rabat 5%/10% obowiązuje "od 10 sztuk włącznie"
- **Oczekiwany wynik (TC-003):** qty=10, cena=1999 gr → 18991 gr (5% rabatu)
- **Rzeczywisty wynik:** `discountRate(10)` zwraca 0 (bo `10 > 10` jest fałszywe) → `orderTotal(1999, 10)` = 19990 gr
- **Oczekiwany wynik (TC-008):** qty=10, cena=11 gr → 105 gr
- **Rzeczywisty wynik:** brak rabatu → 110 gr
- **Lokalizacja:** `src/pricing.ts:5` (`if (quantity > 10) return 0.05;`)
- **Hipoteza:** defekt w kodzie (klasyczny błąd "o jeden" na progu) — wymaganie i przykład sprzedaży w
  `docs/project/05-plan/test-plan.md` (TC-003) jednoznacznie wskazują próg włącznie.
- **Rekomendacja:** zmienić warunki na `quantity >= 10` (próg 5%) i `quantity >= 50` (próg 10%, już poprawny —
  ale sprawdzić spójność po zmianie kolejności warunków).

## DEFEKT-02: brak walidacji całkowitości ilości (H1-AC4)
- **Testy dotknięte:** TC-012, TC-013
- **Wymaganie:** H1-AC4 — ilość musi być liczbą całkowitą ≥1, w przeciwnym razie wycena odrzucona
- **Oczekiwany wynik (TC-012):** qty=2.5 → wycena odrzucona (błąd walidacji)
- **Rzeczywisty wynik:** `orderTotal(1999, 2.5)` nie rzuca wyjątku — sprawdzany jest tylko `quantity < 1`
- **Oczekiwany wynik (TC-013):** qty=9.999999 → wycena odrzucona, NIE traktowane jak qty=10
- **Rzeczywisty wynik:** brak walidacji całkowitości; wartość przechodzi przez `discountRate`/`orderTotal` bez błędu
- **Lokalizacja:** `src/pricing.ts:10` (`if (quantity < 1) throw new RangeError(...)`)
- **Hipoteza:** luka w implementacji względem wymagania AC4 (walidacja niepełna) — możliwa też dwuznaczność w
  wymaganiach co do mechanizmu zgłaszania błędu (patrz otwarte pytanie niżej).
- **Rekomendacja:** dodać warunek `!Number.isInteger(quantity)` do walidacji wejścia, zgłaszany tym samym
  mechanizmem co `quantity < 1` (obecnie wyjątek `RangeError`).

## Otwarte pytanie
Plan testów (TC-010..TC-013) określa oczekiwany wynik jako "wycena odrzucona (błąd walidacji)", ale nie precyzuje
mechanizmu (wyjątek vs wynik z flagą `ok:false`). Kod obecnie używa wyjątku (`RangeError`) — testy zaadaptowano do
tego mechanizmu (`toThrow()`). Jeśli docelowo wymagany jest wynik z flagą błędu (Result), to osobna zmiana kontraktu
funkcji, nie tylko poprawka walidacji — do potwierdzenia z właścicielem wymagań przed implementacją poprawki.
