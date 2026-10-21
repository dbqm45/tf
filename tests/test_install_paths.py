#!/usr/bin/env python3
"""Testy instalatora: ścieżki testów fabryki (`tests/` → `.claude/tests/`) przepisywane tylko tam, gdzie chodzi
o testy fabryki (workflow CI, ustawienia), a nie w treści skilli i scenariuszy, gdzie `tests/` to testy projektu.
python3 tests/test_install_paths.py"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        src = Path(t) / "src"
        shutil.copytree(ROOT / "core", src / "core", ignore=shutil.ignore_patterns("__pycache__"))
        major = int((src / "core" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0])
        pack = src / "packs" / "pack-a"
        write(pack / "pack.yaml", f"id: pack-a\nversion: 1.0.0\ntitle: A\ndescription: A test.\n"
                                  f"requires: {{core: \">={major}.0.0 <{major + 1}.0.0\"}}\n"
                                  "facets:\n  - {prefix: aa-, order: 900, name: a, question: \"a\"}\n")
        write(pack / "skills" / "aa-run" / "SKILL.md",
              "---\nname: aa-run\ndescription: Użyj przy A.\nmetadata:\n  katalog: \"Użyj przy A. Nie do niczego.\"\n"
              "  przeglad: 2099-01-01\n---\n# aa-run\nPrzykład: `python3 tests/test_orders.py`\n")
        write(pack / "skills" / "aa-run" / "references" / "przyklady.md", "```python\n# tests/test_discount.py\n```\n")
        write(pack / "tests" / "skill_evals" / "aa-run.json",
              json.dumps({"skill": "aa-run", "scenarios": [{"id": "x", "expect": "trigger",
                                                             "prompt": "W tests/test_discount.py mam kopie testu."}]}))
        proj = Path(t) / "proj"
        proj.mkdir()
        r = subprocess.run([sys.executable, str(src / "core" / "factory" / "install.py"), str(proj), "--yes",
                            "--shared", "--packs", "pack-a"], capture_output=True, text=True, timeout=300)
        check(r.returncode == 0, f"I-1: instalacja: {r.stdout[-600:]} {r.stderr[-300:]}")
        skill = proj / ".claude" / "skills" / "aa-run"
        read = lambda p: p.read_text(encoding="utf-8") if p.exists() else ""
        check("python3 tests/test_orders.py" in read(skill / "SKILL.md"),
              f"I-2: SKILL.md bez zmian ścieżek testów projektu: {read(skill / 'SKILL.md')[-120:]}")
        check("# tests/test_discount.py" in read(skill / "references" / "przyklady.md"),
              f"I-3: przykłady w references bez zmian: {read(skill / 'references' / 'przyklady.md')}")
        check("W tests/test_discount.py" in read(proj / ".claude" / "tests" / "skill_evals" / "aa-run.json"),
              "I-4: scenariusz ewaluacji bez zmian")
        wf = read(proj / ".github" / "workflows" / "team-factory.yml")
        check(".claude/tests/test_hooks.py" in wf and " tests/test_hooks.py" not in wf,
              "I-5: workflow CI fabryki uruchamia testy z .claude/tests/")
        sett = read(proj / ".claude" / "settings.json")
        check("python3 .claude/tests/test_cleanroom.py" in sett, "I-6: uprawnienie do testu fabryki w .claude/tests/")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów ścieżek instalatora")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
