# Domain building blocks in Java 21 — a tested example

> **Contents:** 1. Money (record + `BigDecimal`) · 2. Typed identifiers · 3. Variants (`sealed` + records) · 4. Operation result · 5. Loan period · 6. Aggregate with a state machine and events · 7. Repository port · 8. Tests: edge cases

One domain runs through every section: a **neighbourhood tool library** that lends drills, ladders and welders to its
members. The same domain is used in `lang-typescript/references/domain-building-blocks.md`, so the two files can be
read side by side.

Checked 2026-11-20 with OpenJDK `javac 21.0.13`: `javac --release 21 -Xlint:all -Werror` reports nothing, and
`java tools.lending.LendingTests` prints the OK line. Each `// ===== Name.java =====` comment starts a separate source
file of the package `tools.lending`.

**In a project:** one top-level type per file (as below), and only the module facade (e.g. a `ToolLending`
application service) is `public`. Everything here is package-private on purpose; records nested in an interface are
implicitly `public`, which is why their compact constructors must be declared `public`.

**On Java 17:** records and `sealed` work, but type patterns in `switch` and `when` guards do not (see the version table
in `SKILL.md`): replace the `switch` with `if (x instanceof Lent l && …)` chains.

## 1. Money (record + `BigDecimal`)
The compact constructor validates and normalises: the scale always equals the currency's fraction digits, so record
equality (`BigDecimal.equals` is scale-sensitive) and `compareTo` agree. Arithmetic returns new records.

```java
// ===== Money.java =====
package tools.lending;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Currency;
import java.util.List;
import java.util.Objects;

record Money(BigDecimal amount, Currency currency) implements Comparable<Money> {

    Money {
        Objects.requireNonNull(amount, "amount");
        Objects.requireNonNull(currency, "currency");
        amount = amount.setScale(currency.getDefaultFractionDigits(), RoundingMode.HALF_UP);
    }

    static Money of(String amount, String currencyCode) {
        return new Money(new BigDecimal(amount), Currency.getInstance(currencyCode));
    }

    static Money zero(Currency currency) {
        return new Money(BigDecimal.ZERO, currency);
    }

    Money plus(Money other) {
        requireSameCurrency(other);
        return new Money(amount.add(other.amount), currency);
    }

    Money minus(Money other) {
        requireSameCurrency(other);
        return new Money(amount.subtract(other.amount), currency);
    }

    /**
     * Splits the amount into {@code parts} shares that add up to exactly this amount.
     * Works on minor units; the leftover units go one by one to the first shares
     * (for a negative amount the first shares are the "more negative" ones).
     */
    List<Money> split(int parts) {
        if (parts < 1) {
            throw new IllegalArgumentException("parts must be at least 1, was " + parts);
        }
        BigInteger[] quotientAndRest = amount.unscaledValue().divideAndRemainder(BigInteger.valueOf(parts));
        BigInteger base = quotientAndRest[0];
        int rest = quotientAndRest[1].intValueExact(); // |rest| < parts, same sign as the amount
        BigInteger step = BigInteger.valueOf(Integer.signum(rest));
        List<Money> shares = new ArrayList<>(parts);
        for (int i = 0; i < parts; i++) {
            BigInteger units = i < Math.abs(rest) ? base.add(step) : base;
            shares.add(new Money(new BigDecimal(units, amount.scale()), currency));
        }
        return List.copyOf(shares);
    }

    @Override
    public int compareTo(Money other) {
        requireSameCurrency(other);
        return amount.compareTo(other.amount);
    }

    private void requireSameCurrency(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("Currency mismatch: " + currency + " vs " + other.currency);
        }
    }

    @Override
    public String toString() {
        return amount.toPlainString() + " " + currency.getCurrencyCode();
    }
}
```

## 2. Typed identifiers
A single-field record per entity: a `MemberId` cannot be passed where a `ToolId` is expected, and the null/blank check
lives in one place.

```java
// ===== ToolId.java =====
package tools.lending;

import java.util.Objects;

record ToolId(String value) {
    ToolId {
        Objects.requireNonNull(value, "value");
        if (value.isBlank()) {
            throw new IllegalArgumentException("ToolId must not be blank");
        }
    }
}
```

