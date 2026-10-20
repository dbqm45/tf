# Preautoryzacja, obciążenie końcowe i sesja przerwana
> Spis: 1. Pojęcia · 2. Kwota preautoryzacji · 3. Przypadki końca sesji · 4. Retry i idempotencja · 5. Karta flotowa i kontrakt · 6. Źródła

## 1. Pojęcia (karta)
| Pojęcie | Znaczenie |
|---|---|
| Preautoryzacja (pre-auth, hold) | bank rezerwuje kwotę na rachunku kierowcy, bez pobrania |
| Capture | pobranie kwoty rzeczywistej z rezerwacji (≤ zablokowanej) |
| Void / cancel | zwolnienie blokady bez pobrania |
| Refund | zwrot już pobranych pieniędzy |
| Chargeback | spór kierowcy u wystawcy karty; pieniądze wracają przymusowo |

Dokładne nazwy operacji i limity kwot dla zwiększenia blokady zależą od PSP i schematu kartowego [niezweryfikowane].

## 2. Kwota preautoryzacji
- OCPI 2.3.0: `Tariff.preauthorize_amount` (liczba, opcjonalna) — kwota, którą PTP ma zablokować dla sesji z tą taryfą.
  Wartość jest w walucie `Tariff.currency`; czy to brutto, wynika z taryfy i umowy z PTP [założenie — pole nie ma
  osobnego opisu].
- Dobór: pokrywa realistyczny koszt do limitu (czas, energia, postój) i mieści się w limitach kart; za mała = sesja
  zatrzymana po osiągnięciu, za duża = kierowcy odrzucają kartę.
- Po osiągnięciu limitu sesję zatrzymuje PTP (`StopSession`) albo backend CPO. Zapisz kto — inaczej oba podmioty
  zatrzymają ją podwójnie lub żaden.
- Zapisz wartość z chwili startu przy sesji; późniejsza zmiana taryfy nie zmienia już trwającej blokady.

## 3. Przypadki końca sesji
| Przypadek | Pobierz | Zwolnij | Uwagi |
|---|---|---|---|
| Normalny koniec | cena rzeczywista | reszta blokady | Financial Advice Confirmation po capture |
| Przerwana po kilku minutach | cena za faktycznie dostarczoną energię i czas; możliwy `min_price` z taryfy | reszta | `min_price` obowiązuje, jeśli taryfa go ma (dom-ev-tariffs-pricing) |
| Auto nie zaczęło pobierać energii | zero lub opłata stała z taryfy | cała blokada | void, brak capture |
| Limit preautoryzacji osiągnięty | do kwoty zablokowanej | — | dalsza energia darmowa albo zatrzymanie; ustal w umowie z PTP |
| Sesja wisi (brak `StopTransaction`/CDR) | nie pobieraj | po czasie ważności blokady | rozwiąż sesję osieroconą (dom-ev-session-lifecycle); blokada wygasa u banku po czasie zależnym od karty [niezweryfikowane] |
| Karta odrzucona przy capture | — | — | `capture_status_code` = `FAILED`; windykacja, nie zmiana CDR |
| Offline stacji | dane po powrocie z licznika | po powrocie | cena po zsynchronizowaniu; kierowca czeka na zwolnienie |

## 4. Retry i idempotencja
- Capture, void i refund wywołuj z kluczem idempotencji (obsługa po stronie PSP); nigdy retry bez klucza.
- Stan płatności trzymaj osobno od stanu sesji: `AUTHORIZED` → `CAPTURED` / `VOIDED` / `FAILED` (nazwy robocze).
- Odpowiedź PSP „timeout” traktuj jako nieznany stan: najpierw zapytaj o status płatności, potem decyduj.
- Duplikaty Financial Advice Confirmation (to samo `id`) przyjmuj idempotentnie (dom-ev-ocpi).

## 5. Karta flotowa, abonament, kontrakt
- Płatność kierowcy nie jest widoczna dla CPO; ma CDR od eMSP i rozlicza się hurtowo (dom-ev-cdr-settlement).
- Limity karty flotowej (kwota dzienna, dozwolone stacje, brak ładowania poza trasą) egzekwuje eMSP przy autoryzacji
  tokenu; CPO dostaje tylko odmowę lub zgodę [założenie — OCPI tego nie opisuje szczegółowo].
- Abonament: opłata stała eMSP↔kierowca poza OCPI; CDR zawiera tylko cenę CPO.

## 6. Źródła
OCPI 2.3.0 `mod_payments` (sekcja Transaction) i `mod_tariffs` (`preauthorize_amount`), baza `ocpi-2.3.0`,
pobrane 2026-10-20; reszta — praktyka, oznaczona [niezweryfikowane] lub [założenie].
