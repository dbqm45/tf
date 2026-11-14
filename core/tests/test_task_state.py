#!/usr/bin/env python3
"""Testy stanu zadania (.tf/factory/task_state.py): katalog `docs/project/changes/<KEY>/` z `task.json`, etapy
i indeks zadań — jeden pisarz, bez modelu i bez sieci. python3 tests/test_task_state.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCRIPT = ROOT / ".tf" / "factory" / "task_state.py"
CTF = ROOT / ".tf" / "factory" / "tf.py"
CHANGES = Path("docs") / "project" / "changes"
OK = f'{sys.executable} -c "print(\'8 passed\')"'
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi "
        "{limit} zł.\n\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")
RED = f'{sys.executable} -c "print(\'FAILED test_x\'); raise SystemExit(3)"'


def run(project: Path, *args: str):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def task(project: Path, key: str) -> dict:
    f = project / CHANGES / key / "task.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def index_rows(project: Path) -> list[str]:
    f = project / CHANGES / "INDEX.md"
    text = f.read_text(encoding="utf-8") if f.is_file() else ""
    return [ln for ln in text.splitlines() if ln.startswith("| ") and not ln.startswith(("| Klucz", "| ---", "|---"))]


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not SCRIPT.is_file():
        print(f"✗ brak {SCRIPT}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        p.mkdir()
        r = run(p, "start", "PROJ-123", "--title", "Limit dobowy 45 zł", "--weight", "lekka", "--mode", "auto")
        d = task(p, "PROJ-123")
        check(r.returncode == 0 and d.get("key") == "PROJ-123" and d.get("title") == "Limit dobowy 45 zł"
              and d.get("stage") == "przyjecie" and d.get("weight") == "lekka" and d.get("mode") == "auto"
              and d.get("schema") == 1 and d.get("created") and d.get("created") == d.get("updated"),
              f"TS-1: start tworzy docs/project/changes/<KEY>/task.json z etapem przyjecie: {r.stdout}{r.stderr}{d}")
        rows = index_rows(p)
        check(len(rows) == 1 and "PROJ-123" in rows[0] and "Limit dobowy 45 zł" in rows[0] and "przyjecie" in rows[0],
              f"TS-2: indeks ma wiersz zadania z etapem: {rows}")

        before = (p / CHANGES / "PROJ-123" / "task.json").read_text(encoding="utf-8")
        r = run(p, "start", "PROJ-123", "--title", "Inny tytuł")
        check(r.returncode == 1 and (p / CHANGES / "PROJ-123" / "task.json").read_text(encoding="utf-8") == before
              and "już istnieje" in r.stdout, f"TS-3: ponowny start nie nadpisuje zadania: {r.returncode} {r.stdout}")

        for bad in ("abc", "../x", "proj-1", "PROJ 1", "PROJ-"):
            r = run(p, "start", bad, "--title", "x")
            check(r.returncode == 2 and not any(p.glob(f"**/{bad.strip('./')}/task.json")),
                  f"TS-4: klucz spoza wzorca odrzucony ({bad!r}): {r.returncode} {r.stdout}")
        check(not (p.parent / "x").exists(), "TS-5: klucz ze ścieżką nie tworzy niczego poza katalogiem zadań")

        r = run(p, "stage", "PROJ-123", "wymyslony")
        check(r.returncode == 2 and task(p, "PROJ-123")["stage"] == "przyjecie" and "specyfikacja" in r.stdout,
              f"TS-6: nieznany etap → błąd z listą etapów, stan bez zmian: {r.stdout}")
        r = run(p, "stage", "PROJ-123", "plan")
        d = task(p, "PROJ-123")
        check(r.returncode == 0 and d["stage"] == "plan" and d["updated"] >= d["created"]
              and "plan" in index_rows(p)[0], f"TS-7: etap do przodu zapisany w task.json i w indeksie: {r.stdout}{d}")
        r = run(p, "stage", "PROJ-123", "specyfikacja")
        check(r.returncode == 1 and task(p, "PROJ-123")["stage"] == "plan" and "--force" in r.stdout,
              f"TS-8: etap wstecz bez --force odrzucony: {r.returncode} {r.stdout}")
        r = run(p, "stage", "PROJ-123", "specyfikacja", "--force")
        check(r.returncode == 0 and task(p, "PROJ-123")["stage"] == "specyfikacja", f"TS-9: --force cofa etap: {r.stdout}")

        run(p, "start", "ABC-7", "--title", "Raport | z kreską")
        run(p, "stage", "ABC-7", "specyfikacja")
        run(p, "stage", "PROJ-123", "plan")
        rows = index_rows(p)
        check(len(rows) == 2 and rows[0].startswith("| ABC-7 ") and rows[1].startswith("| PROJ-123 ")
              and rows[0].replace("\\|", "").count("|") == rows[1].count("|") and "\\|" in rows[0],
              f"TS-10: jeden wiersz na zadanie, posortowane; kreska w tytule nie psuje tabeli: {rows}")

        r = run(p, "status", "PROJ-123", "--json")
        try:
            s = json.loads(r.stdout)
        except ValueError:
            s = {}
        check(r.returncode == 0 and s.get("stage") == "plan" and s.get("key") == "PROJ-123", f"TS-11: status --json: {r.stdout}")
        r = run(p, "status", "PROJ-123")
        check(r.returncode == 0 and "PROJ-123" in r.stdout and "plan" in r.stdout and "{" not in r.stdout,
              f"TS-12: status dla człowieka w zwykłym tekście: {r.stdout}")
        r = run(p, "status", "NIE-MA")
        check(r.returncode == 1 and "NIE-MA" in r.stdout and "start" in r.stdout, f"TS-13: nieznane zadanie → podpowiedź: {r.stdout}")
        r = run(p, "stage", "NIE-MA", "plan")
        check(r.returncode == 1 and not (p / CHANGES / "NIE-MA").exists(), "TS-14: etap nieistniejącego zadania niczego nie tworzy")

        # katalog zmiany z trybu pdi: skrypt dokłada task.json i nie rusza plików pdi
        pdi = p / CHANGES / "CHG-12"
        pdi.mkdir(parents=True)
        plan = "---\nartifact: plan\nchange: CHG-12\nstatus: draft\ntasks: [TSK-57]\n---\n# Plan\n"
        (pdi / "plan.md").write_text(plan, encoding="utf-8")
        r = run(p, "start", "CHG-12", "--title", "Import CDR")
        check(r.returncode == 0 and task(p, "CHG-12").get("key") == "CHG-12"
              and (pdi / "plan.md").read_text(encoding="utf-8") == plan,
              f"TS-15: istniejący katalog pdi dostaje task.json, plan.md bez zmian: {r.stdout}{r.stderr}")
        check((p / CHANGES / "INDEX.md").read_text(encoding="utf-8").count("CHG-12") == 1, "TS-16: zadanie pdi jest w indeksie raz")

        r = run(p, "start", "T-20261113-bez-tytulu")
        check(r.returncode == 2 and "--title" in r.stdout, f"TS-17: start bez tytułu → użycie: {r.stdout}")
        r = run(p, "start", "T-20261113-waga", "--title", "x", "--weight", "ogromna")
        check(r.returncode == 2 and not (p / CHANGES / "T-20261113-waga").exists(), f"TS-18: nieznana waga odrzucona: {r.stdout}")

        # C2: kawałki i dowody — „zrobione” znaczy „jest dowód powstały po ostatniej zmianie plików”
        def states(key):
            r = run(p, "status", key, "--json")
            try:
                return json.loads(r.stdout).get("slice_states", {})
            except ValueError:
                return {"błąd": r.stdout + r.stderr}

        (p / "src").mkdir()
        (p / "src" / "fees.py").write_text("CAP = 4000\n", encoding="utf-8")
        run(p, "start", "EV-1", "--title", "Dowody")
        r = run(p, "slice", "EV-1", "K1", "planned", "--title", "limit 45 zł")
        check(r.returncode == 0 and states("EV-1") == {"K1": "zaplanowany"}, f"TS-20: kawałek zaplanowany: {r.stdout}{states('EV-1')}")
        run(p, "slice", "EV-1", "K1", "implemented")
        check(states("EV-1") == {"K1": "niezweryfikowany"}, f"TS-21: zrobione bez dowodu to niezweryfikowany: {states('EV-1')}")
        r = run(p, "verify", "EV-1", "K1", "--command", OK, "--files", "src/fees.py")
        ev = p / CHANGES / "EV-1" / "evidence" / "K1-1.json"
        e = json.loads(ev.read_text(encoding="utf-8")) if ev.is_file() else {}
        check(r.returncode == 0 and e.get("command") == OK and e.get("exit_code") == 0 and e.get("at")
              and len((e.get("files") or {}).get("src/fees.py", "")) == 64 and e.get("slice") == "K1",
              f"TS-22: dowód w evidence/K1-1.json: polecenie, kod wyjścia, czas, skróty plików: {r.stdout}{r.stderr}{e}")
        check(states("EV-1") == {"K1": "zweryfikowany"}, f"TS-23: zielony dowód na bieżących plikach → zweryfikowany: {states('EV-1')}")
        (p / "src" / "fees.py").write_text("CAP = 4500\n", encoding="utf-8")
        r = run(p, "status", "EV-1")
        check(states("EV-1") == {"K1": "niezweryfikowany"} and "zmienion" in r.stdout and "K1" in r.stdout,
              f"TS-24: zmiana pliku po dowodzie → niezweryfikowany, z powodem: {r.stdout}")
        r = run(p, "stage", "EV-1", "przeglad")
        check(r.returncode == 1 and "K1" in r.stdout and task(p, "EV-1")["stage"] == "przyjecie",
              f"TS-25: przegląd odrzucony, gdy kawałek nie jest zweryfikowany: {r.returncode} {r.stdout}")
        r = run(p, "verify", "EV-1", "K1", "--command", RED, "--files", "src/fees.py")
        e2 = json.loads((ev.parent / "K1-2.json").read_text(encoding="utf-8")) if (ev.parent / "K1-2.json").is_file() else {}
        log = p / ".tf" / "runs" / "EV-1" / "K1-2.log"
        check(r.returncode == 1 and e2.get("exit_code") == 3 and log.is_file() and "FAILED test_x" in log.read_text(encoding="utf-8")
              and "FAILED test_x" in r.stdout,
              f"TS-37: verify samo uruchamia polecenie: prawdziwy kod wyjścia w dowodzie, wyjście w .tf/runs/: {r.returncode} {r.stdout}{e2}")
        check(states("EV-1") == {"K1": "czerwony"} and ev.is_file() and (ev.parent / "K1-2.json").is_file(),
              f"TS-26: czerwony dowód → czerwony; poprzedni dowód zostaje, nowy ma kolejny numer: {states('EV-1')}")
        run(p, "verify", "EV-1", "K1", "--command", OK, "--files", "src/fees.py")
        r = run(p, "stage", "EV-1", "przeglad")
        check(r.returncode == 0 and task(p, "EV-1")["stage"] == "przeglad", f"TS-27: po zielonym dowodzie przegląd dozwolony: {r.stdout}")
        (p / "src" / "fees.py").unlink()
        check(states("EV-1") == {"K1": "niezweryfikowany"}, f"TS-28: usunięty plik po dowodzie → niezweryfikowany: {states('EV-1')}")

        (p / "src" / "cli.py").write_text("x = 1\n", encoding="utf-8")
        run(p, "start", "EV-2", "--title", "Blokada")
        r = run(p, "slice", "EV-2", "K1", "blocked", "--reason", "czeka na decyzję o stawce")
        check(states("EV-2") == {"K1": "zablokowany"} and run(p, "stage", "EV-2", "przeglad").returncode == 1
              and "czeka na decyzję" in run(p, "status", "EV-2").stdout,
              f"TS-29: kawałek zablokowany z powodem wstrzymuje przegląd: {r.stdout}{states('EV-2')}")
        r = run(p, "verify", "EV-2", "K2", "--command", OK)
        check(r.returncode == 2 and "--files" in r.stdout, f"TS-30: dowód bez plików odrzucony: {r.returncode} {r.stdout}")
        r = run(p, "verify", "EV-2", "K2", "--command", OK, "--files", "../poza.py")
        check(r.returncode == 2 and not (p / CHANGES / "EV-2" / "evidence").exists(), f"TS-31: plik spoza projektu odrzucony: {r.stdout}")
        r = run(p, "verify", "EV-2", "K2", "--command", OK, "--files", "src/nie-ma.py")
        check(r.returncode == 2 and "nie-ma.py" in r.stdout, f"TS-32: nieistniejący plik odrzucony: {r.stdout}")
        r = run(p, "slice", "EV-2", "X1", "planned")
        check(r.returncode == 2, f"TS-33: zły identyfikator kawałka odrzucony: {r.returncode} {r.stdout}")
        r = run(p, "slice", "EV-2", "K3", "gotowe")
        check(r.returncode == 2 and "implemented" in r.stdout, f"TS-34: nieznany stan kawałka → lista stanów: {r.stdout}")
        run(p, "start", "EV-3", "--title", "Bez kawałków")
        check(run(p, "stage", "EV-3", "przeglad").returncode == 0, "TS-35: zadanie bez kawałków przechodzi do przeglądu")
        r = run(p, "verify", "EV-3", "K1", "--command", OK, "--files", "src/cli.py")
        check(r.returncode == 0 and states("EV-3") == {"K1": "zweryfikowany"}, f"TS-36: verify zakłada kawałek, jeśli go nie było: {r.stdout}")
        r = run(p, "verify", "EV-3", "K2", "--files", "src/cli.py")
        check(r.returncode == 2 and "quality-gate.json" in r.stdout, f"TS-38: bez --command i bez bramki → nie ma czego uruchomić: {r.stdout}")
        (p / ".claude").mkdir(exist_ok=True)
        (p / ".claude" / "quality-gate.json").write_text(json.dumps({"command": OK}), encoding="utf-8")
        r = run(p, "verify", "EV-3", "K2", "--files", "src/cli.py")
        e3 = json.loads((p / CHANGES / "EV-3" / "evidence" / "K2-1.json").read_text(encoding="utf-8")) if r.returncode == 0 else {}
        check(r.returncode == 0 and e3.get("command") == OK and states("EV-3").get("K2") == "zweryfikowany",
              f"TS-39: bez --command verify uruchamia polecenie bramki jakości: {r.stdout}{r.stderr}")
        r = run(p, "verify", "EV-3", "K2", "--command", OK, "--exit", "0", "--files", "src/cli.py")
        check(r.returncode == 2, f"TS-40: kodu wyjścia nie da się zadeklarować (--exit odrzucone): {r.returncode}")

        # C3: pliki zadania — kto je wygenerował i zatwierdził, z czego powstały, czy są jeszcze aktualne
        def astates(key):
            r = run(p, "status", key, "--json")
            try:
                return json.loads(r.stdout).get("artifact_states", {})
            except ValueError:
                return {"błąd": r.stdout + r.stderr}

        run(p, "start", "AR-1", "--title", "Pliki zadania")
        folder = p / CHANGES / "AR-1"
        (folder / "spec.md").write_text(SPEC.format(limit=45), encoding="utf-8")
        (folder / "plan.md").write_text("# Plan\n- [ ] K1\n", encoding="utf-8")
        r = run(p, "artifact", "AR-1", "spec.md", "--stage", "specyfikacja", "--by", "tf/1.0.0")
        a = task(p, "AR-1").get("artifacts", {}).get("spec.md", {})
        check(r.returncode == 0 and a.get("stage") == "specyfikacja" and a.get("generated", {}).get("by") == "tf/1.0.0"
              and a.get("generated", {}).get("at") and astates("AR-1") == {"spec.md": "szkic"},
              f"TS-41: plik zarejestrowany jako szkic, z wykonawcą i czasem: {r.stdout}{r.stderr}{a}")
        r = run(p, "artifact", "AR-1", "nie-ma.md", "--stage", "plan", "--by", "tf/1.0.0")
        check(r.returncode == 2 and "nie-ma.md" in r.stdout, f"TS-42: nieistniejący plik odrzucony: {r.stdout}")
        r = run(p, "approve", "AR-1", "spec.md", "--by", "tf/1.0.0")
        check(r.returncode == 2 and astates("AR-1") == {"spec.md": "szkic"} and "human:" in r.stdout,
              f"TS-43: zatwierdza tylko człowiek (human:<id>): {r.returncode} {r.stdout}")
        r = run(p, "approve", "AR-1", "spec.md", "--by", "human:anna")
        a = task(p, "AR-1")["artifacts"]["spec.md"]
        check(r.returncode == 0 and astates("AR-1") == {"spec.md": "zatwierdzony"}
              and a.get("verified", [{}])[-1].get("by") == "human:anna" and a["verified"][-1].get("at"),
              f"TS-44: zatwierdzenie przez człowieka zapisane z czasem: {r.stdout}{a}")
        run(p, "artifact", "AR-1", "plan.md", "--stage", "plan", "--by", "tf/1.0.0", "--inputs", "spec.md")
        run(p, "approve", "AR-1", "plan.md", "--by", "human:anna")
        r = run(p, "check", "AR-1")
        check(r.returncode == 0 and astates("AR-1") == {"plan.md": "zatwierdzony", "spec.md": "zatwierdzony"},
              f"TS-45: wszystko aktualne → check 0: {r.returncode} {r.stdout}")
        (folder / "spec.md").write_text(SPEC.format(limit=50), encoding="utf-8")
        r = run(p, "check", "AR-1")
        s = astates("AR-1")
        check(r.returncode == 1 and s.get("plan.md") == "nieaktualny" and s.get("spec.md") == "zmieniony po zatwierdzeniu"
              and "spec.md" in r.stdout and "plan.md" in r.stdout,
              f"TS-46: zmiana spec.md po zatwierdzeniu planu → plan nieaktualny, spec do ponownego zatwierdzenia: {r.stdout}{s}")
        r = run(p, "status", "AR-1")
        check("nieaktualny" in r.stdout and "plan.md" in r.stdout, f"TS-47: status dla człowieka pokazuje nieaktualny plik: {r.stdout}")
        run(p, "artifact", "AR-1", "plan.md", "--stage", "plan", "--by", "tf/1.0.0", "--inputs", "spec.md")
        check(astates("AR-1").get("plan.md") == "szkic", f"TS-48: ponowna rejestracja odświeża wejścia i kasuje zatwierdzenie: {astates('AR-1')}")
        run(p, "approve", "AR-1", "spec.md", "--by", "human:anna")
        run(p, "approve", "AR-1", "plan.md", "--by", "human:jan")
        r = run(p, "check", "AR-1")
        check(r.returncode == 0 and len(task(p, "AR-1")["artifacts"]["plan.md"]["verified"]) == 1,
              f"TS-49: po ponownym zatwierdzeniu check 0; stare zatwierdzenia nie zostają: {r.stdout}")
        for bad, why in ((("artifact", "AR-1", "plan.md", "--stage", "plan", "--by", "tf/1.0.0", "--inputs", "../../x.md"), "wejście spoza katalogu"),
                         (("artifact", "AR-1", "plan.md", "--stage", "wymyslony", "--by", "tf/1.0.0"), "nieznany etap"),
                         (("artifact", "AR-1", "plan.md", "--stage", "plan", "--by", "ktoś"), "zły zapis wykonawcy"),
                         (("artifact", "AR-1", "../EV-1/task.json", "--stage", "plan", "--by", "tf/1.0.0"), "plik spoza katalogu"),
                         (("approve", "AR-1", "report.md", "--by", "human:anna"), "plik niezarejestrowany")):
            r = run(p, *bad)
            check(r.returncode == 2, f"TS-50: odrzucone ({why}): {r.returncode} {r.stdout}")
        # plik z nagłówkiem kontraktu pdi: rejestracja i zatwierdzenie nie zmieniają ani bajtu
        run(p, "artifact", "CHG-12", "plan.md", "--stage", "plan", "--by", "process:pdi")
        run(p, "approve", "CHG-12", "plan.md", "--by", "human:anna")
        check((pdi / "plan.md").read_text(encoding="utf-8") == plan and astates("CHG-12") == {"plan.md": "zatwierdzony"},
              f"TS-51: plik pdi zarejestrowany i zatwierdzony bez zmiany treści: {astates('CHG-12')}")
        r = run(p, "stage", "AR-1", "realizacja")
        (folder / "spec.md").write_text(SPEC.format(limit=55), encoding="utf-8")
        r = run(p, "stage", "AR-1", "przeglad")
        check(r.returncode == 1 and "plan.md" in r.stdout and task(p, "AR-1")["stage"] == "realizacja",
              f"TS-52: przegląd odrzucony, gdy plik zadania jest nieaktualny: {r.returncode} {r.stdout}")

        # tf task … uruchamia skrypt w projekcie
        q = Path(t) / "viatf"
        (q / ".tf" / "factory").mkdir(parents=True)
        (q / ".claude").mkdir()
        (q / ".claude" / "factory-manifest.json").write_text(json.dumps({"version": "1.0.0"}))
        shutil.copy(SCRIPT, q / ".tf" / "factory" / "task_state.py")
        r = subprocess.run([sys.executable, str(CTF), "task", "start", "PROJ-9", "--title", "Przez tf"], cwd=q,
                           capture_output=True, text=True, timeout=60)
        check(r.returncode == 0 and task(q, "PROJ-9").get("title") == "Przez tf", f"TS-19: tf task start: {r.stdout}{r.stderr}")

        # lista zadań (krok C5): `tf status` — etap, kawałki z dowodem, pliki do odświeżenia; stan liczony przy odczycie
        r = run(q, "list")
        check(r.returncode == 0 and "PROJ-9" in r.stdout and "przyjecie" in r.stdout and "Przez tf" in r.stdout,
              f"TS-53: list pokazuje zadanie z etapem i tytułem: {r.stdout}{r.stderr}")
        (q / "src").mkdir(exist_ok=True)
        (q / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
        run(q, "verify", "PROJ-9", "K1", "--command", OK, "--files", "src/a.py")
        run(q, "slice", "PROJ-9", "K2", "planned")
        r = run(q, "list", "--json")
        try:
            rows = {x["key"]: x for x in json.loads(r.stdout)}
        except (ValueError, KeyError, TypeError):
            rows = {}
        row = rows.get("PROJ-9", {})
        check(row.get("stage") == "przyjecie" and row.get("slices") == {"K1": "zweryfikowany", "K2": "zaplanowany"}
              and row.get("verified") == 1 and row.get("stale") == [],
              f"TS-54: list --json: etap, stany kawałków, liczba zweryfikowanych: {r.stdout[:300]}{r.stderr}")
        (q / "src" / "a.py").write_text("a = 2\n", encoding="utf-8")
        r = run(q, "list")
        line = next((ln for ln in r.stdout.splitlines() if "PROJ-9" in ln), "")
        check("0/2" in line and "niezweryfikowany" in r.stdout, f"TS-55: zmiana pliku po dowodzie widać na liście: {r.stdout}")
        r = subprocess.run([sys.executable, str(CTF), "status"], cwd=q, capture_output=True, text=True, timeout=60)
        check(r.returncode == 0 and "PROJ-9" in r.stdout, f"TS-56: tf status to lista zadań: {r.stdout}{r.stderr}")
        with tempfile.TemporaryDirectory() as e:
            r = run(Path(e), "list")
            check(r.returncode == 0 and "tf task start" in r.stdout, f"TS-57: brak zadań → podpowiedź, kod 0: {r.returncode} {r.stdout}")

    # zadanie cięcia zmiany pdi (krok E6): klucz <CHG>-<TSK>, pola `change` i `cut`, bez wiersza w INDEX.md
    with tempfile.TemporaryDirectory() as tmp:
        c = Path(tmp)
        r = run(c, "start", "CHG-12-TSK-57", "--title", "TSK-57: ponowienie płatności", "--change", "CHG-12", "--cut", "TSK-57")
        t = task(c, "CHG-12-TSK-57")
        check(r.returncode == 0 and t.get("change") == "CHG-12" and t.get("cut") == "TSK-57",
              f"TS-58: zadanie cięcia zapisuje zmianę i cięcie: {r.returncode} {r.stdout}{r.stderr} {t}")
        check(not (c / CHANGES / "INDEX.md").exists(),
              "TS-59: samo zadanie cięcia nie zakłada INDEX.md (PR-y cięć jednej zmiany nie mają o co się zderzyć)")
        run(c, "start", "PROJ-9", "--title", "Eksport sesji")
        before = (c / CHANGES / "INDEX.md").read_bytes()
        r = run(c, "start", "CHG-12-TSK-58", "--title", "TSK-58: brak podwójnego obciążenia", "--change", "CHG-12", "--cut", "TSK-58")
        run(c, "stage", "CHG-12-TSK-58", "specyfikacja")
        check(r.returncode == 0 and (c / CHANGES / "INDEX.md").read_bytes() == before
              and [ln for ln in index_rows(c) if "TSK-5" in ln] == [],
              f"TS-60: zapis zadania cięcia nie zmienia INDEX.md: {index_rows(c)}")
        r = run(c, "list")
        line = next((ln for ln in r.stdout.splitlines() if "CHG-12-TSK-57" in ln), "")
        check("cięcie TSK-57 zmiany CHG-12" in line, f"TS-61: lista pokazuje cięcie i jego zmianę: {r.stdout}")
        r = run(c, "list", "--json")
        try:
            rows = {x["key"]: x for x in json.loads(r.stdout)}
        except (ValueError, KeyError, TypeError):
            rows = {}
        check(rows.get("CHG-12-TSK-57", {}).get("change") == "CHG-12" and rows.get("CHG-12-TSK-57", {}).get("cut") == "TSK-57"
              and "change" not in rows.get("PROJ-9", {"change": 1}),
              f"TS-62: list --json podaje zmianę i cięcie tylko dla zadania cięcia: {r.stdout[:400]}")
        r = run(c, "status", "CHG-12-TSK-57")
        check("cięcie TSK-57 zmiany CHG-12" in r.stdout, f"TS-63: status pokazuje cięcie i jego zmianę: {r.stdout}")
        r = run(c, "start", "CHG-12-TSK-60", "--title", "x", "--cut", "TSK-60")
        r2 = run(c, "start", "CHG-12-TSK-61", "--title", "x", "--change", "CHG-12")
        check(r.returncode == 2 and r2.returncode == 2 and not task(c, "CHG-12-TSK-60") and not task(c, "CHG-12-TSK-61"),
              f"TS-64: --cut i --change tylko razem → kod 2: {r.returncode} {r2.returncode}")
        r = run(c, "start", "TSK-62", "--title", "x", "--change", "CHG-12", "--cut", "TSK-62")
        check(r.returncode == 2 and "CHG-12-TSK-62" in r.stdout and not task(c, "TSK-62"),
              f"TS-65: klucz zadania cięcia to <CHG>-<TSK> → kod 2 z podpowiedzią: {r.returncode} {r.stdout}")
        r = run(c, "start", "CHG-12-TSK-63", "--title", "x", "--change", "chg/12", "--cut", "TSK-63")
        check(r.returncode == 2, f"TS-66: zły kształt klucza zmiany → kod 2: {r.returncode} {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów stanu zadania")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
