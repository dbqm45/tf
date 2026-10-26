#!/usr/bin/env python3
"""Testy hooka commit-msg (skill core-conventional-commits, scripts/commit_msg.py): nagłówek Conventional Commits,
stopki `Change:` (klucz zmiany lub cięcia, D3 kontraktu pdi) i `Flag:`, wymagany `Change:` na gałęzi z kluczem,
instalacja hooka w repozytorium git. python3 .claude/tests/test_commit_msg.py"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "core-conventional-commits" / "scripts" / "commit_msg.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.com", "PYTHONDONTWRITEBYTECODE": "1"}


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=ENV, timeout=60)


def new_repo(tmp: str, branch: str = "main") -> Path:
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", branch)
    return repo


def check_msg(repo: Path, message: str) -> subprocess.CompletedProcess:
    f = repo / "MSG"
    f.write_text(message, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "check", str(f)], cwd=repo, capture_output=True, text=True,
                          env=ENV, timeout=60)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    ok = {
        "zwykły commit": "feat(cart): apply discount codes\n",
        "Change z TSK": "feat(payments): retry failed payment\n\nWhy it matters.\n\nChange: TSK-57\n",
        "Change z CHG i zakres F4": "docs(CHG-12): faza requirements (pdi)\n\nChange: CHG-12\n",
        "kilka kluczy": "fix(payments): avoid double charge\n\nChange: TSK-57, TSK-58\n",
        "Flag": "feat(payments): retry behind a flag\n\nChange: TSK-57\nFlag: payment-retry\n",
        "Merge": "Merge branch 'main' into story/x\n",
        "fixup": "fixup! feat(cart): apply discount codes\n",
        "komentarze gita": "feat(cart): apply codes\n\n# Please enter the commit message\n# On branch main\n",
        "breaking": "feat(api)!: remove v1 endpoints\n\nBREAKING CHANGE: clients must call /v2\n",
    }
    bad = {
        "bez typu": ("apply discount codes\n", "typ"),
        "kropka": ("feat(cart): apply discount codes.\n", "kropk"),
        "za długi opis": ("feat(cart): " + "a" * 73 + "\n", "72"),
        "brak pustej linii": ("feat(cart): apply codes\nbody here\n", "pust"),
        "zły klucz w Change": ("feat(cart): apply codes\n\nChange: tsk-57\n", "tsk-57"),
        "pusty Change": ("feat(cart): apply codes\n\nChange:\n", "Change"),
        "Flag ze spacją": ("feat(cart): apply codes\n\nChange: TSK-1\nFlag: payment retry\n", "Flag"),
        "pusta wiadomość": ("# only a comment\n", "pust"),
        "breaking małymi": ("feat(api): drop v1\n\nbreaking change: gone\n", "BREAKING CHANGE"),
    }
    with tempfile.TemporaryDirectory() as tmp:
        repo = new_repo(tmp)
        for label, message in ok.items():
            r = check_msg(repo, message)
            check(r.returncode == 0, f"CM-1 przechodzi: {label}: {r.stdout}{r.stderr}")
        for label, (message, needle) in bad.items():
            r = check_msg(repo, message)
            check(r.returncode == 1 and needle in r.stdout + r.stderr, f"CM-2 odrzuca: {label}: {r.stdout}{r.stderr}")

    with tempfile.TemporaryDirectory() as tmp:
        repo = new_repo(tmp, "story/tsk-57-ponowienie-platnosci")
        r = check_msg(repo, "feat(payments): retry failed payment\n")
        check(r.returncode == 1 and "Change: TSK-57" in r.stdout + r.stderr,
              f"CM-3: gałąź z kluczem bez stopki → błąd z gotową linią do dopisania: {r.stdout}{r.stderr}")
        r = check_msg(repo, "feat(payments): retry failed payment\n\nChange: TSK-57\n")
        check(r.returncode == 0, f"CM-4: gałąź z kluczem i stopką → OK: {r.stdout}{r.stderr}")
        r = check_msg(repo, "feat(payments): retry failed payment\n\nChange: TSK-58\n")
        check(r.returncode == 1 and "TSK-57" in r.stdout + r.stderr, f"CM-5: stopka z innym kluczem niż gałąź: {r.stdout}")

    with tempfile.TemporaryDirectory() as tmp:
        repo = new_repo(tmp)
        local = repo / ".claude" / "skills" / "core-conventional-commits" / "scripts" / "commit_msg.py"
        local.parent.mkdir(parents=True)
        local.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")   # jak w projekcie z fabryką
        git(repo, "add", ".claude")
        r = subprocess.run([sys.executable, str(local), "install"], cwd=repo, capture_output=True, text=True, env=ENV,
                           timeout=60)
        hook = repo / ".git" / "hooks" / "commit-msg"
        check(r.returncode == 0 and hook.is_file() and os.access(hook, os.X_OK),
              f"CM-6: install zapisuje wykonywalny hook commit-msg: {r.stdout}{r.stderr}")
        (repo / "a.txt").write_text("a", encoding="utf-8")
        git(repo, "add", "a.txt")
        r = git(repo, "commit", "-q", "-m", "dodaj plik")
        check(r.returncode != 0 and "commit-msg" in r.stdout + r.stderr and git(repo, "rev-parse", "HEAD").returncode != 0,
              f"CM-7: zainstalowany hook odrzuca commit spoza formatu: {r.stdout}{r.stderr}")
        r = git(repo, "commit", "-q", "-m", "feat(core): add file", "-m", "Change: TSK-1")
        check(r.returncode == 0, f"CM-8: zainstalowany hook przepuszcza poprawny commit: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(SCRIPT), "install"], cwd=repo, capture_output=True, text=True, env=ENV,
                           timeout=60)
        check(r.returncode == 0, f"CM-9: ponowny install (nasz hook) bez błędu: {r.stdout}{r.stderr}")

    with tempfile.TemporaryDirectory() as tmp:
        repo = new_repo(tmp)
        hook = repo / ".git" / "hooks" / "commit-msg"
        hook.write_text("#!/bin/sh\nexec npx commitlint --edit \"$1\"\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "install"], cwd=repo, capture_output=True, text=True, env=ENV,
                           timeout=60)
        check(r.returncode == 1 and "commitlint" in hook.read_text(encoding="utf-8") and "commit_msg.py" in r.stdout,
              f"CM-10: obcy hook nie jest nadpisany; wyjście mówi, jak dopiąć sprawdzenie: {r.stdout}{r.stderr}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów hooka commit-msg")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
