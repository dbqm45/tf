#!/usr/bin/env python3
"""Odfiltrowany eksport logów faz z `$PDI_REGISTRY_PATH/runs/` do wejścia dla N5 (PR2).

Źródłowy katalog zawiera, dla każdego przebiegu fazy, zestaw plików ze wspólnym prefiksem
`<CHG-n>-<phase>-<YYYYMMDDThhmmssZ>`:
  - `*.result.json` — status/koszt/błąd/PR/cuts
  - `*.log` — pełny log fazy (polecenia dockera, wyjście Claude, komunikaty błędów)
  - `*.decisions.json` — snapshot decyzji zmiany przy wejściu w fazę (JSON lista wpisów)
  - `*.answers.json` — odpowiedzi do bramki poprzedniej fazy (JSON lista par Q/A)
  - `*.claude-settings.json`, `*.seccomp.json` — ustawienia uruchomienia

Eksport:
  python3 scripts/export_pdi_runs.py [--runs DIR] [--out DIR] [--manifest-only]

Do każdego przebiegu wychodzi obiekt manifestu z **tylko** polami potrzebnymi dla fixtur N5 (nie dołącza
sekretów, pełnej treści skillsettings ani surowych odpowiedzi persony). Skrypt dodatkowo renderuje
`decisions.md` dla fixtury, odtwarzając format `decision_record.py` (sekcja `## <statement>` z polami ref, id,
wyslano, kiedy, rodzaj, dlaczego oraz, gdy są, blokiem `- answers:`).

Pola każdego wpisu manifestu:
  - `run_id`, `change`, `phase`, `timestamp`
  - `status`, `cost_usd`, `error`, `step`, `pr`, `cuts`, `finished_at`
  - `error_lines`: 1–10 linii z loga, które pokazują przyczynę błędu (prefiks # albo linie `✗`), trim
  - `has_decisions`, `has_answers` (bool)
  - `decisions_count`, `answers_count`

Wyjście domyślne: `tmp/flow-evals/import/` z plikiem `manifest.json` + jeden podkatalog `<run_id>/` na każdy
przebieg ze zrenderowanym `decisions.md` i ewentualnie `answers.md`.

Źródło pola `out` ze strony fazy: `phase_run.py:cmd_run` (modes/mode-pdi/skills/pdi-decisions/scripts/).
Źródło pola `decisions.md` — kontrakt pdi 0.11.0 (`pdi/docs/plan-z1-decyzje-w-fazach.md`).
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
# Pola result.json, które przepuszczamy do manifestu (nic więcej). PRB-28 fix dodaje też `detail`,
# `permission_denials`; brakuje ich w starszych wynikach, więc odczyt jest tolerancyjny.
PASSTHROUGH = ("status", "cost_usd", "error", "step", "pr", "prs", "cuts", "finished_at",
               "detail", "permission_denials")
MAX_ERROR_LINES = 10


def find_runs(root: Path) -> list[str]:
    """Zwraca unikatowe prefiksy przebiegów (np. `CHG-3-delivery-20261105T170638Z`)."""
    seen: set[str] = set()
    for p in sorted(root.iterdir()):
        if not p.is_file():
            continue
        m = RUN_RE.match(p.name)
        if m:
            seen.add(f"{m.group('change')}-{m.group('phase')}-{m.group('ts')}")
    return sorted(seen)


def filter_result(data: dict) -> dict:
    """Przepuszcza TYLKO pola z `PASSTHROUGH`; wszystko inne odrzuca (draft persony, surowe eventy)."""
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in PASSTHROUGH}


def error_lines_from_log(log: str) -> list[str]:
    """Linie z loga wyglądające na przyczynę błędu (`# błąd`, `✗`, `# koniec:`), max MAX_ERROR_LINES, trim."""
    out: list[str] = []
    for line in log.splitlines():
        if ERROR_LINE_RE.match(line):
            out.append(line.strip()[:200])
        if len(out) >= MAX_ERROR_LINES:
            break
    return out


def render_decisions_md(entries: list[dict], change: str) -> str:
    """Renderuje `decisions.md` z listy wpisów (zgodne z `decision_record.py` zapisem).

    Każdy wpis: nagłówek `## <statement>`, pola `- ref`, `- id`, `- wyslano`, `- kiedy`, `- kto`, `- rodzaj`,
    `- dlaczego`, `- zrodlo`, `- szkic`; gdy `answers` — blok `- answers:` z parami `- pytanie:`/`- odpowiedz:`.
    Nagłówek YAML na początku (`artifact: decisions`).
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
        # decision_record.py:parse_entries czyta pary pytanie/odpowiedz jako top-level `- ` (nie w bloku
        # `- answers:` z wcięciem); format musi zgadzać się ze schematem pdi 0.11.0 i z `answers_lines` wprost.
        for a in e.get("answers") or []:
            q = _one_line(a.get("question", ""))
            ans = _one_line(a.get("answer", ""))
            rows.append(f"- pytanie: {q}")
            rows.append(f"- odpowiedz: {ans}")
        rows.append("")
    return "\n".join(rows) + "\n"


def render_answers_md(answers: list[dict]) -> str:
    """Pomocniczy plik `answers.md` z parami Q/A (do przeglądu przez człowieka — fixture ich nie wymaga)."""
    rows = ["# Odpowiedzi bramki", ""]
    for a in answers:
        rows.append(f"**Pytanie:** {_one_line(a.get('question', ''))}")
        rows.append(f"**Odpowiedź:** {_one_line(a.get('answer', ''))}")
        rows.append("")
    return "\n".join(rows) + "\n"


def _one_line(text: Any) -> str:
    """Tekst w jednym wierszu bez znaków sterujących; bezpieczny do wklejenia w markdown."""
    s = str(text or "").replace("\r", " ").replace("\n", " ")
    return " ".join(s.split())


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def export(runs_root: Path, out: Path, *, manifest_only: bool = False) -> dict:
    """Pełny eksport; zwraca manifest (lista obiektów) i tworzy katalogi/plik manifestu."""
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
    ap.add_argument("--runs", help="katalog z logami faz (domyślnie $PDI_REGISTRY_PATH/runs/)")
    ap.add_argument("--out", default="tmp/flow-evals/import",
                    help="katalog wynikowy (domyślnie tmp/flow-evals/import)")
    ap.add_argument("--manifest-only", action="store_true",
                    help="zapisz TYLKO manifest.json, bez podkatalogów na przebieg")
    a = ap.parse_args(argv)
    runs_arg = a.runs or (os.environ.get("PDI_REGISTRY_PATH") and
                          str(Path(os.environ["PDI_REGISTRY_PATH"]) / "runs"))
    if not runs_arg:
        runs_arg = str(Path("/Users/kamil/pdi-decisions") / "runs")
    runs_root = Path(runs_arg).expanduser().resolve()
    if not runs_root.is_dir():
        print(f"✗ brak katalogu {runs_root}")
        return 1
    out = Path(a.out).expanduser().resolve()
    summary = export(runs_root, out, manifest_only=a.manifest_only)
    print(f"✓ {summary['count']} przebiegów → {summary['out']}/manifest.json")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
