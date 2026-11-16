#!/usr/bin/env python3
"""Testy generatora nakładki firmowej: `tools/workspace.py new-org-pack <firma> --out <katalog>` — szablon
`templates/pack-org/` z polami do uzupełnienia, odmowy (katalog w repo fabryki, istniejący katalog, zła nazwa,
zajęty prefiks) i cała droga: instalacja w projekcie przez `install.py --pack-dir` i domyślne organizacji
(`org_defaults`) w konfiguracji projektu. python3 tests/test_new_org_pack.py"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())


def gen(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "tools" / "workspace.py"), "new-org-pack", *args],
                          cwd=ROOT, capture_output=True, text=True, timeout=60)


def packs_mod(factory: Path):
    spec = importlib.util.spec_from_file_location(f"op_packs_{id(factory)}", factory / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(factory))
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        out = base / "acme-factory"
        r = gen("acme", "--out", str(out), "--title", "ACME Sp. z o.o.")
        check(r.returncode == 0, f"OP-1: generator działa: {r.stdout}{r.stderr}")
        files = ["pack.yaml", "README.md", "settings.json", "skills/acme-standardy/SKILL.md",
                 "tests/skill_evals/acme-standardy.json"]
        check(all((out / f).is_file() for f in files), f"OP-1: pliki: {[f for f in files if not (out / f).is_file()]}")
        left = [str(f.relative_to(out)) for f in out.rglob("*") if f.is_file() and "{{" in f.read_text(encoding="utf-8")]
        check(not left, f"OP-2: wszystkie pola szablonu podstawione: {left}")
        pm = packs_mod(ROOT / "core" / "factory")
        pack = pm.load_yaml(out / "pack.yaml") if (out / "pack.yaml").is_file() else {}
        major = int((ROOT / "core" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0])
        check(pack.get("id") == "pack-acme" and pack.get("title") == "ACME Sp. z o.o."
              and str(pack.get("requires", {}).get("core", "")).endswith(f"<{major + 1}.0.0")
              and isinstance(pack.get("org_defaults"), dict)
              and set(pack["org_defaults"].get("config") or {}) <= set(pm.ORG_CONFIG_KEYS),
              f"OP-3: pack.yaml z id, tytułem, zakresem rdzenia i org_defaults z dozwolonymi kluczami: {pack}")
        check("acme-standardy" in json.dumps(pack.get("contributes", {})),
              f"OP-4: standardy firmy trafiają do każdej persony (contributes): {pack.get('contributes')}")
        try:
            json.loads((out / "settings.json").read_text(encoding="utf-8"))
            ev = json.loads((out / "tests" / "skill_evals" / "acme-standardy.json").read_text(encoding="utf-8"))
            ok = ev.get("skill") == "acme-standardy" and len(ev.get("scenarios", [])) >= 3
        except (OSError, ValueError):
            ok = False
        check(ok, "OP-5: settings.json i scenariusze to poprawny JSON, scenariusze dla skilla standardów")

        # odmowy: bez zmian na dysku
        r = gen("acme", "--out", str(out))
        check(r.returncode == 2 and "exists" in r.stdout + r.stderr, f"OP-6: istniejący katalog → kod 2: {r.stdout}{r.stderr}")
        inside = ROOT / ".work" / "org-test-should-not-exist"
        r = gen("acme", "--out", str(inside))
        check(r.returncode == 2 and not inside.exists(), f"OP-7: katalog w repo fabryki → kod 2: {r.stdout}{r.stderr}")
        r = gen("Acme Corp", "--out", str(base / "x"))
        check(r.returncode == 2 and not (base / "x").exists(), f"OP-8: zła nazwa → kod 2: {r.stdout}{r.stderr}")
        r = gen("firma", "--prefix", "core-", "--out", str(base / "y"))
        check(r.returncode == 2 and not (base / "y").exists(), f"OP-9: zajęty prefiks → kod 2: {r.stdout}{r.stderr}")

        # cała droga: instalacja w projekcie i domyślne organizacji w konfiguracji
        app = base / "app"
        app.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=app, check=True)
        r = subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(app), "--yes",
                            "--language", "en", "--packs", "pack-acme", "--pack-dir", str(out)],
                           capture_output=True, text=True, timeout=300)
        check(r.returncode == 0 and (app / ".tf/factory/packs/pack-acme/pack.yaml").is_file()
              and (app / ".claude/skills/acme-standardy/SKILL.md").is_file(),
              f"OP-10: instalacja nakładki firmowej przez --pack-dir: {(r.stdout + r.stderr)[-1500:]}")
        if r.returncode == 0:
            pa = packs_mod(app / ".tf" / "factory")
            labels = [lbl for lbl, _ in pa.config_layers(app)]
            comp = pa.compose(app, pa.load_config(app))
            check(any("pack-acme" in lbl and "org_defaults" in lbl for lbl in labels)
                  and not [e for e in comp["_errors"] if "org_defaults" in e],
                  f"OP-11: warstwa organizacji w konfiguracji projektu, bez błędów składania: {labels} {comp['_errors']}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów new-org-pack")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
