**Wersja protokołu zawsze jawna**
- Każda odpowiedź, ADR, test i kod integracji podaje wersję **i edycję** protokołu: OCPP 1.6 / 2.0.1 / 2.1, OCPI 2.2.1 / 2.3, ISO 15118-2 / -20, DIN 70121.
- Brak wersji w zadaniu → pytasz albo sprawdzasz w kodzie (np. `Sec-WebSocket-Protocol`, endpoint `versions` OCPI); nie zakładasz najnowszej.
- Nie mieszasz słowników wersji (statusy, nazwy komunikatów, pola) — OCPP 2.x nie jest zgodne wstecz z 1.6.
- Wersji i dat standardów nie podajesz z pamięci: sprawdzasz w rejestrze albo u źródła, inaczej **[do weryfikacji]**.
