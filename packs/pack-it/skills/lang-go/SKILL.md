---
name: lang-go
description: Użyj przy kodzie Go 1.22–1.27 — konwencje, błędy (errors.Is/As), współbieżność, pojęcia domenowe (obiekt wartości, warianty, agregat).
metadata:
  przeglad: 2027-01-23
  katalog: "Użyj przy pisaniu i przeglądzie kodu Go (1.22–1.27) — konwencje języka, obsługa błędów (błędy wartownicze, typy błędów, opakowanie %w, errors.Is i errors.As), interfejsy po stronie użytkownika, współbieżność z kontekstem i limitami, testy tabelaryczne, różnice między wersjami (iteratory, WaitGroup.Go, new z wyrażeniem, metody generyczne) oraz wyrażanie pojęć domenowych idiomami Go (obiekt wartości, warianty, agregat, wynik operacji, zdarzenia, port repozytorium). Nie do projektu API HTTP (be-api-design), konteneryzacji (ops-docker) ani modelowania domeny (ddd-*)."
  slowa: "Go, golang, go.mod, błędy w Go, errors.Is, errors.As, wrap %w, sentinel error, wynik operacji w Go, interfejs w Go, gorutyny, context, WaitGroup, kanały, iteratory, range po funkcji, metody generyczne, testy tabelaryczne, kwota w Go, obiekt wartości w Go, agregat w Go, Go 1.27"
---

# Go

## Zasady języka
1. Wersja języka modułu to dyrektywa `go` w `go.mod` — nowej funkcji używasz dopiero po podniesieniu tej
   dyrektywy (`go mod edit -go=1.27`); `toolchain` mówi tylko, czym budować. Wersje w CI i lokalnie te same.
2. Błędy to wartości: zwracasz `error` jako ostatni wynik. Odrzucenia biznesowe — błędy wartownicze
   (`var ErrSlotTaken = errors.New(...)`) albo typy błędów ze szczegółami; opakowujesz `fmt.Errorf("...: %w", err)`,
   sprawdzasz `errors.Is` / `errors.As`, nigdy porównaniem tekstu. `panic` tylko dla błędów programisty.
3. Interfejsy małe i definiowane tam, gdzie się ich **używa** (port w pakiecie domeny), nie przy implementacji;
   funkcje przyjmują interfejsy, zwracają konkretne typy.
4. Pieniądze: `int64` w jednostkach minimalnych (grosze) z walutą w typie albo biblioteka dziesiętna — nigdy
   `float64`.
5. Typy nazwane zamiast gołych `string`/`int` dla identyfikatorów i jednostek; konstruktor `NewX(...) (X, error)`
   pilnuje poprawności, pola nieeksportowane.
6. Współbieżność: każda gorutyna ma właściciela i sposób zakończenia (`context.Context` jako pierwszy parametr,
   limit czasu); `errgroup` lub `sync.WaitGroup` zamiast „wystrzel i zapomnij”; dane współdzielone za muteksem
   albo przekazywane kanałem. Testy z `-race` w CI.
7. Pakiety według odpowiedzialności (domena, adapter), nie warstwy technicznej; `internal/` dla tego, czego nie
   wolno importować spoza modułu. Bez cykli importu (kompilator ich zabrania).
8. Kod formatuje `gofmt`, sprawdza `go vet`; testy tabelaryczne z `t.Run`.

