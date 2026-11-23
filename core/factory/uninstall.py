#!/usr/bin/env python3
"""
Uninstalls the factory from a project (`tf uninstall`). No model, no network.

  python3 .tf/factory/uninstall.py --dry-run        # what would be removed and changed (changes nothing)
  python3 .tf/factory/uninstall.py --yes            # remove the factory files, keep yours
  python3 .tf/factory/uninstall.py --yes --force    # also remove your additions: own skills, the whole .tf/, agent memory

Removes: files from the install manifest (the `.tf/factory/` engine, skills, hooks, tests, factory workflows), generated files
(`_generated` agents, catalog, factory settings, update copies), the factory block in `CLAUDE.local.md`/`CLAUDE.md`
and in `.git/info/exclude`/`.gitignore`, factory entries in Claude Code settings (hooks, permissions, status line —
per the manifest; your entries stay), the permission mode set by the work style (the previous one is restored).
Keeps (without `--force`): own skills in `.claude/skills/`, `.tf/config/` (personas, roles, config.yaml), work results
in `.tf/` (reports, registry, logs), agent memory. Never touches `docs/project/` or the project code.

Before changing anything it saves a copy of everything it removes or changes: `~/.tf/backups/<project>-<date>.zip` (directory:
variable `TF_BACKUP_DIR`); to restore: `unzip -o <file> -d <project>`.
"""
from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (git) also write and read UTF-8

ROOT = Path.cwd()
MANIFEST = ".claude/factory-manifest.json"
LOCK = ".claude/factory-lock.json"
SETTINGS_REL = ".claude/factory-settings.json"
MARK_BEGIN, MARK_END = "<!-- team-factory:begin -->", "<!-- team-factory:end -->"
GI_BEGIN, GI_END = "# team-factory:begin (managed by factory/install.py)", "# team-factory:end"
LEGACY = [("<!-- claude-team-factory:begin -->", "<!-- claude-team-factory:end -->"),
          ("<!-- ev-team-factory:begin -->", "<!-- ev-team-factory:end -->")]
GENERATED_DIRS = [".tf/factory", ".claude/agents/_generated", ".claude/tests", ".tf/backup", ".claude/scratch",
                  ".tf/plugin", ".tf/.claude-plugin"]   # factory mode: the plugin and its directory marketplace
GENERATED_FILES = [".claude/catalog.md", ".claude/cleanroom.json", ".claude/JEV.md", MANIFEST, LOCK, SETTINGS_REL,
                   ".claude/factory-profile.json", ".claude/skill-gate.json"]
FORCE_DIRS = [".tf", ".claude/agent-memory", ".claude/agent-memory-local"]
FORCE_FILES = [".claude/quality-gate.json", ".claude/quality-gate.expected-red"]
NEVER = ("docs/project",)


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except (OSError, ValueError):
        return None


def strip_blocks(text: str, marks: list[tuple[str, str]]) -> str:
    for begin, end in marks:
        while begin in text and end in text.split(begin, 1)[1]:
            head, rest = text.split(begin, 1)
            text = head.rstrip("\n") + ("\n" if head.strip() else "") + rest.split(end, 1)[1].lstrip("\n")
    return text


def exclude_path(root: Path) -> Path | None:
    r = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"], capture_output=True, text=True)
    return (root / r.stdout.strip()).resolve() if r.returncode == 0 and r.stdout.strip() else None


def factory_hook(h: dict, fac_cmds: set[str], hook_files: set[str]) -> bool:
    """Factory hook: the same as in the manifest or points to a factory file (.claude/hooks/<file from the manifest>, .tf/factory/)."""
    text = " ".join([str(h.get("command", "")), *map(str, h.get("args") or [])])
    if text in fac_cmds or ".tf/factory/" in text:
        return True
    return any(f in text for f in hook_files)


def factory_sandbox() -> dict | None:
    """The sandbox the factory writes for the isolation level (templates/sandbox.settings.json); a changed one stays."""
    try:
        return json.loads((Path(__file__).resolve().parent / "templates" / "sandbox.settings.json")
                          .read_text(encoding="utf-8"))["sandbox"]
    except (OSError, ValueError, KeyError):
        return None


