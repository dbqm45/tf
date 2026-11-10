#!/usr/bin/env python3
"""Mapa artefaktów (A4): ścieżki `docs/project/…` ze wszystkich skilli są spójne ze strukturą dziennika
i opisane w mapie core-delivery-lifecycle. python3 tests/test_artifact_map.py

Skille rdzenia, nakładek i trybów wymieniają ponad sto ścieżek artefaktów. Bez jednego miejsca, które je zbiera,
persony nie wiedzą, czego szukać, a nowe skille rozjeżdżają się z układem katalogów (2026-11-10: `03-architecture/`
i `05-delivery/` — katalogi, których nie ma). Test pilnuje trzech rzeczy:
- numerowany katalog `docs/project/NN-…/` w skillu istnieje w strukturze z core-project-record;
- każdy plik pod numerowanym katalogiem jest w mapie (nazwy z datą, numerem kroku i `<…>` po normalizacji);
- ERD jest opisany w be-database i obecny w mapie; SKILL.md core-delivery-lifecycle odsyła do mapy.
"""
import re
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
MAP = ROOT / "core" / "skills" / "core-delivery-lifecycle" / "references" / "mapa-artefaktow.md"
RECORD = ROOT / "core" / "skills" / "core-project-record" / "SKILL.md"
PATH = re.compile(r"docs/project/(\d\d-[a-z-]+)/([0-9A-Za-z_./<>{}*-]*)")


def skill_files():
    for base in ("core", "packs", "modes"):
        for f in sorted((ROOT / base).rglob("*.md")):
            if "/skills/" in f.as_posix() and f != MAP:
                yield f


def norm(path: str) -> str:
    """Postać porównywalna: data, numer kroku, `<…>`, `NNN`, `*` → `*`."""
    p = path.rstrip(".,;:)`")
    p = re.sub(r"<[^>]+>", "*", p)
    p = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\bRRRRMMDD\b|\b\d{8}\b", "*", p)
    folder, _, name = p.partition("/")          # numer katalogu (04-…) zostaje — liczy się, gdzie leży artefakt
    name = re.sub(r"(^|/)(\d{2,4}|N{2,4})(?=-)", r"\1*", name)
    name = re.sub(r"(?<=-)[A-ZĄĆĘŁŃÓŚŹŻ]{3,}(?=\.)", "*", name)   # słowo zastępcze: experiment-NAZWA.md
    return re.sub(r"\*+", "*", f"{folder}/{name}")


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    record = RECORD.read_text(encoding="utf-8")
    canonical = set(re.findall(r"^\s{2}(\d\d-[a-z-]+)/", record, re.M))
    check({"01-discovery", "04-architecture", "06-delivery", "08-operations"} <= canonical,
          f"M-0: struktura dziennika w core-project-record: {sorted(canonical)}")
    bad_dirs, mentioned = [], {}
    for f in skill_files():
        for m in PATH.finditer(f.read_text(encoding="utf-8")):
            folder, rest = m.group(1), m.group(2)
            rel = f.relative_to(ROOT).as_posix()
            if folder not in canonical:
                bad_dirs.append(f"{rel}: {folder}/")
            if rest and not rest.endswith("/") and "." in rest.split("/")[-1]:
                mentioned.setdefault(norm(f"{folder}/{rest}"), rel)
    check(not bad_dirs, f"M-1: katalogi spoza struktury dziennika: {sorted(set(bad_dirs))}")
    check(MAP.is_file(), f"M-2: mapa artefaktów: {MAP.relative_to(ROOT)}")
    if MAP.is_file():
        text = MAP.read_text(encoding="utf-8")
        in_map = {norm(f"{a}/{b}") for a, b in PATH.findall(text)} | {
            norm(x) for x in re.findall(r"`(\d\d-[a-z-]+/[^`\s]+)`", text)}
        missing = sorted(f"{k} ({v})" for k, v in mentioned.items() if k not in in_map)
        check(not missing, f"M-3: artefakty spoza mapy ({len(missing)}): {missing}")
        check("04-architecture/erd.md" in text, "M-4: mapa zawiera ERD (04-architecture/erd.md)")
    db = (ROOT / "packs" / "pack-it" / "skills" / "be-database" / "SKILL.md").read_text(encoding="utf-8")
    check("erDiagram" in db and "docs/project/04-architecture/erd.md" in db,
          "M-5: be-database opisuje ERD (Mermaid erDiagram, docs/project/04-architecture/erd.md)")
    lifecycle = (ROOT / "core" / "skills" / "core-delivery-lifecycle" / "SKILL.md").read_text(encoding="utf-8")
    check("references/mapa-artefaktow.md" in lifecycle, "M-6: SKILL.md core-delivery-lifecycle odsyła do mapy")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} mapa artefaktów: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
