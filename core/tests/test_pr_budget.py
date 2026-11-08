#!/usr/bin/env python3
"""Testy `.claude/skills/core-delivery-lifecycle/scripts/pr_budget.py` (budżet artefaktów w PR: udział artefaktów
w dodanych liniach, rozmiar pojedynczego artefaktu i planu) w tymczasowym repozytorium git. python3 tests/test_pr_budget.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "core-delivery-lifecycle" / "scripts" / "pr_budget.py"


def git(repo, *args):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=repo, check=True,
                   capture_output=True)


def lines(n: int, word="linia") -> str:
    return "".join(f"{word} {i}\n" for i in range(n))


def repo_with(tmp: Path, files: dict) -> Path:
    repo = tmp
    repo.mkdir(parents=True)
    (repo / "README.md").write_text("# r\n")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    git(repo, "checkout", "-qb", "feature")
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "change")
    return repo


def run(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--base", "main", *args], cwd=repo, capture_output=True,
                          text=True, timeout=60)


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    if not SCRIPT.is_file():
        print(f"✗ brak {SCRIPT}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        ok = repo_with(t / "ok", {"src/app.py": lines(120), "docs/project/changes/CHG-1/runs/TSK-1.md": lines(40)})
        r = run(ok)
        check(r.returncode == 0 and r.stdout.startswith("Werdykt: OK") and "120" in r.stdout and "40" in r.stdout,
              f"P-1: mało artefaktów → OK, kod 0, liczby kodu i artefaktów: {r.stdout}{r.stderr}")

        noisy = repo_with(t / "noisy", {"src/app.py": lines(95), "docs/project/changes/CHG-1/plan.md": lines(150),
                                        "docs/test/evidence/01-run.txt": lines(250)})
        r = run(noisy)
        check(r.returncode == 1 and r.stdout.startswith("Werdykt: PRZEKROCZONY") and "%" in r.stdout,
              f"P-2: artefakty > 50% dodanych linii przy zmianie kodu → przekroczony: {r.stdout}{r.stderr}")

        big = repo_with(t / "big", {"src/app.py": lines(2000), "docs/project/02-domain/notatki.md": lines(700),
                                    "docs/project/changes/CHG-2/plan.md": lines(320)})
        r = run(big)
        check(r.returncode == 1 and "notatki.md" in r.stdout and "700" in r.stdout and "plan.md" in r.stdout
              and "320" in r.stdout, f"P-3: artefakt > 600 linii i plan > 300 linii wskazane: {r.stdout}")

        docs = repo_with(t / "docs", {"docs/project/03-requirements/requirements.md": lines(400)})
        r = run(docs)
        check(r.returncode == 0 and r.stdout.startswith("Werdykt: OK"),
              f"P-4: PR bez zmiany kodu (sama dokumentacja) nie podlega limitowi udziału: {r.stdout}")

        cfg = repo_with(t / "cfg", {"src/app.py": lines(50), "reports/run.log": lines(200)})
        r = run(cfg)
        check(r.returncode == 0, f"P-5a: bez konfiguracji reports/ to nie artefakt: {r.stdout}")
        (cfg / ".claude").mkdir()
        (cfg / ".claude" / "pr-budget.json").write_text(json.dumps({"artifacts": ["reports/**"], "max_share": 0.5}))
        r = run(cfg)
        check(r.returncode == 1 and "reports/run.log" in r.stdout, f"P-5b: wzorce artefaktów z .claude/pr-budget.json: {r.stdout}")

        r = run(noisy, "--json")
        try:
            data = json.loads(r.stdout)
        except ValueError:
            data = {}
        check(data.get("verdict") == "PRZEKROCZONY" and data.get("artifact_lines") == 400 and data.get("code_lines") == 95,
              f"P-6: --json z polami verdict, code_lines, artifact_lines: {r.stdout[:300]}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów budżetu artefaktów")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
