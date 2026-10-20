# OCMF: pola, wartości, dziedziczenie

Spis treści: 1. Układ rekordu · 2. Payload · 3. Odczyt (RD) · 4. Wartości tabel · 5. Podpis · 6. Klucz i numer seryjny · 7. Rozszerzenia.

Źródło: `ocmf`, OCMF-en.md (format 1.4.0), pobrane 2026-10-20; zakresy linii w `.claude/knowledge/ocmf/doc.txt`.
Opis własnymi słowami; nazwy pól w oryginale.

## 1. Układ rekordu
`OCMF|<payload JSON>|<podpis JSON>` (L233-250). Nagłówek to literały `OCMF`. Podpis obejmuje payload; kilka
podpisów można dołączać niezależnie (L32, wersja 1.0).

## 2. Payload (L251-342)
| Pole | Znaczenie | Uwaga |
|---|---|---|
| `FV` | wersja formatu `<major>.<minor>` | opcjonalne |
| `GI`, `GS`, `GV` | bramka (system podpisujący): identyfikacja, numer seryjny, wersja | `GS` warunkowo obowiązkowe |
| `PG` | paginacja: `T<n>` transakcja (obowiązkowa), `F<n>` fiskalna (opcjonalna) | osobny licznik na kontekst, bez zer wiodących, +1 |
| `MV`, `MM`, `MS`, `MF` | licznik: producent, model, numer seryjny, firmware | numer seryjny licznika lub bramki wystarcza do identyfikacji |
| `IS`, `IL`, `IF`, `IT`, `ID`, `TT` | przypisanie użytkownika: status (boolean), poziom, flagi, typ, dane, tekst taryfy | tylko przy odniesieniu do transakcji; `IS` i `IT` obowiązkowe |
| `CF`, `LC` | firmware sterownika ładowania; kompensacja strat kabla | `CF` bywa wymagane przez jednostki notyfikowane |
| `CT`, `CI` | typ i identyfikator punktu ładowania (`EVSEID`, `CBIDC`) | opcjonalnie, alternatywa dla numerów seryjnych |
| `RD` | tablica odczytów | co najmniej jeden |

## 3. Odczyt `RD[]` (L343-372)
- Pole o takiej samej wartości jak w poprzednim odczycie **tego samego rekordu** się pomija (np. `RI`, `RU`, `RT`,
  `ST`, `EF`); `TX` może być w pierwszym `B`, w drugim `C`, w ostatnim `E` — odczyty pośrednie dziedziczą `C`.
- `RI` i `RU` tworzą grupę (razem albo wcale). `RV`, `RI`, `RU`, `RT` można pominąć, gdy odczyt zgłasza tylko zdarzenie
  licznika (błąd). Utrata zasilania przy rozliczeniu czasowym jest zdarzeniem błędu.
- `RV` to JSON Number i jego zapis nie może się zmieniać po drodze (wykładnik, obcięcie miejsc) — spec zaleca dla kWh
  dwa miejsca dziesiętne.
- `CL`: tylko przy rejestrze akumulującym; zerowane przy `TX=B`; w jednostce `RV`.

| Pole | Znaczenie |
|---|---|
| `TM` | `RRRR-MM-DDThh:mm:ss,mmm±hhmm` plus spacja i stan czasu |
| `TX` | powód odczytu (tabela niżej); brak pola = pomiar fiskalny (bez transakcji) |
| `RV`, `RI`, `RU`, `RT` | wartość, rejestr (kod OBIS), jednostka, rodzaj prądu (`AC`, `DC`) |
| `CL`, `EF`, `ST` | skumulowana strata, flagi błędów (`E`, `t`), stan licznika |

## 4. Wartości tabel
| `TX` | Znaczenie |
|---|---|
| `B` | początek transakcji |
| `C` | w trakcie ładowania (opcjonalnie) |
| `X` | wyjątek: błąd w trakcie, transakcja trwa, czas i/lub energia od tego odczytu (włącznie) nieużyteczne |
| `E` | koniec; dokładniej `L` lokalnie, `R` zdalnie, `A` przerwane błędem, `P` brak zasilania |
| `S` | zawieszona (aktywna, nie ładuje; opcjonalnie) |
| `T` | zmiana taryfy |

| `ST` (L570-588) | Znaczenie | | `TM` stan (L716-726) | Znaczenie |
|---|---|---|---|---|
| `G` | OK | | `S` | zsynchronizowany |
| `N`, `T`, `D`, `R` | brak licznika, timeout, odłączony, zniknął | | `I` | informacyjny (zegar informacyjny) |
| `M` | wykryta manipulacja | | `U` | nieznany, niezsynchronizowany |
| `X` | licznik wymieniony (numer seryjny inny niż ostatni) | | `R` | względny: czas liczony zgodnie z legalizacją na bazie zegara informacyjnego |
| `I`, `O`, `S`, `E`, `F` | niezgodny, poza zakresem, wartość zastępcza, inny błąd, błąd odczytu | | | |

`EF`: `E` energia, `t` czas — wielkości, których nie wolno użyć do rozliczenia. Jednostki: `kWh`, `Wh`, `mOhm`, `uOhm`.

## 5. Podpis (L390-427, L747-778)
| Pole | Znaczenie |
|---|---|
| `SA` | algorytm; domyślnie `ECDSA-secp256r1-SHA256` (domyślny od wersji 0.4). Inne: secp192k1, secp256k1, secp192r1, brainpool256r1, secp384r1, brainpool384r1 (z SHA-256) |
| `SE` | kodowanie `SD`: `hex` (domyślne) albo `base64` |
| `SM` | typ MIME: domyślnie `application/x-der` (struktura ASN.1 DER) |
| `SD` | dane podpisu (obowiązkowe) |

## 6. Klucz publiczny i numer seryjny (L428-447)
Klucz publiczny przekazuje się do weryfikatora **poza protokołem**, powiązany z numerem seryjnym licznika lub bramki
(np. centralny rejestr). Gdy bramka obsługuje kilka punktów, tożsamość to para: numer seryjny bramki i licznika.

## 7. Rozszerzenia
- W payloadzie nazwy najwyższego poziomu na `U`–`Z` są dla producenta; w sekcji podpisu `U`–`Z` dla producenta,
  a litery `A`–`F` zarezerwowane dla dalszego przetwarzania (L390-427).
- Kody OBIS wersji 1.4 odróżniają energię sieci (Mains), urządzenia (Device) i transakcji (Transaction) w imporcie
  i eksporcie (L812+). Sprawdź, który rejestr trafia do `total_energy` w CDR.
- Zalecane klucze OCPP: `StopTransactionSignatureFormat` (MR, SR), `StopTransactionSignatureContexts`,
  `MeterValuesSignatureContexts` (L793-811).
