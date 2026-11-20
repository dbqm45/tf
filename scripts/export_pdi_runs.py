#!/usr/bin/env python3
"""A filtered export of phase logs from `$PDI_REGISTRY_PATH/runs/` as input for N5 (PR2).

The source directory contains, for each phase run, a set of files with a common prefix
`<CHG-n>-<phase>-<YYYYMMDDThhmmssZ>`:
  - `*.result.json` — status/cost/error/PR/cuts
  - `*.log` — the full phase log (docker commands, Claude output, error messages)
  - `*.decisions.json` — a snapshot of the change decisions on entering the phase (a JSON list of entries)
  - `*.answers.json` — answers to the previous phase gate (a JSON list of Q/A pairs)
  - `*.claude-settings.json`, `*.seccomp.json` — run settings

Export:
  python3 scripts/export_pdi_runs.py [--runs DIR] [--out DIR] [--manifest-only]

For each run a manifest object is emitted with **only** the fields needed for the N5 fixtures (it does not include
secrets, the full skillsettings content, or raw persona responses). The script additionally renders
`decisions.md` for the fixture, reproducing the `decision_record.py` format (a `## <statement>` section with the fields ref, id,
wyslano, kiedy, rodzaj, dlaczego and, when present, an `- answers:` block).

Fields of each manifest entry:
  - `run_id`, `change`, `phase`, `timestamp`
  - `status`, `cost_usd`, `error`, `step`, `pr`, `cuts`, `finished_at`
  - `error_lines`: 1–10 log lines that show the cause of the error (a # prefix or `✗` lines), trimmed
  - `has_decisions`, `has_answers` (bool)
  - `decisions_count`, `answers_count`

Default output: `tmp/flow-evals/import/` with a `manifest.json` file + one `<run_id>/` subdirectory for each
run with a rendered `decisions.md` and possibly `answers.md`.

Source of the `out` field from the phase side: `phase_run.py:cmd_run` (modes/mode-pdi/skills/pdi-decisions/scripts/).
Source of the `decisions.md` field — the pdi 0.11.0 contract (`pdi/docs/plan-z1-decyzje-w-fazach.md`).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

RUN_RE = re.compile(r"^(?P<change>CHG-\d+)-(?P<phase>intent|requirements|architecture|design|delivery)-"
                    r"(?P<ts>\d{8}T\d{6}Z)")
ERROR_LINE_RE = re.compile(r"^(?:#\s*(?:błąd|koniec|error)|\s*✗)", re.I)
# Fields of result.json that we pass through to the manifest (nothing more). The PRB-28 fix also adds `detail`,
# `permission_denials`; they are missing in older results, so reading is tolerant.
PASSTHROUGH = ("status", "cost_usd", "error", "step", "pr", "prs", "cuts", "finished_at",
               "detail", "permission_denials")
MAX_ERROR_LINES = 10


def find_runs(root: Path) -> list[str]:
    """Returns the unique run prefixes (e.g. `CHG-3-delivery-20261105T170638Z`)."""
    seen: set[str] = set()
    for p in sorted(root.iterdir()):
        if not p.is_file():
            continue
        m = RUN_RE.match(p.name)
        if m:
            seen.add(f"{m.group('change')}-{m.group('phase')}-{m.group('ts')}")
    return sorted(seen)


def filter_result(data: dict) -> dict:
    """Passes through ONLY the fields from `PASSTHROUGH`; rejects everything else (persona draft, raw events)."""
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in PASSTHROUGH}


def error_lines_from_log(log: str) -> list[str]:
    """Log lines that look like the cause of an error (`# błąd`, `✗`, `# koniec:`), max MAX_ERROR_LINES, trimmed."""
    out: list[str] = []
    for line in log.splitlines():
        if ERROR_LINE_RE.match(line):
            out.append(line.strip()[:200])
        if len(out) >= MAX_ERROR_LINES:
            break
    return out


def render_decisions_md(entries: list[dict], change: str) -> str:
    """Renders `decisions.md` from a list of entries (consistent with the `decision_record.py` format).

    Each entry: a `## <statement>` heading, the fields `- ref`, `- id`, `- wyslano`, `- kiedy`, `- kto`, `- rodzaj`,
    `- dlaczego`, `- zrodlo`, `- szkic`; when `answers` — an `- answers:` block with `- pytanie:`/`- odpowiedz:` pairs.
    A YAML header at the start (`artifact: decisions`).
    """
    rows = [f"---",
            f"artifact: decisions",
            f"phase: plan",
            f"status: draft",
            f"version: 1",
            f"author: pdi",
            f"inputs: []",
            f"change: {change}",
            f"---",
            f"# Decyzje zmiany {change}",
            ""]
    for i, e in enumerate(entries, start=1):
        ref = f"{change}/D{i}"
        rows.append(f"## {e.get('statement', '').strip()}")
        rows.append(f"- ref: {ref}")
        if e.get("id"):
            rows.append(f"- id: {e['id']}")
            rows.append(f"- wyslano: tak")
        else:
            rows.append(f"- wyslano: nie")
        if e.get("decided_at"):
            rows.append(f"- kiedy: {e['decided_at']}")
        if e.get("decided_by"):
            rows.append(f"- kto: {e['decided_by']}")
        if e.get("kind"):
            rows.append(f"- rodzaj: {e['kind']}")
        if e.get("why"):
            rows.append(f"- dlaczego: {_one_line(e['why'])}")
        rows.append(f"- zrodlo: {e.get('source_kind') or 'manual'}")
        rows.append(f"- szkic: {e.get('drafted_by') or 'ai'}")
        # decision_record.py:parse_entries reads pytanie/odpowiedz pairs as top-level `- ` (not in an indented
        # `- answers:` block); the format must match the pdi 0.11.0 schema and `answers_lines` directly.
        for a in e.get("answers") or []:
            q = _one_line(a.get("question", ""))
            ans = _one_line(a.get("answer", ""))
            rows.append(f"- pytanie: {q}")
            rows.append(f"- odpowiedz: {ans}")
        rows.append("")
    return "\n".join(rows) + "\n"


def render_answers_md(answers: list[dict]) -> str:
    """An auxiliary `answers.md` file with Q/A pairs (for human review — the fixture does not require them)."""
    rows = ["# Gate answers", ""]
    for a in answers:
        rows.append(f"**Question:** {_one_line(a.get('question', ''))}")
        rows.append(f"**Answer:** {_one_line(a.get('answer', ''))}")
        rows.append("")
    return "\n".join(rows) + "\n"


def _one_line(text: Any) -> str:
    """Text on one line without control characters; safe to paste into markdown."""
    s = str(text or "").replace("\r", " ").replace("\n", " ")
    return " ".join(s.split())


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def export(runs_root: Path, out: Path, *, manifest_only: bool = False) -> dict:
    """A full export; returns the manifest (a list of objects) and creates the directories/manifest file."""
    out.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    for run_id in find_runs(runs_root):
        m = RUN_RE.match(run_id)
        if not m:
            continue
        change = m.group("change")
        phase = m.group("phase")
        ts = m.group("ts")
        result = _read_json(runs_root / f"{run_id}.result.json") or {}
        decisions = _read_json(runs_root / f"{run_id}.decisions.json") or []
        answers = _read_json(runs_root / f"{run_id}.answers.json") or []
        log_path = runs_root / f"{run_id}.log"
        log_text = log_path.read_text(encoding="utf-8", errors="ignore") if log_path.is_file() else ""
        entry = {
            "run_id": run_id,
            "change": change,
            "phase": phase,
            "timestamp": ts,
            **filter_result(result),
            "error_lines": error_lines_from_log(log_text),
            "has_decisions": isinstance(decisions, list) and len(decisions) > 0,
            "has_answers": isinstance(answers, list) and len(answers) > 0,
            "decisions_count": len(decisions) if isinstance(decisions, list) else 0,
            "answers_count": len(answers) if isinstance(answers, list) else 0,
        }
        manifest.append(entry)
        if manifest_only:
            continue
        run_dir = out / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "manifest.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        if isinstance(decisions, list) and decisions:
            (run_dir / "decisions.md").write_text(render_decisions_md(decisions, change), encoding="utf-8")
        if isinstance(answers, list) and answers:
            (run_dir / "answers.md").write_text(render_answers_md(answers), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"count": len(manifest), "out": str(out)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", help="directory with the phase logs (default $PDI_REGISTRY_PATH/runs/)")
    ap.add_argument("--out", default="tmp/flow-evals/import",
                    help="output directory (default tmp/flow-evals/import)")
    ap.add_argument("--manifest-only", action="store_true",
                    help="write ONLY manifest.json, without a subdirectory per run")
    a = ap.parse_args(argv)
    runs_arg = a.runs or (os.environ.get("PDI_REGISTRY_PATH") and
                          str(Path(os.environ["PDI_REGISTRY_PATH"]) / "runs"))
    if not runs_arg:
        runs_arg = str(Path("/Users/kamil/pdi-decisions") / "runs")
    runs_root = Path(runs_arg).expanduser().resolve()
    if not runs_root.is_dir():
        print(f"✗ no such directory: {runs_root}")
        return 1
    out = Path(a.out).expanduser().resolve()
    summary = export(runs_root, out, manifest_only=a.manifest_only)
    print(f"✓ {summary['count']} runs → {summary['out']}/manifest.json")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
