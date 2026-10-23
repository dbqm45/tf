# Klocki domenowe w C# — przetestowane przykłady

Projekt sprawdzony 2026-10-23: `dotnet test` (xUnit) na net8.0 (C# 12) i net10.0 (C# 14) z
`TreatWarningsAsErrors` i `Nullable`, `dotnet format --verify-no-changes` bez uwag (SDK 8.0.132 i 10.0.113).
Kod używa tylko C# 12, więc działa w całym zakresie skilla. Pliki skopiowane bez zmian.

## Spis treści
- Booking.Domain.csproj
- Money.cs — kwota i identyfikator (obiekty wartości)
- ResourceAvailability.cs — wynik operacji, stany, zdarzenie, agregat, port repozytorium
- ResourceAvailabilityTests.cs — testy xUnit, wyczerpujące `switch` na wyniku

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

/// <summary>Kwota — obiekt wartości: decimal z jawną walutą, niezmienny, równość po wartości (record struct).</summary>
public readonly record struct Money
{
    public decimal Amount { get; }
    public string Currency { get; }

    public Money(decimal amount, string currency)
    {
        if (string.IsNullOrWhiteSpace(currency) || currency.Length != 3)
            throw new ArgumentException("Waluta: trzyliterowy kod ISO 4217.", nameof(currency));
        Amount = decimal.Round(amount, 2, MidpointRounding.ToEven);
        Currency = currency.ToUpperInvariant();
    }

    public Money Add(Money other) =>
        other.Currency == Currency
            ? new Money(Amount + other.Amount, Currency)
            : throw new InvalidOperationException($"Różne waluty: {Currency} i {other.Currency}.");

    public override string ToString() => $"{Amount:0.00} {Currency}";
}

/// <summary>Identyfikator jako typ, nie goły Guid/string.</summary>
public readonly record struct ResourceId(Guid Value)
{
    public static ResourceId New() => new(Guid.NewGuid());
}
```

## ResourceAvailability.cs
```csharp
namespace Booking.Domain;

/// <summary>Wynik operacji: sukces albo odrzucenie biznesowe — zamknięta hierarchia rekordów.</summary>
public abstract record BlockResult
{
    private BlockResult() { } // tylko warianty zagnieżdżone

    public sealed record Blocked(ResourceId Resource, string By) : BlockResult;
    public sealed record AlreadyBlockedBySameOwner : BlockResult;
    public sealed record Conflict(string BlockedBy) : BlockResult;
    public sealed record Disabled : BlockResult;
}

/// <summary>Stan jako warianty (maszyna stanów).</summary>
public abstract record AvailabilityState
{
    private AvailabilityState() { }

    public sealed record Free : AvailabilityState;
    public sealed record Taken(string By) : AvailabilityState;
    public sealed record Off : AvailabilityState;
}

public interface IDomainEvent;

public sealed record ResourceBlocked(ResourceId Resource, string By, DateTimeOffset At) : IDomainEvent;

/// <summary>Agregat: stan prywatny, zmiana tylko metodami biznesowymi, wersja i zdarzenia.</summary>
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
                throw new InvalidOperationException($"Nieobsłużony stan {State}."); // błąd programisty
        }
    }

    public void Disable() => State = new AvailabilityState.Off();

    /// <summary>Oddaje zdarzenia do publikacji (np. przez outbox) i czyści listę.</summary>
    public IReadOnlyList<IDomainEvent> PullEvents()
    {
        var events = _events.ToArray();
        _events.Clear();
        return events;
    }
}

/// <summary>Port repozytorium w domenie; adapter (EF Core, Dapper) w infrastrukturze.</summary>
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
            BlockResult.Conflict c => $"zajęte przez {c.BlockedBy}",
            BlockResult.Disabled => "wyłączony",
            _ => throw new InvalidOperationException(),
        };

        Assert.Equal("wyłączony", message);
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

