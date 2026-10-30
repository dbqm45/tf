---
name: dom-ev-oicp-hubs
description: Użyj przy integracji OICP 2.3 z Hubject i wyborze huba — operacje CPO i EMP, ProviderID i OperatorID, OICP vs OCPI, P2P czy hub, adaptery OCPI+OICP.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy budujesz, debugujesz albo oceniasz integrację OICP 2.3 przez Hubject (role CPO i EMP, push EVSE Data i EVSE Status, pull z deltą i paginacją, AuthorizeStart/Stop, AuthorizeRemoteStart/Stop, ChargeDetailRecord, ChargingNotifications, DynamicPricing, kody 017/018/603/604), gdy porównujesz OICP z OCPI, wybierasz peer-to-peer albo hub, planujesz warstwę adapterów dla OCPI i OICP naraz lub migrację z OICP 2.1. Nie do protokołu OCPI i routingu OCPI przez hub (dom-ev-ocpi), formatów EVSE ID i EMAID (dom-ev-identifiers), CDR i rozliczeń (dom-ev-cdr-settlement), taryf i ceny (dom-ev-tariffs-pricing), ról rynku (dom-ev-market-roles)."
  slowa: "OICP, OICP 2.3, Hubject, HBS, hub Hubject, roaming przez Hubject, intercharge, ProviderID, OperatorID, EvcoID, EvseID Hubject, eRoamingPushEvseData, eRoamingPullEvseData, eRoamingPushEvseStatus, eRoamingAuthorizeStart, eRoamingAuthorizeRemoteStart, eRoamingChargeDetailRecord, ChargingNotifications, DynamicPricing, kod 017, kod 604, IsHubjectCompatible, hub operator, hub provider, sub operator, OICP vs OCPI, P2P czy hub, Gireve, e-clearing, adapter OCPI i OICP, OICP 2.1 wycofanie, certyfikat klienta Hubject, delta pull LastCall, ActionType fullLoad"
---

# OICP 2.3 i huby roamingowe — Hubject, różnice wobec OCPI, wybór modelu

OICP (Open InterCharge Protocol) łączy CPO i EMP **przez jednego pośrednika**, Hubject (w specyfikacji: HBS).
Strony nie rozmawiają ze sobą bezpośrednio: każda ma kontrakt i połączenie z hubem, a hub przechowuje dane,
nadaje identyfikator sesji i przekazuje wiadomości. OCPI jest protokołem między stronami (z opcjonalnym hubem
jako routerem) — szczegóły: `dom-ev-ocpi`.

## Zakres i granice
- OCPI (handshake, moduły, routing przez hub w OCPI) → `dom-ev-ocpi`.
- Formaty EVSE ID, EMAID, `party_id` i ich walidacja → `dom-ev-identifiers`.
- CDR, korekty, uzgadnianie z fakturą → `dom-ev-cdr-settlement`; taryfy i liczenie ceny → `dom-ev-tariffs-pricing`.
- Role rynku i przepływy pieniędzy → `dom-ev-market-roles`.
- Prawo (AFIR) — poza skillem. Inne huby (Gireve, e-clearing.net): [do weryfikacji], w bazie ich nie ma.

## Procedura
1. **Ustal rolę i wersję.** CPO, EMP czy obie (wtedy dwa ID: OperatorID i ProviderID); czy jesteś hubem dla pod-partnerów;
   wersja operacji (tabela niżej). Tylko REST/JSON; nowe wdrożenia na OICP 2.3.
2. **Ustal, które operacje są obowiązkowe** dla roli (kolumna „Wdrożenie”) i które usługi hub włączył w kontrakcie.
3. **Zmapuj model wewnętrzny** na operacje (sekcja „Adaptery”), z jednym modelem kanonicznym dla OCPI i OICP.
4. **Zaplanuj kolejność push** (sekwencyjnie), obsługę kodów statusu i ponawianie.
5. Testuj na środowisku testowym huba [do weryfikacji: adresy środowisk nie są w bazie].

## Model huba
- Hubject sprawdza przy **każdym** żądaniu zgodność `ProviderID`/`OperatorID` z certyfikatem klienta SSL partnera;
  niezgodność = kod **017** „Unauthorized Access”. Własne tokeny A/B/C jak w OCPI tu nie występują.
- ID jest przypisane do roli i unikalne na rynku; firma w dwóch rolach ma dwa ID.
- **Hub CPO / hub EMP:** partner może wiązać pod-partnerów (sub operator, sub provider), których ID skonfigurowano
  w Hubject. W polach `ProviderID` i `OperatorID` zawsze idzie ID partnera łączącego się z hubem; ID pod-partnera
  wynika tylko z `EvseID` lub `EvcoID`. Hub nie odróżnia rekordów EVSE huba od rekordów jego pod-operatorów.
