#!/usr/bin/env python3
"""Spis zadań bez konfliktów: `docs/project/changes/INDEX.md` nie jest już przepisywany przy każdym zapisie zadania
(dwa otwarte naraz pull requesty zadań miały w nim konflikt). Listę daje `tf status`; istniejący plik staje się stałą
notką i więcej się nie zmienia. python3 .claude/tests/test_task_index.py"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
REPORT = ROOT / ".claude" / "skills" / "tf" / "scripts" / "run_report.py"
CHANGES = Path("docs") / "project" / "changes"
OLD_INDEX = ("# Zadania\n\nGenerowany przez `tf task` — nie edytuj ręcznie. Szczegóły zadania: "
             "`docs/project/changes/<klucz>/`.\n\n| Klucz | Tytuł | Etap | Zmieniono |\n|---|---|---|---|\n"
             "| OLD-1 | Stare zadanie | pr | 2026-11-01 |\n")


def call(project: Path, script: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_CONFIG_DIR": str(project.parent / "cfg"),
           "TF_DASHBOARD_OPEN": "0"}
    return subprocess.run([sys.executable, str(script), *args], cwd=project, capture_output=True, text=True, env=env,
                          timeout=120)


def git(project: Path, *args: str, ok: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 or not ok, (args, r.stdout, r.stderr)
    return r


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # nowy projekt: spisu w pliku nie ma, listę daje polecenie
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        p.mkdir()
        call(p, TASK, "start", "PROJ-1", "--title", "Limit dobowy")
        call(p, TASK, "stage", "PROJ-1", "specyfikacja")
        r = call(p, TASK, "list")
        check(not (p / CHANGES / "INDEX.md").exists() and "PROJ-1" in r.stdout and "specyfikacja" in r.stdout,
              f"I-1: zapis zadania nie zakłada INDEX.md; listę z etapem daje `tf status`: {r.stdout}")
        r = call(p, REPORT, "start", "Eksport sesji", "--key", "PROJ-2", "--story", "Jako operator chcę eksport.")
        f = call(p, REPORT, "finish", str(p / ".tf" / "runs" / "PROJ-2"))
        check("git add docs/project/changes/PROJ-2`" in f.stdout and "INDEX.md" not in f.stdout,
              f"I-2: commit plików zadania nie wymienia INDEX.md, gdy pliku nie ma: {f.stdout[-300:]}")

    # projekt ze starym spisem w gicie: dwa zadania na dwóch gałęziach z tej samej bazy scalają się bez konfliktu
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "proj"
        (p / CHANGES / "OLD-1").mkdir(parents=True)
        (p / CHANGES / "INDEX.md").write_text(OLD_INDEX, encoding="utf-8")
        (p / CHANGES / "OLD-1" / "task.json").write_text(
            '{"schema": 1, "key": "OLD-1", "title": "Stare zadanie", "stage": "pr", "updated": "2026-11-01T10:00:00Z"}\n',
            encoding="utf-8")
        git(p, "init", "-q", "-b", "main")
        for k, v in (("user.name", "t"), ("user.email", "t@t"), ("commit.gpgsign", "false")):
            git(p, "config", k, v)
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "docs: stare zadanie")

        git(p, "switch", "-q", "-c", "story/a")
        call(p, TASK, "start", "PROJ-2", "--title", "Zadanie A")
        note = (p / CHANGES / "INDEX.md").read_text(encoding="utf-8")
        check("tf status" in note and "OLD-1" not in note and "|" not in note,
              f"I-3: istniejący spis staje się stałą notką wskazującą `tf status`, bez wierszy zadań: {note}")
        call(p, TASK, "stage", "PROJ-2", "specyfikacja")
        call(p, TASK, "slice", "PROJ-2", "K1", "planned", "--title", "limit")
        check((p / CHANGES / "INDEX.md").read_text(encoding="utf-8") == note,
              "I-4: kolejne zapisy zadania nie zmieniają już pliku INDEX.md")
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "docs(task): record PROJ-2")

        git(p, "switch", "-q", "main")
        git(p, "switch", "-q", "-c", "story/b")
        call(p, TASK, "start", "PROJ-3", "--title", "Zadanie B")
        call(p, TASK, "stage", "PROJ-3", "specyfikacja")
        git(p, "add", "-A")
        git(p, "commit", "-q", "-m", "docs(task): record PROJ-3")
        m = git(p, "merge", "-q", "--no-edit", "story/a", ok=False)
        status = git(p, "status", "--porcelain").stdout
        check(m.returncode == 0 and status == "" and (p / CHANGES / "PROJ-2" / "task.json").is_file()
              and (p / CHANGES / "PROJ-3" / "task.json").is_file(),
              f"I-5: gałęzie dwóch zadań z tej samej bazy scalają się bez konfliktu: {m.returncode} {m.stdout} {m.stderr} {status}")
        r = call(p, TASK, "list")
        check(all(k in r.stdout for k in ("OLD-1", "PROJ-2", "PROJ-3")), f"I-6: po scaleniu `tf status` widzi wszystkie zadania: {r.stdout}")

        # plik istnieje (notka): polecenie commitu plików zadania go wymienia, żeby zmiana notki nie została w drzewie
        call(p, REPORT, "start", "Eksport sesji", "--key", "PROJ-4", "--story", "Jako operator chcę eksport.")
        f = call(p, REPORT, "finish", str(p / ".tf" / "runs" / "PROJ-4"))
        check("docs/project/changes/INDEX.md" in f.stdout, f"I-7: gdy plik istnieje, commit plików zadania go obejmuje: {f.stdout[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów spisu zadań")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
