#!/usr/bin/env python3
"""Testy lintera polszczyzny: python3 tests/test_polish_lint.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

LINT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir()) / ".claude/skills/txt-polish-correctness/scripts/polish_lint.py"

BAD = [  # (tekst, oczekiwana kategoria)
    ("To napewno zadziała, bo wiem.", "SPELLING"),
    ("Wiem że system działa poprawnie.", "PUNCTUATION"),
    ("Moduł pełni rolę bramy do usług.", "COLLOCATION"),
    ("Proces trzeba kontynuować dalej jutro.", "PLEONASM"),
    ("Zwiększyła się ilość użytkowników w systemie.", "COLLOCATION"),
    ("Kliknij \"Zapisz\" na dole ekranu, żeby zakończyć.", "TYPOGRAPHY"),
    ("Wdrożenie - jak zawsze - zajęło godzinę.", "TYPOGRAPHY"),
    ("Proszę wybrać tą opcję z listy.", "GRAMMAR"),
    ("Trzeba zaadresować problem wydajności.", "CALQUE"),
    ("Na dzień dzisiejszy nie mamy danych.", "STYLE"),
    ("\n# Aplikacja Rezerwacji Sal Konferencyjnych", "SPELLING"),
    ("Test może zawodzić mimo że kod jest dobry.", "PUNCTUATION"),
]
GOOD = [
    "Wiem, że system działa, i wiem, który moduł odpowiada za zapis.",
    "Dokument, w którym opisano decyzję, jest w repozytorium.",
    "Test może zawodzić, mimo że kod jest dobry.",
    "Moduł odgrywa rolę bramy; w każdym razie tak było do wersji 2.",
    "Liczba użytkowników wzrosła o 10 000 w latach 2024–2026.",
    "Kliknij „Zapisz”, aby zakończyć – to wszystko.",
    "Sprawdź, czy plik istnieje, i uruchom `npm test -- --run` w kodzie: `x = \"a\"`.",
    "Wybierz tę opcję i przejdź dalej.",
    "- punkt listy z łącznikiem na początku",
    "\n## Mapa kontekstów dla Sprzedaży",
]


def lint(text: str, name: str = "t.md") -> list[dict]:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / name
        f.write_text(text + "\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(LINT), str(f), "--json"], capture_output=True, text=True, timeout=20)
        return json.loads(r.stdout)


def main() -> int:
    fails = []
    for text, cat in BAD:
        got = {i["category"] for i in lint("Źródło: " + text)}
        if cat not in got:
            fails.append(f"did not detect {cat}: {text!r} (got {got})")
    for text in GOOD:
        got = [i for i in lint("Zażółć gęślą jaźń. " + text) if i["priority"] != "LOW" or i["category"] != "PUNCTUATION"]
        if got:
            fails.append(f"false alarm: {text!r} → {[(i['category'], i['fragment']) for i in got]}")
    code = "Zażółć.\n```\nWiem że \"to\" napewno - kod\n```\n"
    if lint(code):
        fails.append("a code block should be skipped")
    if lint("<!-- polish-lint: ignore-file -->\nTo napewno błąd, ąę."):
        fails.append("ignore-file")
    if lint("I know that it works - english only."):
        fails.append("text without Polish characters should be skipped")
    total = len(BAD) + len(GOOD) + 3
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the Polish linter")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
