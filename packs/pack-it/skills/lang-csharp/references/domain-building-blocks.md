# Domain building blocks in C# — example

> **Contents:** ToolLibrary.Lending.csproj · Money.cs · Ids.cs · Results.cs · LendableTool.cs · LendableToolTests.cs

The domain is a **neighbourhood tool library** (the same one as in the Java, TypeScript and Go skills): members
borrow tools; a tool is on the shelf, lent or withdrawn.

**Verification status:** checked 2026-11-20 with SDK 8.0.134 and 10.0.115 (Ubuntu 24.04 packages): `dotnet test`
on `net8.0` and `net10.0` (6 tests each) with `TreatWarningsAsErrors` (0 warnings) and
`dotnet format --verify-no-changes`. The test project references `Microsoft.NET.Test.Sdk` 18.12.0, `xunit` 2.9.3 and
`xunit.runner.visualstudio` 3.1.5. Only C# 12 features are used (primary constructors in classes, collection
expressions), so the same code builds on .NET 8 and .NET 10.

Files:
- ToolLibrary.Lending.csproj — the domain project, no dependency on ASP.NET or EF Core
- Money.cs — amount as a value object with an exact split
- Ids.cs — typed identifiers
- Results.cs — operation results as closed record hierarchies, states, events
- LendableTool.cs — the aggregate and the repository port
- LendableToolTests.cs — xUnit tests, including an exhaustive `switch` over a result

Design choices:
- A business rejection is a **result value**, not an exception: `LendResult` is an `abstract record` with a private
  constructor and `sealed` nested records, so no other code can add a variant. C# (up to 14) does not check a
  `switch` over such a hierarchy for exhaustiveness: the `_ => throw new UnreachableException()` arm marks the
  programmer error, and a new variant shows up when reviewing every `switch` on the type.
- Exceptions stay for broken contracts: a currency mismatch, a blank identifier, `Split(0)`.
- `Version` grows with every recorded event; the EF Core or Dapper adapter compares it with `expectedVersion`.

## ToolLibrary.Lending.csproj
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFrameworks>net8.0;net10.0</TargetFrameworks>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <RootNamespace>ToolLibrary.Lending</RootNamespace>
  </PropertyGroup>
</Project>
```

## Money.cs
```csharp
using System.Globalization;

namespace ToolLibrary.Lending;

/// <summary>An amount with two decimal places; `decimal` equality ignores trailing zeros (1.0m == 1.00m).</summary>
public readonly record struct Money
{
    public decimal Amount { get; }
    public string Currency { get; }

    public Money(decimal amount, string currency)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(currency);
        if (decimal.Round(amount, 2) != amount)
        {
            throw new ArgumentException($"At most two decimal places, got {amount}.", nameof(amount));
        }
        Amount = amount;
        Currency = currency.ToUpperInvariant();
    }

    public Money Add(Money other) => other.Currency == Currency
        ? new Money(Amount + other.Amount, Currency)
        : throw new InvalidOperationException($"Currency mismatch: {Currency} vs {other.Currency}.");

    /// <summary>Shares that add up exactly; leftover cents go to the first shares, with the amount's sign.</summary>
    public IReadOnlyList<Money> Split(int parts)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(parts, 1);
        var cents = (long)(Amount * 100m);
        var baseCents = cents / parts;   // integer division truncates toward zero
        var rest = cents % parts;        // same sign as the amount
        var step = Math.Sign(rest);
        var extra = Math.Abs(rest);
        var currency = Currency;
        return Enumerable.Range(0, parts)
            .Select(i => new Money((baseCents + (i < extra ? step : 0)) / 100m, currency))
            .ToArray();
    }

    public override string ToString() =>
        string.Create(CultureInfo.InvariantCulture, $"{Amount:0.00} {Currency}");
}
```
`default(Money)` has a `null` currency: never use it as a value; at a boundary build `Money` only through the constructor.

## Ids.cs
```csharp
namespace ToolLibrary.Lending;

