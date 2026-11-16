---
artifact: requirements
phase: requirements
status: accepted
version: 1
author: ewa
created: 2026-09-20
updated: 2026-09-22
inputs: []
---
# Wymagania: wycena zamówienia

## TL;DR
Rabat ilościowy przy wycenie pozycji zamówienia: progi 10 i 50 sztuk, kwoty w groszach.

## H1 Rabat ilościowy
Jako klient hurtowy chcę dostać rabat przy większym zamówieniu, żeby opłacało mi się kupować więcej.

- **H1-AC1:** poniżej 10 sztuk — brak rabatu.
- **H1-AC2:** od 10 sztuk włącznie — rabat 5% od wartości pozycji.
- **H1-AC3:** od 50 sztuk włącznie — rabat 10% (rabaty się nie sumują).
- **H1-AC4:** ilość musi być liczbą całkowitą ≥ 1; inaczej wycena jest odrzucana (błąd).
- **H1-AC5:** kwoty w groszach; wynik zaokrąglany do pełnego grosza (połówka w górę).

Przykład od działu sprzedaży: 10 szt. × 19,99 zł = 189,91 zł (199,90 zł − 5% = 189,905 → 189,91).

## Otwarte pytania
- [x] Czy rabaty się sumują? → Nie (sprzedaż, 2026-09-21).

## Przekazanie
- **Dla:** kasia
- **Zadanie:** plan testów i testy automatyczne wyceny
- **Przeczytaj:** H1
