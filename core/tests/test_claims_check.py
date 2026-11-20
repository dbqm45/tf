#!/usr/bin/env python3
"""Tests of `.claude/skills/core-grounding/scripts/claims_check.py` (a reviewer of numbers in documents: the arithmetic of
"X/Y (Z%)", dates, numbers with no trace of origin) without a network and without a model. python3 tests/test_claims_check.py"""
import datetime as dt
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "core-grounding" / "scripts" / "claims_check.py"

TOMORROW = (dt.date.today() + dt.timedelta(days=2)).isoformat()

DOC = f"""# Raport pomiaru

| Zbiór | Ze skillami | Bez skilli |
|---|---|---|
| strojenie | 46/48 (96%) | 22/48 (46%) |
| holdout | 45/56 (85%) | 37/56 (66%) |

Koszt pomiaru wyniósł 21,07 USD (`docs/evals/raport.jsonl`).
Skuteczność wzrosła o 30% po zmianie opisu.
Według źródła https://example.org/raport czas odpowiedzi spadł o 120 ms.
Szacunek: 40% użytkowników nie zauważy zmiany [assumption].
Bramka uruchomiona 2026-02-30 na gałęzi roboczej.
Stan na {TOMORROW}: wszystkie testy przechodzą (`pytest -q`).

```
przykład 1/2 (99%) w bloku kodu — pomijany
```
"""

CLEAN = """# Raport

| Zbiór | Wynik |
|---|---|
| holdout | 45/56 (80%) |

Koszt: 2,31 USD (`docs/evals/raport.jsonl`).
"""


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=60)


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    if not SCRIPT.is_file():
        print(f"✗ missing {SCRIPT}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        (d / "report.md").write_text(DOC, encoding="utf-8")
        (d / "czysty.md").write_text(CLEAN, encoding="utf-8")
        r = run(["report.md"], d)
        out = r.stdout
        lines = out.splitlines()
        check(r.returncode == 1 and lines and lines[0].startswith("Verdict: ERRORS"),
              f"C-1: errors -> code 1 and the verdict on the first line: {out}")
        check("report.md:6" in out and "45/56" in out and "80%" in out,
              f"C-2: a wrong percentage at 45/56 pointed out with file:line and the correct value: {out}")
        check("report.md:5" not in out, f"C-3: correct 46/48 (96%) and 22/48 (46%) with no remarks: {out}")
        check("2026-02-30" in out, f"C-4: an invalid date detected: {out}")
        check(TOMORROW in out and "future" in out, f"C-5: a future 'as of' date detected: {out}")
        check("report.md:9" in out and "30%" in out and "WARNING" in out.upper(),
              f"C-6: a number without a source in a paragraph -> a warning: {out}")
        check("report.md:8" not in out and "report.md:10" not in out and "report.md:11" not in out,
              f"C-7: numbers with a source (path, URL) and marked [assumption] with no remarks: {out}")
        check("99%" not in out, f"C-8: code blocks skipped: {out}")
        r = run(["czysty.md"], d)
        check(r.returncode == 0 and r.stdout.startswith("Verdict: OK"), f"C-9: a clean document -> OK, code 0: {r.stdout}")
        (d / "tylko-ostrzezenia.md").write_text("Liczba sesji wzrosła o 12%.\n", encoding="utf-8")
        r = run(["tylko-ostrzezenia.md"], d)
        check(r.returncode == 0 and r.stdout.startswith("Verdict: WARNINGS"),
              f"C-10: warnings only -> code 0 and the WARNINGS verdict: {r.stdout}")
        r = run(["tylko-ostrzezenia.md", "--strict"], d)
        check(r.returncode == 1, f"C-11: --strict treats warnings as errors: {r.stdout}")
        (d / "kat").mkdir()
        (d / "kat" / "a.md").write_text(DOC, encoding="utf-8")
        (d / "kat" / "b.md").write_text(CLEAN, encoding="utf-8")
        r = run(["kat"], d)
        check(r.returncode == 1 and "kat/a.md:6" in r.stdout.replace("\\", "/") and "b.md" not in r.stdout,
              f"C-12: a directory checked recursively, results with file:line: {r.stdout}")
        (d / "z-deklaracja.md").write_text("# Pomiar\n\n- **Pliki:** surowe wyniki w `pomiar.jsonl`.\n\n"
                                           "Koszt wyniósł 21,07 USD, wynik wzrósł o 12%.\n", encoding="utf-8")
        r = run(["z-deklaracja.md"], d)
        check(r.returncode == 0 and r.stdout.startswith("Verdict: OK"),
              f"C-13: a document's data source declaration (Pliki:/Źródło danych: with a `path`) covers the numbers: {r.stdout}")
        (d / "inline.md").write_text("# Pomiar\n\nPowtórzenie testu. Dane: `wyniki/v2/`, skrypty obok.\n\n"
                                     "Koszt 5,38 USD, pokrycie 90%.\n", encoding="utf-8")
        r = run(["inline.md"], d)
        check(r.returncode == 0 and r.stdout.startswith("Verdict: OK"),
              f"C-14: a 'Dane: `path`' declaration in the middle of a sentence also covers the document's numbers: {r.stdout}")
        (d / "bez.md").write_text("# Pomiar\n\nNie mamy danych: wynik 5 USD.\n", encoding="utf-8")
        r = run(["bez.md"], d)
        check(r.stdout.startswith("Verdict: WARNINGS"), f"C-15: the word 'danych' without a path is not a declaration: {r.stdout}")
        (d / "en.md").write_text("# Measurement\n\nAbout 40% of users will not notice [assumption].\n"
                                 "Latency dropped by 120 ms according to the vendor.\n"
                                 "Coverage is 70% [unverified].\n"
                                 f"As of {TOMORROW}: all tests pass.\n", encoding="utf-8")
        r = run(["en.md"], d)
        check("en.md:3" not in r.stdout and "en.md:4" not in r.stdout and "en.md:5" not in r.stdout
              and "en.md:6" in r.stdout,
              f"C-16: English markers [assumption]/[unverified], 'according to' and a future 'As of' date: {r.stdout}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} number reviewer tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