public readonly record struct ToolId
{
    public ToolId(string value)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        Value = value;
    }

    public string Value { get; }

    public override string ToString() => Value;
}

public readonly record struct MemberId
{
    public MemberId(string value)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        Value = value;
    }

    public string Value { get; }

    public override string ToString() => Value;
}
```

## Results.cs
```csharp
namespace ToolLibrary.Lending;

public interface IToolEvent
{
    ToolId Tool { get; }
    DateTimeOffset At { get; }
}

public sealed record ToolLent(ToolId Tool, MemberId Borrower, DateTimeOffset At) : IToolEvent;
public sealed record ToolReturned(ToolId Tool, MemberId Borrower, DateTimeOffset At) : IToolEvent;
public sealed record ToolWithdrawn(ToolId Tool, MemberId By, string Reason, DateTimeOffset At) : IToolEvent;

public abstract record ShelfState
{
    private ShelfState() { }

    public sealed record OnShelf : ShelfState;
    public sealed record Lent(MemberId Borrower, DateTimeOffset Since) : ShelfState;
    public sealed record Withdrawn(MemberId By, string Reason) : ShelfState;
}

public abstract record LendResult
{
    private LendResult() { }

    public sealed record Lent(ToolLent Event) : LendResult;
    public sealed record OnLoan(MemberId Borrower) : LendResult;
    public sealed record Withdrawn : LendResult;
}

public abstract record ReturnResult
{
    private ReturnResult() { }

    public sealed record Returned(ToolReturned Event) : ReturnResult;
    public sealed record NotTheBorrower : ReturnResult;
    public sealed record NotLent : ReturnResult;
    public sealed record Withdrawn : ReturnResult;
}
```

## LendableTool.cs
```csharp
using System.Diagnostics;

namespace ToolLibrary.Lending;

public sealed class LendableTool(ToolId id)
{
    private readonly List<IToolEvent> _pending = [];

    public ToolId Id { get; } = id;
    public ShelfState State { get; private set; } = new ShelfState.OnShelf();
    public int Version { get; private set; }

    public LendResult Lend(MemberId member, DateTimeOffset at) => State switch
    {
        ShelfState.OnShelf => StartLoan(member, at),
        ShelfState.Lent lent => new LendResult.OnLoan(lent.Borrower),
        ShelfState.Withdrawn => new LendResult.Withdrawn(),
        _ => throw new UnreachableException($"Unknown state {State}."),
    };

    public ReturnResult GiveBack(MemberId member, DateTimeOffset at) => State switch
    {
        ShelfState.Lent lent when lent.Borrower == member => EndLoan(member, at),
        ShelfState.Lent => new ReturnResult.NotTheBorrower(),
        ShelfState.OnShelf => new ReturnResult.NotLent(),
        ShelfState.Withdrawn => new ReturnResult.Withdrawn(),
        _ => throw new UnreachableException($"Unknown state {State}."),
    };

    /// <summary>A staff decision (broken, lost, sold); it cannot be refused.</summary>
    public ToolWithdrawn Withdraw(MemberId by, string reason, DateTimeOffset at)
    {
        State = new ShelfState.Withdrawn(by, reason);
        return Record(new ToolWithdrawn(Id, by, reason, at));
    }

    /// <summary>Hands over the events recorded since the last call and empties the buffer.</summary>
    public IReadOnlyList<IToolEvent> PullEvents()
    {
        var drained = _pending.ToArray();
        _pending.Clear();
        return drained;
    }

    private LendResult.Lent StartLoan(MemberId member, DateTimeOffset at)
    {
        State = new ShelfState.Lent(member, at);
        return new LendResult.Lent(Record(new ToolLent(Id, member, at)));
    }

    private ReturnResult.Returned EndLoan(MemberId member, DateTimeOffset at)
    {
        State = new ShelfState.OnShelf();
        return new ReturnResult.Returned(Record(new ToolReturned(Id, member, at)));
    }

