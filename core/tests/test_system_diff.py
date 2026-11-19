#!/usr/bin/env python3
"""System diff (`.tf/factory/system_diff.py`, `tf diff`) on artificial git repositories.

python3 tests/test_system_diff.py

A branch diff against the base → per category (behavior, user interface, data, API contract, dependencies, configuration,
operations, documentation) what the change touches beyond code lines. Only categories with changes appear. Deterministic,
no model and no network; informative (exit code 0), 2 on a call error. Patterns: `system_diff` in config.yaml.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory").is_dir())
ENGINE = ROOT / ".tf" / "factory"
SCRIPT = ENGINE / "system_diff.py"


def git(repo: Path, *args) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.com"}
    return subprocess.run(["git", "-C", str(repo), *args], env=env, capture_output=True, text=True,
                          check=True).stdout.strip()


def write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


BASE_FILES = {
    "README.md": "# app\n",
    "src/app.py": "def run():\n    return 1\n",
    "tests/test_app.py": "def test_run():\n    assert True\n",
    "package.json": json.dumps({"dependencies": {"left-pad": "1.0.0", "react": "17.0.0"},
                                "devDependencies": {"jest": "29.0.0"}}, indent=1) + "\n",
    "package-lock.json": "{}\n",
    "api/openapi.json": json.dumps({"openapi": "3.0.0", "paths": {"/users": {"get": {}}}}, indent=1) + "\n",
    "web/locales/en.json": json.dumps({"hello": "Hello", "bye": "Bye"}, indent=1) + "\n",
    ".env.example": "DB_URL=x\n",
}

CHANGES = {
    "src/app.py": "def run():\n    return 2\n",
    "src/reports/build.py": "def build():\n    return 1\n",
    "tests/test_app.py": "def test_run():\n    assert True\n\n\ndef test_new():\n    assert 1\n",
    "tests/test_reports.py": "def test_r():\n    assert 1\n",
    "web/Button.tsx": "export const B = () => null;\n",
    "web/button.scss": ".b { color: red; }\n",
    "web/locales/en.json": json.dumps({"hello": "Hello", "welcome": "Welcome", "thanks": "Thanks"}, indent=1) + "\n",
    "migrations/002_drop.sql": "ALTER TABLE users DROP COLUMN age;\n",
    "api/openapi.json": json.dumps({"openapi": "3.0.0", "paths": {"/users": {"get": {}}, "/orders": {"get": {}}}},
                                   indent=1) + "\n",
    "package.json": json.dumps({"dependencies": {"react": "18.0.0", "axios": "1.6.0"},
                                "devDependencies": {"jest": "29.0.0"}}, indent=1) + "\n",
    "package-lock.json": '{"x": 1}\n',
    ".env.example": "DB_URL=x\nSTRIPE_KEY=\n",
    ".github/workflows/ci.yml": "on: push\n",
    "docs/guide.md": "# guide\n",
}


def repo_with(t: Path, name: str, changes: dict, deletes=()) -> Path:
    repo = t / name
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for rel, txt in BASE_FILES.items():
        write(repo, rel, txt)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    git(repo, "checkout", "-q", "-b", "feature")
    for rel, txt in changes.items():
        write(repo, rel, txt)
    for rel in deletes:
        (repo / rel).unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", "change")
    return repo


def run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True, timeout=60,
                          encoding="utf-8")


def bullet(md: str, label: str) -> str:
    return next((ln for ln in md.splitlines() if ln.startswith(f"- **{label}**")), "")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    check(SCRIPT.is_file(), f"SD-0: the engine script exists: {SCRIPT}")
    with tempfile.TemporaryDirectory() as d:
        t = Path(d)
        repo = repo_with(t, "all", CHANGES)
        r = run(repo, "--base", "main", "--md")
        md = r.stdout
        check(r.returncode == 0 and md.startswith("## System diff"),
              f"SD-1: --md: code 0 and the header: {r.returncode} {md[:80]} {r.stderr[-200:]}")
        beh = bullet(md, "Behavior")
        check("2 source files" in beh and "`src/reports/`" in beh and "tests: +1 file" in beh and "+2 tests" in beh,
              f"SD-2: behavior (source files, a new module, tests): {beh}")
        ui = bullet(md, "User interface")
        check("`web/Button.tsx`" in ui and "`web/button.scss`" in ui and "`web/locales/en.json`" in ui
              and "+2/-1 keys" in ui, f"SD-3: user interface incl. i18n keys: {ui}")
        data = bullet(md, "Data")
        check("`migrations/002_drop.sql`" in data and "destructive" in data and "DROP COLUMN" in data,
              f"SD-4: data, destructive SQL flagged: {data}")
        api = bullet(md, "API contract")
        check("`api/openapi.json`" in api and "+`/orders`" in api, f"SD-5: API contract with an added path: {api}")
        deps = bullet(md, "Dependencies")
        check("package.json" in deps and "+`axios`" in deps and "-`left-pad`" in deps
              and "`react` 17.0.0→18.0.0" in deps and "devDependencies" not in deps and "lockfile" not in deps,
              f"SD-6: dependencies: added, removed, upgraded: {deps}")
        cfg = bullet(md, "Configuration")
        check("`.env.example`" in cfg and "STRIPE_KEY" in cfg, f"SD-7: configuration, a new variable: {cfg}")
        ops = bullet(md, "Operations")
        check("`.github/workflows/ci.yml`" in ops, f"SD-8: operations: {ops}")
        doc = bullet(md, "Documentation")
        check("1 file" in doc, f"SD-9: documentation (count only): {doc}")
        order = [md.find(f"**{x}**") for x in ("Behavior", "User interface", "Data", "API contract", "Dependencies",
                                               "Configuration", "Operations", "Documentation")]
        check(all(x >= 0 for x in order) and order == sorted(order), f"SD-10: fixed category order: {order}")

        # SD-11: --json — the same data, structured
        r = run(repo, "--base", "main", "--json")
        try:
            js = json.loads(r.stdout)
            cats = js["categories"]
            ok = (r.returncode == 0 and js["base"] == "main"
                  and set(cats) == {"behavior", "ui", "data", "api", "deps", "config", "ops", "docs"}
                  and cats["data"]["destructive"] and cats["deps"]["changes"][0]["file"] == "package.json"
                  and "STRIPE_KEY" in cats["config"]["env_added"])
        except (ValueError, KeyError, IndexError, TypeError):
            ok = False
        check(ok, f"SD-11: --json structure: {r.stdout[:300]} {r.stderr[-200:]}")

        # SD-12: a docs-only change — only Documentation
        repo = repo_with(t, "docs", {"README.md": "# app\n\nmore\n", "docs/a.md": "x\n"})
        md = run(repo, "--base", "main", "--md").stdout
        bullets = [ln for ln in md.splitlines() if ln.startswith("- **")]
        check(len(bullets) == 1 and bullets[0].startswith("- **Documentation**") and "2 files" in bullets[0],
              f"SD-12: docs only → only Documentation: {md}")

        # SD-13: lockfile-only; SD-14: a deleted test file
        repo = repo_with(t, "lock", {"package-lock.json": '{"y": 2}\n'})
        deps = bullet(run(repo, "--base", "main", "--md").stdout, "Dependencies")
        check("lockfile only" in deps and "`package-lock.json`" in deps, f"SD-13: lockfile-only change: {deps}")
        repo = repo_with(t, "removed", {}, deletes=("tests/test_app.py",))
        beh = bullet(run(repo, "--base", "main", "--md").stdout, "Behavior")
        check("tests: -1 file" in beh and "-1 test" in beh, f"SD-14: a deleted test file: {beh}")

        # SD-15: more than 5 sub-items → "… +N more"
        many = {f"web/c{i}.tsx": "x\n" for i in range(8)}
        ui = bullet(run(repo_with(t, "many", many), "--base", "main", "--md").stdout, "User interface")
        check("… +3 more" in ui and ui.count("`web/c") == 5, f"SD-15: the cap of 5 sub-items: {ui}")

        # SD-16: no changes → a header and no bullets; SD-17/18: unknown base, not a repository → code 2
        repo = repo_with(t, "empty", {})
        r = run(repo, "--base", "main", "--md")
        check(r.returncode == 0 and "## System diff" in r.stdout and "- **" not in r.stdout,
              f"SD-16: no changes: {r.returncode} {r.stdout}")
        r = run(repo, "--base", "no-such-branch", "--md")
        check(r.returncode == 2 and r.stderr.strip(), f"SD-17: unknown base → code 2: {r.returncode} {r.stderr}")
        plain = t / "plain"
        plain.mkdir()
        r = run(plain, "--md")
        check(r.returncode == 2, f"SD-18: not a git repository → code 2: {r.returncode}")

        # SD-19: a project override of the patterns (.tf/config/config.yaml: system_diff)
        repo = repo_with(t, "custom", {"src/tariffs/calc.py": "def calc():\n    return 0\n"})
        write(repo, ".tf/config/config.yaml", "system_diff:\n  ops:\n    - '(^|/)tariffs/'\n")
        md = run(repo, "--base", "main", "--md").stdout
        check("`src/tariffs/calc.py`" in bullet(md, "Operations"), f"SD-19: a project pattern override: {md}")

        # SD-20: a config file under config/
        repo = repo_with(t, "flags", {"config/flags.json": json.dumps({"test": {"new-ui": True}}) + "\n"})
        md = run(repo, "--base", "main", "--md").stdout
        check("`config/flags.json`" in bullet(md, "Configuration"), f"SD-20: a config file under config/: {md}")

        # SD-22: feature flags of the operations card
        card = {"flags": {"file": "config/flags.json", "envs": ["test", "prod"]}}
        repo = repo_with(t, "card", {"config/flags.json": json.dumps({"test": {"new-ui": True}}) + "\n",
                                     ".tf/config/operations.json": json.dumps(card)})
        md = run(repo, "--base", "main", "--md").stdout
        check("flags +`new-ui@test`" in bullet(md, "Configuration"), f"SD-22: a new feature flag: {md}")

    tf = (ENGINE / "tf.py").read_text(encoding="utf-8")
    check("tf diff" in tf.split('"""')[1] and '"diff"' in tf, "SD-21: tf diff in the help and the launcher dispatch")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} system diff: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