- **SessionID** nadaje Hubject (GUID) przy pierwszym żądaniu sesji i trzeba go podać w każdym kolejnym żądaniu tej
  sesji; nieznany lub nieważny = odpowiedź negatywna. Własny numer sesji strony: `CPOPartnerSessionID`,
  `EMPPartnerSessionID` (do 250 znaków) — hub odsyła je w odpowiedziach.
- Usługi są synchroniczne, UTF-8; każda wiadomość dostaje odpowiedź (co najmniej `eRoamingAcknowledgement` z `Result`
  i `StatusCode`). Czas w ISO 8601 z offsetem; CPO podaje strefę miejsca ładowania.

## Operacje OICP 2.3 (nazwy w oryginale)
Kierunek z punktu widzenia roli; „Wdrożenie” wg specyfikacji CPO (EMP: `references/operacje-oicp.md`).

| Grupa | Operacja (wersja operacji) | CPO | EMP | Wdrożenie CPO |
|---|---|---|---|---|
| EVSE Data | `eRoamingPushEvseData` (2.3) | wysyła | — | obowiązkowe |
| | `eRoamingPullEvseData` (2.3) | — | wysyła | — |
| EVSE Status | `eRoamingPushEvseStatus` (2.1) | wysyła | — | obowiązkowe |
| | `eRoamingPullEvseStatus` (+ByID, +ByOperatorID) | — | wysyła | — |
| Autoryzacja | `eRoamingAuthorizeStart` (2.1) | wysyła | odpowiada | obowiązkowe |
| | `eRoamingAuthorizeStop` (2.1) | wysyła | odpowiada | opcjonalne |
| Zdalny start/stop | `eRoamingAuthorizeRemoteStart/Stop` (2.1) | odbiera | wysyła | obowiązkowe |
| CDR | `eRoamingChargeDetailRecord` (2.2) | wysyła | odbiera | obowiązkowe |
| | `eRoamingGetChargeDetailRecords` (2.2) | — | wysyła | — |
| Dane uwierzytelniające | `eRoamingPushAuthenticationData` (2.1) | — | wysyła | — |
| Powiadomienia | `eRoamingChargingNotifications` (Start, Progress, End, Error) | wysyła | odbiera | opcjonalne |
| Ceny dynamiczne | `eRoamingPushPricingProductData`, `eRoamingPushEVSEPricing` (1.0) | wysyła | — | opcjonalne |
| | `eRoamingPullPricingProductData`, `eRoamingPullEVSEPricing` (1.0) | — | wysyła | — |
| Rezerwacja | `eRoamingAuthorizeRemoteReservationStart/Stop` (1.1) | odbiera | wysyła | opcjonalne (usługę włącza hub) |

„V2.1” przy `AuthorizeStart` to wersja **operacji**, nie protokołu: OICP 2.3 nadal jej używa. Zmieniły się w 2.3:
`PushEvseData`, `PullEvseData`, `ChargeDetailRecord`, `GetChargeDetailRecords`, `ChargingNotification`.

### Wzorce, które trzeba znać
- **Push EVSE:** pole `ActionType` ma cztery wartości: `fullLoad`, `update`, `insert`, `delete`. Pushe tej samej
  operacji idą **sekwencyjnie** — kolejne dopiero po odpowiedzi huba, bo równoległe mogą się wyprzedzić (duży
  `fullLoad` nadpisze późniejszy mały). Hub odrzuca EVSE, którego ID nie pasuje do OperatorID (kod **018**).
- **Pull EVSE (EMP):** domyślnie wszystkie ważne rekordy; `LastCall` daje deltę (`deltaType`: insert, update,
  delete); delta nie łączy się z `SearchCenter` (promień). W 2.3 pull ma **paginację** `?page=0&size=20`
  (domyślnie 20 rekordów, obowiązkowa po stronie EMP). Status EVSE: zalecana częstotliwość pull 1–5 minut.
- **Autoryzacja online:** CPO wysyła `AuthorizeStart`; hub najpierw próbuje offline (dane z `PushAuthenticationData`),
  potem wyprowadza EMP z `EvcoID` (QR, Plug & Charge), a przy RFID rozsyła zapytanie do wszystkich EMP po kontrakcie
  z CPO i autoryzuje, gdy choć jeden się zgodzi. Brak odpowiedzi EMP = `NotAuthorized`.
