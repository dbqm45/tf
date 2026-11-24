"""The cart page."""
from html import escape

from app.components.button import button
from app.pricing import order_total


def money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def render(items: list[str], lines: list[tuple[int, int]] = ()) -> str:
    """The cart: item names, the order total for `lines` ((unit price in cents, quantity) pairs) and the button."""
    rows = "".join(f"<li>{escape(name)}</li>" for name in items)
    total = f"<p>Total: {money(order_total(list(lines)))}</p>"
    return f"<h1>Cart</h1><ul>{rows}</ul>{total}" + button("Proceed", kind="primary", style="width: 100%")
