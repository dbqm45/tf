# Domain building blocks in C# — tested examples

> **Contents:** Booking.Domain.csproj · Money.cs · ResourceAvailability.cs · ResourceAvailabilityTests.cs

Project checked 2026-10-23: `dotnet test` (xUnit) on net8.0 (C# 12) and net10.0 (C# 14) with
`TreatWarningsAsErrors` and `Nullable`, `dotnet format --verify-no-changes` with no findings (SDK 8.0.132 and 10.0.113).
The code uses only C# 12, so it works across the whole range of the skill. Code from the tested project; only comments and message strings were translated to English (logic unchanged).

## Contents
- Booking.Domain.csproj
- Money.cs — amount and identifier (value objects)
- ResourceAvailability.cs — operation result, states, event, aggregate, repository port
- ResourceAvailabilityTests.cs — xUnit tests, an exhaustive `switch` on the result

## Booking.Domain.csproj
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFrameworks>net8.0;net10.0</TargetFrameworks>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
```

## Money.cs
```csharp
namespace Booking.Domain;

/// <summary>Amount — a value object: decimal with an explicit currency, immutable, value equality (record struct).</summary>
public readonly record struct Money
{
    public decimal Amount { get; }
    public string Currency { get; }

    public Money(decimal amount, string currency)
    {
        if (string.IsNullOrWhiteSpace(currency) || currency.Length != 3)
            throw new ArgumentException("Currency: a three-letter ISO 4217 code.", nameof(currency));
        Amount = decimal.Round(amount, 2, MidpointRounding.ToEven);
        Currency = currency.ToUpperInvariant();
    }

    public Money Add(Money other) =>
        other.Currency == Currency
            ? new Money(Amount + other.Amount, Currency)
            : throw new InvalidOperationException($"Different currencies: {Currency} and {other.Currency}.");

    public override string ToString() => $"{Amount:0.00} {Currency}";
}

/// <summary>An identifier as a type, not a bare Guid/string.</summary>
public readonly record struct ResourceId(Guid Value)
{
    public static ResourceId New() => new(Guid.NewGuid());
}
```

## ResourceAvailability.cs
```csharp
namespace Booking.Domain;

/// <summary>Operation result: success or a business rejection — a closed hierarchy of records.</summary>
public abstract record BlockResult
{
    private BlockResult() { } // only nested variants

    public sealed record Blocked(ResourceId Resource, string By) : BlockResult;
    public sealed record AlreadyBlockedBySameOwner : BlockResult;
    public sealed record Conflict(string BlockedBy) : BlockResult;
    public sealed record Disabled : BlockResult;
}

/// <summary>State as variants (a state machine).</summary>
public abstract record AvailabilityState
{
    private AvailabilityState() { }

    public sealed record Free : AvailabilityState;
    public sealed record Taken(string By) : AvailabilityState;
    public sealed record Off : AvailabilityState;
}

public interface IDomainEvent;

public sealed record ResourceBlocked(ResourceId Resource, string By, DateTimeOffset At) : IDomainEvent;

/// <summary>Aggregate: private state, changed only through business methods, a version and events.</summary>
public sealed class ResourceAvailability
{
    private readonly List<IDomainEvent> _events = [];

    public ResourceAvailability(ResourceId id) => Id = id;

    public ResourceId Id { get; }
    public AvailabilityState State { get; private set; } = new AvailabilityState.Free();
    public int Version { get; private set; }

    public BlockResult Block(string by, DateTimeOffset at)
    {
        switch (State)
        {
            case AvailabilityState.Free:
                State = new AvailabilityState.Taken(by);
                Version++;
                _events.Add(new ResourceBlocked(Id, by, at));
                return new BlockResult.Blocked(Id, by);
            case AvailabilityState.Taken taken when taken.By == by:
                return new BlockResult.AlreadyBlockedBySameOwner();
            case AvailabilityState.Taken taken:
                return new BlockResult.Conflict(taken.By);
            case AvailabilityState.Off:
                return new BlockResult.Disabled();
            default:
                throw new InvalidOperationException($"Unhandled state {State}."); // a programmer error
        }
    }

    public void Disable() => State = new AvailabilityState.Off();

    /// <summary>Hands out the events for publishing (e.g. through an outbox) and clears the list.</summary>
    public IReadOnlyList<IDomainEvent> PullEvents()
    {
        var events = _events.ToArray();
        _events.Clear();
        return events;
    }
}

/// <summary>The repository port in the domain; the adapter (EF Core, Dapper) in the infrastructure.</summary>
public interface IResourceAvailabilityRepository
{
    Task<ResourceAvailability?> GetAsync(ResourceId id, CancellationToken ct);
    Task SaveAsync(ResourceAvailability aggregate, int expectedVersion, CancellationToken ct);
}
```

## ResourceAvailabilityTests.cs
```csharp
using Booking.Domain;

namespace Booking.Domain.Tests;

public class ResourceAvailabilityTests
{
    private static readonly DateTimeOffset Now = new(2026, 10, 23, 9, 0, 0, TimeSpan.Zero);

    [Fact]
    public void Free_resource_gets_blocked_and_raises_event()
    {
        var r = new ResourceAvailability(ResourceId.New());

        var result = r.Block("anna", Now);

        Assert.IsType<BlockResult.Blocked>(result);
        Assert.Single(r.PullEvents());
        Assert.Equal(1, r.Version);
    }

    [Theory]
    [InlineData("jan", typeof(BlockResult.Conflict))]
    [InlineData("anna", typeof(BlockResult.AlreadyBlockedBySameOwner))]
    public void Taken_resource(string by, Type expected)
    {
        var r = new ResourceAvailability(ResourceId.New());
        r.Block("anna", Now);

        Assert.IsType(expected, r.Block(by, Now));
    }

    [Fact]
    public void Disabled_resource_rejects()
    {
        var r = new ResourceAvailability(ResourceId.New());
        r.Disable();

        var message = r.Block("anna", Now) switch
        {
            BlockResult.Blocked => "ok",
            BlockResult.AlreadyBlockedBySameOwner => "ok",
            BlockResult.Conflict c => $"taken by {c.BlockedBy}",
            BlockResult.Disabled => "disabled",
            _ => throw new InvalidOperationException(),
        };

        Assert.Equal("disabled", message);
    }

    [Fact]
    public void Money_adds_same_currency_and_rejects_other()
    {
        var sum = new Money(19.99m, "pln").Add(new Money(0.01m, "PLN"));

        Assert.Equal(new Money(20m, "PLN"), sum);
        Assert.Throws<InvalidOperationException>(() => sum.Add(new Money(1m, "EUR")));
    }
}
```

