#!/usr/bin/env python3
"""Testy stanu przebiegu Talosa i dashboardu (tryb mode-talos, skill talos-story-run, scripts/run_state.py).
python3 .claude/tests/test_run_state.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "talos-story-run" / "scripts" / "run_state.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL
REPORT = SCRIPT.with_name("run_report.py")


def run(script, args, cwd, cfg, extra_env=None):
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(cfg), "TALOS_DASHBOARD_OPEN": "0", **(extra_env or {})}
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
        d = next((proj / ".tf" / "runs" / "talos").glob("*-sortowanie-listy"), None)
        check(r.returncode == 0 and d is not None, f"S-0: przygotowanie przebiegu: {r.stdout} {r.stderr}")
        if d is None:
            print("✗ brak katalogu przebiegu")
            return 1
        dash = proj / ".tf" / "runs" / "talos" / "dashboard.html"

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
        (d / "plan.md").write_text("# Plan\n- [ ] K1 — sortowanie rosnące · kryteria: t\n- [ ] K2 — malejące · kryteria: t\n"
                                   "- [ ] K3 — po dacie · kryteria: t\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        o = one()
        check(o.get("stage") == "plan" and [s["id"] for s in o["slices"]] == ["K1", "K2", "K3"],
              f"S-2a: plan z kawałkami → etap plan: {o.get('stage')}")
        (d / "plan.md").write_text("# Plan\n- [x] K1 — sortowanie rosnące · kryteria: t\n- [ ] K2 — malejące · kryteria: t\n"
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
        r = run(SCRIPT, ["stage", str(d), "needs", "--needs", "stop", "--reason", "Skan czerwony po 2 próbach (K2)."],
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
        (d / "report.md").write_text("# Raport\nok\n", encoding="utf-8")
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
        (d / "story.md").write_text("# s\n</script><b>x</b>\n", encoding="utf-8")
        run(SCRIPT, ["dashboard", "--no-cost"], proj, cfg)
        html = dash.read_text(encoding="utf-8")
        check(html.count("</script>") == 1 and "</script><b>" not in html,
              f"S-9: </script> w treści pliku nie rozbija strony: {html.count('</script>')}")

    # S-10: start przebiegu buduje dashboard (domyślnie włączony), a opcje w .claude/talos.json i zmienne go wyłączają
    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        dash = proj / ".tf" / "runs" / "talos" / "dashboard.html"
        r = run(REPORT, ["start", "Pierwsza historyjka", "--story", "x"], proj, cfg)
        check(r.returncode == 0 and dash.is_file() and "Dashboard: file://" in r.stderr
              and r.stdout.strip().startswith(".tf/runs/talos/"),
              f"S-10a: start buduje dashboard, adres na stderr, stdout bez zmian: {r.stdout!r} {r.stderr!r}")
        dash.unlink()
        (proj / ".claude").mkdir()
        (proj / ".claude" / "talos.json").write_text('{"dashboard": false}', encoding="utf-8")
        r = run(REPORT, ["start", "Druga historyjka", "--story", "x"], proj, cfg)
        check(r.returncode == 0 and not dash.exists() and "Dashboard" not in r.stderr,
              f"S-10b: {{\"dashboard\": false}} — start niczego nie buduje: {r.stderr!r}")
        (proj / ".claude" / "talos.json").write_text('{"dashboard_open": false}', encoding="utf-8")
        r = run(REPORT, ["start", "Trzecia historyjka", "--story", "x"], proj, cfg)
        check(dash.is_file(), "S-10c: dashboard_open=false — buduje, ale nie otwiera (plik jest)")
        dash.unlink()
        (proj / ".claude" / "talos.json").unlink()
        r = run(REPORT, ["start", "Czwarta historyjka", "--story", "x"], proj, cfg, {"TALOS_DASHBOARD": "0"})
        check(r.returncode == 0 and not dash.exists(), "S-10d: TALOS_DASHBOARD=0 wyłącza bez pliku")
        # uszkodzony plik opcji → domyślne (włączone), przebieg się nie wywraca
        (proj / ".claude" / "talos.json").write_text("{nie json", encoding="utf-8")
        r = run(REPORT, ["start", "Piata historyjka", "--story", "x"], proj, cfg)
        check(r.returncode == 0 and dash.is_file(), f"S-10e: uszkodzony talos.json → opcje domyślne: {r.stderr!r}")

    # jedna czynność na polecenie: odhaczenie kawałka i odłożenie sprawy skryptem (bez sed, >> i heredoc w powłoce)
    with tempfile.TemporaryDirectory() as t:
        proj, cfg = Path(t) / "proj", Path(t) / "cfg"
        proj.mkdir()
        run(REPORT, ["start", "Limit dobowy", "--story", "Jako operator chcę limit."], proj, cfg)
        d = next((proj / ".tf" / "runs" / "talos").glob("*-limit-dobowy"), None)
        plan = d / "plan.md"
        head = plan.read_text(encoding="utf-8")
        plan.write_text(head + "- [ ] K1 — limit 45 zł · kryteria: AC1 · pliki: fees.py\n"
                               "- [ ] K2 — druga doba · kryteria: AC3 · pliki: fees.py\n", encoding="utf-8")
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

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} testów stanu przebiegu Talosa: {'wszystkie przeszły' if not fails else len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
