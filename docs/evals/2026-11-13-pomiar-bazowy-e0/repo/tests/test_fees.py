import unittest

from parking.fees import fee


class FeeTest(unittest.TestCase):
    def test_first_half_hour_is_free(self):
        self.assertEqual(fee(0), 0)
        self.assertEqual(fee(30), 0)

    def test_every_started_hour_costs_four_zloty(self):
        self.assertEqual(fee(31), 400)
        self.assertEqual(fee(60), 400)
        self.assertEqual(fee(61), 800)

    def test_one_day_is_capped(self):
        self.assertEqual(fee(11 * 60), 4000)
        self.assertEqual(fee(24 * 60 - 1), 4000)

    def test_second_day_starts_a_new_cap(self):
        self.assertEqual(fee(24 * 60 + 61), 4000 + 800)

    def test_negative_minutes_are_rejected(self):
        with self.assertRaises(ValueError):
            fee(-1)


if __name__ == "__main__":
    unittest.main()
