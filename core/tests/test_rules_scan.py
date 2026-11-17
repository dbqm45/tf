#!/usr/bin/env python3
"""Testy skanera reguł deklaratywnych `.tf/factory/rules_scan.py` i modułu `tf analyze` z `tier0.rules`: standardy
firmy sprawdzane bez modelu (wzorzec zakazany w linii, wzorzec wymagany w nagłówku pliku, wzorce ścieżek, błędne
reguły) oraz bramka modułu na fixtures. python3 tests/test_rules_scan.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
SCAN = ROOT / ".tf" / "factory" / "rules_scan.py"
ANALYZE = ROOT / ".tf" / "factory" / "analyze.py"

RULES = r"""rules:
  - id: no-print
    title: print zamiast loggera firmowego
    files: ["**/*.py"]
    exclude: ["tests/**"]
    forbid: '^\s*print\('
    severity: medium
    suggestion: użyj acme.log
  - id: license-header
    title: brak nagłówka licencji
    files: ["src/**/*.py"]
    require: 'Copyright ACME'
    head: 3
    severity: low
"""


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def scan(rules: Path, root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCAN), "--rules", str(rules), "--root", str(root), *extra],
                          capture_output=True, text=True, timeout=60)


def found(r: subprocess.CompletedProcess) -> list[tuple[str, str, int]]:
    return sorted((f["rule"], f["file"], f["line"]) for f in map(json.loads, filter(None, r.stdout.splitlines())))


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        rules = base / "rules.yaml"
        write(rules, RULES)
        repo = base / "repo"
        write(repo / "src" / "app.py", "# Copyright ACME\nimport x\nprint('a')\n    print('b')\n")
        write(repo / "src" / "lib" / "util.py", "import y\n\n\n# Copyright ACME\n")
        write(repo / "tests" / "test_app.py", "print('ok w testach')\n")
        write(repo / "node_modules" / "p" / "a.py", "print('zależność')\n")
        write(repo / ".tf" / "factory" / "x.py", "print('fabryka')\n")
        r = scan(rules, repo)
        got = found(r)
        check(r.returncode == 0 and got == [("license-header", "src/lib/util.py", 1), ("no-print", "src/app.py", 3),
                                            ("no-print", "src/app.py", 4)],
              f"RS-1: forbid w linii, require w pierwszych `head` liniach, exclude, bez zależności i plików fabryki: "
              f"{got} {r.stderr}")
        first = json.loads(r.stdout.splitlines()[0]) if r.stdout.strip() else {}
        check({"rule", "title", "file", "line", "snippet", "severity", "confidence", "evidence", "basis",
               "suggestion"} <= set(first) and first.get("severity") in ("low", "medium"),
              f"RS-2: ustalenie w kontrakcie tf analyze: {first}")
        r = scan(rules, repo, "--files", "src/app.py,tests/test_app.py")
        check(found(r) == [("no-print", "src/app.py", 3), ("no-print", "src/app.py", 4)],
              f"RS-3: --files ogranicza skan (exclude nadal działa): {found(r)}")
        for name, body in (("bez-wzorca", "rules:\n  - {id: x, title: X}\n"),
                           ("zly-wzorzec", "rules:\n  - {id: x, title: X, forbid: '(['}\n"),
                           ("zle-id", "rules:\n  - {id: 'Złe ID', title: X, forbid: a}\n"),
                           ("oba", "rules:\n  - {id: x, title: X, forbid: a, require: b}\n"),
                           ("zla-waga", "rules:\n  - {id: x, title: X, forbid: a, severity: huge}\n")):
            bad = base / f"{name}.yaml"
            write(bad, body)
            r = scan(bad, repo)
            check(r.returncode == 2 and "rule" in r.stderr, f"RS-4 {name}: błędna reguła → kod 2 z opisem: {r.returncode} {r.stderr}")

        # moduł tf analyze z tier0.rules: uruchomienie i bramka na fixtures
        mods = base / "mods"
        mod = mods / "firma"
        write(mod / "analyzer.yaml", "name: firma\nprefix: ACME\ntitle: Standardy ACME\ndescription: test\nversion: 0.1.0\n"
                                     "applies_when: {files_any: ['**/*.py']}\ntier0: {rules: rules.yaml}\n"
                                     "gate: {min_recall: 1.0, max_false_positives: 0}\n")
        write(mod / "rules.yaml", RULES)
        write(mod / "fixtures" / "planted" / "repo" / "src" / "a.py", "print('x')\n")
        write(mod / "fixtures" / "planted" / "expected.json", json.dumps([
            {"rule": "no-print", "file": "src/a.py"}, {"rule": "license-header", "file": "src/a.py"}]))
        write(mod / "fixtures" / "clean" / "repo" / "src" / "a.py", "# Copyright ACME\nimport x\n")
        write(mod / "fixtures" / "clean" / "expected.json", "[]")
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(g + ["add", "-A"], cwd=repo, check=True)
        subprocess.run(g + ["commit", "-qm", "init"], cwd=repo, check=True)
        env = {**os.environ, "TF_ANALYZERS_PATH": str(mods), "TF_ANALYZE_NO_CACHE": "1"}
        r = subprocess.run([sys.executable, str(ANALYZE), "run", "--only", "firma"], cwd=repo, env=env,
                           capture_output=True, text=True, timeout=120)
        report = repo / ".tf" / "reports" / "firma.json"
        data = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else {}
        check(r.returncode == 0 and len(data.get("findings", [])) == 3
              and all(f["id"].startswith("ACME-") for f in data["findings"]),
              f"RS-5: tf analyze uruchamia moduł z tier0.rules skanerem rdzenia: {r.stdout[-500:]}{r.stderr[-500:]}")
        r = subprocess.run([sys.executable, str(ANALYZE), "gate", "--module", "firma"], cwd=repo, env=env,
                           capture_output=True, text=True, timeout=120)
        check(r.returncode == 0, f"RS-6: bramka modułu z tier0.rules na fixtures: {r.stdout[-600:]}{r.stderr[-300:]}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów rules_scan")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
