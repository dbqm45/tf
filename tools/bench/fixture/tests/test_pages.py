import unittest

from app.pages import cart, orders, profile, search, settings_page, wishlist


class PagesTest(unittest.TestCase):
    def test_titles_and_items(self):
        for page, title in ((cart, "Cart"), (orders, "Orders"), (profile, "Profile"), (search, "Search"),
                            (settings_page, "Settings"), (wishlist, "Wishlist")):
            html = page.render(["a & b"])
            self.assertIn(f"<h1>{title}</h1>", html)
            self.assertIn("<li>a &amp; b</li>", html)

    def test_labels(self):
        self.assertIn(">Proceed<", cart.render([]))
        self.assertIn(">Proceed<", orders.render([]))
        self.assertIn(">Discard<", profile.render([]))
        self.assertIn(">Discard<", wishlist.render([]))

    def test_cart_total(self):
        self.assertIn("Total: 25.50", cart.render(["x"], [(1200, 2), (150, 1)]))


if __name__ == "__main__":
    unittest.main()
