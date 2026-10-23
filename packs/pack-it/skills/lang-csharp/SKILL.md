---
name: lang-csharp
description: Użyj przy kodzie C# 12–14 (.NET 8–10) — konwencje, nullable, rekordy, wynik operacji, async, pojęcia domenowe (obiekt wartości, warianty, agregat).
metadata:
  przeglad: 2027-01-23
  katalog: "Użyj przy pisaniu i przeglądzie kodu C# na .NET 8–10 (C# 12–14) — konwencje języka, typy referencyjne dopuszczające null, rekordy i niezmienność, wynik operacji zamiast wyjątków dla odrzuceń biznesowych, dopasowanie wzorców i wyczerpujące switch, async i CancellationToken, różnice między wersjami (konstruktory główne, wyrażenia kolekcji, kolekcje params, field, bloki extension, ?.=) oraz wyrażanie pojęć domenowych idiomami C#. Nie do ASP.NET Core — endpointów, walidacji, OpenAPI, testów integracyjnych (fw-aspnet-core), projektu API niezależnie od technologii (be-api-design) ani modelowania domeny (ddd-*)."
  slowa: "C#, csharp, .NET, dotnet, net8.0, net10.0, LangVersion, record, record struct, nullable, wynik operacji w C#, wyjątki czy wynik, switch expression, pattern matching, sealed, primary constructor, konstruktor główny, field keyword, extension members, blok extension, async await, CancellationToken, decimal kwota, obiekt wartości w C#, agregat w C#"
---

# C#

## Zasady języka
1. Wersję języka wyznacza platforma (`TargetFramework`): net8.0 → C# 12, net9.0 → C# 13, net10.0 → C# 14.
   Nowa składnia = podniesienie platformy; `LangVersion` wyżej niż domyślna to ryzyko (część funkcji wymaga
   wsparcia środowiska uruchomieniowego) — tylko świadomie i z testami.
2. `<Nullable>enable</Nullable>` i `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>` w każdym projekcie;
   `null` nie jest wartością domenową — brak wartości wyrażasz typem (`T?` na granicy, warianty w domenie).
3. Niezmienność: `record` / `readonly record struct` dla wartości, `init` zamiast `set`, kolekcje wystawiane jako
   `IReadOnlyList<T>`.
4. Pieniądze: `decimal` z jawną walutą i zaokrągleniem (`MidpointRounding`) — nigdy `double`/`float`.
5. Wyjątki dla błędów programisty i infrastruktury; **odrzucenia biznesowe** jako wynik operacji (zamknięta
   hierarchia rekordów + `switch`), mapowane na odpowiedź na granicy (fw-aspnet-core).
6. Async do końca: metody I/O `async Task`, `CancellationToken` jako ostatni parametr i przekazywany dalej;
   bez `.Result`/`.Wait()` (zakleszczenia, blokowanie wątków puli).
7. Identyfikatory jako typy (`readonly record struct ResourceId(Guid Value)`), nie goły `Guid`/`string`.
8. Granice modułów: `internal` domyślnie, publiczne tylko API projektu; zależności między projektami tylko
   w jedną stronę (domena nie zna infrastruktury).

