#!/usr/bin/env python3
"""Slice security scan tests (skill tf, scripts/security_scan.py): scanning only the changed
files, dependency audit only when a manifest or lockfile changes, SARIF in the result directory, a missing scanner is a FAIL,
verdict like SEC-001 in ci_for_sdlc, the FAIL -> STOP path of the slice loop, version cooldown (N10).
Scanners are stubbed (TF_SCAN_PATH). python3 .claude/tests/test_security_scan.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "security_scan.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL).is_file()), None)
SCRIPT = ROOT / REL if ROOT else None

# Stub semgrep: writes argv to $FAKE_LOG; a result for every line with "SQLI" in the scanned files (a rule
# with no level in the result, default warning, tag CWE-89 — like the real semgrep 1.x); exit code from $FAKE_EXIT.
FAKE_SEMGREP = r'''
import json, os, sys
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(["semgrep", *args]) + "\n")
if os.environ.get("FAKE_ENV_LOG"):
    keys = ("SEMGREP_SETTINGS_FILE", "SEMGREP_LOG_FILE", "SEMGREP_VERSION_CACHE_PATH")
    with open(os.environ["FAKE_ENV_LOG"], "w", encoding="utf-8") as f:
        json.dump({k: os.environ.get(k) for k in keys}, f)
out = args[args.index("--output") + 1]
skip = {args[i + 1] for i, a in enumerate(args) if a in ("--config", "--output")}
targets = [a for a in args[1:] if not a.startswith("-") and a not in skip]
results = []
for t in targets:
    for n, line in enumerate(open(t, encoding="utf-8").read().splitlines(), 1):
        if "SQLI" in line:
            results.append({"ruleId": "fake.sql-injection", "ruleIndex": 0, "message": {"text": "SQL built from user input"},
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
        print(f"✗ missing script {REL}")
        return 1
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = tmp / "log.jsonl"
        full = fake_bin(tmp / "bin", {"semgrep": FAKE_SEMGREP, "npm": FAKE_NPM, "pip-audit": FAKE_PIP_AUDIT})
        empty = fake_bin(tmp / "empty", {})
        env = {**os.environ, "TF_SCAN_PATH": str(full), "FAKE_LOG": str(log)}

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

        # S-1: the scan covers only the slice's changes (changed and new files), not the whole repo
        write(repo, "old.py", "x = 2\n")
        write(repo, "src/new.py", "y = 1\n")
        out = repo / ".claude" / "runs" / "r1" / "security"
        r = run("scan", "--out", str(out), cwd=repo)
        calls = log_of(log)
        sem = [c for c in calls if c[0] == "semgrep"]
        targets = {a.removeprefix("./") for a in (sem[0][1:] if sem else []) if a.endswith(".py")}
        check(r.returncode == 0 and len(sem) == 1, f"S-1: semgrep once, PASS: {r.returncode} {r.stdout} {r.stderr}")
        check(targets == {"old.py", "src/new.py"}, f"S-2: only changed files: {targets}")
        check(sem and "--metrics=off" in sem[0] and "--sarif" in sem[0] and "p/owasp-top-ten" in sem[0],
              f"S-3: OWASP rules, SARIF, no metrics: {sem[:1]}")
        check((out / "semgrep.sarif").is_file() and (out / "verdict.json").is_file(), "S-4: SARIF and verdict in the result directory")
        check(not [c for c in calls if c[0] in ("npm", "pip-audit")], f"S-5: no audit without a manifest change: {calls}")
        check("SCAN: PASS" in r.stdout, f"S-6: PASS verdict line: {r.stdout}")

        # S-19: semgrep state (settings, log, version cache) in the clone, not in $HOME — in the container's Bash sandbox
        # of the phase HOME is not writable and semgrep ends with FileNotFoundError on mkdir (PRB-32, A6 2026-11-05)
        env_log = tmp / "env.json"
        log.unlink(missing_ok=True)
        run("scan", "--out", str(out), cwd=repo, FAKE_ENV_LOG=str(env_log))
        seen = json.loads(env_log.read_text()) if env_log.is_file() else {}
        state = (repo / ".tf" / "cache" / "semgrep").resolve()
        check(seen and all(v and Path(v).resolve().parent == state for v in seen.values()),
              f"S-19: the SEMGREP_* variables point to {state}: {seen}")
        status = subprocess.run(["git", "status", "--porcelain", ".tf"], cwd=repo, capture_output=True, text=True).stdout
        check(state.is_dir() and not status.strip(), f"S-20: the semgrep state directory is outside git: {status!r}")
        run("scan", "--out", str(out), cwd=repo, FAKE_ENV_LOG=str(env_log), SEMGREP_SETTINGS_FILE=str(tmp / "own.yml"))
        seen = json.loads(env_log.read_text()) if env_log.is_file() else {}
        check(seen.get("SEMGREP_SETTINGS_FILE") == str(tmp / "own.yml"), f"S-21: a custom setting is kept: {seen}")

        # S-7: the product's own rules (.semgrep.yml) are added to OWASP
        write(repo, ".semgrep.yml", "rules: []\n")
        log.unlink(missing_ok=True)
        run("scan", "--out", str(out), cwd=repo)
        sem = [c for c in log_of(log) if c[0] == "semgrep"]
        check(sem and ".semgrep.yml" in sem[0], f"S-7: the product's .semgrep.yml in the configuration: {sem[:1]}")
        (repo / ".semgrep.yml").unlink()

        # S-7b: semgrep rules of packs (e.g. a company one) from .tf/factory/packs/<id>/semgrep.yml are added to the slice scan
        write(repo, ".tf/factory/packs/pack-firma/semgrep.yml", "rules: []\n")
        log.unlink(missing_ok=True)
        run("scan", "--out", str(out), cwd=repo)
        sem = [c for c in log_of(log) if c[0] == "semgrep"]
        check(sem and any(x.endswith(".tf/factory/packs/pack-firma/semgrep.yml") for x in sem[0]),
              f"S-7b: the company pack's semgrep rules in the configuration: {sem[:1]}")
        (repo / ".tf" / "factory" / "packs" / "pack-firma" / "semgrep.yml").unlink()

        # S-8: an npm lockfile change runs npm audit; the result as SARIF with a line in the lockfile
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
              f"S-9: npm audit as SARIF (high -> error, line in the lockfile): {ares}")
        check(r.returncode == 1 and "npm-audit/GHSA-grv7-fg5c-xmjg" in r.stdout and "package-lock.json:4" in r.stdout,
              f"S-10: a high vulnerability blocks, with rule and location: {r.returncode} {r.stdout}")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "lock")

        # S-11: a requirements*.txt change runs pip-audit; a known vulnerability with no severity blocks (A06:2021)
        write(repo, "requirements.txt", "jinja2==3.1.2\n")
        log.unlink(missing_ok=True)
        r = run("scan", "--out", str(out), cwd=repo)
        pa = [c for c in log_of(log) if c[0] == "pip-audit"]
        check(pa and "-r" in pa[0] and "requirements.txt" in pa[0] and "json" in pa[0], f"S-11: pip-audit -r … -f json: {pa}")
        check((out / "pip-audit.sarif").is_file() and r.returncode == 1 and "GHSA-h5c8-rqwp-cp95" in r.stdout,
              f"S-12: pip-audit as SARIF, the vulnerability blocks: {r.returncode} {r.stdout}")
        check(not (out / "npm-audit.sarif").exists(), "S-13: the old npm audit SARIF removed from the result directory")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "req")

        # S-14: --base: changes since the base branch (CI on a PR), including already committed ones
        git(repo, "checkout", "-qb", "feat/x")
        write(repo, "src/committed.py")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "c")
        log.unlink(missing_ok=True)
        r = run("scan", "--base", "main", "--out", str(out), cwd=repo)
        sem = [c for c in log_of(log) if c[0] == "semgrep"]
        targets = {a.removeprefix("./") for a in (sem[0][1:] if sem else []) if a.endswith(".py")}
        check(r.returncode == 0 and targets == {"src/committed.py"}, f"S-14: --base takes the branch's commits: {targets} {r.stderr}")

        # S-15: no changes -> PASS without running the scanner, empty SARIF (CI does not report a missing scan)
        git(repo, "checkout", "-q", "main")
        log.unlink(missing_ok=True)
        r = run("scan", "--out", str(out), cwd=repo)
        empty_sarif = json.loads((out / "semgrep.sarif").read_text()) if (out / "semgrep.sarif").is_file() else {}
        check(r.returncode == 0 and not log_of(log) and empty_sarif.get("runs", [{}])[0].get("results") == [],
              f"S-15: no changes: {r.returncode} {log_of(log)} {empty_sarif}")

        # S-16: no scanner -> FAIL with an install command, never a silent PASS
        write(repo, "a.py")
        r = run("scan", "--out", str(out), cwd=repo, TF_SCAN_PATH=str(empty))
        check(r.returncode == 1 and "semgrep" in r.stdout and "pipx install semgrep" in r.stdout and "SCAN: FAIL" in r.stdout,
              f"S-16: no semgrep: {r.returncode} {r.stdout} {r.stderr}")
        write(repo, "requirements.txt", "jinja2==3.1.4\n")
        r = run("scan", "--out", str(out), cwd=repo, TF_SCAN_PATH=str(fake_bin(tmp / "semonly", {"semgrep": FAKE_SEMGREP})))
        check(r.returncode == 1 and "pip install pip-audit" in r.stdout, f"S-17: no pip-audit on a manifest change: {r.stdout}")
        git(repo, "checkout", "-q", "--", "requirements.txt")

        # S-18: scanner error (code != 0) -> FAIL, not PASS
        r = run("scan", "--out", str(out), cwd=repo, FAKE_EXIT="2")
        check(r.returncode == 1 and "SCAN: FAIL" in r.stdout and "invalid configuration" in r.stdout,
              f"S-18: a semgrep error is a FAIL: {r.returncode} {r.stdout}")

        # D: the project's one decision to work without a scanner (tf config security.scanner off): recorded, not a FAIL
        import shutil
        engine = repo / ".tf" / "factory"
        engine.mkdir(parents=True, exist_ok=True)
        for name in ("packs.py", "task_weight.py"):
            if (ROOT / ".tf" / "factory" / name).is_file():
                shutil.copy(ROOT / ".tf" / "factory" / name, engine / name)
        if (ROOT / ".tf" / "factory" / "_vendor").is_dir():
            shutil.copytree(ROOT / ".tf" / "factory" / "_vendor", engine / "_vendor", dirs_exist_ok=True)
        (repo / ".tf" / ".gitignore").write_text("*\n", encoding="utf-8")
        r = run("scanner", cwd=repo, TF_SCAN_PATH=str(empty))
        check(r.returncode == 1 and "security.scanner off" in r.stdout and "human:" in r.stdout,
              f"D-1: no scanner and no decision -> `scanner` says what to ask the human: {r.returncode} {r.stdout}{r.stderr}")
        import importlib.util
        spec = importlib.util.spec_from_file_location("scan_test_packs", engine / "packs.py")
        packs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packs)
        (repo / ".tf" / "config").mkdir(parents=True, exist_ok=True)
        (repo / ".tf" / "config" / "config.yaml").write_text("# own\nsecurity:\n  other: 1\n", encoding="utf-8")
        packs.write_scanner_decision(repo, "off", "human:anna", "no semgrep on Windows laptops", "2026-11-24")
        cfg_text = (repo / ".tf" / "config" / "config.yaml").read_text(encoding="utf-8")
        check("# own" in cfg_text and "other: 1" in cfg_text and cfg_text.count("scanner:") == 1
              and (packs.scanner_decision(repo) or {}).get("by") == "human:anna",
              f"D-2: the decision goes into the existing security block, the rest of the file stays: {cfg_text}")
        r = run("scan", "--out", str(out), "--slice", "S1", "--attempt", "1", cwd=repo, TF_SCAN_PATH=str(empty))
        v = json.loads((out / "attempt-1" / "verdict.json").read_text()) if (out / "attempt-1" / "verdict.json").is_file() else {}
        check(r.returncode == 0 and "scanner off by decision (human:anna, 2026-11-24)" in r.stdout and "STOP" not in r.stdout
              and v.get("status") == "PASS" and any("by decision" in n for n in v.get("notes") or []),
              f"D-3: a missing scanner with the decision -> recorded in the verdict, no FAIL or STOP: {r.returncode} {r.stdout} {v}")
        r = run("scanner", cwd=repo, TF_SCAN_PATH=str(empty))
        check(r.returncode == 0 and "⚠" in r.stdout and "by decision" in r.stdout, f"D-4: `scanner` shows the decision: {r.stdout}")
        r = run("scan", "--out", str(out), cwd=repo)
        check(r.returncode == 0 and any(x[0] == "semgrep" for x in log_of(log)),
              f"D-5: with the scanner installed the decision changes nothing — it runs: {r.stdout}")
        packs.write_scanner_decision(repo, "on", "human:anna", "", "2026-11-25")
        r = run("scan", "--out", str(out), cwd=repo, TF_SCAN_PATH=str(empty))
        check(r.returncode == 1 and "SCAN: FAIL" in r.stdout and packs.scanner_decision(repo) is None,
              f"D-6: the decision withdrawn -> a missing scanner is a FAIL again: {r.stdout}")
        (repo / "a.py").unlink()

        # the scan runs only on the slice's changed files, whatever their kind — there is no skipping by extension
        write(repo, "web/list.component.html", "<div>SQLI</div>\n")
        log.unlink(missing_ok=True)
        r = run("scan", "--out", str(out), cwd=repo)
        scanned = [a for x in log_of(log) for a in x if a.startswith("web/")]
        check(r.returncode == 1 and scanned == ["web/list.component.html"],
              f"P-1: a changed template is scanned like any changed file: {scanned} {r.stdout}")
        (repo / "web" / "list.component.html").unlink()

        # N: package.json without dependencies and without a lockfile (e.g. only scripts and engines) — nothing to audit:
        # no audit, no error, the verdict and summary say the audit was skipped; with dependencies and no lockfile -> error
        nd = tmp / "nodeps"
        nd.mkdir()
        git(nd, "init", "-q", "-b", "main")
        write(nd, "package.json", '{"name": "p", "scripts": {"test": "node --test"}, "engines": {"node": ">=20"}}\n')
        write(nd, "app.js", "x = 1\n")
        git(nd, "add", "-A")
        git(nd, "commit", "-qm", "init")
        write(nd, "package.json", '{"name": "p", "scripts": {"test": "node --test"}, "engines": {"node": ">=22.13"}}\n')
        nout = nd / "reports" / "security"
        log.unlink(missing_ok=True)
        r = run("scan", "--out", str(nout), "--json", cwd=nd)
        v = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 0 and v.get("status") == "PASS" and not v.get("errors") and not v.get("audits"),
              f"N-1: package.json without dependencies -> PASS with no error and no audit: {r.returncode} {r.stdout[:400]}")
        check(not [c for c in log_of(log) if c[0] in ("npm", "pip-audit")], f"N-2: audit not run: {log_of(log)}")
        check(v.get("skipped") and "package.json" in v["skipped"][0] and "without dependencies" in v["skipped"][0],
              f"N-3: the verdict says the audit was skipped (manifest without dependencies): {v.get('skipped')}")
        r = run("scan", "--out", str(nout), "--slice", "S1", "--attempt", "1", cwd=nd)
        summary = (nout / "attempt-1" / "summary.md").read_text(encoding="utf-8") if (nout / "attempt-1" / "summary.md").is_file() else ""
        check(r.returncode == 0 and "GATE S1: PASS" in r.stdout and "dependency audit skipped" in r.stdout.lower()
              and "dependency audit skipped" in summary.lower() and "without dependencies" in summary,
              f"N-4: the scan line and summary.md mention the skipped audit: {r.stdout} | {summary}")
        for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
            write(nd, "package.json", '{"name": "p", "%s": {"left-pad": "1.3.0"}}\n' % section)
            r = run("scan", "--out", str(nout), "--json", cwd=nd)
            v = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
            check(r.returncode == 1 and any("without a lockfile" in e for e in v.get("errors", [])) and not v.get("skipped"),
                  f"N-5: {section} without a lockfile -> error as before: {r.returncode} {r.stdout[:400]}")
        write(nd, "package.json", "{not json\n")
        r = run("scan", "--out", str(nout), "--json", cwd=nd)
        v = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        check(r.returncode == 1 and v.get("errors"), f"N-6: an unreadable package.json without a lockfile -> error, not a skip: {r.stdout[:400]}")
        # cooldown consistent with the scan: no dependencies -> PASS with the same reason; dependencies without a lockfile -> FAIL
        git(nd, "checkout", "-q", "--", "package.json")
        r = run("cooldown", cwd=nd)
        check(r.returncode == 0 and "without dependencies" in r.stdout, f"N-7: cooldown: package.json without dependencies -> PASS: {r.stdout}")
        write(nd, "package.json", '{"name": "p", "dependencies": {"left-pad": "1.3.0"}}\n')
        r = run("cooldown", cwd=nd)
        check(r.returncode == 1 and "lockfile" in r.stdout and "package.json" in r.stdout,
              f"N-8: cooldown: dependencies without a lockfile -> FAIL like the scan: {r.returncode} {r.stdout}")

        # V: verdict rule = SEC-001 of ci_for_sdlc (error, or warning with a CWE from the OWASP Top 10 2021/2025)
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
        check(r.returncode == 1 and v.get("status") == "FAIL", f"V-1: blocking findings -> FAIL: {r.returncode} {r.stdout[:300]}")
        check(blocking == {"r.error", "r.warn-owasp", "r.default", "r.result-cwe", "r.warn-2025"},
              f"V-2: blocking per SEC-001: {blocking}")
        check(other == {"r.warn-other", "r.note"}, f"V-3: below the threshold (for the report), level none skipped: {other}")
        b0 = next((b for b in v.get("blocking", []) if b.get("rule") == "r.warn-owasp"), {})
        check(b0.get("file") == "app.py" and b0.get("line") == 2 and 89 in b0.get("cwe", []), f"V-4: rule, file, line, CWE: {b0}")
        (vdir / "b.sarif").write_text(json.dumps(sarif([res("r.warn-other", "warning", tags=["CWE-1333"])])))
        r = run("verdict", str(vdir / "b.sarif"), cwd=repo)
        check(r.returncode == 0 and "SCAN: PASS" in r.stdout and "r.warn-other" in r.stdout,
              f"V-5: only below the threshold -> PASS with a list for the report: {r.returncode} {r.stdout}")
        (vdir / "bad.sarif").write_text("not json")
        r = run("verdict", str(vdir / "bad.sarif"), cwd=repo)
        check(r.returncode == 1 and "Traceback" not in r.stderr, f"V-6: a bad SARIF is a FAIL, not a silent PASS: {r.returncode} {r.stderr}")
        r = run("verdict", cwd=repo)
        check(r.returncode == 2, f"V-7: a bad invocation -> 2: {r.returncode}")

        # L: slice loop — attempt 1 with SQL injection -> FAIL with a finding for the next attempt; attempt 2 still failing -> STOP;
        # after a fix -> PASS and a report of findings below the threshold in the run directory
        write(repo, "src/orders.py", 'q = "SELECT * FROM o WHERE id=%s" % user_id  # SQLI\n')
        out = repo / ".claude" / "runs" / "r2" / "security"
        r = run("scan", "--out", str(out), "--slice", "S2", "--attempt", "1", cwd=repo)
        fb = (out / "feedback.md").read_text(encoding="utf-8") if (out / "feedback.md").is_file() else ""
        check(r.returncode == 1 and "GATE S2: FAIL" in r.stdout and "attempt 1/2" in r.stdout
              and "fake.sql-injection src/orders.py:1" in r.stdout, f"L-1: FAIL of attempt 1 with rule and location: {r.stdout}")
        check("fake.sql-injection" in fb and "src/orders.py:1" in fb, f"L-2: finding saved for the next attempt: {fb}")
        check("STOP" not in r.stdout, f"L-3: no STOP yet after attempt 1: {r.stdout}")
        r = run("scan", "--out", str(out), "--slice", "S2", "--attempt", "2", cwd=repo)
        check(r.returncode == 1 and "STOP — S2" in r.stdout and "Reason:" in r.stdout and "src/orders.py:1" in r.stdout,
              f"L-4: FAIL of attempt 2 -> STOP block: {r.stdout}")
        write(repo, "src/orders.py", 'q = db.execute("SELECT * FROM o WHERE id=?", (user_id,))\n')
        r = run("scan", "--out", str(out), "--slice", "S2", "--attempt", "2", cwd=repo)
        check(r.returncode == 0 and "GATE S2: PASS" in r.stdout and "STOP" not in r.stdout,
              f"L-5: PASS after the fix: {r.returncode} {r.stdout}")
        summary = (out / "attempt-2" / "summary.md").read_text(encoding="utf-8") if (out / "attempt-2" / "summary.md").is_file() else ""
        check(summary.startswith("## Security") and "PASS" in summary, f"L-6: summary.md for the run report: {summary[:200]}")
        # each attempt has its own directory (attempt-<k>): the result of attempt 1 survives attempt 2; feedback.md in --out is from the last one
        first = (out / "attempt-1" / "summary.md").read_text(encoding="utf-8") if (out / "attempt-1" / "summary.md").is_file() else ""
        check("FAIL" in first and "fake.sql-injection src/orders.py:1" in first and (out / "attempt-1" / "semgrep.sarif").is_file()
              and (out / "attempt-1" / "verdict.json").is_file(), f"L-7: the result of attempt 1 kept after attempt 2: {first[:300]}")
        fb = (out / "feedback.md").read_text(encoding="utf-8") if (out / "feedback.md").is_file() else ""
        check("no blocking findings" in fb and "fake.sql-injection" not in fb, f"L-8: feedback.md from the last attempt: {fb}")
        check(not (out / "summary.md").exists() and not list(out.glob("*.sarif")) and not (out / "verdict.json").exists(),
              f"L-9: no attempt result outside attempt-<k>: {sorted(p.name for p in out.iterdir())}")
        git(repo, "add", "src/orders.py")
        git(repo, "commit", "-qm", "orders")

        # C: version cooldown (N10) — the package manager setting and the lockfile in git
        c = tmp / "cool"
        c.mkdir()
        git(c, "init", "-q", "-b", "main")
        write(c, "package.json", '{"name": "p"}\n')
        write(c, "package-lock.json", "{}\n")
        git(c, "add", "-A")
        git(c, "commit", "-qm", "init")
        r = run("cooldown", cwd=c)
        check(r.returncode == 1 and "min-release-age=7" in r.stdout and ".npmrc" in r.stdout,
              f"C-1: npm without a cooldown -> FAIL with the line to add: {r.returncode} {r.stdout}")
        write(c, ".npmrc", "min-release-age=7\n")
        r = run("cooldown", cwd=c)
        check(r.returncode == 0, f"C-2: npm with a 7-day cooldown -> PASS: {r.returncode} {r.stdout}")
        write(c, ".npmrc", "min-release-age=3\n")
        r = run("cooldown", cwd=c)
        check(r.returncode == 1 and "3" in r.stdout, f"C-3: a cooldown shorter than 7 days -> FAIL: {r.stdout}")
        write(c, ".npmrc", "min-release-age=7\n")
        write(c, "pnpm-workspace.yaml", "packages: []\n")
        write(c, "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        r = run("cooldown", cwd=c)
        check(r.returncode == 1 and "minimumReleaseAge: 10080" in r.stdout and "pnpm-lock.yaml" in r.stdout,
              f"C-4: pnpm without a cooldown and a lockfile outside git -> FAIL: {r.stdout}")
        write(c, "pnpm-workspace.yaml", "packages: []\nminimumReleaseAge: 10080\n")
        git(c, "add", "-A")
        git(c, "commit", "-qm", "pnpm")
        r = run("cooldown", cwd=c)
        check(r.returncode == 0, f"C-5: pnpm 10080 min + lockfile in git -> PASS: {r.stdout}")
        p = tmp / "py"
        p.mkdir()
        git(p, "init", "-q", "-b", "main")
        write(p, "pyproject.toml", '[project]\nname = "p"\nversion = "0"\n')
        write(p, "uv.lock", "version = 1\n")
        git(p, "add", "-A")
        git(p, "commit", "-qm", "init")
        r = run("cooldown", cwd=p)
        check(r.returncode == 1 and 'exclude-newer = "7 days"' in r.stdout, f"C-6: uv without exclude-newer -> FAIL: {r.stdout}")
        write(p, "pyproject.toml", '[project]\nname = "p"\nversion = "0"\n\n[tool.uv]\nexclude-newer = "7 days"\n')
        r = run("cooldown", cwd=p)
        check(r.returncode == 0, f"C-7: uv exclude-newer 7 days -> PASS: {r.stdout}")

        # F: cooldown --fix writes the missing settings itself (one command instead of editing files by hand)
        f = tmp / "fix"
        f.mkdir()
        git(f, "init", "-q", "-b", "main")
        write(f, "package.json", '{"name": "p"}\n')
        write(f, "package-lock.json", "{}\n")
        write(f, ".npmrc", "registry=https://registry.example/\nmin-release-age=3\n")
        write(f, "yarn.lock", "# yarn\n")
        write(f, ".yarnrc.yml", "nodeLinker: node-modules\n")
        write(f, "pyproject.toml", '[project]\nname = "p"\nversion = "0"\n\n[tool.uv]\npackage = true\n')
        write(f, "uv.lock", "version = 1\n")
        git(f, "add", "-A")
        git(f, "commit", "-qm", "init")
        r = run("cooldown", "--fix", cwd=f)
        npmrc = (f / ".npmrc").read_text(encoding="utf-8")
        check(r.returncode == 0 and "registry=https://registry.example/" in npmrc and "min-release-age=7" in npmrc
              and "min-release-age=3" not in npmrc, f"F-1: npm: the short cooldown raised, other lines kept: {r.stdout} {npmrc}")
        yarnrc = (f / ".yarnrc.yml").read_text(encoding="utf-8")
        check("nodeLinker: node-modules" in yarnrc and 'npmMinimalAgeGate: "7d"' in yarnrc, f"F-2: Yarn: {yarnrc}")
        pyproject = (f / "pyproject.toml").read_text(encoding="utf-8")
        check('package = true' in pyproject and 'exclude-newer = "7 days"' in pyproject
              and pyproject.count("[tool.uv]") == 1, f"F-3: uv: inside the existing [tool.uv]: {pyproject}")
        check("COOLDOWN: PASS" in r.stdout and "written" in r.stdout, f"F-4: the check after the fix passes: {r.stdout}")
        before = {n: (f / n).read_text(encoding="utf-8") for n in (".npmrc", ".yarnrc.yml", "pyproject.toml")}
        r = run("cooldown", "--fix", cwd=f)
        check(r.returncode == 0 and all((f / n).read_text(encoding="utf-8") == t for n, t in before.items()),
              f"F-5: --fix again changes nothing: {r.stdout}")
        g = tmp / "fix2"
        g.mkdir()
        git(g, "init", "-q", "-b", "main")
        write(g, "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
        write(g, "pyproject.toml", '[project]\nname = "p"\nversion = "0"\n')
        write(g, "uv.lock", "version = 1\n")
        r = run("cooldown", "--fix", cwd=g)
        check(r.returncode == 1 and "minimum-release-age=10080" in (g / ".npmrc").read_text(encoding="utf-8")
              and not (g / "pnpm-workspace.yaml").exists() and "[tool.uv]" in (g / "pyproject.toml").read_text(encoding="utf-8")
              and "pnpm-lock.yaml is not in git" in r.stdout,
              f"F-6: pnpm without a workspace file -> .npmrc; new [tool.uv]; a lockfile outside git is only reported: "
              f"{r.returncode} {r.stdout}")

    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} slice security scan (security_scan.py)")
    for f in fails:
        print(f"  ✗ {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
