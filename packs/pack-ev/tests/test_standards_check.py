#!/usr/bin/env python3
"""Testy rejestru standardów i przepisów (skill dom-ev-knowledge-base, `standards_check.py`): walidacja wpisów, termin
ponownego sprawdzenia, daty nadchodzące i daty, które minęły od ostatniego sprawdzenia, zastąpienia, odwołania do
źródeł z bazy wiedzy i do skilli, kody wyjścia. Na końcu sprawdza prawdziwy rejestr fabryki."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
KB = ROOT / ".claude" / "skills" / "dom-ev-knowledge-base"
SCRIPT = KB / "scripts" / "standards_check.py"
REGISTRY = KB / "references" / "rejestr-standardow.json"

ENTRY = {"id": "eu-afir", "nazwa": "AFIR — rozporządzenie (UE) 2023/1804", "rodzaj": "regulacja", "rynek": "EU",
         "wersja": "2023/1804", "status": "obowiązuje", "zrodlo": "kb:eu-afir", "sprawdzono": "2026-10-20",
         "skille": ["dom-ev-regulations-eu"],
         "daty": [{"co": "stosowanie", "data": "2024-04-13"}, {"co": "terminal na TEN-T ≥ 50 kW", "data": "2027-01-01"}]}


def reg(*entries, months=6):
    return {"przeglad_miesiecy": months, "wpisy": list(entries)}


def load():
    spec = importlib.util.spec_from_file_location("standards_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not SCRIPT.exists():
        print(f"✗ brak {SCRIPT.relative_to(ROOT)}")
        return 1
    m = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    def codes(r, key="errors"):
        return [x["code"] for x in r[key]]

    r = m.check(reg(ENTRY), today="2026-10-20", root=ROOT)
    check(r["errors"] == [] and r["stale"] == [] and r["recent"] == [], f"S-1: poprawny wpis bez uwag: {r}")
    r30 = m.check(reg(ENTRY), today="2026-10-20", root=ROOT, horizon_days=30)
    check(r30["upcoming"] == [], "S-2: termin 2027-01-01 jest dalej niż horyzont 30 dni")
    r = m.check(reg(ENTRY), today="2026-10-20", root=ROOT, horizon_days=90 + 365)
    check([(u["id"], u["data"]) for u in r["upcoming"]] == [("eu-afir", "2027-01-01")],
          f"S-3: nadchodząca data w horyzoncie: {r['upcoming']}")

    r = m.check(reg(ENTRY), today="2027-05-01", root=ROOT)
    check([s["id"] for s in r["stale"]] == ["eu-afir"], f"S-4: sprawdzono > 6 mies. temu → do ponownego sprawdzenia: {r['stale']}")
    check([(x["id"], x["data"]) for x in r["recent"]] == [("eu-afir", "2027-01-01")],
          f"S-5: data, która minęła od ostatniego sprawdzenia → przejrzyj skille: {r['recent']}")
    r = m.check(reg(ENTRY, months=12), today="2027-05-01", root=ROOT)
    check(r["stale"] == [], "S-6: przeglad_miesiecy z rejestru zmienia termin")

    bad = copy.deepcopy(ENTRY)
    bad.pop("sprawdzono")
    check("missing" in codes(m.check(reg(bad), today="2026-10-20", root=ROOT)), "V-1: brak pola obowiązkowego")
    for key, val in (("rodzaj", "ustawa?"), ("status", "chyba"), ("rynek", "Mars"), ("sprawdzono", "20.10.2026")):
        bad = copy.deepcopy(ENTRY)
        bad[key] = val
        check("value" in codes(m.check(reg(bad), today="2026-10-20", root=ROOT)), f"V-2: zła wartość {key}={val!r}")
    bad = copy.deepcopy(ENTRY)
    bad["daty"] = [{"co": "stosowanie", "data": "2024-13-40"}]
    check("value" in codes(m.check(reg(bad), today="2026-10-20", root=ROOT)), "V-3: zła data w daty[]")
    check("duplicate" in codes(m.check(reg(ENTRY, ENTRY), today="2026-10-20", root=ROOT)), "V-4: powtórzone id")
    bad = copy.deepcopy(ENTRY)
    bad["zrodlo"] = "kb:nie-ma-takiego"
    check("source" in codes(m.check(reg(bad), today="2026-10-20", root=ROOT)), "V-5: kb:<id> spoza zrodla.json")
    ok = copy.deepcopy(ENTRY)
    ok["zrodlo"] = "https://eur-lex.europa.eu/eli/reg/2023/1804/oj"
    check(m.check(reg(ok), today="2026-10-20", root=ROOT)["errors"] == [], "V-6: źródło jako URL https")
    bad = copy.deepcopy(ENTRY)
    bad["skille"] = ["dom-ev-nie-istnieje"]
    check("skill" in codes(m.check(reg(bad), today="2026-10-20", root=ROOT)), "V-7: skill spoza .claude/skills")
    old = {**ENTRY, "id": "eu-red-da", "nazwa": "RED DA 2022/30", "status": "uchylony", "daty": []}
    check("replaced-by" in codes(m.check(reg(old), today="2026-10-20", root=ROOT)),
          "V-8: status uchylony/zastąpiony wymaga pola zastapiony_przez")
    old["zastapiony_przez"] = "eu-afir"
    check(m.check(reg(ENTRY, old), today="2026-10-20", root=ROOT)["errors"] == [], "V-9: zastapiony_przez wskazuje istniejący wpis")
    old["zastapiony_przez"] = "brak"
    check("replaced-by" in codes(m.check(reg(ENTRY, old), today="2026-10-20", root=ROOT)), "V-10: zastapiony_przez do nieistniejącego wpisu")
    unk = copy.deepcopy(ENTRY)
    unk["daty"] = [{"co": "stosowanie", "data": None, "do_weryfikacji": True}]
    r = m.check(reg(unk), today="2026-10-20", root=ROOT)
    check(r["errors"] == [] and [u["id"] for u in r["unverified"]] == ["eu-afir"],
          f"V-11: data nieznana z do_weryfikacji → lista do weryfikacji, nie błąd: {r}")
    try:
        m.check({"wpisy": "nie lista"}, today="2026-10-20", root=ROOT)
        check(False, "V-12: wpisy nie-lista → InputError")
    except m.InputError:
        check(True, "")

    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "r.json"
        f.write_text(json.dumps(reg(ENTRY)), encoding="utf-8")
        run = lambda *a: subprocess.run([sys.executable, str(SCRIPT), "--registry", str(f), "--root", str(ROOT), *a],
                                        capture_output=True, text=True)
        p = run("--today", "2026-10-20")
        check(p.returncode == 0, f"CLI-1: kod 0 bez uwag: {p.returncode} {p.stdout[-300:]} {p.stderr[-200:]}")
        p = run("--today", "2027-05-01")
        check(p.returncode == 0 and "eu-afir" in p.stdout, f"CLI-2: bez --strict uwagi nie zmieniają kodu: {p.returncode}")
        p = run("--today", "2027-05-01", "--strict")
        check(p.returncode == 1, f"CLI-3: --strict i wpis po terminie → kod 1: {p.returncode}")
        p = run("--today", "2026-10-20", "--json")
        try:
            check(json.loads(p.stdout)["entries"] == 1, "CLI-4: --json")
        except (ValueError, KeyError) as e:
            check(False, f"CLI-4: --json zwraca JSON: {e}")
        f.write_text(json.dumps(reg({"id": "x"})), encoding="utf-8")
        check(run("--today", "2026-10-20").returncode == 2, "CLI-5: błędy rejestru → kod 2")

    if REGISTRY.exists():
        r = m.check(json.loads(REGISTRY.read_text(encoding="utf-8")), today="2026-10-20", root=ROOT)
        check(r["errors"] == [] and r["entries"] >= 20, f"R-1: rejestr fabryki poprawny i ≥ 20 wpisów: {r['errors'][:5]} {r['entries']}")
    else:
        check(False, f"R-1: brak {REGISTRY.relative_to(ROOT)}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów standards_check nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów standards_check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
