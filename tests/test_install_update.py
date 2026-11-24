#!/usr/bin/env python3
"""Installer update tests: the manifest stores the file hash after `.tf/factory/build.py` (the table of contents of reference files),
so an update of a clean install leaves no `*.factory-new`; factory files changed in the project are
overwritten by the update (like node_modules), while `.tf/config/` (configuration overrides, own personas) is left alone; a clone of a team install (manifest outside git)
updates from the committed `.claude/factory-lock.json` and does not skip factory files; the tables of contents in the factory
source are up to date. python3 tests/test_install_update.py"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import os
os.environ["TF_NO_PLUGIN_REGISTER"] = "1"   # installs here never call the real Claude Code CLI (plugin_register.py)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
LOCK = ".claude/factory-lock.json"
MANIFEST = ".claude/factory-manifest.json"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def long_reference(toc: str | None) -> str:
    """A reference file > 100 lines with 3 sections — build.py adds a table of contents to it."""
    body = ["# Długi", ""] + ([toc, ""] if toc else [])
    for h in ("Pierwsza", "Druga", "Trzecia"):
        body += [f"## {h}", ""] + [f"Linia {i} sekcji {h}." for i in range(40)] + [""]
    return "\n".join(body) + "\n"


def install(src: Path, proj: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(src / "core" / "factory" / "install.py"), str(proj), "--yes", "--layout", "default", *args],
                          capture_output=True, text=True, timeout=300)


def factory_new(proj: Path) -> list[str]:
    return sorted(p.relative_to(proj).as_posix() for p in proj.rglob("*.factory-new"))


def stale_tocs(root: Path) -> list[str]:
    """Reference-skill files in the factory source whose table of contents build.py would change."""
    spec = importlib.util.spec_from_file_location("tf_build", root / "core" / "factory" / "build.py")
    sys.path.insert(0, str(root / "core" / "factory"))
    try:
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
    finally:
        sys.path.pop(0)
    refs = [p for base in (root / "core" / "skills", *sorted((root / "packs").glob("*/skills")),
                           *sorted((root / "modes").glob("*/skills")))
            for p in sorted(base.glob("*/references/**/*.md"))]
    return [p.relative_to(root).as_posix() for p in refs
            if build.with_toc(p.read_text(encoding="utf-8")) != p.read_text(encoding="utf-8")]


def toc_of(root: Path, text: str) -> str:
    spec = importlib.util.spec_from_file_location("tf_build_toc", root / "core" / "factory" / "build.py")
    sys.path.insert(0, str(root / "core" / "factory"))
    try:
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
    finally:
        sys.path.pop(0)
    return build.with_toc(text)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # T-1: the factory source has up-to-date tables of contents (otherwise every project gets a file that build.py rewrites)
    stale = stale_tocs(ROOT)
    check(not stale, f"T-1: stale table of contents in the source ({len(stale)}): {stale[:5]}")
    # T-1b: the table of contents in the file's language — an English file gets “Contents”, a Polish one keeps “Spis treści”
    en = long_reference(None).replace("# Długi", "# Long").replace("Linia", "Line").replace("sekcji", "of section")
    en = en.replace("Pierwsza", "First").replace("Druga", "Second").replace("Trzecia", "Third")
    pl = long_reference(None).replace("Linia", "Zażółć gęślą jaźń, linia")
    out_en, out_pl = toc_of(ROOT, en), toc_of(ROOT, pl)
    check("> **Contents:** First · Second · Third" in out_en and "Spis treści" not in out_en,
          f"T-1b: an English reference file gets “Contents”: {out_en[:120]!r}")
    check("> **Spis treści:** Pierwsza · Druga · Trzecia" in out_pl, f"T-1b: a Polish one keeps “Spis treści”: {out_pl[:120]!r}")
    check(toc_of(ROOT, out_pl.replace("Spis treści", "Contents")) == out_pl,
          "T-1b: the marker swapped for the language's own (the old marker recognized and removed)")

    with tempfile.TemporaryDirectory() as t:
        src = Path(t) / "src"
        shutil.copytree(ROOT / "core", src / "core", ignore=shutil.ignore_patterns("__pycache__"))
        major = int((src / "core" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0])
        pack = src / "packs" / "pack-a"
        write(pack / "pack.yaml", f"id: pack-a\nversion: 1.0.0\ntitle: A\ndescription: A test.\n"
                                  f"requires: {{core: \">={major}.0.0 <{major + 1}.0.0\"}}\n"
                                  "facets:\n  - {prefix: aa-, order: 900, name: a, question: \"a\"}\n")
        write(pack / "skills" / "aa-run" / "SKILL.md",
              "---\nname: aa-run\ndescription: Użyj przy A.\nmetadata:\n  catalog: \"Użyj przy A. Nie do niczego.\"\n"
              "  review: 2099-01-01\n---\n# aa-run\nTreść 1.\n")
        write(pack / "skills" / "ab-tool" / "SKILL.md",
              "---\nname: ab-tool\ndescription: Użyj przy B.\nmetadata:\n  catalog: \"Użyj przy B. Nie do niczego.\"\n"
              "  review: 2099-01-01\n---\n# ab-tool\nTreść 2.\n")
        write(pack / "skills" / "ab-tool" / "scripts" / "tool.py", "print('b')\n")
        ref = pack / "skills" / "aa-run" / "references" / "dlugi.md"
        write(ref, long_reference("> **Spis treści:** Pierwsza · Druga"))   # stale table of contents (missing “Trzecia”)

        # U-1..U-3: a clean install, then an update with the same version — no *.factory-new
        proj = Path(t) / "proj"
        proj.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=proj, check=True)
        r = install(src, proj, "--shared", "--packs", "pack-a")
        check(r.returncode == 0, f"U-1: install: {r.stdout[-600:]} {r.stderr[-300:]}")
        check((proj / ".tf" / "reports" / "README.md").is_file() and (proj / ".tf" / "logs").is_dir(),
              "U-1a: the install creates .tf/ (like tf init)")
        installed = proj / ".claude" / "skills" / "aa-run" / "references" / "dlugi.md"
        text = installed.read_text(encoding="utf-8") if installed.exists() else ""
        man = json.loads((proj / MANIFEST).read_text(encoding="utf-8")) if (proj / MANIFEST).exists() else {}
        import hashlib
        rel = ".claude/skills/aa-run/references/dlugi.md"
        check("Trzecia" in text.splitlines()[2] if len(text.splitlines()) > 2 else False,
              f"U-2: build.py fixed the table of contents in the project: {text.splitlines()[:3]}")
        check(man.get("files", {}).get(rel) == hashlib.sha256(text.encode("utf-8")).hexdigest(),
              "U-3: the manifest has the file hash after build.py (the one on disk)")
        r = install(src, proj)
        check(r.returncode == 0 and not factory_new(proj) and "You changed these factory files" not in r.stdout,
              f"U-4: an update of a clean install without *.factory-new: {factory_new(proj)} {r.stdout[-500:]}")
        # U-5 (19.0.0): a factory block from before 14.x — the project's commands under „### Komendy” survive the update
        import re
        md = proj / "CLAUDE.md"
        old = re.sub(r"### Commands\n.*?(?=\n### )", "### Komendy\n- Test: `make proj-test`\n", md.read_text(encoding="utf-8"),
                     count=1, flags=re.S)
        md.write_text(old, encoding="utf-8")
        r = install(src, proj)
        new = md.read_text(encoding="utf-8")
        check("### Komendy" in old and "### Commands\n- Test: `make proj-test`" in new and "Komendy" not in new,
              f"U-5: the Polish commands subsection migrated before the block is rewritten: {new[:800]}")
        # U-6: a required factory file missing before an update (deleted, antivirus, broken copy) is restored, and the
        # update does not crash on it; a deleted skill stays deleted (the project's choice)
        skill_md = proj / ".claude/skills/aa-run/SKILL.md"
        skill_bytes = skill_md.read_bytes()
        for rel_ in (".tf/factory/build.py", ".tf/factory/skill_profile.py", ".claude/skills/aa-run/SKILL.md"):
            (proj / rel_).unlink()
        r = install(src, proj)
        check(r.returncode == 0 and (proj / ".tf/factory/build.py").is_file()
              and (proj / ".tf/factory/skill_profile.py").is_file() and "restored" in r.stdout,
              f"U-6: missing .tf/factory files restored by the update: {r.returncode} {r.stdout[-500:]} {r.stderr[-500:]}")
        check(not (proj / ".claude/skills/aa-run/SKILL.md").exists() and "not restoring" in r.stdout,
              f"U-6: a deleted skill stays deleted: {r.stdout[-300:]}")
        skill_md.write_bytes(skill_bytes)   # the rest of the scenario uses the skill
        # U-6b: a missing script of a skill that stays (its SKILL.md is there) is restored — other factory scripts import
        # it (run_state.py imports ui_snap.py, and `tf status --open` broke without it); a skill deleted as a whole
        # (SKILL.md too) stays deleted with its scripts
        snap = proj / ".claude/skills/tf/scripts/ui_snap.py"
        snap.unlink()
        tool = proj / ".claude/skills/ab-tool"
        for p in (tool / "scripts" / "tool.py", tool / "SKILL.md"):
            p.unlink()
        r = install(src, proj)
        check(r.returncode == 0 and snap.is_file() and ".claude/skills/tf/scripts/ui_snap.py" in r.stdout
              and "restored" in r.stdout,
              f"U-6b: a missing skill script restored by the update: {r.returncode} {r.stdout[-600:]}")
        check(not (tool / "scripts" / "tool.py").exists() and not (tool / "SKILL.md").exists(),
              f"U-6b: the scripts of a skill deleted as a whole stay deleted: {r.stdout[-300:]}")
        # U-6 (19.0.0): settings with the Polish snapshot hook arguments — after the update exactly one snapshot hook per event,
        # with the English argument (the old argument would otherwise not match and the hook would be added a second time)
        def snapshot_args(settings: Path) -> dict:
            data = json.loads(settings.read_text(encoding="utf-8"))
            return {ev: [h["args"][-1] for e in data.get("hooks", {}).get(ev, []) for h in e.get("hooks", [])
                         if any(str(a).endswith("project_record.py") for a in h.get("args") or [])
                         and "--hook-snapshot" in h.get("args")] for ev in ("SessionEnd", "PreCompact")}

        def polish(settings: Path) -> None:
            text = settings.read_text(encoding="utf-8")
            settings.write_text(text.replace('"session end"', '"koniec sesji"').replace('"context compaction"',
                                                                                       '"kompaktowanie kontekstu"'), encoding="utf-8")
        shared_set = proj / ".claude" / "settings.json"
        polish(shared_set)
        old_args = snapshot_args(shared_set)
        r = install(src, proj)
        check(old_args == {"SessionEnd": ["koniec sesji"], "PreCompact": ["kompaktowanie kontekstu"]}
              and snapshot_args(shared_set) == {"SessionEnd": ["session end"], "PreCompact": ["context compaction"]},
              f"U-6: one snapshot hook per event with the English argument after the update: {old_args} → {snapshot_args(shared_set)}")

        # L-1..L-3: a team install has a committed lock (without local data), a private one does not
        lock = json.loads((proj / LOCK).read_text(encoding="utf-8")) if (proj / LOCK).exists() else {}
        gi = (proj / ".gitignore").read_text(encoding="utf-8") if (proj / ".gitignore").exists() else ""
        check(lock.get("packs") == ["pack-a"] and lock.get("files", {}).get(rel) == man.get("files", {}).get(rel)
              and lock.get("version") and not {"source", "python", "installed_at"} & set(lock),
              f"L-1: the lock in team mode — version, overlays, hashes, no local data: {sorted(lock)}")
        check(LOCK not in gi.splitlines() and MANIFEST in gi.splitlines(), "L-2: the lock is not ignored, the manifest is")
        priv = Path(t) / "priv"
        priv.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=priv, check=True)
        install(src, priv, "--packs", "pack-a")
        check(not (priv / LOCK).exists(), "L-3: a private install does not write a lock")
        local_set = priv / ".claude" / "settings.local.json"
        polish(local_set)
        install(src, priv)
        check(snapshot_args(local_set) == {"SessionEnd": ["session end"], "PreCompact": ["context compaction"]},
              f"U-7: the same in a private install (settings.local.json): {snapshot_args(local_set)}")

        # C-1..C-4: a clone of a team install (without the manifest and ignored files), a new source version
        clone = Path(t) / "clone"
        subprocess.run(["git", "add", "-A"], cwd=proj, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i"], cwd=proj, check=True)
        subprocess.run(["git", "clone", "-q", str(proj), str(clone)], check=True)
        check(not (clone / MANIFEST).exists() and (clone / LOCK).exists(), "C-1: the clone has the lock, no manifest")
        write(pack / "skills" / "aa-run" / "SKILL.md",
              (pack / "skills" / "aa-run" / "SKILL.md").read_text(encoding="utf-8").replace("Treść 1.", "Treść 2."))
        write(src / "core" / "factory" / "VERSION", f"{major}.99.0\n")
        own = clone / ".claude" / "skills" / "aa-run" / "references" / "dlugi.md"
        own.write_text(own.read_text(encoding="utf-8") + "Moja notatka.\n", encoding="utf-8")   # a team change
        r = install(src, clone)
        skill = (clone / ".claude" / "skills" / "aa-run" / "SKILL.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and "Treść 2." in skill and "Skipped existing" not in r.stdout,
              f"C-2: updating the clone overwrites an unchanged factory file, skips nothing: {r.stdout[-700:]}")
        check("packs: pack-a" in r.stdout and f"→ {major}.99.0" in r.stdout,
              f"C-3: overlays and version from the lock: {r.stdout[-400:]}")
        check("Moja notatka." not in own.read_text(encoding="utf-8") and not factory_new(clone)
              and "dlugi.md" in r.stdout,
              f"C-4: a factory file changed in the project overwritten (like node_modules), no *.factory-new, listed "
              f"in the output: {factory_new(clone)} {r.stdout[-600:]}")
        lock2 = json.loads((clone / LOCK).read_text(encoding="utf-8")) if (clone / LOCK).exists() else {}
        check(lock2.get("version") == f"{major}.99.0", f"C-5: lock updated: {lock2.get('version')}")

        # N-1..N-4: the engine (including the default config.yaml) is overwritten; project overrides and own personas in .tf/config/
        # untouched, and new default keys work without patching the project file
        cfg_src = src / "core" / "factory" / "config.yaml"
        write(cfg_src, cfg_src.read_text(encoding="utf-8") + "\n# a new factory key\nnowy_klucz_testu:\n  a: 1\n")
        write(src / "core" / "factory" / "VERSION", f"{major}.99.1\n")
        own = clone / ".tf" / "config" / "config.yaml"
        own.parent.mkdir(parents=True, exist_ok=True)
        own.write_text("default_profile: economy\n", encoding="utf-8")
        mine = clone / ".tf" / "config" / "personas" / "moja-persona.yaml"
        write(mine, "name: moja\n")
        r = install(src, clone)
        engine = (clone / ".tf" / "factory" / "config.yaml").read_text(encoding="utf-8") \
            if (clone / ".tf" / "factory" / "config.yaml").exists() else ""
        check(r.returncode == 0 and "nowy_klucz_testu:" in engine and own.read_text(encoding="utf-8") ==
              "default_profile: economy\n", f"N-1: the engine's default config updated, project overrides "
              f"unchanged: {r.stdout[-500:]}")
        spec = importlib.util.spec_from_file_location("tf_packs_n2", clone / ".tf" / "factory" / "packs.py")
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        merged = pm.load_config(clone)
        check(merged.get("default_profile") == "economy" and (merged.get("nowy_klucz_testu") or {}).get("a") == 1,
              f"N-2: the composed configuration — a project override and a new engine key: {merged.get('default_profile')}")
        check(mine.read_text(encoding="utf-8") == "name: moja\n", "N-3: an own persona in .tf/config/personas/ untouched")
        check(not factory_new(clone) and not (clone / "factory").exists(), f"N-4: no *.factory-new or factory/: "
              f"{factory_new(clone)}")

    # a mode retired from the factory (mode-talos: the loop is in the core as /tf) — updating a project that had it
    # skips it with a message instead of ending with an "Unknown packs" error, and its files go to the backup
    with tempfile.TemporaryDirectory() as t:
        proj = Path(t) / "app"
        proj.mkdir()
        r = install(ROOT, proj, "--packs", "none")
        check(r.returncode == 0, f"W-0: install: {r.stdout[-400:]} {r.stderr[-300:]}")
        man = json.loads((proj / MANIFEST).read_text(encoding="utf-8"))
        man["packs"]["mode-talos"] = "1.3.0"
        if "offered" in man:
            man["offered"] = sorted({*man["offered"], "mode-talos"})
        old = proj / ".claude" / "skills" / "talos-story-run" / "SKILL.md"
        write(old, "---\nname: talos-story-run\n---\n# stary skill\n")
        spec = importlib.util.spec_from_file_location("tf_install_w", ROOT / "core" / "factory" / "install.py")
        inst = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inst)
        man["files"][".claude/skills/talos-story-run/SKILL.md"] = inst.sha(old.read_bytes())
        (proj / MANIFEST).write_text(json.dumps(man), encoding="utf-8")
        r = install(ROOT, proj, "--update")
        after = json.loads((proj / MANIFEST).read_text(encoding="utf-8"))
        check(r.returncode == 0 and "mode-talos" in r.stdout and "/tf" in r.stdout and "Unknown packs" not in r.stdout,
              f"W-1: an update with a retired mode passes and says what replaced it: {r.returncode} {r.stdout[-500:]}")
        check("mode-talos" not in (after.get("packs") or {}) and not old.exists()
              and (proj / ".claude" / "skills" / "tf" / "SKILL.md").is_file(),
              f"W-2: the retired mode disappears from the manifest, its file from the project, and the loop is in the core: {list(after.get('packs') or {})}")
        r = install(ROOT, proj, "--add", "mode-talos")
        check(r.returncode == 2 and "mode-talos" in r.stdout and "/tf" in r.stdout,
              f"W-3: an explicit request for a retired mode → refusal with an explanation: {r.returncode} {r.stdout[-300:]}")

        # pack-ev retired: the EV knowledge lives in the EV Intelligence project (ev-* skills, an MCP server), not in the factory
        man = json.loads((proj / MANIFEST).read_text(encoding="utf-8"))
        man["packs"]["pack-ev"] = "1.1.0"
        man["offered"] = sorted({*(man.get("offered") or []), "pack-ev"})
        ev = proj / ".claude" / "skills" / "dom-ev-glossary" / "SKILL.md"
        write(ev, "---\nname: dom-ev-glossary\n---\n# słownik\n")
        man["files"][".claude/skills/dom-ev-glossary/SKILL.md"] = inst.sha(ev.read_bytes())
        (proj / MANIFEST).write_text(json.dumps(man), encoding="utf-8")
        r = install(ROOT, proj, "--update")
        after = json.loads((proj / MANIFEST).read_text(encoding="utf-8"))
        check(r.returncode == 0 and "pack-ev" in r.stdout and "ev-intelligence" in r.stdout and "Unknown packs" not in r.stdout
              and "pack-ev" not in (after.get("packs") or {}) and not ev.exists(),
              f"W-4: an update with pack-ev passes, points to ev-intelligence, files to the backup: {r.returncode} {r.stdout[-500:]}")
        r = install(ROOT, proj, "--add", "pack-ev")
        check(r.returncode == 2 and "ev-intelligence" in r.stdout, f"W-5: --add pack-ev → refusal with an address: {r.stdout[-300:]}")

        # a hook retired from the factory (isolation_notice, SessionStart): the update moves its unchanged file to the
        # backup and drops its registration from the project's settings, the other hooks of the event stay
        man = json.loads((proj / MANIFEST).read_text(encoding="utf-8"))
        hook = proj / ".claude" / "hooks" / "isolation_notice.py"
        write(hook, "print('old notice')\n")
        man["files"][".claude/hooks/isolation_notice.py"] = inst.sha(hook.read_bytes())
        (proj / MANIFEST).write_text(json.dumps(man), encoding="utf-8")
        local = proj / ".claude" / "settings.local.json"
        data = json.loads(local.read_text(encoding="utf-8"))
        start = data.setdefault("hooks", {}).setdefault("SessionStart", [])
        before = sum(len(g.get("hooks") or []) for g in start)
        start.append({"hooks": [{"type": "command", "command": "python3",
                                 "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/isolation_notice.py"], "timeout": 10}]})
        local.write_text(json.dumps(data, indent=2), encoding="utf-8")
        r = install(ROOT, proj, "--update")
        text = local.read_text(encoding="utf-8")
        after = json.loads(text).get("hooks", {}).get("SessionStart", [])
        backups = list((proj / ".tf" / "backup").rglob("isolation_notice.py"))
        check(r.returncode == 0 and not hook.exists() and backups and "isolation_notice" not in text
              and sum(len(g.get("hooks") or []) for g in after) == before,
              f"W-6: a retired hook — file to the backup, registration dropped, other SessionStart hooks kept: "
              f"{r.returncode} {hook.exists()} {backups} {r.stdout[-400:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} installer update tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