```java
// ===== MemberId.java =====
package tools.lending;

import java.util.Objects;

record MemberId(String value) {
    MemberId {
        Objects.requireNonNull(value, "value");
        if (value.isBlank()) {
            throw new IllegalArgumentException("MemberId must not be blank");
        }
    }
}
```

## 3. Variants (`sealed` + records)
A member is an adult, a junior (borrows under a guardian) or a company account. `permits` closes the hierarchy, so a
`switch` without `default` is checked for exhaustiveness: adding a fourth variant breaks compilation at every such
`switch`. Collections are copied in the compact constructor; `Optional` appears only as a component for a reference
that is genuinely optional (the parent company).

```java
// ===== Licence.java =====
package tools.lending;

enum Licence { POWER_TOOLS, LADDERS, WELDING }

// ===== Member.java =====
package tools.lending;

import java.util.Objects;
import java.util.Optional;
import java.util.Set;

sealed interface Member permits Member.Adult, Member.Junior, Member.Company {

    MemberId id();

    Set<Licence> licences();

    default boolean mayUse(Licence licence) {
        return licences().contains(licence);
    }

    record Adult(MemberId id, String fullName, Set<Licence> licences) implements Member {
        public Adult {
            Objects.requireNonNull(id, "id");
            Objects.requireNonNull(fullName, "fullName");
            licences = Set.copyOf(licences);
        }
    }

    record Junior(MemberId id, String fullName, MemberId guardian) implements Member {
        public Junior {
            Objects.requireNonNull(id, "id");
            Objects.requireNonNull(fullName, "fullName");
            Objects.requireNonNull(guardian, "guardian");
        }

        @Override
        public Set<Licence> licences() {
            return Set.of(); // juniors never hold a licence of their own
        }
    }

    record Company(MemberId id, String legalName, Set<Licence> licences, Optional<MemberId> parent)
            implements Member {
        public Company {
            Objects.requireNonNull(id, "id");
            Objects.requireNonNull(legalName, "legalName");
            licences = Set.copyOf(licences);
            Objects.requireNonNull(parent, "parent (use Optional.empty())");
        }
    }

    static String displayName(Member member) {
        return switch (member) {
            case Adult a -> a.fullName();
            case Junior j -> j.fullName() + " (junior)";
            case Company c -> c.legalName();
        };
    }
}
```

## 4. Operation result
A business rejection is an expected outcome, not an exception. Records give structural equality, so a test can compare a
whole result with `equals`.

```java
// ===== Result.java =====
package tools.lending;

import java.util.Objects;

sealed interface Result<E, T> {

    record Success<E, T>(T value) implements Result<E, T> {
        public Success {
            Objects.requireNonNull(value, "value");
        }
    }

    record Failure<E, T>(E error) implements Result<E, T> {
        public Failure {
            Objects.requireNonNull(error, "error");
        }
    }

    static <E, T> Result<E, T> success(T value) {
        return new Success<>(value);
    }

    static <E, T> Result<E, T> failure(E error) {
        return new Failure<>(error);
    }
}
```

## 5. Loan period
Half-open interval `[start, end)`: a loan ending at 10:00 and the next one starting at 10:00 do not overlap.

```java
// ===== LoanPeriod.java =====
package tools.lending;

import java.time.Instant;
import java.util.Objects;

record LoanPeriod(Instant start, Instant end) {
    LoanPeriod {
        Objects.requireNonNull(start, "start");
        Objects.requireNonNull(end, "end");
        if (!start.isBefore(end)) {
            throw new IllegalArgumentException("start must be before end: " + start + " / " + end);
        }
    }

    boolean overlaps(LoanPeriod other) {
        return start.isBefore(other.end) && other.start.isBefore(end);
    }
}
```

## 6. Aggregate with a state machine and events
States are records of a `sealed` interface, so combinations such as "on the shelf but with a borrower" cannot be built.
Transitions are `switch` expressions with type patterns and a `when` guard. Every recorded event bumps `version`
(the hook for optimistic locking in the adapter); `pullEvents()` hands the buffer over and empties it.

