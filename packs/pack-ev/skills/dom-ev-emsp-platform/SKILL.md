---
name: dom-ev-emsp-platform
description: Użyj przy platformie eMSP i aplikacji kierowcy — tokeny i karty RFID, mapa i status EVSE, start zdalny, rozliczenie kierowcy, zgłoszenia „nie startuje”, CarPlay.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy projektujesz lub diagnozujesz platformę eMSP i doświadczenie kierowcy — konto kierowcy, tokeny OCPI (RFID, APP_USER, AD_HOC_USER, EMAID, whitelist, valid, wydanie, blokada i zgubienie karty), synchronizacja tokenów z CPO, mapa z Locations (własne i roamingowe źródła, deduplikacja, opóźnienie statusu EVSE, filtry, jakość danych, AFIR art. 20, NEVI 680.116), CarPlay i Android Auto, start i stop zdalny z aplikacji (Commands i asynchroniczny wynik), postęp sesji, cena przed startem, faktura i historia kierowcy, typowe zgłoszenia do wsparcia i to, co aplikacja musi pokazać. Nie do protokołu OCPI — handshake, endpointy, kody (dom-ev-ocpi), płatności ad hoc na stacji (dom-ev-payments), flot i kart flotowych (dom-ev-fleet-charging), liczenia ceny z taryfy (dom-ev-tariffs-pricing), korekt CDR (dom-ev-cdr-settlement) ani mechaniki Plug & Charge (dom-ev-iso15118)."
  slowa: "aplikacja kierowcy, app eMSP, konto kierowcy, karta RFID, zgubiona karta, zablokować kartę, nowa karta RFID, token aplikacji, APP_USER, AD_HOC_USER, whitelist tokenu, kontrakt Plug & Charge, mapa ładowarek, wyszukiwarka stacji, filtr złącza, filtr mocy, status wolne zajęte, status w czasie rzeczywistym, opóźnienie statusu, duplikaty stacji, deduplikacja, dane roamingowe, jakość danych lokalizacji, godziny otwarcia, udogodnienia, CarPlay, Android Auto, nawigacja do ładowarki, start z aplikacji, remote start, kręci się i nie startuje, historia ładowań, faktura kierowcy, abonament ładowania, nie startuje, wolno ładuje, zła cena, karta nie działa, ticket wsparcia, driver app, driver support, charging map, EVSE availability, app does not start charging"
---

# Platforma eMSP i doświadczenie kierowcy

Skill dotyczy tego, co eMSP buduje **dla kierowcy** na danych od CPO: konto i tokeny, mapa, start z aplikacji,
sesja, rozliczenie, wsparcie. Protokół OCPI (handshake, endpointy, kody) opisuje `dom-ev-ocpi`; w tym skillu
jest tylko to, co zmienia decyzje produktu i backendu. Role stron: `dom-ev-market-roles`.

## Mapa pojęć: skąd co pochodzi
| Co widzi kierowca | Dane / mechanizm | Właściciel | Skill szczegółowy |
|---|---|---|---|
| konto, karta, token aplikacji | OCPI Tokens (eMSP → CPO) | **eMSP** | ten skill, `references/konto-i-tokeny.md` |
| mapa, złącza, moc, godziny | OCPI Locations (CPO → eMSP) | CPO | ten skill, `references/mapa-i-dostepnosc.md` |
| „wolne / zajęte” | `EVSE.status`, push PATCH | CPO | j.w. |
| cena przed startem | OCPI Tariffs (`tariff_ids` na Connectorze) | CPO | `dom-ev-tariffs-pricing` |
| przycisk Start / Stop | OCPI Commands → OCPP | CPO wykonuje, eMSP woła | `references/start-zdalny-i-sesja.md` |
| postęp sesji | OCPI Sessions (+ `charging_periods`) | CPO | j.w. |
| faktura, historia | OCPI CDRs → faktura eMSP | CPO → eMSP | `references/rozliczenie-i-wsparcie.md`, `dom-ev-cdr-settlement` |
| zgłoszenie do wsparcia | wszystkie powyższe | — | `references/rozliczenie-i-wsparcie.md` |

Zasada nadrzędna: eMSP **nie jest źródłem prawdy** o stacji, cenie ani sesji, tylko o kierowcy i jego tokenach.
Aplikacja pokazuje stan z ostatniej wiadomości od CPO razem z jej wiekiem, a nie „stan na pewno aktualny”.

## 1. Konto kierowcy i tokeny
Jedno konto kierowcy ma wiele nośników autoryzacji. Każdy jest osobnym tokenem OCPI, a para (`uid`, `type`) jest
unikalna u eMSP (`dom-ev-identifiers`: UID karty, token i kontrakt to trzy różne identyfikatory).

