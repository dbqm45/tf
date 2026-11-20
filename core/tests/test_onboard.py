#!/usr/bin/env python3
"""`tf onboard` tests (.tf/factory/onboard.py): detecting the project's commands from files, a readiness report in plain language,
writing `.claude/quality-gate.json` — without running anything in the project. python3 tests/test_onboard.py"""
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
        print(f"✗ missing {ONBOARD}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = make(base, "npm", {"package.json": NODE, "package-lock.json": "{}", ".gitignore": "node_modules\n",
                               ".github/workflows/ci.yml": "on: push\n"})
        d = detected(p)
        check(cmds(d) == {"test": "npm test", "lint": "npm run lint", "typecheck": "npm run typecheck",
                          "build": "npm run build"}, f"O-1: package.json scripts -> npm commands: {d}")
        check(d.get("verdict") == "ready" and not (p / ".claude").exists() and not (p / ".tf").exists(),
              f"O-2: complete -> the 'ready' verdict; --json writes nothing: {d.get('verdict')}")

        p = make(base, "notest", {"package.json": {"scripts": {"test": 'echo "Error: no test specified" && exit 1'}}})
        r = run(p, "--json")
        d = json.loads(r.stdout)
        check("test" not in cmds(d) and d.get("verdict") == "no-tests" and r.returncode == 1,
              f"O-3: the default npm script is not tests -> the no-tests verdict, code 1: {r.returncode} {d}")

        p = make(base, "pnpm", {"package.json": NODE, "pnpm-lock.yaml": ""})
        check(cmds(detected(p)).get("test") == "pnpm test" and cmds(detected(p)).get("lint") == "pnpm run lint",
              f"O-4: pnpm-lock.yaml -> pnpm: {cmds(detected(p))}")

        p = make(base, "py", {"pyproject.toml": '[project]\nname = "x"\n[tool.pytest.ini_options]\n[tool.ruff]\n'
                                                '[tool.mypy]\n', "uv.lock": "", "tests/test_a.py": "def test_a(): pass\n"})
        check(cmds(detected(p)) == {"test": "uv run pytest", "lint": "uv run ruff check .", "typecheck": "uv run mypy ."},
              f"O-5: pyproject with pytest, ruff, mypy and uv.lock: {cmds(detected(p))}")

        p = make(base, "go", {"go.mod": "module x\n\ngo 1.23\n", "go.sum": ""})
        check(cmds(detected(p)) == {"test": "go test ./...", "lint": "go vet ./...", "build": "go build ./..."},
              f"O-6: go.mod: {cmds(detected(p))}")

        p = make(base, "mvn", {"pom.xml": "<project/>", "mvnw": "#!/bin/sh\n"})
        check(cmds(detected(p)).get("test") == "./mvnw -q test", f"O-7: pom.xml z mvnw: {cmds(detected(p))}")

        p = make(base, "make", {"Makefile": "test:\n\tpytest\nlint:\n\truff check .\n.PHONY: test lint\n"})
        check(cmds(detected(p)) == {"test": "make test", "lint": "make lint"}, f"O-8: a Makefile as a fallback: {cmds(detected(p))}")

        p = make(base, "empty", {"README.md": "# x\n"})
        r = run(p, "--json")
        check(r.returncode == 1 and json.loads(r.stdout).get("verdict") == "no-tests",
              f"O-9: nothing detected -> no-tests, no exception: {r.stdout}{r.stderr}")

        # writing: only with --yes; an existing gate configuration is not overwritten
        p = make(base, "write", {"package.json": NODE, "package-lock.json": "{}"})
        r = run(p)
        check(r.returncode == 0 and not (p / ".claude" / "quality-gate.json").exists() and "--yes" in r.stdout
              and "npm test" in r.stdout, f"O-10: without --yes and without a terminal only a proposal: {r.stdout}{r.stderr}")
        r = run(p, "--yes")
        gate = p / ".claude" / "quality-gate.json"
        report = p / ".tf" / "reports" / "readiness.md"
        want = "npm test" if os.name == "nt" else "./verify.sh"
        check(r.returncode == 0 and gate.is_file() and json.loads(gate.read_text()).get("command") == want,
              f"O-11: --yes writes the verification command to the gate ({want}): {r.stdout}{r.stderr}")
        text = report.read_text(encoding="utf-8") if report.is_file() else ""
        check(all(h in text for h in ("## What is there", "## What is missing", "## What the factory blocks", "## When a human should look")),
              f"O-12: the readiness report has fixed sections: {text[:300]}")
        blocking = text.split("## What the factory blocks", 1)[-1].split("## ", 1)[0]
        n = sum(1 for ln in blocking.splitlines() if ln.startswith("- "))
        check(1 <= n <= 5, f"O-13: at most five blocking checks ({n}): {blocking}")
        check(not any(w in text.lower() for w in ("hook", "tier", "harness", "triaż")),
              "O-14: a human-facing report without factory-internals vocabulary")
        gate.write_text(json.dumps({"command": "npm run test:ci", "watch": ["src/"]}))
        r = run(p, "--yes")
        check(json.loads(gate.read_text()).get("command") == "npm run test:ci" and "stays unchanged" in r.stdout,
              f"O-15: an existing gate configuration stays, with a note: {r.stdout}")
        r = run(p, "--dry-run", "--yes")
        check(r.returncode == 0 and "npm test" in r.stdout, f"O-16: --dry-run shows the proposal: {r.stdout}{r.stderr}")

        p = make(base, "dry", {"package.json": NODE})
        r = run(p, "--dry-run", "--yes")
        check(not (p / ".claude").exists() and not (p / ".tf").exists(), "O-17: --dry-run writes nothing")
        check("lockfile" not in r.stdout.lower() or "no dependency lockfile" in r.stdout.lower(), f"O-18: a missing version lock file is named: {r.stdout}")

        # part 2: one verification command (lint, types, tests), commands in the instructions file, a trial run on request
        if os.name != "nt":
            p = make(base, "verify", {"package.json": NODE, "package-lock.json": "{}"})
            run(p, "--yes")
            v = p / "verify.sh"
            body = v.read_text(encoding="utf-8") if v.is_file() else ""
            order = [body.find(c) for c in ("npm run lint", "npm run typecheck", "npm test")]
            check(v.is_file() and os.access(v, os.X_OK) and -1 not in order and order == sorted(order)
                  and "set -e" in body and "npm run build" not in body,
                  f"O-21: verify.sh executable, in the order lint -> types -> tests, without build: {body}")
            text = (p / ".tf" / "reports" / "readiness.md").read_text(encoding="utf-8")
            blocking = text.split("## What the factory blocks", 1)[-1].split("## ", 1)[0]
            n = sum(1 for ln in blocking.splitlines() if ln.startswith("- "))
            check(n == 5 and "npm run lint" in blocking and "npm run typecheck" in blocking and "Only warns" in text
                  and "npm run build" in text.split("Only warns", 1)[-1],
                  f"O-22: lint and types block (five checks in all), build only warns: {blocking}")

            p = make(base, "own-verify", {"package.json": NODE, "verify.sh": "#!/bin/sh\necho moje\n"})
            r = run(p, "--yes")
            check((p / "verify.sh").read_text() == "#!/bin/sh\necho moje\n" and "stays unchanged" in r.stdout
                  and json.loads((p / ".claude" / "quality-gate.json").read_text()).get("command") == "./verify.sh",
                  f"O-23: an existing verify.sh stays and is the gate command: {r.stdout}")

            p = make(base, "run", {"Makefile": "test:\n\t@echo testy-ok\nlint:\n\t@echo lint-ok\n"})
            if shutil.which("make"):
                r = run(p, "--yes", "--verify")
                check(r.returncode == 0 and "Verification passes" in r.stdout, f"O-24: --verify runs the verification once, green: {r.stdout}{r.stderr}")
                (p / "Makefile").write_text("test:\n\t@echo FAILED test_x; exit 1\nlint:\n\t@echo lint-ok\n")
                r = run(p, "--yes", "--verify")
                check(r.returncode == 1 and "does not pass" in r.stdout and "FAILED test_x" in r.stdout,
                      f"O-25: --verify with red tests -> code 1 and the end of the output: {r.stdout}{r.stderr}")
                (p / "gen.py").write_text("import sys\nprint('PIERWSZY-BLAD')\nfor i in range(300):\n"
                                          "    print(f'linia-{i}-' + 'x' * 20)\nprint('PODSUMOWANIE-1-failed')\nsys.exit(1)\n")
                (p / "Makefile").write_text(f"test:\n\t@{sys.executable} gen.py\nlint:\n\t@echo lint-ok\n")
                r = run(p, "--yes", "--verify")
                saved = p / ".tf" / "logs" / "verify-output.txt"
                check(r.returncode == 1 and "PIERWSZY-BLAD" in r.stdout and "PODSUMOWANIE-1-failed" in r.stdout
                      and "linia-150-" not in r.stdout and "skipped" in r.stdout and ".tf/logs/verify-output.txt" in r.stdout
                      and saved.is_file() and "linia-150-" in saved.read_text(encoding="utf-8"),
                      f"O-34: long --verify output -> the beginning and the end on screen, all of it in a file: {r.stdout[-400:]}")

        block = ("moje zasady\n\n<!-- team-factory:begin -->\n## Agent team (team factory)\n\n### Commands\n"
                 "- Test: `npm test` · Lint: `npm run lint` · Typecheck: `npm run typecheck` · Build: `npm run build`\n"
                 "  (adapt to your project — executors use them for verification)\n\n### Stack\n- x\n"
                 "<!-- team-factory:end -->\nna końcu\n")
        p = make(base, "md", {"pyproject.toml": "[tool.pytest.ini_options]\n[tool.ruff]\n", "uv.lock": "",
                              "CLAUDE.local.md": block})
        r = run(p, "--yes")
        md = (p / "CLAUDE.local.md").read_text(encoding="utf-8")
        check("Test: `uv run pytest`" in md and "Lint: `uv run ruff check .`" in md and "npm" not in md
              and "adapt to your project" not in md and md.startswith("moje zasady\n") and md.endswith("na końcu\n")
              and "### Stack\n- x" in md and "CLAUDE.local.md" in r.stdout,
              f"O-26: the project's commands in the 'Commands' section of the factory block, the rest of the file unchanged: {md}")
        p = make(base, "nomd", {"pyproject.toml": "[tool.pytest.ini_options]\n", "CLAUDE.md": "# moje\n"})
        run(p, "--yes")
        check((p / "CLAUDE.md").read_text() == "# moje\n" and not (p / "CLAUDE.local.md").exists(),
              "O-27: an instructions file without the factory block stays untouched; no new one is created")

        # on update the installer keeps commands adapted to the project
        import importlib.util
        spec = importlib.util.spec_from_file_location("tf_install_t", ROOT / ".tf" / "factory" / "install.py")
        inst = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(inst)
            keep = getattr(inst, "keep_commands", None)
        except Exception as e:  # noqa: BLE001
            keep = None
            fails.append(f"install.py cannot be imported: {e}")
        fresh = "<!-- team-factory:begin -->" + block.split("<!-- team-factory:begin -->", 1)[1].split("na końcu")[0]
        out = keep(fresh, md) if keep else ""
        check("Test: `uv run pytest`" in out and "npm" not in out and "### Stack" in out,
              f"O-28: an update keeps the commands written by tf onboard: {out}")
        out = keep(fresh.replace("### Stack\n- x", "### Stack\n- nowe"), block) if keep else ""
        check("npm test" in out and "adapt to your project" in out and "- nowe" in out,
              f"O-29: an unadapted section (with the 'adapt to your project' note) is replaced with the current one: {out}")
        out = keep(fresh.replace("`npm test`", "`pnpm test`"), block) if keep else ""
        check("pnpm test" in out and "`npm test`" not in out,
              f"O-29b: the template commands come from the new block, not the old template: {out}")
        check(keep and keep(fresh, "bez bloku") == fresh, "O-30: the first write of the block unchanged")

        # private installation: the files from tf onboard stay local, the working tree clean (the /tf loop requires it)
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
                dirty = git(p, "status", "--porcelain", "-uall").stdout.strip()   # -uall: files, not collapsed directories
                excl = (p / ".git" / "info" / "exclude").read_text()
                if mode == "private":
                    check(dirty == "" and excl.count("verify.sh") == 1 and excl.count(".claude/quality-gate.json") == 1
                          and "stay local" in r.stdout,
                          f"O-31: private installation -> a clean tree, entries in .git/info/exclude once: {dirty!r} {r.stdout[-300:]}")
                else:
                    check("verify.sh" in dirty and "quality-gate.json" in dirty and "verify.sh" not in excl
                          and "To commit" in r.stdout,
                          f"O-32: team installation -> files to commit, no ignore entries: {dirty!r} {r.stdout[-300:]}")
            p = make(base, "git-tracked", {"package.json": NODE, "verify.sh": "#!/bin/sh\n"})
            git(p, "init", "-q", "-b", "main")
            git(p, "add", "-A")
            git(p, "commit", "-qm", "init")
            (p / ".claude").mkdir()
            (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"mode": "private"}))
            run(p, "--yes")
            excl = (p / ".git" / "info" / "exclude").read_text() if (p / ".git" / "info" / "exclude").exists() else ""
            check("verify.sh" not in excl and ".claude/quality-gate.json" in excl,
                  f"O-33: a file already tracked by git does not go into the ignore entries: {excl}")

        # the operations card gets a `preview` entry (for the visual check) only for a web frontend
        for name, pkg, url, start in (
                ("vite", {"scripts": {"dev": "vite", "test": "vitest run"}, "devDependencies": {"vite": "^5"}},
                 "http://localhost:5173", "npm run dev"),
                ("ng", {"scripts": {"start": "ng serve", "test": "ng test"}, "dependencies": {"@angular/core": "^17"}},
                 "http://localhost:4200", "npm start")):
            p = make(base, f"web-{name}", {"package.json": pkg})
            r = run(p, "--yes")
            try:
                prev = json.loads((p / ".tf" / "config" / "operations.json").read_text(encoding="utf-8")).get("preview")
            except (OSError, ValueError):
                prev = None
            check(prev == {"url": url, "start": start, "routes": ["/"]}, f"O-40: preview entry for {name}: {prev} {r.stdout[-200:]}")
        p = make(base, "web-card", {"package.json": {"scripts": {"dev": "vite"}, "devDependencies": {"vite": "^5"}},
                                    ".tf/config/operations.json": {"flags": {"file": None}, "deploy": {"smoke": "x"},
                                                                   "tracker": {"type": "jira"}}})
        run(p, "--yes")
        card = json.loads((p / ".tf" / "config" / "operations.json").read_text(encoding="utf-8"))
        check(card.get("tracker") == {"type": "jira"} and card.get("deploy") == {"smoke": "x"} and "preview" in card,
              f"O-41: an existing card keeps its keys and gets the missing preview: {card}")
        card["preview"]["url"] = "http://localhost:9999"
        (p / ".tf" / "config" / "operations.json").write_text(json.dumps(card), encoding="utf-8")
        run(p, "--yes")
        card = json.loads((p / ".tf" / "config" / "operations.json").read_text(encoding="utf-8"))
        check(card["preview"]["url"] == "http://localhost:9999", f"O-42: an existing preview entry is not overwritten: {card}")
        p = make(base, "not-web", {"package.json": NODE})
        run(p, "--yes")
        card = json.loads((p / ".tf" / "config" / "operations.json").read_text(encoding="utf-8"))
        check("preview" not in card, f"O-43: a project that is not a web frontend gets no preview entry: {card}")

        # tf onboard passes its arguments to the script in the project
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
        check(ok, f"O-19: tf onboard runs .tf/factory/onboard.py: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(CTF), "onboard"], cwd=base / "empty", capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=60)
        check(r.returncode == 2 and "tf install" in r.stdout, f"O-20: without the factory in the directory -> an install hint: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tf onboard tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
