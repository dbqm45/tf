#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/schema_scan.py: tabele, kolumny, ograniczenia i powiązania z migracji SQL
(w tym Flyway) oraz encji JPA i EF Core — z miejscem plik:linia. python3 .claude/tests/test_schema_scan.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts" / "schema_scan.py"

REPO = {
    "db/migration/V1__init.sql":
        "-- konta\nCREATE TABLE customer (\n  id BIGINT PRIMARY KEY,\n  email VARCHAR(200) NOT NULL UNIQUE,\n"
        "  status VARCHAR(20) NOT NULL CHECK (status IN ('ACTIVE','BLOCKED'))\n);\n"
        "CREATE TABLE IF NOT EXISTS \"invoice\" (\n  id BIGINT PRIMARY KEY,\n"
        "  customer_id BIGINT NOT NULL REFERENCES customer(id),\n  total NUMERIC(12,2) NOT NULL\n);\n",
    "db/migration/V2__invoice_due.sql":
        "ALTER TABLE invoice ADD COLUMN due_date DATE NOT NULL;\n"
        "ALTER TABLE invoice ADD CONSTRAINT total_positive CHECK (total > 0);\n",
    "src/main/java/a/Order.java":
        "package a;\nimport jakarta.persistence.*;\nimport jakarta.validation.constraints.*;\n\n@Entity\n"
        "@Table(name = \"orders\")\npublic class Order {\n  @Id\n  private Long id;\n"
        "  @Column(nullable = false, length = 3)\n  private String currency;\n  @NotNull @Size(max = 50)\n"
        "  private String number;\n  @ManyToOne\n  private Customer customer;\n}\n",
    "src/main/java/a/NotEntity.java": "package a;\npublic class NotEntity { private String x; }\n",
    "Shop/ShopContext.cs":
        "using Microsoft.EntityFrameworkCore;\npublic class ShopContext : DbContext {\n"
        "  public DbSet<Product> Products { get; set; }\n}\n",
    "Shop/Product.cs":
        "using System.ComponentModel.DataAnnotations;\n[Table(\"product\")]\npublic class Product {\n"
        "  [Key] public int Id { get; set; }\n  [Required, MaxLength(80)] public string Name { get; set; }\n"
        "  public Category Category { get; set; }\n}\n",
}


def write(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60,
                          stdin=subprocess.DEVNULL)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        write(repo, REPO)
        r = run(str(repo), "--json")
        check(r.returncode == 0, f"D-1: działa: {r.stderr[-300:]}")
        out = json.loads(r.stdout) if r.returncode == 0 else {}
        t = {x["name"]: x for x in out.get("tables", [])}
        check({"customer", "invoice", "orders", "product"} <= set(t) and "notentity" not in {k.lower() for k in t},
              f"D-2: tabele z SQL, JPA (@Table) i EF ([Table]): {sorted(t)}")
        cust = t.get("customer", {})
        check(cust.get("source") == "sql" and cust.get("at") == "db/migration/V1__init.sql:2", f"D-3: miejsce tabeli: {cust}")
        cols = {c["name"]: c for c in cust.get("columns", [])}
        check({"primary key"} <= set(cols.get("id", {}).get("constraints", []))
              and {"not null", "unique"} <= set(cols.get("email", {}).get("constraints", [])),
              f"D-4: ograniczenia kolumn: {cols}")
        check(any("ACTIVE" in c for c in cols.get("status", {}).get("constraints", [])), f"D-5: CHECK w kolumnie: {cols.get('status')}")
        inv = t.get("invoice", {})
        check(inv.get("references") == ["customer"], f"D-6: klucz obcy invoice → customer: {inv.get('references')}")
        icols = {c["name"]: c for c in inv.get("columns", [])}
        check("due_date" in icols and icols["due_date"].get("at") == "db/migration/V2__invoice_due.sql:1",
              f"D-7: ALTER TABLE ADD COLUMN z miejscem: {icols.get('due_date')}")
        rules = out.get("rules", [])
        check(any(x["table"] == "invoice" and "total > 0" in x["rule"] and x["at"] == "db/migration/V2__invoice_due.sql:2"
                  for x in rules), f"D-8: reguła z ADD CONSTRAINT CHECK: {rules}")
        o = t.get("orders", {})
        ocols = {c["name"]: c for c in o.get("columns", [])}
        check(o.get("source") == "jpa" and "not null" in ocols.get("currency", {}).get("constraints", [])
              and "max 50" in ocols.get("number", {}).get("constraints", []), f"D-9: JPA kolumny: {o}")
        check(o.get("references") == ["Customer"], f"D-10: JPA relacja @ManyToOne: {o.get('references')}")
        p = t.get("product", {})
        pcols = {c["name"]: c for c in p.get("columns", [])}
        check(p.get("source") == "ef" and {"required", "max 80"} <= set(pcols.get("Name", {}).get("constraints", [])),
              f"D-11: EF kolumny: {p}")
        r = run(str(repo))
        check(r.returncode == 0 and "invoice" in r.stdout and "V2__invoice_due.sql:2" in r.stdout, f"D-12: tekst: {r.stdout[:400]}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów schema_scan")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
