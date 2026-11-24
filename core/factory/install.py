#!/usr/bin/env python3
"""
Installs and updates the team factory (core + selected packs) in a project. Standard library only
(PyYAML for pack metadata: system copy or the one bundled in .tf/factory/_vendor).

Run it from the project directory — the project is the current directory, the factory is where this script lives:

  cd ~/projects/my-app
  python3 "$TEAM_FACTORY/core/factory/install.py"                     # private install (default): nothing gets committed
  python3 "$TEAM_FACTORY/core/factory/install.py" --dry-run           # show what would happen
  python3 "$TEAM_FACTORY/core/factory/install.py" --packs pack-it,pack-ux   # choose packs without asking
  python3 "$TEAM_FACTORY/core/factory/install.py" --add pack-ux       # add a pack to an existing install
  python3 "$TEAM_FACTORY/core/factory/install.py" --remove pack-ux    # remove a pack
  python3 "$TEAM_FACTORY/core/factory/install.py" --shared            # team install: the factory is committed with the project
  python3 "$TEAM_FACTORY/core/factory/install.py" --gitignore         # private, but entries go to .gitignore, not .git/info/exclude
  python3 "$TEAM_FACTORY/core/factory/install.py" --python py         # force the Python command for hooks (default: detected)
  python3 "$TEAM_FACTORY/core/factory/install.py" --yes               # no questions: defaults or the previous choice
  python3 "$TEAM_FACTORY/core/factory/install.py" --pack-dir ~/src/my-domain/factory-pack --add pack-my-domain
                                                                      # a pack from outside the factory's packs/

External packs: `--pack-dir <source>` (comma-separated or repeated) adds a pack source outside the factory's `packs/`:
a directory with `pack.yaml`, a directory whose subdirectories hold packs (`*/pack.yaml`), or a git repository URL
(`https://…`, `file://…`, `…/repo.git`; `#<ref>` pins a tag or branch, without it the latest `vX.Y.Z` tag, else the
default branch) searched the same way. The same contract applies as to `packs/`: `kind` and id prefix, `requires.core`
(checked by `.tf/factory/build.py check`), the skill gate. Their skills pass `skill_audit.py` first (high severity
stops the install). The sources are remembered in the manifest (and the team lock), so updates fetch the packs again;
`--drop-pack-dir <source>` forgets one (remove its packs with `--remove`). A pack id taken by the factory is refused.

The core is always installed. Packs (`packs/pack-*`) are chosen interactively on the first install (or with
`--packs`); later runs keep the previous choice. Modes (`modes/mode-*`, e.g. `mode-team`) are on-demand ways of
working installed like packs (`--add mode-team`, `--remove mode-team`). A default pack or mode that is new in this
version is added once on update; one you removed does not come back. A pack's required packs are added automatically.
There is no language setting: the agents answer in the language you write in (and write your documents in it), and
commit messages follow the language of the repository's history (`git log`; a new repository: English).

`TEAM_FACTORY` is the factory directory set once in your shell profile (e.g. `export TEAM_FACTORY=~/tools/tf`); any
path works too, relative to the current directory. The project can also be given as the first argument.
Running the installer again in an installed project = update (`--update` is not needed).

Day to day you update from inside the project: `python3 .tf/factory/update.py` (or `tf`, or `/core-factory-update`).

Private mode (default): skills, hooks, `.tf/factory/`, factory tests (`.claude/tests/`) go into the project; permissions and
hooks into `.claude/settings.local.json`, rules into `CLAUDE.local.md`; all factory paths into `.git/info/exclude`.
Team mode (`--shared`): `.claude/settings.json`, `CLAUDE.md`, CI workflow and `.gitignore`.
After copying, the installer builds the agents (`.tf/factory/build.py`) for the chosen packs.

The manifest `.claude/factory-manifest.json` records the version, source, mode, packs and a hash of every installed
file (as it is after `.tf/factory/build.py`). The manifest stays outside git; in team mode the installer also writes
`.claude/factory-lock.json` (version, packs, file hashes — nothing machine-specific), committed with the
project, so a fresh clone without the manifest updates from it instead of skipping factory files. Thanks to them an
update:
- overwrites factory files you did not change and adds new ones;
- overwrites factory files changed in the project (like node_modules — change the factory repository instead); never
  touches `.tf/config/` (your config.yaml overrides, own personas, roles and traits);
- moves files removed from the factory (or from a removed pack) to `.tf/backup/<date>/` (if unchanged);
- never touches your own skills, personas, roles and traits (files the factory did not install).
Installs of claude-team-factory or ev-team-factory are migrated: the old instruction and ignore blocks are replaced
and the packs whose `migrates_from` names the old factory are selected (with their available `optional_packs`).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import os
import shutil
import re
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "✓", "⚠" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # the engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]      # the factory repository: core/, packs/ and modes/
CORE = SRC / "core"
PACKS_SRC = SRC / "packs"
MODES_SRC = SRC / "modes"   # on-demand work modes (kind: mode) — installed like packs
ITEM_DIRS = ((PACKS_SRC, "pack", "pack-"), (MODES_SRC, "mode", "mode-"))   # directory, kind, id prefix
MANIFEST = ".claude/factory-manifest.json"
# Team mode: the manifest is outside git (the source and Python are local), so a clone gets the update base from the lock —
# the version, packs, languages and file hashes of the factory, committed with the project.
LOCK = ".claude/factory-lock.json"
BACKUP_DIR = ".tf/backup"
MARK_BEGIN, MARK_END = "<!-- team-factory:begin -->", "<!-- team-factory:end -->"
GI_BEGIN, GI_END = "# team-factory:begin (managed by factory/install.py)", "# team-factory:end"
# install markers we migrate from (claude-team-factory, ev-team-factory)
LEGACY_MARKS = [(f"<!-- {n}:begin -->", f"<!-- {n}:end -->") for n in ("claude-team-factory", "ev-team-factory")]
LEGACY_GI = [(f"# {n}:begin (zarządzane przez factory/install.py)", f"# {n}:end")
             for n in ("claude-team-factory", "ev-team-factory")]
CORE_DIRS = {"skills": ".claude/skills", "hooks": ".claude/hooks", "factory": ".tf/factory",
             "tests": ".claude/tests"}   # the factory tests do not mix with your `tests/` (pytest will not collect them)
CORE_FILES = {"guide/JEV.md": ".claude/JEV.md",   # guide and FAQ in .tf/factory/ — no README in the project root
              "guide/GUIDE.md": ".tf/factory/GUIDE.md", "guide/FAQ.md": ".tf/factory/FAQ.md",
              "guide/LOOP.md": ".tf/factory/LOOP.md"}
PACK_DIRS = {"skills": ".claude/skills", "hooks": ".claude/hooks", "tests": ".claude/tests",
             "workflows": ".claude/workflows",   # workflows: Claude Code multi-agent scripts (Workflow)
             "analyzers": ".tf/factory/analyzers"}   # tf analyze modules (analyzer.yaml, scripts/, fixtures/)
PACK_META = ("pack.yaml", "roles", "personas", "traits", "technologies.json", "GUIDE.md", "semgrep.yml",
             "migrations.py")   # → .tf/factory/packs/<id>/
SHARED_ONLY_FILES = {"workflows/team-factory.yml": ".github/workflows/team-factory.yml"}
USER_OWNED = (".tf/config/",)   # project configuration — the installer creates the template, never overwrites it
ALWAYS_OWNED = (".claude/cleanroom.json",)   # assembled from the core and packs — always from the current version
# The factory's own machinery: without these files the installer, hooks and agents do not work, so a missing one is
# always restored (a deleted skill or scenario stays deleted).
REQUIRED = (".tf/factory/", ".claude/hooks/")
# Scripts of a skill import each other (run_state.py imports ui_snap.py): a missing script of a skill that stays — its
# SKILL.md is there — is restored like the machinery; a skill deleted as a whole stays deleted with its scripts.
SKILL_SCRIPT = re.compile(r"^((?:\.claude|\.tf/plugin)/skills/([^/]+))/scripts/")


def skill_stays(root: Path, rel: str) -> bool:
    """`rel` is a script of a skill that is still installed. In the plugin layout SKILL.md is only in .tf/plugin/skills/,
    and .claude/skills/<skill>/scripts/ holds the copies that skill texts call — they count too."""
    m = SKILL_SCRIPT.match(rel)
    return bool(m) and any((root / base / m.group(2) / "SKILL.md").is_file()
                           for base in (".claude/skills", ".tf/plugin/skills"))
GENERATED = (".claude/agents/_generated/", ".claude/catalog.md", ".tf/plugin/agents/")   # built in the project by .tf/factory/build.py
SKIP = ("__pycache__", ".pyc", "/logs/", ".factory-new")
# Layouts (docs/plans/2026-11-20-tryb-fabryki-plan.md). `default` (the classic layout, `--layout default`): the factory
# lives in .claude/ and every Claude Code session in the project loads it, the Desktop app too. `plugin` (factory mode,
# the default since T5): the factory lives in a local plugin in .tf/plugin/, registered for the folder with the Claude
# Code CLI in local scope (plugin_register.py: settings.local.json and the user's Claude config), so every session in
# the folder loads it — a plain `claude`, `tf code` and the Desktop app — with the commands /tf:tf, /tf:tf-task…;
# without the registration only `tf code` loads it (claude --plugin-dir .tf/plugin --settings <session settings>).
LAYOUTS = ("default", "plugin")
PLUGIN = ".tf/plugin"
PLUGIN_SKILLS = PLUGIN + "/skills/"
PLUGIN_MARKET = ".tf/.claude-plugin"
CLASSIC_OK = ("✓ Classic layout: the factory is in .claude/ — every Claude Code session loads it (also the Desktop app).")
# Core tests that make sense only in the factory repository (paths relative to core/): the N5 run evals import
# `scripts/export_pdi_runs.py` and `modes/mode-pdi/.../phase_result.py` from the source, so in a project they would fail on import.
# They do not go to `.claude/tests/` (an update removes their copies from earlier versions); `tools/workspace.py check`
# runs them from the source (core/tests/).
FACTORY_ONLY = ("tests/flow_evals/", "tests/flow_evals_runner.py", "tests/test_flow_evals.py",
                "tests/test_export_pdi_runs.py")


CONFIG_TEMPLATE = """# Factory configuration overrides for this project (merged recursively onto .tf/factory/config.yaml).
# Write only what you change, e.g.:
#   default_profile: economy
#   tiers:
#     fast: {maxTurns: 20}
# After a change: python3 .tf/factory/build.py
"""
CONFIG_DIRS = {"personas": "the project's own personas (they override core and pack personas with the same name)",
               "roles": "the project's own roles (they override pack roles with the same name)",
               "traits": "the project's own traits (*.md)"}


def ensure_config(dst_root: Path) -> list[str]:
    """`.tf/config/` — project configuration: the config.yaml template and directories for custom personas, roles and traits. Does not
    change existing files."""
    base, made = dst_root / ".tf" / "config", []
    base.mkdir(parents=True, exist_ok=True)
    if not (base / "config.yaml").exists():
        (base / "config.yaml").write_text(CONFIG_TEMPLATE, encoding="utf-8")
        made.append(".tf/config/config.yaml")
    for d, what in CONFIG_DIRS.items():
        (base / d).mkdir(exist_ok=True)
        if not (base / d / "README.md").exists():
            (base / d / "README.md").write_text(f"# .tf/config/{d}/\n\n{what.capitalize()}. After a change: "
                                                  "`python3 .tf/factory/build.py`.\n", encoding="utf-8")
    return made


def load_packs_module():
    """.tf/factory/packs.py from the NEW version of the factory (reading pack.yaml, project settings)."""
    spec = importlib.util.spec_from_file_location("tf_packs_src", CORE / "factory" / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def available_packs(external: dict[str, Path] | None = None) -> dict[str, dict]:
    """Packs from packs/ and modes from modes/ (the same pack.yaml); kind and id prefix must match the directory.
    `external`: source → directory of packs outside the factory (--pack-dir); the same rules, the id must not be taken."""
    pm = load_packs_module()
    out = {}
    for root, kind, prefix in ITEM_DIRS:
        for p in sorted(root.glob("*/pack.yaml")) if root.is_dir() else []:
            data = pm.load_yaml(p)
            data["_dir"] = p.parent
            pid = data.get("id") or p.parent.name
            if data.get("kind", "pack") != kind or not pid.startswith(prefix):
                raise ValueError(f"{pid} in {root.name}/ needs `kind: {kind}` and an id starting with {prefix}")
            out[pid] = data
    prefixes = {kind: prefix for _, kind, prefix in ITEM_DIRS}
    for src, base in (external or {}).items():
        files = pack_yaml_files(base)
        if not files:
            raise ValueError(f"no pack.yaml in the pack source {src} (expected pack.yaml or */pack.yaml)")
        for p in files:
            data = pm.load_yaml(p)
            data["_dir"], data["_external"] = p.parent, src
            pid = data.get("id") or p.parent.name
            kind = data.get("kind", "pack")
            if kind not in prefixes or not str(pid).startswith(prefixes[kind]):
                raise ValueError(f"{pid} in the pack source {src} needs `kind: pack` and an id starting with pack- "
                                 "(or `kind: mode` and mode-)")
            if pid in out:
                where = out[pid].get("_external") or "the factory"
                raise ValueError(f"{pid} from the pack source {src}: the id is already used by {where} — rename the pack")
            out[pid] = data
    return out


def pack_yaml_files(base: Path) -> list[Path]:
    """A pack in a directory (pack.yaml) or a directory of packs (*/pack.yaml)."""
    return [base / "pack.yaml"] if (base / "pack.yaml").is_file() else sorted(base.glob("*/pack.yaml"))


def is_git(src: str) -> bool:
    return src.startswith(("https://", "http://", "git@", "ssh://", "file://")) or src.split("#")[0].endswith(".git")


def normalize_source(src: str) -> str:
    """Local path → absolute (from the current directory); a git address is left unchanged."""
    return src if is_git(src) else str(Path(src).expanduser().resolve())


def _vt(tag: str) -> tuple[int, ...]:
    return tuple(int(x) for x in tag[1:].split("."))


def latest_release_tag(url: str) -> str | None:
    """Highest `vX.Y.Z` tag of the repository (git ls-remote); None when there are no tags or on error."""
    try:
        r = subprocess.run(["git", "ls-remote", "--tags", "--refs", url], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    tags = re.findall(r"refs/tags/(v\d+\.\d+\.\d+)$", r.stdout, re.M) if r.returncode == 0 else []
    return max(tags, key=_vt) if tags else None


def fetch_pack_source(src: str, tmp: Path) -> tuple[Path | None, str]:
    """Pack source directory (a git repository cloned into `tmp`). Returns (directory or None, description of the problem)."""
    if not is_git(src):
        p = Path(src)
        return (p, "") if p.is_dir() else (None, "directory not found")
    url, _, ref = src.partition("#")
    ref = ref or latest_release_tag(url) or ""
    dest = tmp / f"src{len(list(tmp.iterdir()))}"
    cmd = ["git", "clone", "--depth", "1", "--quiet"] + (["--branch", ref] if ref else []) + [url, str(dest)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)
    return (dest, "") if r.returncode == 0 else (None, r.stderr.strip()[-400:])


def audit_external(packs: list[str], available: dict) -> tuple[int, list[str]]:
    """skill_audit.py (from this factory version) on the skills of external packs: (number of high findings, rows)."""
    spec = importlib.util.spec_from_file_location("tf_skill_audit_src", CORE / "factory" / "skill_audit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    high, lines = 0, []
    for pid in packs:
        if not available[pid].get("_external") or not (available[pid]["_dir"] / "skills").is_dir():
            continue
        for d in mod.find_skills(available[pid]["_dir"] / "skills"):
            for f in mod.audit_skill(d)["findings"]:
                if f["severity"] in ("high", "medium"):
                    high += f["severity"] == "high"
                    lines.append(f"  {'✗' if f['severity'] == 'high' else '⚠'} {pid}/{d.name}: {f['code']} — "
                                 f"{f['file']}:{f['line']} {f['message']}")
    return high, lines


def offered_before(manifest: dict | None, available: dict) -> set[str] | None:
    """What the project has already been offered. A manifest from before modes (no `offered`): all packs, no modes."""
    if not manifest:
        return None
    if "offered" in manifest:
        return set(manifest["offered"])
    return set(manifest.get("packs") or {}) | {pid for pid, p in available.items() if p.get("kind", "pack") == "pack"}


def core_config() -> dict:
    return load_packs_module().load_yaml(CORE / "factory" / "config.yaml")


PY_DEFAULT = "python3"            # command written into the factory source files
PY_NAMES = ("python3", "python", "py")


def python_works(cmd: str) -> bool:
    """Whether the command really runs Python 3.9+ (the Microsoft Store alias fails with an error and is rejected)."""
    try:
        r = subprocess.run([cmd, "-c", "import sys; print(int(sys.version_info >= (3, 9)))"],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError, ValueError):
        return False
    return r.returncode == 0 and r.stdout.strip() == "1"


def choose_python(forced: str | None, previous: str | None) -> tuple[str, str]:
    """Returns (command, description of origin). Order: --python, the previous install's choice, detection, path."""
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
    """Factory hooks and permission rules run Python with the `py` command instead of `python3`."""
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
    """A custom status line in ~/.claude/settings.json — a project setting would shadow it, so we do not add one then."""
    try:
        return bool(json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8")).get("statusLine"))
    except (OSError, ValueError):
        return False


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version_of(root: Path) -> str:
    """Core version: core/factory/VERSION in the factory repository or .tf/factory/VERSION in the project."""
    for p in (root / "core" / "factory" / "VERSION", root / ".tf" / "factory" / "VERSION"):
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    return "0.0.0"


class Plan:
    def __init__(self, dst_root: Path, dry: bool, update: bool, old_files: dict | None, stamp: str):
        self.root, self.dry, self.update, self.old, self.stamp = dst_root, dry, update, old_files, stamp
        self.created, self.updated, self.conflicts, self.merged = [], [], [], []
        self.kept_new, self.backed_up, self.removed, self.kept_removed, self.skipped_deleted = [], [], [], [], []
        self.overwritten, self.restored = [], []
        self.files: dict[str, str] = {}          # new manifest: path → hash of the installed factory version

    def _required(self, rel: str) -> bool:
        """A factory file that is restored when missing: the machinery, or a script of a skill that is still there."""
        if rel.startswith(REQUIRED):
            return True
        return skill_stays(self.root, rel)

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
        """Factory file `src` (or ready content `data`, e.g. assembled from the core and packs) at path `rel`."""
        if data is None:
            # only the factory CI workflow; in skills and scenarios `tests/` are the project's tests (settings: compose_settings)
            data = retarget(src.read_bytes()) if rel in SHARED_ONLY_FILES.values() else src.read_bytes()
        dst, new_hash = self.root / rel, sha(data)
        old_hash = (self.old or {}).get(rel)
        self.files[rel] = new_hash
        if not dst.exists():
            if self.update and old_hash is not None and not self._required(rel):   # you deleted it — we respect that
                self.skipped_deleted.append(rel)
                return
            if self.update and old_hash is not None:     # required factory file missing (deleted, antivirus, broken copy)
                self.restored.append(rel)
                self._write(dst, data, src)
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
        elif old_hash is not None and sha(cur) == old_hash:          # you did not change it — we update
            self.updated.append(rel)
            self._write(dst, data, src)
        elif old_hash is not None:                                    # factory file changed in the project: like
            self.overwritten.append(rel)                              # node_modules — overwritten with the factory version
            self._write(dst, data, src)
        elif self.update and self.old is None:                        # an old install without a manifest
            self._backup(rel)
            self.updated.append(rel)
            self._write(dst, data, src)
        else:                                                         # your file with the same name
            self.conflicts.append(rel)
            self.files.pop(rel, None)

    def remove_obsolete(self) -> None:
        """Files from the previous factory version that the new version no longer has."""
        for rel, old_hash in (self.old or {}).items():
            if rel in self.files or rel.startswith(GENERATED):   # agents and the catalog are built by build.py in the project
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
                parent = p.parent                                       # empty directories left after a removed skill
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
            write_keeping_eol(path, text)


def write_keeping_eol(path: Path, text: str) -> None:
    """Writes `text` (read with universal newlines) in the line ending the file already has: LF by default, CRLF only
    when the file had it. A text-mode write would turn every LF file into CRLF on Windows (lint with endOfLine: lf)."""
    try:
        crlf = b"\r\n" in path.read_bytes()
    except OSError:
        crlf = False
    path.write_bytes((text.replace("\r\n", "\n").replace("\n", "\r\n") if crlf else text).encode("utf-8"))


def retarget(data: bytes) -> bytes:
    """In the target project the factory tests live in `.claude/tests/`."""
    return data.replace(b" tests/test_", b" .claude/tests/test_").replace(b"(python3 tests/", b"(python3 .claude/tests/")


# Packs and modes retired from the factory: id → what replaced them. A project update that had them skips them
# with a message (files go to .tf/backup/ like any file the factory no longer ships); an explicit request
# for such an identifier (--packs, --add) is refused with an explanation.
RETIRED_PACKS = {"mode-talos": "the task loop is part of the core now: use /tf-task (agent `tf-task`)",
                 "pack-ev": "EV knowledge lives in the EV Intelligence project (github.com/dbqm45/ev-intelligence): "
                            "ev-* skills and an MCP server for Claude Code (integrations/claude-code/README.md there)"}


# Rules retired from the template: the Bash sandbox turns Read(...) from permissions.deny into a read ban for programs,
# so npm test and build could not read node_modules. Context economy is now enforced by the guard_paths hook.
RETIRED_DENY = ("Read(./node_modules/**)", "Read(./dist/**)", "Read(./build/**)", "Read(./coverage/**)",
                "Read(**/package-lock.json)", "Read(**/pnpm-lock.yaml)", "Read(**/yarn.lock)")


# Hooks retired from the factory: an update moves the file to .tf/backup/ (remove_obsolete) and drops its registration
# from the project's settings here, so a session does not run a missing script. The plugin layout regenerates
# hooks.json, so only the default layout needs this.
# after 24.12.2: isolation_notice (SessionStart) — the status line shows the level, `tf doctor` and `tf isolation` the gaps.
RETIRED_HOOKS = ("isolation_notice.py",)


def drop_retired_hooks(settings: dict) -> dict:
    """A copy of the settings without the registrations of RETIRED_HOOKS (an empty group or event goes too)."""
    out = json.loads(json.dumps(settings))
    hooks = out.get("hooks") if isinstance(out.get("hooks"), dict) else None
    if not hooks:
        return out

    def retired(h) -> bool:
        parts = [h.get("command", ""), *(h.get("args") or [])] if isinstance(h, dict) else []
        return any(isinstance(x, str) and f".claude/hooks/{name}" in x for x in parts for name in RETIRED_HOOKS)

    for event, groups in list(hooks.items()):
        if not isinstance(groups, list):
            continue
        kept = []
        for g in groups:
            if not isinstance(g, dict) or not isinstance(g.get("hooks"), list):
                kept.append(g)
                continue
            hs = [h for h in g["hooks"] if not retired(h)]
            if hs:
                kept.append({**g, "hooks": hs})
            elif not g["hooks"]:
                kept.append(g)
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event)
    return out


