---
name: dom-ev-csms-migration
description: Użyj przy migracji ładowarek między systemami CSMS lub z OCPP 1.6 na 2.0.1 — inwentarz, przełączenie stacji falami, ciągłość sesji i roamingu, rollback.
metadata:
  przeglad: 2027-04-20
  katalog: "Użyj, gdy przenosisz zarządzanie ładowarkami z jednego CSMS/CPMS na inny (wyjście z zewnętrznego SaaS na własny CPMS albo do innego dostawcy) lub z OCPP 1.6 na 2.0.1 — inwentarz stacji (model, firmware, wersja OCPP, profil bezpieczeństwa, certyfikaty, SIM/APN), podział własności danych (historia sesji i CDR, tokeny, taryfy, EVSE ID, party_id OCPI, umowy roamingowe), zależności od dostawcy (DataTransfer, firmware zarządzany), zmiana adresu CSMS i poświadczeń na stacji (SetNetworkProfile, NetworkConfigurationPriority, Reset), fale pilot → partie, okno serwisowe, rollback, stacje wymagające wizyty serwisu, ciągłość biznesowa (sesje w toku, transakcje offline, CDR przed i po, ten sam EVSE ID i Location ID w OCPI, taryfy, terminale płatnicze, smart charging, uptime w okresie migracji), rejestr ryzyk, komunikacja z partnerami, kryteria wyłączenia starego systemu. Nie do architektury CSMS (dom-ev-cpms-architecture), onboardingu nowego modelu ładowarki (dom-ev-charger-onboarding), szczegółów OCPI (dom-ev-ocpi), rejestru assetów (dom-ev-asset-operations), szczegółów komunikatów OCPP (dom-ev-ocpp-16, dom-ev-ocpp-2x)."
  slowa: "migracja CSMS, zmiana CSMS, zmiana dostawcy CSMS, wyjście z SaaS, własny CPMS, przepięcie stacji, przełączenie ładowarek, zmiana adresu CSMS, zmiana URL CSMS, nowy backend, fale migracji, pilot migracji, rollback migracji, migracja 1.6 na 2.0.1, upgrade OCPP, koegzystencja 1.6 i 2.0.1, eksport danych od dostawcy, historia sesji, vendor lock-in, Driivz, Data Act eksport, przeniesienie EVSE ID, przerwa w publikacji OCPI, sesje w toku podczas migracji, CSMS migration, switch CSMS, charge point migration, cutover, decommission old CSMS, SetNetworkProfile, NetworkConfigurationPriority, stacje bez zdalnego dostępu, wizyta serwisu"
---

# Migracja CSMS i wersji OCPP — przełączenie floty bez utraty biznesu

