#!/usr/bin/env python3
"""
Zamknięcie zadania do commita jednym poleceniem (tańszy kontekst): sprawdzenia, treść commita, dziennik, commit.

  python3 .tf/factory/finish.py --message /ścieżka/msg.txt
  python3 .tf/factory/finish.py --message msg.txt --log "Co zrobiono (jedno zdanie)" --wip <punkt-kontrolny>
  --by claude · --phase maintenance · --no-check (pomiń .tf/factory/check.py) · --root <repozytorium>

Kolejność (zatrzymuje się na pierwszym błędzie): gałąź nie jest main/master → w zmianach nie ma plików `.env*`
(poza `.env.example`) → `.tf/factory/check.py` zielony → treść commita przechodzi `scripts/check_commit_message.py`
(gdy jest) → wpis w dzienniku i zamknięcie punktu kontrolnego (gdy podane) → `git add -A` i `git commit -F`.
**Pushu nie robi**: wypisuje polecenie `git push -u origin <gałąź>` do uruchomienia osobno — strażnik guard_bash pyta
o push człowieka, a skrypt nie może tego obchodzić. Plik z treścią commita trzymaj poza repozytorium (scratchpad).
"""
from __future__ import annotations

import subprocess
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne (build.py, testy, hooki) też piszą i czytają UTF-8

sys.dont_write_bytecode = True   # silnik w .tf/factory/ bez __pycache__ (jak node_modules — tylko kod)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def py(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)


def tail(r: subprocess.CompletedProcess, n: int = 8) -> str:
    lines = [ln for ln in (r.stdout + "\n" + r.stderr).splitlines() if ln.strip()]
    return "\n".join("    " + ln for ln in lines[-n:])


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv[1:])
    for a in it:
        if a in ("--root", "--message", "--log", "--by", "--phase", "--wip"):
            opts[a] = next(it, "")
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    root = Path(opts.get("--root") or ROOT).resolve()
    msg = Path(opts.get("--message") or "")
    if not msg.is_file():
        print("✗ Give --message <file with the commit message> (best outside the repository).")
        return 2
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch in ("main", "master", "HEAD", ""):
        print(f"✗ Branch \"{branch or '?'}\" — commit on a working branch (core-git-workflow), not on main/master.")
        return 2
    status = git(root, "status", "--porcelain", "--untracked-files=all").stdout
    paths = [ln[3:].split(" -> ")[-1].strip('"') for ln in status.splitlines() if ln.strip()]
    secrets = [p for p in paths if Path(p).name.startswith(".env") and Path(p).name != ".env.example"]
    if secrets:
        print(f"✗ The changes contain secret files: {', '.join(secrets)} — remove them or add them to .gitignore (secrets only "
              "through environment variables).")
        return 2
    if not paths and not opts.get("--log"):
        print("✓ No changes — nothing to commit.")
        return 0
    if not opts.get("--no-check") and (root / ".tf" / "factory" / "check.py").is_file():
        r = py(root / ".tf" / "factory" / "check.py", cwd=root)
        if r.returncode != 0:
            print("✗ Checks are red — no commit:\n" + tail(r, 15))
            return 1
        print("✓ checks green")
    checker = root / "scripts" / "check_commit_message.py"
    if checker.is_file():
        r = py(checker, "--file", str(msg), cwd=root)
        if r.returncode != 0:
            print("✗ The commit message does not pass the check:\n" + tail(r))
            return 1
    record = root / ".claude" / "hooks" / "project_record.py"
    if record.is_file() and (opts.get("--log") or opts.get("--wip")):
        if opts.get("--log"):
            r = py(record, "log", "--by", opts.get("--by") or "claude", "--phase", opts.get("--phase") or "maintenance",
                   opts["--log"], cwd=root)
            if r.returncode != 0:
                print("✗ The project record entry failed:\n" + tail(r))
                return 1
        if opts.get("--wip"):
            r = py(record, "wip", "done", opts["--wip"], cwd=root)
            if r.returncode != 0:
                print("✗ Closing the checkpoint failed:\n" + tail(r))
                return 1
        r = py(record, "check", cwd=root)
        if r.returncode != 0:
            print("✗ The project record is invalid after the entry:\n" + tail(r))
            return 1
        print("✓ project record updated")
    elif opts.get("--log") or opts.get("--wip"):
        print("ℹ No .claude/hooks/project_record.py — project record entry skipped.")
    hooks = root / ".tf" / "factory" / "hooks_status.py"
    if hooks.is_file():
        r = py(hooks, "--root", str(root), cwd=root)
        if r.stdout.startswith("⚠"):
            print(r.stdout.strip())
    git(root, "add", "-A")
    if not git(root, "diff", "--cached", "--name-only").stdout.strip():
        print("✓ No changes — nothing to commit.")
        return 0
    r = git(root, "commit", "-q", "-F", str(msg))
    if r.returncode != 0:
        print("✗ git commit failed:\n" + tail(r))
        return 1
    head = git(root, "log", "-1", "--format=%h %s").stdout.strip()
    print(f"✓ commit {head}\nPush with a separate command (the guard asks for approval): git push -u origin {branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
