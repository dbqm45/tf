#!/usr/bin/env python3
"""Testy skryptu ai-evals/scripts/eval_gate.py — bramka ewaluacji w CI: próg z rozrzutu linii bazowej, zadania
regresyjne, budżet (T4 planu programu AI; docs/plans/2026-11-11-program-ai-luki-w-fabryce.md w repozytorium fabryki).

Skrypt nie uruchamia modelu. Czyta wyniki przebiegu ewaluacji produktu (JSON Lines, jedna linia na próbę:
`id`, `passed`, opcjonalnie `layer`, `cost_usd`, `trial`), z kilku przebiegów bazy liczy rozrzut i próg, a przebieg
kandydata ocenia: wypuść / zbadaj / wstrzymaj. Wartości oczekiwane w testach są policzone ręcznie.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "ai-evals" / "scripts" / "eval_gate.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, timeout=60,
                          encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)


def write_run(path: Path, passed: int, total: int = 20, **extra) -> Path:
    """Przebieg: `total` zadań po jednej próbie, pierwsze `passed` zaliczone (t01…)."""
    lines = [json.dumps({"id": f"t{i:02d}", "passed": i <= passed, **extra}) for i in range(1, total + 1)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_lines(path: Path, rows: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return path


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    r = run("--help")
    check(r.returncode == 0 and "baseline" in r.stdout and "check" in r.stdout and "kod" in r.stdout.lower(),
          f"EG-1: --help opisuje polecenia i kody wyjścia: {r.returncode} {r.stdout[:200]} {r.stderr[-200:]}")

    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        # Baza: trzy przebiegi po 20 zadań, zaliczone 14, 15, 16 → 0,70 / 0,75 / 0,80; margines 0,04 → próg 0,66.
        runs = [write_run(d / f"base{i}.jsonl", n) for i, n in enumerate((14, 15, 16), 1)]
        base = d / "baseline.json"
        r = run("baseline", *runs, "--margin", "0.04", "--out", base)
        data = json.loads(base.read_text(encoding="utf-8")) if base.is_file() else {}
        s = data.get("success", {})
        check(r.returncode == 0 and data.get("runs") == 3 and abs(s.get("min", 0) - 0.70) < 1e-9
              and abs(s.get("max", 0) - 0.80) < 1e-9 and abs(s.get("mean", 0) - 0.75) < 1e-9,
              f"EG-2: baza z trzech przebiegów: min 0,70, max 0,80, średnia 0,75: rc={r.returncode} {data} {r.stderr[-200:]}")
        check(abs(data.get("threshold", 0) - 0.66) < 1e-9 and abs(data.get("margin", 0) - 0.04) < 1e-9,
              f"EG-2b: próg = dolna granica rozrzutu − margines = 0,66: {data.get('threshold')}")
        check(data.get("stable_tasks") == [f"t{i:02d}" for i in range(1, 15)],
              f"EG-2c: zadania stabilne = zaliczone w każdym przebiegu bazy (t01–t14): {data.get('stable_tasks')}")

        # Kandydat w rozrzucie bazy → wypuść
        r = run("check", write_run(d / "ok.jsonl", 15), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("verdict") == "wypuść" and abs(out.get("success", 0) - 0.75) < 1e-9,
              f"EG-3: 0,75 przy bazie 0,70–0,80 → wypuść, kod 0: rc={r.returncode} {r.stdout[:300]} {r.stderr[-200:]}")

        # Poniżej dolnej granicy rozrzutu, ale w marginesie → zbadaj (kod 0; ze --strict kod 1)
        # 13 z 20 zaliczonych = 0,65 < 0,66 byłoby już wstrzymaj, więc bierzemy bazę 0,70 i wynik 0,68 na 50 zadaniach.
        r = run("check", write_run(d / "edge.jsonl", 34, 50), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("verdict") == "zbadaj" and abs(out.get("success", 0) - 0.68) < 1e-9,
              f"EG-4: 0,68 (poniżej min 0,70, powyżej progu 0,66) → zbadaj, kod 0: rc={r.returncode} {r.stdout[:300]}")
        r = run("check", d / "edge.jsonl", "--baseline", base, "--strict")
        check(r.returncode == 1, f"EG-4b: --strict zamienia zbadaj na kod 1: rc={r.returncode}")

        # Poniżej progu → wstrzymaj
        r = run("check", write_run(d / "bad.jsonl", 12), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("verdict") == "wstrzymaj" and any("progu" in x for x in out.get("reasons", [])),
              f"EG-5: 0,60 poniżej progu 0,66 → wstrzymaj, kod 1, powód z progiem: rc={r.returncode} {r.stdout[:300]}")
        check(out.get("regressions") == ["t13", "t14"],
              f"EG-5b: regresje = zadania stabilne w bazie, które teraz padły: {out.get('regressions')}")

        # Zadanie z warstwy regresyjnej nie może paść, nawet gdy wynik ogólny jest w normie
        rows = [{"id": f"t{i:02d}", "passed": i <= 16} for i in range(1, 21)]
        rows[17] = {"id": "t18", "passed": False, "layer": "regression"}
        r = run("check", write_lines(d / "reg.jsonl", rows), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("verdict") == "wstrzymaj" and out.get("regression_layer_failures") == ["t18"],
              f"EG-6: porażka zadania z warstwy regresyjnej → wstrzymaj mimo 0,80: rc={r.returncode} {r.stdout[:300]}")

        # Budżet
        r = run("check", write_run(d / "cost.jsonl", 15, cost_usd=0.16), "--baseline", base, "--budget-usd", "3", "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and out.get("verdict") == "wstrzymaj" and abs(out.get("cost_usd", 0) - 3.2) < 1e-9
              and any("budżet" in x for x in out.get("reasons", [])),
              f"EG-7: koszt 3,20 USD przy budżecie 3 → wstrzymaj: rc={r.returncode} {r.stdout[:300]}")
        r = run("check", d / "cost.jsonl", "--baseline", base, "--budget-usd", "4", "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("verdict") == "wypuść", f"EG-7b: koszt w budżecie → wypuść: {r.stdout[:200]}")
        r = run("check", d / "ok.jsonl", "--baseline", base, "--budget-usd", "4", "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and out.get("verdict") == "zbadaj" and out.get("cost_usd") is None
              and any("koszt" in x for x in out.get("reasons", [])),
              f"EG-7c: budżet podany, a wyniki bez kosztu → zbadaj (nie „w budżecie”): rc={r.returncode} {r.stdout[:300]}")

        # pass^k i pass@k: 4 zadania × 3 próby: a 3/3, b 2/3, c 0/3, d 1/3 → sukces 6/12 = 0,5; pass^3 = 1/4; pass@3 = 3/4
        trials = {"a": [1, 1, 1], "b": [1, 0, 1], "c": [0, 0, 0], "d": [0, 1, 0]}
        rows = [{"id": k, "passed": bool(v), "trial": i + 1} for k, vs in trials.items() for i, v in enumerate(vs)]
        one = d / "k-base.json"
        run("baseline", write_lines(d / "k.jsonl", rows), "--out", one)
        r = run("check", d / "k.jsonl", "--baseline", one, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(out.get("k") == 3 and out.get("tasks") == 4 and out.get("attempts") == 12
              and abs(out.get("success", 0) - 0.5) < 1e-9 and abs(out.get("pass_all_k", 0) - 0.25) < 1e-9
              and abs(out.get("pass_any_k", 0) - 0.75) < 1e-9,
              f"EG-8: sukces 0,5, pass^3 0,25, pass@3 0,75: {r.stdout[:300]} {r.stderr[-200:]}")

        # Baza z jednego przebiegu działa, ale ostrzega o rozrzucie
        r = run("baseline", runs[0], "--out", d / "single.json")
        check(r.returncode == 0 and (d / "single.json").is_file() and "3" in r.stdout and "rozrzut" in r.stdout.lower(),
              f"EG-9: baza z jednego przebiegu → ostrzeżenie o rozrzucie (3–5 powtórzeń): rc={r.returncode} {r.stdout[:300]}")

        # Inny zestaw zadań niż w bazie → porównanie niepewne
        r = run("check", write_run(d / "other.jsonl", 20, 25), "--baseline", base, "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(out.get("verdict") == "zbadaj" and any("zestaw" in x for x in out.get("reasons", [])),
              f"EG-10: zestaw zadań inny niż w bazie → zbadaj z powodem: {r.stdout[:300]}")

        # Złe dane → kod 2, bez werdyktu (pusty plik to nie „0 porażek”)
        (d / "empty.jsonl").write_text("", encoding="utf-8")
        (d / "broken.jsonl").write_text('{"id": "t01", "passed": true}\nto nie jest json\n', encoding="utf-8")
        (d / "nofield.jsonl").write_text('{"id": "t01"}\n', encoding="utf-8")
        for name, what in (("empty.jsonl", "pusty plik"), ("broken.jsonl", "linia spoza JSON"), ("nofield.jsonl", "brak pola passed"),
                           ("nie-ma.jsonl", "brak pliku")):
            r = run("check", d / name, "--baseline", base, "--json")
            check(r.returncode == 2 and "verdict" not in r.stdout,
                  f"EG-11: {what} → kod 2 bez werdyktu: rc={r.returncode} {r.stdout[:120]} {r.stderr[:160]}")
        r = run("check", d / "ok.jsonl", "--baseline", d / "brak-bazy.json")
        check(r.returncode == 2, f"EG-11b: brak pliku bazy → kod 2: rc={r.returncode}")

        # Raport tekstowy i plik raportu
        report = d / "raport.md"
        r = run("check", d / "bad.jsonl", "--baseline", base, "--report", report)
        text = report.read_text(encoding="utf-8") if report.is_file() else ""
        check("Werdykt: wstrzymaj" in r.stdout and "60" in r.stdout and "70" in r.stdout and "80" in r.stdout,
              f"EG-12: tekst: werdykt, wynik i rozrzut bazy w procentach: {r.stdout[:400]}")
        check("wstrzymaj" in text and "t13" in text and "t14" in text,
              f"EG-12b: --report zapisuje raport z werdyktem i regresjami: {text[:300]}")

    print(f"test_eval_gate: {total - len(fails)}/{total} OK")
    for f in fails:
        print(f"  ✗ {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
