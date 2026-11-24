import unittest

from app.auth.permissions import can


class PermissionsTest(unittest.TestCase):
    def test_roles(self):
        self.assertTrue(can("viewer", "orders:read"))
        self.assertFalse(can("viewer", "orders:write"))
        self.assertTrue(can("admin", "users:manage"))

    def test_unknown_role(self):
        self.assertFalse(can("guest", "orders:read"))


if __name__ == "__main__":
    unittest.main()
