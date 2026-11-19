#!/usr/bin/env python3
"""Catalog coverage map (B2): area terms → the skills in which routing sees them. python3 tests/test_coverage_map.py

A tool for the factory author: shows holes (a term without a skill) and thin spots (one skill) based on the skills'
metadata (`description`, `metadata.catalog`, `metadata.keywords`), i.e. what the hint and the model pick a skill by.
The result is information — exit code 0 also with holes. A new skill is created where the map shows a hole,
and an evaluation scenario confirms that the absence hurts.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
TOOL = ROOT / "tools" / "coverage_map.py"
AREAS = ROOT / "tools" / "coverage_areas.json"


def skill(root: Path, base: str, name: str, desc: str, katalog: str, keywords: str) -> None:
    d = root / base / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f'---\nname: {name}\ndescription: {desc}\nmetadata:\n  catalog: "{katalog}"\n  keywords: "{keywords}"\n---\n'
        f"\n# {name}\n\nTreść: płatności, chargeback (w treści, nie w metadanych — nie liczy się).\n", encoding="utf-8")


def run(*args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        (root / "core" / "factory").mkdir(parents=True)
        skill(root, "core", "core-a", "Użyj przy planie projektu.", "Plan, Kamienie milowe.", "harmonogram")
        skill(root, "packs/pack-x", "x-billing", "Użyj przy subskrypcjach.", "Rozliczenia i FAKTURY.", "zwroty")
        skill(root, "packs/pack-x", "x-invoices", "Użyj przy fakturach.", "Faktury VAT.", "")
        skill(root, "modes/mode-y", "y-flow", "Użyj przy trybie.", "Tryb pracy.", "harmonogram")
        areas = root / "areas.json"
        areas.write_text(json.dumps({"Finanse": ["faktur", "chargeback", "zwrot"],
                                     "Plan": ["harmonogram", "kamień milow", "kamienie milow"]}, ensure_ascii=False),
                         encoding="utf-8")
        out = root / "report.md"
        r = run("--root", str(root), "--areas", str(areas), "--out", str(out))
        rep = out.read_text(encoding="utf-8") if out.is_file() else ""
        check(r.returncode == 0, f"C-1: code 0 also with holes: {r.returncode} {r.stderr[-300:]}")
        check("| Finanse | `faktur` | 2 | x-billing, x-invoices |" in rep,
              f"C-2: a term in the catalog regardless of letter case, two skills: {rep[:900]}")
        check("| Finanse | `chargeback` | 0 |" in rep, "C-3: a term only in a skill's body is a hole (metadata counts)")
        check("| Plan | `harmonogram` | 2 | core-a, y-flow |" in rep, "C-4: keywords, the core and a mode counted")
        check("| Finanse | `zwrot` | 1 | x-billing |" in rep, "C-5: the stem of a word matches an inflected form (“zwroty”)")
        check("Holes" in rep and "`chargeback`" in rep.split("Holes", 1)[1] and "Thin" in rep
              and "`zwrot`" in rep.split("Thin", 1)[1], f"C-6: the holes and thin sections: {rep[-600:]}")
        r = run("--root", str(root), "--areas", str(areas), "--summary")
        check(r.returncode == 0 and "holes: 2" in r.stdout and "chargeback" in r.stdout,
              f"C-7: --summary for CI: {r.stdout}")
    # C-8: the real repo — the areas file is non-empty, every area has terms, the report is produced
    areas = json.loads(AREAS.read_text(encoding="utf-8")) if AREAS.is_file() else {}
    check(len(areas) >= 8 and all(isinstance(v, list) and len(v) >= 3 for v in areas.values()),
          f"C-8: tools/coverage_areas.json — at least 8 areas with 3+ terms each: {list(areas)}")
    r = run("--summary")
    check(r.returncode == 0 and "terms:" in r.stdout, f"C-9: --summary on the factory repo: {r.stdout[:300]} {r.stderr[-300:]}")
    wf = (ROOT / ".github" / "workflows" / "factory-checks.yml").read_text(encoding="utf-8")
    check("tools/coverage_map.py --summary" in wf, "C-10: an informational step in CI (factory-checks.yml)")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} coverage map: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
