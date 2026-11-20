#!/usr/bin/env python3
"""Tests of phase_result.py: a single place to read the result of `phase_run.py run` (N5, DZ13).

A7 and N1 change the stream content in parallel; N5 always reads the phase stdout through the same function,
so that a change in phase_run.py (new PDI-PROGRESS lines, a new second_review field in the result) does not break the runner.
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

    # R-1: plain JSON without progress lines
    out = pr.read_result(json.dumps({"change": "CHG-1", "phase": "intent", "status": "done",
                                     "cost_usd": 0.42, "gate": "B1", "persona": "maja"}))
    check(out["change"] == "CHG-1" and out["status"] == "done" and out["cost_usd"] == 0.42,
          f"R-1: bad result {out}")

    # R-2: PDI-PROGRESS lines: ignored, JSON at the end
    stdout = "\n".join([
        'PDI-PROGRESS: {"phase":"intent","status":"started"}',
        'PDI-PROGRESS: {"phase":"intent","status":"in_progress","message":"reads file"}',
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

    # R-4: two JSON blocks in a row — picks the last (e.g. the judge printed something alongside)
    stdout = (
        json.dumps({"ignore": "me", "status": "done"}, indent=2) + "\n"
        + json.dumps({"change": "CHG-1", "phase": "requirements", "status": "waiting_gate",
                      "cost_usd": 0.33, "gate": "B2"}, indent=2))
    out = pr.read_result(stdout)
    check(out.get("change") == "CHG-1" and out.get("gate") == "B2",
          f"R-4: the last JSON was not taken, {out}")

    # R-5: the second_review field from N1 — preserved (a new key does not break the reader)
    out = pr.read_result(json.dumps({"change": "CHG-1", "phase": "requirements", "status": "waiting_gate",
                                     "cost_usd": 0.44, "gate": "B2",
                                     "second_review": {"status": "ok", "blocking": 1, "cost_usd": 0.03}}))
    check(out.get("second_review", {}).get("blocking") == 1,
          f"R-5: second_review zgubiony, {out}")

    # R-6: no JSON at all → ValueError with a readable message
    try:
        pr.read_result("PDI-PROGRESS: {\"phase\":\"intent\",\"status\":\"started\"}\nnic więcej")
        fails.append("R-6: no exception for stdout without JSON")
        total += 1
    except ValueError as e:
        check("phase_run" in str(e) or "wynik" in str(e), f"R-6: niejasny komunikat: {e}")

    # R-7: pusty stdout → ValueError
    try:
        pr.read_result("")
        fails.append("R-7: no exception for empty stdout")
        total += 1
    except ValueError:
        total += 1

    # R-8: status spoza zestawu → ValueError
    try:
        pr.read_result(json.dumps({"change": "CHG-1", "phase": "intent", "status": "zupelnie-inny"}))
        fails.append("R-8: no exception for an unknown status")
        total += 1
    except ValueError as e:
        check("status" in str(e).lower(), f"R-8: niejasny komunikat: {e}")

    # R-9: status dry_run dopuszczony
    out = pr.read_result(json.dumps({"change": "CHG-1", "phase": "intent", "status": "dry_run",
                                     "argv": ["claude", "--print"], "prompt": "..."}))
    check(out["status"] == "dry_run", f"R-9: dry_run odrzucony, {out}")

    # R-10: JSON is an array (not a dict) → ValueError
    try:
        pr.read_result(json.dumps([1, 2, 3]))
        fails.append("R-10: no exception for an array")
        total += 1
    except ValueError:
        total += 1

    # R-11: JSON not at the end — an unfinished line after it → still finds the last valid one
    stdout = (
        'PDI-PROGRESS: {"phase":"intent","status":"started"}\n'
        + json.dumps({"change": "CHG-1", "phase": "intent", "status": "done", "cost_usd": 0.1}, indent=2)
        + "\nsmieci po JSONie bez newline")
    out = pr.read_result(stdout)
    check(out["status"] == "done" and out.get("cost_usd") == 0.1,
          f"R-11: junk after the JSON broke the read, {out}")

    # ── read_progress ─────────────────────────────────────────────────────────

    # P-1: all PDI-PROGRESS lines collected, the rest skipped
    stdout = "\n".join([
        'PDI-PROGRESS: {"phase":"intent","status":"started"}',
        'nie linia postępu',
        'PDI-PROGRESS: {"phase":"intent","status":"in_progress","message":"reads file"}',
        'PDI-PROGRESS: {"phase":"intent","status":"done","cost_usd":0.4}',
        json.dumps({"status": "done", "change": "CHG-1", "phase": "intent", "cost_usd": 0.4}),
    ])
    rows = pr.read_progress(stdout)
    check(len(rows) == 3, f"P-1: wrong number of progress lines, {len(rows)}")
    check(rows[0]["status"] == "started" and rows[-1]["status"] == "done",
          f"P-1: statuses out of order, {rows}")

    # P-2: a non-JSON line after PDI-PROGRESS: — skipped without an exception
    stdout = 'PDI-PROGRESS: {ne-json}\nPDI-PROGRESS: {"phase":"intent","status":"done"}'
    rows = pr.read_progress(stdout)
    check(len(rows) == 1, f"P-2: bad parsing, {rows}")

    # P-3: pusty stdout → pusta lista
    check(pr.read_progress("") == [], "P-3: non-empty result for empty stdout")

    # ── derived metrics ──────────────────────────────────────────────────────

    # M-1: files_read counts unique files from the "reads file <path>" messages
    rows = [
        {"phase": "intent", "status": "started"},
        {"phase": "intent", "status": "in_progress", "message": "reads file docs/project/changes/CHG-1/intent.md"},
        {"phase": "intent", "status": "in_progress", "message": "reads file docs/project/changes/CHG-1/intent.md"},
        {"phase": "intent", "status": "in_progress", "message": "reads file docs/project/changes/CHG-1/plan.md"},
        {"phase": "intent", "status": "in_progress", "message": "reads file docs/project/changes/CHG-1/spec.md"},
        {"phase": "intent", "status": "in_progress", "message": "uruchamia polecenie"},
        {"phase": "intent", "status": "done", "cost_usd": 0.4},
    ]
    check(pr.files_read(rows) == 3, f"M-1: files_read {pr.files_read(rows)} ≠ 3")

    # M-2: denials_count counts messages with the "tool denied" prefix
    rows = [
        {"phase": "delivery", "status": "in_progress", "message": "tool denied Bash: not in allow"},
        {"phase": "delivery", "status": "in_progress", "message": "tool denied Write: locked path"},
        {"phase": "delivery", "status": "in_progress", "message": "reads file x"},
    ]
    check(pr.denials_count(rows) == 2, f"M-2: denials {pr.denials_count(rows)} ≠ 2")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of phase_result")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
