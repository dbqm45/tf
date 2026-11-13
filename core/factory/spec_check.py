#!/usr/bin/env python3
"""
Specyfikacja zadania sprawdzana skryptem (krok D osi przebiegu): `docs/project/changes/<KEY>/spec.md`.

  tf spec new <KEY>                 # szablon spec.md z tytułem zadania (nie nadpisuje istniejącego)
  tf spec check <KEY> [--json]      # czy specyfikacja jest gotowa do planu

Format pliku (bez nagłówka artefaktu — stan pliku trzyma task.json):

  # Specyfikacja: <tytuł>
  ## Kryteria          - AC-1: Zakładając <stan>, gdy <jedna akcja>, wtedy <obserwowalny wynik>.
  ## Bez zmian         co ma działać jak dotąd (albo „brak, bo …”)
  ## Poza zakresem     czego historyjka nie obejmuje (albo „brak, bo …”)
  ## Otwarte pytania   pytanie, bez którego nie da się zacząć, ma znacznik [blokuje]

Kryterium może też zajmować kilka linii pod nagłówkiem `### AC-1`. Słowa kluczowe po polsku (Zakładając / Mając,
Gdy / Kiedy, Wtedy) albo po angielsku (Given, When, Then; sekcje: Acceptance criteria, Unchanged, Out of scope, Open
questions).

Reguły — strukturalne, bez modelu:
  SPEC-001 brak kryteriów `AC-n` · SPEC-002 kryterium bez części Zakładając, Gdy albo Wtedy · SPEC-003 powtórzony
  identyfikator · SPEC-004 więcej niż jedno „Gdy” (jedna akcja na kryterium) · SPEC-005 sekcja „Bez zmian” albo „Poza
  zakresem” pusta, nieobecna albo samo „brak” bez powodu · SPEC-006 otwarte pytanie ze znacznikiem [blokuje] ·
  SPEC-007 niewypełniony szablon (`<…>` w kryterium albo w sekcji) · SPEC-008 wynik, którego nie da się sprawdzić
  („działa poprawnie”, „works as expected”) bez liczby ani cytowanej wartości w części Wtedy.
SPEC-004 obejmuje też łącznik kolejnej akcji w części Gdy („a następnie”, „potem”, „oraz”, „and then”).
Pozostałe reguły językowe (szczegół implementacji, kilka akcji w historyjce, pełny słownik) sprawdza
`requirements_lint.py` z nakładki pack-it, gdy jest zainstalowana.

Z niepoprawną specyfikacją `tf task stage <KEY> plan` (i dalsze etapy) kończy się odmową. Zadanie bez `spec.md`
działa jak dotąd.

Kod wyjścia: 0 — gotowa; 1 — błędy (albo odmowa `new`); 2 — brak pliku lub błąd wywołania. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")

CHANGES = Path("docs") / "project" / "changes"
KEY = re.compile(r"[A-Z][A-Z0-9]*-[A-Za-z0-9][A-Za-z0-9-]*")
SECTIONS = {"criteria": ("kryteria", "kryteria akceptacji", "acceptance criteria", "criteria"),
            "unchanged": ("bez zmian", "unchanged"),
            "out": ("poza zakresem", "out of scope"),
            "questions": ("otwarte pytania", "open questions")}
LABEL = {"unchanged": "Bez zmian", "out": "Poza zakresem"}
AC_START = re.compile(r"^\s*(?:[-*]\s+|#{3,6}\s+)?\**(AC-\d+)\**\s*[:—–-]?\s*(.*)$")
GIVEN = re.compile(r"\b(zakładając|zakladajac|mając|majac|przy założeniu|given)\b", re.I)
WHEN = re.compile(r"\b(gdy|kiedy|when)\b", re.I)
THEN = re.compile(r"\b(wtedy|then)\b", re.I)
NEXT_ACTION = re.compile(r"\b(a następnie|następnie|potem|oraz|po czym|and then|after that|afterwards)\b", re.I)
WEAK = re.compile(r"\b(poprawnie|prawidłowo|właściwie|odpowiednio|dobrze|sprawnie|bez problemu|bez problemów|zgodnie z oczekiwani\w+|"
                  r"działa|działają|correctly|properly|successfully|as expected|works|work fine|is fine)\b", re.I)
CONCRETE = re.compile(r"\d|[\"„“”'`«»]")       # liczba albo cytowana wartość — wynik da się porównać w teście
PLACEHOLDER = re.compile(r"<[^<>\n]{2,}>")
NONE_ONLY = re.compile(r"^(brak|nie dotyczy|none|n/a|-|—)[.!]?$", re.I)
BLOCKING = re.compile(r"\[(blokuje|blocking)\]", re.I)
TEMPLATE = """# Specyfikacja: {title}

