"""Hidden acceptance check of the `medium` bench task: python3 medium.py <project>; exit code 0 = accepted."""
import sys

sys.path.insert(0, sys.argv[1])
from app.pages import cart  # noqa: E402
from app.pricing import order_discount, order_total  # noqa: E402

assert order_discount([(100, 9)]) == 0
assert order_discount([(1000, 10)]) == 500
assert order_discount([(999, 10)]) == 499, order_discount([(999, 10)])
assert order_discount([(100, 30), (100, 19)]) == 245
assert order_discount([(100, 50)]) == 500
assert order_total([(1000, 10)]) == 9500
assert order_total([(100, 9)]) == 900
html = cart.render(["a"], [(1000, 10)])
assert "Discount: -5.00" in html and "Total: 95.00" in html, html
assert html.index("Discount:") < html.index("Total:"), html
assert "Discount" not in cart.render(["a"], [(100, 1)])
print("accepted")