## Pojęcia domenowe w Go
| Pojęcie (słownik) | Idiom w Go |
|---|---|
| **obiekt wartości** | struktura z polami nieeksportowanymi, konstruktor z walidacją, metody na wartości zwracające nową wartość; porównywalna `==` |
| **encja** | struktura z identyfikatorem typu nazwanego (`type CustomerID string`) i zachowaniem; równość po identyfikatorze |
| **agregat** | wskaźnik na strukturę z prywatnym stanem, metody biznesowe zamiast setterów, `version` do blokady optymistycznej, `PullEvents()` |
| **warianty** | interfejs z metodą nieeksportowaną (zbiór zamknięty w pakiecie) + `switch v := x.(type)`; `default` z `panic` dla nieobsłużonego wariantu |
| **wynik operacji** | `(T, error)`; odrzucenia jako błędy wartownicze lub typy błędów z `Unwrap`, rozróżniane `errors.Is` / `errors.As` |
| **zdarzenie** | struktura w czasie przeszłym (`ResourceBlocked`) implementująca interfejs zdarzeń modułu |
| **polityka** | interfejs z jedną metodą albo typ funkcji (`type DiscountPolicy func(Order) Money`) wstrzykiwany konstruktorem |
| **repozytorium** | interfejs (port) w pakiecie domeny operujący na agregatach; adapter SQL w pakiecie infrastruktury |
| **read model** | osobna struktura i zapytanie SQL omijające agregat |
| **maszyna stanów** | stan jako warianty (`Free`, `Blocked`, `Disabled`), przejścia w `switch` po typie w metodzie agregatu |
| **moduł** | pakiet z małym eksportowanym API, reszta nieeksportowana; `internal/` dla granic |

Przetestowane implementacje (kwota, identyfikator, błędy odrzucenia, warianty stanu, agregat ze zdarzeniami, port
repozytorium, testy tabelaryczne): `references/domain-building-blocks.md`.

## Zależne od wersji
Każdy próg sprawdzony kompilatorem (2026-10-23): kod nie kompiluje się w wersji wcześniejszej, kompiluje w podanej.
| Wersja | Zmiany istotne dla tego skilla |
|---|---|
| 1.22 | zmienna pętli `for` nowa w każdej iteracji; `for i := range n`; wzorce w `http.ServeMux` (metoda, `{id}`, `r.PathValue`) |
| 1.23 | iteratory: `range` po funkcji, pakiet `iter` (`iter.Seq`, `iter.Seq2`) |
| 1.24 | `os.Root` (dostęp do plików ograniczony do katalogu), `testing.B.Loop` w benchmarkach |
| 1.25 | `sync.WaitGroup.Go`; pakiet `testing/synctest` (testy kodu z czasem i gorutynami) |
| 1.26 | `new` z wyrażeniem: `p := new(42)` |
| 1.27 | metody generyczne — metoda może mieć własne parametry typu: `func (b Box[T]) Map[U any](f func(T) U) Box[U]` |
Projekt z dyrektywą starszą niż 1.22 → `detect_stack.py` zgłosi `PROJECT_OLDER`: stosuj tylko to, co działa w tej
wersji. Nowsza niż 1.27 → `SKILL_OUTDATED`, aktualizacja wg core-stack-sync.

## Przykład
Pytanie: „Reserve ma zwrócić sukces albo odrzucenie (termin zajęty, zasób wyłączony)”. Wynik:
`func (r *ResourceAvailability) Block(by string, at time.Time) error` — `nil` to sukces; `ErrDisabled`
(błąd wartowniczy); `*ConflictError{BlockedBy: "jan"}` z `Unwrap() error { return ErrSlotTaken }`. Wywołujący:
`errors.Is(err, ErrSlotTaken)` → 409, `errors.As(err, &ce)` → komunikat z `ce.BlockedBy`, inny błąd → 500.
Pełny kod z testem: `references/domain-building-blocks.md`.

## Checklista
- [ ] `gofmt -l` pusty, `go vet ./...` bez uwag, `go test -race ./...` w CI
- [ ] brak `float64` dla kwot, identyfikatory jako typy nazwane
- [ ] odrzucenia jako błędy rozróżniane `errors.Is`/`errors.As`, bez porównywania tekstu błędu
- [ ] każda gorutyna z `context` i sposobem zakończenia
- [ ] dyrektywa `go` w `go.mod` pozwala na użyte funkcje języka

## Źródła
- Specyfikacja języka i notatki wydań: go.dev/ref/spec, go.dev/doc/go1.22 … go1.27 (go.dev niedostępne z sesji
  2026-10-23; wersje i progi sprawdzone kompilatorami go1.21.0–go1.27.3 z proxy.golang.org).
- „Effective Go”, „Go Code Review Comments” (go.dev/wiki), pakiet `errors` (`Is`, `As`, `%w`).
Opisane własnymi słowami.
