#!/usr/bin/env python3
"""Testy eksportu logów faz z $PDI_REGISTRY_PATH/runs/ (scripts/export_pdi_runs.py, PR2 N5).

python3 core/tests/test_export_pdi_runs.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next((p for p in HERE.parents if (p / "scripts" / "export_pdi_runs.py").is_file()), HERE.parent)
sys.path.insert(0, str(ROOT / "scripts"))
import export_pdi_runs as e  # noqa: E402


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="export-pdi-runs-"))


def _put(dir_: Path, name: str, payload) -> Path:
    f = dir_ / name
    f.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, (dict, list)):
        f.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    else:
        f.write_text(payload, encoding="utf-8")
    return f


def main() -> int:
    fails: list[str] = []
    total = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # ── find_runs ────────────────────────────────────────────────────────────
    tmp = _tmp()
    try:
        for name in ("CHG-1-intent-20261030T222959Z.result.json",
                     "CHG-1-intent-20261030T222959Z.log",
                     "CHG-1-intent-20261030T222959Z.decisions.json",
                     "CHG-3-delivery-20261105T170638Z.result.json",
                     "CHG-3-delivery-20261105T170638Z.log",
                     "notes.md",
                     "CHG-2-intent-20261103T204330Z.result.json"):
            _put(tmp, name, "{}" if name.endswith(".json") else "log")
        runs = e.find_runs(tmp)
        check(runs == ["CHG-1-intent-20261030T222959Z",
                       "CHG-2-intent-20261103T204330Z",
                       "CHG-3-delivery-20261105T170638Z"],
              f"F-1: {runs}")
    finally:
        shutil.rmtree(tmp)

    # ── filter_result ────────────────────────────────────────────────────────
    out = e.filter_result({"status": "done", "cost_usd": 0.4, "detail": "x",
                           "secret_token": "abc", "answers": [{"q": "y"}]})
    check("status" in out and "cost_usd" in out and "detail" in out
          and "secret_token" not in out and "answers" not in out,
          f"P-1: {out}")

    # ── error_lines_from_log ─────────────────────────────────────────────────
    log = "\n".join([
        "$ git status",
        "# błąd: Talos nie zostawił gałęzi story/*",
        "$ git push",
        "  ✗ test_fetch_page.py",
        "✗ pdi: coś padło",
        "# koniec: failed",
    ])
    lines = e.error_lines_from_log(log)
    check(len(lines) == 4 and any("Talos" in l for l in lines) and any("koniec" in l for l in lines),
          f"E-1: {lines}")

    # ── render_decisions_md ──────────────────────────────────────────────────
    md = e.render_decisions_md([
        {"id": "DEC-0001", "statement": "Zatwierdzamy X",
         "why": "bo\ntak\nchcemy",
         "decided_at": "2026-11-03", "decided_by": "pdi", "kind": "gate",
         "source_kind": "manual", "drafted_by": "ai",
         "answers": [{"question": "czy A?", "answer": "tak"},
                     {"question": "czy B?", "answer": "nie"}]}
    ], "CHG-9")
    check("## Zatwierdzamy X" in md and "ref: CHG-9/D1" in md and "id: DEC-0001" in md
          and "wyslano: tak" in md and "- pytanie: czy A?" in md
          and "- odpowiedz: nie" in md and "artifact: decisions" in md
          and "- answers:" not in md,   # top-level pary, nie `- answers:` z wcięciem (parse_entries)
          f"RD-1: md=\n{md[:400]}")
    # Nowa linia w `why` zastąpiona spacją — jeden wiersz w markdownie.
    check("bo tak chcemy" in md, f"RD-2: `why` nie jest jednowierszowe:\n{md[:400]}")

    md2 = e.render_decisions_md([{"statement": "Draft",  # bez id → wyslano: nie
                                  "decided_at": "2026-11-05", "kind": "triage"}], "CHG-7")
    check("wyslano: nie" in md2 and "ref: CHG-7/D1" in md2, f"RD-3: {md2[:200]}")

    # ── render_answers_md ────────────────────────────────────────────────────
    am = e.render_answers_md([{"question": "Q1?", "answer": "A1"}])
    check("**Pytanie:** Q1?" in am and "**Odpowiedź:** A1" in am, f"RA-1: {am[:200]}")

    # ── _one_line ────────────────────────────────────────────────────────────
    v = e._one_line("a\nb\r\nc")
    check(v == "a b c", f"O-1: {v!r}")
    check(e._one_line(None) == "", f"O-2: {e._one_line(None)!r}")

    # ── full export flow ─────────────────────────────────────────────────────
    tmp = _tmp()
    try:
        runs = tmp / "runs"
        out = tmp / "import"
        _put(runs, "CHG-3-intent-20261103T205530Z.result.json",
             {"status": "done", "cost_usd": 0.38, "detail": "ok", "finished_at": "2026-11-03T20:56:00Z",
              "secret": "nope"})
        _put(runs, "CHG-3-intent-20261103T205530Z.log",
             "$ claude --print\n# koniec: done\n")
        _put(runs, "CHG-3-intent-20261103T205530Z.decisions.json",
             [{"id": "DEC-0012", "statement": "triage", "decided_at": "2026-11-03", "kind": "triage"}])
        _put(runs, "CHG-3-intent-20261103T205530Z.answers.json",
             [{"question": "Q?", "answer": "A"}])
        # drugi przebieg bez decisions/answers
        _put(runs, "CHG-1-delivery-20261031T132001Z.result.json",
             {"status": "failed", "step": "cuts", "error": "brak cięć"})
        _put(runs, "CHG-1-delivery-20261031T132001Z.log",
             "# błąd: brak cięć\n# koniec: failed\n")
        summary = e.export(runs, out)
        check(summary["count"] == 2, f"X-1: {summary}")
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        check(len(manifest) == 2 and all("secret" not in str(m) for m in manifest),
              f"X-2: sekret wyciekł: {manifest}")
        intent_entry = next((m for m in manifest if m["phase"] == "intent"), None)
        check(intent_entry and intent_entry["has_decisions"] and intent_entry["has_answers"]
              and intent_entry["status"] == "done" and intent_entry["cost_usd"] == 0.38,
              f"X-3: {intent_entry}")
        delivery_entry = next((m for m in manifest if m["phase"] == "delivery"), None)
        check(delivery_entry and not delivery_entry["has_decisions"]
              and delivery_entry["status"] == "failed" and delivery_entry["step"] == "cuts"
              and any("brak cięć" in l for l in delivery_entry["error_lines"]),
              f"X-4: {delivery_entry}")
        # Pliki per run
        intent_run = out / "CHG-3-intent-20261103T205530Z"
        check(intent_run.is_dir() and (intent_run / "decisions.md").is_file()
              and (intent_run / "answers.md").is_file() and (intent_run / "manifest.json").is_file(),
              f"X-5: brak plików per-run w {intent_run}")
        # manifest-only pomija podkatalogi
        out2 = tmp / "import2"
        e.export(runs, out2, manifest_only=True)
        check((out2 / "manifest.json").is_file() and not (out2 / "CHG-3-intent-20261103T205530Z").exists(),
              "X-6: manifest-only zrobił podkatalogi")
    finally:
        shutil.rmtree(tmp)

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów export_pdi_runs")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
