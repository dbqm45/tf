#!/usr/bin/env python3
"""Testy zgodności zmian z planem Talosa (tryb mode-talos, scripts/plan_drift.py): pliki w diffie vs pliki kawałków
z plan.md, zmiany spoza planu, kawałki bez zmian, testy w diffie. python3 .claude/tests/test_plan_drift.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "talos-story-run" / "scripts" / "plan_drift.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL).is_file()), None)
SCRIPT = ROOT / REL if ROOT else None

PLAN = """# Plan
- [x] K1 — eksport CSV · kryteria: test_export_csv · pliki: src/export/csv.py, tests/test_export.py · weryfikacja: `pytest -q` · kto: std
- [x] K2 — przycisk w UI · kryteria: e2e · pliki: web/src/export/ · weryfikacja: `npm test` · kto: std
- [ ] K3 — limit rozmiaru · kryteria: test_limit · pliki: src/export/limits.py · weryfikacja: `pytest -q` · kto: std
"""


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t"})


def write(root: Path, rel: str, text: str = "x\n") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def run(*args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=60)


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
        repo = Path(d)
        git(repo, "init", "-q", "-b", "main")
        write(repo, "README.md")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "init")
        git(repo, "checkout", "-qb", "story/export")
        run_dir = repo / ".claude" / "runs" / "2026-10-23-export"
        write(repo, ".claude/runs/2026-10-23-export/plan.md", PLAN)
        for f in ("src/export/csv.py", "tests/test_export.py", "web/src/export/Button.tsx", "src/util/helpers.py"):
            write(repo, f)
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "work")
        r = run(str(run_dir), "--base", "main", "--json", cwd=repo)
        check(r.returncode == 0, f"P-1: działa: {r.stdout}{r.stderr}")
        out = json.loads(r.stdout) if r.returncode == 0 else {}
        sl = {s["id"]: s for s in out.get("slices", [])}
        check(set(sl) == {"K1", "K2", "K3"} and sl["K1"]["done"] and not sl["K3"]["done"], f"P-2: kawałki i stan: {sl}")
        check(sorted(sl.get("K1", {}).get("touched", [])) == ["src/export/csv.py", "tests/test_export.py"],
              f"P-3: pliki kawałka K1 w diffie: {sl.get('K1')}")
        check(sl.get("K2", {}).get("touched") == ["web/src/export/Button.tsx"], f"P-4: katalog w planie obejmuje pliki: {sl.get('K2')}")
        check(sl.get("K3", {}).get("missing") == ["src/export/limits.py"], f"P-5: nietknięte pliki planu: {sl.get('K3')}")
        check(out.get("unplanned") == ["src/util/helpers.py"], f"P-6: zmiany spoza planu (bez .claude/runs): {out.get('unplanned')}")
        check(out.get("coverage") == 75 and out.get("tests_changed") == 1, f"P-7: pokrycie planem 3/4 i testy: {out}")
        r = run(str(run_dir), "--base", "main", cwd=repo)
        check(r.returncode == 0 and "spoza planu" in r.stdout and "src/util/helpers.py" in r.stdout and "75%" in r.stdout,
              f"P-8: tekst: {r.stdout}")
        r = run(str(repo / "nie-ma"), cwd=repo)
        check(r.returncode == 2, "P-9: brak katalogu przebiegu → kod 2")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów plan_drift")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
