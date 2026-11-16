---
artifact: adr
phase: architecture
status: accepted
version: 1
author: tomasz-solution-architect
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/03-requirements/requirements.md, docs/project/04-architecture/stack-decision.md]
---
# 0004. Integracja z M365: Microsoft Graph, uprawnienia aplikacyjne, outbox, synchronizacja w jedną stronę

## Kontekst
H1 wymaga wpisu rezerwacji sali w kalendarzu M365. Spójność rezerwacji (ADR-0002) nie może zależeć od dostępności
zewnętrznego API. Nie wiemy jeszcze, czy sale są skrzynkami zasobów (room mailbox) w Exchange i czy ludzie rezerwują je
bezpośrednio w Outlooku — wtedy powstają dwa źródła prawdy (otwarte pytanie do IT).

## Decyzja
**[propozycja, warunkowa — zależy od odpowiedzi IT]**
- Źródłem prawdy o dostępności jest aplikacja. Synchronizacja **w jedną stronę**: aplikacja → kalendarz M365 (utworzenie, zmiana, anulowanie wydarzenia).
- Rezerwacja i zdarzenie domenowe zapisywane w jednej transakcji (Spring Modulith Event Publication Registry, JDBC = outbox); moduł `calendarsync` wysyła do Graph asynchronicznie z ponowieniami. Awaria Graph nie cofa rezerwacji; UI pokazuje stan synchronizacji.
- Uprawnienie aplikacyjne `Calendars.ReadWrite` przyznane przez **Exchange Online RBAC for Applications** z zakresem ograniczonym do grupy pracowników i skrzynek sal (bez uprawnienia w całym tenancie w Entra). Uwierzytelnianie aplikacji do Graph przez Managed Identity lub certyfikat w Key Vault.
- Jeśli sale są skrzynkami zasobów: bezpośrednie rezerwacje w Exchange muszą zostać zablokowane (polityka rezerwacji skrzynki) albo decyzja o źródle prawdy wraca do użytkownika.

## Rozważane opcje
- Graph, uprawnienia aplikacyjne + outbox (wybrana) — zalety: rezerwacja niezależna od Graph, ponowienia, działa też dla zadań w tle (no-show release anuluje wydarzenie); wady: wymaga zgody administratora M365 i konfiguracji RBAC for Applications.
- Graph delegowany (On-Behalf-Of) synchronicznie w żądaniu — zalety: działa w imieniu użytkownika, węższe uprawnienia; wady: rezerwacja zależy od Graph w szczycie 9:00, zadania w tle (no-show) nie mają tokenu użytkownika.
- Zaproszenie iCalendar (.ics) mailem — zalety: brak uprawnień do kalendarzy; wady: użytkownik musi zaakceptować, brak automatycznego anulowania przy no-show, słabsze UX. Opcja zapasowa, jeśli IT nie udzieli zgody.
- Exchange jako źródło prawdy dla sal — odrzucone wstępnie: gwarancja „0 podwójnych” wyszłaby poza naszą bazę i poza scenariusz (H,H).

## Konsekwencje
- Spójność ostateczna między aplikacją a Outlookiem (sekundy–minuty) — akceptowalne, bo o dostępności decyduje aplikacja.
- Potrzebne: rejestracja aplikacji w Entra, zgoda administratora, zakres RBAC w Exchange (spike S3), test na tenancie deweloperskim (S2).
- Pierwsze cięcie pionowe (H6 + H1) może powstać bez synchronizacji — `calendarsync` dołączamy po S2/S3.
