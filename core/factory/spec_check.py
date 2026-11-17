#!/usr/bin/env python3
"""
Specyfikacja zadania sprawdzana skryptem (krok D osi przebiegu): `docs/project/changes/<KEY>/spec.md`.

  tf spec new <KEY>                 # szablon spec.md z tytułem zadania (nie nadpisuje istniejącego)
  tf spec check <KEY> [--json]      # czy specyfikacja jest gotowa do planu

Format pliku (bez nagłówka artefaktu — stan pliku trzyma task.json):

  # Spec: <tytuł>
  ## Acceptance criteria   - AC-1: Given <stan>, when <jedna akcja>, then <obserwowalny wynik>.
  ## Unchanged             co ma działać jak dotąd (albo „none, because …”)
  ## Out of scope          czego historyjka nie obejmuje (albo „none, because …”)
  ## Open questions        pytanie, bez którego nie da się zacząć, ma znacznik [blocking]

Kryterium może też zajmować kilka linii pod nagłówkiem `### AC-1`. Słowa kluczowe i sekcje po angielsku; dawne polskie
(Zakładając / Mając, Gdy / Kiedy, Wtedy; Kryteria, Bez zmian, Poza zakresem, Otwarte pytania, [blokuje]) skrypt
przyjmuje przez wydanie 14.x, a migracja przepisuje je w otwartych zadaniach.

Reguły — strukturalne, bez modelu:
  SPEC-001 brak kryteriów `AC-n` · SPEC-002 kryterium bez części Given, When albo Then · SPEC-003 powtórzony
  identyfikator · SPEC-004 więcej niż jedno „When” (jedna akcja na kryterium) · SPEC-005 sekcja „Unchanged” albo „Out of
  scope” pusta, nieobecna albo samo „none” bez powodu · SPEC-006 otwarte pytanie ze znacznikiem [blocking] ·
  SPEC-007 niewypełniony szablon (`<…>` w kryterium albo w sekcji) · SPEC-008 wynik, którego nie da się sprawdzić
  („działa poprawnie”, „works as expected”) bez liczby ani cytowanej wartości w części Then.
SPEC-009 (ostrzeżenie, nie blokuje etapu): żadne kryterium nie opisuje zachowania niedozwolonego — odmowy, błędu,
„nie …” w części Then; sprawdzane tylko przy specyfikacji bez błędów.
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
LABEL = {"unchanged": "Unchanged", "out": "Out of scope"}
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
# wynik opisujący zachowanie niedozwolone: odmowa, blokada, błąd, „nie …” (SPEC-009, tylko ostrzeżenie)
NEGATIVE = re.compile(r"\b(nie|odmaw\w*|odmow\w*|odrzuc\w*|blokuj\w*|zablok\w*|błęd\w*|zabron\w*|brak\w*|"
                      r"not|no|never|cannot|rejects?|rejected|denie[sd]|deny|error|forbidden|blocked)\b", re.I)
TEMPLATE = """# Spec: {title}

Source: `ticket.md`. Each criterion is one behaviour: Given <state>, when <one action>, then <result that a test can
check>. Check: `tf spec check {key}`.

## Acceptance criteria

- AC-1: Given <initial state>, when <one action>, then <observable result>.
- AC-2: Given <state>, when <forbidden action or invalid data>, then <what the system does not do — refusal, message>.
  (negative criterion: what the result must not be; remove it if the story has none)

## Unchanged

- <what must keep working as before — or „none, because …”>

## Out of scope

- <what this story does not cover — or „none, because …”>

## Open questions