# Hook fields that an update adds to a hook already present in the project (onFailure: Claude Code ≥ 2.1.295).
HOOK_KEYS_ADDED = ("onFailure",)


def merge_settings(src: dict, dst: dict) -> dict:
    out = drop_retired_hooks(dst)
    out.setdefault("$schema", src.get("$schema"))
    for k, v in (src.get("env") or {}).items():
        out.setdefault("env", {}).setdefault(k, v)          # your values take precedence
    perms = out.setdefault("permissions", {})
    if "deny" in perms:
        perms["deny"] = [r for r in perms["deny"] if r not in RETIRED_DENY]
    for key in ("allow", "ask", "deny"):
        cur = perms.setdefault(key, [])
        cur += [r for r in (src.get("permissions", {}).get(key) or []) if r not in cur]
    perms.setdefault("defaultMode", src.get("permissions", {}).get("defaultMode", "default"))
    for k, v in src.items():                                  # remaining keys: your values take precedence
        if k not in ("env", "permissions", "hooks", "$schema"):
            out.setdefault(k, v)
    hooks = out.setdefault("hooks", {})
    for event, entries in (src.get("hooks") or {}).items():
        cur = hooks.setdefault(event, [])
        for e in entries:
            have = json.dumps(cur, ensure_ascii=False)
            # the hook is already there when all its arguments appear in the settings (the Python command may differ)
            missing = [h for h in e.get("hooks", [])
                       if not all(a in have for a in (h.get("args") or [h.get("command", "")]))]
            for h in e.get("hooks", []):          # new factory fields in a hook that is already there (the user's choice stays)
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


