"""Order totals. Amounts are integers in cents."""


def line_total(unit_price_cents: int, quantity: int) -> int:
    return unit_price_cents * quantity


def order_total(lines: list[tuple[int, int]]) -> int:
    """The total of the order's lines: (unit price in cents, quantity) pairs."""
    return sum(line_total(price, qty) for price, qty in lines)
