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
        want = "npm test" if os.name == "nt" else "./verify.sh"
        check(r.returncode == 0 and gate.is_file() and json.loads(gate.read_text()).get("command") == want,
              f"O-11: --yes zapisuje polecenie weryfikacji do bramki ({want}): {r.stdout}{r.stderr}")
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

        # część 2: jedno polecenie weryfikacji (lint, typy, testy), polecenia w pliku instrukcji, próba na żądanie
        if os.name != "nt":
            p = make(base, "verify", {"package.json": NODE, "package-lock.json": "{}"})
            run(p, "--yes")
            v = p / "verify.sh"
            body = v.read_text(encoding="utf-8") if v.is_file() else ""
            order = [body.find(c) for c in ("npm run lint", "npm run typecheck", "npm test")]
            check(v.is_file() and os.access(v, os.X_OK) and -1 not in order and order == sorted(order)
                  and "set -e" in body and "npm run build" not in body,
                  f"O-21: verify.sh wykonywalny, w kolejności lint → typy → testy, bez buildu: {body}")
            text = (p / ".tf" / "reports" / "readiness.md").read_text(encoding="utf-8")
            blocking = text.split("## Co fabryka blokuje", 1)[-1].split("## ", 1)[0]
            n = sum(1 for ln in blocking.splitlines() if ln.startswith("- "))
            check(n == 5 and "npm run lint" in blocking and "npm run typecheck" in blocking and "Tylko ostrzega" in text
                  and "npm run build" in text.split("Tylko ostrzega", 1)[-1],
                  f"O-22: lint i typy blokują (razem pięć kontroli), build tylko ostrzega: {blocking}")

            p = make(base, "own-verify", {"package.json": NODE, "verify.sh": "#!/bin/sh\necho moje\n"})
            r = run(p, "--yes")
            check((p / "verify.sh").read_text() == "#!/bin/sh\necho moje\n" and "zostaje" in r.stdout
                  and json.loads((p / ".claude" / "quality-gate.json").read_text()).get("command") == "./verify.sh",
                  f"O-23: istniejący verify.sh zostaje i jest poleceniem bramki: {r.stdout}")

            p = make(base, "run", {"Makefile": "test:\n\t@echo testy-ok\nlint:\n\t@echo lint-ok\n"})
            if shutil.which("make"):
                r = run(p, "--yes", "--verify")
                check(r.returncode == 0 and "przechodzi" in r.stdout, f"O-24: --verify uruchamia weryfikację raz, zielona: {r.stdout}{r.stderr}")
                (p / "Makefile").write_text("test:\n\t@echo FAILED test_x; exit 1\nlint:\n\t@echo lint-ok\n")
                r = run(p, "--yes", "--verify")
                check(r.returncode == 1 and "nie przechodzi" in r.stdout and "FAILED test_x" in r.stdout,
                      f"O-25: --verify przy czerwonych testach → kod 1 i koniec wyjścia: {r.stdout}{r.stderr}")

        block = ("moje zasady\n\n<!-- team-factory:begin -->\n## Zespół agentów (team factory)\n\n### Komendy\n"
                 "- Test: `npm test` · Lint: `npm run lint` · Typecheck: `npm run typecheck` · Build: `npm run build`\n"
                 "  (dostosuj do swojego projektu — wykonawcy używają ich do weryfikacji)\n\n### Stack\n- x\n"
                 "<!-- team-factory:end -->\nna końcu\n")
        p = make(base, "md", {"pyproject.toml": "[tool.pytest.ini_options]\n[tool.ruff]\n", "uv.lock": "",
                              "CLAUDE.local.md": block})
        r = run(p, "--yes")
        md = (p / "CLAUDE.local.md").read_text(encoding="utf-8")
        check("Test: `uv run pytest`" in md and "Lint: `uv run ruff check .`" in md and "npm" not in md
              and "dostosuj do swojego projektu" not in md and md.startswith("moje zasady\n") and md.endswith("na końcu\n")
              and "### Stack\n- x" in md and "CLAUDE.local.md" in r.stdout,
              f"O-26: polecenia projektu w sekcji „Komendy” bloku fabryki, reszta pliku bez zmian: {md}")
        p = make(base, "nomd", {"pyproject.toml": "[tool.pytest.ini_options]\n", "CLAUDE.md": "# moje\n"})
        run(p, "--yes")
        check((p / "CLAUDE.md").read_text() == "# moje\n" and not (p / "CLAUDE.local.md").exists(),
              "O-27: plik instrukcji bez bloku fabryki zostaje nietknięty; nowy nie powstaje")

        # instalator przy aktualizacji zachowuje polecenia dostosowane do projektu
        import importlib.util
        spec = importlib.util.spec_from_file_location("tf_install_t", ROOT / ".tf" / "factory" / "install.py")
        inst = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(inst)
            keep = getattr(inst, "keep_commands", None)
        except Exception as e:  # noqa: BLE001
            keep = None
            fails.append(f"install.py nie daje się zaimportować: {e}")
        fresh = "<!-- team-factory:begin -->" + block.split("<!-- team-factory:begin -->", 1)[1].split("na końcu")[0]
        out = keep(fresh, md) if keep else ""
        check("Test: `uv run pytest`" in out and "npm" not in out and "### Stack" in out,
              f"O-28: aktualizacja zachowuje polecenia wpisane przez tf onboard: {out}")
        out = keep(fresh.replace("### Stack\n- x", "### Stack\n- nowe"), block) if keep else ""
        check("npm test" in out and "dostosuj do swojego projektu" in out and "- nowe" in out,
              f"O-29: niedostosowana sekcja (z dopiskiem „dostosuj”) jest podmieniana na bieżącą: {out}")
        check(keep and keep(fresh, "bez bloku") == fresh, "O-30: pierwszy zapis bloku bez zmian")

        # instalacja prywatna: pliki z tf onboard zostają lokalne, drzewo robocze czyste (Talos tego wymaga)
        if shutil.which("git") and os.name != "nt":
            def git(repo, *a):
                return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=repo,
                                      capture_output=True, text=True)
            for mode in ("private", "shared"):
                p = make(base, f"git-{mode}", {"package.json": NODE, "package-lock.json": "{}"})
                git(p, "init", "-q", "-b", "main")
                git(p, "add", "-A")
                git(p, "commit", "-qm", "init")
                (p / ".claude").mkdir()
                (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"mode": mode}))
                (p / ".git" / "info").mkdir(exist_ok=True)
                with (p / ".git" / "info" / "exclude").open("a") as f:
                    f.write(".claude/factory-manifest.json\n.tf/\n")
                r = run(p, "--yes")
                run(p, "--yes")
                dirty = git(p, "status", "--porcelain", "-uall").stdout.strip()   # -uall: pliki, nie zwinięte katalogi
                excl = (p / ".git" / "info" / "exclude").read_text()
                if mode == "private":
                    check(dirty == "" and excl.count("verify.sh") == 1 and excl.count(".claude/quality-gate.json") == 1
                          and "lokaln" in r.stdout,
                          f"O-31: instalacja prywatna → czyste drzewo, wpisy w .git/info/exclude raz: {dirty!r} {r.stdout[-300:]}")
                else:
                    check("verify.sh" in dirty and "quality-gate.json" in dirty and "verify.sh" not in excl
                          and "Do commita" in r.stdout,
                          f"O-32: instalacja zespołowa → pliki do commita, bez wpisów ignorowania: {dirty!r} {r.stdout[-300:]}")
            p = make(base, "git-tracked", {"package.json": NODE, "verify.sh": "#!/bin/sh\n"})
            git(p, "init", "-q", "-b", "main")
            git(p, "add", "-A")
            git(p, "commit", "-qm", "init")
            (p / ".claude").mkdir()
            (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"mode": "private"}))
            run(p, "--yes")
            excl = (p / ".git" / "info" / "exclude").read_text() if (p / ".git" / "info" / "exclude").exists() else ""
            check("verify.sh" not in excl and ".claude/quality-gate.json" in excl,
                  f"O-33: plik już śledzony przez git nie trafia do wpisów ignorowania: {excl}")

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
