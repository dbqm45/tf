# Konteksty domeny, zdarzenia, multi-tenancy, szablon ADR

## 1. Granice kontekstów
Podział jest propozycją wyjściową — zweryfikuj go z domeną operatora.
| Kontekst | Własność (źródło prawdy) | Typowe zdarzenia wychodzące |
|---|---|---|
| Asset | stacje, EVSE, złącza, konfiguracja, Device Model, firmware | StationRegistered, ConnectorStatusChanged |
| Charging Session | cykl życia sesji i transakcji, liczniki | SessionStarted, SessionUpdated, SessionEnded |
| Authorization | tokeny, lista lokalna, decyzje Authorize | AuthorizationDecided |
| Pricing | taryfy i ich wersje, wycena | TariffPublished, SessionPriced |
| Billing/CDR | CDR niezmienny, korekty nowym zapisem, rozliczenia | CdrIssued |
| Roaming | model OCPI, rejestracje partnerów, komendy roamingowe | (adapter do OCPI) |
| Energy | limity mocy, smart charging, integracja z EMS | ChargingProfileApplied |
| Support/NOC | alarmy, zgłoszenia, widok operatora | (odbiorca zdarzeń) |

Reguła: kontekst nie czyta cudzej bazy; współdzieli zdarzenia i jawne API. Pojęcia i nazwy — dom-ev-glossary
(np. sesja vs transakcja).

## 2. Zdarzenia między kontekstami
- Zdarzenie niesie `eventId`, `tenantId`, `stationId`, czas **stacji** i czas **odbioru** (różnią się po offline).
- Producent zapisuje stan i zdarzenie atomowo (outbox), konsument jest idempotentny (inbox).
- Kolejność: gwarantowana per `stationId`; konsumenci łączący dane wielu stacji nie mogą zakładać globalnego porządku.
- Zdarzenia wersjonuj; dodawanie pól wstecznie zgodne, usuwanie i zmiana znaczenia — nowa wersja zdarzenia.

## 3. Multi-tenancy i white-label
| Decyzja | Opcje | Kryterium |
|---|---|---|
| izolacja danych | wspólny schemat z `tenantId` / osobny schemat / osobna baza | wymagania umowne i regulacyjne vs koszt |
| izolacja połączeń | wspólna brama z limitami / pula bram per najemca | hałaśliwy sąsiad, wymagania dużych CPO |
| rozpoznanie najemcy | ścieżka URL stacji, certyfikat (profil 3), rejestr stacji | źródło **uwierzytelnione**, nie z treści ramki |
| tożsamość w roamingu | `country_code` + `party_id` na najemcę (lub na rolę najemcy) | dom-ev-identifiers; rola white-label w OCPI ustalana w umowie (dom-ev-market-roles) |
| limity | połączenia, handshake’i, komendy, wiadomości na najemcę | brak limitu = jeden najemca zagłodzi resztę |
| migracja/wdrożenie | wdrożenia wspólne vs okna per najemca | wpływ na reconnect storm |

Testy izolacji: próba odczytu cudzych danych przez API, przez zdarzenie i przez rejestr połączeń (stacja najemcy A
nie może przejąć `stationId` najemcy B). Dane osobowe kierowców per najemca: osobna podstawa, retencja i dostęp (RODO).

## 4. Szablon ADR
```
ADR-NN: <decyzja w jednym zdaniu>
Kontekst: <siły, wymagania, skala (z oznaczeniem [do weryfikacji])>
Opcje: A ... / B ... / C ...
Decyzja: <wybór i dlaczego>
Konsekwencje: <koszt, ryzyka, co monitorujemy, kiedy wracamy do decyzji>
```
Typowe ADR: wydzielenie bramy; rejestr połączeń i TTL; szyna komend; klucz partycji; polityka heartbeat;
obrona przed storm; model wspólny wersji; poziom izolacji najemców; granice kontekstów.

## 5. Źródła
Wiedza ogólna architektury (oznaczona jako taka), `.claude/skills/dom-ev-charging/references/ocpi.md`, `ocpp.md` (stan na 2026-10-20).
