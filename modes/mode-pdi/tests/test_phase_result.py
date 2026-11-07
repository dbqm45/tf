#!/usr/bin/env python3
"""Testy phase_result.py: jedno miejsce do odczytu wyniku `phase_run.py run` (N5, DZ13).

A7 i N1 zmieniają zawartość strumienia równolegle; N5 czyta stdout fazy zawsze przez tę samą funkcję,
żeby zmiana w phase_run.py (nowe linie PDI-PROGRESS, nowe pole second_review w wyniku) nie łamała runnera.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REL_WORK = Path(".claude") / "skills" / "pdi-decisions" / "scripts" / "phase_result.py"
REL_SRC = Path("modes") / "mode-pdi" / "skills" / "pdi-decisions" / "scripts" / "phase_result.py"
ROOT = next((p for p in Path(__file__).resolve().parents
             if (p / REL_WORK).is_file() or (p / REL_SRC).is_file()), None)
SCRIPT = (ROOT / REL_WORK) if ROOT and (ROOT / REL_WORK).is_file() else ((ROOT / REL_SRC) if ROOT else None)

if SCRIPT is None:
    raise SystemExit("nie znaleziono phase_result.py")
sys.path.insert(0, str(SCRIPT.parent))
import phase_result as pr  # noqa: E402


def main() -> int:
    fails: list[str] = []
    total = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # ── read_result ──────────────────────────────────────────────────────────

    # R-1: czysty JSON bez linii postępu
    out = pr.read_result(json.dumps({"change": "CHG-1", "phase": "intent", "status": "done",
                                     "cost_usd": 0.42, "gate": "B1", "persona": "maja"}))
    check(out["change"] == "CHG-1" and out["status"] == "done" and out["cost_usd"] == 0.42,
          f"R-1: zły wynik {out}")

    # R-2: linie PDI-PROGRESS: ignorowane, JSON na końcu
    stdout = "\n".join([
        'PDI-PROGRESS: {"phase":"intent","status":"started"}',
        'PDI-PROGRESS: {"phase":"intent","status":"in_progress","message":"czyta plik"}',
        json.dumps({"change": "CHG-1", "phase": "intent", "status": "waiting_gate",
                    "cost_usd": 0.42, "gate": "B1", "persona": "maja"}),
    ])
    out = pr.read_result(stdout)
    check(out["status"] == "waiting_gate" and out["gate"] == "B1",
          f"R-2: PDI-PROGRESS nie ignorowane, {out}")

    # R-3: wieloliniowy pretty JSON (json.dumps(..., indent=2) jak w phase_run.py)
    out = pr.read_result(json.dumps(
        {"change": "CHG-3", "phase": "delivery", "status": "failed",
         "error": "kod 1", "detail": "linia 1\nlinia 2\nlinia 3", "permission_denials": []},
        ensure_ascii=False, indent=2))
    check(out["status"] == "failed" and out["detail"] == "linia 1\nlinia 2\nlinia 3"
          and out["error"] == "kod 1", f"R-3: pretty JSON zepsuty, {out}")

    # R-4: dwa bloki JSON pod rząd — wybiera ostatni (np. sędzia wypisał coś obok)
    stdout = (
        json.dumps({"ignore": "me", "status": "done"}, indent=2) + "\n"
        + json.dumps({"change": "CHG-1", "phase": "requirements", "status": "waiting_gate",
                      "cost_usd": 0.33, "gate": "B2"}, indent=2))
    out = pr.read_result(stdout)
    check(out.get("change") == "CHG-1" and out.get("gate") == "B2",
          f"R-4: nie wzięto ostatniego JSONa, {out}")

    # R-5: pole second_review z N1 — zachowane (nowy klucz nie łamie czytnika)
    out = pr.read_result(json.dumps({"change": "CHG-1", "phase": "requirements", "status": "waiting_gate",
                                     "cost_usd": 0.44, "gate": "B2",
                                     "second_review": {"status": "ok", "blocking": 1, "cost_usd": 0.03}}))
    check(out.get("second_review", {}).get("blocking") == 1,
          f"R-5: second_review zgubiony, {out}")

    # R-6: brak JSONa w ogóle → ValueError z czytelnym komunikatem
    try:
        pr.read_result("PDI-PROGRESS: {\"phase\":\"intent\",\"status\":\"started\"}\nnic więcej")
        fails.append("R-6: brak wyjątku dla stdout bez JSONa")
        total += 1
    except ValueError as e:
        check("phase_run" in str(e) or "wynik" in str(e), f"R-6: niejasny komunikat: {e}")

    # R-7: pusty stdout → ValueError
    try:
        pr.read_result("")
        fails.append("R-7: brak wyjątku dla pustego stdout")
        total += 1
    except ValueError:
        total += 1

    # R-8: status spoza zestawu → ValueError
    try:
        pr.read_result(json.dumps({"change": "CHG-1", "phase": "intent", "status": "zupelnie-inny"}))
        fails.append("R-8: brak wyjątku dla nieznanego statusu")
        total += 1
    except ValueError as e:
        check("status" in str(e).lower(), f"R-8: niejasny komunikat: {e}")

    # R-9: status dry_run dopuszczony
    out = pr.read_result(json.dumps({"change": "CHG-1", "phase": "intent", "status": "dry_run",
                                     "argv": ["claude", "--print"], "prompt": "..."}))
    check(out["status"] == "dry_run", f"R-9: dry_run odrzucony, {out}")

    # R-10: JSON jest tablicą (nie słownikiem) → ValueError
    try:
        pr.read_result(json.dumps([1, 2, 3]))
        fails.append("R-10: brak wyjątku dla tablicy")
        total += 1
    except ValueError:
        total += 1

    # R-11: JSON nie na końcu — niedokończona linia po nim → wciąż znajduje ostatni poprawny
    stdout = (
        'PDI-PROGRESS: {"phase":"intent","status":"started"}\n'
        + json.dumps({"change": "CHG-1", "phase": "intent", "status": "done", "cost_usd": 0.1}, indent=2)
        + "\nsmieci po JSONie bez newline")
    out = pr.read_result(stdout)
    check(out["status"] == "done" and out.get("cost_usd") == 0.1,
          f"R-11: śmieci po JSONie zepsuły odczyt, {out}")

    # ── read_progress ─────────────────────────────────────────────────────────

    # P-1: wszystkie linie PDI-PROGRESS zebrane, pozostałe pominięte
    stdout = "\n".join([
        'PDI-PROGRESS: {"phase":"intent","status":"started"}',
        'nie linia postępu',
        'PDI-PROGRESS: {"phase":"intent","status":"in_progress","message":"czyta plik"}',
        'PDI-PROGRESS: {"phase":"intent","status":"done","cost_usd":0.4}',
        json.dumps({"status": "done", "change": "CHG-1", "phase": "intent", "cost_usd": 0.4}),
    ])
    rows = pr.read_progress(stdout)
    check(len(rows) == 3, f"P-1: zła liczba linii postępu, {len(rows)}")
    check(rows[0]["status"] == "started" and rows[-1]["status"] == "done",
          f"P-1: statusy nie w kolejności, {rows}")

    # P-2: niejsonowa linia po PDI-PROGRESS: — pominięta bez wyjątku
    stdout = 'PDI-PROGRESS: {ne-json}\nPDI-PROGRESS: {"phase":"intent","status":"done"}'
    rows = pr.read_progress(stdout)
    check(len(rows) == 1, f"P-2: złe parsowanie, {rows}")

    # P-3: pusty stdout → pusta lista
    check(pr.read_progress("") == [], "P-3: nie-pusty wynik dla pustego stdout")

    # ── derived metrics ──────────────────────────────────────────────────────

    # M-1: files_read liczy unikatowe pliki z wiadomości „czyta plik <ścieżka>"
    rows = [
        {"phase": "intent", "status": "started"},
        {"phase": "intent", "status": "in_progress", "message": "czyta plik docs/project/changes/CHG-1/intent.md"},
        {"phase": "intent", "status": "in_progress", "message": "czyta plik docs/project/changes/CHG-1/intent.md"},
        {"phase": "intent", "status": "in_progress", "message": "czyta plik docs/project/changes/CHG-1/plan.md"},
        {"phase": "intent", "status": "in_progress", "message": "uruchamia polecenie"},
        {"phase": "intent", "status": "done", "cost_usd": 0.4},
    ]
    check(pr.files_read(rows) == 2, f"M-1: files_read {pr.files_read(rows)} ≠ 2")

    # M-2: denials_count liczy wiadomości z prefiksem „odmowa narzędzia"
    rows = [
        {"phase": "delivery", "status": "in_progress", "message": "odmowa narzędzia Bash: not in allow"},
        {"phase": "delivery", "status": "in_progress", "message": "odmowa narzędzia Write: locked path"},
        {"phase": "delivery", "status": "in_progress", "message": "czyta plik x"},
    ]
    check(pr.denials_count(rows) == 2, f"M-2: denials {pr.denials_count(rows)} ≠ 2")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów phase_result")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