Źródło: `ticket.md`. Każde kryterium to jedno zachowanie: Zakładając <stan>, gdy <jedna akcja>, wtedy <wynik, który
da się sprawdzić testem>. Sprawdzenie: `tf spec check {key}`.

## Kryteria

- AC-1: Zakładając <stan początkowy>, gdy <jedna akcja>, wtedy <obserwowalny wynik>.

## Bez zmian

- <co ma działać jak dotąd — albo „brak, bo …”>

## Poza zakresem

- <czego ta historyjka nie obejmuje — albo „brak, bo …”>

## Otwarte pytania

- <pytanie; gdy bez odpowiedzi nie da się zacząć, dodaj [blokuje] — albo usuń tę linię>
"""


def parse(text: str) -> dict:
    """Sekcje (nazwa → linie z numerami) i kryteria (id, numer linii, tekst)."""
    sections: dict[str, list[tuple[int, str]]] = {}
    criteria: list[dict] = []
    current, item = None, None
    for n, line in enumerate(text.splitlines(), 1):
        head = re.match(r"^##\s+(.+?)\s*#*\s*$", line)
        if head:
            name = head.group(1).strip().lower()
            current = next((k for k, names in SECTIONS.items() if name in names), None)
            item = None
            if current:
                sections.setdefault(current, [])
            continue
        if current is None:
            continue
        sections[current].append((n, line))
        if current == "criteria":
            m = AC_START.match(line)
            if m:
                item = {"id": m.group(1), "line": n, "text": m.group(2)}
                criteria.append(item)
            elif item is not None and line.strip():
                item["text"] += "\n" + line.strip()
    return {"sections": sections, "criteria": criteria}


def filled(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Linie z treścią: bez pustych i bez znaczników listy."""
    out = []
    for n, line in lines:
        body = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", line).strip()
        if body:
            out.append((n, body))
    return out


