# Szablon teczki systemu legacy

Spis treści: 1. Indeks `README.md` · 2. Karta modułu `modules/<moduł>.md` · 3. Skąd brać reguły biznesowe ·
4. Kontrakt dla `dossier_check.py`

## 1. Indeks `README.md`

```markdown
<!-- legacy-dossier -->
# Teczka systemu: <nazwa>
System: <nazwa> · Commit: <HEAD> · Data: <RRRR-MM-DD>

## TL;DR
<5–7 zdań: co system robi dla biznesu, z ilu modułów się składa, gdzie jest rdzeń, największe ryzyko zmiany,
ile reguł „do weryfikacji”.>

## Moduły
| Moduł | Po co | Stan |
|---|---|---|
| [faktury](modules/faktury.md) | wystawianie faktur i korekt | żółty |

## Przepływy
### Wystawienie faktury
1. `InvoiceController.create` (src/web/InvoiceController.java:40) przyjmuje zamówienie …
(diagram sekwencji Mermaid)

## Słownik
| W kodzie | W biznesie | Uwaga |
|---|---|---|
| `Doc` | faktura | także korekta (`type = 'K'`) |

## Stan i kandydaci do refaktoru
| Moduł | Stan | Kandydat | Dlaczego (dowód) |
|---|---|---|---|
| faktury | żółty | jedno miejsce zaokrągleń | R-FAK-01 vs R-FAK-02 |

## Pytania otwarte
- <pytanie> — kogo zapytać (obszar, nie ocena osoby)

## Ograniczenia
<czego teczka nie obejmuje: moduły pominięte, brak dostępu do bazy produkcyjnej, kod generowany>

## Przekazanie
<dla eng-tech-debt-audit / eng-refactor-planning: od których kandydatów zacząć>
```

## 2. Karta modułu `modules/<moduł>.md`

```markdown
<!-- legacy-dossier:module -->
# Moduł: <nazwa>
Stan: zielony|żółty|czerwony — <powód jednym zdaniem>

## Po co
## Odpowiedzialności
## Wejścia i wyjścia
## Reguły biznesowe
| ID | Reguła | Dowód | Pewność |
|---|---|---|---|
| R-<MOD>-01 | <zdanie dla biznesu> | ścieżka/Plik.java:42 | test|kod|do weryfikacji |
## Dane
## Zależności
## Pułapki
## Testy
## Pytania
```

- ID reguły unikalne w całej teczce: `R-<skrót modułu>-<numer>`.
- Dowód: ścieżka względem katalogu repozytorium, `plik:linia` albo `plik:od-do`; kilka dowodów po przecinku.
- Brak dowodu: `—` i pewność `do weryfikacji`, a pytanie trafia do sekcji Pytania.

## 3. Skąd brać reguły biznesowe

| Miejsce w kodzie | Co zwykle kryje | Przykład |
|---|---|---|
| warunki z liczbami i datami | progi, terminy, limity | `if (days > 30)` → termin płatności |
| walidacje i komunikaty błędów | warunki konieczne | `"Kwota musi być dodatnia"` |
| wyjątki domenowe | stany zabronione | `InvoiceAlreadyPaidException` |
| `WHERE` / filtry w zapytaniach | kto i co jest „aktywne” | `status <> 'ARCH' AND deleted = 0` |
| enumy i stałe | stany i przejścia | `DRAFT → ISSUED → PAID` |
| flagi i konfiguracja | warianty dla klientów lub krajów | `vat.reverse-charge.enabled` |
| nazwy testów | zachowanie potwierdzone testem | `shouldRejectCorrectionAfterPayment` |
| historia gita (`git log -S`, opisy „fix”) | reguły dodane po incydencie | „fix: korekta po zapłacie” |
| triggery i procedury w bazie | reguły poza kodem aplikacji | `BEFORE UPDATE ON invoices` |

Reguła z testu ma pewność `test`. Reguła z samego kodu — `kod`. Wniosek z nazwy, komentarza albo historii bez
potwierdzenia w kodzie — `do weryfikacji`. Gdy test i kod mówią co innego, wpisz obie wersje i pytanie.

## 4. Kontrakt dla `dossier_check.py`

- Pierwsza linia indeksu: `<!-- legacy-dossier -->`, karty: `<!-- legacy-dossier:module -->`.
- Sekcje indeksu: TL;DR, Moduły, Przepływy, Słownik, Stan i kandydaci do refaktoru, Pytania otwarte, Ograniczenia.
- Sekcje karty: Po co, Odpowiedzialności, Wejścia i wyjścia, Reguły biznesowe, Dane, Zależności, Pułapki, Testy,
  Pytania; linia `Stan: <zielony|żółty|czerwony> — <powód>`.
- Moduł z indeksu bez pliku i błędny dowód to błąd; karta spoza indeksu — ostrzeżenie.
