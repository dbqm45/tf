---
artifact: brief
phase: discovery
status: accepted
version: 1
author: użytkownik
created: 2026-09-27
updated: 2026-09-27
inputs: []
---
# Brief: Rezerwacja sal i biurek

## TL;DR
Firma (300 osób, model hybrydowy) rezerwuje sale i biurka w arkuszu — dochodzi do podwójnych rezerwacji. Cel: aplikacja webowa
do samoobsługowych rezerwacji z integracją z kalendarzem Microsoft 365. Sukces: 90% rezerwacji samoobsługowo w 3 miesiące,
zero podwójnych rezerwacji. Ograniczenia: MVP w 3 miesiące, zespół 2 × TypeScript/Angular + 1 × Java, hosting Azure w UE.

## Problem i kontekst
Rezerwacje w współdzielonym arkuszu Excel; konflikty i „martwe” rezerwacje (nikt nie przyszedł).
## Użytkownicy i interesariusze
Pracownicy (rezerwują), recepcja/facility (zarządza zasobami, blokuje do serwisu), IT (utrzymanie).
## Cele i miary sukcesu
| Cel | Miara | Wartość docelowa |
|---|---|---|
| Samoobsługa | % rezerwacji przez aplikację | 90% po 3 mies. |
| Brak konfliktów | podwójne rezerwacje | 0 |
## Zakres
- W zakresie: rezerwacja sal i biurek na przedziały czasu, blokady serwisowe, zwalnianie nieodebranych rezerwacji, SSO Microsoft (Entra ID), zapis do kalendarza M365.
- Poza zakresem: rozliczenia kosztów, aplikacja mobilna natywna.
## Ograniczenia
MVP 3 miesiące; zespół 2 × TS/Angular, 1 × Java (Spring); hosting Azure, dane w UE; budżet utrzymania niski.
## Typ projektu
greenfield

## Otwarte pytania
- [ ] Czy biurka mają przypisane strefy/uprawnienia? → facility

## Przekazanie
- **Dla:** tomasz (solution architect)
- **Zadanie:** rekomendacja stacku i stylu architektury (04-architecture/stack-decision.md)
- **Przeczytaj:** TL;DR, Zakres, Ograniczenia oraz wymagania (03-requirements)
- **Gotowe, gdy:** stack-decision.md ma status proposed i przechodzi project_record.py check
