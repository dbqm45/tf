#!/usr/bin/env python3
"""Testy update.py: pobieranie nowej wersji (z repozytorium git domyślnie najnowsze wydanie, tag vX.Y.Z) i komunikat
o nowszym wydaniu przy starcie sesji (notice, hook update_notice.py)."""
import importlib.util
import json
import os
import zipfile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "update.py").is_file())


def load():
    spec = importlib.util.spec_from_file_location("ctf_update_fetch", ROOT / "factory" / "update.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "-c",
                    "tag.gpgsign=false", *args], cwd=cwd, check=True, capture_output=True)


def make_repo(base: Path, name: str, versions: list[tuple[str, str | None]]) -> str:
    """Repozytorium fabryki: kolejne commity z factory/VERSION = wersja, opcjonalnie otagowane; zwraca adres *.git."""
    work = base / f"{name}-work"
    (work / "factory").mkdir(parents=True)
    (work / "factory" / "install.py").write_text("")
    git(work, "init", "-q", "-b", "main")
    for version, tag in versions:
        (work / "factory" / "VERSION").write_text(version + "\n")
        git(work, "add", "-A")
        git(work, "commit", "-qm", f"wersja {version}")
        if tag:
            git(work, "tag", "-a", tag, "-m", tag)
    bare = base / f"{name}.git"
    git(base, "clone", "-q", "--bare", str(work), str(bare))
    return str(bare)


def project(base: Path, name: str, version: str, source: str | None) -> Path:
    p = base / name
    (p / ".claude").mkdir(parents=True)
    man = {"version": version, "files": {}}
    if source:
        man["source"] = source
    (p / ".claude" / "factory-manifest.json").write_text(json.dumps(man))
    return p


def factory_dir(base: Path, name: str, version: str) -> Path:
    d = base / name
    (d / "factory").mkdir(parents=True)
    (d / "factory" / "install.py").write_text("")
    (d / "factory" / "VERSION").write_text(version + "\n")
    return d


def notice_tests(up, check) -> None:
    env = {"PATH": os.environ.get("PATH", "")}
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        cache = base / "cache"
        src = factory_dir(base, "fabryka", "2.20.0")
        p = project(base, "app", "2.19.0", str(src))
        msg = up.notice(p, env=env, cache_dir=cache, now=1000.0)
        check(msg and "2.20.0" in msg and "2.19.0" in msg and "update.py" in msg,
              f"UN-1: nowsze wydanie w źródle (katalog) → komunikat z wersjami i poleceniem: {msg}")
        check(up.notice(project(base, "same", "2.20.0", str(src)), env=env, cache_dir=cache, now=1000.0) is None,
              "UN-2: ta sama wersja → brak komunikatu")
        bare = base / "bare"
        (bare / ".claude").mkdir(parents=True)
        check(up.notice(bare, env=env, cache_dir=cache, now=1000.0) is None, "UN-3: brak manifestu (repo fabryki) → brak")
        check(up.notice(p, env={**env, "CTF_UPDATE_CHECK": "0"}, cache_dir=cache, now=1000.0) is None,
              "UN-4: CTF_UPDATE_CHECK=0 wyłącza sprawdzanie")
        (src / "factory" / "VERSION").write_text("3.0.0\n")
        msg = up.notice(p, env=env, cache_dir=cache, now=1000.0 + 3600)
        check(msg and "2.20.0" in msg, f"UN-5: w ciągu doby wynik z pamięci podręcznej (bez ponownego pytania): {msg}")
        msg = up.notice(p, env=env, cache_dir=cache, now=1000.0 + 2 * 86400)
        check(msg and "3.0.0" in msg and "MAJOR" in msg, f"UN-6: po dobie sprawdza ponownie; wydanie MAJOR oznaczone: {msg}")
        z = base / "fabryka.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("claude-team-factory-main/factory/VERSION", "2.21.0\n")
            zf.writestr("claude-team-factory-main/factory/install.py", "")
        msg = up.notice(project(base, "zip", "2.19.0", str(z)), env=env, cache_dir=cache, now=1000.0)
        check(msg and "2.21.0" in msg, f"UN-7: źródło .zip → wersja z factory/VERSION w archiwum: {msg}")
        envsrc = factory_dir(base, "z-env", "2.22.0")
        msg = up.notice(project(base, "env", "2.19.0", str(src)), env={**env, "CLAUDE_TEAM_FACTORY": str(envsrc)},
                        cache_dir=cache, now=1000.0)
        check(msg and "2.22.0" in msg, f"UN-8: CLAUDE_TEAM_FACTORY ma pierwszeństwo przed manifestem: {msg}")
        check(up.notice(project(base, "gone", "2.19.0", str(base / "nie-ma")), env=env, cache_dir=cache,
                        now=1000.0) is None, "UN-9: niedostępne źródło → brak komunikatu, bez wyjątku")

        # Hook SessionStart w projekcie: komunikat widoczny dla człowieka (systemMessage) i w kontekście agenta.
        app = project(base, "hook-app", "2.19.0", str(factory_dir(base, "hook-src", "2.20.0")))
        (app / "factory").mkdir()
        shutil.copy(ROOT / "factory" / "update.py", app / "factory" / "update.py")
        (app / ".claude" / "hooks").mkdir()
        shutil.copy(ROOT / ".claude" / "hooks" / "update_notice.py", app / ".claude" / "hooks" / "update_notice.py")
        r = subprocess.run([sys.executable, str(app / ".claude" / "hooks" / "update_notice.py")], capture_output=True,
                           text=True, env={**env, "CLAUDE_PROJECT_DIR": str(app), "XDG_CACHE_HOME": str(base / "xdg")},
                           input="{}", timeout=30)
        try:
            out = json.loads(r.stdout)
        except ValueError:
            out = {}
        check(r.returncode == 0 and "2.20.0" in out.get("systemMessage", "")
              and "2.20.0" in out.get("hookSpecificOutput", {}).get("additionalContext", ""),
              f"UN-10: hook pokazuje komunikat człowiekowi i agentowi: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(app / ".claude" / "hooks" / "update_notice.py")], capture_output=True,
                           text=True, env={**env, "CLAUDE_PROJECT_DIR": str(bare)}, input="{}", timeout=30)
        check(r.returncode == 0 and r.stdout.strip() == "", f"UN-11: nic do powiedzenia → hook milczy: {r.stdout}{r.stderr}")


