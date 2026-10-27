#!/usr/bin/env python3
"""Testy kopii kontraktu pdi (tools/sync_contract.py): sync z katalogu źródłowego zapisuje kopie i VERSION, check
porównuje bajt w bajt, rozjazd i brak pliku → 1, złe przypięcie → 2. Bez sieci (--source).
python3 tests/test_sync_contract.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
SCRIPT = ROOT / "tools" / "sync_contract.py"


def run(*args, cwd: Path):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=60)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        src = t / "contract"
        (src / "examples").mkdir(parents=True)
        (src / "a.schema.json").write_text('{"title": "A (kontrakt 9.9.9)"}\n', encoding="utf-8")
        (src / "examples" / "a.json").write_text('{"x": 1}\n', encoding="utf-8")
        repo = t / "repo"
        repo.mkdir()
        pin = {"repo": "dbqm45/pdi", "version": "9.9.9", "version_files": ["fix/VERSION"],
               "files": {"a.schema.json": ["scripts/a.schema.json", "fix/a.schema.json"],
                         "examples/a.json": ["fix/a.json"]}}
        pin_path = repo / "pin.json"
        pin_path.write_text(json.dumps(pin), encoding="utf-8")
        base = ["--pin", str(pin_path), "--source", str(src)]

        r = run("sync", *base, cwd=repo)
        check(r.returncode == 0 and (repo / "scripts/a.schema.json").read_bytes() == (src / "a.schema.json").read_bytes()
              and (repo / "fix/a.json").read_bytes() == (src / "examples/a.json").read_bytes()
              and (repo / "fix/VERSION").read_text(encoding="utf-8") == "9.9.9\n",
              f"S-1: sync zapisuje wszystkie kopie i VERSION: {r.stdout}{r.stderr}")
        r = run("check", *base, cwd=repo)
        check(r.returncode == 0, f"S-2: check po sync → 0: {r.stdout}{r.stderr}")

        (repo / "fix").mkdir(exist_ok=True)
        (repo / "fix/a.schema.json").write_text('{"title": "poprawione ręcznie"}\n', encoding="utf-8")
        r = run("check", *base, cwd=repo)
        check(r.returncode == 1 and "fix/a.schema.json" in r.stdout + r.stderr and "scripts/a.schema.json" not in r.stdout,
              f"S-3: ręczna zmiana kopii → 1 z nazwą tylko tej kopii: {r.stdout}{r.stderr}")
        (repo / "fix/VERSION").write_text("1.0.0\n", encoding="utf-8")
        r = run("check", *base, cwd=repo)
        check(r.returncode == 1 and "fix/VERSION" in r.stdout + r.stderr, f"S-4: zła VERSION → 1: {r.stdout}{r.stderr}")
        r = run("sync", *base, cwd=repo)
        check(r.returncode == 0 and run("check", *base, cwd=repo).returncode == 0, "S-5: sync naprawia rozjazd")

        (src / "examples" / "a.json").unlink()
        r = run("check", *base, cwd=repo)
        check(r.returncode == 1 and "examples/a.json" in r.stdout + r.stderr, f"S-6: brak pliku w źródle → 1: {r.stdout}{r.stderr}")

        pin_path.write_text(json.dumps({**pin, "extra": 1}), encoding="utf-8")
        r = run("check", *base, cwd=repo)
        check(r.returncode == 2, f"S-7: nieznany klucz w przypięciu → 2: {r.stdout}{r.stderr}")

    real = json.loads((ROOT / "tools" / "pdi-contract.json").read_text(encoding="utf-8")) \
        if (ROOT / "tools" / "pdi-contract.json").is_file() else {}
    dests = [d for ds in real.get("files", {}).values() for d in ds] + real.get("version_files", [])
    check(real.get("repo") == "dbqm45/pdi" and dests and all((ROOT / d).is_file() for d in dests)
          and "packs/pack-it/skills/eng-codebase-mapping/scripts/reconstruction-export.schema.json" in dests,
          f"S-8: przypięcie tf istnieje i wskazuje istniejące kopie (w tym schemat rekonstrukcji): {dests}")
    copies = {}
    for name, ds in real.get("files", {}).items():
        contents = {(ROOT / d).read_bytes() for d in ds if (ROOT / d).is_file()}
        copies[name] = len(contents)
    check(copies and all(n == 1 for n in copies.values()),
          f"S-9: kopie tego samego pliku kontraktu są identyczne w całym repo: {copies}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów kopii kontraktu pdi")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
