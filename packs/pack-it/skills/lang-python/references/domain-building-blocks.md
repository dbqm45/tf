# Domain building blocks in Python — examples

> **Contents:** 1. Money · 2. Result · 3. Events · 4. Room booking aggregate · 5. Repository port and in-memory adapter · 6. Variant for Python 3.11

Code checked 2026-10-03:
- the 3.12+ variant (sections 1–5) run on CPython 3.14 and checked with `mypy --strict` (mypy 2.4.0) and `ruff check`;
- the 3.11 variant (section 6) run on CPython 3.11.

## 1. Money
```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

CENT = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if len(self.currency) != 3:
            raise ValueError(f"ISO 4217 currency code: {self.currency!r}")
        object.__setattr__(self, "amount", self.amount.quantize(CENT, ROUND_HALF_EVEN))

    @classmethod
    def of(cls, amount: str | int, currency: str) -> Money:
        return cls(Decimal(amount), currency)

    def __add__(self, other: Money) -> Money:
        if other.currency != self.currency:
            raise ValueError("different currencies")
        return Money(self.amount + other.amount, self.currency)
```
`ValueError` is correct here: a wrong currency is a programmer error, not a business rejection.

## 2. Result
```python
from dataclasses import dataclass
from typing import assert_never


@dataclass(frozen=True, slots=True)
class Ok[T]:
    value: T


@dataclass(frozen=True, slots=True)
class Rejected:
    reason: str


type Result[T] = Ok[T] | Rejected


def message(r: Result[str]) -> str:
    match r:
        case Ok(value=v):
            return f"Booked: {v}"
        case Rejected(reason=why):
            return f"Rejected: {why}"
        case _:
            assert_never(r)
```
Adding a third variant without a new `case` branch → mypy reports an error in `assert_never`.

## 3. Events
```python
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class SlotHeld:
    room: str
    slot: str
    by: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class SlotBooked:
    room: str
    slot: str
    by: str
    occurred_at: datetime


type RoomEvent = SlotHeld | SlotBooked


def now() -> datetime:
    return datetime.now(UTC)
```

## 4. Room booking aggregate
```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Free:
    pass


@dataclass(frozen=True, slots=True)
class Held:
    by: str


@dataclass(frozen=True, slots=True)
class Booked:
    by: str


type SlotState = Free | Held | Booked


class RoomSchedule:
    """Aggregate: consistency boundary = one room; changes only through business methods."""

    def __init__(self, room: str, version: int = 0) -> None:
        self.room = room
        self.version = version
        self._slots: dict[str, SlotState] = {}
        self._events: list[RoomEvent] = []

    def hold(self, slot: str, by: str) -> Result[str]:
        match self._slots.get(slot, Free()):
            case Free():
                self._slots[slot] = Held(by)
                self._events.append(SlotHeld(self.room, slot, by, now()))
                return Ok(slot)
            case Held(by=other) | Booked(by=other) if other != by:
                return Rejected("slot taken")
            case _:
                return Ok(slot)   # a retry by the same person — idempotent

    def confirm(self, slot: str, by: str) -> Result[str]:
        match self._slots.get(slot, Free()):
            case Held(by=holder) if holder == by:
                self._slots[slot] = Booked(by)
                self._events.append(SlotBooked(self.room, slot, by, now()))
                return Ok(slot)
            case Booked(by=holder) if holder == by:
                return Ok(slot)
            case _:
                return Rejected("hold the slot first")

    def pull_events(self) -> list[RoomEvent]:
        events, self._events = self._events, []
        return events
```

## 5. Repository port and in-memory adapter
```python
from typing import Protocol


class ConcurrencyConflict(Exception):
    """Someone saved the aggregate earlier — retry the command on fresh state."""


class RoomSchedules(Protocol):
    def get(self, room: str) -> RoomSchedule: ...
    def save(self, schedule: RoomSchedule) -> None: ...


class InMemoryRoomSchedules:
    def __init__(self) -> None:
        self._data: dict[str, RoomSchedule] = {}

    def get(self, room: str) -> RoomSchedule:
        return self._data.get(room) or RoomSchedule(room)

    def save(self, schedule: RoomSchedule) -> None:
        stored = self._data.get(schedule.room)
        if stored is not None and stored is not schedule:
            if stored.version != schedule.version:
                raise ConcurrencyConflict(schedule.room)
        schedule.version += 1
        self._data[schedule.room] = schedule


def reserve(repo: RoomSchedules, room: str, slot: str, by: str) -> Result[str]:
    schedule = repo.get(room)
    result = schedule.hold(slot, by)
    if isinstance(result, Ok):
        repo.save(schedule)
    return result
```
The SQL adapter implements the same `Protocol` and checks the version in `UPDATE … WHERE version = :expected`.
The domain test in pytest uses `InMemoryRoomSchedules` (tool-pytest).

## 6. Variant for Python 3.11
Without the `type` statement and without `class Ok[T]`: the generic through `TypeVar`, the alias through `TypeAlias`, `assert_never`
from `typing` (3.11 has it).
```python
from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar, Union, assert_never

T = TypeVar("T")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True)
class Rejected:
    reason: str


Result: TypeAlias = Union[Ok[T], Rejected]


def message(r: "Result[str]") -> str:
    if isinstance(r, Ok):
        return f"Booked: {r.value}"
    if isinstance(r, Rejected):
        return f"Rejected: {r.reason}"
    assert_never(r)
```
In 3.11 `match` also works; `slots=True` in a dataclass and `datetime.UTC` are available from 3.10 and 3.11.