| Nośnik | `type` | `whitelist` (zalecenie specyfikacji / praktyka) | Uwagi |
|---|---|---|---|
| karta RFID | `RFID` | `ALWAYS` lub `ALLOWED`; `NEVER` wydłuża autoryzację przy czytniku | używana lokalnie przy stacji; blokada działa dopiero po propagacji |
| token aplikacji | `APP_USER` | zalecany `NEVER` | stały dla konta, używany tylko w komendach eMSP |
| jednorazowy | `AD_HOC_USER` | zalecany `NEVER` | wiąże sesję z klientem bez konta stałego |
| kontrakt Plug & Charge | `EMAID` (OCPI 2.3.0) | eMSP **nie pcha** tokenów tego typu | CPO poznaje wystawcę ze stacji i pyta eMSP real-time; certyfikaty poza OCPI (`dom-ev-iso15118`) |

**Wydanie karty:** utwórz token z `valid: true`, `uid`, `visual_number` (numer widoczny na karcie), `issuer`,
`contract_id` (EMAID, `dom-ev-identifiers`), `group_id` tylko gdy karty mają działać parami; PUT do CPO i potwierdź GET-em.
**Blokada lub zgubienie:** nie usuwaj tokenu; wyślij PATCH z `valid: false` i nowym `last_updated`. Dla tokenów
`whitelist: ALWAYS` CPO autoryzuje z pamięci podręcznej, więc blokada działa dopiero po tym, jak CPO przetworzy
PATCH. Dla `NEVER` i `ALLOWED_OFFLINE` zapytanie real-time zwróci `BLOCKED`. Trwającej sesji karta zablokowana nie
przerywa sama, więc przy kradzieży wyślij `STOP_SESSION`. **Nowa karta:** nowy token na to samo konto, historia
zostaje przy koncie (CDR wiążesz z kontem przez `cdr_token`), nie przy karcie.

## 2. Mapa i dostępność
Źródła: własne i roamingowe Locations (OCPI), hub, dane otwarte. Cztery decyzje, każda w `references/mapa-i-dostepnosc.md`:
1. **Model:** Location → EVSE → Connector; dostępność czytasz z **EVSE**, a filtr złącza z **Connectora**
   (`standard`, `format`, `power_type`, `max_electric_power`).
2. **Świeżość:** status idzie CPO → push PATCH → eMSP, a w drodze są opóźnienia. Pokaż wiek statusu, a po
   przekroczeniu progu wiek zamiast „wolne”. `UNKNOWN` oznacza także stację offline.
3. **Deduplikacja:** ta sama stacja z kilku źródeł. Klucz: `evse_id` (jeśli jest), inaczej para
   (`country_code`, `party_id`, `Location.id`) z źródła + bliskość współrzędnych jako sygnał do ręcznego scalenia.
   Nigdy nie scalaj tylko po współrzędnych.
4. **Wymogi danych:** AFIR art. 20 (dane statyczne i dynamiczne dostępne przez NAP) wiąże operatora punktu; eMSP, który
   wyświetla dane, korzysta z nich i odpowiada za ich prezentację. Zakres: `dom-ev-regulations-eu`.

## 3. Start zdalny i sesja
`ACCEPTED` w odpowiedzi na `START_SESSION` mówi tylko, że CPO przyjął komendę. Prawdziwy wynik przychodzi POST-em
na `response_url` (`CommandResult`), a sesja istnieje dopiero jako OCPI Session. Aplikacja ma więc cztery stany:
„wysyłam”, „stacja przyjęła, czekam na kabel/start”, „ładuje” (Session `ACTIVE`), „nie udało się” (z powodem).
Limit czasu = `timeout` z odpowiedzi CPO. Szczegóły, mapowanie `CommandResult` na komunikaty i idempotencja:
`references/start-zdalny-i-sesja.md`. Kolejność OCPP+OCPI: `dom-ev-session-lifecycle`.

## 4. Rozliczenie kierowcy
CDR od CPO → weryfikacja (`dom-ev-cdr-settlement`, kalkulator `dom-ev-tariffs-pricing`) → pozycja faktury eMSP.
Cena dla kierowcy może się różnić od ceny CPO (marża, abonament); różnicę ustala umowa i tę różnicę eMSP pokazuje
na fakturze jako własną cenę. Korekta CDR kredytowym zmienia fakturę **kolejną notą**, nie edycją wystawionej.
Płatność kartą kierowcy za abonament lub fakturę: `dom-ev-payments`; subskrypcje cykliczne opisz własnym modelem
(plan, okres rozliczeniowy, proporcjonalna zmiana planu) i trzymaj poza OCPI.

## 5. Wsparcie kierowcy
Cztery zgłoszenia pokrywają większość ruchu; tabela diagnostyczna i teksty w `references/rozliczenie-i-wsparcie.md`.
| Zgłoszenie | Pierwsze pytanie do danych | Dalej |
|---|---|---|
| nie startuje | jaki `CommandResult` / który krok? | `dom-ev-diagnostics` |
| wolno ładuje | moc z `charging_periods` vs limit złącza i auta | `dom-ev-vehicle-battery`, `dom-ev-diagnostics` |
| zła cena | którą taryfę widział kierowca przed startem? | `dom-ev-tariffs-pricing`, `dom-ev-cdr-settlement` |
| karta nie działa | `valid`, `whitelist`, czas propagacji, odpowiedź real-time | sekcja 1 |

