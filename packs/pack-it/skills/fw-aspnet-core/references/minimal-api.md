# Minimal API with typed results, ProblemDetails, validation and OpenAPI — example

> **Contents:** ToolLibrary.Api.csproj · Program.cs · ToolLibrary.Api.Tests.csproj · LendToolTests.cs

One endpoint, `POST /tools/{id}/loans`, over the tool-lending domain from
`.claude/skills/lang-csharp/references/domain-building-blocks.md` (`LendableTool`, `LendResult`, `ToolId`,
`MemberId`). The handler maps the domain result to HTTP; the domain knows nothing about HTTP.

**Verification status:** checked 2026-11-20 with SDK 10.0.115 (runtime 10.0.15, Ubuntu 24.04 packages):
`dotnet test` passes all 5 integration tests, the build has 0 warnings with `TreatWarningsAsErrors`, and
`dotnet format --verify-no-changes` is clean. Packages: `Microsoft.AspNetCore.OpenApi` and
`Microsoft.AspNetCore.Mvc.Testing` 10.0.13.

What it shows:
- `Results<Ok<LoanResponse>, NotFound, ProblemHttpResult>` as the handler's return type: the set of responses is
  checked by the compiler and described in OpenAPI;
- business refusals (`OnLoan`, `Withdrawn`) as `409` with `application/problem+json`, an unknown tool as `404`;
- validation (.NET 10 `AddValidation()`) with DataAnnotations on a record parameter → `400` before the handler runs;
- the `LendTool` operation in `/openapi/v1.json`;
- `TimeProvider` injected instead of `DateTimeOffset.UtcNow`.

Files:
- ToolLibrary.Api.csproj — the web project referencing the domain project
- Program.cs — registration, the endpoint, request/response records, an in-memory store
- ToolLibrary.Api.Tests.csproj — the test project
- LendToolTests.cs — integration tests through `WebApplicationFactory<Program>`

## ToolLibrary.Api.csproj
```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="10.0.13" />
  </ItemGroup>
  <ItemGroup>
    <ProjectReference Include="..\ToolLibrary.Lending\ToolLibrary.Lending.csproj" />
  </ItemGroup>
</Project>
```

## Program.cs
```csharp
using System.ComponentModel.DataAnnotations;
using System.Diagnostics;
using Microsoft.AspNetCore.Http.HttpResults;
using ToolLibrary.Lending;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddProblemDetails();
builder.Services.AddValidation();
builder.Services.AddOpenApi();
builder.Services.AddSingleton(TimeProvider.System);
builder.Services.AddSingleton<IToolStore, InMemoryToolStore>();

var app = builder.Build();
app.UseExceptionHandler();
app.UseStatusCodePages();
app.MapOpenApi();

app.MapGroup("/tools")
   .MapPost("/{id}/loans", LendTool)
   .WithName("LendTool");

app.Run();

static Results<Ok<LoanResponse>, NotFound, ProblemHttpResult> LendTool(
    string id, LoanRequest request, IToolStore store, TimeProvider clock)
{
    var tool = store.Find(new ToolId(id));
    if (tool is null)
    {
        return TypedResults.NotFound();
    }

    // A real store would now save the aggregate with its expected version and publish tool.PullEvents().
    return tool.Lend(new MemberId(request.MemberId), clock.GetUtcNow()) switch
    {
        LendResult.Lent lent => TypedResults.Ok(new LoanResponse(id, lent.Event.Borrower.Value, lent.Event.At)),
        LendResult.OnLoan onLoan => TypedResults.Problem(
            title: "Tool on loan",
            detail: $"The tool is lent to {onLoan.Borrower}.",
            statusCode: StatusCodes.Status409Conflict),
        LendResult.Withdrawn => TypedResults.Problem(
            title: "Tool withdrawn",
            statusCode: StatusCodes.Status409Conflict),
        _ => throw new UnreachableException(),
    };
}

public sealed record LoanRequest([Required, RegularExpression(@"^[msc]-\d{4}$")] string MemberId);

public sealed record LoanResponse(string ToolId, string Borrower, DateTimeOffset Since);

public interface IToolStore
{
    LendableTool? Find(ToolId id);
}

/// <summary>Demo only: a singleton with a plain dictionary, no locking, no persistence.</summary>
public sealed class InMemoryToolStore : IToolStore
{
    private readonly Dictionary<ToolId, LendableTool> _tools = [];

    public InMemoryToolStore()
    {
        var drill = new LendableTool(new ToolId("T-100"));
        var welder = new LendableTool(new ToolId("T-900"));
        welder.Withdraw(new MemberId("s-0001"), "failed inspection", DateTimeOffset.UnixEpoch);
        _tools[drill.Id] = drill;
        _tools[welder.Id] = welder;
    }

    public LendableTool? Find(ToolId id) => _tools.GetValueOrDefault(id);
}
```

## ToolLibrary.Api.Tests.csproj
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <IsPackable>false</IsPackable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Mvc.Testing" Version="10.0.13" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="18.12.0" />
    <PackageReference Include="xunit" Version="2.9.3" />
    <PackageReference Include="xunit.runner.visualstudio" Version="3.1.5" />
  </ItemGroup>
  <ItemGroup>
    <ProjectReference Include="..\ToolLibrary.Api\ToolLibrary.Api.csproj" />
  </ItemGroup>
</Project>
```

## LendToolTests.cs
The tests share one `WebApplicationFactory` (and so one in-memory store): each test uses its own tool or does not
change state.

```csharp
using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

public class LendToolTests(WebApplicationFactory<Program> factory) : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task Lends_once_then_refuses_with_problem_details()
    {
        var client = factory.CreateClient();

        var first = await client.PostAsJsonAsync("/tools/T-100/loans", new { memberId = "m-0042" });
        Assert.Equal(HttpStatusCode.OK, first.StatusCode);

        var second = await client.PostAsJsonAsync("/tools/T-100/loans", new { memberId = "m-0107" });
        Assert.Equal(HttpStatusCode.Conflict, second.StatusCode);
        Assert.Equal("application/problem+json", second.Content.Headers.ContentType?.MediaType);
        Assert.Contains("m-0042", await second.Content.ReadAsStringAsync());
    }

    [Fact]
    public async Task Withdrawn_tool_is_a_conflict()
    {
        var response = await factory.CreateClient()
            .PostAsJsonAsync("/tools/T-900/loans", new { memberId = "m-0042" });

        Assert.Equal(HttpStatusCode.Conflict, response.StatusCode);
        Assert.Contains("Tool withdrawn", await response.Content.ReadAsStringAsync());
    }

    [Fact]
    public async Task Unknown_tool_is_not_found()
    {
        var response = await factory.CreateClient()
            .PostAsJsonAsync("/tools/T-404/loans", new { memberId = "m-0042" });

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task Invalid_member_id_is_rejected_by_validation()
    {
        var response = await factory.CreateClient()
            .PostAsJsonAsync("/tools/T-100/loans", new { memberId = "x" });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.Equal("application/problem+json", response.Content.Headers.ContentType?.MediaType);
    }

    [Fact]
    public async Task OpenApi_document_lists_the_operation()
    {
        var document = await factory.CreateClient().GetStringAsync("/openapi/v1.json");

        Assert.Contains("LendTool", document);
    }
}
```
