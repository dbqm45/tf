#!/usr/bin/env python3
"""Tests of the modes (`modes/mode-*`) in the installer: detection next to overlays, installation of the default mode, new defaults
on update (the manifest `offered`), deliberately removed ones do not come back, `kind` ↔ directory and prefix validation.
python3 tests/test_modes.py

The installer works on a copy of the core in a temporary factory source with artificial overlays and modes."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def item(src: Path, folder: str, pid: str, prefix: str, default: bool, kind: str | None) -> None:
    major = int((src / "core" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0])
    base = src / folder / pid
    write(base / "pack.yaml", f"id: {pid}\nversion: 1.0.0\ntitle: {pid}\ndescription: {pid} test.\n"
                              + (f"kind: {kind}\n" if kind else "") + f"default: {str(default).lower()}\n"
                              f"requires: {{core: \">={major}.0.0 <{major + 1}.0.0\"}}\n"
                              f"facets:\n  - {{prefix: {prefix}, order: 900, name: {pid}, question: \"{pid}\"}}\n")
    name = prefix + "run"
    write(base / "skills" / name / "SKILL.md",
          f"---\nname: {name}\ndescription: Użyj przy {pid}.\nmetadata:\n  catalog: \"Użyj przy {pid}. Nie do niczego.\"\n"
          f"  review: 2099-01-01\n---\n# {name}\n")


def source(base: Path) -> Path:
    src = base / "src"
    shutil.copytree(ROOT / "core", src / "core", ignore=shutil.ignore_patterns("__pycache__"))
    item(src, "packs", "pack-a", "aa-", False, None)
    item(src, "packs", "pack-d", "dd-", True, None)
    item(src, "modes", "mode-x", "xx-", True, "mode")
    return src


def install(src: Path, proj: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(src / "core" / "factory" / "install.py"), str(proj), "--yes", "--layout", "default", *args],
                          capture_output=True, text=True, timeout=300)


def manifest(proj: Path) -> dict:
    p = proj / ".claude" / "factory-manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        src = source(base)

        # first install: the default overlays and modes; a mode lands like an overlay
        p = base / "nowy"
        p.mkdir()
        r = install(src, p)
        m = manifest(p)
        check(r.returncode == 0 and sorted(m.get("packs", {})) == ["mode-x", "pack-d"],
              f"M-1: the default mode from modes/ installed on the first install: {m.get('packs')} {r.stdout[-800:]}")
        check((p / ".tf" / "factory" / "packs" / "mode-x" / "pack.yaml").is_file()
              and (p / ".claude" / "skills" / "xx-run" / "SKILL.md").is_file(), "M-2: the mode's files in place")
        check(sorted(m.get("offered", [])) == ["mode-x", "pack-a", "pack-d"],
              f"M-3: the manifest records what was on offer: {m.get('offered')}")

        # updating an install from before the modes (a manifest without `offered`): new default modes arrive,
        # default overlays that the project may already have rejected do not
        old = base / "stary"
        old.mkdir()
        install(src, old, "--packs", "pack-a")
        mo = manifest(old)
        mo.pop("offered", None)
        (old / ".claude" / "factory-manifest.json").write_text(json.dumps(mo), encoding="utf-8")
        r = install(src, old)
        m = manifest(old)
        check(sorted(m.get("packs", {})) == ["mode-x", "pack-a"],
              f"M-4: an old manifest → the new default mode arrives, pack-d does not: {m.get('packs')} {r.stdout[-800:]}")
        check("mode-x" in r.stdout, f"M-5: a message about the new item: {r.stdout[-800:]}")

        # a deliberately removed mode does not come back on the next update
        install(src, old, "--remove", "mode-x")
        r = install(src, old)
        check(sorted(manifest(old).get("packs", {})) == ["pack-a"],
              f"M-6: a removed mode does not come back: {manifest(old).get('packs')} {r.stdout[-500:]}")

        # a new default mode in the next factory version reaches an existing install
        item(src, "modes", "mode-y", "yy-", True, "mode")
        r = install(src, old)
        check(sorted(manifest(old).get("packs", {})) == ["mode-y", "pack-a"],
              f"M-7: a new default mode arrives on update: {manifest(old).get('packs')} {r.stdout[-500:]}")

        # an explicit --packs on update wins over adding the defaults
        item(src, "modes", "mode-z", "zz-", True, "mode")
        install(src, old, "--packs", "pack-a")
        check(sorted(manifest(old).get("packs", {})) == ["pack-a"],
              f"M-8: --packs without adding the defaults: {manifest(old).get('packs')}")

        # validation: a mode without kind or with an overlay prefix, an overlay with kind: mode → an error, nothing written
        for folder, pid, kind, label in (("modes", "mode-bad", None, "a mode without kind: mode"),
                                         ("modes", "pack-zle", "mode", "a mode without the mode- prefix"),
                                         ("packs", "pack-tryb", "mode", "an overlay with kind: mode")):
            bad = base / f"src-{pid}"
            shutil.copytree(src, bad)
            item(bad, folder, pid, "qq-", False, kind)
            q = base / f"proj-{pid}"
            q.mkdir()
            r = install(bad, q)
            check(r.returncode == 2 and pid in r.stdout and not manifest(q),
                  f"M-9: {label} → code 2 with the item name: {r.returncode} {r.stdout[-400:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} mode tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