## Przykład
Wejście: kierowca w aplikacji dotyka Start na EVSE `PL*ABC*E100*1`, a CPO odpowiada HTTP 200 z `ACCEPTED`.
```
POST {commands_cpo}/START_SESSION  { "response_url": "https://emsp.example/ocpi/commands/START_SESSION/7f3a",
  "token": { "uid": "u-5521", "type": "APP_USER", "whitelist": "NEVER", "valid": true, ... },
  "location_id": "LOC1", "evse_uid": "evse-1", "authorization_reference": "auth-7f3a" }
```
Wynik w aplikacji: ekran „Stacja przyjęła polecenie. Podłącz kabel”. Po `CommandResult: ACCEPTED` nadal czekasz na
Session. Gdy przyjdzie Session `ACTIVE`, ekran zmienia się na „Ładuje”. Gdy przyjdzie `EVSE_OCCUPIED`, pokaż
„Stanowisko zajęte, wybierz inne”, a gdy `TIMEOUT` albo brak wyniku po `timeout`, pokaż „Nie udało się
rozpocząć, nic nie pobraliśmy” i **sprawdź GET-em Sessions**, zanim pozwolisz na ponowny start (dublowanie komend).

## Pułapki
- Traktowanie `ACCEPTED` z odpowiedzi HTTP jako startu sesji; brak limitu czasu i stanu „nie udało się”.
- Real-time authorize z kontrolą godzin otwarcia lub statusu EVSE po stronie eMSP (zabronione przez specyfikację).
- Usuwanie tokenu zamiast `valid: false`; brak PATCH po zgubieniu karty; zakładanie, że blokada działa natychmiast przy `ALWAYS`.
- Pokazywanie „wolne” z cache bez wieku; filtr „dostępne teraz” oparty na statusie sprzed godzin.
- Deduplikacja po samej nazwie albo współrzędnych; scalanie dwóch operatorów w jedną stację.
- Cena na ekranie z innej taryfy niż ta, którą CPO zastosuje (zmiana `tariff_ids` między mapą a startem).
- Pchanie tokenów `EMAID` do CPO; mylenie UID karty z kontraktem.
- Obietnica zgodności z CarPlay lub Android Auto bez sprawdzenia wymagań platform [do weryfikacji].
- Zgłoszenie „wolno ładuje” zamykane jako błąd stacji, bez sprawdzenia mocy auta.

## Checklista
- [ ] Każdy nośnik kierowcy ma token z właściwym `type` i `whitelist`; blokada przez `valid: false`
- [ ] Znasz czas propagacji tokenu do CPO i komunikujesz go kierowcy
- [ ] Mapa pokazuje wiek statusu; `UNKNOWN` ≠ wolne; zdefiniowany próg nieświeżości
- [ ] Deduplikacja po `evse_id` lub identyfikatorze źródła; ręczna kolejka niepewnych scaleń
- [ ] Cena przed startem pochodzi z taryfy przypiętej do Connectora i jest zapisana z sesją
- [ ] Start zdalny: stany, `timeout`, idempotentny ponowny start, sprawdzenie Sessions po błędzie
- [ ] Faktura ma ścieżkę korekt (nota kredytowa po CDR kredytowym)
- [ ] Aplikacja pokazuje dane potrzebne wsparciu (identyfikator sesji, wynik komendy, wiek statusu)
- [ ] Niepewne fakty (CarPlay, Android Auto, opóźnienia) oznaczone [do weryfikacji]

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| wydanie, blokada, zgubienie karty; typy tokenów; whitelist; synchronizacja z CPO; Plug & Charge od strony konta | `references/konto-i-tokeny.md` |
| pola Locations do mapy, filtry, status i jego opóźnienie, deduplikacja, jakość danych, AFIR, NEVI, CarPlay i Android Auto | `references/mapa-i-dostepnosc.md` |
| Commands, `CommandResult` na komunikat, Sessions w aplikacji, cena przed startem, błędy | `references/start-zdalny-i-sesja.md` |
| faktura, abonament, historia, spory, tabela zgłoszeń wsparcia i co pokazać w aplikacji | `references/rozliczenie-i-wsparcie.md` |

## Źródła
- OCPI `v2.2.1-d2` i `v2.3.0` (mod_tokens, mod_locations, mod_commands, mod_sessions), baza wiedzy fabryki
  (`ocpi-2.2.1-d2`, `ocpi-2.3.0`), github.com/ocpi/ocpi, pobrane 2026-10-20.
- AFIR (UE) 2023/1804, art. 5 i 20, eur-lex.europa.eu/eli/reg/2023/1804/oj (wersja skonsolidowana 08.01.2026),
  pobrane 2026-10-20 (baza `eu-afir`); NEVI 23 CFR 680.116, ecfr.gov, pobrane 2026-10-20 (baza `us-nevi`).
- Skille fabryki: `dom-ev-ocpi`, `dom-ev-tariffs-pricing`, `dom-ev-cdr-settlement`, `dom-ev-session-lifecycle`.
- Opóźnienia statusu, zasady CarPlay i Android Auto, praktyka wsparcia: wiedza ogólna branży, w bazie brak
  źródeł [do weryfikacji].
