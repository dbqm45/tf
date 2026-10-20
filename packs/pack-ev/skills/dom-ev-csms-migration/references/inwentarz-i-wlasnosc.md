# Inwentarz floty, własność danych i zależności od dostawcy

Spis treści: 1. Inwentarz · 2. Własność danych · 3. Eksport (Data Act) · 4. Zależności od dostawcy

## 1. Inwentarz floty (jedna tabela, jeden wiersz = jedna stacja)
| Kolumna | Po co w migracji |
|---|---|
| stationId / `chargePointId`, EVSE ID każdego punktu | klucz łączenia starego i nowego systemu; EVSE ID nie zmienia się |
| producent, model, numer seryjny, firmware | grupowanie fal; zgodność z kartą onboardingu nowego CSMS |
| wersja OCPP i edycja, podprotokół | czy zmiana adresu to `ChangeConfiguration` czy `SetNetworkProfile` |
| profil bezpieczeństwa (0–3), dane Basic Auth, certyfikat stacji i jego ważność | co trzeba wydać po stronie nowego CSMS; profil nie może się obniżyć |
| zdalny dostęp: czy stacja przyjmuje zmianę adresu zdalnie, czy wymaga lokalnej konfiguracji | lista „tylko wizyta serwisu” |
| SIM / APN / VPN, operator, status karty | nowy CSMS bywa za firewallem lub na innym APN; limit danych |
| lokalizacja, site host, godziny serwisowe | okna serwisowe, kontakt na miejscu |
| profile smart charging ustawione na stacji, lista lokalna | do odtworzenia po przełączeniu |
| terminal płatniczy: model, integracja (przez CSMS czy niezależna) | czy terminal działa po zmianie CSMS (dom-ev-payments) |
| roaming: Location ID, `evse.uid`, publikujące platformy | ciągłość OCPI |
| taryfa przypisana do EVSE | do odtworzenia w nowym systemie (dom-ev-tariffs-pricing) |
| status życia: operational / planned / decommissioned | czego nie przenosisz; stacji wycofanych nie przełączasz |

Inwentarz bierz **z dwóch źródeł** i porównuj: eksport ze starego CSMS oraz rejestr aktywów operatora
(dom-ev-asset-operations). Rozbieżność (stacja w CSMS, której nie ma w rejestrze, albo odwrotnie) wyjaśnij przed pierwszą falą.

## 2. Własność danych — kto czym dysponuje
| Obiekt | Typowo należy do | Ryzyko przy wyjściu |
|---|---|---|
| Dane sesji, CDR, historia kierowców | operator (CPO) jako administrator/posiadacz; dostawca SaaS jako procesor | dostawca eksportuje tylko widoki raportowe, bez surowych `MeterValues` i ramek |
| Tokeny (RFID, wnioski o autoryzację) | właściciel tokenu to eMSP; CPO trzyma kopię z OCPI Tokens | brak tokenów lokalnych/własnych kart w eksporcie |
| Taryfy | operator | taryfy w formacie dostawcy, nie w OCPI Tariffs |
| EVSE ID i Location ID | operator (przydziela się je w ramach rejestru ID; format: dom-ev-identifiers) | dostawca wygenerował je w swoim schemacie i uważa za swoje |
| `country_code` + `party_id` OCPI | strona (CPO) — rejestracja w organizacji prowadzącej rejestr ID, nie u dostawcy CSMS | `party_id` zarejestrowany na dostawcę — wymaga przeniesienia lub nowej rejestracji [do weryfikacji w rejestrze] |
| Umowy roamingowe i konta u hubów | operator jako strona umowy | dostawca prowadzi je „w imieniu” — umowa cesji lub nowa umowa |
| Certyfikaty stacji i PKI | zależy od modelu: operator lub dostawca jako CA | stacje ufają CA dostawcy; zmiana CA = nowe certyfikaty na każdej stacji |
| Konfiguracja i firmware | producent ładowarki; dostawca CSMS bywa pośrednikiem | firmware „zarządzany” przez dostawcę może wymagać jego zgody na zmianę |

Zasada: dla każdego wiersza zapisz **kto jest stroną umowy**, **w jakim formacie dostajesz dane** i **do kiedy**. Brak odpowiedzi
= ryzyko w rejestrze ryzyk. To nie porada prawna.

## 3. Prawo do eksportu — Data Act
Data Act zawiera przepisy o zmianie dostawcy usług przetwarzania danych (Art. 23-31): wypowiedzenie, okres przejścia,
eksport danych i aktywów cyfrowych; opłaty za zmianę znoszone od 12.01.2027. Daty, zakres i kwalifikacja SaaS-owego CSMS
jako usługi przetwarzania danych: **dom-ev-regulations-eu** (tam z numerami artykułów i liniami źródła). Dodatkowo
dostęp do danych z produktu (stacji) ma użytkownik (Art. 3-5). W praktyce umowa dostawcy bywa ważniejsza niż przepis:
sprawdź okres wypowiedzenia, format i koszt eksportu, czas przechowywania danych po wygaśnięciu.

Wymagaj w eksporcie co najmniej: lista stacji i EVSE ID; sesje z identyfikatorami transakcji OCPP i CDR; surowe
odczyty liczników, jeśli są potrzebne do sporów; tokeny i whitelisty; taryfy i przypisania; konfiguracje stacji;
log zdarzeń i zdalnych komend. Zażądaj próbki na początku (10 stacji, miesiąc) i sprawdź ją, zanim podpiszesz harmonogram.
Dane osobowe kierowców: podstawa prawna przekazania, retencja i procesor (RODO) ustal z działem prawnym.

## 4. Zależności od dostawcy
| Zależność | Jak ją znaleźć | Co zrobić |
|---|---|---|
| `DataTransfer` z własnym `vendorId` dostawcy | przeszukaj logi wiadomości po `DataTransfer` i `vendorId`; policz po `messageId` | odtworzyć funkcję w nowym CSMS albo wyłączyć na stacji; sprawdzić, czy stacja nie czeka na odpowiedź |
| Rozszerzone klucze konfiguracji (1.6) i zmienne spoza standardu (2.0.1) | porównaj `GetConfiguration` / `GetBaseReport` ze standardowym zestawem | nowy CSMS musi je znać lub ignorować bez błędu |
| Firmware zarządzany przez dostawcę (kanał aktualizacji, podpisy) | umowa, panel dostawcy, logi `UpdateFirmware` / `FirmwareStatusNotification` | uzgodnić przekazanie podpisów i repozytorium firmware, albo plan aktualizacji przed migracją |
| Funkcje dostawcy poza OCPP: load balancing, reguły cen dynamicznych, powiadomienia | wywiad z operacjami, lista modułów dostawcy | odtworzyć przed falą lub świadomie zrezygnować |
| Terminale płatnicze i bramki płatności zintegrowane przez dostawcę | umowa z acquirerem, konfiguracja terminala | nowe połączenie, nowe klucze, ponowna certyfikacja po stronie acquirera (dom-ev-payments) |
| Integracje roamingowe prowadzone przez dostawcę | lista partnerów OCPI/OICP i ich poświadczenia | patrz references/ciaglosc-i-plan.md |
| SIM/APN/VPN dostarczone przez dostawcę | umowa, panel SIM | przeniesienie kart albo nowy APN; wymiana kart to wizyta serwisu |

Deklaracja: ten plik nie wskazuje wad żadnego produktu; nazwy produktów to przykłady kategorii.
