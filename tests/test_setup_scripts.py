#!/usr/bin/env python3
"""Instalacja komendy `tf` jedną linijką (docs/setup.md): scripts/install.sh sprawdza Pythona 3.9+ i gita, pobiera
fabrykę do katalogu tymczasowego i instaluje launcher (`core/factory/tf.py --install-launcher`) z adresem repozytorium.
Działa także podany na stdin (`curl … | sh`). scripts/install.ps1 — to samo w PowerShellu (test, gdy jest pwsh).
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

    check(SH.is_file() and PS1.is_file(), "S-0: scripts/install.sh i scripts/install.ps1 istnieją")
    check((ROOT / "docs" / "setup.md").is_file() and "install.sh" in (ROOT / "docs" / "setup.md").read_text()
          and "install.ps1" in (ROOT / "docs" / "setup.md").read_text(), "S-0: docs/setup.md opisuje oba skrypty")
    for f in (SH, PS1):
        bad = [(i, ln) for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1) if not ln.isascii()] \
            if f.is_file() else []
        check(not bad, f"S-7: {f.name} tylko ASCII (Windows PowerShell 5.1 czyta `irm | iex` bez UTF-8 i psuje znaki): "
                       f"{bad[:3]}")
    if not SH.is_file() or not shutil.which("git") or not shutil.which("sh"):
        print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów skryptów instalacji")
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
              f"S-1: launcher w TF_BIN z adresem repozytorium: {r.stdout[-500:]}{r.stderr[-500:]}")
        check(not list((t / "tmp").iterdir()), f"S-2: katalog tymczasowy usunięty: {list((t / 'tmp').iterdir())}")
        launcher.unlink(missing_ok=True)
        r = subprocess.run(["sh"], input=SH.read_text(encoding="utf-8"), env=env, capture_output=True, text=True,
                           timeout=300)
        check(r.returncode == 0 and launcher.is_file(), f"S-3: działa z stdin (curl … | sh): {r.stdout[-300:]}"
                                                        f"{r.stderr[-300:]}")
        r = subprocess.run(["sh", str(SH)], env={**env, "TF_PYTHON": str(t / "brak-pythona")}, capture_output=True,
                           text=True, timeout=60)
        check(r.returncode != 0 and "Python" in r.stdout + r.stderr, f"S-4: brak Pythona → błąd z podpowiedzią: "
                                                                     f"{r.stdout}{r.stderr}")
        r = subprocess.run(["sh", str(SH)], env={**env, "TF_GIT": str(t / "brak-gita")}, capture_output=True, text=True,
                           timeout=60)
        check(r.returncode != 0 and "git" in (r.stdout + r.stderr).lower(), f"S-5: brak gita → błąd z podpowiedzią: "
                                                                            f"{r.stdout}{r.stderr}")
        pwsh = shutil.which("pwsh")
        if pwsh:
            (t / "bin2").mkdir()
            r = subprocess.run([pwsh, "-NoProfile", "-File", str(PS1)], env={**env, "TF_BIN": str(t / "bin2")},
                               capture_output=True, text=True, timeout=300)
            check(r.returncode == 0 and (t / "bin2" / "tf").is_file(), f"S-6: install.ps1: {r.stdout}{r.stderr}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów skryptów instalacji")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
