#!/usr/bin/env python3
"""Tests of eng-codebase-mapping/scripts/recon_check.py: file:line evidence in the report (the file exists, the line in range,
the quote matches the code ±2 lines), claims without evidence and the sections of the final report. python3 .claude/tests/test_recon_check.py"""
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

POLISH = """# Rekonstrukcja
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

PL_EN = (("## Moduły", "## Modules"), ("## Domeny", "## Domains"), ("## Wymagania", "## Requirements"),
         ("## Reguły", "## Rules"), ("## Standardy", "## Standards"), ("## Ryzyka", "## Risks"),
         ("## Pytania", "## Questions"), ("## Czego nie sprawdzono", "## Not checked"),
         ("| Język |", "| Language |"), ("| Dane |", "| Data |"), ("| Testy |", "| Tests |"),
         ("| Konfiguracja |", "| Configuration |"), ("[założenie", "[assumption"),
         ("[niezweryfikowane]", "[unverified]"), ("[pytanie", "[question"))
GOOD = POLISH   # the report in English sections and markers (the Polish ones from before 14.x: the 19.0.0 migration)
for _pl, _en in PL_EN:
    GOOD = GOOD.replace(_pl, _en)

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
    """The card modules/<stem>.json and (optionally) its current modules/<stem>.md with the card content digest."""
    raw = json.dumps(data, ensure_ascii=False)
    write(rep, {f"modules/{stem}.json": raw})
    if md:
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
        write(rep, {f"modules/{stem}.md": f"<!-- card: modules/{stem}.json sha256:{h} -->\n# {data['module']}\n"})


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
        check(r.returncode == 0 and out.get("refs") == 8 and out.get("bad") == [], f"R-1: a valid report: {r.stdout[:500]}")
        check(out.get("unsupported") == [], f"R-2: claims marked [assumption]/[question] are not without evidence: {out.get('unsupported')}")
        r = run("bad.md", "--repo", str(repo), "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        why = {b["ref"]: b["problem"] for b in out.get("bad", [])}
        check(r.returncode == 1, f"R-3: bad evidence → code 1: rc={r.returncode}")
        check(why.get("src/billing/discount.py:5") == "no such file", f"R-4: missing file: {why}")
        check(why.get("src/billing/tax.py:40") == "line outside the file (1)", f"R-5: line outside the file: {why}")
        check(why.get("src/billing/invoice.py:4") == "quote does not match lines 2–5", f"R-6: cytat niezgodny: {why}")
        uns = out.get("unsupported", [])
        check(len(uns) == 1 and "EUR" in uns[0]["text"] and uns[0]["at"] == "bad.md:6", f"R-7: a claim without evidence: {uns}")
        r = run("docs/project/00-reconstruction/report.md", "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 0, f"R-8: --final on a complete report: {r.stdout[-400:]}")
        (repo / "docs/project/00-reconstruction/report.md").write_text(POLISH, encoding="utf-8")
        r = run("docs/project/00-reconstruction/report.md", "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 1, f"R-8b: the Polish sections from before 14.x are no longer read (19.0.0 migrates them): {r.stdout[-400:]}")
        r = run("docs/project/00-reconstruction/report.md", "--repo", str(repo), "--json", cwd=d)
        check(json.loads(r.stdout).get("unsupported") != [],
              f"R-8c: the Polish markers no longer count as marks: {r.stdout[:400]}")
        (repo / "docs/project/00-reconstruction/report.md").write_text(GOOD, encoding="utf-8")
        r = run("bad.md", "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 1 and "TL;DR" in r.stdout and "Not checked" in r.stdout,
              f"R-9: --final lists the missing sections: {r.stdout[-500:]}")
        r = run("docs/project/00-reconstruction", "--repo", str(repo), cwd=d)
        check(r.returncode == 0 and "Evidence: 8," in r.stdout, f"R-10: the report directory: {r.stdout[-300:]}")

        # --final: a stack table with the required rows and a module list matching the cards
        rep = repo / "docs/project/00-reconstruction"
        card(rep, "billing", {"module": "billing"})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("stack_missing") == [] and out.get("modules_missing") == [],
              f"R-11: a complete report with the stack table and the modules from the cards: {r.stdout[-500:]}")
        no_ci = GOOD.replace("| CI | brak konfiguracji CI [unverified] | — |\n", "").replace(
            "| Tests | brak testów [unverified] | — |\n", "")
        write(rep, {"report.md": no_ci})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 1 and "stack: missing rows: Tests, CI" in r.stdout, f"R-12: missing stack rows: {r.stdout[-500:]}")
        write(rep, {"report.md": GOOD.replace("| Configuration | stała w kodzie | `src/billing/tax.py:1` |",
                                              "| Configuration | stała w kodzie | — |")})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and any("Configuration" in u["text"] for u in out.get("unsupported", [])),
              f"R-13: a stack row without evidence and a marker: {out.get('unsupported')}")
        write(rep, {"report.md": GOOD})
        card(rep, "customers", {"module": "customers"})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 1 and "modules with no entry in the Modules section: customers" in r.stdout,
              f"R-14: a module from a card not described in the report: {r.stdout[-500:]}")
        write(rep, {"report.md": no_ci})
        r = run(str(rep / "report.md"), "--repo", str(repo), cwd=d)
        check(r.returncode == 0, f"R-15: without --final the new checks do not run: {r.stdout[-300:]}")

        # --final: every card has a current modules/<card>.md (recon_cards.py), the card content digest matches
        (rep / "modules/customers.json").unlink()
        (rep / "modules/customers.md").unlink()
        write(rep, {"report.md": GOOD})
        (rep / "modules/billing.md").unlink()
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", cwd=d)
        check(r.returncode == 1 and "cards without an up-to-date .md (recon_cards.py): billing" in r.stdout,
              f"R-16: a card without .md: {r.stdout[-500:]}")
        card(rep, "billing", {"module": "billing"})
        write(rep, {"modules/billing.json": json.dumps({"module": "billing", "purpose": "zmiana"})})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("cards_stale") == ["billing"], f"R-17: .md older than the card: {r.stdout[-500:]}")
        card(rep, "billing", {"module": "billing"})

        # --final: the repo has pipeline files, and the CI row points to none of them
        write(repo, {".github/workflows/ci.yml": "name: ci\non: push\n"})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("ci_unreferenced") == [".github/workflows/ci.yml"],
              f"R-18: CI in the repo, the CI row without a pointer: {r.stdout[-500:]}")
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", cwd=d)
        check("CI: the repo has pipeline files, but the CI row points to none of them: .github/workflows/ci.yml" in r.stdout,
              f"R-19: the CI message: {r.stdout[-500:]}")
        write(rep, {"report.md": GOOD.replace("| CI | brak konfiguracji CI [unverified] | — |",
                                              "| CI | GitHub Actions na push | `.github/workflows/ci.yml:2` |")})
        r = run(str(rep / "report.md"), "--repo", str(repo), "--final", "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("ci_unreferenced") == [], f"R-20: the CI row points to a pipeline file: {r.stdout[-500:]}")
        write(rep, {"report.md": GOOD})
        r = run(str(rep / "report.md"), "--repo", str(repo), cwd=d)
        check(r.returncode == 0, f"R-21: without --final the CI check does not run: {r.stdout[-300:]}")

        # raw/ (refresh orders, working notes) is not part of the documentation checked for the directory
        write(rep, {"raw/refresh/STALE.md": "# Do sprawdzenia\n- opis bez dowodu w notatce roboczej\n- zły dowód `nie/ma.py:3`\n"})
        r = run(str(rep), "--repo", str(repo), "--json", cwd=d)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(not any("raw/" in u["at"] for u in out.get("unsupported", []) + out.get("bad", [])),
              f"R-22: raw/ skipped: {out.get('unsupported')} {out.get('bad')}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of recon_check")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