def check_text(text: str) -> dict:
    data = parse(text)
    errors: list[dict] = []

    def add(rule: str, line: int, msg: str) -> None:
        errors.append({"rule": rule, "line": line, "message": msg})

    criteria = data["criteria"]
    if not criteria:
        add("SPEC-001", 1, "brak kryteriów: w sekcji „Kryteria” dodaj pozycje `- AC-1: Zakładając …, gdy …, wtedy …`")
    seen: dict[str, int] = {}
    for c in criteria:
        if c["id"] in seen:
            add("SPEC-003", c["line"], f"{c['id']} powtórzone (pierwsze w linii {seen[c['id']]}) — nadaj kolejny numer")
        seen.setdefault(c["id"], c["line"])
        if PLACEHOLDER.search(c["text"]):
            add("SPEC-007", c["line"], f"{c['id']}: niewypełniony szablon (`<…>`) — wpisz stan, akcję i wynik")
            continue
        missing = [name for name, rx in (("Zakładając", GIVEN), ("Gdy", WHEN), ("Wtedy", THEN)) if not rx.search(c["text"])]
        if missing:
            add("SPEC-002", c["line"], f"{c['id']}: brakuje części {', '.join(missing)}")
        when, then = WHEN.search(c["text"]), THEN.search(c["text"])
        action = c["text"][when.end():then.start()] if when and then and then.start() > when.end() else ""
        if len(WHEN.findall(c["text"])) > 1:
            add("SPEC-004", c["line"], f"{c['id']}: więcej niż jedno „gdy” — jedna akcja na kryterium, drugą opisz osobnym AC")
        elif NEXT_ACTION.search(action):
            add("SPEC-004", c["line"], f"{c['id']}: druga akcja w części Gdy („{NEXT_ACTION.search(action).group(0)}”) — "
                                       "jedna akcja na kryterium, drugą opisz osobnym AC")
        outcome = c["text"][then.end():] if then else ""
        weak = [m.group(0) for m in WEAK.finditer(outcome)]
        if weak and not CONCRETE.search(outcome):
            add("SPEC-008", c["line"], f"{c['id']}: wyniku „{' '.join(weak)}” nie da się sprawdzić testem — napisz, co "
                                       "dokładnie widać (wartość, komunikat, stan)")
    for name in ("unchanged", "out"):
        if name not in data["sections"]:
            add("SPEC-005", 1, f"brak sekcji „{LABEL[name]}” — wpisz pozycje albo „brak, bo …”")
            continue
        body = filled(data["sections"][name])
        start = data["sections"][name][0][0] if data["sections"][name] else 1
        if not body:
            add("SPEC-005", start, f"sekcja „{LABEL[name]}” jest pusta — wpisz pozycje albo „brak, bo …”")
        for n, line in body:
            if PLACEHOLDER.search(line):
                add("SPEC-007", n, f"sekcja „{LABEL[name]}”: niewypełniony szablon (`<…>`)")
            elif NONE_ONLY.match(line) and len(body) == 1:
                add("SPEC-005", n, f"sekcja „{LABEL[name]}”: samo „{line}” — dopisz powód („brak, bo …”)")
    for n, line in filled(data["sections"].get("questions", [])):
        if not PLACEHOLDER.search(line) and BLOCKING.search(line):
            add("SPEC-006", n, "otwarte pytanie blokuje start — potrzebna odpowiedź człowieka: " + line[:120])
    errors.sort(key=lambda e: (e["line"], e["rule"]))
    return {"ok": not errors, "criteria": [c["id"] for c in criteria], "errors": errors}


def spec_path(root: Path, key: str) -> Path:
    return root / CHANGES / key / "spec.md"


def check_task(root: Path, key: str) -> dict | None:
    """Wynik sprawdzenia spec.md zadania; None, gdy pliku nie ma (zadanie bez specyfikacji)."""
    path = spec_path(root, key)
    if not path.is_file():
        return None
    return check_text(path.read_text(encoding="utf-8", errors="replace"))


def cmd_check(root: Path, key: str, as_json: bool) -> int:
    result = check_task(root, key)
    rel = CHANGES / key / "spec.md"
    if result is None:
        print(f"✗ nie ma {rel} — szablon założysz: tf spec new {key}")
        return 2
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 0 if result["ok"] else 1
    if result["ok"]:
        print(f"✓ {rel}: {len(result['criteria'])} kryteriów ({', '.join(result['criteria'])}), gotowa do planu")
        return 0
    print(f"✗ {rel}: {len(result['errors'])} do poprawy")
    for e in result["errors"]:
        print(f"  {rel}:{e['line']}  {e['rule']}  {e['message']}")
    return 1


def cmd_new(root: Path, key: str) -> int:
    folder = root / CHANGES / key
    try:
        task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"✗ nie ma zadania {key} — załóż je: tf task start {key} --title \"…\"")
        return 1
    path = folder / "spec.md"
    if path.exists():
        print(f"✗ {CHANGES / key / 'spec.md'} już istnieje — nie nadpisuję; sprawdzenie: tf spec check {key}")
        return 1
    path.write_text(TEMPLATE.format(title=task.get("title") or key, key=key), encoding="utf-8")
    print(f"✓ {CHANGES / key / 'spec.md'} — wypełnij kryteria, potem: tf spec check {key}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf spec", description="Specyfikacja zadania: szablon i sprawdzenie.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("key")
    c = sub.add_parser("check")
    c.add_argument("key")
    c.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv[1:])
    except SystemExit as e:
        return 2 if e.code else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not KEY.fullmatch(a.key):
        print(f"✗ klucz „{a.key}” nie pasuje do wzorca (np. PROJ-123, CHG-12, T-20261113-limit)")
        return 2
    return cmd_new(root, a.key) if a.cmd == "new" else cmd_check(root, a.key, a.json)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
