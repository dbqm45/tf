# pytest 9 examples

> **Contents:** 1. Case table · 2. Property-based test · 3. `tmp_path` and `monkeypatch` · 4. Factory fixture and a fake repository · 5. An asyncio test with a time limit · 6. Subtests

Run on 2026-10-03: pytest 9.1.1, pytest-asyncio 1.4.0, hypothesis 6.168.3, CPython 3.14.8, with the configuration
from SKILL.md (`strict = true`, `--import-mode=importlib`, `asyncio_mode = "auto"`) and the code in `src/shop/`.

## 1. Case table
The code: `discount(amount: Decimal) -> Decimal` — 5% from 200 PLN, 10% from 1000 PLN.
```python
# tests/test_discount.py
from decimal import Decimal

import pytest

from shop.discount import discount


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        pytest.param("199.99", "0.00", id="just-below-threshold-200"),
        pytest.param("200.00", "10.00", id="threshold-200"),
        pytest.param("999.99", "50.00", id="just-below-threshold-1000"),
        pytest.param("1000.00", "100.00", id="threshold-1000"),
    ],
)
def test_discount_thresholds(amount: str, expected: str) -> None:
    assert discount(Decimal(amount)) == Decimal(expected)
```
Boundary values on both sides of the threshold (qa-test-design). The `id` is visible in the report and in `-k "threshold-200"`.

## 2. Property-based test
```python
# tests/test_discount_properties.py
from decimal import Decimal

from hypothesis import example, given
from hypothesis import strategies as st

from shop.discount import discount

amounts = st.decimals(min_value=0, max_value=1_000_000, places=2)


@given(amounts)
@example(Decimal("1000.00"))
def test_discount_never_exceeds_ten_percent(amount: Decimal) -> None:
    assert Decimal(0) <= discount(amount) <= amount * Decimal("0.10") + Decimal("0.005")
```
An invariant instead of single examples; you preserve a case found by Hypothesis in `@example`.

## 3. `tmp_path` and `monkeypatch`
```python
# tests/test_export.py
from pathlib import Path

import pytest

from shop.export import export_report


def test_export_uses_name_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPORT_NAME", "may.csv")
    path = export_report(["a", "b"], tmp_path)
    assert path == tmp_path / "may.csv"
    assert path.read_text(encoding="utf-8") == "a\nb"
```
`monkeypatch` reverts the variable change after the test; `tmp_path` is a separate directory for every test.

## 4. Factory fixture and a fake repository
```python
# tests/conftest.py
from collections.abc import Callable
from dataclasses import dataclass, field

import pytest


@dataclass
class Order:
    id: str
    owner: str
    lines: list[tuple[str, int]] = field(default_factory=list)


class InMemoryOrders:
    """A fake of the repository port — real behavior, no database."""

    def __init__(self) -> None:
        self.saved: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self.saved[order.id] = order

    def of_owner(self, owner: str) -> list[Order]:
        return [o for o in self.saved.values() if o.owner == owner]


@pytest.fixture
def orders() -> InMemoryOrders:
    return InMemoryOrders()


@pytest.fixture
def make_order(orders: InMemoryOrders) -> Callable[..., Order]:
    counter = 0

    def make(owner: str = "ola", **kw: object) -> Order:
        nonlocal counter
        counter += 1
        order = Order(id=f"o{counter}", owner=owner, **kw)  # type: ignore[arg-type]
        orders.save(order)
        return order

    return make
```
```python
# tests/test_orders.py
def test_owner_sees_only_own_orders(orders, make_order) -> None:
    mine = make_order(owner="ola")
    make_order(owner="jan")
    assert orders.of_owner("ola") == [mine]
```
**Do not import from `conftest.py`** (`from conftest import …`): with `--import-mode=importlib` this ends in
`ModuleNotFoundError` (verified). Tests get objects through fixtures; when helper classes are needed
in annotations or in many places, put them in a separate test package installed in the development
environment or in `src/<package>/testing.py`.

## 5. An asyncio test with a time limit
```python
# tests/test_notify.py
import asyncio

import pytest

from shop.notify import first_event


async def test_returns_first_event() -> None:
    q: asyncio.Queue[str] = asyncio.Queue()
    q.put_nowait("RoomReserved")
    assert await first_event(q, limit_s=1) == "RoomReserved"


async def test_times_out_without_event() -> None:
    with pytest.raises(TimeoutError):
        await first_event(asyncio.Queue(), limit_s=0.01)
```
With `asyncio_mode = "auto"`, `async def` functions are asyncio tests without a marker.

## 6. Subtests
```python
# tests/test_codes.py
import pytest

CODES = {"PLN": 2, "EUR": 2, "JPY": 0}


def test_currency_minor_units(subtests: pytest.Subtests) -> None:
    for code, digits in CODES.items():
        with subtests.test(code=code):
            assert digits in (0, 2)
```
Every failure in the loop is reported separately; for simple tables choose `parametrize`.
