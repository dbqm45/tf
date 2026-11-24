"""Hidden acceptance check of the `simple` bench task: python3 simple.py <project>; exit code 0 = accepted."""
import sys

sys.path.insert(0, sys.argv[1])
from app.components.button import button  # noqa: E402
from app.pages import cart, orders, profile, search, settings_page, wishlist  # noqa: E402

pages = (cart, orders, profile, search, settings_page, wishlist)
assert "btn-block" in button("x"), button("x")
for page in pages:
    html = page.render([])
    assert "btn-block" in html, (page.__name__, html)
    assert "width" not in html, (page.__name__, html)
    assert ">Proceed<" not in html and ">Discard<" not in html, (page.__name__, html)
for page in (cart, orders):
    assert ">Continue<" in page.render([]), page.__name__
for page in (profile, wishlist):
    assert ">Remove<" in page.render([]), page.__name__
print("accepted")
