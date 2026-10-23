#!/usr/bin/env python3
"""Testy generatora nowej nakładki lub trybu: `tools/workspace.py new-pack` — szkielet pack.yaml, skill, scenariusze,
rola, przewodnik trybu, wpis w macierzy CI, odmowa nadpisania i kolizji prefiksu. python3 tests/test_new_pack.py

Generator działa na kopii narzędzia w tymczasowym katalogu ze sztucznym rdzeniem, nakładką i workflow CI."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
MATRIX = "        packs: [none, pack-it, mode-talos, all]\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fake_root(base: Path) -> Path:
    r = base / "tf"
    write(r / "tools" / "workspace.py", (ROOT / "tools" / "workspace.py").read_text(encoding="utf-8"))
    write(r / "core" / "factory" / "VERSION", "5.13.0\n")
    write(r / "core" / "factory" / "config.yaml",
          "facets:\n  - {prefix: core-, order: 900, name: praktyki, question: \"jak pracujemy\"}\n")
    write(r / "packs" / "pack-it" / "pack.yaml",
          "id: pack-it\nversion: 1.0.0\nfacets:\n  - {prefix: it-, order: 10, name: it, question: \"it\"}\n")
    write(r / ".github" / "workflows" / "factory-checks.yml", "jobs:\n  workspace:\n    strategy:\n      matrix:\n" + MATRIX)
    return r


def run(root: Path, *args):
    return subprocess.run([sys.executable, str(root / "tools" / "workspace.py"), "new-pack", *args],
                          cwd=root, capture_output=True, text=True, timeout=60)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        root = fake_root(Path(d))
        r = run(root, "demo", "--prefix", "dm-", "--title", "Demo", "--description", "Demo pack for tests.",
                "--skill", "dm-start", "--role", "demo-role", "--no-check")
        base = root / "packs" / "pack-demo"
        check(r.returncode == 0, f"N-1: działa: {r.stdout}{r.stderr}")
        files = ["pack.yaml", "skills/dm-start/SKILL.md", "tests/skill_evals/dm-start.json", "roles/demo-role.yaml"]
        check(all((base / f).is_file() for f in files), f"N-2: pliki: {[f for f in files if not (base / f).is_file()]}")
        pack = (base / "pack.yaml").read_text(encoding="utf-8") if (base / "pack.yaml").is_file() else ""
        check("id: pack-demo" in pack and "version: 0.1.0" in pack and "default: false" in pack
              and 'core: ">=5.13.0 <6.0.0"' in pack and "prefix: dm-" in pack and "kind:" not in pack
              and 'title: "Demo"' in pack and 'description: "Demo pack for tests."' in pack, f"N-3: pack.yaml:\n{pack}")
        sk = base / "skills" / "dm-start" / "SKILL.md"
        text = sk.read_text(encoding="utf-8") if sk.is_file() else ""
        check("name: dm-start" in text and "description: Użyj" in text and "katalog:" in text and "przeglad:" in text
              and "slowa:" in text and "## Przykład" in text and "## Źródła" in text, f"N-4: SKILL.md:\n{text}")
        ev = base / "tests" / "skill_evals" / "dm-start.json"
        data = json.loads(ev.read_text(encoding="utf-8")) if ev.is_file() else {}
        sc = data.get("scenarios", [])
        check(data.get("skill") == "dm-start" and len(sc) >= 3 and any(s.get("expect") == "no-trigger" and s.get("neighbor")
              for s in sc) and "TODO" in json.dumps(data), f"N-5: szkielet scenariuszy do uzupełnienia: {data}")
        role = (base / "roles" / "demo-role.yaml").read_text(encoding="utf-8") if (base / "roles" / "demo-role.yaml").is_file() else ""
        check("name: demo-role" in role and "skills: [dm-start]" in role and "verify: \"" in role, f"N-6: rola: {role}")
        ci = (root / ".github" / "workflows" / "factory-checks.yml").read_text(encoding="utf-8")
        check("packs: [none, pack-it, mode-talos, pack-demo, all]" in ci, f"N-7: macierz CI: {ci}")
        check("Do zrobienia" in r.stdout and "skill_gate" in r.stdout, f"N-8: lista do zrobienia: {r.stdout}")

        before = (base / "pack.yaml").read_text(encoding="utf-8") if (base / "pack.yaml").is_file() else ""
        r = run(root, "demo", "--prefix", "dx-", "--no-check")
        after = (base / "pack.yaml").read_text(encoding="utf-8") if (base / "pack.yaml").is_file() else ""
        check(r.returncode == 2 and after == before and before,
              f"N-9: istniejący katalog → kod 2 bez nadpisania: {r.returncode} {r.stderr}")

        r = run(root, "tracker", "--kind", "mode", "--prefix", "tr-", "--no-check")
        mb = root / "modes" / "mode-tracker"
        mp = (mb / "pack.yaml").read_text(encoding="utf-8") if (mb / "pack.yaml").is_file() else ""
        check(r.returncode == 0 and "id: mode-tracker" in mp and "kind: mode" in mp and (mb / "GUIDE.md").is_file()
              and (mb / "skills" / "tr-podstawy" / "SKILL.md").is_file(), f"N-10: tryb z przewodnikiem: {r.stdout}{r.stderr}")
        ci = (root / ".github" / "workflows" / "factory-checks.yml").read_text(encoding="utf-8")
        check("pack-demo, mode-tracker, all]" in ci, f"N-11: tryb w macierzy CI: {ci}")

        r = run(root, "inny", "--prefix", "it-", "--no-check")
        check(r.returncode == 2 and not (root / "packs" / "pack-inny").exists(), f"N-12: prefiks zajęty → kod 2: {r.stdout}{r.stderr}")
        r = run(root, "Zła_Nazwa", "--no-check")
        check(r.returncode == 2, "N-13: zła nazwa → kod 2")
        r = run(root, "beta", "--no-check")
        bp = root / "packs" / "pack-beta" / "pack.yaml"
        check(r.returncode == 0 and bp.is_file() and "prefix: beta-" in bp.read_text(encoding="utf-8")
              and 'description: "TODO: ' in bp.read_text(encoding="utf-8"),
              f"N-14: prefiks domyślny z nazwy: {r.stdout}{r.stderr}")
        r = run(root, "gamma", "--skill", "zz-cos", "--prefix", "gm-", "--no-check")
        check(r.returncode == 2 and not (root / "packs" / "pack-gamma").exists(), "N-15: skill spoza prefiksu → kod 2")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów new-pack")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
