#!/usr/bin/env python3
"""
Installs and updates the team factory (core + selected packs) in a project. Standard library only
(PyYAML for pack metadata: system copy or the one bundled in factory/_vendor).

Run it from the project directory — the project is the current directory, the factory is where this script lives:

  cd ~/projects/my-app
  python3 "$TEAM_FACTORY/core/factory/install.py"                     # private install (default): nothing gets committed
  python3 "$TEAM_FACTORY/core/factory/install.py" --dry-run           # show what would happen
  python3 "$TEAM_FACTORY/core/factory/install.py" --packs pack-it,pack-ev   # choose packs without asking
  python3 "$TEAM_FACTORY/core/factory/install.py" --add pack-ux       # add a pack to an existing install
  python3 "$TEAM_FACTORY/core/factory/install.py" --remove pack-ux    # remove a pack
  python3 "$TEAM_FACTORY/core/factory/install.py" --language pl --commit-language en
  python3 "$TEAM_FACTORY/core/factory/install.py" --shared            # team install: the factory is committed with the project
  python3 "$TEAM_FACTORY/core/factory/install.py" --gitignore         # private, but entries go to .gitignore, not .git/info/exclude
  python3 "$TEAM_FACTORY/core/factory/install.py" --python py         # force the Python command for hooks (default: detected)
  python3 "$TEAM_FACTORY/core/factory/install.py" --yes               # no questions: defaults or the previous choice

The core is always installed. Packs (`packs/pack-*`) are chosen interactively on the first install (or with
`--packs`); later runs keep the previous choice. A pack's required packs and the pack of the chosen working language
(e.g. `pack-editorial-pl` for `pl`) are added automatically. On the first install you also choose the working
language (conversation, documentation; default `pl`) and the commit language (commit messages, PR titles and
descriptions; default `en`). Both can be changed later: `tf language <code>`, `tf commit-language <code>`.

`TEAM_FACTORY` is the factory directory set once in your shell profile (e.g. `export TEAM_FACTORY=~/tools/tf`); any
path works too, relative to the current directory. The project can also be given as the first argument.
Running the installer again in an installed project = update (`--update` is not needed).

Day to day you update from inside the project: `python3 factory/update.py` (or `tf`, or `/core-factory-update`).

Private mode (default): skills, hooks, `factory/`, factory tests (`.claude/tests/`) go into the project; permissions and
hooks into `.claude/settings.local.json`, rules into `CLAUDE.local.md`; all factory paths into `.git/info/exclude`.
Team mode (`--shared`): `.claude/settings.json`, `CLAUDE.md`, CI workflow and `.gitignore`.
After copying, the installer builds the agents (`factory/build.py`) for the chosen packs and languages.

The manifest `.claude/factory-manifest.json` records the version, source, mode, packs and a hash of every installed
file. Thanks to it an update:
- overwrites factory files you did not change and adds new ones;
- leaves files you changed alone — the new version is written next to them as `<file>.factory-new`;
- moves files removed from the factory (or from a removed pack) to `.claude/factory-backup/<date>/` (if unchanged);
- never touches your own skills, personas, roles and traits (files the factory did not install).
Installs of claude-team-factory or ev-team-factory are migrated: the matching packs are selected and the old
instruction and ignore blocks are replaced.
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

SRC = Path(__file__).resolve().parent.parent.parent      # repozytorium fabryki: core/ i packs/
CORE = SRC / "core"
PACKS_SRC = SRC / "packs"
MANIFEST = ".claude/factory-manifest.json"
BACKUP_DIR = ".claude/factory-backup"
MARK_BEGIN, MARK_END = "<!-- team-factory:begin -->", "<!-- team-factory:end -->"
GI_BEGIN, GI_END = "# team-factory:begin (managed by factory/install.py)", "# team-factory:end"
# znaczniki instalacji, z których migrujemy (claude-team-factory, ev-team-factory)
LEGACY_MARKS = [(f"<!-- {n}:begin -->", f"<!-- {n}:end -->") for n in ("claude-team-factory", "ev-team-factory")]
LEGACY_GI = [(f"# {n}:begin (zarządzane przez factory/install.py)", f"# {n}:end")
             for n in ("claude-team-factory", "ev-team-factory")]
CORE_DIRS = {"skills": ".claude/skills", "hooks": ".claude/hooks", "factory": "factory",
             "tests": ".claude/tests"}   # testy fabryki nie mieszają się z Twoimi `tests/` (pytest ich nie zbierze)
CORE_FILES = {"guide/JEV.md": ".claude/JEV.md"}
PACK_DIRS = {"skills": ".claude/skills", "hooks": ".claude/hooks", "tests": ".claude/tests"}
PACK_META = ("pack.yaml", "roles", "personas", "traits", "technologies.json")   # → factory/packs/<id>/
SHARED_ONLY_FILES = {"workflows/team-factory.yml": ".github/workflows/team-factory.yml"}
USER_OWNED = ("factory/personas/", "factory/roles/", "factory/traits/", "factory/config.yaml", "factory/packs/")
ALWAYS_OWNED = (".claude/cleanroom.json",)   # składany z rdzenia i nakładek — zawsze z bieżącej wersji
GENERATED = (".claude/agents/_generated/", ".claude/catalog.md")   # budowane w projekcie przez factory/build.py
SKIP = ("__pycache__", ".pyc", "/logs/", ".factory-new")


def load_packs_module():
    """factory/packs.py z NOWEJ wersji fabryki (czytanie pack.yaml, ustawienia projektu)."""
    spec = importlib.util.spec_from_file_location("tf_packs_src", CORE / "factory" / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def available_packs() -> dict[str, dict]:
    pm = load_packs_module()
    out = {}
    for p in sorted(PACKS_SRC.glob("*/pack.yaml")) if PACKS_SRC.is_dir() else []:
        data = pm.load_yaml(p)
        data["_dir"] = p.parent
        out[data.get("id") or p.parent.name] = data
    return out


def core_config() -> dict:
    return load_packs_module().load_yaml(CORE / "factory" / "config.yaml")


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
        return forced, "given with --python" + ("" if python_works(forced) else " — WARNING: this command did not run Python 3.9+")
    if previous and python_works(previous):
        return previous, "from the previous install"
    order = ("py", "python", "python3") if os.name == "nt" else ("python3", "python")
    for cmd in order:
        if python_works(cmd):
            return cmd, "detected"
    return sys.executable, "full path of the installer's interpreter (none of " + ", ".join(order) + " works)"


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
    """Wersja rdzenia: core/factory/VERSION w repozytorium fabryki albo factory/VERSION w projekcie."""
    for p in (root / "core" / "factory" / "VERSION", root / "factory" / "VERSION"):
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    return "0.0.0"


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

    def copy(self, src: Path | None, rel: str, data: bytes | None = None) -> None:
        """Plik fabryki `src` (albo gotowa treść `data`, np. złożona z rdzenia i nakładek) pod ścieżką `rel`."""
        if data is None:
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
            if rel in self.files or rel.startswith(GENERATED):   # agentów i katalog buduje build.py w projekcie
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


# Pola hooka, które aktualizacja dopisuje do hooka już obecnego w projekcie (onFailure: Claude Code ≥ 2.1.295).
HOOK_KEYS_ADDED = ("onFailure",)


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
            for h in e.get("hooks", []):          # nowe pola fabryki w hooku, który już jest (wybór użytkownika zostaje)
                if h in missing or not h.get("args"):
                    continue
                for mine in (x for c in cur for x in c.get("hooks", []) if x.get("args") == h["args"]):
                    for k in HOOK_KEYS_ADDED:
                        if k in h:
                            mine.setdefault(k, h[k])
            if not missing:
                continue
            target = next((c for c in cur if c.get("matcher") == e.get("matcher")), None)
            if target is not None:
                target.setdefault("hooks", []).extend(missing)
            else:
                cur.append({**e, "hooks": missing})
    return out


def claude_md_section(py: str = PY_DEFAULT, settings: dict | None = None, cfg: dict | None = None) -> str:
    """Sekcja fabryki w CLAUDE.md / CLAUDE.local.md: zasady rdzenia + język pracy i commitów."""
    text = (CORE / "CLAUDE.md").read_text(encoding="utf-8")
    body = text.split("\n", 1)[1] if text.startswith("# ") else text   # bez nagłówka „# Zasady projektu”
    body = "\n".join("#" + ln if ln.startswith("## ") else ln for ln in body.splitlines())   # podsekcje o poziom niżej
    if py != PY_DEFAULT:
        shown = py if simple_command(py) else f'"{py}"'
        body = (f"- **Python w tym projekcie: `{shown}`.** Wszędzie, gdzie skille, przewodnik i komunikaty piszą `python3`, "
                f"uruchamiaj `{shown}` (np. `{shown} .claude/hooks/project_record.py status`).\n" + body.lstrip("\n"))
    if settings and cfg:
        langs = cfg.get("languages") or {}
        lines = [(langs.get(settings.get("language")) or {}).get("work"),
                 (langs.get(settings.get("commit_language")) or {}).get("commits"), cfg.get("code_language_note")]
        body = body.rstrip() + "\n\n### Język\n" + "\n".join(f"- {x.strip()}" for x in lines if x)
    return f"{MARK_BEGIN}\n## Zespół agentów (team factory)\n{body.strip()}\n{MARK_END}\n"


def drop_legacy_blocks(text: str, marks: list[tuple[str, str]]) -> str:
    """Usuwa bloki starych fabryk (claude-team-factory, ev-team-factory) — zastępuje je blok tej fabryki."""
    for begin, end in marks:
        if begin in text and end in text:
            a, b = text.index(begin), text.index(end) + len(end)
            text = (text[:a].rstrip() + "\n\n" + text[b:].lstrip("\n")).strip("\n")
            text = text + "\n" if text else ""
    return text


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


def ignored_paths(files: dict[str, str] | None = None) -> list[str]:
    """Każda ścieżka instalowana przez fabrykę — per skill i per hook, żeby Twoje własne skille/hooki zostały w repo."""
    out = ["factory/", ".claude/agents/_generated/", ".claude/tests/", ".claude/catalog.md", ".claude/cleanroom.json",
           ".claude/JEV.md", ".claude/settings.local.json", "CLAUDE.local.md", MANIFEST, BACKUP_DIR + "/",
           ".claude/agent-memory/", ".claude/factory-profile.json", ".claude/factory-settings.json",
           ".claude/skill-gate.json", ".claude/scratch/", ".claude/runs/", "*.factory-new"]
    rels = sorted(files or {})
    out += list(dict.fromkeys("/".join(r.split("/")[:3]) + "/" for r in rels if r.startswith(".claude/skills/")))
    out += [r for r in rels if r.startswith(".claude/hooks/")]
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
        if p.exists() and any(b in p.read_text(encoding="utf-8") for b in [MARK_BEGIN, *(m[0] for m in LEGACY_MARKS)]):
            return mode
    return None


def legacy_packs(manifest: dict | None, dst_root: Path) -> list[str] | None:
    """Nakładki dla instalacji claude-team-factory / ev-team-factory (manifest bez listy nakładek)."""
    if not manifest or "packs" in manifest:
        return None
    src = str(manifest.get("source", "")).lower()
    md = " ".join((dst_root / n).read_text(encoding="utf-8") for n in ("CLAUDE.md", "CLAUDE.local.md")
                  if (dst_root / n).exists())
    if "ev-team-factory" in src or "ev-team-factory:begin" in md:
        return ["pack-ev", "pack-docs"]
    return ["pack-it", "pack-ux", "pack-docs"]


def resolve_packs(chosen: list[str], available: dict, language: str, cfg: dict) -> tuple[list[str], list[str]]:
    """Wybrane nakładki + wymagane przez nie + nakładka języka pracy. Zwraca (nakładki, nieznane)."""
    unknown = [c for c in chosen if c not in available]
    out = [c for c in chosen if c in available]
    lang_pack = ((cfg.get("languages") or {}).get(language) or {}).get("pack")
    if lang_pack in available and lang_pack not in out:
        out.append(lang_pack)
    i = 0
    while i < len(out):
        for dep in (available[out[i]].get("requires") or {}).get("packs") or []:
            if dep in available and dep not in out:
                out.append(dep)
        i += 1
    return sorted(out), unknown


def ask(question: str, default: str) -> str:
    try:
        answer = input(f"{question} [{default}]: ").strip()
    except EOFError:
        return default
    return answer or default


def interactive_choice(available: dict, cfg: dict, preset: list[str]) -> tuple[list[str], str, str]:
    """Pierwsza instalacja w terminalu: język pracy, język commitów, nakładki."""
    langs = cfg.get("languages") or {}
    codes = "/".join(langs)
    print("Team factory — first install. The core is always installed.")
    language = ask(f"Working language (conversation, documentation) — {codes}", cfg.get("default_language", "pl"))
    while language not in langs:
        language = ask(f"  unknown language; choose {codes}", cfg.get("default_language", "pl"))
    commit = ask(f"Commit language (commit messages, PR titles and descriptions) — {codes}",
                 cfg.get("default_commit_language", "en"))
    while commit not in langs:
        commit = ask(f"  unknown language; choose {codes}", cfg.get("default_commit_language", "en"))
    lang_pack = (langs.get(language) or {}).get("pack")
    print("\nAvailable packs:")
    ids = list(available)
    for i, pid in enumerate(ids, 1):
        p = available[pid]
        mark = "*" if pid in preset else " "
        auto = " (installed with this language)" if pid == lang_pack else ""
        print(f"  {i}. [{mark}] {pid} — {p.get('description', p.get('title', ''))}{auto}")
    raw = ask("Packs to install: numbers or ids separated by commas, 'all', or Enter for the marked ones",
              ",".join(preset) or "none")
    if raw.strip().lower() == "all":
        chosen = ids
    elif raw.strip().lower() in ("none", "-", ""):
        chosen = []
    else:
        chosen = []
        for tok in (t.strip() for t in raw.split(",") if t.strip()):
            chosen.append(ids[int(tok) - 1] if tok.isdigit() and 0 < int(tok) <= len(ids) else tok)
    return chosen, language, commit


def rebuild(dst_root: Path, dry: bool) -> str:
    """Buduje agentów i katalog w projekcie dla wybranych nakładek i języków (factory/build.py)."""
    if dry:
        return ""
    r = subprocess.run([sys.executable, "factory/build.py"], cwd=dst_root, capture_output=True, text=True)
    if r.returncode == 0:
        n = len(list((dst_root / ".claude" / "agents" / "_generated").rglob("*.md")))
        return f"✓ Built {n} agents and the catalog (factory/build.py)."
    return ("⚠ `factory/build.py` reported problems — run `python3 factory/build.py check` and fix them:\n"
            + r.stdout[-1500:] + r.stderr[-500:])


def compose_cleanroom(packs: list[str], available: dict) -> bytes:
    """`.claude/cleanroom.json`: opis z rdzenia + profile z nakładek."""
    data = json.loads((CORE / "cleanroom.json").read_text(encoding="utf-8"))
    for pid in packs:
        f = available[pid]["_dir"] / "cleanroom.json"
        if f.exists():
            data["profiles"] = data.get("profiles", []) + json.loads(f.read_text(encoding="utf-8")).get("profiles", [])
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def compose_settings(packs: list[str], available: dict) -> dict:
    """Uprawnienia i hooki rdzenia + nakładek (`settings.json` w nakładce)."""
    base = json.loads(retarget((CORE / "settings.json").read_bytes()).decode("utf-8"))
    for pid in packs:
        f = available[pid]["_dir"] / "settings.json"
        if f.exists():
            base = merge_settings(json.loads(retarget(f.read_bytes()).decode("utf-8")), base)
    return base


def parse_args(argv: list[str]) -> tuple[list[str], dict]:
    args, opts = [], {}
    it = iter(argv[1:])
    for a in it:
        if a in ("--source", "--python", "--packs", "--add", "--remove", "--language", "--commit-language"):
            opts[a.lstrip("-")] = next(it, "")
        elif a.startswith("--") or a == "-h":
            opts[a] = True
        else:
            args.append(a)
    return args, opts


def split_ids(raw: str | None) -> list[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def main(argv: list[str]) -> int:
    args, opts = parse_args(argv)
    if opts.get("--help") or opts.get("-h"):
        print(__doc__)
        return 0
    dst_root = Path(args[0]).expanduser().resolve() if args else Path.cwd().resolve()   # domyślnie: bieżący katalog
    if dst_root in (Path.home().resolve(), Path("/")):
        print(f"✗ {dst_root} is your home or root directory, not a project. Go to the project directory (cd …) "
              "or pass it as an argument.")
        return 2
    if not dst_root.is_dir():
        print(f"✗ Directory {dst_root} does not exist")
        return 2
    if dst_root == SRC or dst_root == CORE or CORE in dst_root.parents or PACKS_SRC in [dst_root, *dst_root.parents]:
        print("✗ You are in the factory directory. Go to your project and run the installer from there, e.g.:\n"
              f"  cd ~/projects/my-app && python3 {CORE / 'factory' / 'install.py'}")
        return 2
    dry, update = bool(opts.get("--dry-run")), bool(opts.get("--update"))
    man_p = dst_root / MANIFEST
    manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.exists() else None
    if manifest and not update:
        print(f"ℹ The factory is already installed (version {manifest.get('version')}) — updating.")
        update = True
    mode = ("shared" if opts.get("--shared") else None) or (manifest or {}).get("mode") or \
        (detect_mode(dst_root) if update else None) or "private"
    shared = mode == "shared"
    force_gitignore = bool(opts.get("--gitignore")) or (manifest or {}).get("ignore") == "gitignore"
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    plan = Plan(dst_root, dry, update, (manifest or {}).get("files") if manifest else None, stamp)
    py, py_how = choose_python(opts.get("python") or None, (manifest or {}).get("python"))

    # nakładki i języki
    cfg = core_config()
    pm = load_packs_module()
    available = available_packs()
    settings = pm.load_settings(dst_root, cfg)
    had_settings = (dst_root / pm.SETTINGS_REL).exists()
    language = opts.get("language") or settings["language"]
    commit_language = opts.get("commit-language") or settings["commit_language"]
    for label, code in (("language", language), ("commit language", commit_language)):
        if code not in (cfg.get("languages") or {}):
            print(f"✗ Unknown {label} '{code}'. Available: {', '.join(cfg.get('languages') or {})}")
            return 2
    legacy = legacy_packs(manifest, dst_root)
    previous = list((manifest or {}).get("packs") or {}) if manifest and "packs" in manifest else legacy
    preset = previous if previous is not None else [pid for pid, p in available.items() if p.get("default")]
    if opts.get("packs") is not None and opts.get("packs") != "":
        chosen = [] if opts["packs"] in ("none", "-") else list(available) if opts["packs"] == "all" \
            else split_ids(opts["packs"])
    elif opts.get("packs") == "":
        chosen = []
    elif previous is None and not opts.get("--yes") and sys.stdin.isatty() and not dry:
        chosen, language, commit_language = interactive_choice(available, cfg, preset)
    else:
        chosen = list(preset)
    chosen = [c for c in chosen if c not in split_ids(opts.get("remove"))] + split_ids(opts.get("add"))
    lang_pack = ((cfg.get("languages") or {}).get(language) or {}).get("pack")
    if lang_pack and lang_pack in split_ids(opts.get("remove")):
        print(f"✗ {lang_pack} is required by the working language '{language}'. Change the language first "
              f"(tf language <code>) or keep the pack.")
        return 2
    packs, unknown = resolve_packs(list(dict.fromkeys(chosen)), available, language, cfg)
    if unknown:
        print(f"✗ Unknown packs: {', '.join(unknown)}. Available: {', '.join(available) or '—'}")
        return 2
    if legacy is not None:
        print(f"ℹ Migrating an install of {manifest.get('source') or 'an older factory'} "
              f"(version {manifest.get('version')}) — packs: {', '.join(packs) or 'none'}.")

    # pliki rdzenia
    for d, target in CORE_DIRS.items():
        for f in sorted((CORE / d).rglob("*")):
            rel = target + "/" + f.relative_to(CORE / d).as_posix()
            if f.is_file() and not any(x in rel for x in SKIP):
                plan.copy(f, rel)
    for src_rel, dst_rel in {**CORE_FILES, **(SHARED_ONLY_FILES if shared else {})}.items():
        if (CORE / src_rel).exists():
            plan.copy(CORE / src_rel, dst_rel)
    if (SRC / "LICENSE").exists():
        plan.copy(SRC / "LICENSE", "factory/LICENSE")
    # pliki nakładek
    for pid in packs:
        base = available[pid]["_dir"]
        for d, target in PACK_DIRS.items():
            for f in sorted((base / d).rglob("*")):
                rel = target + "/" + f.relative_to(base / d).as_posix()
                if f.is_file() and not any(x in rel for x in SKIP):
                    plan.copy(f, rel)
        for meta in PACK_META:
            src_meta = base / meta
            files = [src_meta] if src_meta.is_file() else sorted(src_meta.rglob("*")) if src_meta.is_dir() else []
            for f in files:
                if f.is_file() and not any(x in f.name for x in SKIP):
                    plan.copy(f, f"factory/packs/{pid}/" + f.relative_to(base).as_posix())
    plan.copy(None, ".claude/cleanroom.json", compose_cleanroom(packs, available))
    if update:
        plan.remove_obsolete()

    # ustawienia: prywatnie → settings.local.json, zespołowo → settings.json (zawsze scalane z tym, co już jest)
    src_set = apply_python(compose_settings(packs, available), py)
    if user_has_statusline():
        src_set.pop("statusLine", None)
    set_p = dst_root / (".claude/settings.json" if shared else ".claude/settings.local.json")
    cur = json.loads(set_p.read_text(encoding="utf-8")) if set_p.exists() else {}
    merged = apply_python(merge_settings(src_set, cur), py) if cur else src_set
    if merged != cur:
        plan.write(set_p, json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
                   f"{set_p.relative_to(dst_root)} (factory permissions and hooks)")

    # zasady: prywatnie → CLAUDE.local.md, zespołowo → CLAUDE.md; sekcja między znacznikami, przy aktualizacji podmieniana
    md_p = dst_root / ("CLAUDE.md" if shared else "CLAUDE.local.md")
    md_old = md_p.read_text(encoding="utf-8") if md_p.exists() else ""
    md_base = drop_legacy_blocks(md_old, LEGACY_MARKS)
    section = claude_md_section(py, {"language": language, "commit_language": commit_language}, cfg)
    plan.write(md_p, with_block(md_base, MARK_BEGIN, MARK_END, section, update or md_base != md_old),
               f"{md_p.name} (factory section)")

    # wpisy ignorowania: prywatnie → .git/info/exclude (nic nie widać w repo), zespołowo lub --gitignore → .gitignore
    exclude = None if (shared or force_gitignore) else git_exclude_path(dst_root)
    ign = exclude or dst_root / ".gitignore"
    ign_label = ".git/info/exclude" if exclude else ".gitignore"
    ign_old = drop_legacy_blocks(ign.read_text(encoding="utf-8") if ign.exists() else "", LEGACY_GI)
    outside = ign_old.split(GI_BEGIN)[0] + (ign_old.split(GI_END, 1)[1] if GI_END in ign_old else "")
    have = set(outside.splitlines())
    temp = [ln for ln in (CORE / "gitignore").read_text(encoding="utf-8").splitlines() if ln]
    extra = [MANIFEST, BACKUP_DIR + "/", "*.factory-new", ".claude/factory-settings.json"] if shared \
        else ignored_paths(plan.files)
    lines = [ln for ln in dict.fromkeys(temp + extra) if ln not in have]
    if lines:
        plan.write(ign, with_block(ign_old, GI_BEGIN, GI_END, "\n".join([GI_BEGIN, *lines, GI_END]) + "\n", True),
                   f"{ign_label} ({len(lines)} factory entries)")
    gi = dst_root / ".gitignore"
    if exclude and gi.exists() and GI_BEGIN in gi.read_text(encoding="utf-8"):   # po starszej wersji instalatora
        plan.write(gi, drop_block(gi.read_text(encoding="utf-8")), ".gitignore (factory block removed — now in .git/info/exclude)")
    if not shared and not exclude and not force_gitignore:
        print("ℹ This is not a git repository — entries go to .gitignore. After `git init` run the update again.")

    # manifest i ustawienia projektu
    old_version = (manifest or {}).get("version") or ("unknown" if update else None)
    new_version = version_of(SRC)
    if not dry:
        man_p.parent.mkdir(parents=True, exist_ok=True)
        man_p.write_text(json.dumps({
            "version": new_version,
            # źródło aktualizacji: --source, poprzednie (nie z migrowanej fabryki) albo katalog tej fabryki
            "source": opts.get("source") or ((manifest or {}).get("source") if legacy is None else None) or str(SRC),
            "mode": mode,
            "python": py,
            "ignore": "gitignore" if force_gitignore else "exclude",
            "packs": {pid: str(available[pid].get("version", "0.0.0")) for pid in packs},
            "installed_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "files": dict(sorted(plan.files.items())),
            "skill_overrides": (manifest or {}).get("skill_overrides") or {},   # wpisy fabryki w skillOverrides
            **({"skill_describe": manifest["skill_describe"]} if (manifest or {}).get("skill_describe") else {}),
            **({"auto_update": manifest["auto_update"]} if "auto_update" in (manifest or {}) else {}),   # update.py --auto
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if not had_settings or language != settings["language"] or commit_language != settings["commit_language"]:
            pm.save_settings(dst_root, language=language, commit_language=commit_language)

    # raport
    mode_txt = "team (committed)" if shared else "private (outside git)"
    head = "Preview (nothing written)" if dry else ("Updated" if update else "Installed")
    ver = f"{old_version} → {new_version}" if update else new_version
    print(f"{head} in {dst_root} — version {ver}, {mode_txt} mode: new files {len(plan.created)}, "
          f"updated {len(plan.updated)}, merged {len(plan.merged)}, removed {len(plan.removed)}")
    print(f"  packs: {', '.join(packs) or '— (core only)'} · working language: {language} · "
          f"commit language: {commit_language}")
    for m in plan.merged:
        print(f"  ~ {m}")
    if not dry and update:     # autokorekta własnych plików projektu po zmianach nazw w rdzeniu (factory/migrations.py)
        spec = importlib.util.spec_from_file_location("tf_migrations", CORE / "factory" / "migrations.py")
        mig = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mig)
        for c in mig.apply(dst_root, dry=False):
            print(f"  ✓ migrated: {c}")
    if not dry:
        msg = rebuild(dst_root, dry)
        if msg:
            print(msg)
    # widoczność opisów skilli: z opisem to, czego używa ten projekt, reszta jako sama nazwa (factory/skill_profile.py)
    if dry:
        print("ℹ Skill visibility will be matched to the project after the install (factory/skill_profile.py).")
    else:
        spec = importlib.util.spec_from_file_location("tf_skill_profile", dst_root / "factory" / "skill_profile.py")
        prof = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prof)
        print(prof.summary(prof.apply(dst_root), False))
    print(f"ℹ Python for hooks and agents: `{py}` ({py_how}).")
    if not simple_command(py) or not python_works(py):
        print("⚠ Security hooks only work if this command runs Python. If it does not, fix it: "
              "run the install again with `--python <command>`.")
    if shared and py != PY_DEFAULT:
        print(f"⚠ Team mode: `{py}` goes into the committed .claude/settings.json. People on another OS "
              "need another command — a team on mixed systems is better off with private installs (without --shared).")
    new_skills = sorted({r.split("/")[2] for r in plan.created if r.startswith(".claude/skills/") and r.endswith("/SKILL.md")})
    if new_skills and update:
        print(f"  + new skills: {', '.join(new_skills)}")
    new_personas = sorted({Path(r).stem for r in plan.created if r.startswith("factory/packs/") and "/personas/" in r})
    if new_personas and update:
        print(f"  + new personas: {', '.join(new_personas)}")
    if plan.removed:
        print(f"  − moved to {BACKUP_DIR}/{stamp}/ (removed from the factory or a removed pack): "
              f"{', '.join(plan.removed[:10])}" + (f" … +{len(plan.removed) - 10}" if len(plan.removed) > 10 else ""))

    def listing(title: str, items: list[str], hint: str) -> None:
        if items:
            print(f"{title} ({len(items)}):")
            for c in items[:15]:
                print(f"  ! {c}")
            if len(items) > 15:
                print(f"  … and {len(items) - 15} more")
            print(f"  {hint}")

    listing("⚠ You changed these factory files — yours stay, the new version is next to them as *.factory-new",
            plan.kept_new, "Compare (`diff file file.factory-new`), carry over what you need and delete *.factory-new. "
            "In Claude Code `/core-factory-update` helps.")
    listing(f"ℹ Older install without a manifest — changed files overwritten, copies in {BACKUP_DIR}/{stamp}/",
            plan.backed_up, "If any of them held your change, carry it over from the copy.")
    listing("ℹ Removed from the factory, but changed by you — left in place", plan.kept_removed,
            "Delete them by hand if you no longer need them.")
    listing("ℹ You deleted these factory files — not restoring them", plan.skipped_deleted,
            "To get them back, remove their entries from .claude/factory-manifest.json and run the update.")
    listing("⚠ Skipped existing files with the same name as factory files (yours stay)", plan.conflicts,
            "Rename your file (e.g. the skill) and run the update if you also want the factory version.")

    personal = Path.home() / ".claude/skills"
    installed_skills = sorted({r.split("/")[2] for r in plan.files if r.startswith(".claude/skills/")})
    shadowed = [n for n in installed_skills if (personal / n / "SKILL.md").exists()]
    if shadowed:
        print(f"⚠ Personal skills in {personal} have the same names as factory skills and take precedence (Claude Code: "
              f"personal > project): {', '.join(shadowed)}. Rename the personal ones if agents should use the factory's.")
    if not shared:
        already = tracked(dst_root, ignored_paths(plan.files))
        if already:
            print(f"⚠ {len(already)} factory files are already tracked in the repository — ignore entries will not hide "
                  "them. Remove them from the index (files on disk stay):")
            print("  git rm -r --cached " + " ".join(sorted({p.split("/")[0] if p.startswith("factory/") else
                                                             "/".join(p.split("/")[:3]) for p in already})[:12]))
        if not (dst_root / "CLAUDE.md").exists() and (dst_root / "AGENTS.md").exists():
            print("⚠ The project uses AGENTS.md: CLAUDE.local.md alone makes Claude stop reading it. Add the line "
                  "`@AGENTS.md` at the top of CLAUDE.local.md.")
    if not dry and not update:
        md = "CLAUDE.md" if shared else "CLAUDE.local.md"
        dispatchers = [pid for pid in packs if pid in ("pack-it", "pack-ev")]
        start = {"pack-it": "`claude --agent maja` (describe the problem)", "pack-ev": "`claude --agent iwona` (EV)"}
        print(f"""
Next:
  1. Fill in your project's test/lint/build commands in {md}.
  2. Run `claude` once in the project directory and accept folder trust (hooks and permissions need it).
  3. Start: {' or '.join(start[d] for d in dispatchers) or 'a persona from .claude/catalog.md'}, e.g. `claude --agent <name>`.
  4. Costs: the `zrownowazony` profile works right away; `{py} factory/profile.py oszczedny|jakosc` switches the team.
  Packs: `tf add <pack>` / `tf remove <pack>` · languages: `tf language <code>`, `tf commit-language <code>`.
  Updates: `{py} factory/update.py` (or `tf`, or `/core-factory-update` in Claude Code).""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
