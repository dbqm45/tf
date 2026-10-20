#!/usr/bin/env python3
"""
Egzamin branżowy EV: pytania z odpowiedzią wzorcową i sprawdzeniami (tests/ev_exam/<obszar>.json), zadawane modelowi
przez Claude Code (`claude -p`) z fabryką i bez niej — mierzy, ile wiedzy wnosi fabryka.

  python3 tests/run_ev_exam.py --validate                               # tylko sprawdź pytania (bez modelu, w CI)
  python3 tests/run_ev_exam.py --models haiku                           # cały egzamin, z fabryką i bez (płatne)
  python3 tests/run_ev_exam.py --areas ocpp,roaming --models haiku,sonnet --budget-usd 5
  python3 tests/run_ev_exam.py --ids ocpp:faulted-vs-unavailable --no-baseline --yes

Przebieg na modelu kosztuje — runner pokazuje prognozę i pyta o zgodę (--yes pomija pytanie; tylko za zgodą
człowieka). Uruchamianie, sprawdzanie odpowiedzi i ocena modelem pomocniczym jak w tests/run_skill_evals.py
(te same funkcje). Wynik: raport .md i surowe wyniki .jsonl. Format pytań: tests/ev_exam/README.md.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import re
import sys
import threading
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
EXAM = HERE / "ev_exam"
_spec = importlib.util.spec_from_file_location("run_skill_evals", HERE / "run_skill_evals.py")
rse = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rse)
SKILLS, ROOT = rse.SKILLS, rse.ROOT
KB_REGISTRY = SKILLS / "dom-ev-knowledge-base" / "references" / "zrodla.json"


def _kb_ids() -> set[str]:
    try:
        d = json.loads(KB_REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {s.get("id") for s in (d.get("sources", []) if isinstance(d, dict) else d)}


def validate_file(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"{path.name}: niepoprawny JSON ({e})"]
    errs, kb, ids = [], _kb_ids(), set()
    if data.get("obszar") != path.stem:
        errs.append(f"{path.name}: obszar={data.get('obszar')!r} ≠ nazwa pliku")
    qs = data.get("pytania") or []
    if not qs:
        errs.append(f"{path.name}: brak pytań")
    for i, q in enumerate(qs):
        where = f"{path.name}#{q.get('id', i)}"
        if not q.get("id") or q["id"] in ids:
            errs.append(f"{where}: brak lub powtórzone id")
        ids.add(q.get("id"))
        if len(str(q.get("pytanie", ""))) < 15:
            errs.append(f"{where}: za krótkie pytanie")
        if not str(q.get("wzorzec", "")).strip():
            errs.append(f"{where}: brak odpowiedzi wzorcowej (wzorzec)")
        if q.get("trudnosc") not in (1, 2, 3):
            errs.append(f"{where}: trudnosc musi być 1, 2 albo 3")
        for src in [s.strip() for s in str(q.get("zrodlo", "")).split(",") if s.strip()] or [""]:
            if src.startswith("kb:"):
                if src[3:] not in kb:
                    errs.append(f"{where}: źródło {src} nie ma w zrodla.json")
            elif not (SKILLS / src / "SKILL.md").exists():
                errs.append(f"{where}: źródło {src!r} to nie skill fabryki ani kb:<id>")
        checks = q.get("checks") or {}
        groups = checks.get("all") or []
        if not groups:
            errs.append(f"{where}: wymagane checks.all")
        bad_rx = False
        for g in groups:
            if not isinstance(g, list) or not g:
                errs.append(f"{where}: checks.all to lista niepustych list alternatyw")
                bad_rx = True
                continue
            for rx in g:
                try:
                    re.compile(rx)
                except re.error as e:
                    errs.append(f"{where}: zły regex {rx!r}: {e}")
                    bad_rx = True
        for rx in checks.get("none") or []:
            try:
                re.compile(rx)
            except re.error as e:
                errs.append(f"{where}: zły regex w none {rx!r}: {e}")
                bad_rx = True
        if groups and not bad_rx and q.get("wzorzec"):
            ok, misses = rse.evaluate_checks(q["wzorzec"], checks)
            if not ok:
                errs.append(f"{where}: odpowiedź wzorcowa nie spełnia własnych sprawdzeń: {misses}")
    return errs


def load_questions(exam_dir: Path = EXAM, areas: list[str] | None = None) -> list[dict]:
    out = []
    for p in sorted(exam_dir.glob("*.json")):
        if areas and p.stem not in areas:
            continue
        for q in json.loads(p.read_text(encoding="utf-8")).get("pytania") or []:
            out.append({**q, "obszar": p.stem})
    return out


def count_questions(exam_dir: Path = EXAM) -> int:
    return len(load_questions(exam_dir))


def run_question(q: dict, model: str, mode: str, args) -> dict:
    sc = {"skill": "_egzamin", "id": q["id"], "expect": "trigger", "prompt": q["pytanie"] + " Odpowiedz zwięźle.",
          "checks": q["checks"], "rubric": q.get("rubric")}
    r = rse.run_one(sc, model, mode == "bez", args)
    return {"obszar": q["obszar"], "id": q["id"], "model": model, "mode": mode, "trudnosc": q.get("trudnosc"),
            "passed": bool(r["checks_ok"]) and not r["error"], "misses": r["misses"], "error": r["error"],
            "cost": r["cost"], "seconds": r["seconds"], "skills_used": r["skills_used"], "answer": r["answer"]}


def report(results: list[dict], out: Path) -> None:
    lines = [f"# Egzamin branżowy EV — {datetime.now():%Y-%m-%d %H:%M}", "",
             "| Model | Tryb | Zaliczone | Wynik |", "|---|---|---|---|"]
    score = {}
    for model in sorted({r["model"] for r in results}):
        for mode in ("fabryka", "bez"):
            rs = [r for r in results if r["model"] == model and r["mode"] == mode]
            if not rs:
                continue
            ok = sum(r["passed"] for r in rs)
            score[(model, mode)] = 100 * ok / len(rs)
            lines.append(f"| {model} | {'z fabryką' if mode == 'fabryka' else 'bez fabryki'} | {ok}/{len(rs)} | {score[(model, mode)]:.1f} % |")
    lines.append("")
    for model in sorted({m for m, _ in score}):
        if (model, "fabryka") in score and (model, "bez") in score:
            delta = score[(model, "fabryka")] - score[(model, "bez")]
            lines.append(f"Różnica ({model}): {delta:+.1f} pkt proc. na korzyść {'fabryki' if delta >= 0 else 'modelu bez fabryki'}.")
    lines += ["", "## Wynik według obszaru", "", "| Obszar | Model | Tryb | Zaliczone |", "|---|---|---|---|"]
    for key in sorted({(r["obszar"], r["model"], r["mode"]) for r in results}):
        rs = [r for r in results if (r["obszar"], r["model"], r["mode"]) == key]
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {sum(r['passed'] for r in rs)}/{len(rs)} |")
    failed = [r for r in results if not r["passed"]]
    lines += ["", "## Niezaliczone", ""]
    lines += [f"- `{r['obszar']}:{r['id']}` ({r['model']}, {r['mode']}): {'; '.join(r['misses']) or r['error']}" for r in failed] or ["(brak)"]
    lines += ["", f"Koszt łącznie: ${sum(r['cost'] for r in results):.3f}"]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--validate", action="store_true", help="tylko sprawdź pliki pytań")
    ap.add_argument("--dir", default=str(EXAM), help="katalog z plikami pytań")
    ap.add_argument("--areas", default="", help="obszary (nazwy plików), po przecinku")
    ap.add_argument("--ids", default="", help="pytania: id albo obszar:id, po przecinku")
    ap.add_argument("--models", default="haiku")
    ap.add_argument("--no-baseline", action="store_true", help="bez przebiegu bez fabryki")
    ap.add_argument("--judge", default="haiku", help="model oceniający, gdy wyrażenie nie trafi ('none' = bez oceny)")
    ap.add_argument("--max-turns", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--budget-usd", type=float, default=rse.DEFAULT_BUDGET_USD)
    ap.add_argument("--isolated", action="store_true", help="bez osobistych ustawień i skilli (--setting-sources project,local)")
    ap.add_argument("--out", default="")
    ap.add_argument("--yes", action="store_true", help="bez pytania o zgodę na koszt")
    args = ap.parse_args(argv)
    exam_dir = Path(args.dir)

    errs = [e for p in sorted(exam_dir.glob("*.json")) for e in validate_file(p)]
    if args.validate:
        for e in errs:
            print(f"✗ {e}")
        print(f"{'✓' if not errs else '✗'} egzamin EV: {count_questions(exam_dir) if not errs else '?'} pytań w "
              f"{len(list(exam_dir.glob('*.json')))} obszarach, błędów: {len(errs)}")
        return 1 if errs else 0
    if errs:
        print("✗ Popraw pytania (python3 tests/run_ev_exam.py --validate):")
        for e in errs[:20]:
            print(f"  {e}")
        return 2
    qs = load_questions(exam_dir, [a.strip() for a in args.areas.split(",") if a.strip()] or None)
    if args.ids:
        want = [x.strip() for x in args.ids.split(",") if x.strip()]
        sel = [q for q in qs if q["id"] in want or f"{q['obszar']}:{q['id']}" in want]
        known = {q["id"] for q in sel} | {f"{q['obszar']}:{q['id']}" for q in sel}
        unknown = [w for w in want if w not in known]
        if unknown:
            print(f"✗ Nie ma pytań: {', '.join(unknown)}")
            return 2
        qs = sel
    if not qs:
        print("Brak pytań do zadania.")
        return 2
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    modes = ["fabryka"] + ([] if args.no_baseline else ["bez"])
    jobs = [(q, m, mode) for q in qs for m in models for mode in modes]
    guess = sum(rse.COST_GUESS.get(m, 0.15) for _, m, _ in jobs)
    print(f"Pytań: {len(qs)}, przebiegów: {len(jobs)} ({', '.join(models)}; {' i '.join(modes)}). "
          f"Zgrubna prognoza kosztu: ~${guess:.2f}, limit: ${args.budget_usd:.2f}.")
    if not args.yes:
        if input("Uruchomić? [t/N] ").strip().lower() not in ("t", "tak", "y", "yes"):
            return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_md = Path(args.out) if args.out else Path.cwd() / f"ev-exam-{stamp}.md"
    out_jsonl = out_md.with_suffix(".jsonl")
    run_args = SimpleNamespace(bare=False, isolated=args.isolated, max_turns=args.max_turns, timeout=args.timeout,
                               judge=args.judge)
    results, spent, lock, stop = [], 0.0, threading.Lock(), threading.Event()

    def task(job):
        nonlocal spent
        if stop.is_set():
            return None
        r = run_question(*job, run_args)
        with lock:
            spent += r["cost"]
            if spent >= args.budget_usd or (r["error"] and rse.LIMIT_RE.search(r["error"])):
                stop.set()
            with out_jsonl.open("a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"  {'✓' if r['passed'] else '✗'} {r['obszar']}:{r['id']:<34} {r['model']:<7} {r['mode']:<8} ${r['cost']:.3f}"
                  f"{'  ' + r['error'] if r['error'] else ''}")
        return r

    with cf.ThreadPoolExecutor(max_workers=max(1, args.parallel)) as ex:
        results = [r for r in ex.map(task, jobs) if r]
    report(results, out_md)
    print(f"Raport: {out_md} (surowe wyniki: {out_jsonl}); koszt ${spent:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