def preflight_tests(up, check) -> None:
    """Piaskownica Bash agenta blokuje zapis do skilli, agentów i ustawień: aktualizacja ma to wykryć przed pierwszym
    zapisem, a nie zostawić instalacji w połowie (root w testach omija chmod, więc blokadę udaje plik zamiast katalogu)."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for rel in (".claude/hooks", ".claude/agents/_generated", "factory"):
            (root / rel).mkdir(parents=True)
        (root / ".claude" / "settings.json").write_text("{}")
        check(up.unwritable(root) == [], f"PF-1: zapisywalny projekt → pusta lista: {up.unwritable(root)}")
        check(not list(root.rglob(".ctf-probe-*")), "PF-2: próba zapisu nie zostawia plików")
        (root / ".claude" / "skills").write_text("")
        (root / "CLAUDE.md").mkdir()
        got = up.unwritable(root)
        check(got == [".claude/skills/", "CLAUDE.md"], f"PF-3: niezapisywalne ścieżki wymienione z nazwy: {got}")
        code, msg = up.preflight(root, "python3 factory/update.py --yes")
        check(code == 2 and ".claude/skills/" in msg and "python3 factory/update.py --yes" in msg,
              f"PF-4: komunikat każe człowiekowi uruchomić polecenie samemu: {code} {msg}")
        (root / ".claude" / "skills").unlink()
        (root / "CLAUDE.md").rmdir()
        check(up.preflight(root, "x") == (0, ""), "PF-5: bez blokad aktualizacja idzie dalej")


def main() -> int:
    up = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    notice_tests(up, check)
    preflight_tests(up, check)
    if not shutil.which("git"):
        print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów update.py (brak git — pominięto część)")
        return 1 if fails else 0

    def version_of(src: str, tmp: Path) -> str:
        return (up.fetch(src, tmp) / "factory" / "VERSION").read_text().strip()

    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        repo = make_repo(base, "factory", [("1.0.0", "v1.0.0"), ("1.10.0", "v1.10.0"), ("1.9.0", "v1.9.0"),
                                           ("2.0.0-rc.1", "v2.0.0-rc.1"), ("2.0.0-dev", None)])
        check(up.latest_tag(repo) == "v1.10.0", f"najwyższe wydanie wg SemVer, bez rc: {up.latest_tag(repo)}")
        for i, (src, want, msg) in enumerate((
                (repo, "1.10.0", "bez #ref → najnowsze wydanie, nie stan main"),
                (repo + "#main", "2.0.0-dev", "#main → gałąź wprost"),
                (repo + "#v1.0.0", "1.0.0", "#tag → ta wersja"))):
            tmp = base / f"t{i}"
            tmp.mkdir()
            got = version_of(src, tmp)
            check(got == want, f"{msg}: {got}")
        untagged = make_repo(base, "untagged", [("0.1.0", None)])
        check(up.latest_tag(untagged) is None, "repozytorium bez tagów → brak wydania")
        (base / "t9").mkdir()
        check(version_of(untagged, base / "t9") == "0.1.0", "bez tagów → domyślna gałąź")
        check(up.latest_tag(str(base / "brak.git")) is None, "niedostępne repozytorium → None, bez wyjątku")
        cache = base / "cache"
        for i, (src, want, msg) in enumerate((
                (repo, "1.10.0", "UN-12: źródło git → komunikat o najnowszym wydaniu (tag)"),
                (repo + "#v1.0.0", None, "UN-13: źródło przypięte do #ref → brak komunikatu"),
                (str(base / "brak.git"), None, "UN-14: niedostępne repozytorium → brak komunikatu"))):
            got = up.notice(project(base, f"g{i}", "1.0.0", src), env={"PATH": os.environ.get("PATH", "")},
                            cache_dir=cache, now=1000.0)
            check((got is None) if want is None else (got and want in got), f"{msg}: {got}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów update.py")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
