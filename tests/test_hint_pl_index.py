#!/usr/bin/env python3
"""Tests of tools/hint_pl_index.py: the Polish hint index from git history for skills translated into English.
python3 tests/test_hint_pl_index.py"""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hint_pl_index", REPO / "tools" / "hint_pl_index.py")
hpi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hpi)

PL = "---\nname: core-x\ndescription: Użyj przy x.\n---\n# Praca w nocy\nAgent zatrzymuje się po dwóch nieudanych próbach naprawy.\n"
EN = "---\nname: core-x\ndescription: Use for x.\n---\n# Overnight work\nThe agent stops after two failed repair attempts.\n"
EN2 = EN.replace("two failed", "two unsuccessful")


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin"})


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    check(hpi.language(PL) == "pl" and hpi.language(EN) == "en", "HPI-1: recognizes the content language")
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        skill = root / "core" / "skills" / "core-x"
        skill.mkdir(parents=True)
        git(root, "init", "-q")
        for text, msg in ((PL, "pl"), (EN, "en"), (EN2, "en2")):
            (skill / "SKILL.md").write_text(text, encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", msg)
        hpi.ROOT = root
        check(hpi.missing([skill]) == ["core/skills/core-x"], f"HPI-2: --check sees the missing index: {hpi.missing([skill])}")
        out = hpi.write(skill)
        idx = (skill / hpi.INDEX).read_text(encoding="utf-8") if (skill / hpi.INDEX).is_file() else ""
        check(out.startswith("✓") and idx.startswith("head: Użyj przy x.\n# Praca w nocy") and "description" not in idx,
              f"HPI-3: index = the head line (the former description and catalog) + the body of the last Polish version: {out} {idx[:60]!r}")
        check(hpi.missing([skill]) == [], "HPI-4: after writing, --check reports nothing missing")
        (skill / hpi.INDEX).unlink()
        (skill / "SKILL.md").write_text(PL, encoding="utf-8")
        check("no index needed" in hpi.write(skill) and not (skill / hpi.INDEX).exists(),
              "HPI-5: a Polish skill gets no index")
    hpi.ROOT = REPO
    r = subprocess.run([sys.executable, str(REPO / "tools" / "hint_pl_index.py"), "--all", "--check"],
                       capture_output=True, text=True, cwd=REPO)
    check(r.returncode == 0, f"HPI-6: every translated factory skill has hint.pl.txt: {r.stdout[-400:]}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the Polish hint index (tool)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
