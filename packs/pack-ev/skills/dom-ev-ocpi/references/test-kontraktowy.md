# Test kontraktowy OCPI z partnerem

Spis treści: 1. Zasady · 2. Scenariusze minimalne · 3. Dowód i zapis · 4. Gdy partner zawiedzie

Źródło: wnioski ze specyfikacji OCPI (`v2.2.1-d2`, `v2.3.0`, czytane 2026-10-20). Sandboxy partnerów, narzędzia i atrapy
oparte na specyfikacji, anonimizacja nagranych logów: `.claude/skills/dom-ev-simulation-testing/references/kontrakt-ocpi-i-regresja.md`.

## 1. Zasady
- Testujesz **oba kierunki**: jako Sender i jako Receiver (własny interfejs wobec partnera i jego wobec ciebie).
- Wersja i tag specyfikacji zapisane przed testem; ten sam zestaw na każdą wersję (2.2.1 i 2.3.0).
- Środowisko partnera (sandbox) z osobnymi tokenami; nigdy dane produkcyjne kierowców bez zgody.
- Wynik testu to odpowiedź OCPI i HTTP, nagłówki i obiekt po drugiej stronie, nie samo „200”.

## 2. Scenariusze minimalne
| # | Scenariusz | Oczekiwany dowód |
|---|---|---|
| 1 | Handshake A→B→C, potem wywołanie modułu tokenem C | odpowiedź 1000; token A po handshake daje 401 poza `credentials`/`versions` |
| 2 | Ponowne POST `credentials` po rejestracji | HTTP 405 |
| 3 | Zły i brakujący `Authorization`; token bez Base64 | 401; ustal, czy partner wymaga Base64 |
| 4 | `versions` i szczegóły: wspólne moduły, role `SENDER`/`RECEIVER` | brak oczekiwanego modułu → 3003 |
| 5 | Pull z paginacją: `limit` mniejszy od liczby obiektów | `Link` `rel="next"`, `X-Total-Count`, `X-Limit` zgodne; ostatnia strona bez `Link` |
| 6 | Locations PUT → PATCH statusu EVSE → `REMOVED` | partner pokazuje zmianę; obiekt nie znika |
| 7 | Sessions: PUT, kilka PATCH z `charging_periods`, PATCH końcowy `COMPLETED` | okresy dopisane bez dubli; PUT z pustą listą czyści okresy |
| 8 | PATCH Session bez `last_updated` | 2001 |
| 9 | PUT z `{id}` w URL innym niż w obiekcie | 2001 |
| 10 | Tokens: PUT, PATCH `valid:false`, `POST authorize` dla `whitelist` `NEVER` | `AuthorizationInfo` ze statusem; nieznany token → 2004 |
| 11 | Authorize bez `LocationReferences` (gdy partner wymaga lokalizacji) | 2002 |
| 12 | Commands `START_SESSION` → `CommandResponse` → `CommandResult` na `response_url` | wynik przychodzi osobno; scenariusz `TIMEOUT` |
| 13 | Nieznane pole w JSON (2.3.0) | przyjęte bez błędu |
| 14 | Przez hub: nagłówki `OCPI-from/to-*` w żądaniu i odwrócone w odpowiedzi | 4001/4003 dla nieznanego lub niepołączonego odbiorcy |
Scenariusze CDR i taryf: `dom-ev-cdr-settlement`, `dom-ev-tariffs-pricing` (kalkulator
`.claude/skills/dom-ev-tariffs-pricing/scripts/ocpi_tariff_calc.py <taryfa>.json <okresy>.json [--cdr <cdr>.json] [--json]`).

## 3. Dowód i zapis
Dla każdego scenariusza zapisz: wersja i tag, adres, żądanie (bez tokenów), HTTP, `status_code`, nagłówki paginacji,
stan obiektu po drugiej stronie (GET), wynik zgodny/niezgodny. Odchylenia partnera trafiają do karty partnera (kraj +
party_id, wersja, odchylenie, obejście). Niezgodność ze specyfikacją ≠ błąd po twojej stronie: oznacz i zgłoś partnerowi.

## 4. Gdy partner zawiedzie
| Objaw | Pierwsza hipoteza |
|---|---|
| 401 po handshake | token bez Base64 albo użyty token A zamiast C |
| 404 na PUT/GET | trójka `country_code`/`party_id` spoza `roles` z handshake |
| Dublujące się okresy w sesji | PATCH ponawiany po timeoucie, partner dopisuje |
| Pull zwraca mniej niż `X-Total-Count` | limit serwera, ignorowany `limit`; idź po `Link` |
| Komenda `ACCEPTED`, brak sesji | brak `CommandResult` albo `TIMEOUT`; sprawdź OCPP po stronie CPO |
| Hub zwraca 4001 | nieznany odbiorca w `OCPI-to-*` |
| 3003 przy rejestracji | partner nie wystawia oczekiwanego modułu |