```java
// ===== LoanRefusal.java =====
package tools.lending;

enum LoanRefusal { ON_LOAN, NOT_THE_BORROWER, NOT_LENT, WITHDRAWN }

// ===== ShelfState.java =====
package tools.lending;

import java.time.Instant;

sealed interface ShelfState {
    record OnShelf() implements ShelfState {}
    record Lent(MemberId borrower, Instant since) implements ShelfState {}
    record Withdrawn(MemberId by, String reason) implements ShelfState {}
}

// ===== ToolEvent.java =====
package tools.lending;

import java.time.Instant;

sealed interface ToolEvent {
    ToolId tool();

    record ToolLent(ToolId tool, MemberId borrower, Instant at) implements ToolEvent {}
    record ToolReturned(ToolId tool, MemberId borrower, Instant at) implements ToolEvent {}
    record ToolWithdrawn(ToolId tool, MemberId by, String reason, Instant at) implements ToolEvent {}
}

// ===== LendableTool.java =====
package tools.lending;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

final class LendableTool {

    private final ToolId id;
    private ShelfState state = new ShelfState.OnShelf();
    private long version;
    private final List<ToolEvent> pending = new ArrayList<>();

    LendableTool(ToolId id) {
        this.id = Objects.requireNonNull(id, "id");
    }

    Result<LoanRefusal, ToolEvent> lend(MemberId member, Instant at) {
        return switch (state) {
            case ShelfState.OnShelf onShelf ->
                    accept(new ShelfState.Lent(member, at), new ToolEvent.ToolLent(id, member, at));
            case ShelfState.Lent lent -> Result.failure(LoanRefusal.ON_LOAN);
            case ShelfState.Withdrawn withdrawn -> Result.failure(LoanRefusal.WITHDRAWN);
        };
    }

    Result<LoanRefusal, ToolEvent> giveBack(MemberId member, Instant at) {
        return switch (state) {
            case ShelfState.Lent lent when lent.borrower().equals(member) ->
                    accept(new ShelfState.OnShelf(), new ToolEvent.ToolReturned(id, member, at));
            case ShelfState.Lent lent -> Result.failure(LoanRefusal.NOT_THE_BORROWER);
            case ShelfState.OnShelf onShelf -> Result.failure(LoanRefusal.NOT_LENT);
            case ShelfState.Withdrawn withdrawn -> Result.failure(LoanRefusal.WITHDRAWN);
        };
    }

    /** Withdrawing (broken, stolen, sold) is a staff decision and cannot be refused. */
    ToolEvent withdraw(MemberId by, String reason, Instant at) {
        state = new ShelfState.Withdrawn(by, reason);
        return record(new ToolEvent.ToolWithdrawn(id, by, reason, at));
    }

    /** Returns the events recorded since the last call and clears the buffer. */
    List<ToolEvent> pullEvents() {
        List<ToolEvent> drained = List.copyOf(pending);
        pending.clear();
        return drained;
    }

    ToolId id() {
        return id;
    }

    ShelfState state() {
        return state;
    }

    long version() {
        return version;
    }

    private Result<LoanRefusal, ToolEvent> accept(ShelfState next, ToolEvent event) {
        state = next;
        return Result.success(record(event));
    }

    private ToolEvent record(ToolEvent event) {
        pending.add(event);
        version++;
        return event;
    }
}
```

## 7. Repository port
The interface belongs to the domain package and speaks in aggregates. The JPA or JDBC adapter (e.g.
`tools.lending.infra.JdbcLendableTools`, which checks `version` in `UPDATE … WHERE version = ?`) lives in the
infrastructure package and is not shown here.

```java
// ===== LendableTools.java =====
package tools.lending;

import java.util.Optional;

interface LendableTools {
    Optional<LendableTool> byId(ToolId id);

    void save(LendableTool tool);
}
```

## 8. Tests: edge cases
Plain Java without a framework: a tiny `eq` helper and a `main`. Run with
`javac --release 21 -Xlint:all -Werror -d out *.java && java -cp out tools.lending.LendingTests`.

