#!/usr/bin/env python3
"""Testy stanu przebiegu i dashboardu (skill tf, scripts/run_state.py).
python3 .claude/tests/test_run_state.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "run_state.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL
REPORT = SCRIPT.with_name("run_report.py")
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'8 passed\')"'
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi 45 zł.\n"
        "\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")
RED = f'{sys.executable} -c "print(\'FAILED test_x\'); raise SystemExit(3)"'


def run(script, args, cwd, cfg, extra_env=None):
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "TF_DASHBOARD_OPEN": "0", **(extra_env or {})}
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True, env=env,
                          timeout=60)


def runs_json(html: str) -> list:
    m = re.search(r"const RUNS = (\[.*?\]);\n", html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</")) if m else []


def main() -> int:
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        r = run(REPORT, ["start", "Sortowanie listy", "--story", "Jako admin chcę sortować."], proj, cfg)
        d = next((proj / ".tf" / "runs").glob("T-*-sortowanie-listy"), None)
        check(r.returncode == 0 and d is not None, f"S-0: przygotowanie przebiegu: {r.stdout} {r.stderr}")
        if d is None:
            print("✗ brak katalogu przebiegu")
            return 1
        doc = proj / CHANGES / d.name          # katalog trwały zadania (krok C4): plan, ticket i raport
        (doc / "spec.md").write_text(SPEC, encoding="utf-8")      # gotowa specyfikacja (krok D1) — bez niej nie ma planu
        run(SCRIPT, ["flag", str(d), "none", "--reason", "test stanu przebiegu, nie ma czego ukrywać"], proj, cfg)   # krok D4
        dash = proj / ".tf" / "runs" / "dashboard.html"

        def one():
            html = dash.read_text(encoding="utf-8")
            rs = runs_json(html)
            return rs[0] if rs else {}

        # S-1: etap z plan.md — szablon bez kawałków to jeszcze przyjęcie
        r = run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        check(r.returncode == 0 and dash.is_file() and r.stdout.strip().startswith("file://"),
              f"S-1a: dashboard buduje plik i drukuje adres: {r.stdout} {r.stderr}")
        o = one()
        check(o.get("stage") == "intake" and o.get("slices") == [] and o.get("title") == "Sortowanie listy",
              f"S-1b: bez planu etap intake: {o.get('stage')} {o.get('slices')}")

        # S-2: plan z kawałkami → etap plan, potem odhaczenie → slices
        (doc / "plan.md").write_text("# Plan\n- [ ] K1 — sortowanie rosnące · kryteria: t\n- [ ] K2 — malejące · kryteria: t\n"
                                   "- [ ] K3 — po dacie · kryteria: t\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        o = one()
        check(o.get("stage") == "plan" and [s["id"] for s in o["slices"]] == ["K1", "K2", "K3"],
              f"S-2a: plan z kawałkami → etap plan: {o.get('stage')}")
        (proj / "sort.py").write_text("ASC = True\n", encoding="utf-8")     # odhaczony kawałek ma dowód (krok C4)
        run(SCRIPT, ["verify", str(d), "K1", "--files", "sort.py", "--command", OK], proj, cfg)
        (doc / "plan.md").write_text("# Plan\n- [x] K1 — sortowanie rosnące · kryteria: t\n- [ ] K2 — malejące · kryteria: t\n"
                                   "- [ ] K3 — po dacie · kryteria: t\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        o = one()
        check(o.get("stage") == "slices" and [s["state"] for s in o["slices"]] == ["done", "cur", "todo"],
              f"S-2b: odhaczony K1 → slices, K2 bieżący: {o.get('stage')} {[s['state'] for s in o['slices']]}")

        # S-3: step zapisuje rundy; wcześniejsze etapy dostają pass, nowa runda po nieudanej bramce
        r = run(SCRIPT, ["step", str(d), "K2", "R1", "weryf", "fail"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and meta["current"]["rounds"][0] == {"test": "pass", "kod": "pass", "weryf": "fail",
                                                                  "skan": "todo", "zakres": "todo"},
              f"S-3a: R1 weryf fail, test i kod domyślnie pass: {r.stdout} {r.stderr} {meta.get('current')}")
        run(SCRIPT, ["step", str(d), "K2", "R2", "kod", "run"], proj, cfg)
        run(SCRIPT, ["step", str(d), "K2", "R2", "skan", "run"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        r2 = meta["current"]["rounds"][1]
        check(len(meta["current"]["rounds"]) == 2 and r2["test"] == "pass" and r2["kod"] == "pass"
              and r2["weryf"] == "pass" and r2["skan"] == "run" and r2["zakres"] == "todo",
              f"S-3b: R2 liczona od początku, weryf przed skanem = pass: {r2}")
        check(meta.get("stage") == "slices" and "updated_at" in meta, f"S-3c: step ustawia stage slices: {meta.get('stage')}")
        o = one()
        check(o.get("cur", {}).get("k") == "K2" and len(o["cur"]["rounds"]) == 2
              and o["cur"]["rounds"][0]["weryf"] == "fail",
              f"S-3d: dashboard po step (bez ręcznego odświeżenia): {o.get('cur')}")

        # S-4: nowy kawałek zaczyna od R1
        run(SCRIPT, ["step", str(d), "K3", "R1", "test", "run"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(meta["current"]["k"] == "K3" and len(meta["current"]["rounds"]) == 1,
              f"S-4: nowy kawałek zeruje rundy: {meta['current']}")

        # S-5: błędne wejście → kod 2 i komunikat, run.json bez zmian
        before = (d / "run.json").read_text(encoding="utf-8")
        bad = [["step", str(d), "K2", "R1", "weryf", "zielony"], ["step", str(d), "K2", "R1", "lint", "run"],
               ["step", str(d), "K2", "weryf", "run"], ["stage", str(d), "needs"], ["stage", str(d), "nie-ma"],
               ["stage", str(d), "slices", "--needs", "stop"]]
        codes = [run(SCRIPT, a, proj, cfg).returncode for a in bad]
        check(all(c == 2 for c in codes)
              and (d / "run.json").read_text(encoding="utf-8") == before,
              f"S-5: błędne wejście odrzucone bez zapisu: {codes}")

        # S-6: STOP — etap needs z powodem; kawałek bieżący = fail, plik STOP w panelu
        (d / "security" / "K2" / "proba-2").mkdir(parents=True)
        (d / "security" / "K2" / "proba-2" / "summary.md").write_text("## Bezpieczeństwo\nWerdykt: FAIL\n", encoding="utf-8")
        run(SCRIPT, ["step", str(d), "K2", "R2", "skan", "fail"], proj, cfg)
        r = run(SCRIPT, ["stage", str(d), "needs", "--needs", "stop", "--code", "skan", "--reason", "Skan czerwony po 2 próbach (K2)."],
                proj, cfg)
        o = one()
        names = [i["name"] for g in o.get("files", []) for i in g["items"]]
        check(r.returncode == 0 and o.get("stage") == "needs" and o.get("needs") == "stop"
              and "czerwony" in (o.get("stopText") or "") and "STOP" in names
              and "security/K2/proba-2/summary.md" in names,
              f"S-6a: STOP z powodem i plikami w panelu: {o.get('stage')} {o.get('needs')} {names}")
        check([s["state"] for s in o["slices"]][1] == "fail", f"S-6b: kawałek K2 w STOP = fail: {o['slices']}")
        # po decyzji człowieka kolejny step wznawia przebieg
        run(SCRIPT, ["step", str(d), "K2", "R3", "test", "run"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(meta.get("stage") == "slices" and "needs" not in meta and "stop_text" not in meta
              and len(meta["current"]["rounds"]) == 3,
              f"S-6c: step po STOP wraca do slices i kasuje powód: {meta.get('stage')}")

        # S-7: PR i koniec
        run(SCRIPT, ["step", str(d), "PR", "plan_drift", "pass"], proj, cfg)
        o = one()
        check(o.get("stage") == "pr" and o.get("prSteps") == {"drift": "pass", "pr": "todo"},
              f"S-7a: plan_drift → etap pr: {o.get('stage')} {o.get('prSteps')}")
        run(SCRIPT, ["stage", str(d), "done", "--pr", "41", "--auto", "--effort", "high"], proj, cfg)
        (doc / "report.md").write_text("# Raport\nok\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        o = one()
        check(o.get("stage") == "done" and o.get("pr") == 41 and o.get("auto") is True and o.get("effort") == "high"
              and any(i["name"] == "report.md" for g in o["files"] for i in g["items"]),
              f"S-7b: done z PR, auto, effort i raportem: {o.get('stage')} {o.get('pr')}")

        # S-8: koszt z transkryptów, zapamiętany w run.json (dashboard bez --no-cost); brak transkryptów nie psuje
        r = run(SCRIPT, ["dashboard"], proj, cfg)
        check(r.returncode == 0, f"S-8a: dashboard bez transkryptów działa: {r.stdout} {r.stderr}")
        started = json.loads((d / "run.json").read_text(encoding="utf-8"))["started_at"]
        slug = re.sub(r"[^A-Za-z0-9]", "-", str(proj.resolve()))
        sess = cfg / "projects" / slug / "S1.jsonl"
        sess.parent.mkdir(parents=True, exist_ok=True)
        ts = started.replace("+00:00", "Z")[:19] + "Z"
        year = int(ts[:4]) + 1                       # odpowiedź po starcie, niezależnie od zegara
        later = f"{year}{ts[4:]}"
        sess.write_text(json.dumps({"type": "assistant", "timestamp": later, "message": {
            "id": "m1", "model": "claude-sonnet-5-5", "usage": {"input_tokens": 1000, "output_tokens": 500}}}) + "\n",
                        encoding="utf-8")
        (d / "run.json").write_text(json.dumps({**json.loads((d / "run.json").read_text(encoding="utf-8")),
                                                "stage": "slices"}, ensure_ascii=False), encoding="utf-8")
        run(SCRIPT, ["dashboard"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        o = one()
        check(isinstance(meta.get("usage"), dict) and "sonnet" in meta["usage"]["models"]
              and o.get("models") == ["sonnet"] and o.get("cost") is not None,
              f"S-8b: koszt i modele z transkryptów zapisane w run.json: {meta.get('usage')}")
        run(SCRIPT, ["step", str(d), "K2", "R1", "test", "run"], proj, cfg)   # odświeżenie bez liczenia kosztu
        check(one().get("cost") == o.get("cost"), "S-8c: odświeżenie po step zachowuje zapamiętany koszt")

        # S-9: bezpieczeństwo HTML — treść plików z </script> nie wychodzi z bloku danych
        (doc / "ticket.md").write_text("# s\n</script><b>x</b>\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        html = dash.read_text(encoding="utf-8")
        check(html.count("</script>") == 1 and "</script><b>" not in html,
              f"S-9: </script> w treści pliku nie rozbija strony: {html.count('</script>')}")

    # S-10: start przebiegu buduje dashboard (domyślnie włączony), a opcje w .claude/tf.json i zmienne go wyłączają
    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        dash = proj / ".tf" / "runs" / "dashboard.html"
        r = run(REPORT, ["start", "Pierwsza historyjka", "--story", "x"], proj, cfg)
        check(r.returncode == 0 and dash.is_file() and "Dashboard: file://" in r.stderr
              and r.stdout.strip().startswith(".tf/runs/T-"),
              f"S-10a: start buduje dashboard, adres na stderr, stdout bez zmian: {r.stdout!r} {r.stderr!r}")
        dash.unlink()
        (proj / ".claude").mkdir()
        (proj / ".claude" / "tf.json").write_text('{"dashboard": false}', encoding="utf-8")
        r = run(REPORT, ["start", "Druga historyjka", "--story", "x"], proj, cfg)
        check(r.returncode == 0 and not dash.exists() and "Dashboard" not in r.stderr,
              f"S-10b: {{\"dashboard\": false}} — start niczego nie buduje: {r.stderr!r}")
        (proj / ".claude" / "tf.json").write_text('{"dashboard_open": false}', encoding="utf-8")
        r = run(REPORT, ["start", "Trzecia historyjka", "--story", "x"], proj, cfg)
        check(dash.is_file(), "S-10c: dashboard_open=false — buduje, ale nie otwiera (plik jest)")
        dash.unlink()
        (proj / ".claude" / "tf.json").unlink()
        r = run(REPORT, ["start", "Czwarta historyjka", "--story", "x"], proj, cfg, {"TF_DASHBOARD": "0"})
        check(r.returncode == 0 and not dash.exists(), "S-10d: TF_DASHBOARD=0 wyłącza bez pliku")
        # uszkodzony plik opcji → domyślne (włączone), przebieg się nie wywraca
        (proj / ".claude" / "tf.json").write_text("{nie json", encoding="utf-8")
        r = run(REPORT, ["start", "Piata historyjka", "--story", "x"], proj, cfg)
        check(r.returncode == 0 and dash.is_file(), f"S-10e: uszkodzony tf.json → opcje domyślne: {r.stderr!r}")

    # jedna czynność na polecenie: odhaczenie kawałka i odłożenie sprawy skryptem (bez sed, >> i heredoc w powłoce)
    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        run(REPORT, ["start", "Limit dobowy", "--story", "Jako operator chcę limit."], proj, cfg)
        d = next((proj / ".tf" / "runs").glob("T-*-limit-dobowy"), None)
        run(SCRIPT, ["stage", str(d), "intake", "--auto"], proj, cfg)     # przebieg bez nadzoru: plan bez zgody (krok E3)
        doc = proj / CHANGES / d.name
        plan = doc / "plan.md"
        head = plan.read_text(encoding="utf-8")
        plan.write_text(head + "- [ ] K1 — limit 45 zł · kryteria: AC1 · pliki: fees.py\n"
                               "- [ ] K2 — druga doba · kryteria: AC3 · pliki: fees.py\n", encoding="utf-8")
        (proj / "fees.py").write_text("LIMIT = 45\n", encoding="utf-8")

        def task():
            return json.loads((doc / "task.json").read_text(encoding="utf-8"))

        # specyfikacja przed planem (krok D1): szablon powstaje dopiero na polecenie `spec <katalog> new` (po wczesnym
        # STOP w repozytorium nie zostaje pusty plik); bez spec.md i z niewypełnionym nie ma etapu plan
        check(not (doc / "spec.md").exists(), "P-0a: start nie zakłada spec.md")
        r = run(SCRIPT, ["stage", str(d), "plan"], proj, cfg)
        check(r.returncode == 2 and "spec" in r.stdout and " new" in r.stdout and task().get("stage") == "przyjecie",
              f"P-0b: etap plan odrzucony, gdy specyfikacji jeszcze nie ma: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["spec", str(d), "new"], proj, cfg)
        check(r.returncode == 0 and (doc / "spec.md").is_file(), f"P-0c: spec new zakłada szablon: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["spec", str(d)], proj, cfg)
        check(r.returncode == 1 and "SPEC-007" in r.stdout, f"P-1a: spec na szablonie → kod 1 z regułą: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["stage", str(d), "plan"], proj, cfg)
        check(r.returncode == 2 and json.loads((d / "run.json").read_text(encoding="utf-8")).get("stage") != "plan"
              and task().get("stage") == "przyjecie" and "spec" in r.stdout,
              f"P-1b: etap plan odrzucony bez gotowej specyfikacji: {r.returncode} {r.stdout}")
        (doc / "spec.md").write_text(SPEC, encoding="utf-8")
        r = run(SCRIPT, ["spec", str(d)], proj, cfg)
        check(r.returncode == 0 and "AC-1" in r.stdout, f"P-2: gotowa specyfikacja → kod 0: {r.returncode} {r.stdout}{r.stderr}")

        # dowód przed odhaczeniem (krok C4): tick przechodzi tylko dla kawałka zweryfikowanego przez `verify`
        r = run(SCRIPT, ["tick", str(d), "K1"], proj, cfg)
        check(r.returncode != 0 and "verify" in r.stdout + r.stderr and plan.read_text(encoding="utf-8").count("[x]") == 0,
              f"V-1: tick bez dowodu odrzucony, plan bez zmian: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["verify", str(d), "K1", "--files", "fees.py", "--command", RED], proj, cfg)
        check(r.returncode == 1 and "FAILED test_x" in r.stdout, f"V-2: verify z czerwonym poleceniem → kod 1 i wyjście: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["verify", str(d), "K1", "--files", "fees.py", "--command", OK], proj, cfg)
        check(r.returncode == 0 and (doc / "evidence" / "K1-2.json").is_file(),
              f"V-3: verify zapisuje dowód w katalogu zadania: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["tick", str(d), "K1"], proj, cfg)
        text = plan.read_text(encoding="utf-8")
        check(r.returncode == 0 and "- [x] K1 — limit 45 zł" in text and "- [ ] K2 — druga doba" in text
              and text.startswith(head), f"T-1: tick odhacza tylko wskazany kawałek, reszta pliku bez zmian: {r.stdout}{r.stderr}{text[-200:]}")
        r = run(SCRIPT, ["tick", str(d), "K1"], proj, cfg)
        check(r.returncode == 0 and plan.read_text(encoding="utf-8") == text, f"T-2: ponowny tick niczego nie zmienia: {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["tick", str(d), "K7"], proj, cfg)
        check(r.returncode != 0 and "K7" in (r.stdout + r.stderr) and plan.read_text(encoding="utf-8") == text,
              f"T-3: nieznany kawałek → błąd z nazwą, plik bez zmian: {r.returncode} {r.stdout}{r.stderr}")
        parked = d / "parked.md"
        before = parked.read_text(encoding="utf-8")
        r = run(SCRIPT, ["park", str(d), "Strefy czasowe w znacznikach — do decyzji"], proj, cfg)
        run(SCRIPT, ["park", str(d), "Pliki > 50 MB"], proj, cfg)
        after = parked.read_text(encoding="utf-8")
        check(r.returncode == 0 and after.startswith(before.rstrip("\n")) and after.rstrip().endswith("- Pliki > 50 MB")
              and "- Strefy czasowe w znacznikach — do decyzji\n" in after,
              f"T-4: park dopisuje pozycje na końcu parked.md, każdą w osobnym wierszu: {after[-200:]}")
        r = run(SCRIPT, ["park", str(d), "  "], proj, cfg)
        check(r.returncode != 0 and parked.read_text(encoding="utf-8") == after, f"T-5: pusta sprawa → błąd, plik bez zmian: {r.returncode}")
        rep = run(REPORT, ["status", str(d)], proj, cfg)
        check("2" in rep.stdout or "odłożon" in rep.stdout.lower(), f"T-6: raport przebiegu widzi odłożone sprawy: {rep.stdout[-300:]}")

        # ślad kryteriów (krok D3): poza repozytorium git skrypt mówi wprost, że śladu nie policzy
        r = run(SCRIPT, ["trace", str(d)], proj, cfg)
        check(r.returncode == 2 and "git" in r.stdout, f"TRC-1: trace poza gitem → kod 2 z wyjaśnieniem: {r.returncode} {r.stdout}{r.stderr}")

        # zmiana pliku po dowodzie unieważnia go; etap przebiegu trafia do task.json; do PR tylko ze zweryfikowanymi
        run(SCRIPT, ["verify", str(d), "K2", "--files", "fees.py", "--command", OK], proj, cfg)
        (proj / "fees.py").write_text("LIMIT = 50\n", encoding="utf-8")
        r = run(SCRIPT, ["tick", str(d), "K2"], proj, cfg)
        check(r.returncode != 0 and "- [ ] K2" in plan.read_text(encoding="utf-8"),
              f"V-4: plik zmieniony po dowodzie → tick odrzucony: {r.returncode} {r.stdout}{r.stderr}")
        run(SCRIPT, ["stage", str(d), "plan"], proj, cfg)
        check(task().get("stage") == "plan", f"V-5a: stage plan trafia do task.json: {task().get('stage')}")
        inputs = sorted((task().get("artifacts", {}).get("plan.md", {}).get("inputs") or {}))
        check(inputs == ["spec.md", "ticket.md"], f"P-3: stage plan zapisuje, z czego powstał plan: {inputs}")
        run(SCRIPT, ["step", str(d), "K2", "R1", "test", "run"], proj, cfg)
        check(task().get("stage") == "realizacja", f"V-5b: pierwszy step → realizacja: {task().get('stage')}")
        r = run(SCRIPT, ["stage", str(d), "pr"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(r.returncode == 2 and meta.get("stage") != "pr" and task().get("stage") == "realizacja" and "K2" in r.stdout,
              f"V-6a: etap pr odrzucony z niezweryfikowanym kawałkiem: {r.returncode} {r.stdout} {meta.get('stage')}")
        r = run(SCRIPT, ["step", str(d), "PR", "plan_drift", "pass"], proj, cfg)
        check(r.returncode == 2 and json.loads((d / "run.json").read_text(encoding="utf-8")).get("stage") != "pr",
              f"V-6b: step PR też nie wchodzi do etapu pr bez dowodów: {r.returncode} {r.stdout}")
        for k in ("K1", "K2"):
            run(SCRIPT, ["verify", str(d), k, "--files", "fees.py", "--command", OK], proj, cfg)
        # flaga funkcji (krok D4): zadanie ze specyfikacją nie wchodzi do etapu pr bez flagi albo powodu jej braku
        r = run(SCRIPT, ["stage", str(d), "pr"], proj, cfg)
        check(r.returncode == 2 and "flag" in r.stdout, f"FL-1: etap pr odrzucony bez decyzji o fladze: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["flag", str(d), "mode"], proj, cfg)
        check(r.returncode == 0 and r.stdout.strip().startswith("auto"), f"FL-0a: domyślnie tryb flag to auto: {r.stdout}{r.stderr}")
        (proj / ".tf" / "config").mkdir(parents=True, exist_ok=True)
        (proj / ".tf" / "config" / "config.yaml").write_text("feature_flags:\n  auto: false\n", encoding="utf-8")
        r = run(SCRIPT, ["flag", str(d), "mode"], proj, cfg)
        check(r.returncode == 0 and r.stdout.strip().startswith("manual"), f"FL-0b: feature_flags.auto: false → tryb manual: {r.stdout}{r.stderr}")
        (proj / ".tf" / "config" / "config.yaml").unlink()
        r = run(SCRIPT, ["flag", str(d), "none"], proj, cfg)
        check(r.returncode == 2, f"FL-2: „bez flagi” wymaga powodu: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["flag", str(d), "set", "limit_dobowy", "--remove-by", "2027-01-31"], proj, cfg)
        check(r.returncode == 0 and task().get("flag", {}).get("key") == "limit_dobowy",
              f"FL-3: flag set przez skrypt przebiegu trafia do task.json: {r.returncode} {r.stdout}{r.stderr}")
        # zmiana specyfikacji po planie: plan jest nieaktualny, dopóki pętla nie przejdzie etapu plan ponownie
        (doc / "spec.md").write_text(SPEC.replace("45 zł", "50 zł"), encoding="utf-8")
        r = run(SCRIPT, ["stage", str(d), "pr"], proj, cfg)
        check(r.returncode == 2 and "plan.md" in r.stdout and task().get("stage") == "realizacja",
              f"P-4a: specyfikacja zmieniona po planie → etap pr odrzucony (plan nieaktualny): {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d), "plan"], proj, cfg)
        check(r.returncode == 0, f"P-4b: ponowny etap plan odświeża wejścia planu: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d), "pr"], proj, cfg)
        check(r.returncode == 0 and task().get("stage") == "pr"
              and json.loads((d / "run.json").read_text(encoding="utf-8")).get("stage") == "pr",
              f"V-6c: po dowodach etap pr przechodzi w run.json i task.json: {r.returncode} {r.stdout} {task().get('stage')}")

        # stary przebieg (.tf/runs/cuts/<data>-<slug>/, bez zadania) działa jak dotąd i jest na tej samej stronie
        old = proj / ".tf" / "runs" / "cuts" / "2026-10-01-stary"
        old.mkdir(parents=True)
        (old / "run.json").write_text(json.dumps({"slug": "stary", "title": "Stary przebieg",
                                                  "started_at": "2026-10-01T10:00:00+00:00"}), encoding="utf-8")
        (old / "plan.md").write_text("# Plan\n- [ ] K1 — stara lista · pliki: a.py\n", encoding="utf-8")
        r = run(SCRIPT, ["tick", str(old), "K1"], proj, cfg)
        check(r.returncode == 0 and "- [x] K1" in (old / "plan.md").read_text(encoding="utf-8"),
              f"V-7a: stary przebieg — tick bez dowodu jak dotąd: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["trace", str(old)], proj, cfg)
        check(r.returncode == 2 and "starym układzie" in r.stdout, f"TRC-2: trace w starym przebiegu → kod 2: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["verify", str(old), "K1", "--files", "fees.py", "--command", OK], proj, cfg)
        check(r.returncode == 2 and not (old / "evidence").exists(),
              f"V-7b: verify w starym przebiegu → kod 2 z wyjaśnieniem: {r.returncode} {r.stdout}")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        rs = runs_json((proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8"))
        slugs = {x.get("slug") for x in rs}
        new = next((x for x in rs if x.get("slug") != "stary"), {})
        check("stary" in slugs and len(rs) == 2 and [s["id"] for s in new.get("slices", [])] == ["K1", "K2"]
              and any(i["name"] == "ticket.md" for g in new.get("files", []) for i in g["items"]),
              f"V-8: stary i nowy przebieg na jednej stronie, nowy z planem i ticket.md: {slugs} {new.get('slices')}")

        # podgląd zadania (krok C5): etap zadania, katalog trwały i roboczy, dowody, osobny stan kawałka bez dowodu
        key = d.name
        grp = {g["grp"]: [i["name"] for i in g["items"]] for g in new.get("files", [])}
        durable = next((v for k, v in grp.items() if f"docs/project/changes/{key}" in k), [])
        working = next((v for k, v in grp.items() if f".tf/runs/{key}" in k), [])
        check(new.get("dir") == f".tf/runs/{key}" and new.get("taskDir") == f"docs/project/changes/{key}"
              and new.get("taskStage") == "pr" and new.get("key") == key,
              f"D-1: karta zna katalogi i etap zadania: {new.get('dir')} {new.get('taskDir')} {new.get('taskStage')}")
        check("ticket.md" in durable and "plan.md" in durable and "parked.md" in working,
              f"D-2: panel plików dzieli pliki na katalog trwały i roboczy: {grp}")
        check(any(n.startswith("evidence/K1-") for v in grp.values() for n in v),
              f"D-3: ostatni dowód kawałka w panelu plików: {grp}")
        old_o = next((x for x in rs if x.get("slug") == "stary"), {})
        check(old_o.get("dir") == ".tf/runs/cuts/2026-10-01-stary" and not old_o.get("taskDir"),
              f"D-4: stary przebieg wskazuje swój katalog: {old_o.get('dir')}")
        run(SCRIPT, ["tick", str(d), "K2"], proj, cfg)
        (proj / "fees.py").write_text("LIMIT = 55\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        html = (proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8")
        new = next((x for x in runs_json(html) if x.get("slug") != "stary"), {})
        st = {s["id"]: s["state"] for s in new.get("slices", [])}
        check(st == {"K1": "stale", "K2": "stale"} and all(s.get("proof") == "niezweryfikowany" for s in new["slices"]),
              f"D-5: odhaczony kawałek ze zmienionym plikiem ma stan stale: {new.get('slices')}")
        check(".chip.stale" in html and "r.slices.map" in html and "r.dir" in html,
              "D-6: szablon rysuje pasek kawałków, stan stale i katalog z danych przebiegu")

        # zadanie założone przez `tf task` (bez przebiegu, np. świeży klon) też ma kartę
        ts = ROOT / ".tf" / "factory" / "task_state.py"
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj)}
        subprocess.run([sys.executable, str(ts), "start", "PROJ-7", "--title", "Eksport faktur"], cwd=proj, env=env,
                       capture_output=True, text=True, timeout=60)
        subprocess.run([sys.executable, str(ts), "verify", "PROJ-7", "K1", "--files", "fees.py", "--command", OK],
                       cwd=proj, env=env, capture_output=True, text=True, timeout=60)
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        rs = runs_json((proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8"))
        bare = next((x for x in rs if x.get("key") == "PROJ-7"), {})
        check(len(rs) == 3 and bare.get("title") == "Eksport faktur" and bare.get("stage") == "intake"
              and bare.get("taskStage") == "przyjecie" and [(s["id"], s["state"]) for s in bare.get("slices", [])] == [("K1", "done")],
              f"D-7: zadanie bez przebiegu ma kartę z etapem i kawałkami: {len(rs)} {bare.get('stage')} {bare.get('slices')}")

    # waga zadania w pętli (krok E2): fabryka przydziela wagę i mówi dlaczego; skutki pilnuje skrypt
    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        ts = ROOT / ".tf" / "factory" / "task_state.py"
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj)}
        run(REPORT, ["start", "Reset hasła", "--key", "LOG-1", "--story",
                     "Jako użytkownik chcę zresetować hasło linkiem z maila. AC1: link ważny 30 minut."], proj, cfg)
        d = proj / ".tf" / "runs" / "LOG-1"
        r = run(SCRIPT, ["weight", str(d)], proj, cfg)
        data = json.loads((proj / CHANGES / "LOG-1" / "task.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and data.get("weight") == "pelna" and "pełna" in r.stdout and "hasł" in r.stdout
              and "człowiek" in r.stdout,
              f"W-1: run_state weight przydziela wagę pełną, podaje powód i skutek: {r.returncode} {r.stdout}{r.stderr}")
        (proj / CHANGES / "LOG-1" / "spec.md").write_text(SPEC, encoding="utf-8")
        (proj / CHANGES / "LOG-1" / "plan.md").write_text("# Plan\n- [ ] K1 — reset · pliki: reset.py\n", encoding="utf-8")
        r = run(SCRIPT, ["stage", str(d), "plan", "--auto"], proj, cfg)
        check(r.returncode == 0, f"W-2: plan zadania o wadze pełnej da się zapisać: {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["step", str(d), "K1", "R1", "test", "run"], proj, cfg)
        meta = json.loads((d / "run.json").read_text(encoding="utf-8"))
        check(r.returncode == 2 and "approve LOG-1 plan.md" in r.stdout and "STOP" in r.stdout
              and meta.get("stage") == "plan",
              f"W-3: waga pełna z --auto — pętla kawałka odrzucona z wyjaśnieniem, etap bez zmian: {r.returncode} {r.stdout}")
        subprocess.run([sys.executable, str(ts), "approve", "LOG-1", "plan.md", "--by", "human:anna"], cwd=proj, env=env,
                       capture_output=True, text=True, timeout=60)
        r = run(SCRIPT, ["step", str(d), "K1", "R1", "test", "run"], proj, cfg)
        check(r.returncode == 0, f"W-4: po zatwierdzeniu planu przez człowieka pętla rusza: {r.stdout}{r.stderr}")

        run(REPORT, ["start", "Literówka w README", "--key", "TYP-1", "--story",
                     "Popraw literówkę w README: instlacja na instalacja."], proj, cfg)
        d2 = proj / ".tf" / "runs" / "TYP-1"
        r = run(SCRIPT, ["weight", str(d2)], proj, cfg)
        check(r.returncode == 0 and "lekka" in r.stdout and "bez spec.md" in r.stdout,
              f"W-5: literówka → waga lekka ze skutkiem: {r.stdout}{r.stderr}")
        (proj / CHANGES / "TYP-1" / "plan.md").write_text("# Plan\n- [ ] K1 — literówka · pliki: README.md\n", encoding="utf-8")
        r = run(SCRIPT, ["stage", str(d2), "plan"], proj, cfg)
        check(r.returncode == 0 and not (proj / CHANGES / "TYP-1" / "spec.md").exists(),
              f"W-6: waga lekka — etap plan przebiegu bez spec.md: {r.returncode} {r.stdout}{r.stderr}")
        r = run(SCRIPT, ["weight", str(d2), "--set", "zwykla"], proj, cfg)
        r2 = run(SCRIPT, ["stage", str(d2), "plan"], proj, cfg)
        check(r.returncode == 0 and r2.returncode == 2 and "spec" in r2.stdout,
              f"W-7: po podniesieniu wagi do zwykłej specyfikacja znów jest wymagana: {r.stdout} | {r2.returncode} {r2.stdout}")
        r = run(SCRIPT, ["weight", str(d2), "--set", "lekka"], proj, cfg)
        check(r.returncode != 0 and "human:" in r.stdout, f"W-8: obniżenie wagi z pętli → odmowa: {r.returncode} {r.stdout}")
        run(REPORT, ["start", "Limit dobowy", "--key", "REG-1", "--story",
                     "Jako operator chcę podnieść limit dobowy opłaty z 40 zł do 45 zł. AC1: 12 h = 45 zł."], proj, cfg)
        d3 = proj / ".tf" / "runs" / "REG-1"
        (proj / CHANGES / "REG-1" / "spec.md").write_text(SPEC, encoding="utf-8")
        (proj / CHANGES / "REG-1" / "plan.md").write_text(
            "# Plan\n- [ ] K1 — limit · pliki: fees.py, db/migrations/0008_limit.sql\n", encoding="utf-8")
        r = run(SCRIPT, ["stage", str(d3), "plan"], proj, cfg)
        w = json.loads((proj / CHANGES / "REG-1" / "task.json").read_text(encoding="utf-8")).get("weight")
        check(r.returncode == 0 and w == "pelna" and "pełna" in r.stdout and "db/migrations/0008_limit.sql" in r.stdout,
              f"W-10: etap plan ponawia przydział — plan z migracją podnosi wagę i mówi dlaczego: {w} {r.stdout}{r.stderr}")
        subprocess.run([sys.executable, str(ts), "weight", "REG-1", "--set", "zwykla", "--by", "human:anna", "--reason",
                        "migracja dodaje tylko indeks"], cwd=proj, env=env, capture_output=True, text=True, timeout=60)
        r = run(SCRIPT, ["stage", str(d3), "plan"], proj, cfg)
        w = json.loads((proj / CHANGES / "REG-1" / "task.json").read_text(encoding="utf-8")).get("weight")
        check(r.returncode == 0 and w == "zwykla", f"W-11: waga obniżona przez człowieka zostaje przy kolejnym etapie: {w} {r.stdout}")
        # tryby (krok E3): Plan kończy się na planie, zwykły czeka na zgodę człowieka, Auto idzie dalej
        run(REPORT, ["start", "Eksport sesji", "--key", "EXP-1", "--story", "Jako operator chcę eksport sesji do pliku."],
            proj, cfg)
        d4 = proj / ".tf" / "runs" / "EXP-1"

        def t4():
            return json.loads((proj / CHANGES / "EXP-1" / "task.json").read_text(encoding="utf-8"))

        r = run(SCRIPT, ["stage", str(d4), "intake", "--plan", "--auto"], proj, cfg)
        check(r.returncode == 2, f"T-1: --plan i --auto naraz → kod 2: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d4), "intake", "--plan"], proj, cfg)
        check(r.returncode == 0 and t4().get("mode") == "plan", f"T-2: stage --plan zapisuje tryb Plan: {r.stdout} {t4().get('mode')}")
        (proj / CHANGES / "EXP-1" / "spec.md").write_text(SPEC, encoding="utf-8")
        (proj / CHANGES / "EXP-1" / "plan.md").write_text("# Plan\n- [ ] K1 — eksport · pliki: export.py\n", encoding="utf-8")
        run(SCRIPT, ["stage", str(d4), "plan"], proj, cfg)
        r = run(SCRIPT, ["step", str(d4), "K1", "R1", "test", "run"], proj, cfg)
        check(r.returncode == 2 and "Plan" in r.stdout and json.loads((d4 / "run.json").read_text(encoding="utf-8")).get("stage") == "plan",
              f"T-3: tryb Plan nie wchodzi w pętlę kawałka: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["mode", str(d4), "zwykly"], proj, cfg)
        r2 = run(SCRIPT, ["step", str(d4), "K1", "R1", "test", "run"], proj, cfg)
        check(r.returncode == 0 and t4().get("mode") == "zwykly" and r2.returncode == 2 and "approve" in r2.stdout,
              f"T-4: po przejściu na tryb zwykły pętla czeka na zgodę człowieka: {r.stdout} | {r2.returncode} {r2.stdout}")
        r = run(SCRIPT, ["approve", str(d4)], proj, cfg, {"GIT_AUTHOR_NAME": "Anna Nowak"})
        art = (t4().get("artifacts") or {}).get("plan.md") or {}
        who = (art.get("verified") or [{}])[-1].get("by", "")
        r2 = run(SCRIPT, ["step", str(d4), "K1", "R1", "test", "run"], proj, cfg)
        check(r.returncode == 0 and art.get("status") == "zatwierdzony" and who.startswith("human:") and r2.returncode == 0,
              f"T-5: approve zapisuje zgodę człowieka na plan i pętla rusza: {r.stdout}{r.stderr} {who} | {r2.stdout}")
        # identyfikator kryterium w teście już przy weryfikacji kawałka (pomiar po E3: dopisywany osobnym commitem)
        (proj / "export.py").write_text("ROWS = 1\n", encoding="utf-8")
        (proj / "tests").mkdir(exist_ok=True)
        (proj / "tests" / "test_export.py").write_text("def test_export():\n    assert True\n", encoding="utf-8")
        r = run(SCRIPT, ["verify", str(d4), "K1", "--files", "export.py,tests/test_export.py", "--command", OK], proj, cfg)
        check(r.returncode == 0 and "⚠" in r.stdout and "AC-" in r.stdout and "tests/test_export.py" in r.stdout
              and "przed commitem" in r.stdout,
              f"A-1: verify ostrzega, gdy test kawałka nie ma identyfikatora kryterium: {r.returncode} {r.stdout}")
        (proj / "tests" / "test_export.py").write_text("def test_ac1_export():  # AC-1\n    assert True\n", encoding="utf-8")
        r = run(SCRIPT, ["verify", str(d4), "K1", "--files", "export.py,tests/test_export.py", "--command", OK], proj, cfg)
        check(r.returncode == 0 and "⚠" not in r.stdout, f"A-2: z identyfikatorem w teście bez ostrzeżenia: {r.stdout}")
        r = run(SCRIPT, ["verify", str(d4), "K1", "--files", "export.py", "--command", OK], proj, cfg)
        check(r.returncode == 0 and "⚠" in r.stdout and "pliku testu" in r.stdout,
              f"A-3: verify ostrzega, gdy wśród plików kawałka nie ma testu: {r.stdout}")
        r = run(SCRIPT, ["verify", str(d2), "K1", "--files", "README.md", "--command", OK], proj, cfg)
        check("⚠" not in r.stdout, f"A-4: zadanie bez specyfikacji (waga lekka) — bez ostrzeżenia o kryteriach: {r.stdout}")

        run(REPORT, ["start", "Import sesji", "--key", "IMP-1", "--story", "Jako operator chcę import sesji z pliku."],
            proj, cfg)
        d5 = proj / ".tf" / "runs" / "IMP-1"
        r = run(SCRIPT, ["stage", str(d5), "intake", "--auto"], proj, cfg)
        mode = json.loads((proj / CHANGES / "IMP-1" / "task.json").read_text(encoding="utf-8")).get("mode")
        r2 = run(SCRIPT, ["approve", str(d5)], proj, cfg)
        check(r.returncode == 0 and mode == "auto" and r2.returncode == 2 and "człowiek" in r2.stdout,
              f"T-6: --auto zapisuje tryb Auto; zgody na plan nie da się zapisać bez człowieka: {mode} | {r2.returncode} {r2.stdout}")
        r = run(SCRIPT, ["stage", str(d), "intake", "--auto"], proj, cfg)        # LOG-1: waga pełna
        mode = json.loads((proj / CHANGES / "LOG-1" / "task.json").read_text(encoding="utf-8")).get("mode")
        check(r.returncode == 0 and mode == "zwykly" and "pełn" in r.stdout,
              f"T-7: --auto przy wadze pełnej — zostaje tryb zwykły z wyjaśnieniem: {mode} {r.stdout}")

        # zamknięta lista kodów zatrzymań: brak kodu albo kod spoza listy to błąd; podgląd pokazuje przyczynę
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "stop", "--reason", "Brak kryteriów."], proj, cfg)
        check(r.returncode == 2 and "pytanie" in r.stdout and "budzet" in r.stdout,
              f"T-8: STOP bez kodu → kod 2 z listą kodów: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "stop", "--code", "zmeczenie", "--reason", "x"], proj, cfg)
        check(r.returncode == 2 and "pytanie" in r.stdout, f"T-9: kod spoza listy → kod 2: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "stop", "--code", "pytanie", "--reason",
                         "Brak kryteriów akceptacji."], proj, cfg)
        meta = json.loads((d5 / "run.json").read_text(encoding="utf-8"))
        card = next((x for x in runs_json((proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8"))
                     if x.get("key") == "IMP-1"), {})
        check(r.returncode == 0 and meta.get("stop_code") == "pytanie" and card.get("stopCode") == "pytanie"
              and card.get("stopLabel") and "Brak kryteriów akceptacji." in (card.get("stopText") or "")
              and "r.stopLabel" in (proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8"),
              f"T-10: STOP z kodem — kod w run.json, kod, opis i powód na podglądzie: {r.stdout} {card.get('stopCode')} {card.get('stopLabel')}")
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "plan", "--code", "pytanie"], proj, cfg)
        check(r.returncode == 2, f"T-11: --code tylko dla --needs stop: {r.returncode} {r.stdout}")

        # komunikat zatrzymania w prostym języku (krok E4): co się stało, czego potrzeba, pytanie z opcjami
        r = run(SCRIPT, ["message", "pytanie"], proj, cfg)
        check(r.returncode == 0 and all(s in r.stdout for s in ("Co się stało:", "Czego potrzeba:", "Pytanie:", "Potem:"))
              and r.stdout.count("(rekomendowana)") == 1 and "  1. " in r.stdout and "  2. " in r.stdout,
              f"K-1: message <kod> drukuje komunikat ze stałymi polami i jedną rekomendacją: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["message", "zmeczenie"], proj, cfg)
        check(r.returncode == 2 and "pytanie" in r.stdout, f"K-2: message z kodem spoza listy → kod 2: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["message", "budzet", "--json"], proj, cfg)
        msg = json.loads(r.stdout) if r.returncode == 0 else {}
        check(msg.get("kod") == "budzet" and msg.get("pytanie", "").endswith("?") and len(msg.get("opcje", [])) >= 2,
              f"K-3: message --json: {r.stdout[:200]}")
        r = run(SCRIPT, ["stage", str(d5), "needs", "--needs", "stop", "--code", "testy", "--reason",
                         "pytest: 2 failed (test_fees.py)"], proj, cfg)
        check(r.returncode == 0 and "Co się stało: Testy nie przechodzą" in r.stdout and "pytest: 2 failed (test_fees.py)" in r.stdout
              and "Pytanie:" in r.stdout and "AskUserQuestion" in r.stdout,
              f"K-4: zapis STOP drukuje komunikat dla człowieka z powodem przebiegu: {r.stdout}")
        html = (proj / ".tf" / "runs" / "dashboard.html").read_text(encoding="utf-8")
        card = next((x for x in runs_json(html) if x.get("key") == "IMP-1"), {})
        stop_file = next((i for g in card.get("files", []) for i in g.get("items", []) if i.get("name") == "STOP"), {})
        check(card.get("stopNeed") and card.get("stopQuestion", "").endswith("?") and len(card.get("stopOptions") or []) >= 2
              and "Czego potrzeba" in stop_file.get("text", "") and "r.stopQuestion" in html,
              f"K-5: podgląd pokazuje, czego potrzeba, i pytanie z opcjami: {card.get('stopNeed')} {card.get('stopQuestion')}")

        old = proj / ".tf" / "runs" / "cuts" / "2026-10-01-stary"
        old.mkdir(parents=True)
        (old / "run.json").write_text(json.dumps({"slug": "stary", "title": "Stary przebieg",
                                                  "started_at": "2026-10-01T10:00:00+00:00"}), encoding="utf-8")
        r = run(SCRIPT, ["stage", str(old), "needs", "--needs", "stop", "--code", "testy", "--reason", "czerwone"], proj, cfg)
        check(r.returncode == 0, f"T-12: przebieg cięcia też zapisuje STOP z kodem: {r.returncode} {r.stdout}")
        r = run(SCRIPT, ["weight", str(old)], proj, cfg)
        check(r.returncode == 2 and "cięci" in r.stdout, f"W-9: przebieg cięcia nie ma wagi: {r.returncode} {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} testów stanu przebiegu: {'wszystkie przeszły' if not fails else len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