def claude_md_section(py: str = PY_DEFAULT, root: Path | None = None, cfg: dict | None = None) -> str:
    """Factory section in CLAUDE.md / CLAUDE.local.md: core rules + language (conversation, commits from `git log`)."""
    text = (CORE / "CLAUDE.md").read_text(encoding="utf-8")
    body = text.split("\n", 1)[1] if text.startswith("# ") else text   # without the "# Project rules" heading
    body = "\n".join("#" + ln if ln.startswith("## ") else ln for ln in body.splitlines())   # subsections one level lower
    if py != PY_DEFAULT:
        shown = py if simple_command(py) else f'"{py}"'
        body = (f"- **Python in this project: `{shown}`.** Wherever skills, the guide and messages say `python3`, "
                f"run `{shown}` (e.g. `{shown} .claude/hooks/project_record.py status`).\n" + body.lstrip("\n"))
    if root is not None and cfg:
        body = body.rstrip() + "\n\n### Language\n" + "\n".join(load_packs_module().language_lines(cfg, root))
    return f"{MARK_BEGIN}\n## Agent team (team factory)\n{body.strip()}\n{MARK_END}\n"


def drop_legacy_blocks(text: str, marks: list[tuple[str, str]]) -> str:
    """Removes blocks of old factories (claude-team-factory, ev-team-factory) — replaces them with this factory's block."""
    for begin, end in marks:
        if begin in text and end in text:
            a, b = text.index(begin), text.index(end) + len(end)
            text = (text[:a].rstrip() + "\n\n" + text[b:].lstrip("\n")).strip("\n")
            text = text + "\n" if text else ""
    return text


