# Konto kierowcy i tokeny

Spis treści: 1. Model konta · 2. Cykl życia karty RFID · 3. Whitelist w praktyce · 4. Synchronizacja z CPO ·
5. Plug & Charge od strony konta · 6. Dane osobowe

Źródło: OCPI `v2.2.1-d2` i `v2.3.0`, mod_tokens i mod_commands (baza wiedzy, pobrane 2026-10-20). Co jest wiedzą ogólną
branży, a nie specyfikacją, oznaczono.

## 1. Model konta
Konto kierowcy (własność eMSP) ma kontrakt i wiele nośników. Każdy nośnik = jeden obiekt Token OCPI.
```
Konto 1 ── N Token { uid, type, contract_id, visual_number, issuer, group_id, valid, whitelist, language, last_updated }
```
- Para (`uid`, `type`) jest unikalna u eMSP. `uid` karty RFID pochodzi z odczytu nośnika, a `uid` tokenu aplikacji
  generuje eMSP (unikalny, stały dla `APP_USER`, jednorazowy dla `AD_HOC_USER`).
- `contract_id` to zalecany format EMAID; `visual_number` to numer wydrukowany na karcie (pomaga wsparciu);
  `issuer` to firma widoczna na karcie, niekoniecznie eMSP.
- `group_id` łączy tokeny, gdy sesję startuje jeden, a kończy drugi (np. karta i breloczek); stacje obsługujące
  to mają capability `TOKEN_GROUP_CAPABLE`. Dla OCPP 1.x identyfikator grupy ma do 20 znaków.
- Tokeny `APP_USER` i `AD_HOC_USER` są używane tylko w komendach eMSP i nie muszą być wcześniej wypchnięte do CPO
  (specyfikacja dopuszcza komendę z tokenem niewysłanym przez moduł Tokens).

## 2. Cykl życia karty RFID
| Zdarzenie | Operacja OCPI | Uwagi |
|---|---|---|
| wydanie | PUT Token do każdego CPO z modułem Tokens | `valid: true`; potwierdź GET-em, zanim klient dostanie kartę |
| aktywacja po dostarczeniu | PATCH `valid: true` | gdy karta była wysłana nieaktywna (praktyka, ogranicza nadużycia) |
| zgubienie, kradzież | PATCH `valid: false` + `last_updated` | tokenu nie usuwasz; wpis zostaje do rozliczeń i śledzenia |
| wymiana | nowy Token na to samo konto; stary `valid: false` | historia przy koncie, nie przy karcie |
| wygaśnięcie kontraktu | PATCH `valid: false` na wszystkich tokenach konta | także `APP_USER` |
| odblokowanie znalezionej karty | PATCH `valid: true` | zapisz zdarzenie w audycie |

Co dzieje się po blokadzie zależy od `whitelist` (sekcja 3) i od tego, czy CPO przetworzył PATCH. Trwającej sesji
sama zmiana `valid` nie zatrzymuje [wiedza ogólna]; przy kradzieży z aktywnym ładowaniem wyślij `STOP_SESSION`.
Sprawdź też, czy w kolejnych sesjach nie pojawia się zablokowany `uid` (sygnał opóźnionej synchronizacji u CPO).

## 3. Whitelist w praktyce
| `whitelist` | Zachowanie CPO | Skutek przy blokadzie | Skutek dla UX |
|---|---|---|---|
| `ALWAYS` | autoryzuje zawsze z pamięci podręcznej, bez pytania eMSP | blokada działa po przetworzeniu PATCH | najszybciej, działa offline |
| `ALLOWED` | pamięć podręczna lub real-time, do wyboru CPO | zależnie od wyboru CPO | zwykle szybko |
| `ALLOWED_OFFLINE` | real-time, a bez łączności z eMSP przepuszcza | blokada natychmiast, ale offline karta działa | wolniej online |
| `NEVER` | zawsze pyta eMSP (`POST .../tokens/{token_uid}/authorize`) | blokada natychmiastowa | opóźnienie przy czytniku |

Real-time zwraca `AuthorizationInfo` z `allowed`: `ALLOWED`, `BLOCKED`, `EXPIRED`, `NO_CREDIT`, `NOT_ALLOWED`.
Wartość `NO_CREDIT` służy abonamentom przedpłaconym. Nieznany token → status OCPI 2004. Przy braku `LocationReferences`
→ 2002. **eMSP nie sprawdza przy tym godzin otwarcia ani statusu EVSE.** `authorization_reference` zachowaj: trafia do
Session i CDR i łączy autoryzację z rozliczeniem.
Dobór: karta kierowcy indywidualnego → `ALLOWED` albo `ALWAYS` (szybkość przy czytniku, ryzyko okna po blokadzie
akceptowane); karta o wysokim ryzyku nadużyć lub przedpłacona → `NEVER`/`ALLOWED_OFFLINE` [rekomendacja robocza].

## 4. Synchronizacja z CPO
- **Push:** każda zmiana tokenu (PUT/PATCH) do każdego CPO, z którym masz kontrakt na Tokens. Zbieraj wynik per CPO.
- **Pull po stronie CPO** (GET listy z `date_from`) służy do odbudowy pamięci podręcznej, nie do autoryzacji.
  Dlatego eMSP musi udźwignąć GET listy tokenów po przerwie CPO.
- **Kolejka z ponawianiem:** PATCH jest idempotentny dla pól skalarnych (`valid`), więc ponawiaj do skutku;
  alarmuj, gdy blokada nie jest potwierdzona u CPO po progu czasu [próg: decyzja produktu].
- **Rozjazdy:** token zablokowany u eMSP, a używany u CPO → porównaj `last_updated`; PUT całego obiektu naprawia stan.
- Nowy partner CPO: pierwsza synchronizacja pełnej listy tokenów konta jest PUT-em per token (dla `RFID`); `APP_USER`
  nie wymaga wysyłki, jeśli idą tylko komendy.

## 5. Plug & Charge od strony konta
- Kontrakt Plug & Charge to certyfikat w pojeździe i EMAID na koncie; mechanikę (SLAC, certyfikat kontraktu, PKI)
  opisuje `dom-ev-iso15118`, format EMAID `dom-ev-identifiers`.
- W OCPI 2.3.0 token typu `EMAID` istnieje, ale eMSP **nie powinien go pchać**: CPO poznaje wystawcę ze stacji i pyta
  go real-time. Zarządzanie certyfikatami kontraktu jest poza OCPI.
- Produktowo: konto trzyma EMAID, status kontraktu (aktywny, zawieszony) i datę ważności certyfikatu; zawieszenie
  konta musi skutkować `BLOCKED` w odpowiedzi real-time dla EMAID. Instalacja certyfikatu w aucie zależy od
  producenta pojazdu [do weryfikacji], więc aplikacja pokazuje stan („gotowy”, „wymaga aktywacji u producenta”).
- Kierowca zawsze może nie użyć automatycznej autoryzacji (AFIR art. 5 ust. 2, zapis w bazie `eu-afir`): w UI wybór
  między P&C a aplikacją/kartą.

## 6. Dane osobowe
Konto kierowcy to dane osobowe (RODO). Do CPO wysyłasz identyfikatory i `issuer`, nie imię ani adres.
Dane płatnicze zostają u eMSP lub operatora płatności (`dom-ev-market-roles`). Historia sesji: okres retencji zgodny
z prawem podatkowym i RODO [do weryfikacji z prawnikiem].
