---
name: fw-aspnet-core
description: Użyj przy ASP.NET Core na .NET 8–10 — Minimal API, TypedResults, ProblemDetails, walidacja, OpenAPI, DI, testy z WebApplicationFactory.
metadata:
  przeglad: 2027-01-23
  katalog: "Użyj przy budowie i przeglądzie usług HTTP w ASP.NET Core (.NET 8–10) — Minimal API i grupy tras, wyniki typowane (TypedResults, Results<…>), błędy jako ProblemDetails (application/problem+json), walidacja żądań (AddValidation w .NET 10), dokument OpenAPI (AddOpenApi/MapOpenApi od .NET 9), wstrzykiwanie zależności i czasy życia, konfiguracja i opcje, mapowanie wyniku domeny na HTTP, testy integracyjne z WebApplicationFactory, różnice między wersjami. Nie do składni i idiomów C# (lang-csharp), projektu API niezależnie od technologii (be-api-design), uwierzytelniania i autoryzacji jako tematu (be-auth-security), bazy danych (be-database) ani wdrożenia (ops-*)."
  slowa: "ASP.NET Core, aspnetcore, Minimal API, minimal api, MapGet, MapPost, MapGroup, TypedResults, Results<>, ProblemDetails, problem+json, AddProblemDetails, walidacja w ASP.NET, AddValidation, OpenAPI w .NET, AddOpenApi, MapOpenApi, Swagger, WebApplicationFactory, test integracyjny ASP.NET, Mvc.Testing, kontrolery czy minimal api, DI scoped singleton, IOptions, appsettings, Kestrel"
---

# ASP.NET Core

## Procedura
1. **Wersja platformy** z `TargetFramework` (tabela niżej) — od niej zależy dostępność walidacji i OpenAPI.
2. **Endpointy**: Minimal API z `MapGroup` dla zasobu (kontrolery tylko, gdy projekt już ich używa); handler jako
   metoda statyczna lub klasa, parametry wiązane jawnie (trasa, treść, usługi).
3. **Wynik typowany**: handler zwraca `Results<Ok<T>, NotFound, ProblemHttpResult>` — kompilator pilnuje zestawu
   odpowiedzi, a OpenAPI je opisuje. Wynik domeny (lang-csharp) mapujesz na HTTP w handlerze, nie w domenie.
4. **Błędy**: `AddProblemDetails()` + `UseExceptionHandler()` + `UseStatusCodePages()`; odrzucenie biznesowe →
   `TypedResults.Problem(title, detail, statusCode)`. Uwaga: `TypedResults.Conflict(new ProblemDetails {…})`
   wysyła zwykły `application/json`, nie `application/problem+json` (sprawdzone testem).
5. **Walidacja** (.NET 10): `AddValidation()` i atrybuty `System.ComponentModel.DataAnnotations` na typach
   żądań (także na parametrach rekordu) → 400 z `ValidationProblem` bez kodu w handlerze. Na .NET 8–9: walidacja
   ręczna w handlerze albo filtr endpointu. Reguły biznesowe zostają w domenie.
6. **OpenAPI** (.NET 9+): pakiet `Microsoft.AspNetCore.OpenApi`, `AddOpenApi()` i `MapOpenApi()` →
   `/openapi/v1.json`; nazwy operacji `WithName`. Na .NET 8: Swashbuckle albo NSwag.
7. **Zależności**: czasy życia — `Singleton` bez stanu na żądanie, `Scoped` dla jednostki pracy (np. `DbContext`),
   nigdy `Scoped` wstrzykiwany do `Singleton`; czas przez `TimeProvider`; konfiguracja przez `IOptions<T>`
   z walidacją przy starcie (`ValidateOnStart`), sekrety ze zmiennych środowiskowych lub magazynu sekretów.
