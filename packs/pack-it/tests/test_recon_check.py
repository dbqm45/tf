#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/recon_check.py: dowody plik:linia w raporcie (plik istnieje, linia w zakresie,
cytat zgodny z kodem ±2 linie), twierdzenia bez dowodu i sekcje raportu końcowego. python3 .claude/tests/test_recon_check.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts" / "recon_check.py"

CODE = {
    "src/billing/invoice.py": "def total(lines):\n    # faktura bez pozycji jest błędem\n"
                              "    if not lines:\n        raise ValueError('empty')\n    return sum(lines)\n",
    "src/billing/tax.py": "RATE = 0.23\n",
}

GOOD = """# Rekonstrukcja
## TL;DR
Faktura musi mieć pozycje (`src/billing/invoice.py:3-4`).
## Stack
- Python [założenie: brak pliku budowania]
## Moduły
- billing: liczy faktury — `src/billing/invoice.py:1`
## Domeny
- Fakturowanie — `src/billing/invoice.py:1`
## Wymagania
- Pusta faktura jest odrzucana — `src/billing/invoice.py:4` "raise ValueError('empty')"
## Reguły
- VAT 23% — `src/billing/tax.py:1` „RATE = 0.23”
## Standardy
- [niezweryfikowane] snake_case w nazwach plików
## Ryzyka
- Brak testów modułu billing — `src/billing/invoice.py:1`
## Pytania
- [pytanie] Czy stawka VAT zależy od kraju?
## Czego nie sprawdzono
- Konfiguracja wdrożenia.
"""

BAD = """# Rekonstrukcja
## Reguły
- Rabat 10% dla stałych klientów — `src/billing/discount.py:5`
- VAT liczony od netto — `src/billing/tax.py:40`
- Pusta faktura dozwolona — `src/billing/invoice.py:4` "return 0"
- Faktury wystawia się w EUR
"""


def write(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60,
                          stdin=subprocess.DEVNULL, cwd=cwd)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        write(repo, CODE)
        write(repo, {"docs/project/00-reconstruction/report.md": GOOD, "bad.md": BAD})
        r = run("docs/project/00-reconstruction/report.md", "--repo", str(repo), "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("refs") == 6 and out.get("bad") == [], f"R-1: poprawny raport: {r.stdout[:500]}")
        check(out.get("unsupported") == [], f"R-2: twierdzenia oznaczone [założenie]/[pytanie] nie są bez dowodu: {out.get('unsupported')}")
        r = run("bad.md", "--repo", str(repo), "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        why = {b["ref"]: b["problem"] for b in out.get("bad", [])}
        check(r.returncode == 1, f"R-3: złe dowody → kod 1: rc={r.returncode}")
        check(why.get("src/billing/discount.py:5") == "brak pliku", f"R-4: brak pliku: {why}")
        check(why.get("src/billing/tax.py:40") == "linia poza plikiem (1)", f"R-5: linia poza plikiem: {why}")
        check(why.get("src/billing/invoice.py:4") == "cytat nie pasuje do linii 2–5", f"R-6: cytat niezgodny: {why}")
        uns = out.get("unsupported", [])
        check(len(uns) == 1 and "EUR" in uns[0]["text"] and uns[0]["at"] == "bad.md:6", f"R-7: twierdzenie bez dowodu: {uns}")
        r = run("docs/project/00-reconstruction/report.md", "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 0, f"R-8: --final na kompletnym raporcie: {r.stdout[-400:]}")
        r = run("bad.md", "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 1 and "TL;DR" in r.stdout and "Czego nie sprawdzono" in r.stdout,
              f"R-9: --final wymienia brakujące sekcje: {r.stdout[-500:]}")
        r = run("docs/project/00-reconstruction", "--repo", str(repo), cwd=d)
        check(r.returncode == 0 and "Dowody: 6," in r.stdout, f"R-10: katalog raportu: {r.stdout[-300:]}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów recon_check")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