def clean_settings(cur: dict, fac: dict, overrides: dict, mark: dict | None, hook_files: set[str]) -> dict:
    out = json.loads(json.dumps(cur))
    perms = out.get("permissions") if isinstance(out.get("permissions"), dict) else {}
    fperms = fac.get("permissions") or {}
    for key in ("allow", "ask", "deny"):
        if isinstance(perms.get(key), list):
            perms[key] = [r for r in perms[key] if r not in (fperms.get(key) or [])]
            if not perms[key]:
                perms.pop(key)
    if mark and perms.get("defaultMode") == mark.get("mode"):        # styl pracy (tf style) oddaje poprzedni tryb
        if mark.get("previous") is None:
            perms.pop("defaultMode", None)
        else:
            perms["defaultMode"] = mark["previous"]
    if perms.get("defaultMode") == fperms.get("defaultMode", "default"):
        perms.pop("defaultMode", None)
    if perms:
        out["permissions"] = perms
    else:
        out.pop("permissions", None)
    for k, v in (fac.get("env") or {}).items():
        if (out.get("env") or {}).get(k) == v:
            out["env"].pop(k)
    if out.get("env") == {}:
        out.pop("env")
    if out.get("sandbox") is not None and out.get("sandbox") == factory_sandbox():   # the isolation level's sandbox
        out.pop("sandbox")
    fac_cmds = {" ".join([str(h.get("command", "")), *map(str, h.get("args") or [])])
                for es in (fac.get("hooks") or {}).values() for e in es for h in e.get("hooks", [])}
    hooks = out.get("hooks") if isinstance(out.get("hooks"), dict) else {}
    for event in list(hooks):
        entries = []
        for e in hooks[event] or []:
            keep = [h for h in e.get("hooks", []) if not factory_hook(h, fac_cmds, hook_files)]
            if keep:
                entries.append({**e, "hooks": keep})
        if entries:
            hooks[event] = entries
        else:
            hooks.pop(event)
    if hooks:
        out["hooks"] = hooks
    else:
        out.pop("hooks", None)
    so = out.get("skillOverrides") if isinstance(out.get("skillOverrides"), dict) else None
    if so is not None:
        for k, v in overrides.items():
            if so.get(k) == v:
                so.pop(k)
        if not so:
            out.pop("skillOverrides")
    status = out.get("statusLine")
    if isinstance(status, dict) and any(f in json.dumps(status) for f in hook_files | {".tf/factory/"}):
        out.pop("statusLine")
    for k, v in fac.items():
        if k not in ("permissions", "env", "hooks", "skillOverrides") and out.get(k) == v:
            out.pop(k)
    if set(out) <= {"$schema"}:
        return {}
    return out


def plan(root: Path, force: bool) -> dict:
    man = read_json(root / MANIFEST) or {}
    files = sorted(f for f in (man.get("files") or {}) if (root / f).is_file())
    delete: set[str] = set(files)
    for d in GENERATED_DIRS + (FORCE_DIRS if force else []):
        if (root / d).exists():
            delete |= {p.relative_to(root).as_posix() for p in (root / d).rglob("*") if p.is_file()}
    for f in GENERATED_FILES + (FORCE_FILES if force else []):
        if (root / f).is_file():
            delete.add(f)
    for p in root.rglob("*.factory-new"):
        if ".git" not in p.relative_to(root).parts:
            delete.add(p.relative_to(root).as_posix())
    own_skills = sorted(p.name for p in (root / ".claude" / "skills").iterdir()
                        if p.is_dir() and not any(f.startswith(f".claude/skills/{p.name}/") for f in man.get("files") or {})) \
        if (root / ".claude" / "skills").is_dir() else []
    if force:
        for s in own_skills:
            delete |= {p.relative_to(root).as_posix() for p in (root / ".claude/skills" / s).rglob("*") if p.is_file()}
    delete = {d for d in delete if not d.startswith(NEVER)}
    shared = man.get("mode") == "shared"
    edits: dict[str, str | None] = {}                            # path → new content (None: delete the file)
    for md in ("CLAUDE.local.md", "CLAUDE.md"):
        p = root / md
        if p.is_file():
            old = p.read_text(encoding="utf-8")
            new = strip_blocks(old, [(MARK_BEGIN, MARK_END), *LEGACY])
            if new != old:
                edits[md] = new if new.strip() else None
    ex = exclude_path(root)
    for p in [x for x in (ex, root / ".gitignore") if x]:
        if p.is_file():
            old = p.read_text(encoding="utf-8")
            new = strip_blocks(old, [(GI_BEGIN, GI_END)])
            if new != old:
                rel = p.relative_to(root).as_posix() if root in p.parents else str(p)
                edits[rel] = new if (new.strip() or rel.endswith("exclude")) else None
    marks = read_json(root / SETTINGS_REL) or {}
    hook_files = {f for f in man.get("files") or {} if f.startswith(".claude/hooks/")}
    for rel in (".claude/settings.local.json", ".claude/settings.json"):
        cur = read_json(root / rel)
        if not isinstance(cur, dict):
            continue
        new = clean_settings(cur, man.get("settings") or {}, man.get("skill_overrides") or {},
                             marks.get("style_permission_mode"), hook_files)
        if new != cur:
            edits[rel] = (json.dumps(new, ensure_ascii=False, indent=2) + "\n") if new else None
    warns = [] if man.get("settings") else ["the manifest has no record of the factory settings (installed before this version). "
                                            "I remove the factory hooks. Check the factory permissions (allow/deny) by hand"]
    return {"delete": sorted(delete - set(edits)), "edits": edits, "own_skills": own_skills, "shared": shared,
            "warns": warns}


