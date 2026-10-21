#!/usr/bin/env python3
"""
Updates the team factory in this project, like a software update (standard library only).

  python3 factory/update.py --check                      # is there a new version and what changed (changes nothing)
  python3 factory/update.py                              # show the plan, ask, update
  python3 factory/update.py --yes                        # no question (e.g. in a script)
  python3 factory/update.py --source <source>            # set the source (remembered in the manifest)
  python3 factory/update.py --yes --accept-audit         # apply despite high-severity skill audit findings
  python3 factory/update.py --rollback                   # go back to the state before the last update (copy in .claude/factory-backup/)
  python3 factory/update.py --auto on|off                # automatic PATCH/MINOR releases (session start hook or a PR workflow)
  python3 factory/update.py --auto-run                   # one automatic run (the session start hook runs it in the background)
  python3 factory/update.py --ci --source <git URL>      # CI run (the team-factory-update workflow opens a PR from it)
  python3 factory/update.py --packs a,b|all|none         # change packs (also --add x, --remove y); same version is re-applied
  python3 factory/update.py --language pl --commit-language en   # change languages; same version is re-applied
Before updating, the skills of the new version are audited (`skill_audit.py` from the INSTALLED version, not the
downloaded one): high-severity findings stop an update with `--yes` and need explicit confirmation interactively.

Source of the new version (first available): `--source`, environment variable `TEAM_FACTORY`, the `source` entry
in `.claude/factory-manifest.json`. Relative paths are resolved from the current directory. It can be:
  - the factory directory (e.g. ~/tools/team-factory, kept current with `git pull`),
  - a .zip file with the factory (e.g. ~/Downloads/team-factory.zip),
  - a git repository URL (https://… or git@…): without a suffix the latest release (highest `vX.Y.Z` tag),
    with `#branch-or-tag` exactly that state (e.g. `#main` — unreleased changes, `#v2.7.0` — a pinned version).
The update runs the installer of the NEW version (`core/factory/install.py` in the source) — use only a source you trust.

What an update does: see `python3 <source>/core/factory/install.py --help` (manifest description). Your own skills,
personas, roles and traits stay; factory files you changed stay too — the new version lands next to them as
`*.factory-new`.
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
    """Zwraca katalog główny nowej wersji fabryki (zawierający core/factory/install.py).

    Z repozytorium git bez `#ref` pobiera najnowsze wydanie (tag vX.Y.Z), a bez tagów — domyślną gałąź."""
    if is_git(src):
        url, _, ref = src.partition("#")
        if not ref:
            ref = latest_tag(url) or ""
            print(f"ℹ Latest release: {ref} (unreleased changes: {url}#main)." if ref
                  else "ℹ The repository has no vX.Y.Z release tags — fetching the default branch.")
        cmd = ["git", "clone", "--depth", "1", "--quiet"] + (["--branch", ref] if ref else []) + [url, str(tmp / "repo")]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"✗ Could not fetch {src}:\n{r.stderr.strip()}")
        base = tmp / "repo"
    else:
        p = Path(src).expanduser().resolve()
        if p.is_file() and p.suffix == ".zip":
            with zipfile.ZipFile(p) as z:
                for name in z.namelist():                      # ochrona przed ścieżkami spoza katalogu (zip slip)
                    if name.startswith("/") or ".." in Path(name).parts:
                        sys.exit(f"✗ Suspicious path in the archive: {name}")
                z.extractall(tmp / "zip")
            base = tmp / "zip"
        elif p.is_dir():
            base = p
        else:
            sys.exit(f"✗ Source not found: {src}")
    found = [d.parent.parent.parent for d in base.rglob("core/factory/install.py") if "node_modules" not in d.parts]
    if not found:
        sys.exit(f"✗ No factory in {src} (core/factory/install.py is missing).")
    new = min(found, key=lambda d: len(d.parts))
    if new.resolve() == ROOT:
        sys.exit("✗ The source points at this project — give the factory directory, archive or repository.")
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
        major = " — a MAJOR release (backward-incompatible changes, read „Breaking”)" \
            if vtuple(latest)[0] > vtuple(current)[0] else ""
        return (f"New team factory version available: {latest} (installed {current}){major}. "
                "What changed: python3 factory/update.py --check · update: python3 factory/update.py "
                "(or /core-factory-update).")
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
    skill_dirs = [d for d in [new_root / "core" / "skills", *sorted((new_root / "packs").glob("*/skills")),
                  *sorted((new_root / "modes").glob("*/skills"))] if d.is_dir()]
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
    return 2, ("✗ Cannot write: " + ", ".join(bad) + " — nothing was changed.\n"
               "The update changes skills, hooks and settings, and the agent's Bash sandbox blocks that on purpose.\n"
               f"Run the command yourself in a terminal (outside Claude Code): {command}")


def rollback(root: Path) -> tuple[int, str]:
    """`--rollback`: wraca do stanu z ostatniej kopii. Pliki dodane przez aktualizację usuwa tylko, gdy ich nie
    zmieniałeś; usuwa też `.factory-new` powstałe przy aktualizacji."""
    import shutil
    base = root / BACKUP_DIR
    copies = sorted(d for d in base.iterdir() if (d / "backup.json").is_file()) if base.is_dir() else []
    if not copies:
        return 2, f"✗ No backup in {BACKUP_DIR.as_posix()} — nothing to roll back to."
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
    msg = (f"✓ Restored version {meta.get('version')} (was {current.get('version', '?')}) from "
           f"{src.relative_to(root).as_posix()}. Restart Claude Code.")
    if left:
        msg += "\nKeeping files added by the update that you changed: " + ", ".join(sorted(left))
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
        return 2, "✗ No .claude/factory-manifest.json — the factory is not installed in this project."
    manifest = json.loads(man_p.read_text(encoding="utf-8"))
    shared = manifest.get("mode") == "shared"
    wf = root / WORKFLOW
    lines = []
    if on:
        src = env.get("TEAM_FACTORY") or manifest.get("source") or ""
        if not is_git(src) or "#" in src:
            return 2, ("✗ Automatic updates need a git repository source with vX.Y.Z release tags "
                       f"(no #branch), but it is: {src or 'none'}. Set it: python3 factory/update.py --source <git URL>")
        if shared:
            tpl = root / WORKFLOW_TEMPLATE
            if not tpl.is_file():
                return 2, f"✗ Template {WORKFLOW_TEMPLATE} is missing — update the factory."
            wf.parent.mkdir(parents=True, exist_ok=True)
            wf.write_text(tpl.read_text(encoding="utf-8").replace("__CTF_SOURCE__", src), encoding="utf-8")
            lines += [f"Added {WORKFLOW.as_posix()} — commit it. Once a week it opens a PR with a new PATCH/MINOR "
                      "release when the tests and `build.py check` pass (MAJOR is only reported).",
                      "Enable in the repository: Settings → Actions → General → Workflow permissions → "
                      "„Allow GitHub Actions to create and approve pull requests”."]
        else:
            lines.append("New PATCH/MINOR releases install at session start (in the background, active from the next "
                         "session); MAJOR is only reported. History: .claude/logs/update.jsonl.")
    elif shared and wf.exists():
        wf.unlink()
        lines.append(f"Removed {WORKFLOW.as_posix()} — commit the change.")
    manifest["auto_update"] = on
    man_p.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    head = "✓ Automatic factory updates enabled." if on else "✓ Automatic factory updates disabled."
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
            sys.exit(f"✗ Could not rebuild the manifest of version {current}:\n{(r.stderr or r.stdout).strip()[-500:]}")
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
        print("✗ --ci needs the git URL of the factory repository without #ref (releases are vX.Y.Z tags).")
        return 2
    manifest = _ci_manifest(root, src)
    current = manifest.get("version", "0.0.0")
    tags = release_tags(src, 60)
    if tags is None:
        print(f"✗ Could not read releases from {src}.")
        return 1
    target, major = auto_target(tags, current)
    if major:
        print(f"⚠ MAJOR release {major} available — not installed automatically (run python3 factory/update.py locally).")
    if not target:
        print(f"✓ No new PATCH/MINOR release (installed {current}).")
        return 0
    print(f"Updating the team factory {current} → {target}")
    with tempfile.TemporaryDirectory(prefix="tf-ci-") as t:
        new = fetch(f"{src}#v{target}", Path(t))
        high, findings = audit_new(new)
        if high:
            print(f"✗ Skill audit of version {target}: high-severity findings — update stopped:")
            print("\n".join(findings[:30]))
            return 1
        r = subprocess.run([sys.executable, str(installer_of(new)), str(root), "--update", "--source", src],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"✗ The installer of version {target} failed:\n{(r.stderr or r.stdout).strip()[-1500:]}")
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
        print(f"✗ Failing after installing {target}: {', '.join(failed)} — no PR. Check locally: "
              f"python3 factory/update.py --source {src}#v{target}")
        return 1
    st = _git(root, "status", "--porcelain", "-uall", "--", WORKFLOWS.as_posix())
    workflows = sorted({ln[3:].strip() for ln in st.stdout.splitlines() if ln.strip()})
    if workflows:
        _git(root, "checkout", "HEAD", "--", WORKFLOWS.as_posix())
        _git(root, "clean", "-fdq", "--", WORKFLOWS.as_posix())
    man = json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
    lines = [f"Team factory update {current} → {target} (PATCH/MINOR release; factory tests and "
             "`factory/build.py check` green).", ""]
    if notes:
        lines += ["## What's new", "", notes, ""]
    if major:
        lines += [f"⚠ MAJOR release {major} is also available — not installed automatically; update locally "
                  "(`python3 factory/update.py`) after reading the „Breaking” section.", ""]
    fresh = _factory_new(root, man.get("files", {}))
    if fresh:
        lines += ["## Files changed in the project", "",
                  "These factory files were changed locally, so they were left as they are; their new version is not "
                  "in this PR. Merge by hand: `python3 factory/update.py` run locally puts it next to them as "
                  "`*.factory-new`.", ""]
        lines += [f"- `{f[:-len('.factory-new')]}`" for f in fresh] + [""]
    if workflows:
        lines += ["## Workflows to carry over by hand", "",
                  "GITHUB_TOKEN cannot push changes in `.github/workflows/`, so they are not in this PR. Carry them "
                  "over by hand (e.g. `python3 factory/update.py` locally):", ""]
        lines += [f"- `{w}`" for w in workflows] + [""]
    body = root / PR_BODY
    body.parent.mkdir(parents=True, exist_ok=True)
    body.write_text("\n".join(lines), encoding="utf-8")
    out = env.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"version={target}\n")
    print(f"✓ Installed {target}; PR description: {PR_BODY.as_posix()}")
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
        return (f"Installing the team factory update {current} → {target} in the background (PATCH/MINOR, backup "
                "and tests); it takes effect in the next session, where the result is shown. To turn off: "
                "python3 factory/update.py --auto off")
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
            lines = [f"✓ Factory updated automatically: {a} → {b} (undo: python3 factory/update.py --rollback)."]
            notes = (e.get("notes") or "").splitlines()
            if notes:
                lines += ["What's new:"] + notes[:15] + (["…"] if len(notes) > 15 else [])
            if e.get("factory_new"):
                lines.append("New versions of files you changed (compare and merge): " + ", ".join(e["factory_new"]))
        elif st == "tests_failed":
            lines = [f"✗ Automatic update {a} → {b} rolled back: tests failed after installing "
                     f"({', '.join(e.get('failed', []))}). Version {b} skipped — check by hand: "
                     "python3 factory/update.py"]
        elif st == "audit_blocked":
            lines = [f"✗ Automatic update {a} → {b} stopped: the skill audit found high-severity findings. "
                     f"Version {b} skipped — read them and decide: python3 factory/update.py"]
            lines += e.get("findings", [])[:10]
        elif st == "install_failed":
            lines = [f"✗ Automatic update {a} → {b} failed (installer) and was rolled back. "
                     f"Version {b} skipped: {e.get('error', '')}".rstrip(": ")]
        else:
            continue
        if e.get("major"):
            lines.append(f"⚠ MAJOR release {e['major']} available — not installed automatically (backward-incompatible "
                         "changes). See: python3 factory/update.py --check")
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
                print("✗ Usage: python3 factory/update.py --auto on|off")
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
        print(f"✗ The saved source {saved} no longer exists (factory moved?). Give a new one:\n"
              "  python3 factory/update.py --source <directory|file.zip|git URL>\n"
              "  or set it once in your shell profile: export TEAM_FACTORY=<factory directory>")
        return 2
    src = opts.get("source") or env or saved
    if not src:
        print("✗ No source to fetch the new version from. Give one, e.g.:\n"
              "  python3 factory/update.py --source ~/Downloads/team-factory.zip\n"
              "  python3 factory/update.py --source https://github.com/<you>/team-factory.git\n"
              "  or set it once in your shell profile: export TEAM_FACTORY=<factory directory>")
        return 2
    src = normalize(src)

    with tempfile.TemporaryDirectory(prefix="tf-update-") as t:
        new = fetch(src, Path(t))
        new_version = (new / "core" / "factory" / "VERSION").read_text(encoding="utf-8").strip() \
            if (new / "core" / "factory" / "VERSION").exists() else "0.0.0"
        print(f"Installed version: {current}   available: {new_version}   (source: {src})")
        newer = newer_than(new_version, current) > 0
        if passthrough:                       # zmiana nakładek albo języka — ta sama wersja też się nakłada
            print("ℹ Changing packs or languages: " + " ".join(passthrough))
        if not newer and not opts.get("--force") and not passthrough:
            if newer_than(new_version, current) < 0:
                print("ℹ The source has an older version than the installed one — doing nothing (force: --force).")
            else:
                print("✓ You are up to date. (To re-apply the same version: --force.)")
            return 0
        notes = changelog_since(new, current)
        if notes:
            print("\nWhat's new:\n" + notes + "\n")
        if vtuple(new_version)[0] > vtuple(current)[0]:
            print(f"⚠ This is a MAJOR release ({current} → {new_version}) with backward-incompatible changes. Read the "
                  "„Breaking” sections above (in older entries: „Niezgodne”) — they say what to do after the update "
                  "(SemVer, factory/PUBLIC_API.md).\n")
        if opts.get("--check"):
            return 0

        high, findings = audit_new(new)
        if findings:
            print(f"Skill audit of the new version ({len(findings)} findings, high severity: {high}):")
            print("\n".join(findings[:30]) + ("\n  …" if len(findings) > 30 else "") + "\n")
        else:
            print("Skill audit of the new version: no high or medium severity findings.\n")
        installer = [sys.executable, str(installer_of(new)), str(ROOT), "--update", "--yes", "--source", src, *passthrough]
        print("Update plan:")
        subprocess.run(installer + ["--dry-run"], check=False)
        if opts.get("--dry-run"):
            return 0
        if high and opts.get("--yes") and not opts.get("--accept-audit"):
            print("✗ The audit found high-severity findings — update stopped. Read the listed files; if you accept "
                  "the risk, run again with --accept-audit.")
            return 1
        if high and not opts.get("--yes"):
            print("⚠ The audit found high-severity findings. Read the listed files before you confirm.")
        if not opts.get("--yes"):
            if not sys.stdin.isatty():
                print("\nRun again with --yes to apply (no terminal to confirm in).")
                return 1
            if input("\nApply the update? [y/N] ").strip().lower() not in ("t", "tak", "y", "yes"):
                print("Aborted — nothing was changed.")
                return 1
        code, msg = preflight(ROOT, "python3 factory/update.py --yes")
        if code:
            print(msg)
            return code
        if MANIFEST.exists():
            print(f"Backup before the update: {backup(ROOT).relative_to(ROOT).as_posix()} "
                  "(undo: python3 factory/update.py --rollback)")
        r = subprocess.run(installer, check=False)
        if r.returncode != 0:
            return r.returncode
    print("\nCheck after the update:")
    for test in sorted((ROOT / ".claude" / "tests").glob("test_*.py")):
        res = subprocess.run([sys.executable, str(test)], cwd=ROOT, capture_output=True, text=True)
        print(("  " + (res.stdout.strip().splitlines() or ["?"])[-1]) if res.returncode == 0
              else f"  ✗ {test.name} — run `python3 .claude/tests/{test.name}` to see the details")
    print("Done. If Claude Code is open, restart it so it loads the new skills and agents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
