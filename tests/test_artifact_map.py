#!/usr/bin/env python3
"""Artifact map (A4): the `docs/project/…` paths from all skills are consistent with the journal structure
and described in the core-delivery-lifecycle map. python3 tests/test_artifact_map.py

Skills of the core, overlays and modes mention over a hundred artifact paths. Without one place that collects them,
personas do not know what to look for, and new skills drift from the directory layout (2026-11-10: `03-architecture/`
and `05-delivery/` — directories that do not exist). The test guards three things:
- a numbered `docs/project/NN-…/` directory in a skill exists in the structure from core-project-record;
- every file under a numbered directory is in the map (names with a date, a step number and `<…>` after normalization);
- the ERD is described in be-database and present in the map; SKILL.md of core-delivery-lifecycle points to the map.
"""
import re
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
MAP = ROOT / "core" / "skills" / "core-delivery-lifecycle" / "references" / "artifact-map.md"
RECORD = ROOT / "core" / "skills" / "core-project-record" / "SKILL.md"
PATH = re.compile(r"docs/project/(\d\d-[a-z-]+)/([0-9A-Za-z_./<>{}*-]*)")


def skill_files():
    for base in ("core", "packs", "modes"):
        for f in sorted((ROOT / base).rglob("*.md")):
            if "/skills/" in f.as_posix() and f != MAP:
                yield f


def norm(path: str) -> str:
    """Comparable form: date, step number, `<…>`, `NNN`, `*` → `*`."""
    p = path.rstrip(".,;:)`")
    p = re.sub(r"<[^>]+>", "*", p)
    p = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\bRRRRMMDD\b|\b\d{8}\b", "*", p)
    folder, _, name = p.partition("/")          # the directory number (04-…) stays — where the artifact lives matters
    name = re.sub(r"(^|/)(\d{2,4}|N{2,4})(?=-)", r"\1*", name)
    name = re.sub(r"(?<=-)[A-ZĄĆĘŁŃÓŚŹŻ]{3,}(?=\.)", "*", name)   # placeholder word: experiment-NAZWA.md
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
          f"M-0: journal structure in core-project-record: {sorted(canonical)}")
    bad_dirs, mentioned = [], {}
    for f in skill_files():
        for m in PATH.finditer(f.read_text(encoding="utf-8")):
            folder, rest = m.group(1), m.group(2)
            rel = f.relative_to(ROOT).as_posix()
            if folder not in canonical:
                bad_dirs.append(f"{rel}: {folder}/")
            if rest and not rest.endswith("/") and "." in rest.split("/")[-1]:
                mentioned.setdefault(norm(f"{folder}/{rest}"), rel)
    check(not bad_dirs, f"M-1: directories outside the journal structure: {sorted(set(bad_dirs))}")
    check(MAP.is_file(), f"M-2: artifact map: {MAP.relative_to(ROOT)}")
    if MAP.is_file():
        text = MAP.read_text(encoding="utf-8")
        in_map = {norm(f"{a}/{b}") for a, b in PATH.findall(text)} | {
            norm(x) for x in re.findall(r"`(\d\d-[a-z-]+/[^`\s]+)`", text)}
        missing = sorted(f"{k} ({v})" for k, v in mentioned.items() if k not in in_map)
        check(not missing, f"M-3: artifacts missing from the map ({len(missing)}): {missing}")
        check("04-architecture/erd.md" in text, "M-4: the map contains the ERD (04-architecture/erd.md)")
    db = (ROOT / "packs" / "pack-it" / "skills" / "be-database" / "SKILL.md").read_text(encoding="utf-8")
    check("erDiagram" in db and "docs/project/04-architecture/erd.md" in db,
          "M-5: be-database describes the ERD (Mermaid erDiagram, docs/project/04-architecture/erd.md)")
    lifecycle = (ROOT / "core" / "skills" / "core-delivery-lifecycle" / "SKILL.md").read_text(encoding="utf-8")
    check("references/artifact-map.md" in lifecycle, "M-6: SKILL.md of core-delivery-lifecycle points to the map")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} artifact map: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
