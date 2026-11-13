import io
import unittest
from contextlib import redirect_stdout

from parking.cli import main


class CliTest(unittest.TestCase):
    def test_prints_the_fee_in_zloty(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["cli", "61"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(), "8,00 zł")

    def test_usage_on_bad_input(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["cli", "abc"]), 2)


if __name__ == "__main__":
    unittest.main()
