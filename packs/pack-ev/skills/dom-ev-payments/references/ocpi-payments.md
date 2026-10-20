# OCPI 2.3.0 Payments — obiekty, endpointy, kolejność
> Spis: 1. Role · 2. Terminal · 3. Financial Advice Confirmation · 4. Enumy · 5. Endpointy · 6. Kolejność wywołań · 7. Źródła

Opis własnymi słowami; nazwy pól i operacji w oryginale. Pełny tekst: baza fabryki `ocpi-2.3.0`,
`.claude/knowledge/ocpi-2.3.0/doc.txt` L6571-7260 (`mod_payments`).

## 1. Role
- **PTP** (Payment Terminal Provider) — właściciel danych modułu; tworzy Terminal i Financial Advice Confirmation.
  Interfejs „Sender”.
- **CPO** — interfejs „Receiver” (przyjmuje Terminal i Financial Advice Confirmation od PTP) oraz klient interfejsu
  PTP (aktywuje, przypisuje, dezaktywuje terminal).
- Moduł dotyczy bezpośredniej płatności kartą w świecie roamingu; różni się od stacji z wbudowaną płatnością tym, że
  terminal i CSMS należą do różnych stron.

## 2. Terminal (jeden fizyczny terminal)
| Pole | Karta. | Sens |
|---|---|---|
| `terminal_id` | 1 | unikalny identyfikator terminala (CiString 36); w żądaniu aktywacji opcjonalny, nadaje go PTP |
| `customer_reference` | ? | powiązanie terminala z CSMS CPO; może pochodzić z zamówienia |
| `party_id`, `country_code` | ? | alternatywa dla `customer_reference` |
| `address`, `city`, `postal_code`, `state`, `country`, `coordinates` | ? | adres montażu (kraj ISO 3166-1 alfa-3) |
| `invoice_base_url` | ? | baza adresu pobrania faktury |
| `invoice_creator` | ? | `CPO` albo `PTP` — kto wystawia dokument kierowcy |
| `reference` | ? | wartość nadana przez PTP, np. numer seryjny |
| `location_ids`, `evse_uids` | * | lokacje i EVSE obsługiwane przez terminal (suma obu list) |
| `last_updated` | 1 | czas ostatniej zmiany |

Jeden terminal może obsługiwać wiele lokacji i/lub EVSE; przypisanie robi CPO.

## 3. Financial Advice Confirmation
| Pole | Karta. | Sens |
|---|---|---|
| `id` | 1 | identyfikator obiektu |
| `authorization_reference` | 1 | to samo, co PTP podał w `Commands.StartSession` |
| `total_costs` | 1 | kwota naprawdę pobrana (capture) u PSP, cena konsumencka z VAT (`Price`) |
| `currency` | 1 | ISO 4217 |
| `eft_data` | + | dane transakcji kartowej wymagane na fakturze (lista, 1..255 znaków) |
| `capture_status_code` | 1 | `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED` |
| `capture_status_message` | ? | komunikat błędu |
| `last_updated` | 1 | czas ostatniej zmiany |

Obiekt jest potrzebny tylko wtedy, gdy fakturę wystawia CPO. Gdy `PARTIAL_SUCCESS`: pobrano mniej niż wynika z ceny —
faktura i dług kierowcy opierają się na `total_costs`, a różnica to sprawa windykacji [założenie — spec definiuje
tylko znaczenie kodu].

## 4. Enumy
| Enum | Wartości |
|---|---|
| `InvoiceCreator` | `CPO` (faktura pod `invoice_base_url` + `authorization_reference`), `PTP` (pokazuje ją kierowcy terminal) |
| `CaptureStatusCode` | `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED` |

## 5. Endpointy
| Strona | Zasób | Metody |
|---|---|---|
| PTP (Sender) | `payments/terminals` | `GET` lista (`date_from`, `date_to`, `offset`, `limit`), `GET` jeden, `POST …/activate`, `POST …/{terminal_id}/deactivate`, `PUT`, `PATCH` (przypisanie lokacji/EVSE) |
| PTP (Sender) | `payments/financial-advice-confirmations` | `GET` lista, `GET` jeden |
| CPO (Receiver) | `payments/terminals` | `GET` jeden, `POST` (nowy terminal od PTP) |
| CPO (Receiver) | `payments/financial-advice-confirmations` | `GET` jeden, `POST` |

`PUT` i `PATCH` to wiadomości informacyjne wysyłane przez CPO; obiekt należy do PTP. Dotyczy to też fragmentów
„paginated” list: starsze, niewymienione dane uznaj za nieważne (reguła ogólna listy, zob. dom-ev-ocpi).

## 6. Kolejność wywołań
**Terminal zintegrowany ze stacją:** CPO zamawia stację u producenta z terminalem → producent daje referencję →
CPO wywołuje `activate` u PTP → PTP zakłada Terminal u CPO (`POST`) → CPO przypisuje lokacje/EVSE (`PATCH`).
Aktywacja jest potrzebna, bo PTP musi wcześniej skonfigurować m.in. unikalny identyfikator dla adresu instalacji.
**Terminal dostarczony osobno:** PTP wysyła `POST` Terminal bez `location_ids` (przypisanie robi CPO).
**Transakcja:** wybór złącza → PTP pobiera konektor → `tariff_id` → pobiera taryfę (cena na ekran, `preauthorize_amount`
do blokady) → akceptacja → blokada u PSP → `StartSession` z `authorization_reference` → aktualizacje sesji →
zakończenie (auto, stacja, `StopSession` od PTP albo backend CPO po limicie) → CDR (`invoice_reference_id`) →
capture → Financial Advice Confirmation → CPO uzupełnia fakturę o `eft_data`.

## 7. Źródła
`ocpi-2.3.0` — `mod_payments.asciidoc` (L6571-7260) i `mod_tariffs.asciidoc` (pole `preauthorize_amount`, L3948),
github.com/ocpi/ocpi tag v2.3.0, pobrane 2026-10-20. Adresy przykładów w spec zawierają `2.2.1`; to przykłady, nie
zmiana wersji [założenie].