```java
// ===== LendingTests.java =====
package tools.lending;

import java.time.Instant;
import java.util.Currency;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

public final class LendingTests {

    private LendingTests() {}

    static void eq(Object expected, Object actual, String what) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(what + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    static void throwsIae(Runnable action, String what) {
        try {
            action.run();
        } catch (IllegalArgumentException expected) {
            return;
        }
        throw new AssertionError(what + ": expected IllegalArgumentException");
    }

    public static void main(String[] args) {
        // Money: exact decimal arithmetic, scale fixed by the currency
        eq(Money.of("0.30", "EUR"), Money.of("0.10", "EUR").plus(Money.of("0.20", "EUR")), "0.10 + 0.20");
        eq(Money.of("12.5", "PLN"), Money.of("12.50", "PLN"), "scale normalised");
        eq(0, Money.of("7", "PLN").compareTo(Money.of("7.00", "PLN")), "compareTo ignores input scale");
        eq(List.of(Money.of("33.34", "PLN"), Money.of("33.33", "PLN"), Money.of("33.33", "PLN")),
                Money.of("100.00", "PLN").split(3), "split 100 into 3");
        eq(List.of(Money.of("-0.34", "PLN"), Money.of("-0.33", "PLN"), Money.of("-0.33", "PLN")),
                Money.of("-1.00", "PLN").split(3), "split a negative amount");
        eq(Money.of("-1.00", "PLN"), Money.of("-1.00", "PLN").split(3).stream()
                .reduce(Money.zero(Currency.getInstance("PLN")), Money::plus), "shares add up");
        throwsIae(() -> Money.of("1.00", "PLN").plus(Money.of("1.00", "EUR")), "currency mismatch");

        // Variants: exhaustive switch and a default method
        var ola = new MemberId("m-0042");
        var kuba = new MemberId("m-0107");
        Member adult = new Member.Adult(ola, "Ola Wrona", Set.of(Licence.POWER_TOOLS));
        Member junior = new Member.Junior(new MemberId("m-0108"), "Tymek Wrona", ola);
        Member firm = new Member.Company(new MemberId("c-0007"), "Dach-Serwis sp. z o.o.",
                Set.of(Licence.LADDERS, Licence.WELDING), Optional.empty());
        eq("Ola Wrona", Member.displayName(adult), "adult name");
        eq("Tymek Wrona (junior)", Member.displayName(junior), "junior name");
        eq("Dach-Serwis sp. z o.o.", Member.displayName(firm), "company name");
        eq(true, adult.mayUse(Licence.POWER_TOOLS), "adult with licence");
        eq(false, junior.mayUse(Licence.POWER_TOOLS), "junior without licence");
        eq(false, firm.mayUse(Licence.POWER_TOOLS), "company lacks this licence");

        // Loan period: overlap, and touching periods do not overlap
        var nine = Instant.parse("2026-11-20T09:00:00Z");
        var ten = Instant.parse("2026-11-20T10:00:00Z");
        var eleven = Instant.parse("2026-11-20T11:00:00Z");
        eq(true, new LoanPeriod(nine, eleven).overlaps(new LoanPeriod(ten, eleven)), "overlap");
        eq(false, new LoanPeriod(nine, ten).overlaps(new LoanPeriod(ten, eleven)), "touching periods");
        throwsIae(() -> new LoanPeriod(ten, ten), "empty period");

        // Aggregate: the full lending sequence
        var drill = new LendableTool(new ToolId("T-217"));
        var staff = new MemberId("s-0001");
        eq(Result.success(new ToolEvent.ToolLent(drill.id(), ola, nine)), drill.lend(ola, nine), "first loan");
        eq(Result.failure(LoanRefusal.ON_LOAN), drill.lend(kuba, ten), "rival refused");
        eq(Result.failure(LoanRefusal.NOT_THE_BORROWER), drill.giveBack(kuba, ten), "stranger cannot return");
        eq(Result.success(new ToolEvent.ToolReturned(drill.id(), ola, ten)), drill.giveBack(ola, ten), "return");
        eq(Result.failure(LoanRefusal.NOT_LENT), drill.giveBack(ola, ten), "return twice");
        drill.withdraw(staff, "worn chuck", eleven);
        eq(Result.failure(LoanRefusal.WITHDRAWN), drill.lend(kuba, eleven), "lend after withdrawal");
        eq(Result.failure(LoanRefusal.WITHDRAWN), drill.lend(staff, eleven), "even staff cannot lend it");
        eq(3L, drill.version(), "version counts recorded events");
        eq(List.of(new ToolEvent.ToolLent(drill.id(), ola, nine),
                        new ToolEvent.ToolReturned(drill.id(), ola, ten),
                        new ToolEvent.ToolWithdrawn(drill.id(), staff, "worn chuck", eleven)),
                drill.pullEvents(), "events in order");
        eq(List.of(), drill.pullEvents(), "second pull is empty");

        System.out.println("OK: tool-lending domain tests passed (Java)");
    }
}
```
