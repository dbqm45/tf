#!/usr/bin/env python3
"""Testy skryptu eng-repo-readiness/scripts/readiness_check.py (gotowość repo do pracy agentów, tylko odczyt plików)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-repo-readiness" / "scripts" / "readiness_check.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60,
                          encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)


def write(root: Path, rel: str, text: str = "") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # 1. --help działa i opisuje kody wyjścia
    r = run("--help")
    check(r.returncode == 0 and "kod" in r.stdout.lower(), f"--help: {r.returncode} {r.stdout[:200]}")

    with tempfile.TemporaryDirectory() as d:
        # Repo „zdrowe”: TS strict, lockfile, vitest, CI z etapami, linter, formatter, instrukcje agenta
        good = Path(d) / "good"
        write(good, "package.json", json.dumps({"name": "a", "scripts": {"test": "vitest run", "lint": "eslint ."},
                                                 "devDependencies": {"vitest": "3.2.4", "typescript": "5.9.0",
                                                                     "eslint": "9.39.1", "prettier": "3.6.0"}}))
        write(good, "package-lock.json", "{}")
        write(good, "tsconfig.json", '{\n  // komentarz\n  "compilerOptions": { "strict": true, }\n}\n')
        write(good, "eslint.config.mjs", "export default [];")
        write(good, ".prettierrc", "{}")
        write(good, ".gitignore", "node_modules\n")
        write(good, ".editorconfig", "root = true\n")
        write(good, ".env.example", "API_URL=\n")
        write(good, "CLAUDE.md", "# Zasady\n")
        write(good, ".github/workflows/ci.yml",
              "jobs:\n  ci:\n    steps:\n      - run: npm ci\n      - run: npm run lint\n      - run: npx tsc --noEmit\n"
              "      - run: npm test\n      - run: npm run build\n      - run: npm audit --audit-level=high\n")
        r = run(str(good), "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        check(bool(data), f"--json: niepoprawny JSON: {r.stdout[:300]} {r.stderr[:300]}")
        fam = {f.get("family"): f for f in data.get("families", [])}
        check("js" in fam and fam["js"].get("lockfile") == "package-lock.json", f"js + lockfile: {fam}")
        check("js" in fam and fam["js"].get("audit", "").startswith("npm audit"), f"komenda audytu js: {fam}")
        check("js" in fam and "vitest list" in (fam["js"].get("dry_run") or ""), f"runner vitest na sucho: {fam}")
        ci = data.get("ci", {})
        check(all(ci.get("stages", {}).get(s) for s in ("lint", "test", "build", "types", "security")),
              f"etapy CI: {ci}")
        check(data.get("verdict") == "zdrowe" and r.returncode == 0, f"werdykt zdrowe/kod 0: {data.get('verdict')} {r.returncode}")
        check("CLAUDE.md" in data.get("instructions", []), f"pliki instrukcji: {data.get('instructions')}")

        # Repo „krytyczne”: JS bez lockfile i bez runnera testów, TS bez strict, bez .gitignore i bez CI
        bad = Path(d) / "bad"
        write(bad, "package.json", json.dumps({"name": "b", "dependencies": {"express": "5.1.0"},
                                                "devDependencies": {"typescript": "5.9.0"}}))
        write(bad, "tsconfig.json", '{"compilerOptions": {"target": "es2022"}}')
        write(bad, "api/requirements.txt", "flask==3.1.0\npytest==8.4.0\n")
        r = run(str(bad), "--json")
        data = json.loads(r.stdout or "{}")
        msgs = " | ".join(f"{x.get('severity')}:{x.get('area')}:{x.get('message')}" for x in data.get("findings", []))
        check(r.returncode == 1, f"kod 1 przy ustaleniach wysokiej wagi: {r.returncode}")
        check("lockfile" in msgs.lower() and "wysoka" in msgs, f"brak lockfile = wysoka: {msgs}")
        check("strict" in msgs, f"TS bez strict wykryty: {msgs}")
        check(".gitignore" in msgs, f"brak .gitignore wykryty: {msgs}")
        check(data.get("verdict") == "krytyczne", f"werdykt krytyczne (brak runnera testów js): {data.get('verdict')}")
        fam = {f.get("family"): f for f in data.get("families", [])}
        check("python" in fam and "pip-audit" in fam["python"].get("audit", "")
              and "collect-only" in (fam["python"].get("dry_run") or ""), f"python w podkatalogu: {fam}")
        check("python" in fam and "słaby" in (fam["python"].get("lockfile_note") or ""),
              f"requirements.txt jako słaby zamiennik lockfile: {fam}")

        # Tekst: tabela i rodzina bez audytu wbudowanego → „pominięto”, nie „0”
        java = Path(d) / "java"
        write(java, "pom.xml", "<project><dependencies><dependency><artifactId>junit-jupiter</artifactId>"
                               "</dependency></dependencies></project>")
        write(java, ".gitignore", "target/\n")
        r = run(str(java))
        check("pominięto" in r.stdout and "| " in r.stdout, f"java: tekst z 'pominięto' i tabelą: {r.stdout[:400]}")

        # Błędna ścieżka → kod 2
        check(run(str(Path(d) / "nie-ma")).returncode == 2, "nieistniejąca ścieżka powinna dać kod 2")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów readiness_check")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
