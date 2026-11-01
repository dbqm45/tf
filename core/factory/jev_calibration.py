#!/usr/bin/env python3
"""
Pomiar Jev na danych fabryki — ZANIM go włączysz (wymaga TYPESAFE_API_KEY; koszt rzędu centów).

  python3 factory/jev_calibration.py --routing [--limit 300] [--shuffle] [--target 0.9]
  python3 factory/jev_calibration.py --judge docs/evals/2026-10-02-sonnet.jsonl [--limit 100]

--routing  podpowiedź skilli na wszystkich scenariuszach ewaluacji: same słowa (hook domyślny) kontra dwuetapowy Jev
           (cookbook TypeSafe „skill suggestion”). Miary jak w cookbooku: trafne, błędne (podpowiedziany inny skill),
           zbędne (podpowiedź przy pytaniu, które nie potrzebuje tego skilla), przeoczone. Pytania „no-trigger”
           oczekują sąsiada (pole neighbor) albo braku podpowiedzi.
--judge    odtwarza zapisane odpowiedzi z ewaluacji i porównuje ocenę Jev (każde wymaganie osobno, pas niepewności
           0,30–0,70) z oceną, którą przebieg już ma. Pokazuje zgodność pewnych ocen i odsetek niepewnych (te w kaskadzie
           ocenia haiku).
Progi dopasowane osobno dla każdego punktu decyzji (nigdy domyślne 0,5): trasowanie — najniższy próg „pasuje” z precyzją
≥ --target; sędzia — najwęższy pas niepewności ze zgodnością pewnych ocen ≥95% (etykiety: przebiegi, w których spełniono
wszystkie albo żadne wymaganie). --shuffle: test kolejności opcji (odwrócona lista skilli).
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


def fit_band(points: list[tuple[float, bool]], target: float = 0.95, step: float = 0.05) -> dict:
    """Pas niepewności dopasowany na własnych etykietach (zamiast stałego 0,30–0,70): najwęższy pas [low, high], przy
    którym oceny poza pasem zgadzają się z etykietą w co najmniej `target` przypadków. Bez danych albo bez pasa
    spełniającego cel → pas domyślny klienta (jev_client.LOW/HIGH)."""
    sys.path.insert(0, str(HOOKS))
    import jev_client as jev
    best = {"low": jev.LOW, "high": jev.HIGH, "agreement": None, "unsure": None, "n": len(points), "fitted": False}
    if not points:
        return best
    grid = [round(i * step, 4) for i in range(int(round(1 / step)) + 1)]
    for low in [g for g in grid if g <= 0.5]:
        for high in [g for g in grid if g >= 0.5]:
            sure = [(p > high, y) for p, y in points if p > high or p < low]
            if not sure:
                continue
            agree = sum(v == y for v, y in sure) / len(sure)
            unsure = len(points) - len(sure)
            if agree >= target and (best["unsure"] is None or unsure < best["unsure"]
                                    or (unsure == best["unsure"] and high - low < best["high"] - best["low"])):
                best = {"low": low, "high": high, "agreement": agree, "unsure": unsure, "n": len(points), "fitted": True}
    return best


def fit_threshold(points: list[tuple[float, bool]], target: float = 0.9, step: float = 0.05) -> dict:
    """Próg jednostronny (trasowanie: podpowiadaj, gdy p ≥ próg): najniższy próg, przy którym trafne podpowiedzi
    stanowią co najmniej `target` podpowiedzianych. Pokrycie = odsetek pytań, przy których coś podpowiadamy."""
    out = {"threshold": None, "precision": None, "coverage": 0.0, "n": len(points)}
    cands = sorted({round(p, 4) for p, _ in points} | {round(i * step, 4) for i in range(int(round(1 / step)) + 1)})
    for th in cands:
        sel = [(p, y) for p, y in points if p >= th]
        hit = [y for _, y in sel]
        if hit and sum(hit) / len(hit) >= target:
            return {"threshold": min(p for p, _ in sel), "precision": sum(hit) / len(hit),
                    "coverage": len(hit) / len(points), "n": len(points)}
    return out


def order_sensitivity(pick, prompts: list[str], options: list) -> dict:
    """Test kolejności opcji: ten sam wybór po odwróceniu listy opcji? `pick(prompt, options)` zwraca wybraną opcję
    (albo listę). Zmiana wyboru = model ocenia pozycję, a nie treść."""
    changed = 0
    for pr in prompts:
        a, b = pick(pr, list(options)), pick(pr, list(reversed(options)))
        changed += a != b
    return {"checked": len(prompts), "changed": changed}


def outcome(picked: list[str], expected: set[str]) -> str:
    if picked and set(picked) & expected:
        return "trafne"
    if picked:
        return "zbędne" if not expected else "błędne"
    return "trafne" if not expected else "przeoczone"


def calibrate_routing(limit: int, shuffle: bool = False, target: float = 0.9) -> int:
    hint = load(HOOKS / "skill_hint.py", "skill_hint")
    items = hint.load_index()
    cases = scenarios()[:limit]
    routed, order = [], {"checked": 0, "changed": 0}
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
        if j:   # wynik zwycięzcy = p(„pasuje”) × 20; podpowiedzi poniżej bieżącego progu hook odrzuca, więc ich nie widać
            routed.append((j[0][0] / 20, j[0][1]["name"] in expected))
        if shuffle:
            jr = hint.jev_suggest(s["prompt"], list(reversed(items)))
            if jr is not None:
                order["checked"] += 1
                order["changed"] += [it["name"] for _, it in jr] != jev_pick
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
    th = fit_threshold(routed, target)
    if th["threshold"] is not None:
        print(f"Próg „pasuje” dla trasowania dopasowany na etykietach: {th['threshold']:.2f} (precyzja {th['precision']:.0%}"
              f" przy celu {target:.0%}, podpowiedź przy {th['coverage']:.0%} pytań; bieżący JEV_FITS {hint.JEV_FITS:.2f})")
    else:
        print(f"Żaden próg nie daje precyzji {target:.0%} — zostaw słowa (hook domyślny)")
    if shuffle:
        print(f"Test kolejności opcji: wybór zmienił się w {order['changed']}/{order['checked']} pytań po odwróceniu "
              "listy skilli (każda zmiana = ocena pozycji, nie treści)")
    print(f"Koszt Jev ≈ ${spent:.4f}, czas {time.time() - t0:.0f} s")
    return 0


def calibrate_judge(jsonl: Path, limit: int, jev, ev) -> int:
    scen = {(s["skill"], s["id"]): s for s in scenarios()}
    rows = [json.loads(l) for l in jsonl.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("expect") == "trigger" and r.get("answer") and (r["skill"], r["id"]) in scen][:limit]
    agree = sure = unsure = 0
    cost = 0.0
    points = []
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
        ps = [jev.p_yes(a[f"w{i}"]) for i in range(len(reqs))]
        if r.get("checks_ok") or not (r.get("groups_met") or 0):   # etykieta pewna: wszystko spełnione albo nic
            points += [(p, bool(r.get("checks_ok"))) for p in ps]
        verdicts = [jev.noul_verdict(p) for p in ps]
        if any(v is None for v in verdicts):
            unsure += 1
            continue
        sure += 1
        agree += all(v or rx for v, rx in zip(verdicts, regex)) == bool(r.get("checks_ok"))
    n = len(rows)
    print(f"Ocena treści: {n} odpowiedzi; pewne {sure} ({100 * sure / max(n, 1):.0f}%), zgodne z oceną przebiegu "
          f"{agree}/{sure} ({100 * agree / max(sure, 1):.0f}%); niepewne → haiku: {unsure}. Koszt Jev: ${cost:.4f}")
    band = fit_band(points)
    if band["fitted"]:
        print(f"Pas niepewności sędziego dopasowany na etykietach ({band['n']} wymagań): {band['low']:.2f}–{band['high']:.2f}"
              f" (zgodność {band['agreement']:.0%}, niepewne {band['unsure']}); domyślny {jev.LOW:.2f}–{jev.HIGH:.2f}")
    else:
        print(f"Za mało danych albo żaden pas nie daje zgodności 95% — zostaje {jev.LOW:.2f}–{jev.HIGH:.2f}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judge", type=Path)
    ap.add_argument("--routing", action="store_true")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--shuffle", action="store_true", help="test kolejności: każde pytanie trasowania drugi raz z odwróconą listą skilli (2× koszt)")
    ap.add_argument("--target", type=float, default=0.9, help="docelowa precyzja podpowiedzi przy dopasowaniu progu trasowania")
    args = ap.parse_args(argv[1:])
    sys.path.insert(0, str(HOOKS))
    import jev_client as jev
    if not jev.enabled():
        print("Ustaw TYPESAFE_API_KEY (zmienna środowiskowa, nie plik w repozytorium).")
        return 2
    rc = 0
    if args.routing:
        rc |= calibrate_routing(args.limit, args.shuffle, args.target)
    if args.judge:
        rc |= calibrate_judge(args.judge, args.limit, jev, load(TESTS / "run_skill_evals.py", "run_skill_evals"))
    if not (args.judge or args.routing):
        print(__doc__)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
