#!/usr/bin/env python3
"""Testy aktualizacji instalatora: manifest zapisuje skrót pliku po `factory/build.py` (spis treści plików referencyjnych),
więc aktualizacja czystej instalacji nie zostawia `*.factory-new`; pliki fabryki zmienione w projekcie
aktualizacja nadpisuje (jak node_modules), a w `factory/config.yaml` zostawia ustawienia projektu i dopisuje nowe klucze; klon instalacji zespołowej (manifest poza gitem)
aktualizuje się z commitowanego `.claude/factory-lock.json`, a nie pomija plików fabryki; spisy treści w źródle
fabryki są aktualne. python3 tests/test_install_update.py"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
LOCK = ".claude/factory-lock.json"
MANIFEST = ".claude/factory-manifest.json"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def long_reference(toc: str | None) -> str:
    """Plik referencyjny > 100 linii z 3 sekcjami — build.py dopisuje mu spis treści."""
    body = ["# Długi", ""] + ([toc, ""] if toc else [])
    for h in ("Pierwsza", "Druga", "Trzecia"):
        body += [f"## {h}", ""] + [f"Linia {i} sekcji {h}." for i in range(40)] + [""]
    return "\n".join(body) + "\n"


def install(src: Path, proj: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(src / "core" / "factory" / "install.py"), str(proj), "--yes", *args],
                          capture_output=True, text=True, timeout=300)


def factory_new(proj: Path) -> list[str]:
    return sorted(p.relative_to(proj).as_posix() for p in proj.rglob("*.factory-new"))


def stale_tocs(root: Path) -> list[str]:
    """Pliki referencyjnych skilli w źródle fabryki, którym build.py zmieniłby spis treści."""
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


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # T-1: źródło fabryki ma aktualne spisy treści (inaczej każdy projekt dostaje plik, który build.py przepisze)
    stale = stale_tocs(ROOT)
    check(not stale, f"T-1: nieaktualny spis treści w źródle ({len(stale)}): {stale[:5]}")

    with tempfile.TemporaryDirectory() as t:
        src = Path(t) / "src"
        shutil.copytree(ROOT / "core", src / "core", ignore=shutil.ignore_patterns("__pycache__"))
        major = int((src / "core" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0])
        pack = src / "packs" / "pack-a"
        write(pack / "pack.yaml", f"id: pack-a\nversion: 1.0.0\ntitle: A\ndescription: A test.\n"
                                  f"requires: {{core: \">={major}.0.0 <{major + 1}.0.0\"}}\n"
                                  "facets:\n  - {prefix: aa-, order: 900, name: a, question: \"a\"}\n")
        write(pack / "skills" / "aa-run" / "SKILL.md",
              "---\nname: aa-run\ndescription: Użyj przy A.\nmetadata:\n  katalog: \"Użyj przy A. Nie do niczego.\"\n"
              "  przeglad: 2099-01-01\n---\n# aa-run\nTreść 1.\n")
        ref = pack / "skills" / "aa-run" / "references" / "dlugi.md"
        write(ref, long_reference("> **Spis treści:** Pierwsza · Druga"))   # nieaktualny spis (brak „Trzecia”)

        # U-1..U-3: czysta instalacja, potem aktualizacja tą samą wersją — bez *.factory-new
        proj = Path(t) / "proj"
        proj.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=proj, check=True)
        r = install(src, proj, "--shared", "--packs", "pack-a")
        check(r.returncode == 0, f"U-1: instalacja: {r.stdout[-600:]} {r.stderr[-300:]}")
        check((proj / ".tf" / "reports" / "README.md").is_file() and (proj / ".tf" / "logs").is_dir(),
              "U-1a: instalacja zakłada .tf/ (jak tf init)")
        installed = proj / ".claude" / "skills" / "aa-run" / "references" / "dlugi.md"
        text = installed.read_text(encoding="utf-8") if installed.exists() else ""
        man = json.loads((proj / MANIFEST).read_text(encoding="utf-8")) if (proj / MANIFEST).exists() else {}
        import hashlib
        rel = ".claude/skills/aa-run/references/dlugi.md"
        check("Trzecia" in text.splitlines()[2] if len(text.splitlines()) > 2 else False,
              f"U-2: build.py poprawił spis treści w projekcie: {text.splitlines()[:3]}")
        check(man.get("files", {}).get(rel) == hashlib.sha256(text.encode("utf-8")).hexdigest(),
              "U-3: manifest ma skrót pliku po build.py (taki, jaki jest na dysku)")
        r = install(src, proj)
        check(r.returncode == 0 and not factory_new(proj) and "You changed these factory files" not in r.stdout,
              f"U-4: aktualizacja czystej instalacji bez *.factory-new: {factory_new(proj)} {r.stdout[-500:]}")

        # L-1..L-3: instalacja zespołowa ma commitowany lock (bez danych lokalnych), prywatna — nie
        lock = json.loads((proj / LOCK).read_text(encoding="utf-8")) if (proj / LOCK).exists() else {}
        gi = (proj / ".gitignore").read_text(encoding="utf-8") if (proj / ".gitignore").exists() else ""
        check(lock.get("packs") == ["pack-a"] and lock.get("files", {}).get(rel) == man.get("files", {}).get(rel)
              and lock.get("version") and not {"source", "python", "installed_at"} & set(lock),
              f"L-1: lock w trybie zespołowym — wersja, nakładki, skróty, bez danych lokalnych: {sorted(lock)}")
        check(LOCK not in gi.splitlines() and MANIFEST in gi.splitlines(), "L-2: lock nie jest ignorowany, manifest jest")
        priv = Path(t) / "priv"
        priv.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=priv, check=True)
        install(src, priv, "--packs", "pack-a")
        check(not (priv / LOCK).exists(), "L-3: instalacja prywatna nie zapisuje locka")

        # C-1..C-4: klon instalacji zespołowej (bez manifestu i ignorowanych plików), nowa wersja źródła
        clone = Path(t) / "clone"
        subprocess.run(["git", "add", "-A"], cwd=proj, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i"], cwd=proj, check=True)
        subprocess.run(["git", "clone", "-q", str(proj), str(clone)], check=True)
        check(not (clone / MANIFEST).exists() and (clone / LOCK).exists(), "C-1: klon ma lock, nie ma manifestu")
        write(pack / "skills" / "aa-run" / "SKILL.md",
              (pack / "skills" / "aa-run" / "SKILL.md").read_text(encoding="utf-8").replace("Treść 1.", "Treść 2."))
        write(src / "core" / "factory" / "VERSION", f"{major}.99.0\n")
        own = clone / ".claude" / "skills" / "aa-run" / "references" / "dlugi.md"
        own.write_text(own.read_text(encoding="utf-8") + "Moja notatka.\n", encoding="utf-8")   # zmiana zespołu
        r = install(src, clone)
        skill = (clone / ".claude" / "skills" / "aa-run" / "SKILL.md").read_text(encoding="utf-8")
        check(r.returncode == 0 and "Treść 2." in skill and "Skipped existing" not in r.stdout,
              f"C-2: aktualizacja klonu nadpisuje niezmieniony plik fabryki, nic nie pomija: {r.stdout[-700:]}")
        check("packs: pack-a" in r.stdout and f"→ {major}.99.0" in r.stdout,
              f"C-3: nakładki i wersja z locka: {r.stdout[-400:]}")
        check("Moja notatka." not in own.read_text(encoding="utf-8") and not factory_new(clone)
              and "dlugi.md" in r.stdout,
              f"C-4: plik fabryki zmieniony w projekcie nadpisany (jak node_modules), bez *.factory-new, wymieniony "
              f"w wyniku: {factory_new(clone)} {r.stdout[-600:]}")
        lock2 = json.loads((clone / LOCK).read_text(encoding="utf-8")) if (clone / LOCK).exists() else {}
        check(lock2.get("version") == f"{major}.99.0", f"C-5: lock zaktualizowany: {lock2.get('version')}")

        # N-1..N-4: config.yaml to konfiguracja projektu — ustawienia zostają, nowe klucze fabryki dochodzą;
        # własne pliki w katalogach fabryki zostają nietknięte
        cfg_src = src / "core" / "factory" / "config.yaml"
        write(cfg_src, cfg_src.read_text(encoding="utf-8") + "\n# nowy klucz fabryki\nnowy_klucz_testu:\n  a: 1\n")
        write(src / "core" / "factory" / "VERSION", f"{major}.99.1\n")
        cfg = clone / "factory" / "config.yaml"
        before = cfg.read_text(encoding="utf-8")
        check("default_profile: zrownowazony" in before, "N-0: konfiguracja ma domyślny profil (założenie testu)")
        cfg.write_text(before.replace("default_profile: zrownowazony", "default_profile: oszczedny"), encoding="utf-8")
        mine = clone / "factory" / "personas" / "moja-persona.yaml"
        write(mine, "name: moja\n")
        r = install(src, clone)
        after = cfg.read_text(encoding="utf-8")
        check(r.returncode == 0 and "default_profile: oszczedny" in after and "nowy_klucz_testu:" in after
              and "  a: 1" in after, f"N-1: config.yaml — ustawienie projektu zostaje, nowy klucz dopisany: "
              f"{r.stdout[-500:]} {after[-300:]}")
        check(after.count("default_profile:") == 1, "N-2: istniejący klucz nie jest dublowany")
        check(mine.read_text(encoding="utf-8") == "name: moja\n", "N-3: własny plik w factory/personas/ nietknięty")
        check(not factory_new(clone), f"N-4: żadnych *.factory-new: {factory_new(clone)}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów aktualizacji instalatora")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