def backup(root: Path, p: dict) -> Path:
    base = Path(os.environ.get("TF_BACKUP_DIR") or Path.home() / ".tf" / "backups")
    base.mkdir(parents=True, exist_ok=True)
    out = base / f"{root.name}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in [*p["delete"], *p["edits"]]:
            f = Path(rel) if Path(rel).is_absolute() else root / rel
            if f.is_file():
                z.write(f, rel)
    return out


def prune_empty(root: Path, dirs: list[str]) -> None:
    for d in sorted({str(Path(x).parent) for x in dirs}, key=lambda s: -s.count("/")):
        p = root / d
        while p != root and p.is_dir() and not any(p.iterdir()):
            p.rmdir()
            p = p.parent


def main(argv: list[str]) -> int:
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    root = ROOT
    if not (root / MANIFEST).is_file():
        print("✗ No factory in this directory (no .claude/factory-manifest.json). Run this in the project directory.")
        return 2
    force, yes, dry = "--force" in argv, "--yes" in argv, "--dry-run" in argv
    p = plan(root, force)
    groups: dict[str, int] = {}
    for d in p["delete"]:
        key = next((g + "/" for g in GENERATED_DIRS + FORCE_DIRS + [".claude/skills", ".claude/hooks", ".claude/workflows"]
                    if d.startswith(g + "/")), d)
        groups[key] = groups.get(key, 0) + 1
    print(f"Uninstalling the factory from {root}{' (--force: also your additions)' if force else ''}")
    print(f"Files to delete: {len(p['delete'])}")
    for g, n in sorted(groups.items()):
        print(f"  - {g}" + (f" ({n} files)" if n > 1 else ""))
    if p["edits"]:
        print("Files to change (factory entries removed):")
        for rel, new in p["edits"].items():
            print(f"  - {rel}" + (" — empty after the change, will delete" if new is None else ""))
    keep = [*(f".claude/skills/{s}/" for s in p["own_skills"] if not force),
            *([".tf/ (config, reports, register, logs)", ".claude/agent-memory/"] if not force else []),
            "docs/project/", "project code"]
    print("Kept: " + ", ".join(keep))
    for w in p["warns"]:
        print(f"⚠ {w}")
    if dry:
        return 0
    if not yes:
        if not sys.stdin.isatty():
            print("Run again with --yes to uninstall (no terminal to confirm). Nothing changed.")
            return 1
        if input("Uninstall? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Stopped. Nothing changed.")
            return 1
    reg = Path(__file__).resolve().parent / "plugin_register.py"
    if reg.is_file():   # the plugin's registration for this folder (local scope) first; it edits settings.local.json
        import importlib.util
        spec = importlib.util.spec_from_file_location("tf_plugin_register_uninstall", reg)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ok, detail = mod.unregister(root)
        print(("✓ plugin registration: " if ok else "⚠ plugin registration: ") + detail)
        p = plan(root, force)
    zipped = backup(root, p)
    for rel, new in p["edits"].items():
        f = Path(rel) if Path(rel).is_absolute() else root / rel
        if new is None:
            f.unlink(missing_ok=True)
        else:
            f.write_text(new, encoding="utf-8")
    for rel in p["delete"]:
        (root / rel).unlink(missing_ok=True)
    for d in GENERATED_DIRS + (FORCE_DIRS if force else []):
        if (root / d).is_dir():
            shutil.rmtree(root / d, ignore_errors=True)
    prune_empty(root, p["delete"])
    print(f"✓ Factory uninstalled. Backup: {zipped}")
    print(f"  To restore: unzip -o {zipped} -d {root}")
    print("  The `tf` launcher in ~/.local/bin stays (remove it by hand if you do not use the factory in other projects).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
