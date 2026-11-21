#!/usr/bin/env python3
"""Tests of the design session record (skill tf-design, scripts/design_session.py): the artifact and the stage map,
decisions written to decisions.md, going back with an archived version, skipping with an assumption, the handoff gate.
python3 .claude/tests/test_design_session.py"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf-design" / "scripts" / "design_session.py"
ROOT = next(p for p in Path(__file__).resolve().parents if (p / REL).is_file())
SCRIPT = ROOT / REL
HOOK = ROOT / ".claude" / "hooks" / "project_record.py"
TEMPLATES = ROOT / ".claude" / "skills" / "core-project-record" / "templates"
ART = Path("docs") / "project" / "04-architecture" / "design-uprawnienia.md"
DEC = Path("docs") / "project" / "decisions.md"


def project(base: Path) -> Path:
    """A project with the factory's hooks and record templates, like an installed one."""
    p = base / "proj"
    (p / ".claude" / "hooks").mkdir(parents=True)
    shutil.copy(HOOK, p / ".claude" / "hooks" / "project_record.py")
    shutil.copytree(TEMPLATES, p / ".claude" / "skills" / "core-project-record" / "templates")
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    return p


def run(p: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=p, capture_output=True, text=True,
                          env={"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(p)})


def main() -> int:
    fails: list[str] = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    with tempfile.TemporaryDirectory() as t:
        p = project(Path(t))

        # start: the artifact with a stage map, a checkpoint, no second start
        r = run(p, "start", "Mechanizm uprawnień", "--slug", "uprawnienia",
                "--stages", "Problem i zakres;Stan obecny;Warianty;Plan")
        art = (p / ART).read_text(encoding="utf-8") if (p / ART).is_file() else ""
        check(r.returncode == 0 and "status: proposed" in art and "version: 1" in art and "## TL;DR" in art
              and "## Handoff" in art and art.count("| open |") == 4,
              f"DS-1: start writes the artifact with 4 open stages: {r.stdout}{r.stderr}")
        check((p / ".tf" / "wip" / "design-uprawnienia.md").is_file(), f"DS-2: start opens a checkpoint: {r.stdout}{r.stderr}")
        r = run(p, "start", "Mechanizm uprawnień", "--slug", "uprawnienia", "--stages", "A;B")
        check(r.returncode == 1 and "status uprawnienia" in r.stdout + r.stderr,
              f"DS-3: a second start refuses and points to resuming: {r.returncode} {r.stdout}{r.stderr}")
        r = run(p, "status", "uprawnienia")
        check(r.returncode == 0 and "Next: stage 1" in r.stdout, f"DS-4: status names the next open stage: {r.stdout}")

        # accept: a binding decision in decisions.md and in the stage map
        r = run(p, "stage", "uprawnienia", "1", "accept", "--decision", "Uprawnienia per rola, bez ACL na zasób",
                "--why", "trzy poziomy ról z briefu")
        dec = (p / DEC).read_text(encoding="utf-8") if (p / DEC).is_file() else ""
        art = (p / ART).read_text(encoding="utf-8")
        check(r.returncode == 0 and re.search(r"^\| D-001 \|.*Uprawnienia per rola.*\| accepted \| user \|", dec, re.M)
              and re.search(r"^\| 1 \| Problem i zakres \| accepted \| D-001 \|", art, re.M),
              f"DS-5: accept writes D-001 (accepted by user) and links it in the stage map: {r.stdout}{r.stderr}\n{dec}")
        r = run(p, "stage", "uprawnienia", "2", "accept", "--decision", "Model ról z dziedziczeniem jednego poziomu")
        check(r.returncode == 0 and "D-002" in (p / DEC).read_text(encoding="utf-8"), f"DS-6: the next decision is D-002: {r.stdout}")
        r = run(p, "stage", "uprawnienia", "3", "accept")
        check(r.returncode == 2 and "--decision" in r.stdout + r.stderr, f"DS-7: accept without a decision refuses: {r.stdout}{r.stderr}")

        # back: the old version archived, the stage and the later accepted ones reopened, their decisions marked
        r = run(p, "stage", "uprawnienia", "1", "back", "--reason", "jednak ACL dla raportów")
        art = (p / ART).read_text(encoding="utf-8")
        dec = (p / DEC).read_text(encoding="utf-8")
        archived = list((p / "docs" / "project" / "archive").glob("design-uprawnienia-v1.md"))
        check(r.returncode == 0 and "version: 2" in art and archived
              and "status: superseded" in archived[0].read_text(encoding="utf-8"),
              f"DS-8: going back archives version 1 as superseded and the artifact is version 2: {r.stdout}{r.stderr}")
        check(re.search(r"^\| 1 \| Problem i zakres \| reopened \|", art, re.M) and re.search(r"^\| 2 \| Stan obecny \| reopened \|", art, re.M)
              and re.search(r"^\| D-001 \|.*\| reopened \|", dec, re.M) and re.search(r"^\| D-002 \|.*\| reopened \|", dec, re.M),
              f"DS-9: stage 1 and the later accepted stage 2 are reopened, their decisions too: {art}\n{dec}")

        # handoff gate: open stages, then a missing criterion, then ready
        r = run(p, "handoff", "uprawnienia")
        check(r.returncode == 1 and "stage 1" in r.stdout and "/tf-task" not in r.stdout,
              f"DS-10: handoff refuses while stages are open: {r.stdout}")
        for n, d in (("1", "ACL tylko dla raportów"), ("2", "Model ról z dziedziczeniem"), ("3", "Wariant 2")):
            run(p, "stage", "uprawnienia", n, "accept", "--decision", d)
        r = run(p, "stage", "uprawnienia", "4", "skip", "--assumption", "plan zrobi pętla /tf-task")
        art = (p / ART).read_text(encoding="utf-8")
        check(r.returncode == 0 and re.search(r"^\| 4 \| Plan \| skipped \|", art, re.M) and "plan zrobi pętla" in art,
              f"DS-11: skip records the assumption: {r.stdout}{r.stderr}")
        r = run(p, "handoff", "uprawnienia")
        check(r.returncode == 1 and "AC-" in r.stdout, f"DS-12: handoff refuses without acceptance criteria: {r.stdout}")
        art = (p / ART).read_text(encoding="utf-8")
        handoff = ("## Handoff\n**Story.** Jako administrator nadaję role z dziedziczeniem.\n**Acceptance criteria.**\n"
                   "- AC-1 cykl w rolach jest odrzucany z komunikatem\n- AC-2 rola dziedziczy uprawnienia rodzica\n")
        (p / ART).write_text(re.sub(r"## Handoff\n.*", handoff, art, flags=re.S), encoding="utf-8")
        r = run(p, "handoff", "uprawnienia")
        check(r.returncode == 0 and f"/tf-task {ART.as_posix()}" in r.stdout,
              f"DS-13: a complete design gives the /tf-task command: {r.stdout}{r.stderr}")

        # input errors
        r = run(p, "stage", "nie-ma", "1", "accept", "--decision", "x")
        check(r.returncode == 1 and "start" in r.stdout + r.stderr, f"DS-14: an unknown session points to start: {r.stdout}{r.stderr}")
        r = run(p, "stage", "uprawnienia", "9", "accept", "--decision", "x")
        check(r.returncode == 2, f"DS-15: a stage outside the map is an input error: {r.returncode} {r.stdout}")

    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} design session record tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
