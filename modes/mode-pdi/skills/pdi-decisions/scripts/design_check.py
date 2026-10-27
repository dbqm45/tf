#!/usr/bin/env python3
"""
Tabela ramek w design.md zmiany (kontrakt pdi 0.9.0, conventions.design; etap 07 Design).

  python3 .claude/skills/pdi-decisions/scripts/design_check.py check CHG-12 [--json]
      czyta docs/project/changes/CHG-12/design.md, sprawdza format tabeli
      `Wymaganie | Ścieżka | Stan | Ramka | Uwagi` i pokrycie: każde wymaganie z tabeli ma stany minimalne
      (idle, success i co najmniej jeden stan błędu — liczone per
      historyjka, kryteria US-3/AC-n należą do US-3), a każdy wiersz ramkę albo „nie dotyczy” z powodem.
      Wiersz „brak” to problem (pytanie do projektanta). Wynik: lista problemów; --json: wiersze i problemy.

phase_run.py dokłada te problemy jako pytania do prośby o bramkę design-review. Kod wyjścia: 0 — bez problemów,
1 — problemy albo błąd formatu, 2 — brak pliku lub złe wywołanie. Tylko biblioteka standardowa Pythona 3.9+.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

CHANGES = Path("docs") / "project" / "changes"
# contract.json → conventions.design (kontrakt pdi 0.9.0); test pilnuje zgodności ze schematem z kontraktu.
STATES = ("idle", "loading", "processing", "success", "validation_error", "server_error", "timeout", "retry",
          "empty", "confirmation", "session_expired", "network_failure", "permission_denied")
COLUMNS = (("wymaganie", "ścieżka", "stan", "ramka", "uwagi"), ("requirement", "journey", "state", "frame", "notes"))
MISSING = ("brak", "missing")
NOT_APPLICABLE = ("nie dotyczy", "n/a")
REQUIREMENT = re.compile(r"^[A-Z][A-Z0-9]*-[0-9]+(/AC-[0-9]+)?$")
# Minimum dla każdego wymaganego wiersza tabeli: wejście, wynik i co najmniej jeden stan błędu (plan F6 tf).
MINIMUM = ("idle", "success")
ERRORS = ("validation_error", "server_error", "timeout", "network_failure", "permission_denied", "session_expired")
_FIGMA_PATH = re.compile(r"^/(design|file|proto)/([A-Za-z0-9]+)(/|$)")
_NODE = re.compile(r"^([0-9]+)[-:]([0-9]+)$")


class DesignFormatError(ValueError):
    """Tabela niezgodna z kontraktem; komunikat zaczyna się od numeru wiersza tabeli (od 1)."""


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _frame(url: str, row: int) -> dict:
    parsed = urlparse(url)
    match = _FIGMA_PATH.match(parsed.path)
    if parsed.scheme != "https" or parsed.netloc.lower() not in ("figma.com", "www.figma.com") or not match:
        raise DesignFormatError(f"wiersz {row}: link do ramki musi prowadzić do pliku w figma.com")
    node = _NODE.match(unquote((parse_qs(parsed.query).get("node-id") or [""])[0]))
    if not node:
        raise DesignFormatError(f"wiersz {row}: link do ramki bez node-id (ramka, nie cały plik)")
    return {"file_key": match.group(2), "node_id": f"{node.group(1)}:{node.group(2)}", "url": url}


def parse_design_md(text: str) -> dict:
    """Pierwsza tabela z nagłówkiem z kontraktu → {"rows": [...]} (kształt design-links.schema.json)."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().startswith("|") and tuple(c.lower() for c in _cells(ln)) in COLUMNS), None)
    if start is None:
        raise DesignFormatError("brak tabeli ramek (nagłówek: Wymaganie | Ścieżka | Stan | Ramka | Uwagi)")
    rows = []
    for line in lines[start + 2:]:
        if not line.strip().startswith("|"):
            break
        n = len(rows) + 1
        cells = _cells(line)
        if len(cells) != 5:
            raise DesignFormatError(f"wiersz {n}: oczekiwano 5 kolumn, jest {len(cells)}")
        req, journey, state, frame, note = cells
        if not REQUIREMENT.match(req):
            raise DesignFormatError(f"wiersz {n}: identyfikator wymagania '{req}' (np. US-3 albo US-3/AC-2)")
        if not journey:
            raise DesignFormatError(f"wiersz {n}: pusta ścieżka")
        if state not in STATES:
            raise DesignFormatError(f"wiersz {n}: nieznany stan '{state}' (lista w conventions.design.states)")
        row = {"requirement": req, "journey": journey, "state": state}
        if frame.lower() in MISSING + NOT_APPLICABLE:
            row["status"] = "missing" if frame.lower() in MISSING else "not_applicable"
            if not note:
                raise DesignFormatError(f"wiersz {n}: '{frame}' wymaga uwagi z powodem albo pytaniem")
        else:
            row["status"] = "linked"
            row["frame"] = _frame(frame, n)
        if note:
            row["note"] = note
        rows.append(row)
    return {"rows": rows}


def problems(rows: list[dict]) -> list[str]:
    """Braki do rozstrzygnięcia przed bramką: wiersze bez ramki i wymagania bez stanów minimalnych."""
    out = [f"{r['requirement']} {r['state']} ({r['journey']}): brak ramki — {r['note']}"
           for r in rows if r["status"] == "missing"]
    by_req: dict[str, set[str]] = {}
    for r in rows:   # stany minimalne liczone per historyjka: US-3, US-3/AC-2 i US-3/AC-3 to jeden przepływ
        by_req.setdefault(r["requirement"].split("/")[0], set()).add(r["state"])
    for req, states in by_req.items():
        lacking = [s for s in MINIMUM if s not in states]
        if not states & set(ERRORS):
            lacking.append("stan błędu (" + ", ".join(ERRORS[:3]) + "…)")
        if lacking:
            out.append(f"{req}: brak wiersza dla {', '.join(lacking)} — dodaj ramkę albo „nie dotyczy” z powodem")
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("change")
    c.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    path = CHANGES / a.change / "design.md"
    if not path.is_file():
        print(f"✗ brak {path} — projekt zmiany powstaje w fazie design (szablon templates/design.md)")
        return 2
    try:
        rows = parse_design_md(path.read_text(encoding="utf-8"))["rows"]
    except DesignFormatError as e:
        print(f"✗ {path}: {e}")
        return 1
    found = problems(rows)
    if a.json:
        print(json.dumps({"rows": rows, "problems": found}, ensure_ascii=False, indent=2))
    elif found:
        print(f"✗ {path}: {len(found)} do rozstrzygnięcia przed bramką design-review")
        for p in found:
            print(f"  - {p}")
    else:
        linked = sum(r["status"] == "linked" for r in rows)
        print(f"✓ {path}: {len(rows)} wierszy, {linked} z ramką, stany minimalne pokryte")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
