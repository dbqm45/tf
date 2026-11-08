#!/usr/bin/env python3
"""Moduły tf analyze z pack-it (security, architecture): obecne po instalacji, przechodzą bramkę na swoich zestawach
testowych, sekret nie trafia do raportu. python3 .claude/tests/test_analyzers.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
ANALYZE = ROOT / ".tf" / "factory" / "analyze.py"
MODS = ROOT / ".tf" / "factory" / "analyzers"
SECRET = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"


def git(repo, *args):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false", *args],
                   cwd=repo, check=True, capture_output=True)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    for name in ("security", "architecture"):
        check((MODS / name / "analyzer.yaml").is_file(), f"Z-1: moduł {name} zainstalowany w .tf/factory/analyzers/")
        r = subprocess.run([sys.executable, str(ANALYZE), "gate", "--module", name], cwd=ROOT, capture_output=True,
                           text=True, timeout=300)
        check(r.returncode == 0 and r.stdout.startswith("Werdykt: OK"),
              f"Z-2: moduł {name} przechodzi bramkę: {r.stdout}{r.stderr}")
    r = subprocess.run([sys.executable, str(ANALYZE), "list"], cwd=ROOT, capture_output=True, text=True, timeout=120)
    check("security" in r.stdout and "architecture" in r.stdout, f"Z-3: tf analyze --list pokazuje moduły: {r.stdout}")

    with tempfile.TemporaryDirectory() as t:
        repo = Path(t) / "proj"
        (repo / "src").mkdir(parents=True)
        (repo / ".tf").mkdir()
        (repo / ".tf" / "factory").symlink_to(ROOT / ".tf" / "factory")
        (repo / ".claude").mkdir()
        (repo / ".claude" / "hooks").symlink_to(ROOT / ".claude" / "hooks")
        (repo / ".claude" / "skills").symlink_to(ROOT / ".claude" / "skills")
        (repo / ".claude" / "factory-manifest.json").write_text(json.dumps({"mode": "private"}))
        (repo / "src" / "conf.py").write_text(f'TOKEN = "{SECRET}"\n')
        (repo / "tests").mkdir()
        (repo / "tests" / "test_conf.py").write_text(f'FAKE = "{SECRET}"\n')
        (repo / ".gitignore").write_text(".tf/\n.claude/\n")
        git(repo, "init", "-q", "-b", "main")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "init")
        r = subprocess.run([sys.executable, str(ANALYZE), "run", "--only", "security"], cwd=repo, capture_output=True,
                           text=True, timeout=300)
        rep = repo / ".tf" / "reports" / "security.md"
        body = rep.read_text() if rep.is_file() else ""
        js = (repo / ".tf" / "reports" / "security.json").read_text() if rep.is_file() else ""
        check(r.returncode == 0 and "secret" in js and "src/conf.py" in body,
              f"Z-4: sekret w kodzie znaleziony: {r.stdout}{r.stderr} {body[:500]}")
        found = json.loads(js).get("findings", []) if js else []
        sev = {f["file"]: f["severity"] for f in found if f["rule"] == "secret"}
        check(sev.get("src/conf.py") == "krytyczna" and sev.get("tests/test_conf.py") == "niska",
              f"Z-6: sekret w pliku testowym zgłaszany z niską wagą, w kodzie — krytyczną: {sev}")
        check(SECRET not in body and SECRET not in js and SECRET[8:] not in js,
              "Z-5: wartość sekretu nie trafia do raportu ani do .json")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów modułów analizy pack-it")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
