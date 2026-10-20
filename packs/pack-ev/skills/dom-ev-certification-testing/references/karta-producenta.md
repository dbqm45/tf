# Karta producenta i modelu — szablon i zasady prowadzenia

> **Spis treści:** 1. Gdzie karta żyje · 2. Szablon · 3. Zasady wpisów · 4. Wpis o odchyleniu · 5. Cykl życia · 6. Czego nie wpisywać

Karta zbiera **historię jednego modelu** (i producenta) w sieci operatora: wersje firmware, zachowania odbiegające od
specyfikacji z dowodem, status certyfikacji per kraj, kontakt serwisu. Karta onboardingu
(`.claude/skills/dom-ev-charger-onboarding/references/karta-onboardingu.md`) opisuje decyzję o jednym typie;
karta producenta jest żywym rejestrem nad nią. Fabryka nie zawiera odchyleń konkretnych producentów — każdy wpis
powstaje w projekcie z własnego dowodu.

## 1. Gdzie karta żyje
- W repozytorium projektu: `docs/project/vendors/<producent>-<model>.md` (małe litery, myślniki), np.
  `docs/project/vendors/<producent>-<model>.md`. Producent bez modelu: `docs/project/vendors/<producent>.md` (kontakt,
  wspólne zasady). Dowody (ramki, logi) obok, w `docs/project/vendors/evidence/<producent>-<model>/`, w formie
  zanonimizowanej (bez idTag, danych kierowców, kluczy, haseł).
- Zmiana karty przechodzi przegląd jak kod. Wpis w dzienniku projektu (`docs/project/`) wskazuje kartę, gdy zapada decyzja.
- Sekretów nie ma w karcie; jest odwołanie do magazynu sekretów.

## 2. Szablon
```markdown
# <Producent> <Model>

## Tożsamość
- producent (dokładnie z `chargePointVendor`): <...>
- model (dokładnie z `chargePointModel`): <...>
- opis: <DC/AC, moc znamionowa kW, liczba EVSE i złączy>
- licznik: <producent, typ, klasa, numer certyfikatu — albo „brak danych — dopytać”>
- terminal płatniczy: <typ albo „brak”>
- łączność: <LAN / Wi-Fi / LTE>
- ostatnia aktualizacja karty: <RRRR-MM-DD>, autor: <osoba>

## Wersje (jeden wiersz na kombinację)
| firmware (ciąg z Boot) | wersja OCPP i edycja | profil bezpieczeństwa | status w sieci | data | dowód/raport |
|---|---|---|---|---|---|
| <...> | <1.6 / 2.0.1 / 2.1, edycja [do weryfikacji]> | <1/2/3> | laboratorium / pilot / dopuszczony / wycofany | <data> | <ścieżka> |

## Certyfikat OCPP (OCA) — deklarowany [do weryfikacji]
- numer/odnośnik, wersja i edycja, profile w zakresie, firmware w teście, data, raport (ścieżka) — albo „brak”.

## Wspierane funkcje (deklaracja vs wynik testu)
| funkcja | deklaracja producenta (źródło, data) | wynik testu u nas (data, wiersz macierzy) |
|---|---|---|
| Smart charging (A / W) | <...> | <przeszło / odchylenie / nie sprawdzono> |
| Firmware Management | | |
| Local Auth List | | |
| Reservation | | |
| Odczyt podpisany (OCMF) | | |
| Plug & Charge (ISO 15118) | | |

## Klucze konfiguracji / zmienne (z odpowiedzi stacji)
| klucz / zmienna (dokładna nazwa) | wartość operatora | `readonly` | wymaga restartu | data odczytu |
|---|---|---|---|---|

## Znane odchylenia od specyfikacji
(wpisy wg pkt 4; brak wpisów = „nie stwierdzono w testach <lista>”, nie „brak odchyleń”)

## Status certyfikacji per kraj
| kraj | firmware | wymogi krajowe (licznik, odbiór, rejestry) — dokument i data | status | decyzja (kto, kiedy) |
|---|---|---|---|---|

## Serwis i kontakt
- kontakt techniczny/serwisowy: <rola, kanał, godziny, SLA z umowy>; ścieżka eskalacji; numer zgłoszeń otwartych: <...>
- dokumentacja: <wersja, data pobrania, ścieżka>

## Historia zmian karty
| data | zmiana | autor |
|---|---|---|
```

