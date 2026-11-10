#!/usr/bin/env python3
"""B1b: triaż ryzyka zmian (`tf risk`, .tf/factory/risk_triage.py) na sztucznych repozytoriach git.

python3 tests/test_risk_triage.py

Diff gałęzi względem bazy → poziom high / medium / low i lista „co musi zobaczyć człowiek” (plik, powód).
Wynik doradczy (decyzja człowieka 2026-11-10, D2): nie blokuje merge'a. Reguły domyślne z nadpisaniem w
`.tf/config/config.yaml` (`autonomy.triage`). Bez sieci i bez modelu.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory").is_dir())
ENGINE = ROOT / ".tf" / "factory"


def load():
    spec = importlib.util.spec_from_file_location("tf_risk", ENGINE / "risk_triage.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    "src/auth/session.py": "def check(user):\n    return user.ok\n",
    "tests/test_app.py": "from src.app import run\n\ndef test_run():\n    assert run() == 1\n\ndef test_more():\n    assert True\n",
    "package.json": '{"dependencies": {}}\n',
    "package-lock.json": "{}\n",
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
    git(repo, "commit", "-q", "-m", "change")
    return repo


def reasons(res: dict) -> str:
    return " | ".join(f"{i['level']}:{i['category']}:{i['file']}" for i in res["items"])


def main() -> int:
    fails = []
    m = load()
    with tempfile.TemporaryDirectory() as d:
        t = Path(d)
        cases = [
            # (nazwa, zmiany, usunięte, oczekiwany poziom, kategoria wymagana na liście albo None)
            ("docs", {"README.md": "# app\n\nOpis.\n", "docs/guide.md": "x\n"}, (), "low", None),
            ("deps", {"package.json": '{"dependencies": {"left-pad": "1.3.0"}}\n',
                      "package-lock.json": '{"x": 1}\n'}, (), "low", None),
            ("code", {"src/app.py": "def run():\n    return 2\n"}, (), "medium", None),
            ("auth", {"src/auth/session.py": "def check(user):\n    return True\n"}, (), "high", "auth"),
            ("payments", {"src/billing/refund.py": "def refund(x):\n    return x\n"}, (), "high", "payments"),
            ("schema", {"migrations/0002_add_col.sql": "ALTER TABLE t ADD c int;\n"}, (), "high", "schema"),
            ("deploy", {".github/workflows/ci.yml": "on: push\n", "Dockerfile": "FROM python:3.12\n"}, (), "high",
             "deploy"),
            ("weakened", {"tests/test_app.py": "from src.app import run\n\ndef test_run():\n    pass\n\n"
                                                "def test_more():\n    assert True\n"}, (), "high", "tests-weakened"),
            ("skipped", {"tests/test_app.py": BASE_FILES["tests/test_app.py"]
                         + "\nimport pytest\n\n@pytest.mark.skip\ndef test_x():\n    assert run() == 1\n"}, (),
             "high", "tests-weakened"),
            ("deleted-test", {"src/app.py": "def run():\n    return 3\n"}, ("tests/test_app.py",), "high",
             "tests-weakened"),
            ("spec", {"docs/project/02-requirements/acceptance.feature": "Feature: x\n"}, (), "high", "spec"),
            # pominięcie jako dane (napis w kodzie testu), nie dekorator — bez alarmu; zmiana zwykłego kodu = medium
            ("skip-in-string", {"tests/test_app.py": BASE_FILES["tests/test_app.py"]
                                + "\nSAMPLE = \"@pytest.mark.skip\"\n\ndef test_sample():\n    assert SAMPLE\n"}, (),
             "medium", None),
        ]
        for name, changes, deletes, level, cat in cases:
            repo = repo_with(t, name, changes, deletes)
            res = m.triage(repo, base="main")
            got_cats = {i["category"] for i in res["items"]}
            if res["level"] != level or (cat and cat not in got_cats):
                fails.append(f"R-{name}: poziom {level}{f', kategoria {cat}' if cat else ''}: {res['level']} — "
                             f"{reasons(res)}")
        # R-adr (D3): nowy katalog najwyższego poziomu w kodzie bez ADR → punkt „dowód” na liście (poziom medium)
        repo = repo_with(t, "module", {"src/reports/__init__.py": "", "src/reports/build.py": "def b():\n    pass\n"})
        res = m.triage(repo, base="main")
        if res["level"] != "medium" or not any(i["category"] == "evidence-adr" for i in res["items"]):
            fails.append(f"R-adr: nowy moduł bez ADR → punkt dowodu, poziom medium: {res['level']} {reasons(res)}")
        repo2 = repo_with(t, "module-adr", {"src/reports/build.py": "def b():\n    pass\n",
                                            "docs/adr/0003-reports.md": "# ADR\n"})
        if any(i["category"] == "evidence-adr" for i in m.triage(repo2, base="main")["items"]):
            fails.append("R-adr: nowy moduł z ADR w tej samej zmianie — bez punktu dowodu")
        # R-config: nadpisanie reguł z .tf/config/config.yaml (dodatkowa kategoria high dla ścieżki projektu)
        repo = repo_with(t, "custom", {"src/tariffs/calc.py": "def calc():\n    return 0\n"})
        write(repo, ".tf/config/config.yaml",
              "autonomy:\n  triage:\n    high:\n      ev-pricing:\n        - '(^|/)tariffs/'\n")
        res = m.triage(repo, base="main", rules=m.load_rules(repo))
        if res["level"] != "high" or not any(i["category"] == "ev-pricing" for i in res["items"]):
            fails.append(f"R-config: reguła projektu z .tf/config/config.yaml: {res['level']} {reasons(res)}")
        # R-md: sekcja do opisu PR — poziom, lista z plikiem i powodem, uwaga, że to doradztwo
        md = m.to_markdown(m.triage(repo_with(t, "md", {"src/auth/login.py": "x = 1\n"}), base="main"))
        if "## Ryzyko zmiany: wysokie" not in md or "src/auth/login.py" not in md or "doradcz" not in md:
            fails.append(f"R-md: sekcja opisu PR: {md[:300]}")
        # R-cli: --json bez wyjątku, kod 0 (doradczy — także przy high)
        repo = repo_with(t, "cli", {"src/auth/x.py": "x = 1\n"})
        r = subprocess.run([sys.executable, str(ENGINE / "risk_triage.py"), "--base", "main", "--json"], cwd=repo,
                           capture_output=True, text=True, timeout=60)
        try:
            ok = r.returncode == 0 and json.loads(r.stdout)["level"] == "high"
        except (json.JSONDecodeError, KeyError):
            ok = False
        if not ok:
            fails.append(f"R-cli: --json, kod 0 także przy high: {r.returncode} {r.stdout[:200]} {r.stderr[-300:]}")
    tf = (ENGINE / "tf.py").read_text(encoding="utf-8")
    if "tf risk" not in tf.split('"""')[1] or '"risk"' not in tf:
        fails.append("R-tf: tf risk w pomocy i dyspozycji launchera")
    for f in fails:
        print(f"✗ {f}")
    total = 18
    print(f"{'✓' if not fails else '✗'} triaż ryzyka zmian: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
