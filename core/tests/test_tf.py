#!/usr/bin/env python3
"""Testy polecenia tf (factory/tf.py): instalacja z najnowszego wydania albo aktualizacja, nakładki, launcher z adresem repo."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "tf.py").is_file())
CTF = ROOT / "factory" / "tf.py"

# Atrapa instalatora: zapisuje w projekcie, z której wersji i z jakimi argumentami go uruchomiono.
STUB_INSTALL = """import json, sys
from pathlib import Path
args = [a for a in sys.argv[1:]]
(Path.cwd() / "installed.json").write_text(json.dumps({
    "version": (Path(__file__).resolve().parent / "VERSION").read_text().strip(), "argv": args}))
"""
# Atrapa update.py w zainstalowanym projekcie.
STUB_UPDATE = """import json, sys
from pathlib import Path
(Path(__file__).resolve().parent.parent / "updated.json").write_text(json.dumps(sys.argv[1:]))
"""


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "-c",
                    "tag.gpgsign=false", *args], cwd=cwd, check=True, capture_output=True)


def make_repo(base: Path) -> str:
    work = base / "factory-work"
    (work / "core" / "factory").mkdir(parents=True)
    (work / "core" / "factory" / "install.py").write_text(STUB_INSTALL)
    git(work, "init", "-q", "-b", "main")
    for version, tag in (("1.0.0", "v1.0.0"), ("1.2.0", "v1.2.0"), ("1.3.0-dev", None)):
        (work / "core" / "factory" / "VERSION").write_text(version + "\n")
        git(work, "add", "-A")
        git(work, "commit", "-qm", f"wersja {version}")
        if tag:
            git(work, "tag", "-a", tag, "-m", tag)
    bare = base / "factory.git"
    git(base, "clone", "-q", "--bare", str(work), str(bare))
    return str(bare)


def main() -> int:
    if not shutil.which("git"):
        print("✓ 0/0 testów tf (brak git — pominięto)")
        return 0
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    env = {k: v for k, v in os.environ.items() if k not in ("TF_REPO", "TEAM_FACTORY")}

    def ctf(cwd: Path, *args: str, repo: str | None = None, script: Path = CTF):
        e = dict(env, **({"TF_REPO": repo} if repo else {}))
        return subprocess.run([sys.executable, str(script), *args], cwd=cwd, env=e, capture_output=True, text=True)

    def project(base: Path, name: str, source: str | None = None) -> Path:
        p = base / name
        p.mkdir()
        if source is not None:
            (p / ".claude").mkdir()
            (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"version": "1.0.0", "source": source}))
            (p / "factory").mkdir()
            (p / "factory" / "update.py").write_text(STUB_UPDATE)
        return p

    def installed(p: Path) -> dict:
        f = p / "installed.json"
        return json.loads(f.read_text()) if f.exists() else {}

    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        repo = make_repo(base)

        p = project(base, "nowy")
        r = ctf(p, "--dry-run", "--shared", repo=repo)
        got = installed(p)
        check(r.returncode == 0 and got.get("version") == "1.2.0",
              f"CTF-1: bez fabryki → instalacja z najnowszego wydania: {got} {r.stdout}{r.stderr}")
        check(got.get("argv") == ["--source", repo, "--dry-run", "--shared"],
              f"CTF-2: instalator dostaje --source repo i flagi użytkownika: {got}")

        p = project(base, "przypiety")
        ctf(p, repo=repo + "#v1.0.0")
        check(installed(p).get("version") == "1.0.0", f"CTF-3: #tag w adresie → ta wersja: {installed(p)}")

        p = project(base, "check")
        ctf(p, "--check", repo=repo)
        check("--dry-run" in installed(p).get("argv", []) and "--check" not in installed(p).get("argv", []),
              f"CTF-4: --check przy instalacji → --dry-run: {installed(p)}")

        p = project(base, "zainstalowany", source="https://example.test/f.git#v1.0.0")
        r = ctf(p, "--dry-run", "--yes", repo=repo)
        upd = json.loads((p / "updated.json").read_text()) if (p / "updated.json").exists() else None
        check(r.returncode == 0 and upd == ["--check", "--yes"] and not installed(p),
              f"CTF-5: jest manifest → update.py (--dry-run → --check), źródło git z manifestu zostaje: {upd} {r.stderr}")

        p = project(base, "z-katalogu", source="/stary/katalog/fabryki")
        ctf(p, repo=repo)
        upd = json.loads((p / "updated.json").read_text()) if (p / "updated.json").exists() else None
        check(upd == ["--source", repo], f"CTF-6: manifest bez źródła git → update.py --source repo: {upd}")

        p = project(base, "bez-repo")
        r = ctf(p)
        check(r.returncode == 2 and "TF_REPO" in r.stdout + r.stderr and not installed(p),
              f"CTF-7: brak adresu repo → kod 2 i podpowiedź: {r.returncode} {r.stdout}{r.stderr}")

        p = project(base, "nakladki", source=repo)
        r = ctf(p, "add", "pack-ev", "pack-ux", repo=repo)
        upd = json.loads((p / "updated.json").read_text()) if (p / "updated.json").exists() else None
        check(r.returncode == 0 and upd == ["--add", "pack-ev,pack-ux"], f"CTF-12: tf add → update.py --add: {upd}")
        r = ctf(p, "remove", "pack-ux", repo=repo)
        upd = json.loads((p / "updated.json").read_text()) if (p / "updated.json").exists() else None
        check(r.returncode == 0 and upd == ["--remove", "pack-ux"], f"CTF-13: tf remove → update.py --remove: {upd}")
        r = ctf(p, "add", repo=repo)
        check(r.returncode == 2 and "Usage" in r.stdout, f"CTF-14: tf add bez nakładki → kod 2: {r.stdout}")
        r = ctf(base, "add", "pack-ev", repo=repo)
        check(r.returncode == 2 and "tf install" in r.stdout, f"CTF-15: tf add bez fabryki → podpowiedź: {r.stdout}")
        r = ctf(p, "nieznane", repo=repo)
        check(r.returncode == 2, f"CTF-16: nieznane polecenie → kod 2: {r.returncode}")

        binp = base / "bin"
        r = ctf(base, "--install-launcher", "--bin", str(binp), "--repo", repo)
        launcher = binp / "tf"
        check(r.returncode == 0 and launcher.is_file() and repr(repo) in launcher.read_text(),
              f"CTF-8: launcher z wpisanym adresem repo: {r.stdout}{r.stderr}")
        if os.name != "nt":
            check(launcher.is_file() and os.access(launcher, os.X_OK), "CTF-9: launcher wykonywalny")
        p = project(base, "z-launchera")
        r = ctf(p, script=launcher)
        check(installed(p).get("version") == "1.2.0", f"CTF-10: launcher działa bez TF_REPO: {r.stdout}{r.stderr}")
        r = ctf(base, "--install-launcher", "--bin", str(base / "bin2"), "--repo",
                "https://user:s3kr3t@example.test/f.git")
        text = (base / "bin2" / "tf").read_text() if (base / "bin2" / "tf").exists() else ""
        check(r.returncode == 0 and "s3kr3t" not in text + r.stdout + r.stderr
              and "'https://example.test/f.git'" in text, f"CTF-11: dane logowania z adresu nie trafiają do launchera")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów tf")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
