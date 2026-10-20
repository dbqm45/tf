#!/usr/bin/env python3
"""
ctf — instaluje albo aktualizuje claude-team-factory w bieżącym projekcie jednym poleceniem (tylko biblioteka standardowa).

  cd ~/projekty/moja-aplikacja
  ctf                    # brak fabryki → instalacja z najnowszego wydania; jest → aktualizacja (factory/update.py)
  ctf --dry-run          # tylko pokaż, co się stanie (przy aktualizacji to samo co --check)
  ctf --shared           # instalacja zespołowa; pozostałe flagi trafiają do install.py albo update.py bez zmian
  ctf --repo <adres>     # inne repozytorium fabryki (także <adres>#gałąź-lub-tag)

Launcher instalujesz raz, z klonu fabryki albo z projektu, w którym ona już jest:

  python3 factory/ctf.py --install-launcher [--bin ~/.local/bin] [--repo <adres>]

Kopiuje ten skrypt do `--bin` (domyślnie ~/.local/bin; na Windowsie także ctf.cmd) i wpisuje w nim adres repozytorium:
z `--repo`, zmiennej `CTF_REPO`, źródła git z manifestu projektu albo `origin` klonu fabryki.

Adres repozytorium przy instalacji: `--repo`, zmienna `CTF_REPO`, adres wpisany w launcher. Bez `#ref` pobierane jest
najnowsze wydanie (najwyższy tag vX.Y.Z), bez tagów — domyślna gałąź. Przy aktualizacji źródło zapamiętane
w manifeście ma pierwszeństwo, chyba że nie jest repozytorium git (np. stary katalog fabryki) — wtedy ctf podaje
update.py swoje repozytorium. Instalacja i aktualizacja uruchamiają kod z repozytorium — używaj tylko takiego, któremu ufasz.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Adres repozytorium fabryki — wpisuje go --install-launcher (bez danych logowania).
REPO = ""
MANIFEST = Path(".claude") / "factory-manifest.json"


def is_git(src: str) -> bool:
    return src.startswith(("https://", "http://", "git@", "ssh://")) or src.split("#")[0].endswith(".git")


def public(url: str) -> str:
    """Adres bez danych logowania (https://user:token@host/… → https://host/…), żeby nie trafiły do plików i logów."""
    return re.sub(r"^([a-z+]+://)[^/@]*@", r"\1", url)


def latest_tag(url: str) -> str | None:
    """Najwyższy tag wydania vX.Y.Z (bez przedpremierowych); None, gdy brak tagów lub błąd."""
    try:
        r = subprocess.run(["git", "ls-remote", "--tags", "--refs", url, "v*"], capture_output=True, text=True)
    except OSError:
        return None
    tags = re.findall(r"refs/tags/(v(\d+)\.(\d+)\.(\d+))$", r.stdout, re.M) if r.returncode == 0 else []
    return max(tags, key=lambda t: tuple(int(x) for x in t[1:]))[0] if tags else None


def install(repo: str, args: list[str]) -> int:
    url, _, ref = repo.partition("#")
    ref = ref or latest_tag(url) or ""
    print(f"ℹ Instaluję fabrykę z {public(url)}" + (f" ({ref})" if ref else " (domyślna gałąź — brak tagów wydań)"))
    args = ["--dry-run" if a == "--check" else a for a in args]
    with tempfile.TemporaryDirectory(prefix="ctf-") as t:
        clone = Path(t) / "factory"
        r = subprocess.run(["git", "clone", "--depth", "1", "--quiet", *(["--branch", ref] if ref else []), url,
                            str(clone)], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"✗ Nie udało się pobrać {public(repo)}:\n{r.stderr.strip()}")
            return 1
        installer = clone / "factory" / "install.py"
        if not installer.is_file():
            print(f"✗ W {public(repo)} nie ma fabryki (brak factory/install.py).")
            return 1
        return subprocess.run([sys.executable, str(installer), "--source", public(repo), *args]).returncode


def update(repo: str | None, args: list[str]) -> int:
    try:
        saved = json.loads(MANIFEST.read_text(encoding="utf-8")).get("source") or ""
    except (OSError, ValueError):
        saved = ""
    args = ["--check" if a == "--dry-run" else a for a in args]
    if repo and not is_git(saved) and "--source" not in args:
        args = ["--source", public(repo), *args]
    return subprocess.run([sys.executable, str(Path("factory") / "update.py"), *args]).returncode


def origin_of(path: Path) -> str:
    r = subprocess.run(["git", "-C", str(path), "remote", "get-url", "origin"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def install_launcher(repo: str | None, bin_dir: Path) -> int:
    if not repo:
        try:
            saved = json.loads(MANIFEST.read_text(encoding="utf-8")).get("source") or ""
        except (OSError, ValueError):
            saved = ""
        repo = saved if is_git(saved) else origin_of(Path(__file__).resolve().parent.parent)
    if not repo:
        print("✗ Nie znam adresu repozytorium fabryki. Podaj go: --repo https://github.com/<ty>/claude-team-factory.git")
        return 2
    url = public(repo.partition("#")[0])               # launcher zawsze bierze najnowsze wydanie
    text = Path(__file__).read_text(encoding="utf-8")
    text = re.sub(r"^REPO = .*$", lambda m: f"REPO = {url!r}", text, count=1, flags=re.M)
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / "ctf"
    target.write_text(text, encoding="utf-8")
    target.chmod(0o755)
    if os.name == "nt":
        (bin_dir / "ctf.cmd").write_text(f'@"{sys.executable}" "%~dp0ctf" %*\r\n', encoding="utf-8")
    print(f"✓ Zainstalowano {target} (repozytorium: {url})")
    on_path = [Path(p).expanduser().resolve() for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    if bin_dir.resolve() not in on_path:
        print(f"⚠ {bin_dir} nie ma w PATH — dopisz go w profilu powłoki, np. export PATH=\"{bin_dir}:$PATH\"")
    return 0


def main(argv: list[str]) -> int:
    args, repo, bin_dir, launcher = [], None, Path.home() / ".local" / "bin", False
    it = iter(argv[1:])
    for a in it:
        if a in ("-h", "--help"):
            print(__doc__)
            return 0
        if a == "--repo":
            repo = next(it, "")
        elif a == "--bin":
            bin_dir = Path(next(it, "")).expanduser()
        elif a == "--install-launcher":
            launcher = True
        else:
            args.append(a)
    repo = repo or os.environ.get("CTF_REPO") or None
    if launcher:
        return install_launcher(repo, bin_dir)
    if MANIFEST.exists():
        return update(repo or REPO or None, args)
    repo = repo or REPO
    if not repo:
        print("✗ Nie znam adresu repozytorium fabryki. Podaj --repo <adres>, ustaw CTF_REPO albo zainstaluj launcher:\n"
              "  python3 factory/ctf.py --install-launcher --repo https://github.com/<ty>/claude-team-factory.git")
        return 2
    return install(repo, args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
