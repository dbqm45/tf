# Projekt obsługi sesji w CSMS — szczegóły

Zasady ogólne: surowa ramka przed interpretacją, idempotencja, odpowiedź w czasie, skutki z outboxa
(`dom-ev-ocpp-16`, `dom-ev-ocpp-2x`). Architektura samego CSMS: `dom-ev-cpms-architecture`.

## 1. Model danych (minimum)
| Pole | Po co |
|---|---|
| `sesja_id` (własny) | stabilny klucz domenowy, niezależny od protokołu |
| stacja, EVSE, złącze | adresowanie; identyfikatory: `dom-ev-identifiers` |
| `wersja_ocpp`, `transakcja_id` | 1.6 nadany przez CSMS, 2.0.1 przez stację |
| `token`, `sposob_autoryzacji` | RFID / app / ad hoc / PnC |
| `ocpi_session_id`, `ocpi_cdr_id` | powiązania OCPI (puste, gdy brak roamingu) |
| `meter_start`, `meter_stop`, `jednostka` | surowe odczyty licznika |
| `czas_start`, `czas_stop` (zdarzenia) | czas z ramki po korekcie zegara |
| `odebrano_start`, `odebrano_stop` | czas odbioru |
| `energia_szacowana` (bool) | brak odczytu z licznika |
| `stan` | patrz niżej |
| ostatni `seqNo` (2.0.1), braki | wykrywanie luk |

## 2. Maszyna stanów
| Stan | Wejście | Wyjście |
|---|---|---|
| `oczekuje_na_start` | komenda START_SESSION lub Authorize przyjęte | Start/Started → `aktywna`; limit czasu → `nieudana` |
| `aktywna` | Start/Started | Stop/Ended → `zakonczona`; sygnał osierocenia → `osierocona` |
| `osierocona` | boot / Available na złączu / limit bez ramek | późny Stop → `zakonczona` (odczyt rzeczywisty); decyzja → `zakonczona` (szacunek) |
| `zakonczona` | Stop/Ended lub zamknięcie szacunkiem | okno na spóźnione ramki minęło → `cdr_wyslany` |
| `cdr_wyslany` | CDR przyjęty przez eMSP | tylko korekty (`dom-ev-charging`) |

Przejście wstecz z `cdr_wyslany` jest zabronione.

## 3. Tabela decyzji dla nietypowych ramek
| Ramka | Stan sesji | Decyzja |
|---|---|---|
| Duplikat (ten sam `messageId`) | dowolny | ta sama odpowiedź, brak zapisu |
| `Start` z innym `messageId`, ale te same (`connectorId`, `idTag`, `timestamp`, `meterStart`) | `aktywna` | traktuj jak duplikat **[założenie]**; loguj |
| `Stop` bez znanego `Start` | brak | odpowiedz poprawnie; kwarantanna; alarm |
| `Stop` po zamknięciu szacunkiem, CDR niewysłany | `zakonczona` (szacunek) | nadpisz odczytem, usuń flagę szacunku |
| `Stop` po wysłaniu CDR | `cdr_wyslany` | nie zmieniaj CDR; zapisz różnicę; ścieżka korekt |
| `Update`/`MeterValues` po `Stop`/`Ended` | `zakonczona` | zapisz, nie zmieniaj energii rozliczeniowej; alarm |
| Nowy `Start` na złączu z sesją `aktywna` | `aktywna` | najpierw zamknij starą jako `osierocona`, potem otwórz nową |
| `Ended` z luką w `seqNo` | `aktywna` | czekaj na uzupełnienie do limitu, potem CDR z flagą „dane niepełne” |

## 4. Offline po stronie ładowarki
- Ładowarka może autoryzować z lokalnej listy i rozpocząć transakcję bez CSMS; po powrocie wysyła zbuforowane ramki
  w kolejności zapisania. CSMS przyjmuje je bez założenia, że `czas odbioru` ≈ `czas zdarzenia`.
- W 1.6 transakcja offline nie ma `transactionId` nadanego przez CSMS; sposób jego tymczasowej identyfikacji
  zależy od producenta **[do weryfikacji]** (`dom-ev-ocpp-16`, odchylenia). Dopasuj po (`connectorId`, `idTag`,
  `timestamp`, `meterStart`).
- Zegar ładowarki bywa błędny (np. 1970). Korekta: porównaj `currentTime` z ostatniego Heartbeat/Boot i ramkę
  odebraną; zachowaj oba czasy. Gdy korekta niemożliwa, oznacz czas jako niepewny i nie licz na nim taryf czasowych
  bez przeglądu.

## 5. Co wysłać do eMSP po późnym powrocie
1. Jeśli eMSP nie widział sesji: Session od razu w stanie zakończonym (czasy zdarzeń, energia z licznika). Brak
   podglądu na żywo jest tu nieunikniony.
2. Po upływie okna na spóźnione ramki: CDR. Okno i zasady retencji — decyzja biznesowa **[założenie]**.
3. Komenda, na którą ładowarka nie odpowiedziała w czasie: wynik błędu na `response_url`; późniejszy start nie
   jest już odpowiedzią na komendę, lecz zwykłą sesją (token ten sam, może się powiązać po `authorization_reference`
   **[do weryfikacji]**).

## 6. Procedura projektu obsługi sesji (pełna, przeniesiona z SKILL.md)
1. **Zdefiniuj sesję domenową** z własnym id i powiązaniami: stacja, EVSE/złącze, token, `transactionId`
   (wersja protokołu), `session id` OCPI, `CDR id`. Stany: `oczekuje na start`, `aktywna`, `zakończona`,
   `osierocona-szacowana`, `rozliczona`.
2. **Przyjmuj ramkę w jednej transakcji bazy:** surowa ramka + klucz idempotencji (unikalny indeks) + zmiana
   stanu + wpis do outboxa. Ponowienie trafia na indeks i zwraca zapisaną odpowiedź.
3. **Czas:** przechowuj `czas_zdarzenia` (z ramki, skorygowany) i `czas_odbioru`. Kolejność logiczną ustalaj po
   `seqNo` (2.0.1) albo po `czas_zdarzenia` (1.6), nie po czasie odbioru.
4. **Przyjmuj nieoczekiwane** (`Stop` bez `Start`, `Update` po `Ended`): odpowiedz poprawnie, zapisz w
   kwarantannie, alarmuj. Odrzucenie dostarczanej ramki powoduje pętlę ponowień.
5. **Skutki uboczne z outboxa:** Session i CDR do eMSP wysyłaj z kolejki z ponawianiem; `PUT` Session i
   `POST` CDR są bezpieczne dzięki kluczowi (`session id`, `CDR id`). Nie wysyłaj do eMSP przed zapisem stanu.
6. **Zamykacz osieroconych:** zadanie okresowe znajduje sesje `aktywna` bez ramki od czasu T; po sygnale
   z kroku „osierocona” zamyka i oznacza szacunek. T jest konfigurowalne per model ładowarki.
7. **Energia:** surowe odczyty licznika w sesji; `kWh` tylko w CDR. Szacunek ma flagę.
8. **CDR:** generator uruchamia się na `zakończona` + upływie okna na spóźnione ramki; po wysłaniu rekord
   tylko do odczytu (blokada na poziomie modelu).
9. **Test na nagranych ramkach:** scenariusze offline (Start+Stop po 2 h), duplikat, `Stop` bez `Start`,
   luka `seqNo`, restart w trakcie sesji. Asercje: jedna sesja, jedna Session u eMSP, jeden CDR.

Szczegóły (maszyna stanów, tabela decyzji): `references/projekt-obslugi-sesji.md`.

