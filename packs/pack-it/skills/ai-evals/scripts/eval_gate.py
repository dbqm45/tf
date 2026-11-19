#!/usr/bin/env python3
"""
Bramka ewaluacji w CI: próg z rozrzutu linii bazowej, zadania regresyjne, budżet. Nie uruchamia modelu.

  python3 .claude/skills/ai-evals/scripts/eval_gate.py baseline baza1.jsonl baza2.jsonl baza3.jsonl \\
          [--margin 0.02] [--out evals/baseline.json]
  python3 .claude/skills/ai-evals/scripts/eval_gate.py check wyniki.jsonl --baseline evals/baseline.json \\
          [--budget-usd 5] [--strict] [--json] [--report raport.md]

Wejście: wyniki przebiegu ewaluacji produktu w JSON Lines, jedna linia na próbę:
  {"id": "zwrot-17", "passed": true, "layer": "regression", "cost_usd": 0.012, "trial": 2}
`id` i `passed` są wymagane; `layer` równe `regression` (albo `regresyjny`) oznacza zadanie ze zbioru regresyjnego;
`cost_usd` to koszt próby; kilka linii z tym samym `id` to powtórzone próby (k).

`baseline` liczy z kilku przebiegów obecnej wersji (3–5) rozrzut odsetka sukcesów (min, max, średnia), próg
= dolna granica rozrzutu − margines (margines ustala zespół; domyślnie 0) i zadania stabilne (zaliczone w każdym
przebiegu). `check` ocenia przebieg kandydata:
  wstrzymaj  sukces poniżej progu, porażka zadania z warstwy regresyjnej albo koszt ponad budżet
  zbadaj     sukces poniżej dolnej granicy rozrzutu (w marginesie), padło zadanie stabilne w bazie, zestaw zadań inny
             niż w bazie albo podano budżet, a wyniki nie mają kosztu
  wypuść     pozostałe
Metryki: sukces (zaliczone próby / próby), pass^k (zadania zaliczone we wszystkich k próbach), pass@k (zaliczone
w co najmniej jednej), koszt.

Kod wyjścia: 0 — wypuść albo zbadaj; 1 — wstrzymaj (ze --strict także zbadaj); 2 — błąd wywołania albo danych
(pusty plik wyników to błąd, nie „0 porażek”). Tylko biblioteka standardowa, bez sieci.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

REGRESSION_LAYERS = {"regression", "regresyjny"}
MIN_BASELINE_RUNS = 3


class DataError(Exception):
    pass


def load_run(path: Path) -> list[dict]:
    """Próby z pliku JSON Lines; DataError przy braku pliku, pustym pliku, złej linii albo braku `id`/`passed`."""
    if not path.is_file():
        raise DataError(f"brak pliku wyników: {path}")
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise DataError(f"{path}:{n}: linia nie jest poprawnym JSON ({e.msg})") from None
        if not isinstance(row, dict) or "id" not in row or not isinstance(row.get("passed"), bool):
            raise DataError(f"{path}:{n}: wymagane pola `id` i `passed` (true/false)")
        cost = row.get("cost_usd")
        if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0):
            raise DataError(f"{path}:{n}: `cost_usd` ma być liczbą nieujemną")
        rows.append(row)
    if not rows:
        raise DataError(f"{path}: brak wyników — pusty przebieg nie jest dowodem jakości")
    return rows


def metrics(rows: list[dict]) -> dict:
    by_task: dict[str, list[bool]] = {}
    layers: dict[str, str] = {}
    for r in rows:
        tid = str(r["id"])
        by_task.setdefault(tid, []).append(r["passed"])
        if r.get("layer"):
            layers[tid] = str(r["layer"]).strip().lower()
    costs = [r["cost_usd"] for r in rows if r.get("cost_usd") is not None]
    attempts = len(rows)
    tasks = len(by_task)
    return {
        "attempts": attempts, "tasks": tasks, "k": max(len(v) for v in by_task.values()),
        "success": sum(r["passed"] for r in rows) / attempts,
        "pass_all_k": sum(all(v) for v in by_task.values()) / tasks,
        "pass_any_k": sum(any(v) for v in by_task.values()) / tasks,
        "cost_usd": sum(costs) if costs else None,
        "cost_known_attempts": len(costs),
        "task_ids": sorted(by_task),
        "all_passed": sorted(t for t, v in by_task.items() if all(v)),
        "failed": sorted(t for t, v in by_task.items() if not all(v)),
        "regression_layer_failures": sorted(t for t, v in by_task.items() if not all(v) and layers.get(t) in REGRESSION_LAYERS),
    }


def pct(x: float) -> str:
    return f"{x * 100:.1f}%".replace(".", ",")


def cmd_baseline(a) -> int:
    runs = [metrics(load_run(Path(p))) for p in a.runs]
    rates = [m["success"] for m in runs]
    stable = set(runs[0]["all_passed"])
    for m in runs[1:]:
        stable &= set(m["all_passed"])
    low = min(rates)
    data = {
        "version": 1, "created": dt.date.today().isoformat(), "runs": len(runs),
        "success": {"min": low, "max": max(rates), "mean": sum(rates) / len(rates)},
        "margin": a.margin, "threshold": low - a.margin,
        "tasks": sorted(set().union(*(m["task_ids"] for m in runs))),
        "stable_tasks": sorted(stable), "k": max(m["k"] for m in runs),
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Baza: {len(runs)} przebiegów, sukces {pct(low)}–{pct(max(rates))} (średnio {pct(data['success']['mean'])}), "
          f"margines {pct(a.margin)}, próg {pct(data['threshold'])}; zadań {len(data['tasks'])}, stabilnych {len(stable)} → {out}")
    if len(runs) < MIN_BASELINE_RUNS:
        print(f"⚠ Baza z {len(runs)} przebiegu(-ów): rozrzut jest niewiarygodny — powtórz bazę {MIN_BASELINE_RUNS}–5 razy, "
              f"zanim próg zacznie blokować.")
    if a.margin == 0:
        print("· Margines 0: próg to dolna granica rozrzutu. Margines ustala zespół (--margin) i zapisuje, kto i dlaczego.")
    return 0


def judge(m: dict, base: dict, budget: float | None) -> tuple[str, list[str], list[str]]:
    """(werdykt, powody, regresje zadań stabilnych)."""
    stop, look = [], []
    success, low, threshold = m["success"], base["success"]["min"], base["threshold"]
    if success < threshold:
        stop.append(f"sukces {pct(success)} poniżej progu {pct(threshold)} (baza {pct(low)}–{pct(base['success']['max'])}, "
                    f"margines {pct(base.get('margin', 0))})")
    elif success < low:
        look.append(f"sukces {pct(success)} poniżej dolnej granicy rozrzutu bazy {pct(low)}, ale w marginesie (próg {pct(threshold)})")
    if m["regression_layer_failures"]:
        stop.append(f"porażka zadań z warstwy regresyjnej: {', '.join(m['regression_layer_failures'])}")
    regressions = sorted(set(base.get("stable_tasks") or []) & set(m["failed"]))
    if regressions:
        look.append(f"padły zadania stabilne w bazie: {', '.join(regressions)}")
    if set(base.get("tasks") or []) != set(m["task_ids"]):
        missing = sorted(set(base.get("tasks") or []) - set(m["task_ids"]))
        new = sorted(set(m["task_ids"]) - set(base.get("tasks") or []))
        look.append(f"zestaw zadań inny niż w bazie (brakuje {len(missing)}, nowych {len(new)}) — policz bazę na tym samym zestawie")
    if budget is not None:
        if m["cost_usd"] is None:
            look.append("podano budżet, a wyniki nie mają pola cost_usd — koszt przebiegu jest nieznany")
        elif m["cost_usd"] > budget:
            stop.append(f"koszt {m['cost_usd']:.2f} USD ponad budżet {budget:.2f} USD")
        elif m["cost_known_attempts"] < m["attempts"]:
            look.append(f"koszt znany tylko dla {m['cost_known_attempts']} z {m['attempts']} prób — suma jest zaniżona")
    verdict = "wstrzymaj" if stop else ("zbadaj" if look else "wypuść")
    return verdict, stop + look, regressions


def report_text(out: dict) -> str:
    b = out["baseline"]
    cost = "nieznany" if out["cost_usd"] is None else f"{out['cost_usd']:.2f} USD"
    budget = "" if out["budget_usd"] is None else f" (budżet {out['budget_usd']:.2f} USD)"
    lines = [
        f"Werdykt: {out['verdict']}",
        f"Wynik: sukces {pct(out['success'])} vs baza {pct(b['min'])}–{pct(b['max'])} (średnio {pct(b['mean'])}, "
        f"{b['runs']} przebiegów) | próg {pct(out['threshold'])}",
        f"Próby: {out['attempts']} na {out['tasks']} zadaniach, k = {out['k']} | pass^k {pct(out['pass_all_k'])} | "
        f"pass@k {pct(out['pass_any_k'])}",
        f"Koszt: {cost}{budget}",
    ]
    if out["reasons"]:
        lines.append("Powody:")
        lines += [f"- {r}" for r in out["reasons"]]
    if out["regressions"]:
        lines.append(f"Regresje (stabilne w bazie, teraz z porażką): {', '.join(out['regressions'])}")
    if out["regression_layer_failures"]:
        lines.append(f"Porażki warstwy regresyjnej: {', '.join(out['regression_layer_failures'])}")
    return "\n".join(lines)


def cmd_check(a) -> int:
    m = metrics(load_run(Path(a.results)))
    base_path = Path(a.baseline)
    if not base_path.is_file():
        raise DataError(f"brak pliku bazy: {base_path} (utwórz: eval_gate.py baseline <przebiegi…> --out {base_path})")
    try:
        base = json.loads(base_path.read_text(encoding="utf-8"))
        float(base["threshold"]), float(base["success"]["min"]), float(base["success"]["max"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        raise DataError(f"{base_path}: to nie jest plik bazy z eval_gate.py baseline") from None
    verdict, reasons, regressions = judge(m, base, a.budget_usd)
    out = {
        "verdict": verdict, "success": m["success"], "threshold": base["threshold"],
        "baseline": {"min": base["success"]["min"], "max": base["success"]["max"], "mean": base["success"].get("mean"),
                     "runs": base.get("runs"), "margin": base.get("margin", 0), "created": base.get("created")},
        "pass_all_k": m["pass_all_k"], "pass_any_k": m["pass_any_k"], "k": m["k"], "tasks": m["tasks"],
        "attempts": m["attempts"], "cost_usd": m["cost_usd"], "budget_usd": a.budget_usd,
        "regressions": regressions, "regression_layer_failures": m["regression_layer_failures"], "reasons": reasons,
    }
    text = report_text(out)
    if a.report:
        rp = Path(a.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text("## Bramka ewaluacji\n\n" + text.replace("\n", "  \n") + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2) if a.json else text)
    return 1 if verdict == "wstrzymaj" or (a.strict and verdict == "zbadaj") else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Bramka ewaluacji w CI (nie uruchamia modelu). Kod wyjścia: 0 wypuść albo "
                                             "zbadaj, 1 wstrzymaj (ze --strict także zbadaj), 2 błąd wywołania albo danych.",
                                 epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baseline", help="rozrzut i próg z kilku przebiegów obecnej wersji")
    b.add_argument("runs", nargs="+", help="pliki wyników przebiegów bazy (JSON Lines)")
    b.add_argument("--margin", type=float, default=0.0, help="margines poniżej dolnej granicy rozrzutu, ułamek (np. 0.02)")
    b.add_argument("--out", default="evals/baseline.json", help="plik bazy (domyślnie evals/baseline.json)")
    c = sub.add_parser("check", help="ocena przebiegu kandydata względem bazy")
    c.add_argument("results", help="plik wyników kandydata (JSON Lines)")
    c.add_argument("--baseline", default="evals/baseline.json", help="plik bazy z polecenia baseline")
    c.add_argument("--budget-usd", type=float, default=None, help="budżet przebiegu w USD (suma cost_usd)")
    c.add_argument("--strict", action="store_true", help="kod 1 także przy werdykcie zbadaj")
    c.add_argument("--json", action="store_true", help="wynik w JSON")
    c.add_argument("--report", help="zapisz raport Markdown (np. do komentarza w PR)")
    try:
        a = ap.parse_args(argv)
        if a.cmd == "baseline" and not 0 <= a.margin < 1:
            raise DataError("--margin ma być ułamkiem z przedziału [0, 1), np. 0.02")
        return cmd_baseline(a) if a.cmd == "baseline" else cmd_check(a)
    except DataError as e:
        print(f"błąd: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
