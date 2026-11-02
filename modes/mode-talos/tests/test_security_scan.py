#!/usr/bin/env python3
"""Testy skanu bezpieczeństwa kawałka Talosa (tryb mode-talos, scripts/security_scan.py): skan tylko zmienionych
plików, audyt zależności tylko przy zmianie manifestu albo lockfile'a, SARIF w katalogu wyniku, brak skanera to FAIL,
werdykt jak SEC-001 w ci_for_sdlc, ścieżka FAIL → STOP pętli kawałka, karencja wersji (N10).
Skanery są podstawione (TALOS_SCAN_PATH). python3 .claude/tests/test_security_scan.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "talos-story-run" / "scripts" / "security_scan.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL).is_file()), None)
SCRIPT = ROOT / REL if ROOT else None

# Podstawiony semgrep: zapisuje argv do $FAKE_LOG; wynik przy każdej linii z „SQLI” w skanowanych plikach (reguła
# bez poziomu w wyniku, domyślnie warning, tag CWE-89 — tak jak prawdziwy semgrep 1.x); kod wyjścia z $FAKE_EXIT.
FAKE_SEMGREP = r'''
import json, os, sys
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(["semgrep", *args]) + "\n")
out = args[args.index("--output") + 1]
skip = {args[i + 1] for i, a in enumerate(args) if a in ("--config", "--output")}
targets = [a for a in args[1:] if not a.startswith("-") and a not in skip]
results = []
for t in targets:
    for n, line in enumerate(open(t, encoding="utf-8").read().splitlines(), 1):
        if "SQLI" in line:
            results.append({"ruleId": "fake.sql-injection", "ruleIndex": 0, "message": {"text": "SQL z danych użytkownika"},
                            "locations": [{"physicalLocation": {"artifactLocation": {"uri": t.removeprefix("./"), "uriBaseId": "%SRCROOT%"},
                                                                "region": {"startLine": n}}}]})
rules = [{"id": "fake.sql-injection", "defaultConfiguration": {"level": "warning"},
          "properties": {"tags": ["CWE-89: Improper Neutralization of Special Elements used in an SQL Command", "security"]}}]
code = int(os.environ.get("FAKE_EXIT", "0"))
if code == 0:
    json.dump({"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Semgrep OSS", "rules": rules}}, "results": results}]}, open(out, "w"))
else:
    print("invalid configuration", file=sys.stderr)
sys.exit(code)
'''
FAKE_NPM = r'''
import json, os, sys
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(["npm", *sys.argv[1:], os.getcwd()]) + "\n")
print(json.dumps({"auditReportVersion": 2, "vulnerabilities": {"braces": {"name": "braces", "nodes": ["node_modules/braces"], "via": [
    {"source": 1, "name": "braces", "title": "Uncontrolled resource consumption in braces", "severity": "high",
     "url": "https://github.com/advisories/GHSA-grv7-fg5c-xmjg", "cwe": ["CWE-400"], "range": "<3.0.3"}]}}}))
sys.exit(1)
'''
FAKE_PIP_AUDIT = r'''
import json, os, sys
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(["pip-audit", *args]) + "\n")
out = args[args.index("--output") + 1] if "--output" in args else args[args.index("-o") + 1]
json.dump({"dependencies": [{"name": "jinja2", "version": "3.1.2", "vulns": [
    {"id": "GHSA-h5c8-rqwp-cp95", "fix_versions": ["3.1.3"], "aliases": ["CVE-2024-22195"], "description": "XSS in xmlattr"}]}],
    "fixes": []}, open(out, "w"))
sys.exit(1)
'''


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t"})


def write(root: Path, rel: str, text: str = "x = 1\n") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def fake_bin(d: Path, tools: dict) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    for name, body in tools.items():
        p = d / name
        p.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
        p.chmod(0o755)
    return d


def log_of(path: Path) -> list:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def sarif(results, rules=()):
    return {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "t", "rules": list(rules)}}, "results": results}]}


def res(rule, level=None, uri="app.py", line=3, **props):
    r = {"ruleId": rule, "message": {"text": rule},
         "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri}, "region": {"startLine": line}}}]}
    if level:
        r["level"] = level
    if props:
        r["properties"] = props
    return r


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if SCRIPT is None:
        print(f"✗ brak skryptu {REL}")
        return 1
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = tmp / "log.jsonl"
        full = fake_bin(tmp / "bin", {"semgrep": FAKE_SEMGREP, "npm": FAKE_NPM, "pip-audit": FAKE_PIP_AUDIT})
        empty = fake_bin(tmp / "empty", {})
        env = {**os.environ, "TALOS_SCAN_PATH": str(full), "FAKE_LOG": str(log)}

        def run(*args, cwd, **extra):
            return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True,
                                  timeout=60, env={**env, **extra})

        repo = tmp / "repo"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        write(repo, "old.py")
        write(repo, "package.json", '{"name": "p"}\n')
        write(repo, "package-lock.json", '{\n  "packages": {\n    "": {},\n    "node_modules/braces": {}\n  }\n}\n')
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "init")

        # S-1: skan obejmuje tylko zmiany kawałka (zmienione i nowe pliki), nie całe repo
        write(repo, "old.py", "x = 2\n")
        write(repo, "src/new.py", "y = 1\n")
        out = repo / ".claude" / "runs" / "r1" / "security"
        r = run("scan", "--out", str(out), cwd=repo)
        calls = log_of(log)
        sem = [c for c in calls if c[0] == "semgrep"]
        targets = {a.removeprefix("./") for a in (sem[0][1:] if sem else []) if a.endswith(".py")}
        check(r.returncode == 0 and len(sem) == 1, f"S-1: semgrep raz, PASS: {r.returncode} {r.stdout} {r.stderr}")
        check(targets == {"old.py", "src/new.py"}, f"S-2: tylko zmienione pliki: {targets}")
        check(sem and "--metrics=off" in sem[0] and "--sarif" in sem[0] and "p/owasp-top-ten" in sem[0],
              f"S-3: reguły OWASP, SARIF, bez metryk: {sem[:1]}")
        check((out / "semgrep.sarif").is_file() and (out / "verdict.json").is_file(), "S-4: SARIF i werdykt w katalogu wyniku")
        check(not [c for c in calls if c[0] in ("npm", "pip-audit")], f"S-5: bez zmiany manifestu nie ma audytu: {calls}")
        check("SKAN: PASS" in r.stdout, f"S-6: linia werdyktu PASS: {r.stdout}")

        # S-7: własne reguły produktu (.semgrep.yml) dochodzą do OWASP
        write(repo, ".semgrep.yml", "rules: []\n")
        log.unlink(missing_ok=True)
        run("scan", "--out", str(out), cwd=repo)
        sem = [c for c in log_of(log) if c[0] == "semgrep"]
        check(sem and ".semgrep.yml" in sem[0], f"S-7: .semgrep.yml produktu w konfiguracji: {sem[:1]}")
        (repo / ".semgrep.yml").unlink()

        # S-8: zmiana lockfile'a npm uruchamia npm audit; wynik jako SARIF z linią w lockfile'u
        write(repo, "package-lock.json", '{\n  "packages": {\n    "": {},\n    "node_modules/braces": {"version": "3.0.2"}\n  }\n}\n')
        log.unlink(missing_ok=True)
        r = run("scan", "--out", str(out), cwd=repo)
        npm = [c for c in log_of(log) if c[0] == "npm"]
        check(npm and npm[0][1:3] == ["audit", "--json"], f"S-8: npm audit --json: {npm}")
        audit = json.loads((out / "npm-audit.sarif").read_text()) if (out / "npm-audit.sarif").is_file() else {}
        ares = (audit.get("runs") or [{}])[0].get("results") or [{}]
        loc = ares[0].get("locations", [{}])[0].get("physicalLocation", {})
        check(ares[0].get("ruleId") == "npm-audit/GHSA-grv7-fg5c-xmjg" and ares[0].get("level") == "error"
              and loc.get("artifactLocation", {}).get("uri") == "package-lock.json" and loc.get("region", {}).get("startLine") == 4,
              f"S-9: npm audit jako SARIF (high → error, linia w lockfile'u): {ares}")
        check(r.returncode == 1 and "npm-audit/GHSA-grv7-fg5c-xmjg" in r.stdout and "package-lock.json:4" in r.stdout,
              f"S-10: podatność high blokuje, z regułą i miejscem: {r.returncode} {r.stdout}")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "lock")

        # S-11: zmiana requirements*.txt uruchamia pip-audit; znana podatność bez ważności blokuje (A06:2021)
        write(repo, "requirements.txt", "jinja2==3.1.2\n")
        log.unlink(missing_ok=True)
        r = run("scan", "--out", str(out), cwd=repo)
        pa = [c for c in log_of(log) if c[0] == "pip-audit"]
        check(pa and "-r" in pa[0] and "requirements.txt" in pa[0] and "json" in pa[0], f"S-11: pip-audit -r … -f json: {pa}")
        check((out / "pip-audit.sarif").is_file() and r.returncode == 1 and "GHSA-h5c8-rqwp-cp95" in r.stdout,
              f"S-12: pip-audit jako SARIF, podatność blokuje: {r.returncode} {r.stdout}")
        check(not (out / "npm-audit.sarif").exists(), "S-13: stary SARIF audytu npm usunięty z katalogu wyniku")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "req")

        # S-14: --base: zmiany od gałęzi bazowej (CI na PR), także już zacommitowane
        git(repo, "checkout", "-qb", "feat/x")
        write(repo, "src/committed.py")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "c")
        log.unlink(missing_ok=True)
        r = run("scan", "--base", "main", "--out", str(out), cwd=repo)
        sem = [c for c in log_of(log) if c[0] == "semgrep"]
        targets = {a.removeprefix("./") for a in (sem[0][1:] if sem else []) if a.endswith(".py")}
        check(r.returncode == 0 and targets == {"src/committed.py"}, f"S-14: --base bierze commity gałęzi: {targets} {r.stderr}")

        # S-15: brak zmian → PASS bez uruchamiania skanera, pusty SARIF (CI nie zgłasza braku skanu)
        git(repo, "checkout", "-q", "main")
        log.unlink(missing_ok=True)
        r = run("scan", "--out", str(out), cwd=repo)
        empty_sarif = json.loads((out / "semgrep.sarif").read_text()) if (out / "semgrep.sarif").is_file() else {}
        check(r.returncode == 0 and not log_of(log) and empty_sarif.get("runs", [{}])[0].get("results") == [],
              f"S-15: brak zmian: {r.returncode} {log_of(log)} {empty_sarif}")

        # S-16: brak skanera → FAIL z poleceniem instalacji, nigdy cichy PASS
        write(repo, "a.py")
        r = run("scan", "--out", str(out), cwd=repo, TALOS_SCAN_PATH=str(empty))
        check(r.returncode == 1 and "semgrep" in r.stdout and "pipx install semgrep" in r.stdout and "SKAN: FAIL" in r.stdout,
              f"S-16: brak semgrep: {r.returncode} {r.stdout} {r.stderr}")
        write(repo, "requirements.txt", "jinja2==3.1.4\n")
        r = run("scan", "--out", str(out), cwd=repo, TALOS_SCAN_PATH=str(fake_bin(tmp / "semonly", {"semgrep": FAKE_SEMGREP})))
        check(r.returncode == 1 and "pip install pip-audit" in r.stdout, f"S-17: brak pip-audit przy zmianie manifestu: {r.stdout}")
        git(repo, "checkout", "-q", "--", "requirements.txt")

        # S-18: błąd skanera (kod ≠ 0) → FAIL, nie PASS
        r = run("scan", "--out", str(out), cwd=repo, FAKE_EXIT="2")
        check(r.returncode == 1 and "SKAN: FAIL" in r.stdout and "invalid configuration" in r.stdout,
              f"S-18: błąd semgrep to FAIL: {r.returncode} {r.stdout}")
        (repo / "a.py").unlink()

        # V: reguła werdyktu = SEC-001 ci_for_sdlc (error albo warning z CWE z OWASP Top 10 2021/2025)
        vdir = tmp / "v"
        vdir.mkdir()
        cases = sarif([
            res("r.error", "error", line=1),
            res("r.warn-owasp", "warning", line=2, tags=["CWE-89: SQL Injection"]),
            res("r.warn-other", "warning", line=3, tags=["CWE-1333"]),
            res("r.note", "note", line=4, tags=["CWE-89"]),
            res("r.none", "none", line=5),
            res("r.default", None, line=6),
            res("r.result-cwe", "warning", line=7, cwe="external/cwe/cwe-079"),
            res("r.warn-2025", "warning", line=8, tags=["CWE-476"]),
        ], rules=[{"id": "r.default", "defaultConfiguration": {"level": "warning"}, "properties": {"tags": ["CWE-22"]}}])
        (vdir / "a.sarif").write_text(json.dumps(cases))
        r = run("verdict", str(vdir / "a.sarif"), "--json", cwd=repo)
        v = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        blocking = {b.get("rule") for b in v.get("blocking", [])}
        other = {b.get("rule") for b in v.get("other", [])}
        check(r.returncode == 1 and v.get("status") == "FAIL", f"V-1: blokujące ustalenia → FAIL: {r.returncode} {r.stdout[:300]}")
        check(blocking == {"r.error", "r.warn-owasp", "r.default", "r.result-cwe", "r.warn-2025"},
              f"V-2: blokujące wg SEC-001: {blocking}")
        check(other == {"r.warn-other", "r.note"}, f"V-3: poniżej progu (do raportu), level none pominięty: {other}")
        b0 = next((b for b in v.get("blocking", []) if b.get("rule") == "r.warn-owasp"), {})
        check(b0.get("file") == "app.py" and b0.get("line") == 2 and 89 in b0.get("cwe", []), f"V-4: reguła, plik, linia, CWE: {b0}")
        (vdir / "b.sarif").write_text(json.dumps(sarif([res("r.warn-other", "warning", tags=["CWE-1333"])])))
        r = run("verdict", str(vdir / "b.sarif"), cwd=repo)
        check(r.returncode == 0 and "SKAN: PASS" in r.stdout and "r.warn-other" in r.stdout,
              f"V-5: tylko poniżej progu → PASS z listą do raportu: {r.returncode} {r.stdout}")
        (vdir / "bad.sarif").write_text("nie json")
        r = run("verdict", str(vdir / "bad.sarif"), cwd=repo)
        check(r.returncode == 1 and "Traceback" not in r.stderr, f"V-6: zły SARIF to FAIL, nie cichy PASS: {r.returncode} {r.stderr}")
        r = run("verdict", cwd=repo)
        check(r.returncode == 2, f"V-7: zły wywołanie → 2: {r.returncode}")

        # L: pętla kawałka — próba 1 z SQL injection → FAIL z ustaleniem do następnej próby; próba 2 nadal → STOP;
        # po poprawce → PASS i raport ustaleń poniżej progu w katalogu przebiegu
        write(repo, "src/orders.py", 'q = "SELECT * FROM o WHERE id=%s" % user_id  # SQLI\n')
        out = repo / ".claude" / "runs" / "r2" / "security"
        r = run("scan", "--out", str(out), "--slice", "K2", "--attempt", "1", cwd=repo)
        fb = (out / "feedback.md").read_text(encoding="utf-8") if (out / "feedback.md").is_file() else ""
        check(r.returncode == 1 and "BRAMKA K2: FAIL" in r.stdout and "próba 1/2" in r.stdout
              and "fake.sql-injection src/orders.py:1" in r.stdout, f"L-1: FAIL próby 1 z regułą i miejscem: {r.stdout}")
        check("fake.sql-injection" in fb and "src/orders.py:1" in fb, f"L-2: ustalenie zapisane dla następnej próby: {fb}")
        check("STOP" not in r.stdout, f"L-3: po próbie 1 jeszcze bez STOP: {r.stdout}")
        r = run("scan", "--out", str(out), "--slice", "K2", "--attempt", "2", cwd=repo)
        check(r.returncode == 1 and "STOP — K2" in r.stdout and "Powód:" in r.stdout and "src/orders.py:1" in r.stdout,
              f"L-4: FAIL próby 2 → blok STOP: {r.stdout}")
        write(repo, "src/orders.py", 'q = db.execute("SELECT * FROM o WHERE id=?", (user_id,))\n')
        r = run("scan", "--out", str(out), "--slice", "K2", "--attempt", "2", cwd=repo)
        check(r.returncode == 0 and "BRAMKA K2: PASS" in r.stdout and "STOP" not in r.stdout,
              f"L-5: po poprawce PASS: {r.returncode} {r.stdout}")
        summary = (out / "summary.md").read_text(encoding="utf-8") if (out / "summary.md").is_file() else ""
        check(summary.startswith("## Bezpieczeństwo") and "PASS" in summary, f"L-6: summary.md do raportu przebiegu: {summary[:200]}")
        git(repo, "add", "src/orders.py")
        git(repo, "commit", "-qm", "orders")

        # C: karencja wersji (N10) — ustawienie menedżera i lockfile w gicie
        c = tmp / "cool"
        c.mkdir()
        git(c, "init", "-q", "-b", "main")
        write(c, "package.json", '{"name": "p"}\n')
        write(c, "package-lock.json", "{}\n")
        git(c, "add", "-A")
        git(c, "commit", "-qm", "init")
        r = run("cooldown", cwd=c)
        check(r.returncode == 1 and "min-release-age=7" in r.stdout and ".npmrc" in r.stdout,
              f"C-1: npm bez karencji → FAIL z linią do dodania: {r.returncode} {r.stdout}")
        write(c, ".npmrc", "min-release-age=7\n")
        r = run("cooldown", cwd=c)
        check(r.returncode == 0, f"C-2: npm z karencją 7 dni → PASS: {r.returncode} {r.stdout}")
        write(c, ".npmrc", "min-release-age=3\n")
        r = run("cooldown", cwd=c)
        check(r.returncode == 1 and "3" in r.stdout, f"C-3: karencja krótsza niż 7 dni → FAIL: {r.stdout}")
        write(c, ".npmrc", "min-release-age=7\n")
        write(c, "pnpm-workspace.yaml", "packages: []\n")
        write(c, "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        r = run("cooldown", cwd=c)
        check(r.returncode == 1 and "minimumReleaseAge: 10080" in r.stdout and "pnpm-lock.yaml" in r.stdout,
              f"C-4: pnpm bez karencji i lockfile poza gitem → FAIL: {r.stdout}")
        write(c, "pnpm-workspace.yaml", "packages: []\nminimumReleaseAge: 10080\n")
        git(c, "add", "-A")
        git(c, "commit", "-qm", "pnpm")
        r = run("cooldown", cwd=c)
        check(r.returncode == 0, f"C-5: pnpm 10080 min + lockfile w gicie → PASS: {r.stdout}")
        p = tmp / "py"
        p.mkdir()
        git(p, "init", "-q", "-b", "main")
        write(p, "pyproject.toml", '[project]\nname = "p"\nversion = "0"\n')
        write(p, "uv.lock", "version = 1\n")
        git(p, "add", "-A")
        git(p, "commit", "-qm", "init")
        r = run("cooldown", cwd=p)
        check(r.returncode == 1 and 'exclude-newer = "7 days"' in r.stdout, f"C-6: uv bez exclude-newer → FAIL: {r.stdout}")
        write(p, "pyproject.toml", '[project]\nname = "p"\nversion = "0"\n\n[tool.uv]\nexclude-newer = "7 days"\n')
        r = run("cooldown", cwd=p)
        check(r.returncode == 0, f"C-7: uv exclude-newer 7 dni → PASS: {r.stdout}")

    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} skan bezpieczeństwa kawałka (security_scan.py)")
    for f in fails:
        print(f"  ✗ {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
