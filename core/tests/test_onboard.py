#!/usr/bin/env python3
"""Testy `tf onboard` (.tf/factory/onboard.py): wykrycie poleceń projektu z plików, raport gotowości w zwykłym języku,
zapis `.claude/quality-gate.json` — bez uruchamiania czegokolwiek w projekcie. python3 tests/test_onboard.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
ONBOARD = ROOT / ".tf" / "factory" / "onboard.py"
CTF = ROOT / ".tf" / "factory" / "tf.py"

NODE = {"name": "app", "scripts": {"test": "vitest run", "lint": "eslint .", "typecheck": "tsc --noEmit",
                                   "build": "vite build"}}


def make(base: Path, name: str, files: dict) -> Path:
    p = base / name
    for rel, body in files.items():
        f = p / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
    p.mkdir(parents=True, exist_ok=True)
    return p


def run(project: Path, *args: str):
    return subprocess.run([sys.executable, str(ONBOARD), *args], cwd=project, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, timeout=60, env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def detected(project: Path) -> dict:
    r = run(project, "--json")
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"error": r.stdout + r.stderr}


def cmds(d: dict) -> dict:
    return {k: v.get("command") for k, v in (d.get("commands") or {}).items()}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not ONBOARD.is_file():
        print(f"✗ brak {ONBOARD}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = make(base, "npm", {"package.json": NODE, "package-lock.json": "{}", ".gitignore": "node_modules\n",
                               ".github/workflows/ci.yml": "on: push\n"})
        d = detected(p)
        check(cmds(d) == {"test": "npm test", "lint": "npm run lint", "typecheck": "npm run typecheck",
                          "build": "npm run build"}, f"O-1: skrypty package.json → polecenia npm: {d}")
        check(d.get("verdict") == "gotowe" and not (p / ".claude").exists() and not (p / ".tf").exists(),
              f"O-2: komplet → werdykt „gotowe”; --json niczego nie zapisuje: {d.get('verdict')}")

        p = make(base, "notest", {"package.json": {"scripts": {"test": 'echo "Error: no test specified" && exit 1'}}})
        r = run(p, "--json")
        d = json.loads(r.stdout)
        check("test" not in cmds(d) and d.get("verdict") == "brak-testow" and r.returncode == 1,
              f"O-3: domyślny skrypt npm to nie testy → werdykt brak-testow, kod 1: {r.returncode} {d}")

        p = make(base, "pnpm", {"package.json": NODE, "pnpm-lock.yaml": ""})
        check(cmds(detected(p)).get("test") == "pnpm test" and cmds(detected(p)).get("lint") == "pnpm run lint",
              f"O-4: pnpm-lock.yaml → pnpm: {cmds(detected(p))}")

        p = make(base, "py", {"pyproject.toml": '[project]\nname = "x"\n[tool.pytest.ini_options]\n[tool.ruff]\n'
                                                '[tool.mypy]\n', "uv.lock": "", "tests/test_a.py": "def test_a(): pass\n"})
        check(cmds(detected(p)) == {"test": "uv run pytest", "lint": "uv run ruff check .", "typecheck": "uv run mypy ."},
              f"O-5: pyproject z pytest, ruff, mypy i uv.lock: {cmds(detected(p))}")

        p = make(base, "go", {"go.mod": "module x\n\ngo 1.23\n", "go.sum": ""})
        check(cmds(detected(p)) == {"test": "go test ./...", "lint": "go vet ./...", "build": "go build ./..."},
              f"O-6: go.mod: {cmds(detected(p))}")

        p = make(base, "mvn", {"pom.xml": "<project/>", "mvnw": "#!/bin/sh\n"})
        check(cmds(detected(p)).get("test") == "./mvnw -q test", f"O-7: pom.xml z mvnw: {cmds(detected(p))}")

        p = make(base, "make", {"Makefile": "test:\n\tpytest\nlint:\n\truff check .\n.PHONY: test lint\n"})
        check(cmds(detected(p)) == {"test": "make test", "lint": "make lint"}, f"O-8: Makefile jako zapas: {cmds(detected(p))}")

        p = make(base, "empty", {"README.md": "# x\n"})
        r = run(p, "--json")
        check(r.returncode == 1 and json.loads(r.stdout).get("verdict") == "brak-testow",
              f"O-9: nic nie wykryto → brak-testow, bez wyjątku: {r.stdout}{r.stderr}")

        # zapis: tylko z --yes; istniejącej konfiguracji bramki nie nadpisuje
        p = make(base, "write", {"package.json": NODE, "package-lock.json": "{}"})
        r = run(p)
        check(r.returncode == 0 and not (p / ".claude" / "quality-gate.json").exists() and "--yes" in r.stdout
              and "npm test" in r.stdout, f"O-10: bez --yes i bez terminala tylko propozycja: {r.stdout}{r.stderr}")
        r = run(p, "--yes")
        gate = p / ".claude" / "quality-gate.json"
        report = p / ".tf" / "reports" / "readiness.md"
        check(r.returncode == 0 and gate.is_file() and json.loads(gate.read_text()).get("command") == "npm test",
              f"O-11: --yes zapisuje polecenie testów do bramki: {r.stdout}{r.stderr}")
        text = report.read_text(encoding="utf-8") if report.is_file() else ""
        check(all(h in text for h in ("## Co jest", "## Czego brakuje", "## Co fabryka blokuje", "## Kiedy ma spojrzeć człowiek")),
              f"O-12: raport gotowości ma stałe sekcje: {text[:300]}")
        blocking = text.split("## Co fabryka blokuje", 1)[-1].split("## ", 1)[0]
        n = sum(1 for ln in blocking.splitlines() if ln.startswith("- "))
        check(1 <= n <= 5, f"O-13: najwyżej pięć kontroli blokujących ({n}): {blocking}")
        check(not any(w in text.lower() for w in ("hook", "tier", "harness", "triaż")),
              "O-14: raport dla człowieka bez słownictwa z budowy fabryki")
        gate.write_text(json.dumps({"command": "npm run test:ci", "watch": ["src/"]}))
        r = run(p, "--yes")
        check(json.loads(gate.read_text()).get("command") == "npm run test:ci" and "zostaje" in r.stdout,
              f"O-15: istniejąca konfiguracja bramki zostaje, z informacją: {r.stdout}")
        r = run(p, "--dry-run", "--yes")
        check(r.returncode == 0 and "npm test" in r.stdout, f"O-16: --dry-run pokazuje propozycję: {r.stdout}{r.stderr}")

        p = make(base, "dry", {"package.json": NODE})
        r = run(p, "--dry-run", "--yes")
        check(not (p / ".claude").exists() and not (p / ".tf").exists(), "O-17: --dry-run niczego nie zapisuje")
        check("lockfile" not in r.stdout.lower() or "brak" in r.stdout.lower(), f"O-18: brak pliku blokady wersji jest nazwany: {r.stdout}")

        # tf onboard przekazuje argumenty do skryptu w projekcie
        p = make(base, "tf", {"package.json": NODE, "package-lock.json": "{}",
                              ".claude/factory-manifest.json": {"version": "1.0.0"}})
        (p / ".tf" / "factory").mkdir(parents=True)
        shutil.copy(ONBOARD, p / ".tf" / "factory" / "onboard.py")
        r = subprocess.run([sys.executable, str(CTF), "onboard", "--json"], cwd=p, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=60)
        try:
            ok = cmds(json.loads(r.stdout)).get("test") == "npm test"
        except ValueError:
            ok = False
        check(ok, f"O-19: tf onboard uruchamia .tf/factory/onboard.py: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(CTF), "onboard"], cwd=base / "empty", capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=60)
        check(r.returncode == 2 and "tf install" in r.stdout, f"O-20: bez fabryki w katalogu → podpowiedź instalacji: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów tf onboard")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
