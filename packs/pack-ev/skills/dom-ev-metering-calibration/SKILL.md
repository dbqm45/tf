---
name: dom-ev-metering-calibration
description: Użyj przy legalnym pomiarze energii w ładowarce — MID i MI-011, Eichrecht, podpisany odczyt OCMF, signed_data w OCPI, HB44, legalizacja licznika.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy software musi zachować, przenieść albo sprawdzić legalny odczyt licznika — MID 2014/32/UE (MI-003 dla AC) i zmiana 2026/706 (MI-011 dla systemów pomiarowych EVSE, terminy), Eichrecht w Niemczech, struktura rekordu OCMF (PG, TX, ST, EF, TM, LC, CL), skrypt ocmf_check.py, transport podpisanych odczytów w OCPP 1.6, OCPP 2.0.1 i OCPI signed_data, NIST HB44 3.40 w skrócie, taryfa za energię a taryfa za czas, straty kabla, termin legalizacji jako zdarzenie w rejestrze assetów, rozjazd kWh licznik–CSMS. Nie do mapy całego prawa UE (dom-ev-regulations-eu), pełnego HB44 i NEVI (dom-ev-regulations-us), korekty CDR (dom-ev-cdr-settlement), obliczania ceny (dom-ev-tariffs-pricing) ani diagnozy rozjazdu z ramek (dom-ev-diagnostics)."
  slowa: "licznik MID, legalizacja licznika, Eichrecht, OCMF, odczyt podpisany, signed meter values, signedMeterValue, signed_data, SignedData, transparency software, Transparenzsoftware, PTB, MI-011, MI-003, 2026/706, klasa A B C, MMQ, punkt przekazania, transfer point, straty kabla, cable loss, compensation, legal for trade, custody transfer, calibration law, stan czasu licznika, TM, pole PG, kod TX, flaga błędu EF, certyfikat licznika, plomba, termin legalizacji, rozjazd kWh, licznik a CSMS, NIST HB44, wymiana licznika, podpis ECDSA, klucz publiczny licznika"
---

# Legalny pomiar energii przy ładowaniu — co robi software