## 3. Zasady wpisów
1. **Dokładne wartości z ramki**, nie z ulotki: vendor, model i firmware tak, jak przyszły w `BootNotification`.
2. **Każde twierdzenie ma źródło i datę:** deklaracja producenta (dokument, wersja, data) albo pomiar u nas (log,
   wiersz macierzy, data). Wpis bez źródła oznacz **[niezweryfikowane]** albo go nie dodawaj.
3. **Brak danych to „brak danych — dopytać”**, nie puste pole ani domysł.
4. **Odchylenie dotyczy konkretnej wersji firmware.** Po nowym firmware wpis dostaje status: `do ponownego
   sprawdzenia` aż do testu; nie kasujesz go bez dowodu, że zniknął.
5. **Nie przepisujesz opinii** (forum, rozmowy, „słyszałem”, notatki wydania jako fakt zachowania). Opinia może być
   tropem do testu; do karty trafia dopiero wynik testu.
6. **Obejście za flagą** ograniczoną do (producent, model, firmware); nazwa flagi w karcie.
7. Zmiany karty ma sprawdzić druga osoba; decyzje o statusie `dopuszczony` podpisuje człowiek.

## 4. Wpis o odchyleniu
| Pole | Treść |
|---|---|
| id | `<producent>-<model>-NNN` |
| zachowanie | jedno zdanie: co stacja robi, a co przewiduje specyfikacja (wersja OCPP i edycja — pole/komunikat z nazwą w oryginale, sprawdzone w schemacie lub specyfikacji) |
| dowód | ramki lub plik logu z numerami linii; wersja firmware; kto i jak odtworzył; data pierwszej i ostatniej obserwacji |
| warunki | kiedy występuje (po restarcie, offline, określony typ złącza) i kiedy nie |
| wpływ | statusy, sesje, energia, rozliczenie, bezpieczeństwo |
| obejście | flaga w CSMS, domyślnie wyłączona, zakres (producent, model, firmware) |
| zgłoszenie | numer zgłoszenia u producenta, data, odpowiedź (cytat lub streszczenie z datą) |
| status | otwarte / obejście działa / naprawione w firmware <wersja> (po teście) |

Wzorce zachowań i sposób ich testowania w 1.6: `.claude/skills/dom-ev-ocpp-16/references/odchylenia-i-offline.md`.

## 5. Cykl życia
- Nowy model → karta ze statusem `laboratorium`, wiersz w macierzy (`references/program-certyfikacji-cpo.md`).
- Nowy firmware → nowy wiersz w „Wersje”, odchylenia z poprzedniego do ponownego sprawdzenia.
- Nowy kraj → nowy wiersz „Status certyfikacji per kraj”; dokumenty krajowe jako dowód.
- Wycofanie → status `wycofany`, powód, plan zdejmowania z sieci; karta zostaje jako historia.
- Przegląd kart: przy każdej decyzji o nowym firmware i raz na kwartał (**[założenie]**) — karty bez zmian oznacz datą przeglądu.

## 6. Czego nie wpisywać
- ocen producenta w stylu „zawodny”, „zawsze psuje”;
- zachowań z cudzych doświadczeń bez własnego dowodu;
- haseł, kluczy, certyfikatów prywatnych, danych kierowców i pełnych idTag;
- ścieżek i nazw wewnętrznych systemów innych firm;
- cen i warunków umów handlowych (osobny rejestr).