- **Zdalny start:** EMP wysyła `AuthorizeRemoteStart` (ProviderID, EvseID), hub wyprowadza OperatorID z EvseID,
  sprawdza kontrakt i `IsHubjectCompatible` (kody **603** nieznany EVSE, **604** niezgodny z Hubject), tworzy
  SessionID i przekazuje do CPO. CPO odpowiada `eRoamingAcknowledgement`; zalecany czas żądania poniżej 10 s.
- **CDR:** CPO wysyła po zakończeniu sesji (zalecenie: prawie od razu, w ciągu 10 s); ten sam SessionID co sesja;
  hub przyjmuje **jeden CDR na SessionID**, zapisuje go i zwraca sukces także gdy EMP był nieosiągalny — wtedy EMP
  pobiera zaległe przez `GetChargeDetailRecords`. W 2.3 obowiązkowe: `ChargingStart`, `ChargingEnd`,
  `ConsumedEnergy`; `MeteringSignature` zastąpiły `SignedMeteringValues` (do 10) i `CalibrationLawVerificationInfo`.

## Identyfikatory w OICP
Składnię i walidację opisuje `dom-ev-identifiers`; tu tylko to, co OICP dokłada.

| Typ | Przykład z specyfikacji | Uwaga |
|---|---|---|
| `OperatorID` | ISO `DE*A36`, DIN `+49*536` | DIN: kod kraju wg E.164 i obowiązkowy `*` |
| `ProviderID` | `DE8EO`, `DE-8EO` | część `EvcoID` |
| `EvseID` | ISO `DE*AB7*E840*6487`, DIN `+49*810*000*438` | ISO ma `E` po OperatorID; kraj alfa-2 |
| `EvcoID` | ISO `DE-8EO-CAet5e4XY-3`, DIN `DE*8EO*Aet5e4*3` | ISO: człon instancji 8 znaków z `C`; DIN: 6 |
| kraj w rekordzie EVSE | `DEU` | w danych EVSE kraj to alfa-3, w ID alfa-2 |

W OICP nie ma pary `country_code` + `party_id`: stroną jest `OperatorID` lub `ProviderID`. Przy adapterze
tabelę `OperatorID` → (`country_code`, `party_id`) trzymaj jawnie, bo forma DIN (`+49*536`) nie ma liter kraju [założenie].

## OICP vs OCPI
| Cecha | OICP 2.3 | OCPI 2.2.1 / 2.3.0 |
|---|---|---|
| Topologia | zawsze przez Hubject | P2P albo przez hub-router |
| Strona | partner z kontraktem u huba (`OperatorID`/`ProviderID`) | `country_code` + `party_id` |
| Uwierzytelnienie | certyfikat klienta SSL zgodny z ID | tokeny A/B/C wymieniane w handshake |
| Dane EVSE | CPO wypycha do huba, EMP pobiera z huba | Locations: CPO wypycha do eMSP albo eMSP pobiera od CPO |
| Sesja | SessionID nadaje hub | `id` sesji nadaje CPO |
| Zdalny start | synchroniczna odpowiedź `Acknowledgement` na żądanie | komenda z wynikiem asynchronicznym (`response_url`) |
| CDR | jeden na SessionID, hub zapisuje i przekazuje | CDR niezmienny, korekta kredytowym (`dom-ev-cdr-settlement`) |
| Taryfy | `DynamicPricing`: produkty cenowe i przypisanie do EVSE | moduł Tariffs (`dom-ev-tariffs-pricing`) |
| Postęp sesji | `ChargingNotifications` | moduł Sessions |

Różnica w korekcie CDR jest istotna: OICP nie opisuje w źródle mechanizmu korekty po przyjęciu CDR; ustal go
z hubem, zanim obiecasz partnerowi korektę [do weryfikacji].

## P2P czy hub
Kryteria: liczba partnerów po obu stronach i wolumen z każdym; koszt huba i opłaty
[do weryfikacji, w bazie brak]; zasięg (z kim huba łączy, których krajów dotyczy) [do weryfikacji]; elastyczność
danych i cen; kto trzyma kontrakt i rozliczenie. Wzorzec hybrydy (duzi partnerzy bezpośrednio, reszta przez hub)
i pytania przed integracją: `.claude/skills/dom-ev-market-roles/references/roaming-modele.md`. Gireve i e-clearing.net: protokoły, zasięg i
warunki — [do weryfikacji] u operatora huba.

## Adaptery: jeden model, dwa protokoły
Model wewnętrzny nie przyjmuje kształtu żadnego protokołu; OCPI i OICP to adaptery (ACL).
Mapowanie pojęć, pola i różnice semantyczne: `references/adaptery-ocpi-oicp.md`. Skrót:

