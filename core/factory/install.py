#!/usr/bin/env python3
"""
Instaluje i aktualizuje claude-team-factory w projekcie (tylko biblioteka standardowa).

Uruchamiasz z katalogu projektu — projektem jest bieżący katalog, a fabrykę wskazuje ścieżka do tego skryptu:

  cd ~/projekty/moja-aplikacja
  python3 "$CLAUDE_TEAM_FACTORY/factory/install.py"              # instalacja prywatna (domyślna): nic nie trafia do commitów
  python3 "$CLAUDE_TEAM_FACTORY/factory/install.py" --dry-run    # pokaż, co by się stało
  python3 "$CLAUDE_TEAM_FACTORY/factory/install.py" --shared     # instalacja zespołowa: fabryka commitowana z projektem
  python3 "$CLAUDE_TEAM_FACTORY/factory/install.py" --gitignore  # prywatna, ale wpisy w .gitignore zamiast .git/info/exclude
  python3 "$CLAUDE_TEAM_FACTORY/factory/install.py" --python py  # wymuś polecenie Pythona dla hooków (domyślnie: wykrywane)

Windows: zamiast `python3` uruchamiasz instalator przez `py` (np. `py %CLAUDE_TEAM_FACTORY%\\factory\\install.py`).
Polecenie Pythona dla hooków i agentów wykrywa instalator: sprawdza kolejno `py`, `python`, `python3` na Windowsie
oraz `python3`, `python` na Linuksie i macOS. Uznaje polecenie, które naprawdę uruchamia Pythona 3.9+, więc pomija
alias ze Sklepu Microsoft. Wynik zapisuje w ustawieniach hooków, w manifeście i w sekcji CLAUDE.md. Gdy nic nie
działa, używa pełnej ścieżki interpretera, którym uruchomiono instalator. `--python <polecenie>` wymusza wybór.

`CLAUDE_TEAM_FACTORY` to katalog fabryki ustawiony raz w profilu powłoki (np. `export CLAUDE_TEAM_FACTORY=~/narzedzia/
claude-team-factory`); równie dobrze możesz podać dowolną ścieżkę — względną liczoną od bieżącego katalogu.
Projekt możesz też wskazać jawnie jako pierwszy argument (ścieżka względna liczona od bieżącego katalogu).
Ponowne uruchomienie w zainstalowanym projekcie = aktualizacja (`--update` nie jest potrzebne).

Na co dzień aktualizujesz z wnętrza projektu: `python3 factory/update.py` (albo `/core-factory-update` w Claude Code).

Tryb prywatny (domyślny): skille, hooki, agenci, `factory/`, testy fabryki (`.claude/tests/`) i przewodnik trafiają do
projektu; uprawnienia i hooki do `.claude/settings.local.json`, zasady do `CLAUDE.local.md`; wszystkie ścieżki fabryki
do `.git/info/exclude`. Tryb zespołowy (`--shared`): `.claude/settings.json`, `CLAUDE.md`, workflow CI i `.gitignore`.

Manifest `.claude/factory-manifest.json` zapisuje wersję, źródło, tryb i skrót każdego zainstalowanego pliku. Dzięki
niemu aktualizacja:
- nadpisuje pliki fabryki, których nie zmieniałeś, i dodaje nowe;
- pliku, który zmieniłeś, nie rusza — nową wersję zapisuje obok jako `<plik>.factory-new`;
- plik usunięty z fabryki przenosi do `.claude/factory-backup/<data>/` (jeśli go nie zmieniałeś);
- nigdy nie rusza Twoich własnych skilli, person, ról i cech (plików, których fabryka nie instalowała).
Instalacja bez manifestu (starsza wersja instalatora) przy `--update`: zmienione pliki fabryki są nadpisywane z kopią
w `.claude/factory-backup/`, a `factory/personas|roles|traits|config.yaml` dostają `.factory-new`.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
MANIFEST = ".claude/factory-manifest.json"
BACKUP_DIR = ".claude/factory-backup"
MARK_BEGIN, MARK_END = "<!-- claude-team-factory:begin -->", "<!-- claude-team-factory:end -->"
GI_BEGIN, GI_END = "# claude-team-factory:begin (zarządzane przez factory/install.py)", "# claude-team-factory:end"
COPY_DIRS = {".claude/skills": ".claude/skills", ".claude/hooks": ".claude/hooks",
             ".claude/agents/_generated": ".claude/agents/_generated", "factory": "factory",
             "tests": ".claude/tests"}   # testy fabryki nie mieszają się z Twoimi `tests/` (pytest ich nie zbierze)
COPY_FILES = {".claude/cleanroom.json": ".claude/cleanroom.json", ".claude/catalog.md": ".claude/catalog.md",
              "docs/PRZEWODNIK.md": ".claude/PRZEWODNIK.md", "docs/jev.md": ".claude/JEV.md",
              "LICENSE": "factory/LICENSE"}
SHARED_ONLY_FILES = {".github/workflows/team-factory.yml": ".github/workflows/team-factory.yml"}
USER_OWNED = ("factory/personas/", "factory/roles/", "factory/traits/", "factory/config.yaml")
ALWAYS_OWNED = (".claude/agents/_generated/", ".claude/catalog.md")   # generowane — zawsze z bieżącej wersji
SKIP = ("__pycache__", ".pyc", "/logs/", ".factory-new")


PY_DEFAULT = "python3"            # polecenie zapisane w plikach źródłowych fabryki
PY_NAMES = ("python3", "python", "py")


def python_works(cmd: str) -> bool:
    """Czy polecenie naprawdę uruchamia Pythona 3.9+ (alias ze Sklepu Microsoft kończy się błędem i odpada)."""
    try:
        r = subprocess.run([cmd, "-c", "import sys; print(int(sys.version_info >= (3, 9)))"],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError, ValueError):
        return False
    return r.returncode == 0 and r.stdout.strip() == "1"


def choose_python(forced: str | None, previous: str | None) -> tuple[str, str]:
    """Zwraca (polecenie, opis pochodzenia). Kolejność: --python, wybór z poprzedniej instalacji, wykrycie, ścieżka."""
    if forced:
        return forced, "podane w --python" + ("" if python_works(forced) else " — UWAGA: to polecenie nie uruchomiło Pythona 3.9+")
    if previous and python_works(previous):
        return previous, "z poprzedniej instalacji"
    order = ("py", "python", "python3") if os.name == "nt" else ("python3", "python")
    for cmd in order:
        if python_works(cmd):
            return cmd, "wykryte"
    return sys.executable, "pełna ścieżka interpretera instalatora (żadne z poleceń " + ", ".join(order) + " nie działa)"


def simple_command(cmd: str) -> bool:
    return not any(ch in cmd for ch in "/\\ ")


def apply_python(settings: dict, py: str) -> dict:
    """Hooki fabryki i reguły uprawnień uruchamiają Pythona poleceniem `py` zamiast `python3`."""
    for entries in (settings.get("hooks") or {}).values():
        for entry in entries:
            for h in entry.get("hooks", []):
                if any("/.claude/hooks/" in a and a.endswith(".py") for a in (h.get("args") or [])):
                    h["command"] = py
    if py != PY_DEFAULT and simple_command(py):
        perms = settings.get("permissions") or {}
        for key in ("allow", "ask", "deny"):
            perms[key] = list(dict.fromkeys(
                (f"Bash({py} " + r[len(f"Bash({PY_DEFAULT} "):]) if r.startswith(f"Bash({PY_DEFAULT} ") else r
                for r in perms.get(key) or []))
    sl = settings.get("statusLine") or {}
    if py != PY_DEFAULT and str(sl.get("command", "")).startswith(PY_DEFAULT + " .claude/hooks/"):
        sl["command"] = py + sl["command"][len(PY_DEFAULT):]
    return settings


def user_has_statusline() -> bool:
    """Własny pasek stanu w ~/.claude/settings.json — ustawienie projektu by go zasłoniło, więc wtedy go nie dodajemy."""
    try:
        return bool(json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8")).get("statusLine"))
    except (OSError, ValueError):
        return False


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version_of(root: Path) -> str:
    p = root / "factory" / "VERSION"
    return p.read_text(encoding="utf-8").strip() if p.exists() else "0.0.0"


class Plan:
    def __init__(self, dst_root: Path, dry: bool, update: bool, old_files: dict | None, stamp: str):
        self.root, self.dry, self.update, self.old, self.stamp = dst_root, dry, update, old_files, stamp
        self.created, self.updated, self.conflicts, self.merged = [], [], [], []
        self.kept_new, self.backed_up, self.removed, self.kept_removed, self.skipped_deleted = [], [], [], [], []
        self.files: dict[str, str] = {}          # nowy manifest: ścieżka → skrót zainstalowanej wersji fabryki

    def _write(self, dst: Path, data: bytes, src: Path | None) -> None:
        if self.dry:
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        if src is not None:
            shutil.copymode(src, dst)

    def _backup(self, rel: str) -> None:
        self.backed_up.append(rel)
        if not self.dry:
            target = self.root / BACKUP_DIR / self.stamp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.root / rel, target)

    def copy(self, src: Path, rel: str) -> None:
        data = retarget(src.read_bytes()) if rel.endswith((".yml", ".json", ".md")) else src.read_bytes()
        dst, new_hash = self.root / rel, sha(data)
        old_hash = (self.old or {}).get(rel)
        self.files[rel] = new_hash
        if not dst.exists():
            if self.update and old_hash is not None:     # był zainstalowany, a Ty go usunąłeś — szanujemy to
                self.skipped_deleted.append(rel)
                return
            self.created.append(rel)
            self._write(dst, data, src)
            return
        cur = dst.read_bytes()
        if cur == data:
            return
        if rel.startswith(ALWAYS_OWNED):
            self.updated.append(rel)
            self._write(dst, data, src)
        elif old_hash is not None and sha(cur) == old_hash:          # nie zmieniałeś — aktualizujemy
            self.updated.append(rel)
            self._write(dst, data, src)
        elif old_hash is not None or (self.update and rel.startswith(USER_OWNED)):
            self.kept_new.append(rel)                                 # Twoja zmiana zostaje, nowa wersja obok
            self._write(dst.with_name(dst.name + ".factory-new"), data, None)
        elif self.update and self.old is None:                        # stara instalacja bez manifestu
            self._backup(rel)
            self.updated.append(rel)
            self._write(dst, data, src)
        else:                                                         # Twój plik o tej samej nazwie
            self.conflicts.append(rel)
            self.files.pop(rel, None)

    def remove_obsolete(self) -> None:
        """Pliki z poprzedniej wersji fabryki, których nowa wersja już nie ma."""
        for rel, old_hash in (self.old or {}).items():
            if rel in self.files:
                continue
            p = self.root / rel
            if not p.exists():
                continue
            if sha(p.read_bytes()) != old_hash:
                self.kept_removed.append(rel)
                continue
            self.removed.append(rel)
            if not self.dry:
                target = self.root / BACKUP_DIR / self.stamp / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), target)
                parent = p.parent                                       # puste katalogi po usuniętym skillu
                while parent != self.root and parent.is_dir() and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent

    def write(self, path: Path, text: str, note: str) -> None:
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old == text:
            return
        (self.merged if old is not None else self.created).append(note)
        if not self.dry:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


def retarget(data: bytes) -> bytes:
    """W projekcie docelowym testy fabryki leżą w `.claude/tests/`."""
    return data.replace(b" tests/test_", b" .claude/tests/test_").replace(b"(python3 tests/", b"(python3 .claude/tests/")


# Reguły wycofane z szablonu: piaskownica Bash zamienia Read(...) z permissions.deny w zakaz odczytu dla programów,
# więc npm test i build nie przeczytałyby node_modules. Ekonomię kontekstu pilnuje teraz hook guard_paths.
RETIRED_DENY = ("Read(./node_modules/**)", "Read(./dist/**)", "Read(./build/**)", "Read(./coverage/**)",
                "Read(**/package-lock.json)", "Read(**/pnpm-lock.yaml)", "Read(**/yarn.lock)")


def merge_settings(src: dict, dst: dict) -> dict:
    out = json.loads(json.dumps(dst))
    out.setdefault("$schema", src.get("$schema"))
    for k, v in (src.get("env") or {}).items():
        out.setdefault("env", {}).setdefault(k, v)          # Twoje wartości mają pierwszeństwo
    perms = out.setdefault("permissions", {})
    if "deny" in perms:
        perms["deny"] = [r for r in perms["deny"] if r not in RETIRED_DENY]
    for key in ("allow", "ask", "deny"):
        cur = perms.setdefault(key, [])
        cur += [r for r in (src.get("permissions", {}).get(key) or []) if r not in cur]
    perms.setdefault("defaultMode", src.get("permissions", {}).get("defaultMode", "default"))
    for k, v in src.items():                                  # pozostałe klucze: Twoje wartości mają pierwszeństwo
        if k not in ("env", "permissions", "hooks", "$schema"):
            out.setdefault(k, v)
    hooks = out.setdefault("hooks", {})
    for event, entries in (src.get("hooks") or {}).items():
        cur = hooks.setdefault(event, [])
        for e in entries:
            have = json.dumps(cur, ensure_ascii=False)
            # hook już jest, gdy wszystkie jego argumenty występują w ustawieniach (polecenie Pythona może być inne)
            missing = [h for h in e.get("hooks", [])
                       if not all(a in have for a in (h.get("args") or [h.get("command", "")]))]
            if not missing:
                continue
            target = next((c for c in cur if c.get("matcher") == e.get("matcher")), None)
            if target is not None:
                target.setdefault("hooks", []).extend(missing)
            else:
                cur.append({**e, "hooks": missing})
    return out


def claude_md_section(py: str = PY_DEFAULT) -> str:
    text = (SRC / "CLAUDE.md").read_text(encoding="utf-8")
    body = text.split("\n", 1)[1] if text.startswith("# ") else text   # bez nagłówka „# Zasady projektu”
    body = "\n".join("#" + ln if ln.startswith("## ") else ln for ln in body.splitlines())   # podsekcje o poziom niżej
    if py != PY_DEFAULT:
        shown = py if simple_command(py) else f'"{py}"'
        body = (f"- **Python w tym projekcie: `{shown}`.** Wszędzie, gdzie skille, przewodnik i komunikaty piszą `python3`, "
                f"uruchamiaj `{shown}` (np. `{shown} .claude/hooks/project_record.py status`).\n" + body.lstrip("\n"))
    return f"{MARK_BEGIN}\n## Zespół agentów (claude-team-factory)\n{body.strip()}\n{MARK_END}\n"


def with_block(text: str, begin: str, end: str, block: str, replace: bool) -> str:
    """Wstawia blok między znacznikami na końcu pliku albo (przy replace) podmienia istniejący."""
    if begin not in text:
        return (text.rstrip() + "\n\n" if text.strip() else "") + block
    if not replace:
        return text
    start = text.index(begin)
    end_at = text.find(end, start + len(begin))
    if end_at < 0:      # uszkodzony blok (brak znacznika końca) — nie zgadujemy, żeby nie skasować treści człowieka
        raise SystemExit(f"✗ Znacznik {begin!r} bez {end!r} w pliku instrukcji — popraw ręcznie (dopisz znacznik końca "
                         "albo usuń początek bloku) i uruchom ponownie.")
    stop = end_at + len(end)
    rest = text[stop:].lstrip("\n")
    return text[:start].rstrip() + ("\n\n" if text[:start].strip() else "") + block + ("\n" + rest if rest else "")


def ignored_paths() -> list[str]:
    """Każda ścieżka instalowana przez fabrykę — per skill i per hook, żeby Twoje własne skille/hooki zostały w repo."""
    out = ["factory/", ".claude/agents/_generated/", ".claude/tests/", ".claude/catalog.md", ".claude/cleanroom.json",
           ".claude/PRZEWODNIK.md", ".claude/JEV.md", ".claude/settings.local.json", "CLAUDE.local.md", MANIFEST, BACKUP_DIR + "/",
           ".claude/agent-memory/", ".claude/factory-profile.json", ".claude/skill-gate.json",
           "*.factory-new"]
    out += [f".claude/skills/{d.name}/" for d in sorted((SRC / ".claude/skills").iterdir()) if d.is_dir()]
    out += [f".claude/hooks/{f.name}" for f in sorted((SRC / ".claude/hooks").iterdir())
            if f.is_file() and not any(s in f.name for s in SKIP)]
    return out


def git_exclude_path(dst_root: Path) -> Path | None:
    """Ścieżka `info/exclude` repozytorium (działa też w worktree); None, gdy to nie repozytorium git."""
    try:
        r = subprocess.run(["git", "-C", str(dst_root), "rev-parse", "--path-format=absolute", "--git-path", "info/exclude"],
                           capture_output=True, text=True, timeout=20)
        return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except (OSError, subprocess.SubprocessError):
        return None


def drop_block(text: str) -> str:
    if GI_BEGIN not in text:
        return text
    start, stop = text.index(GI_BEGIN), text.index(GI_END) + len(GI_END)
    return (text[:start].rstrip() + "\n" + text[stop:].lstrip("\n")).lstrip("\n") if text[:start].strip() or text[stop:].strip() else ""


def tracked(dst_root: Path, paths: list[str]) -> list[str]:
    try:
        r = subprocess.run(["git", "-C", str(dst_root), "ls-files", "--", *[p.rstrip("/") for p in paths]],
                           capture_output=True, text=True, timeout=20)
        return r.stdout.split() if r.returncode == 0 else []
    except (OSError, subprocess.SubprocessError):
        return []


def detect_mode(dst_root: Path) -> str | None:
    """Tryb starej instalacji bez manifestu — po sekcji fabryki w CLAUDE.local.md / CLAUDE.md."""
    for name, mode in (("CLAUDE.local.md", "private"), ("CLAUDE.md", "shared")):
        p = dst_root / name
        if p.exists() and MARK_BEGIN in p.read_text(encoding="utf-8"):
            return mode
    return None


def rebuild(dst_root: Path, dry: bool) -> str:
    """Po aktualizacji przebuduj agentów, jeśli są własne persony/role/cechy (wymaga pyyaml)."""
    if dry:
        return ""
    try:
        import yaml  # noqa: F401
    except ImportError:
        return "⚠ Masz własne persony/role/cechy — doinstaluj `pip install pyyaml` i uruchom `python3 factory/build.py`."
    r = subprocess.run([sys.executable, "factory/build.py"], cwd=dst_root, capture_output=True, text=True)
    return "✓ Przebudowano agentów i katalog (factory/build.py)." if r.returncode == 0 else \
        "⚠ `factory/build.py` zgłosił problemy — uruchom `python3 factory/build.py check` i popraw je:\n" + r.stdout[-1500:]


def main(argv: list[str]) -> int:
    args, opts = [], {}
    it = iter(argv[1:])
    for a in it:
        if a == "--source":
            opts["source"] = next(it, "")
        elif a == "--python":
            opts["python"] = next(it, "")
        elif a.startswith("--") or a == "-h":
            opts[a] = True
        else:
            args.append(a)
    if opts.get("--help") or opts.get("-h"):
        print(__doc__)
        return 0
    dst_root = Path(args[0]).expanduser().resolve() if args else Path.cwd().resolve()   # domyślnie: bieżący katalog
    if dst_root in (Path.home().resolve(), Path("/")):
        print(f"✗ {dst_root} to katalog domowy lub główny, a nie projekt. Przejdź do katalogu projektu (cd …) "
              "albo podaj go jako argument.")
        return 2
    if not dst_root.is_dir():
        print(f"✗ Nie ma katalogu {dst_root}")
        return 2
    if dst_root == SRC:
        print("✗ Jesteś w katalogu fabryki. Przejdź do katalogu projektu i uruchom instalator stamtąd, np.:\n"
              f"  cd ~/projekty/moja-aplikacja && python3 {SRC / 'factory' / 'install.py'}")
        return 2
    dry, update = bool(opts.get("--dry-run")), bool(opts.get("--update"))
    man_p = dst_root / MANIFEST
    manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.exists() else None
    if manifest and not update:
        print(f"ℹ Fabryka jest już zainstalowana (wersja {manifest.get('version')}) — wykonuję aktualizację.")
        update = True
    mode = ("shared" if opts.get("--shared") else None) or (manifest or {}).get("mode") or \
        (detect_mode(dst_root) if update else None) or "private"
    shared = mode == "shared"
    force_gitignore = bool(opts.get("--gitignore")) or (manifest or {}).get("ignore") == "gitignore"
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    plan = Plan(dst_root, dry, update, (manifest or {}).get("files") if manifest else None, stamp)
    py, py_how = choose_python(opts.get("python") or None, (manifest or {}).get("python"))

    for d, target in COPY_DIRS.items():
        for f in sorted((SRC / d).rglob("*")):
            rel = target + "/" + f.relative_to(SRC / d).as_posix()
            if f.is_file() and not any(s in rel for s in SKIP):
                plan.copy(f, rel)
    for s, d in {**COPY_FILES, **(SHARED_ONLY_FILES if shared else {})}.items():
        if (SRC / s).exists():
            plan.copy(SRC / s, d)
    if update:
        plan.remove_obsolete()

    # ustawienia: prywatnie → settings.local.json, zespołowo → settings.json (zawsze scalane z tym, co już jest)
    src_set = apply_python(json.loads(retarget((SRC / ".claude/settings.json").read_bytes()).decode("utf-8")), py)
    if user_has_statusline():
        src_set.pop("statusLine", None)
    set_p = dst_root / (".claude/settings.json" if shared else ".claude/settings.local.json")
    cur = json.loads(set_p.read_text(encoding="utf-8")) if set_p.exists() else {}
    merged = apply_python(merge_settings(src_set, cur), py) if cur else src_set
    if merged != cur:
        plan.write(set_p, json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
                   f"{set_p.relative_to(dst_root)} (uprawnienia i hooki fabryki)")

    # zasady: prywatnie → CLAUDE.local.md, zespołowo → CLAUDE.md; sekcja między znacznikami, przy aktualizacji podmieniana
    md_p = dst_root / ("CLAUDE.md" if shared else "CLAUDE.local.md")
    md_old = md_p.read_text(encoding="utf-8") if md_p.exists() else ""
    plan.write(md_p, with_block(md_old, MARK_BEGIN, MARK_END, claude_md_section(py), update),
               f"{md_p.name} (sekcja fabryki)")

    # wpisy ignorowania: prywatnie → .git/info/exclude (nic nie widać w repo), zespołowo lub --gitignore → .gitignore
    exclude = None if (shared or force_gitignore) else git_exclude_path(dst_root)
    ign = exclude or dst_root / ".gitignore"
    ign_label = ".git/info/exclude" if exclude else ".gitignore"
    ign_old = ign.read_text(encoding="utf-8") if ign.exists() else ""
    outside = ign_old.split(GI_BEGIN)[0] + (ign_old.split(GI_END, 1)[1] if GI_END in ign_old else "")
    have = set(outside.splitlines())
    temp = [ln for ln in (SRC / ".gitignore").read_text(encoding="utf-8").splitlines() if ln]
    extra = [MANIFEST, BACKUP_DIR + "/", "*.factory-new"] if shared else ignored_paths()
    lines = [ln for ln in dict.fromkeys(temp + extra) if ln not in have]
    if lines:
        plan.write(ign, with_block(ign_old, GI_BEGIN, GI_END, "\n".join([GI_BEGIN, *lines, GI_END]) + "\n", True),
                   f"{ign_label} ({len(lines)} wpisów fabryki)")
    gi = dst_root / ".gitignore"
    if exclude and gi.exists() and GI_BEGIN in gi.read_text(encoding="utf-8"):   # po starszej wersji instalatora
        plan.write(gi, drop_block(gi.read_text(encoding="utf-8")), ".gitignore (usunięty blok fabryki — jest teraz w .git/info/exclude)")
    if not shared and not exclude and not force_gitignore:
        print("ℹ To nie jest repozytorium git — wpisy trafią do .gitignore. Po `git init` uruchom aktualizację ponownie.")

    # manifest
    old_version = (manifest or {}).get("version") or ("nieznana" if update else None)
    new_version = version_of(SRC)
    if not dry:
        man_p.parent.mkdir(parents=True, exist_ok=True)
        man_p.write_text(json.dumps({
            "version": new_version,
            "source": opts.get("source") or (manifest or {}).get("source") or str(SRC),
            "mode": mode,
            "python": py,
            "ignore": "gitignore" if force_gitignore else "exclude",
            "installed_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "files": dict(sorted(plan.files.items())),
            "skill_overrides": (manifest or {}).get("skill_overrides") or {},   # wpisy fabryki w skillOverrides
            **({"skill_describe": manifest["skill_describe"]} if (manifest or {}).get("skill_describe") else {}),
            **({"auto_update": manifest["auto_update"]} if "auto_update" in (manifest or {}) else {}),   # update.py --auto
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # raport
    mode_txt = "zespołowy (commitowany)" if shared else "prywatny (poza gitem)"
    head = "Podgląd (nic nie zapisano)" if dry else ("Zaktualizowano" if update else "Zainstalowano")
    ver = f"{old_version} → {new_version}" if update else new_version
    print(f"{head} w {dst_root} — wersja {ver}, tryb {mode_txt}: nowych plików {len(plan.created)}, "
          f"zaktualizowanych {len(plan.updated)}, scalonych {len(plan.merged)}, usuniętych {len(plan.removed)}")
    for m in plan.merged:
        print(f"  ~ {m}")
    # widoczność opisów skilli: z opisem to, czego używa ten projekt, reszta jako sama nazwa (factory/skill_profile.py)
    if dry:
        print("ℹ Widoczność skilli zostanie dopasowana do projektu po instalacji (factory/skill_profile.py).")
    else:
        spec = importlib.util.spec_from_file_location("ctf_skill_profile", SRC / "factory" / "skill_profile.py")
        prof = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prof)
        print(prof.summary(prof.apply(dst_root), False))
    print(f"ℹ Python dla hooków i agentów: `{py}` ({py_how}).")
    if not simple_command(py) or not python_works(py):
        print("⚠ Hooki bezpieczeństwa działają tylko wtedy, gdy to polecenie uruchamia Pythona. Jeśli nie — popraw je: "
              "ponów instalację z `--python <polecenie>`.")
    if shared and py != PY_DEFAULT:
        print(f"⚠ Tryb zespołowy: `{py}` trafia do commitowanego .claude/settings.json. Osoby na innym systemie "
              "potrzebują innego polecenia — zespół z różnymi systemami lepiej instaluje fabrykę prywatnie (bez --shared).")
    new_skills = sorted({r.split("/")[2] for r in plan.created if r.startswith(".claude/skills/") and r.endswith("/SKILL.md")})
    if new_skills and update:
        print(f"  + nowe skille: {', '.join(new_skills)}")
    new_personas = sorted({Path(r).stem for r in plan.created if r.startswith("factory/personas/")})
    if new_personas and update:
        print(f"  + nowe persony: {', '.join(new_personas)}")
    if plan.removed:
        print(f"  − przeniesione do {BACKUP_DIR}/{stamp}/ (usunięte z fabryki): {', '.join(plan.removed[:10])}")

    def listing(title: str, items: list[str], hint: str) -> None:
        if items:
            print(f"{title} ({len(items)}):")
            for c in items[:15]:
                print(f"  ! {c}")
            if len(items) > 15:
                print(f"  … i {len(items) - 15} więcej")
            print(f"  {hint}")

    listing("⚠ Zmieniłeś te pliki fabryki — zostały Twoje, nowa wersja leży obok jako *.factory-new", plan.kept_new,
            "Porównaj (`diff plik plik.factory-new`), przenieś potrzebne zmiany i usuń *.factory-new. "
            "W Claude Code pomoże `/core-factory-update`.")
    listing(f"ℹ Starsza instalacja bez manifestu — zmienione pliki nadpisane, kopie w {BACKUP_DIR}/{stamp}/",
            plan.backed_up, "Jeśli coś z tych plików było Twoją zmianą, przenieś ją z kopii.")
    listing("ℹ Usunięte z fabryki, ale zmienione przez Ciebie — zostawione", plan.kept_removed,
            "Jeśli już ich nie potrzebujesz, usuń je ręcznie.")
    listing("ℹ Usunąłeś te pliki fabryki — nie przywracam ich", plan.skipped_deleted,
            "Jeśli chcesz je z powrotem, usuń ich wpisy z .claude/factory-manifest.json i uruchom aktualizację.")
    listing("⚠ Pominięto istniejące pliki o tej samej nazwie co pliki fabryki (Twoje zostały)", plan.conflicts,
            "Zmień nazwę własnego pliku (np. skilla) i uruchom aktualizację, jeśli chcesz mieć też wersję fabryki.")

    personal = Path.home() / ".claude/skills"
    shadowed = sorted(d.name for d in (SRC / ".claude/skills").iterdir() if (personal / d.name / "SKILL.md").exists())
    if shadowed:
        print(f"⚠ Skille osobiste w {personal} mają te same nazwy co skille fabryki i mają pierwszeństwo (Claude Code: "
              f"osobiste > projektu): {', '.join(shadowed)}. Zmień nazwy osobistych, jeśli agenci mają używać wersji fabryki.")
    if not shared:
        already = tracked(dst_root, ignored_paths())
        if already:
            print(f"⚠ {len(already)} plików fabryki jest już w repozytorium — wpisy ignorowania ich nie ukryją. "
                  "Usuń je z indeksu (pliki na dysku zostaną):")
            print("  git rm -r --cached " + " ".join(sorted({p.split("/")[0] if p.startswith("factory/") else
                                                             "/".join(p.split("/")[:3]) for p in already})[:12]))
        if not (dst_root / "CLAUDE.md").exists() and (dst_root / "AGENTS.md").exists():
            print("⚠ Projekt używa AGENTS.md: sam CLAUDE.local.md sprawi, że Claude przestanie go czytać. Dodaj na początku "
                  "CLAUDE.local.md linię `@AGENTS.md`.")
    own = [p for sub in ("personas", "roles", "traits") for p in (dst_root / "factory" / sub).glob("*")
           if p.is_file() and f"factory/{sub}/{p.name}" not in plan.files]
    profile_set = (dst_root / ".claude" / "factory-profile.json").exists()   # profil kosztów inny niż domyślny
    if update and (own or plan.kept_new or profile_set):
        msg = rebuild(dst_root, dry)
        if msg:
            print(msg)
    if not dry and not update:
        md = "CLAUDE.md" if shared else "CLAUDE.local.md"
        print(f"""
Dalej:
  1. Uzupełnij w {md} komendy testów/lintu/buildu Twojego projektu.
  2. Uruchom raz `claude` w katalogu projektu i zaakceptuj zaufanie do folderu (bez tego hooki i uprawnienia nie działają).
  3. Opcjonalnie: `pip install pyyaml` i `{py} factory/build.py check` — potrzebne tylko, gdy zmieniasz persony/role.
  4. Start: `claude --agent maja` (opisz problem) albo wybrana persona, np. `claude --agent filip`.
  5. Koszty: profil `zrownowazony` działa od razu; `{py} factory/profile.py oszczedny|jakosc` przełącza cały zespół
     (wymaga pyyaml). Pasek stanu pokazuje kontekst, cache i koszt sesji.
  Aktualizacje: `{py} factory/update.py` (albo `/core-factory-update` w Claude Code).""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
