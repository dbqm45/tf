---
name: dom-ev-charging
description: Użyj przy przeglądzie całego ładowania EV — mapa warstw od auta do eMSP, który protokół za co, sesja w skrócie, archetypy i niezmienniki domeny.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy trzeba zobaczyć ładowanie EV w całości — warstwy protokołów (pojazd–ładowarka–CSMS–eMSP), który protokół łączy kogo, sesja w skrócie, archetypy i niezmienniki domeny, punkt startu przed wyborem skilla szczegółowego. Nie do ISO 15118 i Plug & Charge (dom-ev-iso15118), V2G (dom-ev-v2x), baterii i pojazdu (dom-ev-vehicle-battery), metrologii (dom-ev-metering-calibration), słownika pojęć (dom-ev-glossary), ról rynku (dom-ev-market-roles), formatów identyfikatorów (dom-ev-identifiers), komunikatów OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x), protokołu OCPI (dom-ev-ocpi), taryf i ceny (dom-ev-tariffs-pricing), CDR i rozliczeń (dom-ev-cdr-settlement), przebiegu sesji (dom-ev-session-lifecycle), architektury CSMS (dom-ev-cpms-architecture) ani diagnozy awarii (dom-ev-diagnostics)."
  slowa: "przegląd ładowania EV, mapa warstw, warstwy protokołów, który protokół za co, od auta do aplikacji, od samochodu do eMSP, jak działa ładowanie, ekosystem ładowania, archetypy domeny ładowania, model domeny ładowania, niezmienniki domeny, overview of EV charging, protocol layers"
---

# Ładowanie pojazdów elektrycznych — wiedza branżowa

Skill mówi, **jak działa branża** (pojęcia, role, protokoły, przepływy). Jak to zamodelować — sekcja
„Pojęcia domenowe”. Wiedza pochodzi z importu (źródła 2024–2025, włączone 2026-09-27);
wersje i daty oznaczone „do weryfikacji” sprawdza `researcher`, zanim trafią do decyzji lub dokumentu.

## Wydzielone skille
Pojęcia i nazewnictwo (Location/EVSE/Connector, liczenie punktów po EVSE, CSMS/CPMS) → **dom-ev-glossary**. Role
stron i przepływy pieniędzy → **dom-ev-market-roles**. Formaty EVSE ID, EMAID, `party_id` i ich walidacja →
**dom-ev-identifiers**. Komunikaty, statusy i transakcje OCPP → **dom-ev-ocpp-16**, **dom-ev-ocpp-2x**. Przebieg sesji
end-to-end → **dom-ev-session-lifecycle**; architektura CSMS → **dom-ev-cpms-architecture**; diagnoza awarii →
**dom-ev-diagnostics**; sprzęt, onboarding i testy na symulatorze → **dom-ev-charger-hardware**,
**dom-ev-charger-onboarding**, **dom-ev-simulation-testing**. Protokół OCPI → **dom-ev-ocpi**; taryfy i cena →
**dom-ev-tariffs-pricing**; CDR, korekty i rozliczenie → **dom-ev-cdr-settlement**; OICP i huby → **dom-ev-oicp-hubs**;
płatności → **dom-ev-payments**. Smart charging i energia lokacji → **dom-ev-smart-charging**,
**dom-ev-energy-management**; ISO 15118, DIN 70121 i Plug & Charge → **dom-ev-iso15118**; V2G/V2H → **dom-ev-v2x**;
bateria, krzywa ładowania, 400/800 V → **dom-ev-vehicle-battery**; MID, Eichrecht, OCMF → **dom-ev-metering-calibration**.
Ten skill zostaje przeglądem warstw i archetypów domeny.

## Mapa warstw
**Warstwy protokołów:**
| Protokół | Łączy | Do czego |
|---|---|---|
| ISO 15118 / DIN 70121 / PWM | pojazd ↔ ładowarka | parametry ładowania, Plug & Charge, V2G |
| OCPP | ładowarka ↔ CSMS | sterowanie sprzętem, statusy, transakcje, telemetria, smart charging |
| OCPI (alternatywa: OICP) | CPO ↔ eMSP / hub | roaming: lokalizacje, taryfy, tokeny, sesje, CDR, komendy |
| OpenADR | sieć ↔ system energii | demand response — poza samym ładowaniem |

„Roaming, rozliczenia między firmami” → OCPI. „Ładowarka nie odpowiada, statusy, firmware” → OCPP. „Auto, certyfikat,
SoC” → ISO 15118.

**Jednostki:** kW = moc (jak szybko), kWh = energia (ile). AC: konwersja w aucie (ładowarka pokładowa, typowo
3,7–22 kW — często ona ogranicza, nie stacja); DC: prąd stały prosto do baterii.

## Sesja end-to-end (skrót — szczegóły: dom-ev-session-lifecycle)
1. **Podłączenie** — `StatusNotification` (1.6 `Preparing` / 2.0.1 `Occupied`).
2. **Autoryzacja** — aplikacja (OCPI `START_SESSION` → OCPP Remote/RequestStart), RFID (`Authorize`, tokeny z OCPI
   Tokens lub lokalna lista), terminal płatniczy (preautoryzacja), Plug & Charge (certyfikat kontraktu, EMAID).