- <question; if work cannot start without an answer, add [blocking] — or remove this line>
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
        add("SPEC-001", 1, "no criteria: in the „Acceptance criteria” section add items `- AC-1: Given …, when …, then …`")
    seen: dict[str, int] = {}
    for c in criteria:
        if c["id"] in seen:
            add("SPEC-003", c["line"], f"{c['id']} repeated (first on line {seen[c['id']]}) — use the next number")
        seen.setdefault(c["id"], c["line"])
        if PLACEHOLDER.search(c["text"]):
            add("SPEC-007", c["line"], f"{c['id']}: template not filled in (`<…>`) — write the state, the action and the result")
            continue
        missing = [name for name, rx in (("Given", GIVEN), ("When", WHEN), ("Then", THEN)) if not rx.search(c["text"])]
        if missing:
            add("SPEC-002", c["line"], f"{c['id']}: missing part {', '.join(missing)}")
        when, then = WHEN.search(c["text"]), THEN.search(c["text"])
        action = c["text"][when.end():then.start()] if when and then and then.start() > when.end() else ""
        if len(WHEN.findall(c["text"])) > 1:
            add("SPEC-004", c["line"], f"{c['id']}: more than one „when” — one action per criterion, describe the second one in a separate AC")
        elif NEXT_ACTION.search(action):
            add("SPEC-004", c["line"], f"{c['id']}: second action in the When part („{NEXT_ACTION.search(action).group(0)}”) — "
                                       "one action per criterion, describe the second one in a separate AC")
        outcome = c["text"][then.end():] if then else ""
        weak = [m.group(0) for m in WEAK.finditer(outcome)]
        if weak and not CONCRETE.search(outcome):
            add("SPEC-008", c["line"], f"{c['id']}: a test cannot check the result „{' '.join(weak)}” — write what "
                                       "exactly is visible (value, message, state)")
    for name in ("unchanged", "out"):
        if name not in data["sections"]:
            add("SPEC-005", 1, f"no „{LABEL[name]}” section — add items or „none, because …”")
            continue
        body = filled(data["sections"][name])
        start = data["sections"][name][0][0] if data["sections"][name] else 1
        if not body:
            add("SPEC-005", start, f"section „{LABEL[name]}” is empty — add items or „none, because …”")
        for n, line in body:
            if PLACEHOLDER.search(line):
                add("SPEC-007", n, f"section „{LABEL[name]}”: template not filled in (`<…>`)")
            elif NONE_ONLY.match(line) and len(body) == 1:
                add("SPEC-005", n, f"section „{LABEL[name]}”: only „{line}” — add the reason („none, because …”)")
    for n, line in filled(data["sections"].get("questions", [])):
        if not PLACEHOLDER.search(line) and BLOCKING.search(line):
            add("SPEC-006", n, "open question blocks the start — a human must answer: " + line[:120])
    errors.sort(key=lambda e: (e["line"], e["rule"]))
    warnings: list[dict] = []
    outcomes = [c["text"][THEN.search(c["text"]).end():] for c in criteria if THEN.search(c["text"])]
    if criteria and not errors and not any(NEGATIVE.search(o) for o in outcomes):
        line = data["sections"]["criteria"][0][0] if data["sections"].get("criteria") else 1
        warnings.append({"rule": "SPEC-009", "line": line,
                         "message": "no criterion describes forbidden behaviour (refusal, error, „not …”) — "
                                    "add a negative criterion or confirm that the story has none"})
    return {"ok": not errors, "criteria": [c["id"] for c in criteria], "errors": errors, "warnings": warnings}


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
        print(f"✗ {rel} does not exist — create the template: tf spec new {key}")
        return 2
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 0 if result["ok"] else 1
    if result["ok"]:
        print(f"✓ {rel}: {len(result['criteria'])} criteria ({', '.join(result['criteria'])}), ready for the plan")
        for w in result.get("warnings", []):
            print(f"  ⚠ {rel}:{w['line']}  {w['rule']}  {w['message']}")
        return 0
    print(f"✗ {rel}: {len(result['errors'])} to fix")
    for e in result["errors"]:
        print(f"  {rel}:{e['line']}  {e['rule']}  {e['message']}")
    return 1


def cmd_new(root: Path, key: str) -> int:
    folder = root / CHANGES / key
    try:
        task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"✗ task {key} does not exist — create it: tf task start {key} --title \"…\"")
        return 1
    path = folder / "spec.md"
    if path.exists():
        print(f"✗ {CHANGES / key / 'spec.md'} already exists — not overwriting; check: tf spec check {key}")
        return 1
    path.write_text(TEMPLATE.format(title=task.get("title") or key, key=key), encoding="utf-8")
    print(f"✓ {CHANGES / key / 'spec.md'} — fill in the criteria, then: tf spec check {key}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf spec", description="Task spec: template and check.")
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
        print(f"✗ key „{a.key}” does not match the pattern (e.g. PROJ-123, CHG-12, T-20261113-limit)")
        return 2
    return cmd_new(root, a.key) if a.cmd == "new" else cmd_check(root, a.key, a.json)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
