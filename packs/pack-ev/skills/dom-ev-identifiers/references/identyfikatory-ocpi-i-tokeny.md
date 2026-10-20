# OCPI: strony, uid vs evse_id, tokeny

## Adresowanie strony i obiektu
- `country_code` — CiString(2), ISO 3166-1 alpha-2 kraju CPO; `party_id` — CiString(3), ID strony wg ISO 15118
  (pierwotne: OCPI 2.2.1, mod_locations).
- Para `country_code` + `party_id` identyfikuje **stronę** (CPO lub eMSP), nie punkt ładowania ani kierowcę.
- Obiekty adresuje trójka `{country_code}/{party_id}/{id}` (`.claude/skills/dom-ev-charging/references/ocpi.md`).

## uid vs evse_id
| Pole | Rola | Kto nadaje |
|---|---|---|
| `uid` | odrębny identyfikator obiektu w OCPI (pierwotne: odrębny od `evse_id`); rola klucza przy PUT/PATCH — [do weryfikacji] | zapewne CPO [do weryfikacji] |
| `evse_id` | identyfikator „branżowy” punktu, CiString(48), opcjonalny, format wg eMI3 V1.0 Part 2 | operator |

Nie wnioskuj jednego z drugiego i nie używaj `evse_id` jako klucza zamiast `uid`; `evse_id` bywa pusty.

## Trzy różne identyfikatory kierowcy
| Identyfikator | Co identyfikuje | Kto wystawia |
|---|---|---|
| UID karty RFID | fizyczny nośnik (numer odczytany z karty) | producent / wydawca karty |
| token OCPI (`uid` tokenu) | uprawnienie do autoryzacji, synchronizowane przez moduł Tokens | eMSP |
| EMAID / Contract ID | kontrakt e-mobilności (m.in. Plug & Charge) | eMSP |

UID karty ≠ kontrakt: to różne rzeczy (nośnik vs umowa); wiąże je eMSP [wiedza ogólna, do weryfikacji]. Tokeny w OCPI
przenosi eMSP do CPO, a CPO używa ich lokalnie przy `Authorize` w OCPP (`.claude/skills/dom-ev-charging/references/ocpi.md`).
Mapowanie EMAID → token/konto to zadanie systemu, nie reguła standardu.

## Kto nadaje ID
Operator nadaje `evse_id` swoim punktom; eMSP nadaje kontrakty (EMAID) i tokeny. Urzędy / rejestry przydzielające
kody operatorów (część `party_id`, ID operatora w EVSE) w poszczególnych krajach: brak w źródłach [do weryfikacji].
