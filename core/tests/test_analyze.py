#!/usr/bin/env python3
"""Testy `.tf/factory/analyze.py` (tf init, tf analyze): szkielet .tf/, moduły piętra 0, stabilne id ustaleń, raport ze
scalaniem checkboxów, rejestr, cache po commicie. Plan: docs/plans/2026-11-08-krok-1-tf-analyze-rdzen.md."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
ANALYZE = ROOT / ".tf" / "factory" / "analyze.py"
TF = ROOT / ".tf" / "factory" / "tf.py"

# Moduł testowy: zgłasza każdą linię z "TODO-SEC" w plikach *.py; liczy uruchomienia w pliku obok repo.
SCRIPT = r'''import argparse, json, os
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--root"); ap.add_argument("--files", default="")
a = ap.parse_args()
root = Path(a.root)
counter = Path(os.environ["T_COUNTER"]); counter.write_text(str(int(counter.read_text() or 0) + 1) if counter.exists() else "1")
files = [f for f in a.files.split(",") if f] or sorted(str(p.relative_to(root)) for p in root.rglob("*.py"))
for rel in files:
    p = root / rel
    if not p.is_file():
        continue
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if "TODO-SEC" in line:
            sev = "wysoka" if "HIGH" in line else "niska"
            print(json.dumps({"rule": "todo-sec", "title": "Znacznik TODO-SEC", "file": rel, "line": i,
                              "snippet": line.strip(), "severity": sev, "confidence": 0.9,
                              "evidence": line.strip(), "basis": "reguła testowa", "suggestion": "usuń znacznik"}))
'''


def git(repo, *args):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false", *args],
                   cwd=repo, check=True, capture_output=True)


def run(*args, cwd, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run([sys.executable, str(ANALYZE), *args], cwd=cwd, capture_output=True, text=True,
                          timeout=120, env=e)


def make_module(base: Path, name="sec", prefix="SEC", applies=None, script=SCRIPT):
    d = base / name
    (d / "scripts").mkdir(parents=True)
    (d / "scripts" / "scan.py").write_text(script)
    lines = [f"name: {name}", f"prefix: {prefix}", f"title: Moduł {name}", "description: moduł testowy",
             "version: 1.0.0", "tier0:", "  script: scripts/scan.py"]
    if applies:
        lines += ["applies_when:", "  files_any:", f"    - '{applies}'"]
    (d / "analyzer.yaml").write_text("\n".join(lines) + "\n")
    return d


def make_project(t: Path, mode="private") -> Path:
    repo = t / "proj"
    (repo / ".claude").mkdir(parents=True)
    (repo / ".claude" / "factory-manifest.json").write_text(json.dumps({"mode": mode}))
    (repo / ".tf" / "factory").mkdir(parents=True)   # silnik fabryki bez modułów nakładek — testy rdzenia nie zależą od zestawu nakładek
    for item in (ROOT / ".tf" / "factory").iterdir():
        if item.name != "analyzers":
            (repo / ".tf" / "factory" / item.name).symlink_to(item)
    sk = ROOT / ".claude" / "skills" / "core-grounding"
    if sk.is_dir():
        (repo / ".claude" / "skills").mkdir()
        (repo / ".claude" / "skills" / "core-grounding").symlink_to(sk)
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("x = 1\n# TODO-SEC HIGH token\n# TODO-SEC drobne\n")
    (repo / "src" / "b.py").write_text("y = 2\n")
    git(repo, "init", "-q", "-b", "main")
    (repo / ".gitignore").write_text(".tf/\n.claude/\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    return repo


def commit(repo, msg="zmiana"):
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", msg)


def main() -> int:
    if not shutil.which("git"):
        print("✓ 0/0 testów analyze (brak git — pominięto)")
        return 0
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    if not ANALYZE.is_file():
        print(f"✗ brak {ANALYZE}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        mods = t / "mods"
        make_module(mods)
        counter = t / "count.txt"
        env = {"TF_ANALYZERS_PATH": str(mods), "T_COUNTER": str(counter)}

        # A-1 init: szkielet, README, idempotencja
        repo = make_project(t)
        r = run("init", cwd=repo)
        tfd = repo / ".tf"
        dirs = ["reports", "register", "wip", "cache", "logs", "runs", "backup"]
        check(r.returncode == 0 and (tfd / "config" / "config.yaml").is_file()
              and all((tfd / d / "README.md").is_file() for d in dirs),
              f"A-1: init tworzy .tf/ z config/config.yaml i README w katalogach: {r.stdout}{r.stderr}")
        check("reports" in r.stdout and "register" in r.stdout, f"A-1: init wypisuje mapę .tf/: {r.stdout}")
        (tfd / "config" / "config.yaml").write_text("analyze:\n  top: 1\n")
        run("init", cwd=repo)
        check((tfd / "config" / "config.yaml").read_text() == "analyze:\n  top: 1\n", "A-1: drugi init nie nadpisuje config.yaml")
        (tfd / "config" / "config.yaml").write_text("analyze:\n  top: 10\n")

        # A-2 git: prywatna → exclude, zespołowa → .gitignore
        excl = (repo / ".git" / "info" / "exclude").read_text() if (repo / ".git" / "info" / "exclude").exists() else ""
        check(".tf/" in excl, f"A-2: instalacja prywatna → .tf/ w .git/info/exclude: {excl!r}")
        shared = make_project(t / "s", mode="shared")
        run("init", cwd=shared)
        gi = (shared / ".gitignore").read_text()
        check(all(f".tf/{d}/" in gi for d in ("cache", "logs", "runs", "backup")) and ".tf/reports" not in gi,
              f"A-2: instalacja zespołowa → .gitignore dostaje tylko katalogi poza gitem: {gi!r}")

        # A-3 list
        r = run("list", cwd=repo)
        check(r.returncode == 0 and "brak modułów" in r.stdout.lower(), f"A-3: list bez modułów mówi to wprost: {r.stdout}")
        r = run("list", cwd=repo, env=env)
        check("sec" in r.stdout and "moduł testowy" in r.stdout, f"A-3: list pokazuje moduł z opisem: {r.stdout}")

        # A-4 run: raport, json, rejestr; id stabilne; dedupe
        r = run("run", cwd=repo, env=env)
        rep = tfd / "reports" / "sec.md"
        data = json.loads((tfd / "reports" / "sec.json").read_text()) if (tfd / "reports" / "sec.json").exists() else {}
        findings = data.get("findings", [])
        check(r.returncode == 0 and rep.is_file() and len(findings) == 2,
              f"A-4: run tworzy raport i pełną listę (2 ustalenia): {r.stdout}{r.stderr} {findings}")
        ids = sorted(f["id"] for f in findings)
        check(all(i.startswith("SEC-") and len(i) == 10 for i in ids), f"A-4: id w formacie SEC-<6 hex>: {ids}")
        reg = [json.loads(x) for x in (tfd / "register" / "items.jsonl").read_text().splitlines()] \
            if (tfd / "register" / "items.jsonl").exists() else []
        check(sorted(x["id"] for x in reg) == ids and all(x["status"] == "otwarte" and x["kind"] == "finding" for x in reg),
              f"A-4: rejestr ma pozycję na ustalenie, status otwarte: {reg}")
        text = rep.read_text() if rep.is_file() else ""
        check(text.splitlines()[1].startswith("Werdykt: DO POPRAWY") if len(text.splitlines()) > 1 else False,
              f"A-4: druga linia raportu to werdykt: {text[:200]}")
        check("## Zakres" in text and "piętro 0" in text and "Historia analiz" in text,
              f"A-4: raport ma zakres (piętra) i historię: {text}")
        (repo / "src" / "a.py").write_text("\n\nx = 1\n# TODO-SEC HIGH token\n# TODO-SEC drobne\n# TODO-SEC drobne\n")
        commit(repo)
        run("run", cwd=repo, env=env)
        data = json.loads((tfd / "reports" / "sec.json").read_text())
        check(sorted(f["id"] for f in data["findings"]) == ids,
              f"A-4: przesunięcie linii nie zmienia id, powtórzona linia nie dubluje ustalenia: {data['findings']}")

        # A-5 ranking i top
        (tfd / "config" / "config.yaml").write_text("analyze:\n  top: 1\n")
        run("run", cwd=repo, env={**env, "TF_ANALYZE_NO_CACHE": "1"})
        text = rep.read_text()
        ust = text.split("## Ustalenia", 1)[1].split("##", 1)[0] if "## Ustalenia" in text else ""
        check("HIGH" in ust and "drobne" not in ust, f"A-5: w ustaleniach top 1 — najwyższa waga: {ust}")
        check(len(json.loads((tfd / "reports" / "sec.json").read_text())["findings"]) == 2,
              "A-5: pełna lista w .json mimo top 1")
        (tfd / "config" / "config.yaml").write_text("analyze:\n  top: 10\n")

        # A-6 scalanie checkboxów
        hi = next(f["id"] for f in data["findings"] if "HIGH" in f["snippet"])
        lo = next(f["id"] for f in data["findings"] if "HIGH" not in f["snippet"])
        text = rep.read_text()
        text = text.replace(f"- [ ] {hi}", f"- [x] {hi}", 1)
        text = text.replace(f"- [ ] {lo}", f"- [ ] {lo}", 1)
        lines = text.splitlines()
        idx = next(i for i, l in enumerate(lines) if l.startswith(f"- [x] {hi}"))
        lines.insert(idx + 1, "  notatka człowieka: naprawione w PR 12")
        rep.write_text("\n".join(lines) + "\n")
        (repo / "src" / "a.py").write_text("x = 1\n# TODO-SEC HIGH token\n# TODO-SEC nowe\n")
        commit(repo)
        run("run", cwd=repo, env=env)
        text = rep.read_text()
        act = text.split("## Rekomendowane działania", 1)[1] if "## Rekomendowane działania" in text else ""
        check(f"- [x] {hi}" in act and "notatka człowieka: naprawione w PR 12" in act,
              f"A-6: odhaczone i notatka człowieka zostają: {act}")
        check("wciąż widzi" in act, f"A-6: odhaczone, a nadal widoczne → adnotacja: {act}")
        lo_line = next((l for l in act.splitlines() if lo in l), "")
        check("potwierdź" in act.split(lo, 1)[1][:300] if lo in act else False,
              f"A-6: nieodhaczone, a zniknęło → „potwierdź”: {act}")
        new_ids = [f["id"] for f in json.loads((tfd / "reports" / "sec.json").read_text())["findings"]]
        newid = next(i for i in new_ids if i not in (hi, lo))
        check(act.index(newid) > act.index(hi), f"A-6: nowe ustalenie na końcu listy: {act}")
        reg = {x["id"]: x for x in map(json.loads, (tfd / "register" / "items.jsonl").read_text().splitlines())}
        check(reg[hi]["status"] == "rozstrzygnięte", f"A-6: odhaczenie w raporcie → rozstrzygnięte w rejestrze: {reg[hi]}")
        check(newid in reg and reg[newid]["status"] == "otwarte", f"A-6: nowe ustalenie w rejestrze: {reg}")

        # A-7 cache i --since
        counter.write_text("0")
        run("run", cwd=repo, env=env)
        check(counter.read_text() == "0", f"A-7: ten sam commit, czyste drzewo → wynik z cache: {counter.read_text()}")
        base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
        (repo / "src" / "b.py").write_text("y = 2\n# TODO-SEC w b\n")
        commit(repo)
        r = run("run", "--since", base, cwd=repo, env=env)
        data = json.loads((tfd / "reports" / "sec.json").read_text())
        files = sorted({f["file"] for f in data["findings"]})
        check(r.returncode == 0 and files == ["src/a.py", "src/b.py"],
              f"A-7: --since bada zmienione pliki i zachowuje ustalenia pozostałych: {files} {r.stdout}{r.stderr}")

        # A-8 odporność i applies_when
        bad = t / "bad"
        make_module(bad, name="zly", prefix="ZLY", script="import sys\nprint('nie json')\nsys.exit(3)\n")
        make_module(bad, name="ui", prefix="UI", applies="**/*.tsx")
        r = run("run", cwd=repo, env={**env, "TF_ANALYZERS_PATH": f"{mods}{os.pathsep}{bad}", "TF_ANALYZE_NO_CACHE": "1"})
        zly = (tfd / "reports" / "zly.md").read_text() if (tfd / "reports" / "zly.md").exists() else ""
        check(r.returncode == 1 and "nie powiódł" in zly and (tfd / "reports" / "sec.md").is_file(),
              f"A-8: błąd modułu w raporcie, pozostałe działają, kod 1: {r.returncode} {zly} {r.stdout}")
        overview = (tfd / "reports" / "README.md").read_text() if (tfd / "reports" / "README.md").exists() else ""
        check("ui" in overview and "pominięty" in overview, f"A-8: moduł bez pasujących plików pominięty z powodem: {overview}")
        r = run("run", "--only", "sec", cwd=repo, env={**env, "TF_ANALYZERS_PATH": f"{mods}{os.pathsep}{bad}"})
        check(r.returncode == 0, f"A-8: --only ogranicza moduły: {r.stdout}{r.stderr}")

        # A-9 tf.py
        r = subprocess.run([sys.executable, str(TF), "analyze", "--list"], cwd=repo, capture_output=True, text=True,
                           env=dict(os.environ, **env), timeout=120)
        check(r.returncode == 0 and "sec" in r.stdout, f"A-9: tf analyze --list → analyze.py: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(TF), "init"], cwd=repo, capture_output=True, text=True, timeout=120)
        check(r.returncode == 0 and "reports" in r.stdout, f"A-9: tf init → analyze.py init: {r.stdout}{r.stderr}")

        # A-10 claims_check
        cc = ROOT / ".claude" / "skills" / "core-grounding" / "scripts" / "claims_check.py"
        if cc.is_file():
            r = subprocess.run([sys.executable, str(cc), str(rep)], capture_output=True, text=True)
            check(r.returncode == 0, f"A-10: raport przechodzi claims_check: {r.stdout}")
        # A-11 bramka modułu na zestawie testowym
        def fixture(mod: Path, case: str, files: dict, expected: list):
            d = mod / "fixtures" / case
            for rel, text in files.items():
                (d / "repo" / rel).parent.mkdir(parents=True, exist_ok=True)
                (d / "repo" / rel).write_text(text)
            (d / "expected.json").write_text(json.dumps(expected))
        gm = t / "gmods"
        good = make_module(gm, name="dobry", prefix="DOB")
        (good / "analyzer.yaml").write_text((good / "analyzer.yaml").read_text()
                                            + "gate:\n  min_recall: 1.0\n  max_false_positives: 0\n")
        fixture(good, "zle", {"x.py": "# TODO-SEC HIGH\n"}, [{"rule": "todo-sec", "file": "x.py"}])
        fixture(good, "czyste", {"y.py": "y = 1\n"}, [])
        noisy = make_module(gm, name="szum", prefix="SZU")
        fixture(noisy, "czyste", {"y.py": "# TODO-SEC drobne\n"}, [])
        make_module(gm, name="bez", prefix="BEZ")
        genv = {"TF_ANALYZERS_PATH": str(gm), "T_COUNTER": str(counter)}
        r = run("gate", "--module", "dobry", cwd=repo, env=genv)
        check(r.returncode == 0 and r.stdout.startswith("Werdykt: OK"),
              f"A-11: moduł znajdujący wszystko bez fałszywych trafień przechodzi bramkę: {r.stdout}{r.stderr}")
        r = run("gate", "--module", "szum", cwd=repo, env=genv)
        check(r.returncode == 1 and "NIE PRZESZŁA" in r.stdout and "fałszyw" in r.stdout,
              f"A-11: fałszywe trafienie w przypadku czystym → bramka nie przechodzi: {r.stdout}{r.stderr}")
        r = run("gate", "--module", "bez", cwd=repo, env=genv)
        check(r.returncode == 1 and "fixtures" in r.stdout, f"A-11: moduł bez zestawu nie przechodzi: {r.stdout}")
        # A-12 bez --module: wszystkie moduły, kod 1, gdy któryś nie przeszedł
        r = run("gate", cwd=repo, env=genv)
        check(r.returncode == 1 and "dobry" in r.stdout and "szum" in r.stdout and "bez" in r.stdout,
              f"A-12: gate bez --module sprawdza wszystkie: {r.stdout}")
        # A-13 moduł całościowy (incremental: false): --since nie zawęża skanu i nie łączy z poprzednim wynikiem
        full = t / "full"
        whole = ("import argparse, json\nap = argparse.ArgumentParser(); ap.add_argument('--root'); "
                 "ap.add_argument('--files', default='')\na = ap.parse_args()\n"
                 "print(json.dumps({'rule': 'args', 'file': 'x', 'line': 1, 'snippet': 'files=' + a.files, "
                 "'severity': 'niska', 'confidence': 1}))\n")
        fm = make_module(full, name="calosc", prefix="CAL", script=whole)
        (fm / "analyzer.yaml").write_text((fm / "analyzer.yaml").read_text() + "incremental: false\n")
        fenv = {"TF_ANALYZERS_PATH": str(full)}
        run("run", cwd=repo, env=fenv)
        before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
        (repo / "src" / "a.py").write_text("x = 2\n")
        commit(repo)
        run("run", "--since", before, cwd=repo, env=fenv)
        snips = [f["snippet"] for f in json.loads((tfd / "reports" / "calosc.json").read_text())["findings"]]
        check(snips == ["files="], f"A-13: incremental: false — skrypt bez --files, bez łączenia z poprzednim: {snips}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów analyze")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
