#!/usr/bin/env python3
"""Odczyt wyniku `phase_run.py run` — jedno miejsce dla runnera N5 (DZ13).

phase_run.py w `cmd_run` wypisuje strumień linii:
  - zero lub więcej linii postępu `PDI-PROGRESS: {json}` (phase_progress.py; A7 stream-json)
  - jeden końcowy obiekt JSON (`json.dumps(out, ensure_ascii=False, indent=2)`) ze stanem fazy

Ten moduł udostępnia:
  - `read_result(stdout: str) -> dict` — ostatni poprawny obiekt JSON ze stdout (status w zestawie);
  - `read_progress(stdout: str) -> list[dict]` — linie postępu sparsowane do słowników;
  - `files_read(rows)`, `denials_count(rows)` — metryki pochodne.

Czytając wynik tylko przez `read_result`, runner N5 jest odporny na zmiany A7 (postać stream-json, nowe pola
w liniach postępu) i N1 (nowe pole `second_review` w końcowym słowniku) — oba scenariusze dalej zwracają
spójny słownik z `status/cost_usd/detail/permission_denials/error`.

Źródło kształtu `out` (pola): `phase_run.py:cmd_run` (PRB-28 fix 2026-11-06).
Źródło prefiksu `PDI-PROGRESS`: `phase_progress.PREFIX` (A7, kontrakt pdi 0.11.0 `run_progress`).
"""
from __future__ import annotations

import json
import re
from typing import Any

PREFIX = "PDI-PROGRESS: "
# Statusy, które `cmd_run` wypisuje (phase_run.py); `dry_run` wchodzi z `--dry-run`.
STATUSES = ("waiting_gate", "done", "failed", "dry_run")
_READ_FILE = re.compile(r"\bczyta plik\s+(?P<path>\S+)")
_DENIAL = re.compile(r"\bodmowa narzędzia\b")


def _strip_progress(stdout: str) -> str:
    """Stdout bez linii zaczynających się od `PDI-PROGRESS:` — do parsowania końcowego JSONa."""
    return "\n".join(line for line in stdout.splitlines() if not line.startswith(PREFIX))


def _iter_json_objects(text: str):
    """Iteruj po poprawnych obiektach JSON (`{...}`) w tekście, w kolejności wystąpienia.

    Skanuje od pierwszego `{`, próbuje `json.loads` od tego miejsca do coraz większych długości przez raw decoder,
    co pozwala obsłużyć pretty-printed JSON wielolinijkowy między śmieciami.
    """
    decoder = json.JSONDecoder()
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        try:
            obj, end = decoder.raw_decode(text, i)
        except ValueError:
            i += 1
            continue
        yield obj
        i = end


def read_result(stdout: str) -> dict:
    """Ostatni poprawny obiekt JSON ze stdout fazy (po pominięciu linii postępu).

    Rzuca `ValueError`, gdy:
      - stdout jest pusty albo zawiera tylko linie postępu;
      - żaden fragment poza postępem nie jest słownikiem JSON;
      - status w słowniku nie pasuje do `STATUSES`.
    """
    if not stdout or not stdout.strip():
        raise ValueError("phase_run wynik: stdout jest pusty")
    text = _strip_progress(stdout)
    if not text.strip():
        raise ValueError("phase_run wynik: w stdout są tylko linie postępu, brak JSONa")
    last: dict | None = None
    for obj in _iter_json_objects(text):
        if isinstance(obj, dict):
            last = obj
    if last is None:
        raise ValueError("phase_run wynik: w stdout nie ma obiektu JSON (jest tablica albo niepoprawne dane)")
    status = last.get("status")
    if status not in STATUSES:
        raise ValueError(f"phase_run wynik: status {status!r} spoza zestawu {', '.join(STATUSES)}")
    return last


def read_progress(stdout: str) -> list[dict]:
    """Linie postępu (słowniki) ze stdout; niepoprawny JSON po prefiksie pomijany bez wyjątku."""
    rows: list[dict] = []
    if not stdout:
        return rows
    for line in stdout.splitlines():
        if not line.startswith(PREFIX):
            continue
        try:
            value = json.loads(line[len(PREFIX):])
        except ValueError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def files_read(rows: list[dict]) -> int:
    """Liczba unikatowych plików wczytanych przez personę w strumieniu (po wiadomości „czyta plik <ścieżka>")."""
    seen: set[str] = set()
    for row in rows:
        msg = row.get("message") if isinstance(row, dict) else None
        if not isinstance(msg, str):
            continue
        m = _READ_FILE.search(msg)
        if m:
            seen.add(m.group("path"))
    return len(seen)


def denials_count(rows: list[dict]) -> int:
    """Liczba odmów narzędzi w strumieniu (sygnał PRB-32: folder nietrusted albo brak reguły allow)."""
    count = 0
    for row in rows:
        msg = row.get("message") if isinstance(row, dict) else None
        if isinstance(msg, str) and _DENIAL.search(msg):
            count += 1
    return count


def read_cost(result: Any) -> float | None:
    """Koszt USD z wyniku `phase_run.py`; None, gdy brak albo nieliczbowy. `phase_result` utrzymuje tu jedno miejsce,
    żeby runner N5 nie zgadywał pól `cost_usd` z result.json i progress równolegle."""
    if not isinstance(result, dict):
        return None
    value = result.get("cost_usd")
    if isinstance(value, (int, float)):
        return float(value)
    return None


if __name__ == "__main__":  # pragma: no cover
    import sys
    data = sys.stdin.read()
    try:
        out = read_result(data)
    except ValueError as e:
        print(f"✗ {e}")
        sys.exit(1)
    print(json.dumps(out, ensure_ascii=False, indent=2))
