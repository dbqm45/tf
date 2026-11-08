#!/usr/bin/env python3
"""Testy `.claude/skills/core-grounding/scripts/claims_check.py` (recenzent liczb w dokumentach: arytmetyka
„X/Y (Z%)”, daty, liczby bez śladu pochodzenia) bez sieci i bez modelu. python3 tests/test_claims_check.py"""
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
Szacunek: 40% użytkowników nie zauważy zmiany [założenie].
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
        print(f"✗ brak {SCRIPT}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        (d / "raport.md").write_text(DOC, encoding="utf-8")
        (d / "czysty.md").write_text(CLEAN, encoding="utf-8")
        r = run(["raport.md"], d)
        out = r.stdout
        lines = out.splitlines()
        check(r.returncode == 1 and lines and lines[0].startswith("Werdykt: BŁĘDY"),
              f"C-1: błędy → kod 1 i werdykt w pierwszej linii: {out}")
        check("raport.md:6" in out and "45/56" in out and "80%" in out,
              f"C-2: zły procent przy 45/56 wskazany z plik:linia i wartością poprawną: {out}")
        check("raport.md:5" not in out, f"C-3: poprawne 46/48 (96%) i 22/48 (46%) bez uwag: {out}")
        check("2026-02-30" in out, f"C-4: niepoprawna data wykryta: {out}")
        check(TOMORROW in out and "przyszło" in out, f"C-5: data stanu w przyszłości wykryta: {out}")
        check("raport.md:9" in out and "30%" in out and "OSTRZEŻENIE" in out.upper(),
              f"C-6: liczba bez źródła w akapicie → ostrzeżenie: {out}")
        check("raport.md:8" not in out and "raport.md:10" not in out and "raport.md:11" not in out,
              f"C-7: liczby ze źródłem (ścieżka, URL) i oznaczone [założenie] bez uwag: {out}")
        check("99%" not in out, f"C-8: bloki kodu pomijane: {out}")
        r = run(["czysty.md"], d)
        check(r.returncode == 0 and r.stdout.startswith("Werdykt: OK"), f"C-9: czysty dokument → OK, kod 0: {r.stdout}")
        (d / "tylko-ostrzezenia.md").write_text("Liczba sesji wzrosła o 12%.\n", encoding="utf-8")
        r = run(["tylko-ostrzezenia.md"], d)
        check(r.returncode == 0 and r.stdout.startswith("Werdykt: OSTRZEŻENIA"),
              f"C-10: same ostrzeżenia → kod 0 i werdykt OSTRZEŻENIA: {r.stdout}")
        r = run(["tylko-ostrzezenia.md", "--strict"], d)
        check(r.returncode == 1, f"C-11: --strict traktuje ostrzeżenia jak błędy: {r.stdout}")
        (d / "kat").mkdir()
        (d / "kat" / "a.md").write_text(DOC, encoding="utf-8")
        (d / "kat" / "b.md").write_text(CLEAN, encoding="utf-8")
        r = run(["kat"], d)
        check(r.returncode == 1 and "kat/a.md:6" in r.stdout.replace("\\", "/") and "b.md" not in r.stdout,
              f"C-12: katalog sprawdzany rekurencyjnie, wyniki z plik:linia: {r.stdout}")
        (d / "z-deklaracja.md").write_text("# Pomiar\n\n- **Pliki:** surowe wyniki w `pomiar.jsonl`.\n\n"
                                           "Koszt wyniósł 21,07 USD, wynik wzrósł o 12%.\n", encoding="utf-8")
        r = run(["z-deklaracja.md"], d)
        check(r.returncode == 0 and r.stdout.startswith("Werdykt: OK"),
              f"C-13: deklaracja źródła danych dokumentu (Pliki:/Źródło danych: z `ścieżką`) obejmuje liczby: {r.stdout}")
        (d / "inline.md").write_text("# Pomiar\n\nPowtórzenie testu. Dane: `wyniki/v2/`, skrypty obok.\n\n"
                                     "Koszt 5,38 USD, pokrycie 90%.\n", encoding="utf-8")
        r = run(["inline.md"], d)
        check(r.returncode == 0 and r.stdout.startswith("Werdykt: OK"),
              f"C-14: deklaracja „Dane: `ścieżka`” w środku zdania też obejmuje liczby dokumentu: {r.stdout}")
        (d / "bez.md").write_text("# Pomiar\n\nNie mamy danych: wynik 5 USD.\n", encoding="utf-8")
        r = run(["bez.md"], d)
        check(r.stdout.startswith("Werdykt: OSTRZEŻENIA"), f"C-15: słowo „danych” bez ścieżki to nie deklaracja: {r.stdout}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów recenzenta liczb")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
