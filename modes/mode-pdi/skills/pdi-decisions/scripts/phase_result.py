#!/usr/bin/env python3
"""Reading the result of `phase_run.py run` — a single place for the N5 runner (DZ13).

In `cmd_run` phase_run.py prints a stream of lines:
  - zero or more progress lines `PDI-PROGRESS: {json}` (phase_progress.py; A7 stream-json)
  - one final JSON object (`json.dumps(out, ensure_ascii=False, indent=2)`) with the phase state

This module provides:
  - `read_result(stdout: str) -> dict` — the last valid JSON object from stdout (status within the set);
  - `read_progress(stdout: str) -> list[dict]` — progress lines parsed into dicts;
  - `files_read(rows)`, `denials_count(rows)` — derived metrics.

By reading the result only through `read_result`, the N5 runner is resistant to A7 changes (the stream-json form, new fields
in progress lines) and N1 (a new `second_review` field in the final dict) — both scenarios still return a
consistent dict with `status/cost_usd/detail/permission_denials/error`.

Source of the shape of `out` (fields): `phase_run.py:cmd_run` (PRB-28 fix 2026-11-06).
Source of the `PDI-PROGRESS` prefix: `phase_progress.PREFIX` (A7, pdi contract 0.11.0 `run_progress`).
"""
from __future__ import annotations

import json
import re
from typing import Any

PREFIX = "PDI-PROGRESS: "
# Statuses that `cmd_run` prints (phase_run.py); `dry_run` comes from `--dry-run`.
STATUSES = ("waiting_gate", "done", "failed", "dry_run")
# Progress messages from phase_progress.py.
_READ_FILE = re.compile(r"\b(?:reads file|reading file)\s+(?P<path>\S+)")
_DENIAL = re.compile(r"\b(?:tool denied|tool denial|denied tool)\b")


def _strip_progress(stdout: str) -> str:
    """Stdout without lines starting with `PDI-PROGRESS:` — for parsing the final JSON."""
    return "\n".join(line for line in stdout.splitlines() if not line.startswith(PREFIX))


def _iter_json_objects(text: str):
    """Iterate over the valid JSON objects (`{...}`) in the text, in order of appearance.

    Scans from the first `{`, tries `json.loads` from that place to ever larger lengths via a raw decoder,
    which makes it possible to handle multi-line pretty-printed JSON between junk.
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
    """The last valid JSON object from the phase's stdout (after skipping progress lines).

    Raises `ValueError` when:
      - stdout is empty or contains only progress lines;
      - no fragment outside the progress is a JSON dict;
      - the status in the dict does not match `STATUSES`.
    """
    if not stdout or not stdout.strip():
        raise ValueError("phase_run result: stdout is empty")
    text = _strip_progress(stdout)
    if not text.strip():
        raise ValueError("phase_run result: stdout has only progress lines, no JSON")
    last: dict | None = None
    for obj in _iter_json_objects(text):
        if isinstance(obj, dict):
            last = obj
    if last is None:
        raise ValueError("phase_run result: stdout has no JSON object (an array or invalid data)")
    status = last.get("status")
    if status not in STATUSES:
        raise ValueError(f"phase_run result: status {status!r} is not one of {', '.join(STATUSES)}")
    return last


def read_progress(stdout: str) -> list[dict]:
    """Progress lines (dicts) from stdout; invalid JSON after the prefix is skipped without an exception."""
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
    """Number of unique files read by the persona in the stream (by the message „reads file <path>")."""
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
    """Number of tool denials in the stream (signal PRB-32: untrusted folder or no allow rule)."""
    count = 0
    for row in rows:
        msg = row.get("message") if isinstance(row, dict) else None
        if isinstance(msg, str) and _DENIAL.search(msg):
            count += 1
    return count


def read_cost(result: Any) -> float | None:
    """USD cost from the `phase_run.py` result; None when missing or non-numeric. `phase_result` keeps this one place,
    so that the N5 runner does not guess the `cost_usd` fields from result.json and progress in parallel."""
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
