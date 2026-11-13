#!/usr/bin/env python3
"""Testy polecenia tf (.tf/factory/tf.py): instalacja z najnowszego wydania albo aktualizacja, nakładki, launcher z adresem repo."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
CTF = ROOT / ".tf" / "factory" / "tf.py"

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
(Path(__file__).resolve().parents[2] / "updated.json").write_text(json.dumps(sys.argv[1:]))
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
            (p / ".tf" / "factory").mkdir(parents=True)
            (p / ".tf" / "factory" / "update.py").write_text(STUB_UPDATE)
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

        # CTF-17: instalacja sprzed przeniesienia silnika (factory/ w katalogu głównym, bez .tf/factory/) — komunikat
        p = base / "stary-uklad"
        (p / ".claude").mkdir(parents=True)
        (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"version": "8.0.0", "source": repo}))
        (p / "factory").mkdir()
        (p / "factory" / "update.py").write_text(STUB_UPDATE)
        r = ctf(p, "list", repo=repo)
        check(r.returncode == 2 and ".tf/factory" in r.stdout and "tf install" in r.stdout,
              f"CTF-17: stary układ factory/ → kod 2 i polecenie ponownej instalacji: {r.returncode} {r.stdout}")

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

    # tf doctor mówi wprost, że bramka jakości jest wyłączona (i milczy o niej, gdy działa)
    with tempfile.TemporaryDirectory() as t:
        doc = Path(t) / "doc"
        (doc / ".tf" / "factory").mkdir(parents=True)
        (doc / ".claude" / "hooks").mkdir(parents=True)
        (doc / ".claude" / "factory-manifest.json").write_text(json.dumps({"version": "1.0.0"}))
        (doc / ".tf" / "factory" / "migrations.py").write_text("def apply(root, dry=True):\n    return []\n")
        (doc / ".tf" / "factory" / "build.py").write_text("print('ok build check')\n")
        shutil.copy(ROOT / ".claude" / "hooks" / "quality_gate.py", doc / ".claude" / "hooks" / "quality_gate.py")
        denv = {k: v for k, v in env.items() if k != "QG_GATE_DISABLE"}
        r = subprocess.run([sys.executable, str(CTF), "doctor"], cwd=doc, env=denv, capture_output=True, text=True)
        check(r.returncode == 0 and "Bramka jakości wyłączona" in r.stdout and "ok build check" in r.stdout,
              f"CTF-12: doctor zgłasza wyłączoną bramkę i nie zmienia kodu wyjścia: {r.returncode} {r.stdout}{r.stderr}")
        (doc / ".claude" / "quality-gate.json").write_text(json.dumps({"command": "npm test"}))
        r = subprocess.run([sys.executable, str(CTF), "doctor"], cwd=doc, env=denv, capture_output=True, text=True)
        check(r.returncode == 0 and "Bramka jakości włączona" in r.stdout and "npm test" in r.stdout,
              f"CTF-13: doctor potwierdza działającą bramkę z poleceniem: {r.stdout}{r.stderr}")

    # personalizacja: jedno miejsce na polecenia — tf new skill, tf skill check/audit, tf config show
    with tempfile.TemporaryDirectory() as t:
        per = Path(t) / "per"
        shutil.copytree(ROOT / ".tf" / "factory", per / ".tf" / "factory",
                        ignore=shutil.ignore_patterns("packs", "__pycache__"))
        (per / ".claude").mkdir()
        (per / ".claude" / "factory-manifest.json").write_text(json.dumps({"version": "1.0.0"}))
        echo = "import json, sys\nfrom pathlib import Path\n" \
               "Path('called.json').write_text(json.dumps([Path(__file__).name, *sys.argv[1:]]))\n"
        for name in ("build.py", "skill_gate.py", "skill_audit.py"):
            (per / ".tf" / "factory" / name).write_text(echo)

        def called(*args):
            (per / "called.json").unlink(missing_ok=True)
            r = subprocess.run([sys.executable, str(CTF), *args], cwd=per, env=env, capture_output=True, text=True)
            f = per / "called.json"
            return r, (json.loads(f.read_text()) if f.exists() else None)

        r, c = called("new", "skill", "app-faktury", "Użyj przy fakturach. Nie do płatności.", "--role", "backend")
        check(c == ["build.py", "new-skill", "app-faktury", "Użyj przy fakturach. Nie do płatności.", "--role", "backend"],
              f"CTF-14: tf new skill → build.py new-skill z tymi samymi argumentami: {c} {r.stdout}{r.stderr}")
        r, c = called("new", "skill", "app-faktury")
        check(c is None and r.returncode == 2 and "tf new skill" in r.stdout and "Nie do" in r.stdout,
              f"CTF-15: bez opisu → podpowiedź użycia z przykładem opisu, nic nie uruchamia: {r.stdout}")
        r, c = called("skill", "check", "app-faktury", "--model", "haiku")
        check(c == ["skill_gate.py", "app-faktury", "--model", "haiku"], f"CTF-16: tf skill check → skill_gate.py: {c}")
        r, c = called("skill", "audit", ".claude/skills/app-faktury")
        check(c == ["skill_audit.py", ".claude/skills/app-faktury"], f"CTF-17: tf skill audit → skill_audit.py: {c}")
        r, c = called("skill", "zrob-cos")
        check(c is None and r.returncode == 2 and "tf skill check" in r.stdout, f"CTF-18: nieznane podpolecenie → użycie: {r.stdout}")

        (per / ".tf" / "config").mkdir()
        (per / ".tf" / "config" / "config.yaml").write_text("default_profile: oszczedny\ntiers:\n  std:\n    effort: low\n")
        r, _ = called("config", "show")
        lines = {ln.split()[0]: ln for ln in r.stdout.splitlines() if ln.strip() and not ln.startswith(("#", " "))}
        check(r.returncode == 0 and "projekt" in lines.get("default_profile", "") and "oszczedny" in lines.get("default_profile", "")
              and "projekt" in lines.get("tiers", "") and "fabryka" in lines.get("limits", ""),
              f"CTF-19: tf config show pokazuje wartości i skąd pochodzą (projekt / fabryka): {r.stdout[:600]}{r.stderr}")
        r, _ = called("config", "show", "tiers")
        check(r.returncode == 0 and '"effort": "low"' in r.stdout and "haiku" in r.stdout and "limits" not in r.stdout,
              f"CTF-20: tf config show <klucz> pokazuje scaloną wartość jednego klucza: {r.stdout[:400]}")
        r, _ = called("config", "show", "nie-ma")
        check(r.returncode == 2 and "nie-ma" in r.stdout, f"CTF-21: nieznany klucz → kod 2: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów tf")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
