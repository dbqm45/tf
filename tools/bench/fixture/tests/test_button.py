import unittest

from app.components.button import button


class ButtonTest(unittest.TestCase):
    def test_classes(self):
        self.assertIn('class="btn btn-primary"', button("Go"))

    def test_label_escaped(self):
        self.assertIn("&lt;b&gt;", button("<b>"))

    def test_style(self):
        self.assertIn('style="color: red"', button("Go", style="color: red"))
        self.assertNotIn("style=", button("Go"))


if __name__ == "__main__":
    unittest.main()