    private T Record<T>(T @event) where T : IToolEvent
    {
        _pending.Add(@event);
        Version++;
        return @event;
    }
}

/// <summary>The port; the EF Core/Dapper adapter lives in the infrastructure project.</summary>
public interface ILendableTools
{
    Task<LendableTool?> FindAsync(ToolId id, CancellationToken ct);
    Task SaveAsync(LendableTool tool, int expectedVersion, CancellationToken ct);
}
```

## LendableToolTests.cs
The test project references the domain project and the packages `Microsoft.NET.Test.Sdk`, `xunit` (2.9.x) and
`xunit.runner.visualstudio`.

```csharp
using System.Diagnostics;
using ToolLibrary.Lending;
using Xunit;

public class LendableToolTests
{
    private static readonly MemberId Ola = new("m-0042");
    private static readonly MemberId Kuba = new("m-0107");
    private static readonly MemberId Staff = new("s-0001");
    private static readonly DateTimeOffset Nine = new(2026, 11, 20, 9, 0, 0, TimeSpan.Zero);
    private static readonly DateTimeOffset Ten = Nine.AddHours(1);
    private static readonly DateTimeOffset Eleven = Nine.AddHours(2);

    [Fact]
    public void Adding_money_is_exact()
    {
        var sum = new Money(0.10m, "EUR").Add(new Money(0.20m, "EUR"));
        Assert.Equal(new Money(0.30m, "EUR"), sum);
    }

    [Theory]
    [InlineData(100.00, new[] { 33.34, 33.33, 33.33 })]
    [InlineData(-1.00, new[] { -0.34, -0.33, -0.33 })]
    public void Split_shares_add_up(double amount, double[] expected)
    {
        var shares = new Money((decimal)amount, "PLN").Split(expected.Length);
        Assert.Equal(expected.Select(x => (decimal)x), shares.Select(s => s.Amount));
    }

    [Fact]
    public void Adding_another_currency_throws() =>
        Assert.Throws<InvalidOperationException>(() => new Money(1m, "PLN").Add(new Money(1m, "EUR")));

    [Fact]
    public void Lending_sequence()
    {
        var tool = new LendableTool(new ToolId("T-217"));

        Assert.IsType<LendResult.Lent>(tool.Lend(Ola, Nine));
        var refused = Assert.IsType<LendResult.OnLoan>(tool.Lend(Kuba, Ten));
        Assert.Equal(Ola, refused.Borrower);
        Assert.IsType<ReturnResult.NotTheBorrower>(tool.GiveBack(Kuba, Ten));
        Assert.IsType<ReturnResult.Returned>(tool.GiveBack(Ola, Ten));
        Assert.IsType<ReturnResult.NotLent>(tool.GiveBack(Ola, Ten));
        tool.Withdraw(Staff, "worn chuck", Eleven);
        Assert.IsType<LendResult.Withdrawn>(tool.Lend(Kuba, Eleven));
        Assert.IsType<LendResult.Withdrawn>(tool.Lend(Staff, Eleven));

        Assert.Equal(3, tool.Version);
        IToolEvent[] expected =
        [
            new ToolLent(tool.Id, Ola, Nine),
            new ToolReturned(tool.Id, Ola, Ten),
            new ToolWithdrawn(tool.Id, Staff, "worn chuck", Eleven),
        ];
        Assert.Equal(expected, tool.PullEvents());
        Assert.Empty(tool.PullEvents());
    }

    [Fact]
    public void Caller_handles_every_result()
    {
        var tool = new LendableTool(new ToolId("T-301"));
        tool.Lend(Ola, Nine);

        var message = tool.Lend(Kuba, Ten) switch
        {
            LendResult.Lent lent => $"lent to {lent.Event.Borrower}",
            LendResult.OnLoan onLoan => $"on loan to {onLoan.Borrower}",
            LendResult.Withdrawn => "withdrawn",
            _ => throw new UnreachableException(),
        };
        Assert.Equal("on loan to m-0042", message);
    }
}
```