Migracja to **zmiana przekrojowa**: stacja zmienia adres i poświadczenia, ale razem z nią przenosisz sesje, CDR, ceny,
roaming, tokeny, terminale płatnicze i raporty. Błąd w jednej warstwie wychodzi w innej (stacja online, a eMSP nie widzi
lokalizacji). Skill daje kolejność i bramki; protokoły i architekturę opisują skille sąsiednie.
Role stron i własność danych → **dom-ev-market-roles**; OCPI → **dom-ev-ocpi**; CDR → **dom-ev-cdr-settlement**.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/inwentarz-i-wlasnosc.md` | robisz inwentarz floty, rozdzielasz „czyje to dane”, szukasz zależności od dostawcy, żądasz eksportu |
| `references/przelaczenie-stacji.md` | ustawiasz nowy adres i poświadczenia na stacji, planujesz fale, rollback, stacje „tylko wizyta” |
| `references/ciaglosc-i-plan.md` | planujesz sesje w toku, OCPI, taryfy, smart charging, raporty uptime, rejestr ryzyk, komunikację, wyłączenie starego systemu |

## Procedura
| # | Krok | Wynik / bramka |
|---|---|---|
| 1 | **Inwentarz floty** i zależności od dostawcy (kolumny w references) | tabela stacja → model, firmware, OCPP, profil, SIM; lista zależności |
| 2 | **Własność danych**: co eksportujesz, w jakim formacie, do kiedy; wniosek o eksport | potwierdzony zakres i termin eksportu |
| 3 | **Nowy CSMS gotowy**: typy stacji z inwentarza przeszły onboarding (dom-ev-charger-onboarding), PKI i poświadczenia gotowe | karta typu = „dopuszczony” dla każdego modelu |
| 4 | **Dane referencyjne** w nowym systemie: stacje, EVSE ID, taryfy, tokeny, lokalizacje OCPI | uzgodnienie liczb 1:1 ze starym systemem |
| 5 | **Pilot** 1–3 stacje (laboratorium, potem produkcja o niskim ruchu) z pełnym cyklem: sesja, CDR, OCPI, płatność | kryteria przejścia spełnione |
| 6 | **Fale** wg modelu, firmware, lokalizacji; przed każdą falą bramka, po niej obserwacja | decyzja człowieka „idziemy dalej” |
| 7 | **Stacje trudne** (bez zdalnego dostępu, stary firmware) — wizyty serwisu | lista z terminami |
| 8 | **Okres równoległy**: stary system tylko do odczytu historii i eksportu; podwójny monitoring | brak stacji na starym |
| 9 | **Wyłączenie starego systemu** po kryteriach z references | protokół zamknięcia |

Kroki 2–4 idą równolegle z długim czasem wykonania. Czas eksportu i umowa z dostawcą bywają wąskim gardłem całej migracji.

## Zasady, które wyznaczają kolejność
1. **Najpierw dane i nowy system, potem stacje.** Stacja przełączona na system bez jej taryf, tokenów i EVSE ID
   to awaria biznesowa przy zdrowym połączeniu.
2. **Stacja ma dwa adresy, dopóki nie zamkniesz fali.** Stary profil sieciowy zostaje jako ścieżka powrotu; usuwasz go
   dopiero po kryteriach fali. W 2.0.1 robi to priorytet profili, w 1.6 — brak standardowego mechanizmu (patrz niżej).
3. **Fala = jednorodna grupa**: ten sam model, firmware, operator SIM i region. Błąd jednej konfiguracji nie kładzie floty.
4. **Przełączasz stację bez sesji w toku** (`Available` / brak transakcji) w oknie serwisowym; komend nie wysyłasz
   do stacji z aktywną transakcją.
5. **Tożsamość publiczna się nie zmienia**: EVSE ID, `party_id`, Location ID i `evse.uid` w OCPI są te same przed i po.
   Zmiana identyfikatora = nowy zasób dla eMSP, utrata historii i tokenów (zasady: dom-ev-identifiers).
6. **Jedna wersja OCPP naraz na stację.** Migracja systemu i migracja wersji OCPP to dwa osobne projekty;
   łączenie ich w jednej fali mnoży przyczyny awarii. Zacznij od zmiany systemu przy tej samej wersji.

## Przełączenie stacji — skrót (szczegóły i pola: references/przelaczenie-stacji.md)
| Wersja | Jak zmienić adres CSMS | Uwagi |
|---|---|---|
| OCPP 1.6 | `ChangeConfiguration` (`key` ≤50 znaków, `value` ≤500) na kluczu producenta; **w standardzie 1.6 nie ma klucza adresu CSMS** [do weryfikacji w dokumentacji modelu] | często potrzebna lokalna konfiguracja lub narzędzie producenta; po zmianie zwykle `Reset` |
| OCPP 2.0.1 | `SetNetworkProfile` (`configurationSlot`, `connectionData` z `ocppCsmsUrl`, `securityProfile`, `ocppVersion`, `ocppInterface`, `messageTimeout`) → `SetVariables` na priorytecie profili → `Reset` | stary profil zostaje w innym slocie jako rollback |

`SetNetworkProfile` tylko zapisuje profil w slocie; **nie przełącza** stacji. Przełączenie następuje po zmianie
priorytetu profili i ponownym połączeniu (zwykle `Reset`). Nazwę zmiennej priorytetu (`NetworkConfigurationPriority`)
i dozwolone wartości sprawdź w Device Model producenta [do weryfikacji] — schematy JSON jej nie zawierają.

## Co przenosi się samo, a co nie
| Obiekt | Przenosi się? | Co robisz |
|---|---|---|
| Połączenie WebSocket | nie | nowy adres, profil bezpieczeństwa, certyfikaty po stronie nowego CSMS |
| Konfiguracja stacji (klucze 1.6, zmienne 2.0.1) | zostaje na stacji | `GetConfiguration` / `GetBaseReport` przed i po, porównaj |
| Profile smart charging | **nie** — stary CSMS ustawiał je na stacji | odczytaj `GetCompositeSchedule`, ustaw od nowa (dom-ev-smart-charging) |
| Lokalna lista autoryzacji i cache | zostaje na stacji, może być nieaktualna | wyślij pełną listę z nowego systemu (`SendLocalList`) lub wyczyść |
| Historia sesji i CDR | nie | eksport + import tylko do raportów; CDR wystawione nie są wystawiane ponownie |
| Transakcje offline | stacja trzyma je do wysłania | pierwsze połączenie z nowym CSMS wysyła zaległe — przygotuj import (patrz references) |
| Rezerwacje i zdalne starty | nie | zakończ przed falą |

## Migracja OCPP 1.6 → 2.0.1 w skrócie
Szczegóły komunikatów i Device Model: **dom-ev-ocpp-2x** (mapa 1.6 → 2.x) i **dom-ev-ocpp-16**. Od strony migracji:
- **Koegzystencja w jednym CSMS**: brama rozpoznaje wersję po podprotokole WebSocket (`ocpp1.6` / `ocpp2.0.1`), a rdzeń
  pracuje na modelu wewnętrznym, nie na komunikatach żadnej wersji (warstwa anty-korupcyjna; architektura →
  dom-ev-cpms-architecture). Flota mieszana trwa miesiące.
- **Mapowanie**: `StartTransaction` / `StopTransaction` → `TransactionEvent` (`Started` / `Updated` / `Ended`, `seqNo`);
  `transactionId` w 1.6 nadaje CSMS, w 2.0.1 stacja; 9 statusów konektora 1.6 → 5 w 2.0.1 (stan ładowania wynika
  z transakcji). Statusy i ID transakcji w raportach muszą mieć jeden słownik przed i po.
- **Nie ma aktualizacji „w miejscu” przez OCPP**: wersję obsługiwaną przez stację zmienia firmware i konfiguracja
  profilu sieciowego (`ocppVersion` w `NetworkConnectionProfile`), po czym stacja łączy się podprotokołem 2.0.1.
  Czy model w ogóle obsługuje 2.0.1 po aktualizacji, wynika z karty onboardingu [do weryfikacji u producenta].
- **Rollback wersji** wymaga, by stary profil (1.6) został w slocie, a CSMS dalej obsługiwał 1.6.

## Przykład
Operator ma 1200 stacji w SaaS-owym CSMS (przykład kategorii: Driivz) i przechodzi na własny CPMS.
1. Inwentarz: 700 stacji model A (OCPP 1.6, firmware 3.2), 300 model B (2.0.1), 200 model C (1.6, stary firmware,
   SIM z prywatnym APN). Zależność: model C korzysta z `DataTransfer` dostawcy do raportu licznika.
2. Wniosek o eksport (sesje, CDR, tokeny, taryfy, lista stacji) z terminem; Data Act daje podstawę do zmiany dostawcy
   usług przetwarzania danych (dom-ev-regulations-eu). Prawa do `party_id` i EVSE ID sprawdzasz w umowie.
3. Pilot: 3 stacje modelu B w laboratorium, potem 2 w lokalizacji o małym ruchu. Przed pilotem profil sieciowy nr 2
   w slocie 2, priorytet nadal na starym.
4. Fala 1: 100 stacji modelu B, nocą, tylko stacje `Available` bez transakcji. Po fali: 100% `BootNotification`
   `Accepted`, `Heartbeat`, jedna testowa sesja na lokalizację, OCPI `Locations` bez zmian EVSE ID.
5. Model A (1.6): brak klucza adresu w standardzie — producent daje klucz własny; test na 5 stacjach, potem fale po 150.
6. Model C: wizyta serwisu z lokalną konfiguracją; 40 stacji bez SIM-a w sieci operatora — zgłoszenie do operatora SIM.
7. Po 3 tygodniach bez stacji na starym systemie: ostatni eksport, wyłączenie.

## Pułapki
- Zakładanie, że wszystkie stacje 1.6 mają ten sam klucz adresu CSMS. Nie mają; sprawdź w `GetConfiguration` modelu.
- `SetNetworkProfile` przyjęty = stacja przełączona. Nie: bez zmiany priorytetu i ponownego połączenia nic się nie dzieje.
- Kasowanie starego profilu sieciowego przed zakończeniem fali — rollback wymaga wizyty serwisu.
- Zmiana EVSE ID „przy okazji” albo nowe `evse.uid`; eMSP traktuje to jako nowy zasób.
- Brak `REMOVED` jako zamiany: usunięcie lokalizacji w starym systemie wyśle `REMOVED` do eMSP, jeśli stary system
  jeszcze publikuje. Wyłącz publikację starego systemu **po** przejęciu, nie przed, i nie dopuść do dwóch publikujących naraz.
- Przeoczone profile smart charging: po przełączeniu stacja trzyma stary limit albo traci go po `Reset`.
- Wyłączenie starego systemu przed zamknięciem CDR i rozliczeń za okres przed migracją.
- Uptime w raportach za okres migracji liczony z jednego systemu: luki między systemami to „nieznany”, nie awaria
  (reguły: dom-ev-kpi-analytics, wymogi NEVI: dom-ev-regulations-us).
- Fala bez uzgodnienia z operatorem SIM / firewalla po stronie lokalizacji (whitelista adresów IP nowego CSMS).

## Checklista
- [ ] Inwentarz floty z wersją OCPP, firmware, profilem bezpieczeństwa, SIM/APN; zależności od dostawcy spisane
- [ ] Zakres i termin eksportu danych potwierdzony; własność `party_id`, EVSE ID, tokenów, umów roamingowych jasna
- [ ] Każdy model z inwentarza ma kartę onboardingu w nowym CSMS
- [ ] Nowe poświadczenia i certyfikaty wydane; profil bezpieczeństwa nie niższy niż dotychczasowy
- [ ] Pilot z pełnym cyklem sesja → CDR → OCPI → płatność; kryteria przejścia zapisane przed falą
- [ ] Stary profil sieciowy zostaje do końca fali; rollback przećwiczony na pilocie
- [ ] EVSE ID, Location ID i `party_id` bez zmian; partnerzy OCPI poinformowani
- [ ] Profile smart charging, lista lokalna, taryfy i terminale płatnicze przeniesione i sprawdzone
- [ ] Podwójny monitoring i raport uptime z okresu migracji z oznaczeniem luk
- [ ] Kryteria wyłączenia starego systemu spełnione, protokół zamknięcia podpisany przez człowieka

## Źródła
- ocpp-json-schemas (baza fabryki): SetNetworkProfileRequest.json (OCPP 2.0.1), `.claude/knowledge/ocpp-json-schemas/doc.txt`
  L3494-3734; SetVariablesRequest.json L3735 i nast.; ResetRequest.json 2.0.1 L3889 i nast.; ChangeConfiguration.json
  1.6 L3159-3180; Reset.json 1.6 L3201-3216 (github.com/mobilityhouse/ocpp, pobrane 2026-10-20).
- Skille fabryki: dom-ev-ocpp-2x (mapa 1.6 → 2.x), dom-ev-regulations-eu (Data Act Art. 23-31), dom-ev-ocpi (`REMOVED`, uid vs evse_id).
- Specyfikacje OCA (Part 2, Device Model) i program certyfikacji OCA: poza bazą, oznaczone [do weryfikacji].
- Praktyka branżowa (fale, rollback, ciągłość) to wiedza ogólna, bez źródła zewnętrznego w bazie.
