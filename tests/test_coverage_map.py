#!/usr/bin/env python3
"""Mapa pokrycia katalogu (B2): hasła obszarów → skille, w których trasowanie je widzi. python3 tests/test_coverage_map.py

Narzędzie autora fabryki: pokazuje dziury (hasło bez skilla) i miejsca cienkie (jeden skill) na podstawie metadanych
skilli (`description`, `metadata.katalog`, `metadata.slowa`), czyli tego, po czym podpowiedź i model wybierają skill.
Wynik jest informacją — kod wyjścia 0 także przy dziurach. Nowy skill powstaje tam, gdzie mapa pokazuje dziurę,
a scenariusz ewaluacji potwierdza, że brak szkodzi.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
TOOL = ROOT / "tools" / "coverage_map.py"
AREAS = ROOT / "tools" / "coverage_areas.json"


def skill(root: Path, base: str, name: str, desc: str, katalog: str, slowa: str) -> None:
    d = root / base / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f'---\nname: {name}\ndescription: {desc}\nmetadata:\n  katalog: "{katalog}"\n  slowa: "{slowa}"\n---\n'
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
        out = root / "raport.md"
        r = run("--root", str(root), "--areas", str(areas), "--out", str(out))
        rep = out.read_text(encoding="utf-8") if out.is_file() else ""
        check(r.returncode == 0, f"C-1: kod 0 także przy dziurach: {r.returncode} {r.stderr[-300:]}")
        check("| Finanse | `faktur` | 2 | x-billing, x-invoices |" in rep,
              f"C-2: hasło w katalogu bez względu na wielkość liter, dwa skille: {rep[:900]}")
        check("| Finanse | `chargeback` | 0 |" in rep, "C-3: hasło tylko w treści skilla to dziura (liczą się metadane)")
        check("| Plan | `harmonogram` | 2 | core-a, y-flow |" in rep, "C-4: słowa kluczowe, rdzeń i tryb liczone")
        check("| Finanse | `zwrot` | 1 | x-billing |" in rep, "C-5: rdzeń wyrazu trafia w odmianę („zwroty”)")
        check("Dziury" in rep and "`chargeback`" in rep.split("Dziury", 1)[1] and "Cienkie" in rep
              and "`zwrot`" in rep.split("Cienkie", 1)[1], f"C-6: sekcje dziur i cienkich: {rep[-600:]}")
        r = run("--root", str(root), "--areas", str(areas), "--summary")
        check(r.returncode == 0 and "dziury: 2" in r.stdout and "chargeback" in r.stdout,
              f"C-7: --summary do CI: {r.stdout}")
    # C-8: prawdziwe repo — plik obszarów niepusty, każdy obszar ma hasła, raport powstaje
    areas = json.loads(AREAS.read_text(encoding="utf-8")) if AREAS.is_file() else {}
    check(len(areas) >= 8 and all(isinstance(v, list) and len(v) >= 3 for v in areas.values()),
          f"C-8: tools/coverage_areas.json — co najmniej 8 obszarów po 3+ hasła: {list(areas)}")
    r = run("--summary")
    check(r.returncode == 0 and "haseł:" in r.stdout, f"C-9: --summary na repo fabryki: {r.stdout[:300]} {r.stderr[-300:]}")
    wf = (ROOT / ".github" / "workflows" / "factory-checks.yml").read_text(encoding="utf-8")
    check("tools/coverage_map.py --summary" in wf, "C-10: krok informacyjny w CI (factory-checks.yml)")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} mapa pokrycia: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
