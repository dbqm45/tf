import unittest

from app.pricing import line_total, order_total


class PricingTest(unittest.TestCase):
    def test_line_total(self):
        self.assertEqual(line_total(250, 4), 1000)

    def test_order_total(self):
        self.assertEqual(order_total([(250, 4), (99, 1)]), 1099)
        self.assertEqual(order_total([]), 0)


if __name__ == "__main__":
    unittest.main()
