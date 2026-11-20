#!/usr/bin/env python3
"""Tests of eng-codebase-mapping/scripts/recon_export.py: export of the reconstruction from code as JSON (F2 of the pdi integration) —
rules, requirements and the domain glossary from Markdown files with file:line evidence, modules from the cards, the commit from the manifest,
stable identifiers and an evidence check with --repo. python3 .claude/tests/test_recon_export.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPTS = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts"
SCRIPT = SCRIPTS / "recon_export.py"

CODE = {
    "src/billing/invoice.py": "def total(lines):\n    # faktura bez pozycji jest błędem\n"
                              "    if not lines:\n        raise ValueError('empty')\n    return sum(lines)\n",
    "src/billing/model.py": "class CreditNote:\n    pass\n",
    "tests/test_invoice.py": "def test_empty_invoice_rejected():\n    assert True\n",
}
RULES = """# Reguły z kart modułów
Złożone skryptem z `modules/*.json`; reguły przekrojowe i mapowania dopisuje synteza poniżej.

## billing (details: modules/billing.md)
- Faktura bez pozycji jest odrzucana. `src/billing/invoice.py:3-4` "raise ValueError" (confidence: test)
- Kwota faktury to suma pozycji. `src/billing/invoice.py:5` (confidence: kod)

## Reguły przekrojowe
- Stawka VAT jest stała [assumption: nie znaleziono konfiguracji]
"""
REQUIREMENTS = """# Wymagania odtworzone z kodu

## Faktury
- System odrzuca fakturę bez pozycji — `tests/test_invoice.py:1` (confidence: test)
- Korekta faktury zmniejsza należność — `src/billing/model.py:1`, `src/billing/invoice.py:5` (confidence: do potwierdzenia)
- Faktura ma numer nadawany przez system księgowy [question] — skąd numeracja?
"""
DOMAIN = """# Domena

## Subdomeny
- Rozliczenia (core): faktury i korekty — `src/billing/invoice.py:1`

