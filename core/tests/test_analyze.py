#!/usr/bin/env python3
"""Tests of `.tf/factory/analyze.py` (tf init, tf analyze): the .tf/ skeleton, floor-0 modules, stable finding ids, a report with
merged checkboxes, the register, the cache after a commit. Plan: docs/plans/2026-11-08-krok-1-tf-analyze-rdzen.md."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())


def link_or_copy(src: Path, dst: Path) -> None:
    """A symbolic link, or a copy where the system refuses links (Windows without the developer mode: WinError 1314)."""
    try:
        dst.symlink_to(src, target_is_directory=src.is_dir())   # link-ok
    except OSError:
        if src.is_dir():
            shutil.copytree(src, dst, symlinks=True)
        else:
            shutil.copy2(src, dst)
ANALYZE = ROOT / ".tf" / "factory" / "analyze.py"
TF = ROOT / ".tf" / "factory" / "tf.py"

# Test module: reports every line with "TODO-SEC" in *.py files; counts runs in a file next to the repo.
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
            sev = "high" if "HIGH" in line else "low"
            print(json.dumps({"rule": "todo-sec", "title": "TODO-SEC marker", "file": rel, "line": i,
                              "snippet": line.strip(), "severity": sev, "confidence": 0.9,
                              "evidence": line.strip(), "basis": "test rule", "suggestion": "remove the marker"}))
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
    lines = [f"name: {name}", f"prefix: {prefix}", f"title: Module {name}", "description: test module",
             "version: 1.0.0", "tier0:", "  script: scripts/scan.py"]
    if applies:
        lines += ["applies_when:", "  files_any:", f"    - '{applies}'"]
    (d / "analyzer.yaml").write_text("\n".join(lines) + "\n")
    return d


def make_project(t: Path, mode="private") -> Path:
    repo = t / "proj"
    (repo / ".claude").mkdir(parents=True)
    (repo / ".claude" / "factory-manifest.json").write_text(json.dumps({"mode": mode}))
    (repo / ".tf" / "factory").mkdir(parents=True)   # the factory engine without pack modules — core tests do not depend on the set of packs
    for item in (ROOT / ".tf" / "factory").iterdir():
        if item.name != "analyzers":
            link_or_copy(item, repo / ".tf" / "factory" / item.name)
    sk = ROOT / ".claude" / "skills" / "core-grounding"
    if sk.is_dir():
        (repo / ".claude" / "skills").mkdir()
        link_or_copy(sk, repo / ".claude" / "skills" / "core-grounding")
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("x = 1\n# TODO-SEC HIGH token\n# TODO-SEC minor\n")
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
        print("✓ 0/0 analyze tests (no git — skipped)")
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
        check("reports" in r.stdout and "register" in r.stdout, f"A-1: init prints the .tf/ map: {r.stdout}")
        (tfd / "config" / "config.yaml").write_text("analyze:\n  top: 1\n")
        run("init", cwd=repo)
        check((tfd / "config" / "config.yaml").read_text() == "analyze:\n  top: 1\n", "A-1: drugi init nie nadpisuje config.yaml")
        (tfd / "config" / "config.yaml").write_text("analyze:\n  top: 10\n")

        # A-2 git: private → exclude, team → .gitignore
        excl = (repo / ".git" / "info" / "exclude").read_text() if (repo / ".git" / "info" / "exclude").exists() else ""
        check(".tf/" in excl, f"A-2: instalacja prywatna → .tf/ w .git/info/exclude: {excl!r}")
        shared = make_project(t / "s", mode="shared")
        run("init", cwd=shared)
        gi = (shared / ".gitignore").read_text()
        check(all(f".tf/{d}/" in gi for d in ("cache", "logs", "runs", "backup")) and ".tf/reports" not in gi,
              f"A-2: a team installation → .gitignore gets only the directories outside git: {gi!r}")

        # A-3 list
        r = run("list", cwd=repo)
        check(r.returncode == 0 and "no analysis modules" in r.stdout.lower(), f"A-3: list without modules says so explicitly: {r.stdout}")
        r = run("list", cwd=repo, env=env)
        check("sec" in r.stdout and "test module" in r.stdout, f"A-3: list shows the module with its description: {r.stdout}")

        # A-4 run: raport, json, rejestr; id stabilne; dedupe
        r = run("run", cwd=repo, env=env)
        rep = tfd / "reports" / "sec.md"
        data = json.loads((tfd / "reports" / "sec.json").read_text()) if (tfd / "reports" / "sec.json").exists() else {}
        findings = data.get("findings", [])
        check(r.returncode == 0 and rep.is_file() and len(findings) == 2,
              f"A-4: run creates a report and the full list (2 findings): {r.stdout}{r.stderr} {findings}")
        ids = sorted(f["id"] for f in findings)
        check(all(i.startswith("SEC-") and len(i) == 10 for i in ids), f"A-4: id w formacie SEC-<6 hex>: {ids}")
        reg = [json.loads(x) for x in (tfd / "register" / "items.jsonl").read_text().splitlines()] \
            if (tfd / "register" / "items.jsonl").exists() else []
        check(sorted(x["id"] for x in reg) == ids and all(x["status"] == "open" and x["kind"] == "finding" for x in reg),
              f"A-4: the register has an entry per finding, status open: {reg}")
        text = rep.read_text() if rep.is_file() else ""
        check(text.splitlines()[1].startswith("Verdict: NEEDS_FIX") if len(text.splitlines()) > 1 else False,
              f"A-4: druga linia raportu to werdykt: {text[:200]}")
        check("## Scope" in text and "floor 0" in text and "Analysis history" in text,
              f"A-4: the report has the scope (floors) and the history: {text}")
        # A-4f --fail-on: a CI gate — exit 1 when a finding is at least that severe (a: one high, one low)
        r = run("run", "--fail-on", "high", cwd=repo, env=env)
        check(r.returncode == 1 and "fail-on" in r.stdout + r.stderr and "SEC-" in r.stdout + r.stderr,
              f"A-4f: --fail-on high with a high finding → exit 1 naming the finding: {r.returncode} {r.stdout}{r.stderr}")
        r = run("run", "--fail-on", "critical", cwd=repo, env=env)
        check(r.returncode == 0, f"A-4f: --fail-on critical with nothing critical → exit 0: {r.returncode} {r.stdout}{r.stderr}")
        r = run("run", "--fail-on", "low", cwd=repo, env=env)
        check(r.returncode == 1, f"A-4f: --fail-on low counts every severity at or above low: {r.returncode} {r.stdout}")
        r = run("run", "--fail-on", "urgent", cwd=repo, env=env)
        check(r.returncode == 2, f"A-4f: an unknown severity is refused: {r.returncode} {r.stderr}")
        (repo / "src" / "a.py").write_text("\n\nx = 1\n# TODO-SEC HIGH token\n# TODO-SEC minor\n# TODO-SEC minor\n")
        commit(repo)
        run("run", cwd=repo, env=env)
        data = json.loads((tfd / "reports" / "sec.json").read_text())
        check(sorted(f["id"] for f in data["findings"]) == ids,
              f"A-4: a line shift does not change the id, a repeated line does not duplicate the finding: {data['findings']}")

        # A-5 ranking i top
        (tfd / "config" / "config.yaml").write_text("analyze:\n  top: 1\n")
        run("run", cwd=repo, env={**env, "TF_ANALYZE_NO_CACHE": "1"})
        text = rep.read_text()
        ust = text.split("## Findings", 1)[1].split("##", 1)[0] if "## Findings" in text else ""
        check("HIGH" in ust and "minor" not in ust, f"A-5: in the top 1 findings — the highest severity: {ust}")
        check(len(json.loads((tfd / "reports" / "sec.json").read_text())["findings"]) == 2,
              "A-5: the full list in .json despite top 1")
        (tfd / "config" / "config.yaml").write_text("analyze:\n  top: 10\n")

        # A-6 merging checkboxes
        hi = next(f["id"] for f in data["findings"] if "HIGH" in f["snippet"])
        lo = next(f["id"] for f in data["findings"] if "HIGH" not in f["snippet"])
        text = rep.read_text()
        text = text.replace(f"- [ ] {hi}", f"- [x] {hi}", 1)
        text = text.replace(f"- [ ] {lo}", f"- [ ] {lo}", 1)
        lines = text.splitlines()
        idx = next(i for i, l in enumerate(lines) if l.startswith(f"- [x] {hi}"))
        lines.insert(idx + 1, "  human note: fixed in PR 12")
        rep.write_text("\n".join(lines) + "\n")
        (repo / "src" / "a.py").write_text("x = 1\n# TODO-SEC HIGH token\n# TODO-SEC nowe\n")
        commit(repo)
        run("run", cwd=repo, env=env)
        text = rep.read_text()
        act = text.split("## Recommended actions", 1)[1] if "## Recommended actions" in text else ""
        check(f"- [x] {hi}" in act and "human note: fixed in PR 12" in act,
              f"A-6: ticked items and the human's note stay: {act}")
        check("still sees" in act, f"A-6: ticked but still visible → annotation: {act}")
        lo_line = next((l for l in act.splitlines() if lo in l), "")
        check("confirm it" in act.split(lo, 1)[1][:300] if lo in act else False,
              f"A-6: unticked but gone → 'confirm it': {act}")
        new_ids = [f["id"] for f in json.loads((tfd / "reports" / "sec.json").read_text())["findings"]]
        newid = next(i for i in new_ids if i not in (hi, lo))
        check(act.index(newid) > act.index(hi), f"A-6: the new finding at the end of the list: {act}")
        reg = {x["id"]: x for x in map(json.loads, (tfd / "register" / "items.jsonl").read_text().splitlines())}
        check(reg[hi]["status"] == "resolved", f"A-6: odhaczenie w raporcie → resolved w rejestrze: {reg[hi]}")
        check(newid in reg and reg[newid]["status"] == "open", f"A-6: nowe ustalenie w rejestrze: {reg}")
        # A-6b: ticks and history are read from the previous report; the Polish headings from before 14.x are not (the 19.0.0 migration rewrites them)
        import importlib.util
        spec = importlib.util.spec_from_file_location("ctf_analyze_t", ANALYZE)
        an = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(an)
        old = ("## Rekomendowane działania\n\n- [x] SEC-abc123 — x (a.py:1) — high\n  notatka\n\n"
               "## Historia analiz\n\n- 2026-11-01 · abc1234 · ustaleń: 1\n")
        new = old.replace("## Rekomendowane działania", "## Recommended actions").replace("## Historia analiz", "## Analysis history")
        items = an.parse_actions(new)
        check(len(items) == 1 and items[0]["checked"] and items[0]["notes"] == ["  notatka"]
              and an.history(new) == ["- 2026-11-01 · abc1234 · ustaleń: 1"] and an.parse_actions(old) == [] and an.history(old) == [],
              f"A-6b: the report headings are read in English only: {items} {an.history(new)}")

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
              f"A-7: --since examines the changed files and keeps the findings of the rest: {files} {r.stdout}{r.stderr}")

        # A-8 resilience and applies_when
        bad = t / "bad"
        make_module(bad, name="zly", prefix="ZLY", script="import sys\nprint('not json')\nsys.exit(3)\n")
        make_module(bad, name="ui", prefix="UI", applies="**/*.tsx")
        r = run("run", cwd=repo, env={**env, "TF_ANALYZERS_PATH": f"{mods}{os.pathsep}{bad}", "TF_ANALYZE_NO_CACHE": "1"})
        zly = (tfd / "reports" / "zly.md").read_text() if (tfd / "reports" / "zly.md").exists() else ""
        check(r.returncode == 1 and "module failed" in zly and (tfd / "reports" / "sec.md").is_file(),
              f"A-8: a module error in the report, the others work, code 1: {r.returncode} {zly} {r.stdout}")
        overview = (tfd / "reports" / "README.md").read_text() if (tfd / "reports" / "README.md").exists() else ""
        check("ui" in overview and "skipped" in overview, f"A-8: a module without matching files skipped with a reason: {overview}")
        r = run("run", "--only", "sec", cwd=repo, env={**env, "TF_ANALYZERS_PATH": f"{mods}{os.pathsep}{bad}"})
        check(r.returncode == 0, f"A-8: --only limits the modules: {r.stdout}{r.stderr}")

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
        # A-11 the module gate on a test set
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
        fixture(good, "clean", {"y.py": "y = 1\n"}, [])
        noisy = make_module(gm, name="szum", prefix="SZU")
        fixture(noisy, "clean", {"y.py": "# TODO-SEC minor\n"}, [])
        make_module(gm, name="bez", prefix="BEZ")
        genv = {"TF_ANALYZERS_PATH": str(gm), "T_COUNTER": str(counter)}
        r = run("gate", "--module", "dobry", cwd=repo, env=genv)
        check(r.returncode == 0 and r.stdout.startswith("Verdict: OK"),
              f"A-11: a module finding everything with no false positives passes the gate: {r.stdout}{r.stderr}")
        r = run("gate", "--module", "szum", cwd=repo, env=genv)
        check(r.returncode == 1 and "FAILED" in r.stdout and "false positives" in r.stdout,
              f"A-11: a false positive in a clean case → the gate does not pass: {r.stdout}{r.stderr}")
        r = run("gate", "--module", "bez", cwd=repo, env=genv)
        check(r.returncode == 1 and "fixtures" in r.stdout, f"A-11: a module without a set does not pass: {r.stdout}")
        # A-12 without --module: all modules, code 1 when any fails
        r = run("gate", cwd=repo, env=genv)
        check(r.returncode == 1 and "dobry" in r.stdout and "szum" in r.stdout and "bez" in r.stdout,
              f"A-12: gate without --module checks all: {r.stdout}")
        # A-13 a whole-repo module (incremental: false): --since does not narrow the scan and does not merge with the previous result
        full = t / "full"
        whole = ("import argparse, json\nap = argparse.ArgumentParser(); ap.add_argument('--root'); "
                 "ap.add_argument('--files', default='')\na = ap.parse_args()\n"
                 "print(json.dumps({'rule': 'args', 'file': 'x', 'line': 1, 'snippet': 'files=' + a.files, "
                 "'severity': 'low', 'confidence': 1}))\n")
        fm = make_module(full, name="calosc", prefix="CAL", script=whole)
        (fm / "analyzer.yaml").write_text((fm / "analyzer.yaml").read_text() + "incremental: false\n")
        fenv = {"TF_ANALYZERS_PATH": str(full)}
        run("run", cwd=repo, env=fenv)
        before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
        (repo / "src" / "a.py").write_text("x = 2\n")
        commit(repo)
        run("run", "--since", before, cwd=repo, env=fenv)
        snips = [f["snippet"] for f in json.loads((tfd / "reports" / "calosc.json").read_text())["findings"]]
        check(snips == ["files="], f"A-13: incremental: false — the script without --files, without merging with the previous one: {snips}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} analyze tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