## Pojęcia domenowe w csharp
<!-- Kontrakt: każde pojęcie ze słownika → idiom tej technologii. Sprawdzane przez `build.py check`. -->
| Pojęcie (słownik) | Idiom |
|---|---|
| **obiekt wartości** | `readonly record struct` albo `record` z walidacją w konstruktorze; równość po wartości z kompilatora |
| **encja** | klasa z identyfikatorem typu (`ResourceId`) i zachowaniem; równość po identyfikatorze |
| **agregat** | `sealed class` z prywatnym stanem, metody biznesowe zamiast setterów, `Version` do blokady optymistycznej, `PullEvents()` |
| **warianty** | `abstract record` z prywatnym konstruktorem i zagnieżdżonymi `sealed record`-ami (zbiór zamknięty) + `switch` |
| **wynik operacji** | zamknięta hierarchia rekordów (`BlockResult.Blocked`, `.Conflict`, `.Disabled`) obsługiwana `switch`; wyjątki tylko dla błędów programisty |
| **zdarzenie** | `sealed record` w czasie przeszłym implementujący `IDomainEvent` |
| **polityka** | interfejs z jedną metodą albo delegat (`Func<Order, Money>`) wstrzykiwany konstruktorem |
| **repozytorium** | interfejs (port) w projekcie domeny z metodami `async` i `CancellationToken`; adapter (EF Core, Dapper) w infrastrukturze |
| **read model** | osobny `record` i zapytanie (Dapper, projekcja EF Core `AsNoTracking`) omijające agregat |
| **maszyna stanów** | stan jako warianty (`Free`, `Taken`, `Off`), przejścia w `switch` z wzorcami i strażnikami `when` |
| **moduł** | projekt (`.csproj`) lub przestrzeń nazw z `internal` domyślnie; zależności między projektami pilnują referencje i testy architektury |

Przetestowane implementacje (kwota, identyfikator, wynik operacji, stany, zdarzenie, agregat, port repozytorium,
testy xUnit): `references/domain-building-blocks.md`.

## Zależne od wersji
Każdy próg sprawdzony kompilatorem (2026-10-23, SDK 10.0.113): kod nie kompiluje się w wersji wcześniejszej,
kompiluje w podanej; domyślna wersja języka dla platformy też sprawdzona.
| Wersja | Zmiany istotne dla tego skilla |
|---|---|
| C# 12 (.NET 8, LTS) | konstruktory główne w klasach (`class P(string n)`), wyrażenia kolekcji (`int[] xs = [1, 2, 3]`), aliasy dowolnych typów |
| C# 13 (.NET 9) | kolekcje `params` (`params ReadOnlySpan<int>`, `params IEnumerable<T>`), typ `System.Threading.Lock` |
| C# 14 (.NET 10, LTS) | słowo kluczowe `field` we właściwościach, bloki `extension` (właściwości i metody rozszerzające), przypisanie warunkowe `x?.Prop = v` |
.NET 11 z C# 15 (m.in. typy unii) jest w fazie kandydata do wydania; wydanie planowane na listopad 2026
[niezweryfikowane: według Visual Studio Magazine, 14.09.2026]. Projekt na .NET 11 → `detect_stack.py` zgłosi
`SKILL_OUTDATED`, aktualizacja wg core-stack-sync.

## Przykład
Pytanie: „Reserve ma zwrócić sukces albo odrzucenie”. Wynik: `public BlockResult Block(string by, DateTimeOffset at)`
z `abstract record BlockResult { private BlockResult() {} sealed record Blocked(...); sealed record Conflict(string
BlockedBy); sealed record Disabled; }`. Wywołujący: `result switch { BlockResult.Blocked => …, BlockResult.Conflict
c => …, BlockResult.Disabled => … }`. Dodanie nowego wariantu pokazuje każde miejsce do uzupełnienia przy przeglądzie
`switch`; brak gałęzi kończy się wyjątkiem w `_ =>` (błąd programisty). Pełny kod z testem:
`references/domain-building-blocks.md`.

## Checklista
- [ ] `Nullable` włączone, ostrzeżenia jako błędy, `dotnet format --verify-no-changes`
- [ ] brak `double` dla kwot, identyfikatory jako typy
- [ ] odrzucenia biznesowe jako wynik, nie wyjątki; `switch` obsługuje każdy wariant
- [ ] `async` z `CancellationToken` do końca, bez `.Result`
- [ ] użyta składnia pasuje do `TargetFramework` (tabela wyżej)

## Źródła
- Microsoft Learn: „What's new in C# 12/13/14”, „C# language versioning” (dostęp 2026-10-23; progi sprawdzone
  kompilatorem z SDK 8.0.132 i 10.0.113, pakiety Ubuntu 24.04).
- .NET 11 RC: Visual Studio Magazine, „.NET 11 RC1 gets go-live support ahead of November launch” (14.09.2026).
Opisane własnymi słowami.