def load_migrations():
    """The core migrations module (.tf/factory/migrations.py) of the factory being installed."""
    spec = importlib.util.spec_from_file_location("tf_migrations", CORE / "factory" / "migrations.py")
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    return mig


COMMANDS_SECTION = re.compile(r"(### Commands\n)(.*?)(?=\n### |\n" + re.escape(MARK_END) + ")", re.S)
COMMANDS_DEFAULT_HINT = "adapt to your project"


def keep_commands(section: str, old: str) -> str:
    """An update keeps the project's commands in the "Commands" subsection (entered by `tf onboard` or by a human).
    A subsection with the note "adapt to your project" is a factory template — it is replaced like the rest of the block."""
    start = old.find(MARK_BEGIN)
    mine = COMMANDS_SECTION.search(old, start) if start >= 0 else None
    if not mine or COMMANDS_DEFAULT_HINT in mine.group(2):
        return section
    return COMMANDS_SECTION.sub(lambda m: m.group(1) + mine.group(2), section, count=1)


def with_block(text: str, begin: str, end: str, block: str, replace: bool) -> str:
    """Inserts a block between markers at the end of the file or (with replace) replaces the existing one."""
    if begin not in text:
        return (text.rstrip() + "\n\n" if text.strip() else "") + block
    if not replace:
        return text
    start = text.index(begin)
    end_at = text.find(end, start + len(begin))
    if end_at < 0:      # corrupted block (no end marker) — we do not guess, so as not to delete human content
        raise SystemExit(f"✗ Marker {begin!r} without {end!r} in the instructions file. Fix it by hand (add the end marker "
                         "or remove the start of the block) and run again.")
    stop = end_at + len(end)
    rest = text[stop:].lstrip("\n")
    return text[:start].rstrip() + ("\n\n" if text[:start].strip() else "") + block + ("\n" + rest if rest else "")


def ignored_paths(files: dict[str, str] | None = None) -> list[str]:
    """Every path installed by the factory — per skill, hook and workflow, so that your own stay in the repo."""
    # `.tf/`: results of the factory's work (reports, registry, logs, runs, copies) — private, entirely outside the repo.
    out = [".tf/factory/", ".claude/agents/_generated/", ".claude/tests/", ".claude/catalog.md", ".claude/cleanroom.json",
           ".claude/JEV.md", ".claude/settings.local.json", "CLAUDE.local.md", MANIFEST, BACKUP_DIR + "/",
           ".claude/agent-memory/", ".claude/factory-profile.json", ".claude/factory-settings.json",
           ".claude/skill-gate.json", ".claude/scratch/", ".tf/", "*.factory-new"]
    rels = sorted(files or {})
    out += list(dict.fromkeys("/".join(r.split("/")[:3]) + "/" for r in rels if r.startswith(".claude/skills/")))
    out += [r for r in rels if r.startswith((".claude/hooks/", ".claude/workflows/"))]
    return out


def git_exclude_path(dst_root: Path) -> Path | None:
    """Path of the repository's `info/exclude` (works in a worktree too); None when this is not a git repository."""
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
    """Mode of an old install without a manifest — by the factory section in CLAUDE.local.md / CLAUDE.md."""
    for name, mode in (("CLAUDE.local.md", "private"), ("CLAUDE.md", "shared")):
        p = dst_root / name
        if p.exists() and any(b in p.read_text(encoding="utf-8") for b in [MARK_BEGIN, *(m[0] for m in LEGACY_MARKS)]):
            return mode
    return None


LEGACY_DEFAULT = ("pack-it", "pack-ux", "pack-docs")   # claude-team-factory: the IT factory the core grew out of


def legacy_packs(manifest: dict | None, dst_root: Path, available: dict) -> list[str] | None:
    """Packs for an old-factory install (a manifest without a pack list): those whose `migrates_from` in pack.yaml
    names it (from the source in the manifest or the marker in CLAUDE.md), with the available `optional_packs`."""
    if not manifest or "packs" in manifest:
        return None
    src = str(manifest.get("source", "")).lower()
    md = " ".join((dst_root / n).read_text(encoding="utf-8") for n in ("CLAUDE.md", "CLAUDE.local.md")
                  if (dst_root / n).exists())
    found = [pid for pid, p in available.items()
             if any(str(n).lower() in src or f"{n}:begin" in md for n in p.get("migrates_from") or [])]
    if found:
        extra = [o for pid in found for o in available[pid].get("optional_packs") or [] if o in available]
        return sorted(dict.fromkeys(found + extra))
    old = next((n for n in ("ev-team-factory",) if n in src or f"{n}:begin" in md), None)
    if old:
        print(f"ℹ This is an install of {old}, but no available pack migrates from it — give its pack source "
              "(--pack-dir <directory|git URL>) or use the EV Intelligence project (github.com/dbqm45/ev-intelligence).")
        return [p for p in ("pack-docs",) if p in available]
    return [p for p in LEGACY_DEFAULT if p in available]


def dispatcher_hints(packs: list[str], available: dict, pm) -> list[str]:
    """Start commands from the packs' dispatchers (personas with `dispatcher: true`)."""
    out = []
    for pid in packs:
        for f in sorted((available[pid]["_dir"] / "personas").glob("*.yaml")):
            data = pm.load_yaml(f)
            if data.get("dispatcher") and data.get("name"):
                out.append(f"`claude --agent {data['name']}` ({available[pid].get('title') or pid} — describe the problem)")
    return out


def resolve_packs(chosen: list[str], available: dict) -> tuple[list[str], list[str]]:
    """Selected packs + those required by them. Returns (packs, unknown)."""
    unknown = [c for c in chosen if c not in available]
    out = [c for c in chosen if c in available]
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


def interactive_choice(available: dict, preset: list[str]) -> list[str]:
    """First install in a terminal: packs (the language is not chosen — agents answer in yours)."""
    print("Team factory — first install. The core is always installed.")
    print("\nAvailable packs and modes:")
    ids = list(available)
    for i, pid in enumerate(ids, 1):
        p = available[pid]
        mark = "*" if pid in preset else " "
        auto = " (mode — on-demand way of working)" if p.get("kind") == "mode" else ""
        print(f"  {i}. [{mark}] {pid} — {p.get('description', p.get('title', ''))}{auto}")
    raw = ask("Packs and modes to install: numbers or ids separated by commas, 'all', or Enter for the marked ones",
              ",".join(preset) or "none")
    if raw.strip().lower() == "all":
        chosen = ids
    elif raw.strip().lower() in ("none", "-", ""):
        chosen = []
    else:
        chosen = []
        for tok in (t.strip() for t in raw.split(",") if t.strip()):
            chosen.append(ids[int(tok) - 1] if tok.isdigit() and 0 < int(tok) <= len(ids) else tok)
    return chosen


