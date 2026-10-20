#!/usr/bin/env python3
"""
Pomiar Jev na danych fabryki — ZANIM go włączysz (wymaga TYPESAFE_API_KEY; koszt rzędu centów).

  python3 factory/jev_calibration.py --routing [--limit 300]
  python3 factory/jev_calibration.py --judge docs/evals/2026-10-02-sonnet.jsonl [--limit 100]

--routing  podpowiedź skilli na wszystkich scenariuszach ewaluacji: same słowa (hook domyślny) kontra dwuetapowy Jev
           (cookbook TypeSafe „skill suggestion”). Miary jak w cookbooku: trafne, błędne (podpowiedziany inny skill),
           zbędne (podpowiedź przy pytaniu, które nie potrzebuje tego skilla), przeoczone. Pytania „no-trigger”
           oczekują sąsiada (pole neighbor) albo braku podpowiedzi.
--judge    odtwarza zapisane odpowiedzi z ewaluacji i porównuje ocenę Jev (każde wymaganie osobno, pas niepewności
           0,30–0,70) z oceną, którą przebieg już ma. Pokazuje zgodność pewnych ocen i odsetek niepewnych (te w kaskadzie
           ocenia haiku).
Rekomendacja: CLAUDE_SKILL_HINT_JEV=1 włącz, gdy Jev ma mniej błędnych i zbędnych podpowiedzi niż słowa przy podobnej
liczbie trafnych; `--judge jev`, gdy zgodność pewnych ocen ≥95%. Dokumentacja TypeSafe: angielski działa najlepiej,
inne języki słabiej — dlatego pomiar na polskich pytaniach jest konieczny.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"
TESTS = ROOT / "tests" if (ROOT / "tests" / "run_skill_evals.py").exists() else ROOT / ".claude" / "tests"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scenarios() -> list[dict]:
    out = []
    for f in sorted((TESTS / "skill_evals").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for s in d["scenarios"]:
            out.append({**s, "skill": d["skill"]})
    return out


def outcome(picked: list[str], expected: set[str]) -> str:
    if picked and set(picked) & expected:
        return "trafne"
    if picked:
        return "zbędne" if not expected else "błędne"
    return "trafne" if not expected else "przeoczone"


def calibrate_routing(limit: int) -> int:
    hint = load(HOOKS / "skill_hint.py", "skill_hint")
    items = hint.load_index()
    cases = scenarios()[:limit]
    stats = {"słowa": {}, "jev": {}}
    t0, spent = time.time(), 0.0
    for s in cases:
        if s["expect"] == "trigger":
            expected = {s["skill"], *(s.get("accept") or [])}
        else:
            expected = {s.get("neighbor"), *(s.get("accept") or [])} - {None, "brak"}
        words = [it["name"] for _, it in hint.select(s["prompt"], items)][:1]
        j = hint.jev_suggest(s["prompt"], items)
        if j is None:
            print("✗ Jev nie odpowiada — sprawdź TYPESAFE_API_KEY i sieć (python3 .claude/hooks/jev_client.py --check)")
            return 1
        jev_pick = [it["name"] for _, it in j]
        for k, picked in (("słowa", words), ("jev", jev_pick)):
            o = outcome(picked, expected)
            stats[k][o] = stats[k].get(o, 0) + 1
    log = ROOT / ".claude" / "logs" / "jev.jsonl"
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("ts", "") >= time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t0)):
                spent += r.get("cost") or 0
    n = len(cases)
    print(f"Podpowiedź skilli na {n} scenariuszach (1. wybór):")
    for k in ("słowa", "jev"):
        st = stats[k]
        print(f"  {k:<6} " + ", ".join(f"{o} {st.get(o, 0)} ({100 * st.get(o, 0) / max(n, 1):.0f}%)"
                                       for o in ("trafne", "błędne", "zbędne", "przeoczone")))
    print(f"Koszt Jev ≈ ${spent:.4f}, czas {time.time() - t0:.0f} s")
    return 0


def calibrate_judge(jsonl: Path, limit: int, jev, ev) -> int:
    scen = {(s["skill"], s["id"]): s for s in scenarios()}
    rows = [json.loads(l) for l in jsonl.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("expect") == "trigger" and r.get("answer") and (r["skill"], r["id"]) in scen][:limit]
    agree = sure = unsure = 0
    cost = 0.0
    for r in rows:
        s = scen[(r["skill"], r["id"])]
        groups = (s.get("checks") or {}).get("all") or []
        if not groups:
            continue
        reqs = s.get("rubric") if s.get("rubric") and len(s["rubric"]) == len(groups) else [ev.requirement(g) for g in groups]
        regex = [any(re.search(rx, r["answer"], re.I | re.S) for rx in g) for g in groups]
        qs = {f"w{i}": {"type": "noul", "instructions": "Does `answer` state the following, literally, in other words "
                        f"or with a synonym (the answer may be in Polish): {q}"} for i, q in enumerate(reqs)}
        a = jev.decide({"answer": r["answer"][:40000]}, qs, timeout=15)
        if not a:
            print(f"✗ brak odpowiedzi Jev dla {r['skill']}#{r['id']} — przerywam")
            return 1
        cost += a["_usage"]["cost"]
        verdicts = [jev.noul_verdict(jev.p_yes(a[f"w{i}"])) for i in range(len(reqs))]
        if any(v is None for v in verdicts):
            unsure += 1
            continue
        sure += 1
        agree += all(v or rx for v, rx in zip(verdicts, regex)) == bool(r.get("checks_ok"))
    n = len(rows)
    print(f"Ocena treści: {n} odpowiedzi; pewne {sure} ({100 * sure / max(n, 1):.0f}%), zgodne z oceną przebiegu "
          f"{agree}/{sure} ({100 * agree / max(sure, 1):.0f}%); niepewne → haiku: {unsure}. Koszt Jev: ${cost:.4f}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judge", type=Path)
    ap.add_argument("--routing", action="store_true")
    ap.add_argument("--limit", type=int, default=300)
    args = ap.parse_args(argv[1:])
    sys.path.insert(0, str(HOOKS))
    import jev_client as jev
    if not jev.enabled():
        print("Ustaw TYPESAFE_API_KEY (zmienna środowiskowa, nie plik w repozytorium).")
        return 2
    rc = 0
    if args.routing:
        rc |= calibrate_routing(args.limit)
    if args.judge:
        rc |= calibrate_judge(args.judge, args.limit, jev, load(TESTS / "run_skill_evals.py", "run_skill_evals"))
    if not (args.judge or args.routing):
        print(__doc__)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
