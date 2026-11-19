#!/usr/bin/env python3
"""Installing the `tf` command with one line (docs/setup.md): scripts/install.sh checks Python 3.9+ and git, downloads the
factory to a temporary directory and installs the launcher (`core/factory/tf.py --install-launcher`) with the repository address.
It also works when given on stdin (`curl … | sh`). scripts/install.ps1 — the same in PowerShell (tested when pwsh is present).
python3 tests/test_setup_scripts.py"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
SH = ROOT / "scripts" / "install.sh"
PS1 = ROOT / "scripts" / "install.ps1"


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    check(SH.is_file() and PS1.is_file(), "S-0: scripts/install.sh and scripts/install.ps1 exist")
    check((ROOT / "docs" / "setup.md").is_file() and "install.sh" in (ROOT / "docs" / "setup.md").read_text()
          and "install.ps1" in (ROOT / "docs" / "setup.md").read_text(), "S-0: docs/setup.md describes both scripts")
    for f in (SH, PS1):
        bad = [(i, ln) for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1) if not ln.isascii()] \
            if f.is_file() else []
        check(not bad, f"S-7: {f.name} ASCII only (Windows PowerShell 5.1 reads `irm | iex` without UTF-8 and garbles characters): "
                       f"{bad[:3]}")
    if not SH.is_file() or not shutil.which("git") or not shutil.which("sh"):
        print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} setup script tests")
        return 1 if fails else 0
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        bare = t / "tf.git"
        subprocess.run(["git", "clone", "-q", "--bare", "--depth", "1", f"file://{ROOT}", str(bare)], check=True,
                       capture_output=True)
        (t / "tmp").mkdir()
        env = {**os.environ, "HOME": str(t / "home"), "TF_REPO": str(bare), "TF_BIN": str(t / "bin"),
               "TMPDIR": str(t / "tmp")}
        env.pop("TF_PYTHON", None)
        r = subprocess.run(["sh", str(SH)], env=env, capture_output=True, text=True, timeout=300)
        launcher = t / "bin" / "tf"
        text = launcher.read_text(encoding="utf-8") if launcher.is_file() else ""
        check(r.returncode == 0 and f"REPO = {str(bare)!r}" in text and os.access(launcher, os.X_OK),
              f"S-1: the launcher in TF_BIN with the repository address: {r.stdout[-500:]}{r.stderr[-500:]}")
        check(not list((t / "tmp").iterdir()), f"S-2: the temporary directory removed: {list((t / 'tmp').iterdir())}")
        launcher.unlink(missing_ok=True)
        r = subprocess.run(["sh"], input=SH.read_text(encoding="utf-8"), env=env, capture_output=True, text=True,
                           timeout=300)
        check(r.returncode == 0 and launcher.is_file(), f"S-3: works from stdin (curl … | sh): {r.stdout[-300:]}"
                                                        f"{r.stderr[-300:]}")
        r = subprocess.run(["sh", str(SH)], env={**env, "TF_PYTHON": str(t / "brak-pythona")}, capture_output=True,
                           text=True, timeout=60)
        check(r.returncode != 0 and "Python" in r.stdout + r.stderr, f"S-4: no Python → an error with a hint: "
                                                                     f"{r.stdout}{r.stderr}")
        r = subprocess.run(["sh", str(SH)], env={**env, "TF_GIT": str(t / "brak-gita")}, capture_output=True, text=True,
                           timeout=60)
        check(r.returncode != 0 and "git" in (r.stdout + r.stderr).lower(), f"S-5: no git → an error with a hint: "
                                                                            f"{r.stdout}{r.stderr}")
        pwsh = shutil.which("pwsh")
        if pwsh:
            (t / "bin2").mkdir()
            r = subprocess.run([pwsh, "-NoProfile", "-File", str(PS1)], env={**env, "TF_BIN": str(t / "bin2")},
                               capture_output=True, text=True, timeout=300)
            check(r.returncode == 0 and (t / "bin2" / "tf").is_file(), f"S-6: install.ps1: {r.stdout}{r.stderr}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} setup script tests")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
