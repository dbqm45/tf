#!/usr/bin/env python3
"""
Odinstalowanie fabryki z projektu (`tf uninstall`). Bez modelu i bez sieci.

  python3 .tf/factory/uninstall.py --dry-run        # co zostanie usunięte i zmienione (nic nie zmienia)
  python3 .tf/factory/uninstall.py --yes            # usuń pliki fabryki, zostaw Twoje
  python3 .tf/factory/uninstall.py --yes --force    # usuń też Twoje dodatki: własne skille, cały .tf/, pamięć agentów

Usuwa: pliki z manifestu instalacji (silnik `.tf/factory/`, skille, hooki, testy, workflowy fabryki), pliki generowane
(agenci `_generated`, katalog, ustawienia fabryki, kopie aktualizacji), blok fabryki w `CLAUDE.local.md`/`CLAUDE.md`
i w `.git/info/exclude`/`.gitignore`, wpisy fabryki w ustawieniach Claude Code (hooki, uprawnienia, pasek stanu —
według manifestu; Twoje wpisy zostają), tryb uprawnień ustawiony przez styl pracy (wraca poprzedni).
Zostawia (bez `--force`): własne skille w `.claude/skills/`, `.tf/config/` (persony, role, config.yaml), wyniki pracy
w `.tf/` (raporty, rejestr, logi), pamięć agentów. Nigdy nie rusza `docs/project/` ani kodu projektu.

Przed zmianą zapisuje kopię wszystkiego, co usuwa lub zmienia: `~/.tf/backups/<projekt>-<data>.zip` (katalog:
zmienna `TF_BACKUP_DIR`); przywrócenie: `unzip -o <plik> -d <projekt>`.
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

ROOT = Path.cwd()
MANIFEST = ".claude/factory-manifest.json"
LOCK = ".claude/factory-lock.json"
SETTINGS_REL = ".claude/factory-settings.json"
MARK_BEGIN, MARK_END = "<!-- team-factory:begin -->", "<!-- team-factory:end -->"
GI_BEGIN, GI_END = "# team-factory:begin (managed by factory/install.py)", "# team-factory:end"
LEGACY = [("<!-- claude-team-factory:begin -->", "<!-- claude-team-factory:end -->"),
          ("<!-- ev-team-factory:begin -->", "<!-- ev-team-factory:end -->")]
GENERATED_DIRS = [".tf/factory", ".claude/agents/_generated", ".claude/tests", ".tf/backup", ".claude/scratch"]
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
    """Hook fabryki: ten sam co w manifeście albo wskazuje plik fabryki (.claude/hooks/<plik z manifestu>, .tf/factory/)."""
    text = " ".join([str(h.get("command", "")), *map(str, h.get("args") or [])])
    if text in fac_cmds or ".tf/factory/" in text:
        return True
    return any(f in text for f in hook_files)


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
    edits: dict[str, str | None] = {}                            # ścieżka → nowa treść (None: usunąć plik)
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
    warns = [] if man.get("settings") else ["manifest bez zapisu ustawień fabryki (instalacja sprzed tej wersji) — "
                                            "usuwam hooki fabryki, a uprawnienia (allow/deny) fabryki sprawdź ręcznie"]
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
        print("✗ W tym katalogu nie ma fabryki (brak .claude/factory-manifest.json) — uruchom w katalogu projektu.")
        return 2
    force, yes, dry = "--force" in argv, "--yes" in argv, "--dry-run" in argv
    p = plan(root, force)
    groups: dict[str, int] = {}
    for d in p["delete"]:
        key = next((g + "/" for g in GENERATED_DIRS + FORCE_DIRS + [".claude/skills", ".claude/hooks", ".claude/workflows"]
                    if d.startswith(g + "/")), d)
        groups[key] = groups.get(key, 0) + 1
    print(f"Odinstalowanie fabryki z {root}{' (--force: także Twoje dodatki)' if force else ''}")
    print(f"Usunę {len(p['delete'])} plików:")
    for g, n in sorted(groups.items()):
        print(f"  - {g}" + (f" ({n} plików)" if n > 1 else ""))
    if p["edits"]:
        print("Zmienię (usunę wpisy fabryki):")
        for rel, new in p["edits"].items():
            print(f"  - {rel}" + (" — po zmianie pusty, usunę" if new is None else ""))
    keep = [*(f".claude/skills/{s}/" for s in p["own_skills"] if not force),
            *([".tf/ (config, raporty, rejestr, logi)", ".claude/agent-memory/"] if not force else []),
            "docs/project/", "kod projektu"]
    print("Zostawię: " + ", ".join(keep))
    for w in p["warns"]:
        print(f"⚠ {w}")
    if dry:
        return 0
    if not yes:
        if not sys.stdin.isatty():
            print("Uruchom ponownie z --yes, żeby odinstalować (nie ma terminala do potwierdzenia). Nic nie zmieniono.")
            return 1
        if input("Odinstalować? [t/N] ").strip().lower() not in ("t", "tak", "y", "yes"):
            print("Przerwane — nic nie zmieniono.")
            return 1
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
    print(f"✓ Fabryka odinstalowana. Kopia zapasowa: {zipped}")
    print(f"  Przywrócenie: unzip -o {zipped} -d {root}")
    print("  Launcher `tf` w ~/.local/bin zostaje (usuń go ręcznie, jeśli nie używasz fabryki w innych projektach).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
