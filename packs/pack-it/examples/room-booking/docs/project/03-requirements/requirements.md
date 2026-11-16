---
artifact: requirements
phase: requirements
status: accepted
version: 1
author: użytkownik
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/01-discovery/brief.md]
---
# Wymagania: Rezerwacja sal i biurek

## TL;DR
6 historyjek MVP. Kluczowe atrybuty: brak podwójnych rezerwacji przy współbieżności, SSO M365, dostępność w godzinach pracy 99,5%.

## Historyjki (MVP)
| ID | Jako … chcę … aby … | Kryteria akceptacji | Priorytet |
|---|---|---|---|
| H1 | pracownik — zarezerwować salę na przedział czasu | Given sala wolna When rezerwuję Then rezerwacja i wpis w M365 | H |
| H2 | pracownik — zarezerwować biurko na dzień | jak H1 | H |
| H3 | facility — zablokować zasób do serwisu | zablokowany zasób niedostępny do rezerwacji | H |
| H4 | system — zwolnić rezerwację bez potwierdzenia obecności po 15 min | zasób wraca do puli | M |
| H5 | pracownik — widzieć kalendarz dostępności zasobów | widok dnia/tygodnia | H |
| H6 | pracownik — zalogować się kontem firmowym | SSO Entra ID | H |
## Atrybuty jakości (scenariusze — wejście dla architektury)
| Atrybut | Scenariusz | Priorytet |
|---|---|---|
| Spójność | 50 osób jednocześnie rezerwuje tę samą salę w 9:00 → dokładnie 1 sukces, reszta dostaje czytelną odmowę, 0 podwójnych rezerwacji | H,H |
| Bezpieczeństwo | logowanie tylko kontem firmowym Entra ID; dane w UE | H,M |
| Dostępność | 99,5% w godz. 7–19 | M,M |
| Modyfikowalność | nowy typ zasobu (np. miejsce parkingowe) w ≤ 2 dni pracy | H,M |
## Ograniczenia techniczne i organizacyjne
Azure (UE), zespół TS/Angular + Java, MVP 3 miesiące.
## Poza zakresem MVP
Rozliczenia, aplikacja natywna.

## Otwarte pytania
- [ ] Limity rezerwacji na osobę? → facility

## Przekazanie
- **Dla:** tomasz (solution architect)
- **Zadanie:** stack i styl architektury
- **Przeczytaj:** TL;DR, Atrybuty jakości, Ograniczenia
