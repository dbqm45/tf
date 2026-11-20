#!/usr/bin/env python3
"""Tests of ddd-archetype-lookup/scripts/archetype_scan.py: code signals of business archetypes (float money, balance
updated in place, role flags, hand-written overlap checks, waiting order by creation time, hard-coded discount rates,
address columns, branches on a product type), domain vocabulary per archetype, skipped directories, exit codes and the
JSON contract.
python3 .claude/tests/test_archetype_scan.py"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = next(p for p in HERE.parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "ddd-archetype-lookup" / "scripts" / "archetype_scan.py"

SHOP = {
    "src/main/java/shop/Order.java": (
        "package shop;\n"
        "public class Order {\n"
        "    private double totalPrice;\n"
        "    private String currency;\n"
        "    public double discounted() { return totalPrice * 0.85; }\n"
        "}\n"
    ),
    "src/main/java/shop/Company.java": (
        "public class Company {\n"
        "    boolean isSupplier;\n"
        "    boolean isCustomer;\n"
        "    String street; String city; String postalCode;\n"
        "}\n"
    ),
    "db/migrations/001_members.sql": (
        "CREATE TABLE members (id INT, points INT, amount FLOAT);\n"
        "UPDATE members SET points = points + 10 WHERE id = 1;\n"
    ),
    "app/rooms.py": (
        "def overlaps(a, b):\n"
        "    return a.start < b.end and b.start < a.end\n"
        "class Room:\n"
        "    is_reserved = False\n"
    ),
    "app/waitlist.py": (
        "WAITLIST_SQL = 'SELECT * FROM waitlist ORDER BY created_at'\n"
    ),
    "web/src/cart.ts": (
        "export interface Cart { total: number; }\n"
        "if (productType === 'bundle') { applyBundle(); }\n"
    ),
    "node_modules/lib/money.js": "var price = 0.1; let amount: number;\n",
    ".tf/factory/x.py": "balance += 1\n",
}


def put(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=cwd)


class ScanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def scan_json(self, *extra):
        r = run("--root", str(self.root), "--json", *extra)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        return r, json.loads(r.stdout)

    def test_signals_per_archetype(self):
        put(self.root, SHOP)
        r, data = self.scan_json()
        self.assertEqual(r.returncode, 0)
        by_signal = {}
        for f in data["findings"]:
            by_signal.setdefault(f["signal"], set()).add((f["file"], f["line"]))
        self.assertIn(("src/main/java/shop/Order.java", 3), by_signal["float-money"])
        self.assertIn(("db/migrations/001_members.sql", 1), by_signal["float-money"])
        self.assertIn(("web/src/cart.ts", 1), by_signal["float-money"])
        self.assertIn(("db/migrations/001_members.sql", 2), by_signal["balance-in-place"])
        self.assertIn(("src/main/java/shop/Company.java", 2), by_signal["role-flags"])
        self.assertIn(("src/main/java/shop/Company.java", 3), by_signal["role-flags"])
        self.assertIn(("app/rooms.py", 2), by_signal["overlap-check"])
        self.assertIn(("app/rooms.py", 4), by_signal["booking-flags"])
        self.assertIn(("app/waitlist.py", 1), by_signal["wait-order-by-time"])
        self.assertIn(("src/main/java/shop/Order.java", 5), by_signal["rate-literal"])
        self.assertIn(("src/main/java/shop/Company.java", 4), by_signal["address-fields"])
        self.assertIn(("web/src/cart.ts", 2), by_signal["type-branch"])
        archetypes = {f["signal"]: f["archetype"] for f in data["findings"]}
        self.assertEqual(archetypes["float-money"], "quantities-and-money")
        self.assertEqual(archetypes["balance-in-place"], "value-ledger")
        self.assertEqual(archetypes["role-flags"], "parties-and-relationships")
        self.assertEqual(archetypes["overlap-check"], "resource-holds")
        self.assertEqual(archetypes["wait-order-by-time"], "waiting-lists")
        self.assertEqual(archetypes["rate-literal"], "price-calculation")
        self.assertEqual(archetypes["address-fields"], "places-and-zones")
        self.assertEqual(archetypes["type-branch"], "product-definitions")

    def test_skips_dependencies_and_factory_files(self):
        put(self.root, SHOP)
        _, data = self.scan_json()
        files = {f["file"] for f in data["findings"]} | {v["file"] for v in data["vocabulary"]}
        self.assertFalse(any(x.startswith(("node_modules/", ".tf/")) for x in files), files)

    def test_vocabulary_points_to_areas(self):
        put(self.root, {
            "src/loyalty/LoyaltyPoints.kt": "class LoyaltyPoints { fun redeem() {} fun expire() {} }\n",
            "src/contracts/Amendment.cs": "public class Amendment { public Contract Contract; }\n",
        })
        _, data = self.scan_json()
        vocab = {(v["archetype"], v["file"]) for v in data["vocabulary"]}
        self.assertIn(("value-ledger", "src/loyalty/LoyaltyPoints.kt"), vocab)
        self.assertIn(("commitments", "src/contracts/Amendment.cs"), vocab)

    def test_summary_orders_archetypes_by_evidence(self):
        put(self.root, SHOP)
        _, data = self.scan_json()
        summary = data["summary"]
        self.assertEqual(summary[0]["archetype"], "quantities-and-money")
        counts = [s["findings"] for s in summary]
        self.assertEqual(counts, sorted(counts, reverse=True))
        self.assertTrue(all("reference" in s for s in summary))

    def test_known_false_positives(self):
        # an Address value object is the remedy, not the smell; a basket line quantity is not a balance;
        # vocabulary from tests and migrations only repeats the production code
        put(self.root, {
            "src/Orders/Address.cs": "public class Address { public string Street; public string City; }\n",
            "src/Basket/BasketItem.cs": "public void Add(int q) { Quantity += q; }\n",
            "tests/LoyaltyTests.cs": "class LoyaltyTests { void Points() { var ledger = new Ledger(); } }\n",
            "db/migrations/002_loyalty.cs": "class AddLoyaltyPoints { void Ledger() {} }\n",
        })
        _, data = self.scan_json()
        self.assertEqual(data["findings"], [])
        self.assertEqual({v["file"] for v in data["vocabulary"]}, {"src/Orders/Address.cs"})

    def test_noise_found_on_a_real_shop(self):
        put(self.root, {
            "shop/variants.py": "stocks_to_create += [stock]\n",
            "shop/listing.py": "is_available = True\nqs.exclude(discount_amount=0.0)\n",
            "shop/tasks.py": "QUEUE = 'default'\nOrder.objects.order_by('created_at')\n",
            "shop/tests/test_cards.py": "old = float(card.balance.amount)\n",
        })
        _, data = self.scan_json()
        self.assertEqual(data["findings"], [])
        _, data = self.scan_json("--include-tests")
        self.assertEqual({(f["file"], f["signal"]) for f in data["findings"]},
                         {("shop/tests/test_cards.py", "float-money")})

    def test_files_filter(self):
        put(self.root, SHOP)
        _, data = self.scan_json("--files", "app/rooms.py")
        self.assertEqual({f["file"] for f in data["findings"]}, {"app/rooms.py"})

    def test_no_signals_exit_1(self):
        put(self.root, {"src/parser.c": "int parse(char *s) { return 0; }\n", "README.md": "price is a double\n"})
        r, data = self.scan_json()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(data["findings"], [])

    def test_empty_repo_text_report(self):
        r = run("--root", str(self.root))
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.startswith("Archetype scan: 0 code files"), r.stdout)

    def test_text_report_first_line(self):
        put(self.root, SHOP)
        r = run("--root", str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        first = r.stdout.splitlines()[0]
        self.assertRegex(first, r"^Archetype scan: \d+ code files, \d+ findings, \d+ archetypes$")
        self.assertIn("quantities-and-money", r.stdout)
        self.assertIn("src/main/java/shop/Order.java:3", r.stdout)

    def test_bad_root_exit_2(self):
        r = run("--root", str(self.root / "missing"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("not a directory", r.stderr)

    def test_limit_per_signal_in_text(self):
        put(self.root, {f"src/m{i}.ts": "let price: number;\n" for i in range(12)})
        r = run("--root", str(self.root), "--limit", "3")
        self.assertEqual(r.returncode, 0)
        self.assertIn("… 9 more", r.stdout)


if __name__ == "__main__":
    unittest.main()
