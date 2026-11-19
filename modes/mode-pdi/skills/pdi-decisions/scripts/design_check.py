#!/usr/bin/env python3
"""
Frames table in a change's design.md (pdi contract 0.9.0, conventions.design; stage 07 Design).

  python3 .claude/skills/pdi-decisions/scripts/design_check.py check CHG-12 [--json]
      reads docs/project/changes/CHG-12/design.md, checks the table format
      `Wymaganie | Ścieżka | Stan | Ramka | Uwagi` and coverage: every requirement in the table has the minimal states
      (idle, success and at least one error state — counted per
      story, US-3/AC-n criteria belong to US-3), and every row has a frame or „nie dotyczy” (not applicable) with a reason.
      A „brak” (missing) row is a problem (a question to the designer). Result: a list of problems; --json: rows and problems.

phase_run.py adds these problems as questions to the design-review gate request. Exit code: 0 — no problems,
1 — problems or a format error, 2 — missing file or bad invocation. Python 3.9+ standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

CHANGES = Path("docs") / "project" / "changes"
# contract.json → conventions.design (pdi contract 0.9.0); a test keeps it consistent with the contract schema.
STATES = ("idle", "loading", "processing", "success", "validation_error", "server_error", "timeout", "retry",
          "empty", "confirmation", "session_expired", "network_failure", "permission_denied")
COLUMNS = (("wymaganie", "ścieżka", "stan", "ramka", "uwagi"), ("requirement", "journey", "state", "frame", "notes"))
MISSING = ("brak", "missing")
NOT_APPLICABLE = ("nie dotyczy", "n/a")
REQUIREMENT = re.compile(r"^[A-Z][A-Z0-9]*-[0-9]+(/AC-[0-9]+)?$")
# Minimum for every required table row: input, result and at least one error state (tf plan F6).
MINIMUM = ("idle", "success")
ERRORS = ("validation_error", "server_error", "timeout", "network_failure", "permission_denied", "session_expired")
_FIGMA_PATH = re.compile(r"^/(design|file|proto)/([A-Za-z0-9]+)(/|$)")
_NODE = re.compile(r"^([0-9]+)[-:]([0-9]+)$")


class DesignFormatError(ValueError):
    """A table that violates the contract; the message starts with the table row number (from 1)."""


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _frame(url: str, row: int) -> dict:
    parsed = urlparse(url)
    match = _FIGMA_PATH.match(parsed.path)
    if parsed.scheme != "https" or parsed.netloc.lower() not in ("figma.com", "www.figma.com") or not match:
        raise DesignFormatError(f"row {row}: the frame link must point to a file on figma.com")
    node = _NODE.match(unquote((parse_qs(parsed.query).get("node-id") or [""])[0]))
    if not node:
        raise DesignFormatError(f"row {row}: the frame link has no node-id (link a frame, not the whole file)")
    return {"file_key": match.group(2), "node_id": f"{node.group(1)}:{node.group(2)}", "url": url}


def parse_design_md(text: str) -> dict:
    """The first table with a header from the contract → {"rows": [...]} (the shape of design-links.schema.json)."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().startswith("|") and tuple(c.lower() for c in _cells(ln)) in COLUMNS), None)
    if start is None:
        raise DesignFormatError("no frames table (header: Wymaganie | Ścieżka | Stan | Ramka | Uwagi, "
                                "or Requirement | Journey | State | Frame | Notes)")
    rows = []
    for line in lines[start + 2:]:
        if not line.strip().startswith("|"):
            break
        n = len(rows) + 1
        cells = _cells(line)
        if len(cells) != 5:
            raise DesignFormatError(f"row {n}: expected 5 columns, got {len(cells)}")
        req, journey, state, frame, note = cells
        if not REQUIREMENT.match(req):
            raise DesignFormatError(f"row {n}: bad requirement ID '{req}' (e.g. US-3 or US-3/AC-2)")
        if not journey:
            raise DesignFormatError(f"row {n}: empty journey")
        if state not in STATES:
            raise DesignFormatError(f"row {n}: unknown state '{state}' (see conventions.design.states)")
        row = {"requirement": req, "journey": journey, "state": state}
        if frame.lower() in MISSING + NOT_APPLICABLE:
            row["status"] = "missing" if frame.lower() in MISSING else "not_applicable"
            if not note:
                raise DesignFormatError(f"row {n}: '{frame}' needs a note with a reason or a question")
        else:
            row["status"] = "linked"
            row["frame"] = _frame(frame, n)
        if note:
            row["note"] = note
        rows.append(row)
    return {"rows": rows}


def problems(rows: list[dict]) -> list[str]:
    """Gaps to resolve before the gate: rows without a frame and requirements without the minimal states."""
    out = [f"{r['requirement']} {r['state']} ({r['journey']}): no frame — {r['note']}"
           for r in rows if r["status"] == "missing"]
    by_req: dict[str, set[str]] = {}
    for r in rows:   # minimal states counted per story: US-3, US-3/AC-2 and US-3/AC-3 are one flow
        by_req.setdefault(r["requirement"].split("/")[0], set()).add(r["state"])
    for req, states in by_req.items():
        lacking = [s for s in MINIMUM if s not in states]
        if not states & set(ERRORS):
            lacking.append("an error state (" + ", ".join(ERRORS[:3]) + "…)")
        if lacking:
            out.append(f"{req}: no row for {', '.join(lacking)} — add a frame, or „n/a” with a reason")
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
        print(f"✗ no {path} — the change design is made in the design phase (template templates/design.md)")
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
        print(f"✗ {path}: {len(found)} to resolve before the design-review gate")
        for p in found:
            print(f"  - {p}")
    else:
        linked = sum(r["status"] == "linked" for r in rows)
        print(f"✓ {path}: {len(rows)} rows, {linked} with a frame, minimum states covered")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