def save_manifest(dst_root: Path, manifest: dict, shared: bool) -> None:
    """Manifest (local) and — in team mode — a lock without local data (committed with the project)."""
    (dst_root / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if shared:
        lock = {"version": manifest["version"], "packs": list(manifest["packs"]), "offered": manifest["offered"],
                **({"pack_dirs": manifest["pack_dirs"]} if manifest.get("pack_dirs") else {}), "files": manifest["files"]}
        (dst_root / LOCK).write_text(json.dumps(lock, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def rebuild(dst_root: Path, dry: bool) -> str:
    """Builds agents and the catalog in the project for the selected packs and languages (.tf/factory/build.py)."""
    if dry:
        return ""
    r = subprocess.run([sys.executable, ".tf/factory/build.py"], cwd=dst_root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        n = len(list((dst_root / ".claude" / "agents" / "_generated").rglob("*.md"))) + \
            len(list((dst_root / ".tf" / "plugin" / "agents").rglob("*.md")))
        return f"✓ Built {n} agents and the catalog (.tf/factory/build.py)."
    return ("⚠ `.tf/factory/build.py` reported problems — run `python3 .tf/factory/build.py check` and fix them:\n"
            + r.stdout[-1500:] + r.stderr[-500:])


def drop_rules_block(text: str) -> str:
    """CLAUDE.md / CLAUDE.local.md without the factory's block between the markers (the rest is yours and stays)."""
    start, stop = text.index(MARK_BEGIN), text.index(MARK_END) + len(MARK_END)
    head, tail = text[:start].rstrip(), text[stop:].lstrip("\n")
    return (head + ("\n\n" + tail if tail.strip() else "\n")) if head else tail


def strip_factory_settings(cur: dict, factory: dict, current: dict, overrides: set[str]) -> dict:
    """Project settings without what the factory put there in the old layout: its hooks (commands running
    .claude/hooks/<factory hook>), env values, status line, permission entries and managed skillOverrides.
    Your entries stay; `factory` is what the manifest recorded, `current` what this version would add."""
    out = json.loads(json.dumps(cur))
    hook_files: set[str] = set()
    for src in (factory, current):
        for groups in (src.get("hooks") or {}).values():
            for g in groups:
                for h in g.get("hooks") or []:
                    for part in [h.get("command", ""), *h.get("args", [])]:
                        if ".claude/hooks/" in part:
                            hook_files.add(part.split(".claude/hooks/", 1)[1].split()[0].strip("\"'"))

    def factory_hook(h: dict) -> bool:
        text = " ".join([h.get("command", ""), *h.get("args", [])])
        return any(f".claude/hooks/{name}" in text for name in hook_files)

    for event, groups in list((out.get("hooks") or {}).items()):
        kept = []
        for g in groups:
            hs = [h for h in g.get("hooks") or [] if not factory_hook(h)]
            if hs:
                kept.append({**g, "hooks": hs})
        if kept:
            out["hooks"][event] = kept
        else:
            out["hooks"].pop(event)
    if "hooks" in out and not out["hooks"]:
        out.pop("hooks")
    for src in (factory, current):
        for k, v in (src.get("env") or {}).items():
            if (out.get("env") or {}).get(k) == v:
                out["env"].pop(k)
        sl = src.get("statusLine")
        if (sl and out.get("statusLine") == sl) or ".claude/hooks/statusline.py" in json.dumps(out.get("statusLine") or ""):
            out.pop("statusLine", None)
        for kind in ("allow", "ask", "deny"):
            drop = set((src.get("permissions") or {}).get(kind) or [])
            if drop and kind in (out.get("permissions") or {}):
                out["permissions"][kind] = [x for x in out["permissions"][kind] if x not in drop]
                if not out["permissions"][kind]:
                    out["permissions"].pop(kind)
        for k, v in src.items():
            if k not in ("hooks", "env", "statusLine", "permissions", "$schema") and out.get(k) == v:
                out.pop(k)
    if "env" in out and not out["env"]:
        out.pop("env")
    if "permissions" in out and not out["permissions"]:
        out.pop("permissions")
    if overrides and isinstance(out.get("skillOverrides"), dict):
        for name in overrides:
            out["skillOverrides"].pop(name, None)
        if not out["skillOverrides"]:
            out.pop("skillOverrides")
    if set(out) <= {"$schema"}:
        out = {}
    return out


def register_module():
    """plugin_register.py of the factory being installed: registers .tf/plugin/ for the folder with the Claude Code CLI
    (local scope), so every session in it loads the factory — a plain `claude` and the Desktop app too."""
    spec = importlib.util.spec_from_file_location("tf_plugin_register_install",
                                                  Path(__file__).resolve().parent / "plugin_register.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def plugin_own_skills(dst_root: Path, old_files: dict) -> list[str]:
    """Skills in .tf/plugin/skills/ that the factory did not put there (no file of theirs in the manifest) — yours."""
    base = dst_root / PLUGIN_SKILLS
    if not base.is_dir():
        return []
    return sorted(d.name for d in base.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
                  and not any(r.startswith(f"{PLUGIN_SKILLS}{d.name}/") for r in old_files))


def leave_plugin(plan: "Plan", dst_root: Path, own_skills: list[str], dry: bool) -> list[str]:
    """Back to the classic layout: the factory files of .tf/plugin/ and .tf/.claude-plugin/ (also ones you changed —
    factory files are like node_modules) and the generated agents go to the backup; your own skills move to
    .claude/skills/ (unless a skill of that name is already there). Returns what is left in the plugin (yours)."""
    plugin_dirs = (PLUGIN + "/", PLUGIN_MARKET + "/")
    for rel in [r for r in plan.kept_removed if r.startswith(plugin_dirs)]:
        plan.kept_removed.remove(rel)
        plan.removed.append(rel)
        if not dry:
            target = dst_root / BACKUP_DIR / plan.stamp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst_root / rel), target)
    agents = dst_root / PLUGIN / "agents"                    # generated: rebuilt in .claude/agents/_generated
    if agents.is_dir() and not dry:
        target = dst_root / BACKUP_DIR / plan.stamp / PLUGIN / "agents"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(agents), target)
    for name in own_skills:
        src, dst = dst_root / PLUGIN_SKILLS / name, dst_root / ".claude" / "skills" / name
        if dst.exists():
            continue
        plan.merged.append(f".claude/skills/{name}/ (your skill, moved from .tf/plugin/skills/)")
        if not dry:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), dst)
    left = []
    for d in (dst_root / PLUGIN, dst_root / PLUGIN_MARKET):
        if not d.is_dir():
            continue
        if not dry:
            for sub in sorted((p for p in d.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                if not any(sub.iterdir()):
                    sub.rmdir()
            if not any(d.iterdir()):
                d.rmdir()
                continue
        left += sorted(p.relative_to(dst_root).as_posix() for p in d.rglob("*") if p.is_file())
    return left


def plugin_files(plan: "Plan", dst_root: Path, settings: dict, py: str, version: str) -> None:
    """The plugin's manifest, its hook registration (with the SessionStart hook that gives the factory rules) and the
    factory session's settings (env, status line, permissions) — `tf code` passes the latter with --settings."""
    hooks = json.loads(json.dumps(settings.get("hooks") or {}))
    rules_hook = {"type": "command", "command": py, "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/factory_rules.py"],
                  "timeout": 10}
    start = hooks.setdefault("SessionStart", [])
    if not any("factory_rules.py" in json.dumps(g) for g in start):
        start.insert(0, {"hooks": [rules_hook]})
    meta = {"name": "tf", "version": version, "description": "Team factory: skills, agents, hooks and rules of the "
            "/tf-task loop. Every Claude Code session in the folder loads it once registered (local scope); tf code "
            "loads it anyway."}
    plan.copy(None, PLUGIN + "/.claude-plugin/plugin.json", (json.dumps(meta, indent=2) + "\n").encode("utf-8"))
    market = {"name": "tf-project", "owner": {"name": "team factory"},       # .tf/ as a directory marketplace: the cloud
              "plugins": [{"name": "tf", "source": "./plugin", "description": meta["description"]}]}   # (tf cloud-setup)
    plan.copy(None, ".tf/.claude-plugin/marketplace.json", (json.dumps(market, indent=2) + "\n").encode("utf-8"))
    plan.copy(None, PLUGIN + "/hooks/hooks.json",
              (json.dumps({"hooks": hooks}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    session = {k: v for k, v in settings.items() if k != "hooks"}
    plan.copy(None, PLUGIN + "/session-settings.json",
              (json.dumps(session, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def compose_cleanroom(packs: list[str], available: dict) -> bytes:
    """`.claude/cleanroom.json`: description from the core + profiles from packs."""
    data = json.loads((CORE / "cleanroom.json").read_text(encoding="utf-8"))
    for pid in packs:
        f = available[pid]["_dir"] / "cleanroom.json"
        if f.exists():
            data["profiles"] = data.get("profiles", []) + json.loads(f.read_text(encoding="utf-8")).get("profiles", [])
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def compose_settings(packs: list[str], available: dict) -> dict:
    """Permissions and hooks of the core + packs (`settings.json` in a pack)."""
    base = json.loads(retarget((CORE / "settings.json").read_bytes()).decode("utf-8"))
    for pid in packs:
        f = available[pid]["_dir"] / "settings.json"
        if f.exists():
            base = merge_settings(json.loads(retarget(f.read_bytes()).decode("utf-8")), base)
    return base


REMOVED_OPTIONS = ("--language", "--commit-language")   # 12.0.0: language without settings


def parse_args(argv: list[str]) -> tuple[list[str], dict]:
    args, opts = [], {}
    it = iter(argv[1:])
    for a in it:
        if a in ("--source", "--python", "--packs", "--add", "--remove", "--layout", "--isolation"):
            opts[a.lstrip("-")] = next(it, "")
        elif a in REMOVED_OPTIONS:                            # old flags with a value — the value does not become a directory
            opts.setdefault("_removed", []).append(f"{a} {next(it, '')}".strip())
        elif a in ("--pack-dir", "--drop-pack-dir"):          # can be given several times
            opts.setdefault(a.lstrip("-"), []).extend(split_ids(next(it, "")))
        elif a.startswith("--") or a == "-h":
            opts[a] = True
        else:
            args.append(a)
    return args, opts


def isolation_module():
    spec = importlib.util.spec_from_file_location("tf_isolation_install", Path(__file__).resolve().parent / "isolation.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def isolation_refusal(level: str) -> str | None:
    """`--isolation <level>`: an unknown level, or an agent session choosing its own isolation → the message; else None."""
    iso = isolation_module()
    if level not in iso.LEVELS:
        return f"✗ Unknown --isolation {level!r}. Available: {', '.join(iso.LEVELS)}"
    if any(os.environ.get(v) for v in iso.SESSION_VARS):
        return ("✗ --isolation is chosen by a human in a terminal, not by an agent session — "
                "run the install outside Claude Code")
    return None


def split_ids(raw: str | None) -> list[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def main(argv: list[str]) -> int:
    import tempfile
    with tempfile.TemporaryDirectory(prefix="tf-packs-") as tmp:   # clones of external pack sources
        return _main(argv, Path(tmp))


def _main(argv: list[str], tmp: Path) -> int:
    args, opts = parse_args(argv)
    if opts.get("--help") or opts.get("-h"):
        print(__doc__)
        return 0
    dst_root = Path(args[0]).expanduser().resolve() if args else Path.cwd().resolve()   # default: the current directory
    if dst_root in (Path.home().resolve(), Path("/")):
        print(f"✗ {dst_root} is your home or root directory, not a project. Go to the project directory (cd …) "
              "or pass it as an argument.")
        return 2
    if not dst_root.is_dir():
        print(f"✗ Directory {dst_root} does not exist")
        return 2
    if dst_root == SRC or dst_root == CORE or CORE in dst_root.parents \
            or any(d in [dst_root, *dst_root.parents] for d in (PACKS_SRC, MODES_SRC)):
        print("✗ You are in the factory directory. Go to your project and run the installer from there, e.g.:\n"
              f"  cd ~/projects/my-app && python3 {CORE / 'factory' / 'install.py'}")
        return 2
    dry, update = bool(opts.get("--dry-run")), bool(opts.get("--update"))
    man_p = dst_root / MANIFEST
    manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.exists() else None
    lock_p = dst_root / LOCK
    lock = json.loads(lock_p.read_text(encoding="utf-8")) if lock_p.exists() else None
    if manifest is None and lock:          # clone of a team install: the update base from the lock
        print(f"ℹ No local manifest — using {LOCK} (version {lock.get('version')}) as the update base.")
        manifest = {"version": lock.get("version"), "mode": "shared", "packs": {p: "0.0.0" for p in lock.get("packs") or []},
                    "offered": lock.get("offered") or [], "pack_dirs": lock.get("pack_dirs") or [],
                    "files": lock.get("files") or {}}
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

    # packs and languages
    cfg = core_config()
    pm = load_packs_module()
    # external pack sources: remembered + --pack-dir − --drop-pack-dir
    dropped = {normalize_source(s) for s in opts.get("drop-pack-dir") or []}
    given = [normalize_source(s) for s in opts.get("pack-dir") or []]
    pack_dirs = [s for s in dict.fromkeys([*((manifest or {}).get("pack_dirs") or []), *given]) if s not in dropped]
    external, missing = {}, {}
    for s in pack_dirs:
        d, why = fetch_pack_source(s, tmp)
        if d is None:
            missing[s] = why
        else:
            external[s] = d
    for s in given:
        if s in missing:
            print(f"✗ Pack source not found: {s} ({missing[s]})")
            return 2
    try:
        available = available_packs(external)
    except ValueError as e:
        print(f"✗ Pack source: {e}")
        return 2
    old_sources = (manifest or {}).get("pack_sources") or {}
    for old in opts.get("_removed") or []:
        print(f"ℹ {old}: this option is gone — there is no language setting. The agents answer in the language you "
              f"write in; commits follow the repository's history (git log).")
    legacy = legacy_packs(manifest, dst_root, available)
    previous = list((manifest or {}).get("packs") or {}) if manifest and "packs" in manifest else legacy
    for pid in [p for p in (previous or []) if p in RETIRED_PACKS]:   # retired: an update skips them instead of failing
        print(f"ℹ {pid} was retired — {RETIRED_PACKS[pid]}. Its files move to .tf/backup/.")
    if previous:
        previous = [p for p in previous if p not in RETIRED_PACKS]
    offered = offered_before(manifest, available)
    new_defaults = [pid for pid, p in available.items() if p.get("default") and offered is not None
                    and pid not in offered and pid not in (previous or [])]
    preset = previous + new_defaults if previous is not None else \
        [pid for pid, p in available.items() if p.get("default")]
    if opts.get("packs") is not None and opts.get("packs") != "":
        chosen = [] if opts["packs"] in ("none", "-") else list(available) if opts["packs"] == "all" \
            else split_ids(opts["packs"])
    elif opts.get("packs") == "":
        chosen = []
    elif previous is None and not opts.get("--yes") and sys.stdin.isatty() and not dry:
        chosen = interactive_choice(available, preset)
    else:
        chosen = list(preset)
        if new_defaults:
            print(f"ℹ New default in this version: {', '.join(new_defaults)} (`tf remove <id>` if you don't want it).")
    chosen = [c for c in chosen if c not in split_ids(opts.get("remove"))] + split_ids(opts.get("add"))
    retired = [c for c in dict.fromkeys(chosen) if c in RETIRED_PACKS]
    if retired:
        print("✗ " + "; ".join(f"{c} was retired — {RETIRED_PACKS[c]}" for c in retired))
        return 2
    packs, unknown = resolve_packs(list(dict.fromkeys(chosen)), available)
    lost = [u for u in unknown if old_sources.get(u) in missing]
    if lost:
        for u in lost:
            print(f"✗ {u} comes from an external pack source that was not found: {old_sources[u]} "
                  f"({missing[old_sources[u]]}).")
        print("  Give its new location: --pack-dir <directory|git URL>, or drop the pack: "
              f"--remove {','.join(lost)} --drop-pack-dir <old source>. Nothing was changed.")
        return 2
    for s in missing:
        print(f"ℹ Pack source {s} not found ({missing[s]}) — forgotten (none of the chosen packs comes from it).")
    pack_dirs = [s for s in pack_dirs if s not in missing]
    if unknown:
        print(f"✗ Unknown packs: {', '.join(unknown)}. Available: {', '.join(available) or '—'}")
        return 2
    high, findings = audit_external(packs, available)
    if findings:
        print(f"Skill audit of external packs ({len(findings)} findings, high severity: {high}):")
        print("\n".join(findings[:30]) + ("\n  …" if len(findings) > 30 else ""))
    if high:
        print("✗ External pack skills have high-severity audit findings — nothing installed. Read the skills "
              "(.tf/factory/skill_audit.py <dir>) and fix the pack, or drop it.")
        return 2
    if shared:
        for s in pack_dirs:
            if not is_git(s):
                print(f"⚠ Team mode: the pack source {s} is a local path — teammates and CI need the same path. "
                      "A git URL works everywhere.")
    if legacy is not None:
        print(f"ℹ Migrating an install of {manifest.get('source') or 'an older factory'} "
              f"(version {manifest.get('version')}) — packs: {', '.join(packs) or 'none'}.")

    # factory mode is the default (plan 2026-11-20, T5): a new install and an update of an older install (a manifest
    # without `layout`) go to the plugin layout; `--layout default` (also through update.py) moves to the classic layout
    # in .claude/, which every session loads (the Desktop app too), and back with `--layout plugin`
    layout = opts.get("layout") or (manifest or {}).get("layout") or "plugin"
    if layout not in LAYOUTS:
        print(f"✗ Unknown --layout {layout!r}. Available: {', '.join(LAYOUTS)}")
        return 2
    iso_level = opts.get("isolation")
    if iso_level is not None:
        err = isolation_refusal(iso_level)
        if err:
            print(err)
            return 2
    plugin = layout == "plugin"
    was_plugin = (manifest or {}).get("layout") == "plugin"
    migrating = plugin and update and not was_plugin   # from the classic layout to the plugin
    returning = not plugin and update and was_plugin   # from the plugin back to the classic layout

    def place(f: Path, rel: str) -> None:
        """A factory file at its path; in the plugin layout a skill goes to the plugin in full, and its scripts and
        references also stay under .claude/skills/<skill>/ (commands in skill texts and tests use that path) — but
        without SKILL.md, so a plain claude session does not see the skill."""
        if plugin and rel.startswith(".claude/skills/"):
            plan.copy(f, PLUGIN_SKILLS + rel[len(".claude/skills/"):])
            if rel.endswith("/SKILL.md") and rel.count("/") == 3:
                return
        plan.copy(f, rel)

    # core files
    for d, target in CORE_DIRS.items():
        for f in sorted((CORE / d).rglob("*")):
            rel = target + "/" + f.relative_to(CORE / d).as_posix()
            if f.relative_to(CORE).as_posix().startswith(FACTORY_ONLY):
                continue
            if f.is_file() and not any(x in rel for x in SKIP):
                place(f, rel)
    for src_rel, dst_rel in {**CORE_FILES, **(SHARED_ONLY_FILES if shared else {})}.items():
        if (CORE / src_rel).exists():
            plan.copy(CORE / src_rel, dst_rel)
    if (SRC / "LICENSE").exists():
        plan.copy(SRC / "LICENSE", ".tf/factory/LICENSE")
    # pack files
    for pid in packs:
        base = available[pid]["_dir"]
        for d, target in PACK_DIRS.items():
            for f in sorted((base / d).rglob("*")):
                rel = target + "/" + f.relative_to(base / d).as_posix()
                if f.is_file() and not any(x in rel for x in SKIP):
                    place(f, rel)
        for meta in PACK_META:
            src_meta = base / meta
            files = [src_meta] if src_meta.is_file() else sorted(src_meta.rglob("*")) if src_meta.is_dir() else []
            for f in files:
                if f.is_file() and not any(x in f.name for x in SKIP):
                    plan.copy(f, f".tf/factory/packs/{pid}/" + f.relative_to(base).as_posix())
    plan.copy(None, ".claude/cleanroom.json", compose_cleanroom(packs, available))
    own_plugin_skills = plugin_own_skills(dst_root, (manifest or {}).get("files") or {}) if returning else []

    # settings: private → settings.local.json, team → settings.json (always merged with what is already there)
    src_set = apply_python(compose_settings(packs, available), py)
    if user_has_statusline():
        src_set.pop("statusLine", None)
    set_p = dst_root / (".claude/settings.json" if shared else ".claude/settings.local.json")
    if plugin:     # hooks → the plugin; env, status line and permissions → the factory session's settings file
        plugin_files(plan, dst_root, src_set, py, version_of(SRC))
        if migrating and set_p.exists():   # the old layout put the factory's entries into the project settings
            try:
                cur_raw = json.loads(set_p.read_text(encoding="utf-8"))
            except ValueError:
                cur_raw = None
            if isinstance(cur_raw, dict):
                factory = (manifest or {}).get("settings") or src_set
                cleaned = strip_factory_settings(cur_raw, factory, src_set,
                                                 set((manifest or {}).get("skill_overrides") or {}))
                if cleaned != cur_raw:
                    plan.write(set_p, json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n",
                               f"{set_p.relative_to(dst_root)} (factory entries moved to .tf/plugin/)")
    else:      # (back from the plugin layout: the factory's entries return to the project settings, yours stay)
        cur_raw = json.loads(set_p.read_text(encoding="utf-8")) if set_p.exists() else {}
        cur = load_migrations().settings_v19(cur_raw)   # 19.0.0: English hook event names, before the merge (no duplicate)
        merged = apply_python(merge_settings(src_set, cur), py) if cur else src_set
        iso = isolation_module()
        level = iso_level or iso.configured(dst_root)[0]
        if not shared:   # the isolation level's sandbox — per person (settings.local.json), never the shared settings
            merged = iso.with_level(merged, level, force=bool(iso_level))
        if merged != cur_raw:
            plan.write(set_p, json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
                       f"{set_p.relative_to(dst_root)} (factory permissions and hooks)")
        local_p = dst_root / ".claude" / "settings.local.json"
        if shared:       # team mode: the shared settings.json stays without a sandbox, each person's local file gets it
            try:
                local_cur = json.loads(local_p.read_text(encoding="utf-8")) if local_p.exists() else {}
            except ValueError:
                local_cur = None
            if isinstance(local_cur, dict):
                local_new = iso.with_level(local_cur, level, force=bool(iso_level))
                if local_new != local_cur:
                    plan.write(local_p, json.dumps(local_new, ensure_ascii=False, indent=2) + "\n",
                               ".claude/settings.local.json (isolation level: sandbox)")

    # rules: private → CLAUDE.local.md, team → CLAUDE.md; a section between markers, replaced on update
    md_p = dst_root / ("CLAUDE.md" if shared else "CLAUDE.local.md")
    md_old = md_p.read_text(encoding="utf-8") if md_p.exists() else ""
    md_base = load_migrations().claude_md_v19(drop_legacy_blocks(md_old, LEGACY_MARKS))   # 19.0.0: Polish subsections
    rules_p = dst_root / PLUGIN / "RULES.md"
    if (plugin and rules_p.is_file()) or (returning and rules_p.is_file() and MARK_BEGIN not in md_base):
        # the commands entered by tf onboard or a human live in RULES.md in the plugin layout (and come back from it)
        section = keep_commands(claude_md_section(py, dst_root, cfg),
                                f"{MARK_BEGIN}\n{rules_p.read_text(encoding='utf-8')}{MARK_END}\n")
    else:                                  # (on the move to the plugin layout: from the old block in CLAUDE.md)
        section = keep_commands(claude_md_section(py, dst_root, cfg), md_base)
    if plugin:     # the rules reach a factory session through the plugin's SessionStart hook (factory_rules.py)
        body = section.replace(MARK_BEGIN + "\n", "").replace(MARK_END + "\n", "")
        plan.copy(None, PLUGIN + "/RULES.md", body.encode("utf-8"))
        for old_md in (dst_root / "CLAUDE.md", dst_root / "CLAUDE.local.md"):   # the old layout's block of rules
            text = old_md.read_text(encoding="utf-8") if old_md.exists() else ""
            if MARK_BEGIN in text and MARK_END in text:
                plan.write(old_md, drop_rules_block(text), f"{old_md.name} (factory section moved to .tf/plugin/RULES.md)")
    else:
        plan.write(md_p, with_block(md_base, MARK_BEGIN, MARK_END, section, update or md_base != md_old),
                   f"{md_p.name} (factory section)")

    # after every copy: files of the previous version that this one no longer has (in the plugin layout the plugin's
    # own files are written above, so an earlier call took them for obsolete)
    if update:
        plan.remove_obsolete()
    if migrating and (dst_root / ".claude" / "agents" / "_generated").is_dir() and not dry:   # rebuilt in .tf/plugin/agents
        target = dst_root / BACKUP_DIR / stamp / ".claude" / "agents" / "_generated"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst_root / ".claude" / "agents" / "_generated"), target)
    plugin_left: list[str] = []
    unregistered = ""
    if returning:  # the plugin is not loaded any more: its factory files go to the backup, your skills to .claude/skills
        if not dry:    # first its registration for this folder (local scope), so the classic layout does not load twice
            unregistered = register_module().unregister(dst_root)[1]
        plugin_left = leave_plugin(plan, dst_root, own_plugin_skills, dry)

    # ignore entries: private → .git/info/exclude (nothing visible in the repo), team or --gitignore → .gitignore
    exclude = None if (shared or force_gitignore) else git_exclude_path(dst_root)
    ign = exclude or dst_root / ".gitignore"
    ign_label = ".git/info/exclude" if exclude else ".gitignore"
    ign_old = drop_legacy_blocks(ign.read_text(encoding="utf-8") if ign.exists() else "", LEGACY_GI)
    outside = ign_old.split(GI_BEGIN)[0] + (ign_old.split(GI_END, 1)[1] if GI_END in ign_old else "")
    have = set(outside.splitlines())
    temp = [ln for ln in (CORE / "gitignore").read_text(encoding="utf-8").splitlines() if ln]
    extra = [MANIFEST, BACKUP_DIR + "/", "*.factory-new", ".claude/factory-settings.json", ".tf/config/me.yaml"] if shared \
        else ignored_paths(plan.files)
    lines = [ln for ln in dict.fromkeys(temp + extra) if ln not in have]
    if lines:
        plan.write(ign, with_block(ign_old, GI_BEGIN, GI_END, "\n".join([GI_BEGIN, *lines, GI_END]) + "\n", True),
                   f"{ign_label} ({len(lines)} factory entries)")
    gi = dst_root / ".gitignore"
    if exclude and gi.exists() and GI_BEGIN in gi.read_text(encoding="utf-8"):   # after an older installer version
        plan.write(gi, drop_block(gi.read_text(encoding="utf-8")), ".gitignore (factory block removed — now in .git/info/exclude)")
    if not shared and not exclude and not force_gitignore:
        print("ℹ This is not a git repository — entries go to .gitignore. After `git init` run the update again.")

    # manifest and project settings
    old_version = (manifest or {}).get("version") or ("unknown" if update else None)
    new_version = version_of(SRC)
    if not dry:
        man_p.parent.mkdir(parents=True, exist_ok=True)
        new_manifest = {
            "version": new_version,
            # update source: --source, the previous one (not from the migrated factory) or the directory of this factory
            "source": opts.get("source") or ((manifest or {}).get("source") if legacy is None else None) or str(SRC),
            "mode": mode,
            "layout": layout,
            "python": py,
            "ignore": "gitignore" if force_gitignore else "exclude",
            "packs": {pid: str(available[pid].get("version", "0.0.0")) for pid in packs},
            **({"pack_dirs": pack_dirs} if pack_dirs else {}),     # pack sources from outside the factory (--pack-dir)
            **({"pack_sources": {pid: available[pid]["_external"] for pid in packs if available[pid].get("_external")}}
               if any(available[pid].get("_external") for pid in packs) else {}),
            "offered": sorted(set(available) | (offered or set())),   # new defaults arrive only once
            "installed_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "files": dict(sorted(plan.files.items())),
            "skill_overrides": (manifest or {}).get("skill_overrides") or {},   # the factory's entries in skillOverrides
            "settings": src_set,             # Claude Code settings entries added by the factory (tf uninstall removes them)
            **({"skill_describe": manifest["skill_describe"]} if (manifest or {}).get("skill_describe") else {}),
            **({"auto_update": manifest["auto_update"]} if "auto_update" in (manifest or {}) else {}),   # update.py --auto
        }
        save_manifest(dst_root, new_manifest, shared)
        pm.drop_settings(dst_root, "language", "commit_language")   # 12.0.0: language is no longer a setting

    # report
    mode_txt = "team (committed)" if shared else "private (outside git)"
    head = "Preview (nothing written)" if dry else ("Updated" if update else "Installed")
    ver = f"{old_version} → {new_version}" if update else new_version
    print(f"{head} in {dst_root} — version {ver}, {mode_txt} mode: new files {len(plan.created)}, "
          f"updated {len(plan.updated)}, merged {len(plan.merged)}, removed {len(plan.removed)}")
    print(f"  packs: {', '.join(packs) or '— (core only)'}")
    if returning and not dry:
        print(CLASSIC_OK)
        print(f"  ✓ plugin registration: {unregistered}")
        for rel in plugin_left:
            print(f"  ℹ left in place (yours): {rel} — the classic layout does not load .tf/plugin/; "
                  "move it to .claude/ if you still need it")
    for m in plan.merged:
        print(f"  ~ {m}")
    if not dry and update:     # self-correction of the project's own files after renames in the core (.tf/factory/migrations.py)
        mig = load_migrations()
        for c in mig.apply(dst_root, dry=False):
            print(f"  ✓ migrated: {c}")
        for c in mig.migrate_values(dst_root, dry=False) if hasattr(mig, "migrate_values") else []:
            print(f"  ✓ migrated values: {c}")
    if not dry:
        msg = rebuild(dst_root, dry)
        if msg:
            print(msg)
        # .tf/ — one place for the factory's work results (reports, registry, logs, runs, copies), like `tf init`
        ensure_config(dst_root)
        if iso_level:
            isolation_module().write_level(dst_root, iso_level)
            print(f"  ✓ isolation: {iso_level} → .tf/config/config.yaml")
        if (dst_root / ".tf" / "factory" / "analyze.py").is_file():
            subprocess.run([sys.executable, ".tf/factory/analyze.py", "init"], cwd=dst_root, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=120)
        # build.py processes files (e.g. the table of contents in references/) — the manifest and lock remember what is on disk,
        # otherwise the next update would take an untouched file for one changed by you (*.factory-new)
        written = [r for r in plan.created + plan.updated if r in new_manifest["files"] and (dst_root / r).is_file()]
        rehashed = {r: sha((dst_root / r).read_bytes()) for r in written}
        if any(new_manifest["files"][r] != h for r, h in rehashed.items()):
            new_manifest["files"] = dict(sorted({**new_manifest["files"], **rehashed}.items()))
            save_manifest(dst_root, new_manifest, shared)
    # visibility of skill descriptions: those the project uses get a description, the rest just the name (.tf/factory/skill_profile.py)
    if dry:
        print("ℹ Skill visibility will be matched to the project after the install (.tf/factory/skill_profile.py).")
    else:
        spec = importlib.util.spec_from_file_location("tf_skill_profile", dst_root / ".tf" / "factory" / "skill_profile.py")
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
    new_personas = sorted({Path(r).stem for r in plan.created if r.startswith(".tf/factory/packs/") and "/personas/" in r})
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

    listing("ℹ Factory files changed in the project — overwritten with the factory version", plan.overwritten,
            "Factory files in a project are like node_modules: change them in the factory repository, then update.")
    listing(f"ℹ Older install without a manifest — changed files overwritten, copies in {BACKUP_DIR}/{stamp}/",
            plan.backed_up, "If any of them held your change, carry it over from the copy.")
    listing("ℹ Removed from the factory, but changed by you — left in place", plan.kept_removed,
            "Delete them by hand if you no longer need them.")
    listing("ℹ Missing factory files the factory needs to run — restored", plan.restored,
            "They were missing from .tf/factory/, .claude/hooks/ or a skill's scripts/ (deleted, blocked by antivirus or a "
            "broken copy).")
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
            print("  git rm -r --cached " + " ".join(sorted({p.split("/")[0] if p.startswith(".tf/factory/") else
                                                             "/".join(p.split("/")[:3]) for p in already})[:12]))
        if not (dst_root / "CLAUDE.md").exists() and (dst_root / "AGENTS.md").exists():
            print("⚠ The project uses AGENTS.md: CLAUDE.local.md alone makes Claude stop reading it. Add the line "
                  "`@AGENTS.md` at the top of CLAUDE.local.md.")
    if not dry and not update:
        md = "CLAUDE.md" if shared else "CLAUDE.local.md"
        start = dispatcher_hints(packs, available, pm)
        print(f"""
Next:
  1. Prepare the repository: `tf onboard --yes` detects the test/lint/build commands, writes them to {md}
     and turns the quality gate on.
  2. Run `claude` once in the project directory and accept folder trust (hooks and permissions need it).
  3. Start: {' or '.join(start) or 'a persona from .claude/catalog.md'}, e.g. `claude --agent <name>`.
  4. Costs: the `balanced` profile works right away; `{py} .tf/factory/profile.py economy|quality` switches the team.
  Packs: `tf add <pack>` / `tf remove <pack>` · language: none to set — write in yours, the agents answer in it.
  Updates: `{py} .tf/factory/update.py` (or `tf`, or `/core-factory-update` in Claude Code).""")
    if plugin and not dry:     # last, after every file is written: register the plugin for this folder (local scope)
        print("\n" + register_module().report(dst_root))   # ✓, or the framed warning with the two commands
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