8. **Testy integracyjne**: `Microsoft.AspNetCore.Mvc.Testing`, `WebApplicationFactory<Program>` jako
   `IClassFixture`, `CreateClient()`; podmiana usług przez `WithWebHostBuilder(b => b.ConfigureServices(…))`.
   Na .NET 10 test widzi `Program` z instrukcji najwyższego poziomu bez dopisywania `public partial class Program`
   (sprawdzone 2026-10-23); na starszych dopisz tę linię.

## Przykład
`POST /resources/{id}/block` z `BlockRequest([Required, StringLength(50, MinimumLength = 2)] string By)`:
200 z `BlockResponse`, 404 dla nieznanego zasobu, 409 jako `application/problem+json` dla „zajęte przez jan”
i „wyłączony”, 400 z walidacji dla `By = "a"`, operacja `BlockResource` w `/openapi/v1.json`. Kod i 4 testy
integracyjne: `references/minimal-api.md`.

## Zależne od wersji
Progi sprawdzone kompilacją 2026-10-23 (net8.0 i net10.0 z SDK; net9.0 z pakietami referencyjnymi z NuGet).
| Wersja | Zmiany istotne dla tego skilla |
|---|---|
| .NET 8 (LTS) | Minimal API z `TypedResults` i `Results<…>`, `AddProblemDetails`; brak `AddOpenApi` i `AddValidation` |
| .NET 9 | wbudowany dokument OpenAPI: `AddOpenApi`, `MapOpenApi`; brak `AddValidation` |
| .NET 10 (LTS) | walidacja w Minimal API: `AddValidation`; `Program` dostępny dla `WebApplicationFactory` bez deklaracji częściowej |
.NET 11 — wydanie planowane na listopad 2026 [niezweryfikowane]; projekt na .NET 11 → `SKILL_OUTDATED`
(core-stack-sync).

## Pojęcia domenowe w aspnet-core
<!-- Kontrakt: każde pojęcie ze słownika → idiom tej technologii. Sprawdzane przez `build.py check`. -->
| Pojęcie (słownik) | Idiom |
|---|---|
| **obiekt wartości** | typ domeny (lang-csharp); w żądaniu i odpowiedzi osobny `record` DTO mapowany na granicy |
| **encja** | klasa domeny; przez API wystawiasz DTO, nie encję (ani encję EF Core) |
| **agregat** | ładowany z repozytorium w handlerze, jedna metoda biznesowa na żądanie, zapis z oczekiwaną wersją → 409 przy konflikcie współbieżności |
| **warianty** | wynik domeny mapowany w handlerze `switch` na `Results<…>` |
| **wynik operacji** | `Results<Ok<T>, NotFound, ProblemHttpResult>`; odrzucenie → `TypedResults.Problem(statusCode: 409)` |
| **zdarzenie** | zbierane z agregatu (`PullEvents`) i zapisywane w outboxie w tej samej transakcji (be-messaging-outbox) |
| **polityka** | usługa w DI wstrzykiwana do handlera lub fabryki agregatu |
| **repozytorium** | adapter portu zarejestrowany w DI (`Scoped` przy EF Core), wstrzykiwany do handlera |
| **read model** | osobny endpoint `GET` z zapytaniem omijającym agregat (projekcja, `AsNoTracking`) |
| **maszyna stanów** | przejścia w domenie; endpoint wywołuje metodę przejścia, niedozwolone przejście → 409 jako ProblemDetails |
| **moduł** | grupa tras (`MapGroup`) i metoda rozszerzająca rejestrująca usługi modułu (`AddBooking()`) |

## Źródła
- Microsoft Learn: Minimal APIs, „Handle errors in ASP.NET Core APIs”, „Generate OpenAPI documents”, „What's new in
  ASP.NET Core 9.0/10.0”, „Integration tests in ASP.NET Core” (dostęp 2026-10-23; zachowanie sprawdzone na
  przykładzie z `references/minimal-api.md`).
- RFC 9457 „Problem Details for HTTP APIs”.
Opisane własnymi słowami.
