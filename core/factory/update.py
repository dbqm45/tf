#!/usr/bin/env python3
"""
Aktualizuje claude-team-factory w tym projekcie — jak aktualizacja oprogramowania (tylko biblioteka standardowa).

  python3 factory/update.py --check                      # czy jest nowa wersja i co się zmieniło (nic nie zmienia)
  python3 factory/update.py                              # pokaż plan, zapytaj, zaktualizuj
  python3 factory/update.py --yes                        # bez pytania (np. w skrypcie)
  python3 factory/update.py --source <źródło>            # ustaw źródło (zapamiętywane w manifeście)
  python3 factory/update.py --yes --accept-audit         # zastosuj mimo ustaleń wysokiej wagi w audycie skilli
  python3 factory/update.py --rollback                   # wróć do stanu sprzed ostatniej aktualizacji (kopia w .claude/factory-backup/)
  python3 factory/update.py --auto on|off                # automatyczne wydania PATCH/MINOR (hook startu sesji albo workflow z PR)
  python3 factory/update.py --auto-run                   # jeden przebieg automatu (uruchamia go hook startu sesji w tle)
  python3 factory/update.py --ci --source <URL git>      # przebieg w CI (workflow team-factory-update otwiera z niego PR)
Przed aktualizacją skille nowej wersji przechodzą audyt (`skill_audit.py` z ZAINSTALOWANEJ wersji, nie z pobranej):
ustalenia wysokiej wagi zatrzymują aktualizację z `--yes`, a w trybie interaktywnym wymagają świadomego potwierdzenia.

Źródło nowej wersji (pierwsze dostępne): `--source`, zmienna środowiskowa `TEAM_FACTORY`, wpis `source`
w `.claude/factory-manifest.json`. Ścieżki względne liczone są od bieżącego katalogu. Może to być:
  - katalog z fabryką (np. ~/narzedzia/claude-team-factory, zaktualizowany `git pull`),
  - plik .zip z fabryką (np. ~/Downloads/claude-team-factory.zip),
  - adres repozytorium git (https://… lub git@…): bez dopisku najnowsze wydanie (najwyższy tag `vX.Y.Z`),
    z `#gałąź-lub-tag` dokładnie ten stan (np. `#main` — niewydane zmiany, `#v2.7.0` — przypięta wersja).
Aktualizacja uruchamia instalator z NOWEJ wersji — używaj tylko źródła, któremu ufasz.

Co robi aktualizacja: patrz `python3 factory/install.py` (opis manifestu). Twoje własne skille, persony, role i cechy
zostają; pliki fabryki, które zmieniłeś, też — nowa wersja ląduje obok jako `*.factory-new`.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # katalog projektu (factory/ leży w projekcie)
MANIFEST = ROOT / ".claude" / "factory-manifest.json"


def _semver():
    """Moduł SemVer ze skilla core-semver (precedencja wg semver.org, także wersje przedpremierowe)."""
    import importlib.util
    p = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "core-semver" / "scripts" / "semver.py"
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("ctf_semver", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def vtuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3]) or (0,)


def newer_than(a: str, b: str) -> int:
    """1, gdy a > b; -1, gdy a < b; 0, gdy równe — wg SemVer 2.0.0 (rezerwa: same liczby X.Y.Z)."""
    sv = _semver()
    try:
        if sv:
            return sv.compare(a.strip().lstrip("v"), b.strip().lstrip("v"))
    except ValueError:
        pass
    x, y = vtuple(a), vtuple(b)
    return (x > y) - (x < y)


def is_git(src: str) -> bool:
    return src.startswith(("https://", "http://", "git@", "ssh://")) or src.split("#")[0].endswith(".git")


def normalize(src: str) -> str:
    """Ścieżkę lokalną zamienia na bezwzględną (liczoną od bieżącego katalogu), adres git zostawia bez zmian."""
    return src if is_git(src) else str(Path(src).expanduser().resolve())


def release_tags(url: str, timeout: float | None = None) -> list[str] | None:
    """Tagi wydań `vX.Y.Z` w repozytorium (bez przedpremierowych); None przy błędzie."""
    try:
        r = subprocess.run(["git", "ls-remote", "--tags", "--refs", url, "v*"], capture_output=True, text=True,
                           timeout=timeout, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return [m.group(1) for m in re.finditer(r"refs/tags/(v\d+\.\d+\.\d+)$", r.stdout, re.M)]


def latest_tag(url: str, timeout: float | None = None) -> str | None:
    """Najwyższy tag wydania `vX.Y.Z` w repozytorium; None, gdy brak tagów lub błąd."""
    tags = release_tags(url, timeout)
    if not tags:
        return None
    from functools import cmp_to_key
    return max(tags, key=cmp_to_key(newer_than))


def auto_target(tags: list[str], current: str, skip=()) -> tuple[str | None, str | None]:
    """(cel automatu, najwyższe nowsze wydanie MAJOR): cel to najwyższe wydanie PATCH/MINOR nowsze niż `current`
    w tej samej wersji głównej, z pominięciem wersji z `skip`; MAJOR automat tylko zgłasza."""
    from functools import cmp_to_key
    key = cmp_to_key(newer_than)
    versions = [t[1:] for t in tags if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    newer = [v for v in versions if newer_than(v, current) > 0]
    same = [v for v in newer if vtuple(v)[0] == vtuple(current)[0] and v not in skip]
    major = [v for v in newer if vtuple(v)[0] > vtuple(current)[0]]
    return (max(same, key=key) if same else None), (max(major, key=key) if major else None)


def installer_of(new: Path) -> Path:
    """Instalator w pobranej wersji fabryki (core/factory/install.py)."""
    return new / "core" / "factory" / "install.py"


def fetch(src: str, tmp: Path) -> Path:
    """Zwraca katalog z nową wersją fabryki (zawierający factory/install.py).

    Z repozytorium git bez `#ref` pobiera najnowsze wydanie (tag vX.Y.Z), a bez tagów — domyślną gałąź."""
    if is_git(src):
        url, _, ref = src.partition("#")
        if not ref:
            ref = latest_tag(url) or ""
            print(f"ℹ Najnowsze wydanie: {ref} (niewydane zmiany: {url}#main)." if ref
                  else "ℹ Repozytorium nie ma tagów wydań vX.Y.Z — pobieram domyślną gałąź.")
        cmd = ["git", "clone", "--depth", "1", "--quiet"] + (["--branch", ref] if ref else []) + [url, str(tmp / "repo")]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"✗ Nie udało się pobrać {src}:\n{r.stderr.strip()}")
        base = tmp / "repo"
    else:
        p = Path(src).expanduser().resolve()
        if p.is_file() and p.suffix == ".zip":
            with zipfile.ZipFile(p) as z:
                for name in z.namelist():                      # ochrona przed ścieżkami spoza katalogu (zip slip)
                    if name.startswith("/") or ".." in Path(name).parts:
                        sys.exit(f"✗ Podejrzana ścieżka w archiwum: {name}")
                z.extractall(tmp / "zip")
            base = tmp / "zip"
        elif p.is_dir():
            base = p
        else:
            sys.exit(f"✗ Nie znaleziono źródła: {src}")
    found = [d.parent.parent.parent for d in base.rglob("core/factory/install.py") if "node_modules" not in d.parts]
    if not found:
        sys.exit(f"✗ No factory in {src} (core/factory/install.py is missing).")
    new = min(found, key=lambda d: len(d.parts))
    if new.resolve() == ROOT:
        sys.exit("✗ Źródło wskazuje na ten sam projekt — podaj katalog, archiwum lub repozytorium fabryki.")
    return new


CHECK_EVERY = 86400            # notice: źródło pytane najwyżej raz na dobę
RETRY_FAILED = 3600            # po nieudanym pytaniu (brak sieci) — ponownie po godzinie


def available_version(src: str, timeout: float = 5) -> str | None:
    """Wersja dostępna w źródle bez pobierania całej fabryki; None, gdy nieznana lub źródło przypięte do `#ref`."""
    if is_git(src):
        url, _, ref = src.partition("#")
        if ref:
            return None
        tag = latest_tag(url, timeout=timeout)
        return tag.lstrip("v") if tag else None
    p = Path(src).expanduser()
    try:
        if p.is_file() and p.suffix == ".zip":
            with zipfile.ZipFile(p) as z:
                names = sorted((n for n in z.namelist() if n == "core/factory/VERSION" or n.endswith("/core/factory/VERSION")),
                               key=lambda n: n.count("/"))
                return z.read(names[0]).decode("utf-8").strip() if names else None
        v = p / "core" / "factory" / "VERSION"
        return v.read_text(encoding="utf-8").strip() if v.is_file() else None
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError):
        return None


def notice(root: Path, env: dict | None = None, cache_dir: Path | None = None, now: float | None = None,
           timeout: float = 5) -> str | None:
    """Komunikat o nowszym wydaniu fabryki dla projektu `root` albo None (hook SessionStart: update_notice.py).

    Źródło jak przy aktualizacji (TEAM_FACTORY, potem `source` z manifestu); wynik pytania zapamiętany na dobę
    w katalogu podręcznym użytkownika, wspólnym dla projektów. CTF_UPDATE_CHECK=0 wyłącza. Nigdy nie rzuca wyjątku."""
    import time
    env = os.environ if env is None else env
    try:
        if env.get("CTF_UPDATE_CHECK", "1").strip().lower() in ("0", "false", "nie", "no", "off"):
            return None
        man_p = root / ".claude" / "factory-manifest.json"
        if not man_p.is_file():
            return None
        manifest = json.loads(man_p.read_text(encoding="utf-8"))
        current = manifest.get("version", "0.0.0")
        src = env.get("TEAM_FACTORY") or manifest.get("source")
        if not src:
            return None
        src = src if is_git(src) else str(Path(src).expanduser().resolve())
        now = time.time() if now is None else now
        if cache_dir is None:
            base = env.get("XDG_CACHE_HOME") or str(Path(env.get("HOME") or Path.home()) / ".cache")
            cache_dir = Path(base) / "team-factory"
        cache_p = cache_dir / "update-check.json"
        try:
            cache = json.loads(cache_p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}
        rec = cache.get(src) or {}
        age = now - rec.get("checked", -1e18)
        if 0 <= age < (CHECK_EVERY if rec.get("latest") else RETRY_FAILED):
            latest = rec.get("latest")
        else:
            latest = available_version(src, timeout=timeout)
            cache[src] = {"checked": now, "latest": latest}
            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            except OSError:
                pass
        if not latest or newer_than(latest, current) <= 0:
            return None
        major = " — wydanie MAJOR (zmiany niezgodne wstecz, przeczytaj „Breaking”)" \
            if vtuple(latest)[0] > vtuple(current)[0] else ""
        return (f"Dostępna nowa wersja claude-team-factory: {latest} (zainstalowana {current}){major}. "
                "Co się zmieniło: python3 factory/update.py --check · aktualizacja: python3 factory/update.py "
                "(albo /core-factory-update).")
    except Exception:  # komunikat jest dodatkiem — nigdy nie psuje startu sesji
        return None


def changelog_since(new: Path, current: str) -> str:
    p = new / "core" / "factory" / "CHANGELOG.md"
    if not p.exists():
        return ""
    out, keep = [], False
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## \[?(\d+\.\d+\.\d+[0-9A-Za-z.+-]*)", line)
        if m:
            keep = newer_than(m.group(1), current) > 0
        if keep:
            out.append(line)
    return "\n".join(out).strip()


def audit_new(new_root: Path) -> tuple[int, list[str]]:
    """Audyt skilli pobranej wersji narzędziem z wersji zainstalowanej (pobrane narzędzie mogłoby kłamać)."""
    import importlib.util
    tool = Path(__file__).resolve().parent / "skill_audit.py"
    skill_dirs = [d for d in [new_root / "core" / "skills", *sorted((new_root / "packs").glob("*/skills"))] if d.is_dir()]
    if not tool.exists() or not skill_dirs:
        return 0, []
    spec = importlib.util.spec_from_file_location("skill_audit_installed", tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    high, lines = 0, []
    for d in [x for sd in skill_dirs for x in mod.find_skills(sd)]:
        for f in mod.audit_skill(d)["findings"]:
            if f["severity"] in ("high", "medium"):
                high += f["severity"] == "high"
                lines.append(f"  {'✗' if f['severity'] == 'high' else '⚠'} {d.name}: {f['code']} — {f['file']}:{f['line']} "
                             f"{f['message']}")
    return high, lines


BACKUP_DIR = Path(".claude") / "factory-backup"
BACKUP_KEEP = 3
BACKUP_EXTRA = (".claude/settings.json", ".claude/settings.local.json", "CLAUDE.md", "CLAUDE.local.md", ".gitignore",
                ".claude/factory-manifest.json")


def _sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _factory_new(root: Path, rels) -> list[str]:
    return sorted(r + ".factory-new" for r in rels if (root / (r + ".factory-new")).is_file())


def backup(root: Path, now: float | None = None) -> Path:
    """Pełna kopia przed aktualizacją: pliki z manifestu, ustawienia, CLAUDE.md, .gitignore i manifest, do
    `.claude/factory-backup/<data>-v<wersja>/` ze znacznikiem `backup.json`. Zostają 3 ostatnie takie kopie
    (katalogi bez znacznika — pliki usunięte przez instalator — nie są ruszane)."""
    import shutil
    import time
    manifest = json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
    version = manifest.get("version", "0.0.0")
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time() if now is None else now))
    base = root / BACKUP_DIR
    dest, n = base / f"{stamp}-v{version}", 1
    while dest.exists():
        n += 1
        dest = base / f"{stamp}-v{version}-{n}"
    files = [r for r in [*manifest.get("files", {}), *BACKUP_EXTRA] if (root / r).is_file()]
    for rel in files:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, dest / rel)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "backup.json").write_text(json.dumps({
        "version": version, "files": files, "factory_new": _factory_new(root, manifest.get("files", {})),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for old in sorted(d for d in base.iterdir() if (d / "backup.json").is_file())[:-BACKUP_KEEP]:
        shutil.rmtree(old, ignore_errors=True)
    return dest


PREFLIGHT_DIRS = (".claude", ".claude/skills", ".claude/hooks", ".claude/agents/_generated", ".claude/tests", "factory")
PREFLIGHT_FILES = (".claude/settings.json", ".claude/factory-manifest.json", "CLAUDE.md", ".git/info/exclude")


def unwritable(root: Path) -> list[str]:
    """Istniejące ścieżki, do których aktualizacja pisze, a zapis się nie udaje (np. piaskownica Bash agenta).
    Sprawdza próbnym plikiem tymczasowym w katalogu i otwarciem pliku do dopisania — bez zmiany treści."""
    bad = []
    for rel in PREFLIGHT_DIRS:
        d = root / rel
        if not d.exists():
            continue
        try:
            fd, tmp = tempfile.mkstemp(prefix=".ctf-probe-", dir=d)
            os.close(fd)
            os.unlink(tmp)
        except OSError:
            bad.append(rel + "/")
    for rel in PREFLIGHT_FILES:
        p = root / rel
        if not p.exists():
            continue
        try:
            open(p, "a").close()
        except OSError:
            bad.append(rel)
    return bad


def preflight(root: Path, command: str) -> tuple[int, str]:
    """Przed pierwszym zapisem: gdy czegoś nie da się zapisać, przerwij, zamiast zostawić instalację w połowie."""
    bad = unwritable(root)
    if not bad:
        return 0, ""
    return 2, ("✗ Nie mogę zapisać: " + ", ".join(bad) + " — nic nie zmieniłem.\n"
               "Aktualizacja zmienia skille, hooki i ustawienia, a piaskownica Bash agenta celowo tego nie przepuszcza.\n"
               f"Uruchom polecenie sam w terminalu (poza Claude Code): {command}")


def rollback(root: Path) -> tuple[int, str]:
    """`--rollback`: wraca do stanu z ostatniej kopii. Pliki dodane przez aktualizację usuwa tylko, gdy ich nie
    zmieniałeś; usuwa też `.factory-new` powstałe przy aktualizacji."""
    import shutil
    base = root / BACKUP_DIR
    copies = sorted(d for d in base.iterdir() if (d / "backup.json").is_file()) if base.is_dir() else []
    if not copies:
        return 2, f"✗ Brak kopii w {BACKUP_DIR.as_posix()} — nie mam do czego wrócić."
    src = copies[-1]
    meta = json.loads((src / "backup.json").read_text(encoding="utf-8"))
    man_p = root / ".claude" / "factory-manifest.json"
    current = json.loads(man_p.read_text(encoding="utf-8")) if man_p.is_file() else {}
    cur_files = current.get("files", {})
    kept = set(meta.get("files", []))
    for rel in _factory_new(root, cur_files):
        if rel not in meta.get("factory_new", []):
            (root / rel).unlink()
    left = []
    for rel, h in cur_files.items():
        p = root / rel
        if rel in kept or not p.is_file():
            continue
        if _sha(p) == h:
            p.unlink()
        else:
            left.append(rel)
    for rel in meta.get("files", []):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, root / rel)
    msg = (f"✓ Przywrócono wersję {meta.get('version')} (była {current.get('version', '?')}) z "
           f"{src.relative_to(root).as_posix()}. Uruchom Claude Code ponownie.")
    if left:
        msg += "\nZostawiam pliki dodane przez aktualizację, które zmieniłeś: " + ", ".join(sorted(left))
    return 0, msg


WORKFLOW = Path(".github") / "workflows" / "team-factory-update.yml"
WORKFLOW_TEMPLATE = Path("factory") / "templates" / "team-factory-update.yml"


def set_auto(root: Path, on: bool, env: dict | None = None) -> tuple[int, str]:
    """`--auto on|off`: tryb prywatny — flaga `auto_update` w manifeście (instaluje hook startu sesji); tryb zespołowy —
    workflow `.github/workflows/team-factory-update.yml` (cotygodniowy PR) i ta sama flaga. Źródło musi być
    repozytorium git bez `#ref` — automat instaluje wyłącznie wydania (tagi vX.Y.Z)."""
    env = os.environ if env is None else env
    man_p = root / ".claude" / "factory-manifest.json"
    if not man_p.is_file():
        return 2, "✗ Brak .claude/factory-manifest.json — fabryka nie jest zainstalowana w tym projekcie."
    manifest = json.loads(man_p.read_text(encoding="utf-8"))
    shared = manifest.get("mode") == "shared"
    wf = root / WORKFLOW
    lines = []
    if on:
        src = env.get("TEAM_FACTORY") or manifest.get("source") or ""
        if not is_git(src) or "#" in src:
            return 2, ("✗ Automatyczna aktualizacja wymaga źródła będącego repozytorium git z tagami wydań vX.Y.Z "
                       f"(bez #gałęzi), a jest: {src or 'brak'}. Ustaw je: python3 factory/update.py --source <URL git>")
        if shared:
            tpl = root / WORKFLOW_TEMPLATE
            if not tpl.is_file():
                return 2, f"✗ Brak szablonu {WORKFLOW_TEMPLATE} — zaktualizuj fabrykę."
            wf.parent.mkdir(parents=True, exist_ok=True)
            wf.write_text(tpl.read_text(encoding="utf-8").replace("__CTF_SOURCE__", src), encoding="utf-8")
            lines += [f"Dodano {WORKFLOW.as_posix()} — zacommituj go. Raz w tygodniu otworzy PR z nowym wydaniem "
                      "PATCH/MINOR, gdy testy i `build.py check` przejdą (MAJOR tylko zgłasza).",
                      "Włącz w repozytorium: Settings → Actions → General → Workflow permissions → "
                      "„Allow GitHub Actions to create and approve pull requests”."]
        else:
            lines.append("Nowe wydania PATCH/MINOR instalują się przy starcie sesji (w tle, działają od następnej sesji); "
                         "MAJOR tylko zgłaszam. Historia: .claude/logs/update.jsonl.")
    elif shared and wf.exists():
        wf.unlink()
        lines.append(f"Usunięto {WORKFLOW.as_posix()} — zacommituj zmianę.")
    manifest["auto_update"] = on
    man_p.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    head = "✓ Automatyczna aktualizacja fabryki włączona." if on else "✓ Automatyczna aktualizacja fabryki wyłączona."
    return 0, "\n".join([head] + lines)


LOG = Path(".claude") / "logs" / "update.jsonl"
SEEN = Path(".claude") / "logs" / "update.seen"
LOCK = Path(".claude") / "logs" / "update.lock"
LOCK_STALE = 3600              # blokada starsza niż godzina to ślad po przerwanym przebiegu
SKIP_STATUSES = ("tests_failed", "install_failed", "audit_blocked")


def _log(root: Path) -> list[dict]:
    p = root / LOG
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _append_log(root: Path, entry: dict) -> None:
    p = root / LOG
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _lock(root: Path, now: float) -> bool:
    p = root / LOCK
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        if p.exists() and now - p.stat().st_mtime > LOCK_STALE:
            p.unlink()
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        return False
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return True


def auto_run(root: Path, env: dict | None = None, now: float | None = None, timeout: float = 20) -> dict:
    """Jeden przebieg automatu (tryb prywatny, w tle ze startu sesji): najwyższe wydanie PATCH/MINOR → audyt skilli →
    kopia → instalator → testy fabryki; czerwone testy lub błąd instalatora → powrót do kopii i pominięcie wersji.
    Wynik (poza „nic nowego”) trafia do `.claude/logs/update.jsonl`; pokazuje go `pending_messages`."""
    import time
    env = os.environ if env is None else env
    now = time.time() if now is None else now
    man_p = root / ".claude" / "factory-manifest.json"
    manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.is_file() else {}
    if manifest.get("auto_update") is not True:
        return {"status": "off"}
    if not _lock(root, now):
        return {"status": "locked"}
    try:
        return _auto_run(root, manifest, env, now, timeout)
    finally:
        (root / LOCK).unlink(missing_ok=True)


def _auto_run(root: Path, manifest: dict, env, now: float, timeout: float) -> dict:
    src = env.get("TEAM_FACTORY") or manifest.get("source") or ""
    if not is_git(src) or "#" in src:
        return {"status": "no_source"}
    tags = release_tags(src, timeout)
    if tags is None:
        return {"status": "offline"}
    current = manifest.get("version", "0.0.0")
    skip = [e.get("to") for e in _log(root) if e.get("status") in SKIP_STATUSES]
    target, major = auto_target(tags, current, skip)
    if not target:
        return {"status": "none", "major": major}
    entry = {"ts": int(now), "from": current, "to": target, "major": major}

    def done(status: str, **extra) -> dict:
        entry.update(status=status, **extra)
        _append_log(root, entry)
        return entry

    with tempfile.TemporaryDirectory(prefix="tf-auto-") as t:
        try:
            new = fetch(f"{src}#v{target}", Path(t))
        except SystemExit as e:
            return done("install_failed", error=str(e.code))
        high, findings = audit_new(new)
        if high:
            return done("audit_blocked", findings=findings)
        backup(root, now)
        r = subprocess.run([sys.executable, str(installer_of(new)), str(root), "--update", "--source", src],
                           capture_output=True, text=True)
        if r.returncode != 0:
            rollback(root)
            return done("install_failed", error=(r.stderr or r.stdout).strip()[-500:])
        notes = changelog_since(new, current)
    failed = _run_tests(root)
    if failed:
        rollback(root)
        return done("tests_failed", failed=failed)
    man = json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
    return done("installed", notes=notes, factory_new=_factory_new(root, man.get("files", {})))


def _run_tests(root: Path) -> list[str]:
    """Testy fabryki w projekcie (`.claude/tests/test_*.py`); zwraca nazwy czerwonych."""
    failed = []
    for test in sorted((root / ".claude" / "tests").glob("test_*.py")):
        try:
            res = subprocess.run([sys.executable, str(test)], cwd=root, capture_output=True, text=True, timeout=600)
            ok = res.returncode == 0
        except subprocess.TimeoutExpired:
            ok = False
        if not ok:
            failed.append(test.name)
    return failed


PR_BODY = Path(".claude") / "logs" / "update-pr.md"
WORKFLOWS = Path(".github") / "workflows"


def _ci_manifest(root: Path, src: str) -> dict:
    """Manifest dla CI. W trybie zespołowym jest w .gitignore, więc po checkout go nie ma: odtwarza go instalator
    wersji z `factory/VERSION` (tag v<wersja>) uruchomiony na pustym katalogu — daje te same skróty plików."""
    man_p = root / ".claude" / "factory-manifest.json"
    if man_p.is_file():
        return json.loads(man_p.read_text(encoding="utf-8"))
    current = (root / "factory" / "VERSION").read_text(encoding="utf-8").strip()
    with tempfile.TemporaryDirectory(prefix="tf-ci-") as t:
        old = fetch(f"{src}#v{current}", Path(t))
        scratch = Path(t) / "scratch"
        scratch.mkdir()
        packs = sorted(p.parent.name for p in (root / "factory" / "packs").glob("*/pack.yaml"))
        settings = {}
        try:
            settings = json.loads((root / ".claude" / "factory-settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        lang = [a for k in ("language", "commit_language") if settings.get(k)
                for a in (f"--{k.replace('_', '-')}", settings[k])]
        r = subprocess.run([sys.executable, str(installer_of(old)), str(scratch), "--shared", "--yes",
                            "--packs", ",".join(packs) or "none", *lang, "--source", src], capture_output=True, text=True)
        rebuilt = scratch / ".claude" / "factory-manifest.json"
        if r.returncode != 0 or not rebuilt.is_file():
            sys.exit(f"✗ Nie udało się odtworzyć manifestu wersji {current}:\n{(r.stderr or r.stdout).strip()[-500:]}")
        manifest = json.loads(rebuilt.read_text(encoding="utf-8"))
    manifest.update(mode="shared", source=src, auto_update=True)
    man_p.parent.mkdir(parents=True, exist_ok=True)
    man_p.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return manifest


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def ci_run(root: Path, src: str, env: dict | None = None) -> int:
    """Tryb zespołowy w CI (workflow team-factory-update): najwyższe wydanie PATCH/MINOR → audyt skilli → instalator
    → testy fabryki i `factory/build.py check`. Zielone → opis PR w `.claude/logs/update-pr.md` i `version=X`
    w `$GITHUB_OUTPUT` (workflow otwiera PR); czerwone → kod 1 (czerwony job to powiadomienie), bez PR."""
    env = os.environ if env is None else env
    if not is_git(src) or "#" in src:
        print("✗ Tryb --ci wymaga adresu repozytorium git fabryki bez #ref (wydania to tagi vX.Y.Z).")
        return 2
    manifest = _ci_manifest(root, src)
    current = manifest.get("version", "0.0.0")
    tags = release_tags(src, 60)
    if tags is None:
        print(f"✗ Nie udało się odczytać wydań z {src}.")
        return 1
    target, major = auto_target(tags, current)
    if major:
        print(f"⚠ Dostępne wydanie MAJOR {major} — automat go nie instaluje (python3 factory/update.py lokalnie).")
    if not target:
        print(f"✓ Brak nowego wydania PATCH/MINOR (zainstalowana {current}).")
        return 0
    print(f"Aktualizacja claude-team-factory {current} → {target}")
    with tempfile.TemporaryDirectory(prefix="tf-ci-") as t:
        new = fetch(f"{src}#v{target}", Path(t))
        high, findings = audit_new(new)
        if high:
            print(f"✗ Audyt skilli wersji {target}: ustalenia wysokiej wagi — aktualizacja wstrzymana:")
            print("\n".join(findings[:30]))
            return 1
        r = subprocess.run([sys.executable, str(installer_of(new)), str(root), "--update", "--source", src],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"✗ Instalator wersji {target} zakończył się błędem:\n{(r.stderr or r.stdout).strip()[-1500:]}")
            return 1
        notes = changelog_since(new, current)
    failed = _run_tests(root)
    build = root / "factory" / "build.py"
    if build.is_file():
        b = subprocess.run([sys.executable, str(build), "check"], cwd=root, capture_output=True, text=True)
        if b.returncode != 0:
            failed.append("factory/build.py check")
            print((b.stdout + b.stderr).strip()[-1500:])
    if failed:
        print(f"✗ Po instalacji {target} czerwone: {', '.join(failed)} — bez PR. Sprawdź lokalnie: "
              f"python3 factory/update.py --source {src}#v{target}")
        return 1
    st = _git(root, "status", "--porcelain", "-uall", "--", WORKFLOWS.as_posix())
    workflows = sorted({ln[3:].strip() for ln in st.stdout.splitlines() if ln.strip()})
    if workflows:
        _git(root, "checkout", "HEAD", "--", WORKFLOWS.as_posix())
        _git(root, "clean", "-fdq", "--", WORKFLOWS.as_posix())
    man = json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
    lines = [f"Aktualizacja claude-team-factory {current} → {target} (wydanie PATCH/MINOR; testy fabryki i "
             "`factory/build.py check` zielone).", ""]
    if notes:
        lines += ["## Co nowego", "", notes, ""]
    if major:
        lines += [f"⚠ Dostępne jest też wydanie MAJOR {major} — automat go nie instaluje; zaktualizuj lokalnie "
                  "(`python3 factory/update.py`) po przeczytaniu sekcji „Breaking”.", ""]
    fresh = _factory_new(root, man.get("files", {}))
    if fresh:
        lines += ["## Pliki zmienione w projekcie", "",
                  "Te pliki fabryki zmieniliście lokalnie, więc zostały bez zmian; nowej wersji nie ma w tym PR. "
                  "Scal ręcznie: `python3 factory/update.py` lokalnie zostawi ją obok jako `*.factory-new`.", ""]
        lines += [f"- `{f[:-len('.factory-new')]}`" for f in fresh] + [""]
    if workflows:
        lines += ["## Workflow do przeniesienia ręcznie", "",
                  "GITHUB_TOKEN nie może wypchnąć zmian w `.github/workflows/`, więc nie ma ich w tym PR. Przenieś je "
                  "ręcznie (np. `python3 factory/update.py` lokalnie):", ""]
        lines += [f"- `{w}`" for w in workflows] + [""]
    body = root / PR_BODY
    body.parent.mkdir(parents=True, exist_ok=True)
    body.write_text("\n".join(lines), encoding="utf-8")
    out = env.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"version={target}\n")
    print(f"✓ Zainstalowano {target}; opis PR: {PR_BODY.as_posix()}")
    return 0


def _spawn(cmd: list[str], cwd: Path) -> None:
    """Proces odłączony od sesji: przeżywa koniec hooka (limit czasu hooka to kilkanaście sekund)."""
    kw = {"creationflags": 0x00000008 | 0x00000200} if os.name == "nt" else {"start_new_session": True}
    subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)


def start_auto(root: Path, env: dict | None = None, cache_dir: Path | None = None, now: float | None = None,
               timeout: float = 5, spawn=None) -> str | None:
    """Hook startu sesji (tryb prywatny z `--auto on`): najwyżej raz na dobę sprawdza wydania i, gdy jest nowe
    PATCH/MINOR, uruchamia `update.py --auto-run` w tle. Zwraca komunikat dla człowieka albo None. Nigdy nie rzuca."""
    import time
    env = os.environ if env is None else env
    try:
        if env.get("CTF_UPDATE_CHECK", "1").strip().lower() in ("0", "false", "nie", "no", "off"):
            return None
        man_p = root / ".claude" / "factory-manifest.json"
        manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.is_file() else {}
        if manifest.get("auto_update") is not True or manifest.get("mode") == "shared":
            return None
        src = env.get("TEAM_FACTORY") or manifest.get("source") or ""
        if not is_git(src) or "#" in src:
            return None
        now = time.time() if now is None else now
        lock = root / LOCK
        if lock.exists() and now - lock.stat().st_mtime <= LOCK_STALE:
            return None
        if cache_dir is None:
            base = env.get("XDG_CACHE_HOME") or str(Path(env.get("HOME") or Path.home()) / ".cache")
            cache_dir = Path(base) / "team-factory"
        cache_p, key = cache_dir / "update-check.json", f"auto:{root.resolve()}"
        try:
            cache = json.loads(cache_p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}
        rec = cache.get(key) or {}
        if 0 <= now - rec.get("checked", -1e18) < (CHECK_EVERY if rec.get("ok") else RETRY_FAILED):
            return None
        tags = release_tags(src, timeout)
        cache[key] = {"checked": now, "ok": tags is not None}
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
        current = manifest.get("version", "0.0.0")
        skip = [e.get("to") for e in _log(root) if e.get("status") in SKIP_STATUSES]
        target, _ = auto_target(tags or [], current, skip)
        if not target:
            return None
        (spawn or _spawn)([sys.executable, str(root / "factory" / "update.py"), "--auto-run"], root)
        return (f"Instaluję w tle aktualizację claude-team-factory {current} → {target} (PATCH/MINOR, kopia i testy); "
                "zadziała od następnej sesji, wynik pokażę przy jej starcie. Wyłączenie: python3 factory/update.py "
                "--auto off")
    except Exception:  # automat jest dodatkiem — nigdy nie psuje startu sesji
        return None


def pending_messages(root: Path) -> list[str]:
    """Komunikaty o przebiegach automatu, których człowiek jeszcze nie widział (pokazywane raz, przy starcie sesji)."""
    entries = _log(root)
    seen_p = root / SEEN
    try:
        seen = int(seen_p.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        seen = 0
    new = entries[seen:] if seen <= len(entries) else entries
    if not new:
        return []
    seen_p.write_text(str(len(entries)), encoding="utf-8")
    out = []
    for e in new:
        a, b, st = e.get("from"), e.get("to"), e.get("status")
        if st == "installed":
            lines = [f"✓ Fabryka zaktualizowana automatycznie: {a} → {b} (powrót: python3 factory/update.py --rollback)."]
            notes = (e.get("notes") or "").splitlines()
            if notes:
                lines += ["Co nowego:"] + notes[:15] + (["…"] if len(notes) > 15 else [])
            if e.get("factory_new"):
                lines.append("Nowe wersje plików, które zmieniłeś (porównaj i scal): " + ", ".join(e["factory_new"]))
        elif st == "tests_failed":
            lines = [f"✗ Automatyczna aktualizacja {a} → {b} cofnięta: testy po instalacji nie przeszły "
                     f"({', '.join(e.get('failed', []))}). Wersja {b} pominięta — sprawdź ręcznie: "
                     "python3 factory/update.py"]
        elif st == "audit_blocked":
            lines = [f"✗ Automatyczna aktualizacja {a} → {b} wstrzymana: audyt skilli znalazł ustalenia wysokiej wagi. "
                     f"Wersja {b} pominięta — przeczytaj je i zdecyduj: python3 factory/update.py"]
            lines += e.get("findings", [])[:10]
        elif st == "install_failed":
            lines = [f"✗ Automatyczna aktualizacja {a} → {b} nie powiodła się (instalator) i została cofnięta. "
                     f"Wersja {b} pominięta: {e.get('error', '')}".rstrip(": ")]
        else:
            continue
        if e.get("major"):
            lines.append(f"⚠ Dostępne wydanie MAJOR {e['major']} — automat go nie instaluje (zmiany niezgodne wstecz). "
                         "Zobacz: python3 factory/update.py --check")
        out.append("\n".join(lines))
    return out


PASS_THROUGH = ("--packs", "--add", "--remove", "--language", "--commit-language")   # → instalator nowej wersji


def main(argv: list[str]) -> int:
    opts, it, passthrough = {}, iter(argv[1:]), []
    for a in it:
        if a == "--source":
            opts["source"] = next(it, "")
        elif a in PASS_THROUGH:
            passthrough += [a, next(it, "")]
        elif a == "--auto":
            val = next(it, "")
            if val not in ("on", "off"):
                print("✗ Użycie: python3 factory/update.py --auto on|off")
                return 2
            code, msg = set_auto(ROOT, val == "on")
            print(msg)
            return code
        elif a == "--rollback":
            code, msg = preflight(ROOT, "python3 factory/update.py --rollback")
            if not code:
                code, msg = rollback(ROOT)
            print(msg)
            return code
        elif a == "--ci":
            opts["--ci"] = True
        elif a == "--auto-run":
            print(json.dumps(auto_run(ROOT), ensure_ascii=False))
            return 0
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    if opts.get("--ci"):
        src = opts.get("source") or os.environ.get("TEAM_FACTORY") or manifest.get("source") or ""
        return ci_run(ROOT, normalize(src) if src else src)
    current = manifest.get("version", "0.0.0")
    env = os.environ.get("TEAM_FACTORY")
    saved = manifest.get("source")
    if saved and not is_git(saved) and not Path(saved).exists() and not opts.get("source") and not env:
        print(f"✗ Zapamiętane źródło {saved} już nie istnieje (fabryka przeniesiona?). Podaj nowe:\n"
              "  python3 factory/update.py --source <katalog|plik.zip|URL git>\n"
              "  albo ustaw raz w profilu powłoki: export TEAM_FACTORY=<katalog fabryki>")
        return 2
    src = opts.get("source") or env or saved
    if not src:
        print("✗ Nie wiem, skąd pobrać nową wersję. Podaj źródło, np.:\n"
              "  python3 factory/update.py --source ~/Downloads/claude-team-factory.zip\n"
              "  python3 factory/update.py --source https://github.com/<ty>/claude-team-factory.git\n"
              "  albo ustaw raz w profilu powłoki: export TEAM_FACTORY=<katalog fabryki>")
        return 2
    src = normalize(src)

    with tempfile.TemporaryDirectory(prefix="tf-update-") as t:
        new = fetch(src, Path(t))
        new_version = (new / "core" / "factory" / "VERSION").read_text(encoding="utf-8").strip() \
            if (new / "core" / "factory" / "VERSION").exists() else "0.0.0"
        print(f"Zainstalowana wersja: {current}   dostępna: {new_version}   (źródło: {src})")
        newer = newer_than(new_version, current) > 0
        if passthrough:                       # zmiana nakładek albo języka — ta sama wersja też się nakłada
            print("ℹ Changing packs or languages: " + " ".join(passthrough))
        if not newer and not opts.get("--force") and not passthrough:
            if newer_than(new_version, current) < 0:
                print("ℹ Źródło ma starszą wersję niż zainstalowana — nic nie robię (wymuś: --force).")
            else:
                print("✓ Masz aktualną wersję. (Ponowne nałożenie tej samej wersji: --force.)")
            return 0
        notes = changelog_since(new, current)
        if notes:
            print("\nCo nowego:\n" + notes + "\n")
        if vtuple(new_version)[0] > vtuple(current)[0]:
            print(f"⚠ To wydanie MAJOR ({current} → {new_version}): zawiera zmiany niezgodne wstecz. Przeczytaj sekcje "
                  "„Breaking” (w starszych wpisach: „Niezgodne”) powyżej — opisują, co zrobić po aktualizacji "
                  "(SemVer, factory/PUBLIC_API.md).\n")
        if opts.get("--check"):
            return 0

        high, findings = audit_new(new)
        if findings:
            print(f"Audyt skilli nowej wersji ({len(findings)} ustaleń, wysokiej wagi: {high}):")
            print("\n".join(findings[:30]) + ("\n  …" if len(findings) > 30 else "") + "\n")
        else:
            print("Audyt skilli nowej wersji: brak ustaleń wysokiej i średniej wagi.\n")
        installer = [sys.executable, str(installer_of(new)), str(ROOT), "--update", "--yes", "--source", src, *passthrough]
        print("Plan aktualizacji:")
        subprocess.run(installer + ["--dry-run"], check=False)
        if opts.get("--dry-run"):
            return 0
        if high and opts.get("--yes") and not opts.get("--accept-audit"):
            print("✗ Audyt znalazł ustalenia wysokiej wagi — aktualizacja wstrzymana. Przeczytaj wskazane pliki; jeśli "
                  "akceptujesz ryzyko, uruchom ponownie z --accept-audit.")
            return 1
        if high and not opts.get("--yes"):
            print("⚠ Audyt znalazł ustalenia wysokiej wagi. Zanim potwierdzisz, przeczytaj wskazane pliki.")
        if not opts.get("--yes"):
            if not sys.stdin.isatty():
                print("\nUruchom ponownie z --yes, żeby zastosować (brak terminala do potwierdzenia).")
                return 1
            if input("\nZastosować aktualizację? [t/N] ").strip().lower() not in ("t", "tak", "y", "yes"):
                print("Przerwano — nic nie zmieniono.")
                return 1
        code, msg = preflight(ROOT, "python3 factory/update.py --yes")
        if code:
            print(msg)
            return code
        if MANIFEST.exists():
            print(f"Kopia przed aktualizacją: {backup(ROOT).relative_to(ROOT).as_posix()} "
                  "(powrót: python3 factory/update.py --rollback)")
        r = subprocess.run(installer, check=False)
        if r.returncode != 0:
            return r.returncode
    print("\nSprawdzenie po aktualizacji:")
    for test in sorted((ROOT / ".claude" / "tests").glob("test_*.py")):
        res = subprocess.run([sys.executable, str(test)], cwd=ROOT, capture_output=True, text=True)
        print(("  " + (res.stdout.strip().splitlines() or ["?"])[-1]) if res.returncode == 0
              else f"  ✗ {test.name} — uruchom `python3 .claude/tests/{test.name}`, żeby zobaczyć szczegóły")
    print("Gotowe. Jeśli Claude Code jest otwarty, uruchom go ponownie, żeby wczytał nowe skille i agentów.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
