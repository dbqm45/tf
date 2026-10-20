#!/usr/bin/env python3
"""Testy egzaminu branżowego EV (tests/ev_exam/, runner tests/run_ev_exam.py) — bez modelu, z atrapą claude:
walidacja pytań (pola, wyrażenia, odpowiedź wzorcowa spełnia własne sprawdzenia, źródło istnieje), wynik z fabryką
i bez niej, różnica, raport, kody wyjścia. Prawdziwy egzamin: ≥ 100 poprawnych pytań."""
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_ev_exam.py"

FAKE = """#!/usr/bin/env python3
import json, os, sys
factory = os.path.isdir(os.path.join(os.getcwd(), ".claude", "skills"))
text = "Jeden EVSE: dwa złącza na wspólnym torze zasilania ładują jedno auto naraz." if factory else "Dwa punkty ładowania."
print(json.dumps({"type": "system", "subtype": "init"}))
print(json.dumps({"type": "result", "subtype": "success", "result": text, "total_cost_usd": 0.01, "num_turns": 1}))
"""

Q = {"id": "evse-dwa-zlacza", "pytanie": "Ile EVSE ma słupek z dwoma złączami na wspólnym torze zasilania?",
     "wzorzec": "Jeden EVSE — w danej chwili ładuje jedno auto, złącza to dwa Connectory tego EVSE.",
     "checks": {"all": [["jed(en|nym) evse|1 evse"]], "none": ["dwa evse"]}, "zrodlo": "dom-ev-glossary", "trudnosc": 1}


def load():
    spec = importlib.util.spec_from_file_location("run_ev_exam", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not RUNNER.exists():
        print(f"✗ brak {RUNNER.name}")
        return 1
    m = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)

        def write(name, data):
            p = d / f"{name}.json"
            p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return p

        good = write("pojecia", {"obszar": "pojecia", "pytania": [Q]})
        check(m.validate_file(good) == [], f"V-1: poprawny plik: {m.validate_file(good)}")
        bad_cases = {
            "V-2 obszar ≠ nazwa pliku": {"obszar": "inny", "pytania": [Q]},
            "V-3 brak pytań": {"obszar": "{n}", "pytania": []},
            "V-4 wzorzec nie spełnia checks.all": {"obszar": "{n}", "pytania": [{**Q, "wzorzec": "Dwa punkty."}]},
            "V-5 wzorzec trafia w checks.none": {"obszar": "{n}", "pytania": [{**Q, "wzorzec": "Jeden EVSE, a nie dwa evse."}]},
            "V-6 zły regex": {"obszar": "{n}", "pytania": [{**Q, "checks": {"all": [["(niedomknięty"]]}}]},
            "V-7 źródło nie istnieje": {"obszar": "{n}", "pytania": [{**Q, "zrodlo": "dom-ev-nie-ma"}]},
            "V-8 brak checks.all": {"obszar": "{n}", "pytania": [{**Q, "checks": {}}]},
            "V-9 powtórzone id": {"obszar": "{n}", "pytania": [Q, Q]},
            "V-10 trudnosc poza 1–3": {"obszar": "{n}", "pytania": [{**Q, "trudnosc": 5}]},
            "V-11 za krótkie pytanie": {"obszar": "{n}", "pytania": [{**Q, "pytanie": "EVSE?"}]},
        }
        for i, (why, data) in enumerate(bad_cases.items()):
            name = f"zly{i}"
            data = json.loads(json.dumps(data).replace("{n}", name))
            check(m.validate_file(write(name, data)) != [], f"{why} → błąd walidacji")
        kb = write("zrodla", {"obszar": "zrodla", "pytania": [{**Q, "zrodlo": "kb:eu-afir, dom-ev-glossary"}]})
        check(m.validate_file(kb) == [], f"V-12: źródło kb:<id> i kilka źródeł po przecinku: {m.validate_file(kb)}")

        exam = d / "exam"
        exam.mkdir()
        (exam / "pojecia.json").write_text(json.dumps({"obszar": "pojecia", "pytania": [Q]}, ensure_ascii=False), encoding="utf-8")
        fake = d / "claude"
        fake.write_text(FAKE, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        env = {**os.environ, "CLAUDE_BIN": str(fake)}
        out = d / "raport.md"
        p = subprocess.run([sys.executable, str(RUNNER), "--dir", str(exam), "--models", "haiku", "--judge", "none",
                            "--yes", "--out", str(out)], capture_output=True, text=True, env=env, timeout=120)
        check(p.returncode == 0, f"R-1: przebieg z atrapą kończy się kodem 0: {p.returncode} {p.stdout[-400:]} {p.stderr[-300:]}")
        rows = [json.loads(x) for x in out.with_suffix(".jsonl").read_text(encoding="utf-8").splitlines()] if out.with_suffix(".jsonl").exists() else []
        modes = {(r["mode"], r["passed"]) for r in rows}
        check(modes == {("fabryka", True), ("bez", False)}, f"R-2: z fabryką zalicza, bez fabryki nie: {modes}")
        rep = out.read_text(encoding="utf-8") if out.exists() else ""
        check("100" in rep and "+100" in rep.replace(" ", "") and "evse-dwa-zlacza" in rep,
              f"R-3: raport z wynikiem 100 % vs 0 %, różnicą +100 pkt i listą pytań: {rep[:600]}")
        p = subprocess.run([sys.executable, str(RUNNER), "--dir", str(exam), "--models", "haiku", "--no-baseline",
                            "--judge", "none", "--yes", "--out", str(d / "r2.md")], capture_output=True, text=True, env=env, timeout=120)
        rows = [json.loads(x) for x in (d / "r2.jsonl").read_text(encoding="utf-8").splitlines()] if (d / "r2.jsonl").exists() else []
        check(p.returncode == 0 and {r["mode"] for r in rows} == {"fabryka"}, f"R-4: --no-baseline bez przebiegu bez fabryki: {rows}")
        p = subprocess.run([sys.executable, str(RUNNER), "--dir", str(exam), "--ids", "nie-ma", "--yes"],
                           capture_output=True, text=True, env=env, timeout=60)
        check(p.returncode == 2, f"R-5: nieznane --ids → kod 2: {p.returncode}")
        p = subprocess.run([sys.executable, str(RUNNER), "--dir", str(exam), "--models", "haiku", "--judge", "none"],
                           input="n\n", capture_output=True, text=True, env=env, timeout=60)
        check(p.returncode == 0 and "Uruchomić" in p.stdout and not (exam / "evals").exists(),
              f"R-6: bez --yes pyta o zgodę (koszt) i kończy po odmowie: {p.stdout[-300:]}")

    p = subprocess.run([sys.executable, str(RUNNER), "--validate"], capture_output=True, text=True, timeout=60)
    n = m.count_questions()
    check(p.returncode == 0 and n >= 100, f"E-1: prawdziwy egzamin poprawny i ≥ 100 pytań: kod {p.returncode}, pytań {n}: {p.stdout[-600:]}")

    if fails:
        print(f"✗ {len(fails)}/{total} testów egzaminu EV nie przeszło:")
        for x in fails:
            print("  -", x)
        return 1
    print(f"✓ {total}/{total} testów egzaminu EV")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