| Model wewnętrzny | OCPI | OICP |
|---|---|---|
| lokalizacja / EVSE | Locations | `PushEvseData` / `PullEvseData` |
| status EVSE | `status` w Locations | `PushEvseStatus` / `PullEvseStatus` |
| autoryzacja | Tokens (whitelist, real-time) | `AuthorizeStart`, `PushAuthenticationData` |
| zdalny start/stop | Commands | `AuthorizeRemoteStart/Stop` |
| sesja w toku | Sessions | `ChargingNotifications` (przybliżenie) |
| rozliczenie | CDRs | `ChargeDetailRecord` |
| cennik | Tariffs | `DynamicPricing` |

## Wycofanie OICP 2.1
README repozytorium hubject/oicp (pobrane 2026-10-20) zapowiada **wycofanie OICP 2.1 w dniu 13 kwietnia 2023**
i wymaga, by nowe wdrożenia opierały się na OICP 2.3 (2.2 jest nadal wymienione w wydaniach). OICP 2.3 oferuje
wyłącznie REST; SOAP nie jest dostępny dla usług od 2.2 wzwyż.

## Przykład
Wejście: CPO z OCPI chce dołączyć do Hubject. Ma 1200 EVSE, jeden wątek wysyłający zmiany statusu i drugi
synchronizujący lokalizacje, obie przez jedną kolejkę „push”.
Wynik: (1) adapter OICP z **osobną kolejką na operację**, w każdej jedno wysyłanie naraz (czeka na odpowiedź);
(2) pierwszy ładunek jako `fullLoad` w paczkach, potem `update`; (3) EVSE ID z `OperatorID` huba, inaczej 018;
(4) `IsHubjectCompatible` ustawione świadomie, bo `false` blokuje zdalny start (604);
(5) CDR raz, z SessionID huba; (6) tabela `OperatorID` ↔ (`country_code`, `party_id`) w konfiguracji.

## Pułapki
- Wysyłanie pushów tej samej operacji równolegle (kolejność nie jest gwarantowana).
- Podawanie w `ProviderID`/`OperatorID` ID pod-partnera zamiast huba; pod-partner idzie w `EvseID`/`EvcoID`.
- Czekanie na błąd huba, gdy EMP jest offline: przy CDR hub zwraca sukces, zaległości EMP pobiera sam.
- Traktowanie `_V2.1` w nazwie operacji jako wersji protokołu.
- Wysyłanie `PIN` jako skrótu w `AuthorizeStart`: PIN idzie jawnie (hub sam liczy skrót; skrót skrótu = odmowa).
- Pull EVSE bez paginacji; `LastCall` razem z `SearchCenter` (dozwolone tylko jedno).
- Zapominanie o strefie czasowej w czasach CDR: psuje taryfy czasowe u EMP.
- Obiecywanie korekty CDR w OICP bez ustaleń z hubem.

## Checklista
- [ ] Rola (CPO/EMP/obie, hub) i wersje operacji spisane; certyfikat i ID zgodne.
- [ ] Kody 017/018/603/604 obsłużone; pushe sekwencyjne, `ActionType` świadomie dobrany.
- [ ] Paginacja i delta w pull EVSE.
- [ ] SessionID z huba przechowywany i podawany w całej sesji; własne ID w polach `...PartnerSessionID`.
- [ ] CDR: jeden na SessionID, czasy ze strefą, pola obowiązkowe 2.3.
- [ ] Adapter OICP za interfejsem modelu kanonicznego; mapowanie `OperatorID` ↔ `party_id` jawne.
- [ ] Fakty o kosztach, zasięgu i innych hubach oznaczone [do weryfikacji].

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| szczegóły operacji EMP, kody statusu, zmiany 2.3, pola obowiązkowe | `references/operacje-oicp.md` |
| mapowanie pojęć i pól OCPI ↔ OICP, różnice semantyczne, szkic adaptera | `references/adaptery-ocpi-oicp.md` |

## Źródła
- OICP 2.3 (CPO i EMP), github.com/hubject/oicp, pliki `01_*_Communication_Paradigms`, `02_*_Services_and_Operations`,
  `03_*_Data_Types`, Release Notes 2.3; baza fabryki `.claude/knowledge/oicp/doc.txt`, pobrane 2026-10-20 (CC BY-SA 4.0).
- README github.com/hubject/oicp: wycofanie OICP 2.1 w dniu 13 kwietnia 2023, pobrane 2026-10-20 (poza cache bazy).
- OCPI 2.2.1 d2 i 2.3.0 (porównania), `.claude/knowledge/ocpi-2.2.1-d2/`, `.claude/knowledge/ocpi-2.3.0/`, pobrane 2026-10-20.
- Koszty, zasięg i oferty hubów (Hubject, Gireve, e-clearing.net): brak w bazie — [do weryfikacji].
