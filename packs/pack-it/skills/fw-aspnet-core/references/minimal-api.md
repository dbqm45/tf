# Minimal API z wynikami typowanymi, ProblemDetails, walidacją i OpenAPI — przetestowany przykład

Projekt sprawdzony 2026-10-23 na net10.0 (SDK 10.0.113, Microsoft.AspNetCore.OpenApi 10.0.13,
Microsoft.AspNetCore.Mvc.Testing 10.0.13): `dotnet test` — 4 testy integracyjne (200, 409 jako
`application/problem+json`, 400 z walidacji, 404, dokument OpenAPI), `TreatWarningsAsErrors`,
`dotnet format --verify-no-changes` bez uwag. Domena (`Booking.Domain`): lang-csharp
(`.claude/skills/lang-csharp/references/domain-building-blocks.md`). Pliki skopiowane bez zmian.

## Spis treści
- Booking.Api.csproj
- Program.cs — endpoint, mapowanie wyniku domeny na HTTP
- Booking.Api.Tests.csproj
- BlockResourceTests.cs — testy integracyjne przez WebApplicationFactory

## Booking.Api.csproj
```xml
<Project Sdk="Microsoft.NET.Sdk.Web">

  <ItemGroup>
    <ProjectReference Include="..\Booking.Domain\Booking.Domain.csproj" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="10.0.*" />
  </ItemGroup>

  <PropertyGroup>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

</Project>
```

## Program.cs
```csharp
using System.ComponentModel.DataAnnotations;
using Booking.Domain;
using Microsoft.AspNetCore.Http.HttpResults;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddProblemDetails();          // błędy jako application/problem+json (RFC 9457)
builder.Services.AddValidation();              // walidacja atrybutów w Minimal API (.NET 10)
builder.Services.AddOpenApi();                 // dokument OpenAPI (.NET 9+)
builder.Services.AddSingleton(TimeProvider.System);
builder.Services.AddSingleton<IResourceStore, InMemoryResourceStore>();

var app = builder.Build();
app.UseExceptionHandler();
app.UseStatusCodePages();
app.MapOpenApi();

app.MapGroup("/resources")
   .MapPost("/{id:guid}/block", BlockResource)
   .WithName("BlockResource");

app.Run();

// Typ wyniku wymienia każdą odpowiedź — trafia do OpenAPI i jest sprawdzany przez kompilator.
static Results<Ok<BlockResponse>, NotFound, ProblemHttpResult> BlockResource(
    Guid id, BlockRequest request, IResourceStore store, TimeProvider clock)
{
    var resource = store.Find(new ResourceId(id));
    if (resource is null)
        return TypedResults.NotFound();

    // Odrzucenie biznesowe z domeny → kod HTTP tu, na granicy; domena nie zna HTTP.
    return resource.Block(request.By, clock.GetUtcNow()) switch
    {
        BlockResult.Blocked or BlockResult.AlreadyBlockedBySameOwner => TypedResults.Ok(new BlockResponse(id, request.By)),
        // TypedResults.Problem → application/problem+json; Conflict(new ProblemDetails()) dałoby zwykły application/json.
        BlockResult.Conflict c => TypedResults.Problem(
            title: "Zasób zajęty", detail: $"Zasób zablokował {c.BlockedBy}.", statusCode: StatusCodes.Status409Conflict),
        BlockResult.Disabled => TypedResults.Problem(title: "Zasób wyłączony", statusCode: StatusCodes.Status409Conflict),
        _ => throw new InvalidOperationException("Nieobsłużony wynik."),
    };
}

public sealed record BlockRequest([Required, StringLength(50, MinimumLength = 2)] string By);

public sealed record BlockResponse(Guid ResourceId, string BlockedBy);

public interface IResourceStore
{
    ResourceAvailability? Find(ResourceId id);
}

public sealed class InMemoryResourceStore : IResourceStore
{
    public static readonly ResourceId Room1 = new(Guid.Parse("11111111-1111-1111-1111-111111111111"));
    private readonly Dictionary<ResourceId, ResourceAvailability> _items = new() { [Room1] = new ResourceAvailability(Room1) };

    public ResourceAvailability? Find(ResourceId id) => _items.GetValueOrDefault(id);
}
```

## Booking.Api.Tests.csproj
```xml
﻿<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <IsPackable>false</IsPackable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="coverlet.collector" Version="6.0.4" />
    <PackageReference Include="Microsoft.AspNetCore.Mvc.Testing" Version="10.0.*" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.14.1" />
    <PackageReference Include="xunit" Version="2.9.3" />
    <PackageReference Include="xunit.runner.visualstudio" Version="3.1.4" />
  </ItemGroup>

  <ItemGroup>
    <Using Include="Xunit" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\..\src\Booking.Api\Booking.Api.csproj" />
  </ItemGroup>

</Project>```

## BlockResourceTests.cs
```csharp
using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;

namespace Booking.Api.Tests;

public class BlockResourceTests(WebApplicationFactory<Program> factory) : IClassFixture<WebApplicationFactory<Program>>
{
    private const string Url = "/resources/11111111-1111-1111-1111-111111111111/block";

    [Fact]
    public async Task Blocks_then_returns_conflict_for_other_person()
    {
        var client = factory.CreateClient();

        var first = await client.PostAsJsonAsync(Url, new { by = "anna" });
        var second = await client.PostAsJsonAsync(Url, new { by = "jan" });

        Assert.Equal(HttpStatusCode.OK, first.StatusCode);
        Assert.Equal(HttpStatusCode.Conflict, second.StatusCode);
        Assert.Equal("application/problem+json", second.Content.Headers.ContentType?.MediaType);
    }

    [Fact]
    public async Task Invalid_request_returns_validation_problem()
    {
        var response = await factory.CreateClient().PostAsJsonAsync(Url, new { by = "a" });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.Contains("By", await response.Content.ReadAsStringAsync());
    }

    [Fact]
    public async Task Unknown_resource_returns_404()
    {
        var response = await factory.CreateClient()
            .PostAsJsonAsync("/resources/22222222-2222-2222-2222-222222222222/block", new { by = "anna" });

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task Exposes_openapi_document()
    {
        var response = await factory.CreateClient().GetAsync("/openapi/v1.json");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("BlockResource", await response.Content.ReadAsStringAsync());
    }
}
```