## Słownik
| Termin | Nazwa w kodzie | Dowód |
|---|---|---|
| korekta | CreditNote | `src/billing/model.py:1` |
| faktura | invoice | `src/billing/invoice.py:99` |
"""
CARD = {"module": "billing", "batch": "src/billing", "purpose": "Wystawia faktury.",
        "entry_points": [{"what": "total()", "evidence": "src/billing/invoice.py:1"}], "rules": [], "terms": []}


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60, cwd=cwd)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        for rel, text in CODE.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding="utf-8")
        rec = repo / "docs" / "project" / "00-reconstruction"
        (rec / "modules").mkdir(parents=True)
        (rec / "rules.md").write_text(RULES, encoding="utf-8")
        (rec / "requirements.md").write_text(REQUIREMENTS, encoding="utf-8")
        (rec / "domain.md").write_text(DOMAIN, encoding="utf-8")
        (rec / "modules" / "billing.json").write_text(json.dumps(CARD, ensure_ascii=False), encoding="utf-8")
        (rec / "manifest.json").write_text(json.dumps({"commit": "abc1234def", "date": "2026-10-26"}), encoding="utf-8")

        r = run(str(rec), "--repo", str(repo))
        out_path = rec / "reconstruction.json"
        data = json.loads(out_path.read_text(encoding="utf-8")) if out_path.is_file() else {}
        check(r.returncode == 0 and data.get("format") == "tf-reconstruction" and data.get("format_version") == 1
              and data.get("commit") == "abc1234def", f"E-1: reconstruction.json obok rules.md z commitem z manifestu: "
                                                     f"{r.stdout}{r.stderr}")
        rules, reqs, dom = data.get("rules", []), data.get("requirements", []), data.get("domain", [])
        check(len(rules) == 3 and len(reqs) == 3 and len(dom) == 3, f"E-2: number of items: {len(rules)}/{len(reqs)}/{len(dom)}")
        r1 = rules[0] if rules else {}
        check(r1.get("text") == "Faktura bez pozycji jest odrzucana." and r1.get("module") == "billing"
              and r1.get("quote") == "raise ValueError" and r1.get("confidence") == "test" and r1.get("status") == "evidence"
              and r1.get("evidence") == [{"path": "src/billing/invoice.py", "line": 3, "line_end": 4, "verified": True}]
              and r1.get("source") == "rules.md:5", f"E-3: a rule with a module, a quote, confidence and a line range: {r1}")
        cross = rules[2] if len(rules) > 2 else {}
        check(cross.get("section") == "Reguły przekrojowe" and cross.get("module") is None
              and cross.get("status") == "assumption" and cross.get("evidence") == [],
              f"E-4: a cross-cutting rule without evidence with the [assumption] marker: {cross}")
        two = reqs[1] if len(reqs) > 1 else {}
        check(two.get("text") == "Korekta faktury zmniejsza należność" and len(two.get("evidence", [])) == 2
              and two.get("confidence") == "do potwierdzenia" and two.get("section") == "Faktury",
              f"E-5: a requirement with two pieces of evidence and confidence: {two}")
        check((reqs[2] if len(reqs) > 2 else {}).get("status") == "question", f"E-6: [question] → status question: {reqs[-1:]}")
        rows = [d for d in dom if d.get("cells")]
        check(len(rows) == 2 and rows[0]["cells"].get("Termin") == "korekta" and rows[0]["cells"].get("Nazwa w kodzie") == "CreditNote"
              and rows[0]["evidence"][0]["verified"] is True,
              f"E-7: glossary rows from the table (columns as cells): {rows}")
        check(len(rows) == 2 and rows[1]["evidence"][0]["verified"] is False,
              f"E-8: evidence beyond the file (line 99) → verified false: {rows[1:]}")
        ids = [i.get("id", "") for i in rules + reqs + dom]
        check(all(ids) and len(set(ids)) == len(ids) and all(i.startswith(("rules-", "requirements-", "domain-")) for i in ids),
              f"E-9: unikalne identyfikatory z rodzajem: {ids}")
        mods = data.get("modules", [])
        check(mods == [{"module": "billing", "purpose": "Wystawia faktury.", "card": "modules/billing.json"}],
              f"E-10: modules from the cards: {mods}")

        (rec / "rules.md").write_text(RULES.replace("## billing", "Nowa linia na górze.\n\n## billing"), encoding="utf-8")
        run(str(rec), "--repo", str(repo))
        moved = json.loads(out_path.read_text(encoding="utf-8"))["rules"]
        check([i["id"] for i in moved] == [i["id"] for i in rules] and moved[0]["source"] != r1.get("source"),
              "E-11: the identifier is stable after the lines shift (the source changes)")

        r = run(str(rec))
        noverify = json.loads(out_path.read_text(encoding="utf-8"))
        check(r.returncode == 0 and all("verified" not in e for i in noverify["rules"] for e in i["evidence"]),
              "E-12: without --repo the evidence is not checked (no verified field)")
        r = run(str(rec), "--out", str(repo / "x.json"))
        check(r.returncode == 0 and (repo / "x.json").is_file(), f"E-13: --out: {r.stdout}{r.stderr}")
        # English markers (14.x, e.g. from recon_cards.py) give the same status as the Polish ones
        (rec / "rules.md").write_text("# Rules\n\n## X\n- A [unverified: no evidence in the card]\n- B [assumption]\n"
                                      "- C [question]\n", encoding="utf-8")
        run(str(rec), "--out", str(repo / "en.json"))
        st = [i["status"] for i in json.loads((repo / "en.json").read_text(encoding="utf-8"))["rules"]]
        check(st == ["unverified", "assumption", "question"], f"E-16: angielskie znaczniki → status: {st}")
        r = run(str(repo / "nie-ma"))
        check(r.returncode == 2 and "Traceback" not in r.stderr, f"E-14: missing directory → 2: {r.returncode} {r.stderr[-200:]}")

        schema = json.loads((SCRIPTS / "reconstruction-export.schema.json").read_text(encoding="utf-8")) \
            if (SCRIPTS / "reconstruction-export.schema.json").is_file() else {}
        item_keys = set(schema.get("$defs", {}).get("item", {}).get("properties", {}))
        top_keys = set(schema.get("properties", {}))
        check(top_keys and set(data) <= top_keys and set(schema.get("required", [])) <= set(data)
              and all(set(i) <= item_keys for i in rules + reqs + dom),
              f"E-15: the result has only fields from the schema: {set(data) - top_keys} {item_keys}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the reconstruction export")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