3. **Ładowanie** — `StartTransaction` (1.6) / `TransactionEvent Started` (2.0.1, `seqNo`), `MeterValues`, OCPI
   `Session` do eMSP, profile mocy.
4. **Zakończenie** — `StopTransaction` / `TransactionEvent Ended`, odblokowanie złącza, powrót do `Available`.
5. **Rozliczenie** — CDR (niezmienny; korekta = CDR kredytowy) przez OCPI CDRs → faktura eMSP, rozliczenie hurtowe
   CPO↔eMSP.

## Wersje (fakty wg importu)
| Standard | Stan | Uwagi |
|---|---|---|
| OCPP 1.6 / 2.0.1 / 2.1 | — | wersje, edycje i różnice: dom-ev-ocpp-16, dom-ev-ocpp-2x |
| OCPI 2.2.1 / 2.3.0 | — | wersje, wydanie d2 i różnice: dom-ev-ocpi |
| DIN 70121 / ISO 15118-2 / -20 | — | wersje i różnice: dom-ev-iso15118; V2G: dom-ev-v2x |

Integracje buduj wielowersyjnie (sieć ma mieszany sprzęt); zawsze zapisuj wersję **i edycję** specyfikacji.

## Pojęcia domenowe (archetypy biznesowe)
| Obszar EV | Archetyp | Na co uważać |
|---|---|---|
| CPO, eMSP, hub, kierowca, flota | **Party** (role i relacje stron) | jedna strona w wielu rolach; identyfikator OCPI strony to `country_code` + `party_id`; EMAID, RFID i konto to różne identyfikatory |
| EVSE jako zasób, rezerwacje (`ReserveNow`, OCPI `RESERVE_NOW`, Bookings) | **Availability** | zasobem jest EVSE, nie connector ani stacja; blokada w czasie; wyłączenie serwisowe to też blokada |
| Taryfy OCPI (energia, czas, postój, opłata stała, ograniczenia czasowe i mocowe) | **Pricing** + **Quantity/Money** | kWh, kW, minuty i waluta jako wartości z jednostką; cena netto/brutto; taryfa to polityka cenowa, nie liczba w kodzie |
| Sesja → CDR → faktura, rozliczenie CPO↔eMSP | **Accounting** | CDR jako niezmienny zapis; korekty nowymi zapisami; rozliczenie hurtowe, nie per sesja |

Przy modelowaniu pilnuj niezmienników (CDR niezmienny, korekty nowymi zapisami) i spójności publikacji zdarzeń z zapisem
w bazie (zdarzenie nie może zginąć ani zdublować rozliczenia).

## Czytaj references, gdy…
| Pytanie | Plik |
|---|---|
| komunikat OCPP, format ramek, kody błędów, profile bezpieczeństwa, smart charging, offline, testowanie — najpierw dom-ev-ocpp-16 / dom-ev-ocpp-2x; tu materiał źródłowy | `references/ocpp.md` |
| OCPI — najpierw dom-ev-ocpi, dom-ev-tariffs-pricing, dom-ev-cdr-settlement; tu materiał źródłowy z importu | `references/ocpi.md` |
| kolejność wiadomości w sesji, 4 ścieżki autoryzacji, moment CDR i rozliczenia | `references/cykl-sesji-ladowania.md` |
| Plug & Charge, PKI, DIN 70121 vs ISO 15118 — najpierw dom-ev-iso15118 (V2G: dom-ev-v2x); tu materiał źródłowy z importu | `references/iso-15118.md` |
| złącza, AC/DC, kW/kWh, punkt vs stacja, instalacja domowa i komercyjna | `references/infrastruktura-ladowania.md` |
| typy pojazdów (BEV/PHEV/HEV/RE-EV/FCEV), komponenty — najpierw dom-ev-vehicle-battery; tu materiał z importu | `references/pojazdy-elektryczne.md` |

## Pułapki
- Traktowanie OCPI jak systemu płatności — przenosi dane do rozliczeń, nie realizuje płatności ani faktur.
- Wymaganie SoC w modelu sesji (bywa niedostępny bez ISO 15118; dom-ev-vehicle-battery).

## Checklista
- [ ] Rola strony (CPO/eMSP/hub) i kierunek komunikacji ustalone jawnie
- [ ] Jednostka dostępności = EVSE; identyfikatory EVSE/Connector zgodne z formatem
- [ ] Wersja (i edycja) OCPP/OCPI zapisana; obsługa wielu wersji rozważona
- [ ] Taryfy, energia i kwoty jako wartości z jednostką; CDR niezmienny
- [ ] Niepewne wersje/daty przekazane do weryfikacji (`researcher`)

Źródła (import): OCA/openchargealliance.org, github.com/ocpi/ocpi, evroaming.org, ocpplab.com, fransiscuss.com,
virta.global, driveco.com, Renewable Energy Institute — treść opracowana własnymi słowami.
