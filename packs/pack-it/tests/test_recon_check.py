#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/recon_check.py: dowody plik:linia w raporcie (plik istnieje, linia w zakresie,
cytat zgodny z kodem ±2 linie), twierdzenia bez dowodu i sekcje raportu końcowego. python3 .claude/tests/test_recon_check.py"""
import hashlib
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
| Obszar | Ustalenie | Dowód |
|---|---|---|
| Język | Python 3 | [założenie: brak pliku budowania] |
| Framework | brak — biblioteka standardowa | `src/billing/invoice.py:1` |
| Dane | brak bazy danych [niezweryfikowane] | — |
| Build | brak pliku budowania [założenie] | — |
| Testy | brak testów [niezweryfikowane] | — |
| CI | brak konfiguracji CI [niezweryfikowane] | — |
| Konfiguracja | stała w kodzie | `src/billing/tax.py:1` |
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


def card(rep: Path, stem: str, data: dict, md: bool = True) -> None:
    """Karta modules/<stem>.json i (opcjonalnie) jej aktualny modules/<stem>.md ze skrótem treści karty."""
    raw = json.dumps(data, ensure_ascii=False)
    write(rep, {f"modules/{stem}.json": raw})
    if md:
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
        write(rep, {f"modules/{stem}.md": f"<!-- karta: modules/{stem}.json sha256:{h} -->\n# {data['module']}\n"})


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
        check(r.returncode == 0 and out.get("refs") == 8 and out.get("bad") == [], f"R-1: poprawny raport: {r.stdout[:500]}")
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
        check(r.returncode == 0 and "Dowody: 8," in r.stdout, f"R-10: katalog raportu: {r.stdout[-300:]}")

        # --final: tabela stacku z wymaganymi wierszami i lista modułów zgodna z kartami
        rep = repo / "docs/project/00-reconstruction"
        card(rep, "billing", {"module": "billing"})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("stack_missing") == [] and out.get("modules_missing") == [],
              f"R-11: kompletny raport z tabelą stacku i modułami z kart: {r.stdout[-500:]}")
        no_ci = GOOD.replace("| CI | brak konfiguracji CI [niezweryfikowane] | — |\n", "").replace(
            "| Testy | brak testów [niezweryfikowane] | — |\n", "")
        write(rep, {"report.md": no_ci})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 1 and "stack: brak wierszy: Testy, CI" in r.stdout, f"R-12: brak wierszy stacku: {r.stdout[-500:]}")
        write(rep, {"report.md": GOOD.replace("| Konfiguracja | stała w kodzie | `src/billing/tax.py:1` |",
                                              "| Konfiguracja | stała w kodzie | — |")})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and any("Konfiguracja" in u["text"] for u in out.get("unsupported", [])),
              f"R-13: wiersz stacku bez dowodu i oznaczenia: {out.get('unsupported')}")
        write(rep, {"report.md": GOOD})
        card(rep, "customers", {"module": "customers"})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 1 and "moduły bez wpisu w sekcji Moduły: customers" in r.stdout,
              f"R-14: moduł z karty nieopisany w raporcie: {r.stdout[-500:]}")
        write(rep, {"report.md": no_ci})
        r = run(str(rep / "report.md"), "--repo", str(repo), cwd=d)
        check(r.returncode == 0, f"R-15: bez --final nowe kontrole nie działają: {r.stdout[-300:]}")

        # --final: każda karta ma aktualny modules/<karta>.md (recon_cards.py), skrót treści karty się zgadza
        (rep / "modules/customers.json").unlink()
        (rep / "modules/customers.md").unlink()
        write(rep, {"report.md": GOOD})
        (rep / "modules/billing.md").unlink()
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 1 and "karty bez aktualnego .md (recon_cards.py): billing" in r.stdout,
              f"R-16: karta bez .md: {r.stdout[-500:]}")
        card(rep, "billing", {"module": "billing"})
        write(rep, {"modules/billing.json": json.dumps({"module": "billing", "purpose": "zmiana"})})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("cards_stale") == ["billing"], f"R-17: .md starszy niż karta: {r.stdout[-500:]}")
        card(rep, "billing", {"module": "billing"})

        # --final: w repo są pliki pipeline'u, a wiersz CI nie wskazuje żadnego z nich
        write(repo, {".github/workflows/ci.yml": "name: ci\non: push\n"})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("ci_unreferenced") == [".github/workflows/ci.yml"],
              f"R-18: CI w repo, wiersz CI bez wskazania: {r.stdout[-500:]}")
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", cwd=d)
        check("CI: w repo są pliki pipeline'u, wiersz CI nie wskazuje żadnego: .github/workflows/ci.yml" in r.stdout,
              f"R-19: komunikat o CI: {r.stdout[-500:]}")
        write(rep, {"report.md": GOOD.replace("| CI | brak konfiguracji CI [niezweryfikowane] | — |",
                                              "| CI | GitHub Actions na push | `.github/workflows/ci.yml:2` |")})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("ci_unreferenced") == [], f"R-20: wiersz CI wskazuje plik pipeline'u: {r.stdout[-500:]}")
        write(rep, {"report.md": GOOD})
        r = run(str(rep / "report.md"), "--repo", str(repo), cwd=d)
        check(r.returncode == 0, f"R-21: bez --final kontrola CI nie działa: {r.stdout[-300:]}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów recon_check")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
