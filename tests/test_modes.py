#!/usr/bin/env python3
"""Testy trybów (`modes/mode-*`) w instalatorze: wykrycie obok nakładek, instalacja domyślnego trybu, nowe domyślne
przy aktualizacji (manifest `offered`), świadomie usunięte nie wracają, walidacja `kind` ↔ katalog i prefiks.
python3 tests/test_modes.py

Instalator działa na kopii rdzenia w tymczasowym źródle fabryki ze sztucznymi nakładkami i trybami."""
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
          f"---\nname: {name}\ndescription: Użyj przy {pid}.\nmetadata:\n  katalog: \"Użyj przy {pid}. Nie do niczego.\"\n"
          f"  przeglad: 2099-01-01\n---\n# {name}\n")


def source(base: Path) -> Path:
    src = base / "src"
    shutil.copytree(ROOT / "core", src / "core", ignore=shutil.ignore_patterns("__pycache__"))
    item(src, "packs", "pack-a", "aa-", False, None)
    item(src, "packs", "pack-d", "dd-", True, None)
    item(src, "modes", "mode-x", "xx-", True, "mode")
    return src


def install(src: Path, proj: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(src / "core" / "factory" / "install.py"), str(proj), "--yes", *args],
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

        # pierwsza instalacja: domyślne nakładki i tryby; tryb ląduje jak nakładka
        p = base / "nowy"
        p.mkdir()
        r = install(src, p)
        m = manifest(p)
        check(r.returncode == 0 and sorted(m.get("packs", {})) == ["mode-x", "pack-d"],
              f"M-1: domyślny tryb z modes/ instalowany przy pierwszej instalacji: {m.get('packs')} {r.stdout[-800:]}")
        check((p / "factory" / "packs" / "mode-x" / "pack.yaml").is_file()
              and (p / ".claude" / "skills" / "xx-run" / "SKILL.md").is_file(), "M-2: pliki trybu na miejscu")
        check(sorted(m.get("offered", [])) == ["mode-x", "pack-a", "pack-d"],
              f"M-3: manifest zapisuje, co było w ofercie: {m.get('offered')}")

        # aktualizacja instalacji sprzed trybów (manifest bez `offered`): dochodzą nowe domyślne tryby,
        # nie dochodzą domyślne nakładki, które projekt już mógł odrzucić
        old = base / "stary"
        old.mkdir()
        install(src, old, "--packs", "pack-a")
        mo = manifest(old)
        mo.pop("offered", None)
        (old / ".claude" / "factory-manifest.json").write_text(json.dumps(mo), encoding="utf-8")
        r = install(src, old)
        m = manifest(old)
        check(sorted(m.get("packs", {})) == ["mode-x", "pack-a"],
              f"M-4: stary manifest → nowy domyślny tryb dochodzi, pack-d nie: {m.get('packs')} {r.stdout[-800:]}")
        check("mode-x" in r.stdout, f"M-5: komunikat o nowym elemencie: {r.stdout[-800:]}")

        # świadomie usunięty tryb nie wraca przy kolejnej aktualizacji
        install(src, old, "--remove", "mode-x")
        r = install(src, old)
        check(sorted(manifest(old).get("packs", {})) == ["pack-a"],
              f"M-6: usunięty tryb nie wraca: {manifest(old).get('packs')} {r.stdout[-500:]}")

        # nowy domyślny tryb w kolejnej wersji fabryki dochodzi do istniejącej instalacji
        item(src, "modes", "mode-y", "yy-", True, "mode")
        r = install(src, old)
        check(sorted(manifest(old).get("packs", {})) == ["mode-y", "pack-a"],
              f"M-7: nowy domyślny tryb dochodzi przy aktualizacji: {manifest(old).get('packs')} {r.stdout[-500:]}")

        # jawne --packs przy aktualizacji wygrywa z dodawaniem domyślnych
        item(src, "modes", "mode-z", "zz-", True, "mode")
        install(src, old, "--packs", "pack-a")
        check(sorted(manifest(old).get("packs", {})) == ["pack-a"],
              f"M-8: --packs bez dopisywania domyślnych: {manifest(old).get('packs')}")

        # walidacja: tryb bez kind albo z prefiksem nakładki, nakładka z kind: mode → błąd, nic nie zapisane
        for folder, pid, kind, label in (("modes", "mode-bad", None, "tryb bez kind: mode"),
                                         ("modes", "pack-zle", "mode", "tryb bez prefiksu mode-"),
                                         ("packs", "pack-tryb", "mode", "nakładka z kind: mode")):
            bad = base / f"src-{pid}"
            shutil.copytree(src, bad)
            item(bad, folder, pid, "qq-", False, kind)
            q = base / f"proj-{pid}"
            q.mkdir()
            r = install(bad, q)
            check(r.returncode == 2 and pid in r.stdout and not manifest(q),
                  f"M-9: {label} → kod 2 z nazwą elementu: {r.returncode} {r.stdout[-400:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów trybów")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