Licznik legalny jest dowodem w sporze o kWh. Software ma **zachować odczyt bez zmian, przenieść go i sprawdzić
strukturę**; podpisu nie podrabia, energii nie przelicza. Fakty prawne pochodzą z bazy fabryki (daty pobrania w
## Źródła); co poza bazą, oznaczam **[do weryfikacji]**. To nie jest porada prawna.

## Procedura
1. Ustal reżim: UE (MID), Niemcy (Eichrecht, rekord podpisany), USA (HB44 3.40) — tabela niżej.
2. Z karty ładowarki weź: klasa (A/B/C), MMQ, numer certyfikatu, numer seryjny licznika, kabel (stały czy wymienny).
3. Sprawdź, **czy rekord podpisany dojeżdża do CSMS i CDR**: OCPP (`format` / `signedMeterValue`), OCPI `signed_data`.
4. Zachowaj surowy rekord razem z sesją; waliduj strukturę `ocmf_check.py`; podpis weryfikuje osobne narzędzie.
5. Energię do faktury licz z rejestru podpisanego (koniec − początek), nie z `MeterValues` telemetrii.
6. Terminy legalizacji i wymiany licznika prowadź jako zdarzenia w rejestrze assetów.

## Reżimy w skrócie
| Obszar | Co obowiązuje | Co robi software |
|---|---|---|
| UE, AC dziś | MID 2014/32/UE; liczniki energii czynnej to MI-003 (zał. V) — treść zał. V poza bazą **[do weryfikacji]** | karta licznika: certyfikat badania typu, klasa |
| UE, po zmianie | dyrektywa (UE) 2026/706: nowy zał. Va, **MI-011** — system pomiarowy EVSE, AC i DC; stosowanie od **10.10.2028** | nowa ładowarka DC po terminie wymaga MI-011 (szczegóły: `references/mid-mi-011.md`) |
| Niemcy | Eichrecht: odczyt podpisany, klucz publiczny licznika przekazany osobną drogą, weryfikacja programem „Transparenzsoftware” — szczegóły rozporządzeń i PTB **[do weryfikacji]** (poza bazą) | przechowuj rekord OCMF i udostępniaj kierowcy |
| USA | NIST HB44 3.40 (wydanie 2026): kWh, rozdzielczość, tolerancje, paragon | pełny opis: dom-ev-regulations-us; tu tylko dane metrologiczne |
| Polska | okres legalizacji i organ **[do weryfikacji]** (poza bazą); obowiązki UDT: dom-ev-regulations-pl | termin w rejestrze assetów |

Wymiana licznika, kabla z wtykiem lub oprogramowania metrologicznego może unieważnić legalizację — takie
zdarzenie to zmiana w rejestrze, a nie zwykły serwis.

## OCMF: struktura rekordu
Postać: `OCMF|<payload JSON>|<podpis JSON>`. Pola, tabele wartości i dziedziczenie: `references/ocmf-pola.md`.

| Element | Reguła |
|---|---|
| `PG` | `T<n>` (transakcja) albo `F<n>` (fiskalny, poza transakcją); osobny licznik na kontekst, +1 bez luk |
| `TX` | `B` początek, `C` w trakcie, `E`/`L`/`R`/`A`/`P` koniec (lokalny, zdalny, błąd, brak zasilania), `X` wyjątek, `T` zmiana taryfy, `S` pauza |
| `ST` | tylko `G` (OK) nadaje się do rozliczenia; `M` manipulacja, `X` wymiana licznika, `F` błąd odczytu itd. |
| `EF` | `E` energia, `t` czas nieużyteczne do rozliczenia |
| `TM` | czas ISO 8601 z ms i stanem: `S` synchron., `I` informacyjny, `U` nieznany, `R` względny (czas liczony zgodnie z legalizacją) |
| `RV`, `RU` | wartość jako JSON Number w oryginalnym zapisie; jednostka `kWh` albo `Wh` |
| `LC`, `CL` | parametry strat kabla i skumulowana strata (zerowana przy `TX=B`) |
| podpis | domyślnie `ECDSA-secp256r1-SHA256`; `SD` w `hex` albo `base64`; klucz publiczny poza rekordem |

Weryfikator ma sprawdzić też spójność **serii**: pierwszy rekord to początek, ostatni to koniec, nic nie dodano
ani nie usunięto (ciągła paginacja), wszystkie z tego samego numeru seryjnego.

## Skrypt `ocmf_check.py`
Polecenie (biblioteka standardowa, sieć: brak):

```
python3 .claude/skills/dom-ev-metering-calibration/scripts/ocmf_check.py <plik>.json
python3 .claude/skills/dom-ev-metering-calibration/scripts/ocmf_check.py - --json < rekord.txt
```

- Sprawdza format, pola obowiązkowe, wartości z tabel (`TX`, `RU`, `RT`, `ST`, stan czasu), paginację, kodowanie `SD`,
  odczyt początkowy i końcowy transakcji, monotoniczność czasu i energii, stan licznika, `EF`; liczy energię rejestru
  (koniec − początek) na `Decimal`, bez zmiany zapisu liczby. Pole pominięte w odczycie dziedziczy wartość z poprzedniego.
- Kod wyjścia: **0** brak błędów, **1** błędy w rekordzie, **2** nie da się odczytać pliku.
- **Nie weryfikuje podpisu** (brak ECDSA w bibliotece standardowej, klucz przychodzi spoza rekordu). Zawsze zgłasza
  ostrzeżenie `signature-not-verified`. Wynik 0 oznacza „struktura poprawna”, nie „dowód rozliczeniowy”.
- Nie sprawdza zgodności klucza z licznikiem, certyfikatu ani legalizacji. Przed rozliczeniem uruchom
  weryfikator podpisu (Transparenzsoftware) **[do weryfikacji]**.

## Transport podpisanych odczytów
| Kanał | Gdzie jest podpisany odczyt | Uwagi |
|---|---|---|
| OCPP 1.6 | `sampledValue` z `format` = `SignedData` (enum `Raw`, `SignedData`; wartość to tekst, wg OCMF hex), w `MeterValues` i `StopTransaction` | schemat w bazie potwierdza pole `format`; zawartość `value` to rekord OCMF |
| OCPP 1.6, klucze OCMF | `StopTransactionSignatureFormat` (MR: start i stop w jednym rekordzie, SR: osobne), `StopTransactionSignatureContexts`, `MeterValuesSignatureContexts`; pusta lista = bez podpisu | zalecenie S.A.F.E., nie wymóg OCPP |
| OCPP 2.0.1 | `signedMeterValue` (`SignedMeterValueType`) w `sampledValue` — `MeterValuesRequest`, `TransactionEventRequest`: wszystkie cztery pola obowiązkowe: `signedMeterData` (base64, do 2500 znaków), `signingMethod`, `encodingMethod` (do 50), `publicKey` (base64, do 2500) | `publicKey` wysyłany zależnie od zmiennej `PublicKeyWithSignedMeterValue` |
| OCPI 2.2.1 / 2.3.0 CDR | `signed_data`: `encoding_method`, `encoding_method_version`, `public_key`, `signed_values` (`nature`: Start, End, Intermediate; `plain_data`; `signed_data` base64, do 5000 znaków), `url` | OCPI nie sprawdza podpisu; szczegóły CDR: dom-ev-cdr-settlement, OCPI: dom-ev-ocpi |

Brama OCPP nie parsuje i nie normalizuje podpisanej części: zapis surowy do magazynu sesji, parsowanie do osobnej
kopii. Odchylenia producentów: dom-ev-ocpp-16, dom-ev-ocpp-2x.

## Taryfa za energię a za czas
- Zał. Va mierzy **energię** (jednostka na wskazaniu: kWh i wielokrotności); wymogi dla pomiaru czasu nie występują
  w jego tekście — status prawny opłat za minuty **[do weryfikacji]**. Trzymaj je osobno od energii (HB44 też każe
  oddzielić opłaty czasowe od energii).
- Rozliczenie za czas lub zmiana ceny w trakcie sesji wymaga zaufanego czasu: `TM` ze stanem `S` (albo `R`). Stan
  `U` i `I` oznacza, że czasu z licznika nie użyjesz do taryfy czasowej; taryfa za sam kWh nadal możliwa, jeśli `EF`
  nie zawiera `E`.
- Zmiany taryfy oznaczaj odczytem `TX=T`; spec OCMF wspomina praktykę zmian na pełnych kwadransach (15 min,
  `ClockAlignedDataInterval=900`). Utrata zasilania przy rozliczeniu czasowym jest zdarzeniem błędu licznika.
- Wyliczenie ceny: dom-ev-tariffs-pricing (`ocpi_tariff_calc.py`); tu wchodzi tylko energia z rejestru.

## Straty kabla (LC, CL)
- MID: licznik mierzy w punkcie przekazania (transfer point); kabel z wtykiem między licznikiem a pojazdem jest albo
  nierozłączny i plombowany, albo wymienny z oznaczeniem i osobną plombą (zał. Va pkt 4).
- OCMF: `LC` niesie rezystancję kabla (`LR`, `LU` w `mOhm` albo `uOhm`; opcjonalnie `LN`, `LI`), `CL` skumulowaną
  stratę w jednostce `RV`. Software **nie dolicza** strat do `RV` — kompensuje je licznik, a `CL` jest tylko dowodem.
- Wymiana kabla bez zgłoszenia zmienia rezystancję i unieważnia założenia podpisu: zdarzenie w rejestrze assetów.

## Legalizacja jako zdarzenie w rejestrze assetów
| Pole zdarzenia | Treść |
|---|---|
| asset | licznik (numer seryjny `MS`), ładowarka, kabel |
| zdarzenie | uruchomienie, legalizacja, wymiana licznika/kabla, zerwanie plomby, zmiana firmware metrologicznego |
| dane | data, ważność do, numer certyfikatu/oceny, numer plomby, wersja `FV`/`CF` |
| przypomnienie | z wyprzedzeniem ustalonym w umowie serwisowej [założenie]; okres w PL **[do weryfikacji]** |
| skutek | po terminie: blokada rozliczenia za kWh albo ostrzeżenie — decyzja prawna, nie techniczna |

Karta ładowarki z danymi licznika: dom-ev-charger-hardware; wprowadzanie nowego modelu: dom-ev-charger-onboarding.

## Rozjazd kWh: licznik a CSMS
Źródło prawdy rozliczeniowej to rejestr licznika podpisany (koniec − początek). `meterStop − meterStart` z OCPP 1.6
jest w **Wh** i bywa liczone z innego rejestru; `MeterValues` to telemetria. Oceniaj różnicę względem klasy
dokładności i MMQ licznika, a nie „zero”. Przebieg diagnozy z ramek: dom-ev-diagnostics (`meter-decrease`, Wh vs kWh).

## Przykład
Skrócony rekord DC z dwoma odczytami, bez błędów (podpis w przykładzie jest atrapą):

```
OCMF|{"FV":"1.4","PG":"T12","MS":"A123","IS":true,"IT":"ISO14443","ID":"04AB12",
"RD":[{"TM":"2026-10-20T08:00:00,000+0200 S","TX":"B","RV":1250.30,"RI":"1-b:1.8.0","RU":"kWh","RT":"DC","ST":"G"},
{"TM":"2026-10-20T08:45:12,000+0200 S","TX":"E","RV":1272.55,"ST":"G"}]}|{"SA":"ECDSA-secp256r1-SHA256","SD":"3045022100ab"}
```

Wynik uruchomienia (kod wyjścia 0):

```
  rejestr 1-b:1.8.0: 22.25 kWh (2 odczytów)
  ⚠ [signature-not-verified] podpis nie był weryfikowany — potrzebny klucz publiczny licznika i narzędzie ECDSA
✓ struktura poprawna
```

Ten sam rekord z następną transakcją (`PG` T13), której drugi odczyt ma `"TX":"C"`, `"EF":"E"` i czas `U`:

```
  rejestr 1-b:1.8.0: 8.55 kWh (2 odczytów)
  ✗ [error-flag] RD[1]: EF zawiera E — energia z tego odczytu nie nadaje się do rozliczenia
  ✗ [transaction] RD[1]: rejestr 1-b:1.8.0: brak odczytu końcowego (TX E, L, R, A albo P)
  ⚠ [time-unsynchronized] RD[1]: czas licznika niesynchronizowany (U) — nie nadaje się do taryfy czasowej
✗ błędów: 2
```

Wniosek: pierwszy rekord ma 22,25 kWh do rozliczenia po weryfikacji podpisu; drugiego nie rozliczasz (brak odczytu
końcowego i `EF=E`), tylko zgłaszasz do serwisu i do procedury sporu.

## Pułapki
- Rozliczenie z `meterStop − meterStart`, gdy jest rekord podpisany: dwa różne rejestry, spór o kWh murowany.
- Parser JSON zmienia zapis `1250.30` na `1250.3` albo `1.2503e3`: zmiana długości zapisu zmienia liczbę cyfr
  znaczących. Parsuj liczby jako `Decimal`, surowy tekst zachowaj.
- Zaokrąglanie, konwersja Wh↔kWh albo przepisywanie podpisanej części przed zapisem; przeliczasz tylko w kopii.
- Uznanie za poprawny rekordu, który przeszedł skrypt: brak weryfikacji podpisu i klucza.
- Klucz publiczny licznika brany z samego rekordu: przychodzi osobną drogą (rejestr), inaczej podpis niczego nie dowodzi.
- Czas z licznika `U`/`I` użyty do taryfy czasowej.
- Brak odczytu końcowego po resecie lub utracie zasilania: transakcja `A`/`P` nie jest dowodem pełnej energii.
- Aplikacja pokazuje własne kWh z telemetrii, nie wynik licznika: w UE wynik ma być powiązany z przyrządem
  (zał. I pkt 10.6 w zmianie 2026/706).

## Checklista
- [ ] Reżim (UE, DE, USA, PL) i granica z dom-ev-regulations-eu / dom-ev-regulations-us ustalone
- [ ] Surowy rekord OCMF zapisany z sesją, bez zmian; kopia robocza osobno
- [ ] `ocmf_check.py` uruchomiony; kod 0 nie uznany za weryfikację podpisu
- [ ] Podpis zweryfikowany osobnym narzędziem, klucz z rejestru **[do weryfikacji]**
- [ ] `ST=G`, brak `EF`, pierwszy `TX=B`, ostatni koniec, `PG` bez luk
- [ ] Stan czasu `S`/`R`, jeśli jest taryfa czasowa
- [ ] `signed_data` w CDR zgodne z rekordem (energia End − Start = `total_energy`)
- [ ] Terminy legalizacji, wymiany kabla i firmware w rejestrze assetów
- [ ] Fakty bez źródła w bazie oznaczone **[do weryfikacji]**

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/ocmf-pola.md` | potrzebujesz tabel pól, wartości `TX`, `ST`, stanu czasu, algorytmów i dziedziczenia |
| `references/mid-mi-011.md` | trzeba parametrów MI-011 (klasy, MMQ, BMPE), terminów 2026/706 i wymogów zał. I pkt 10.6 |
| `references/rejestr-i-sprawy-otwarte.md` | budujesz rejestr legalizacji albo porządkujesz listę faktów do weryfikacji |

## Źródła
- `ocmf`: OCMF-en.md, github.com/SAFE-eV/OCMF-Open-Charge-Metering-Format, pobrane 2026-10-20 (format 1.4.0; ranga P).
- `eu-mid-2026-706`: dyrektywa (UE) 2026/706, EUR-Lex, OJ L 20.3.2026, pobrane 2026-10-20.
- `eu-mid`: MID 2014/32/UE, art. 1–4 i zał. I, wklejone 2026-10-20 (zał. V poza bazą).
- `us-nist-hb44`: NIST Handbook 44 (2026), sekcja 3.40, pobrane 2026-10-20.
- `ocpi-2.2.1-d2`: modules/cdrs, klasy SignedData i SignedValue, pobrane 2026-10-20.
- `ocpp-json-schemas`: v16 MeterValues i StopTransaction, v201 MeterValuesRequest i TransactionEventRequest (SignedMeterValueType), github.com/mobilityhouse/ocpp, pobrane 2026-10-20.
