#!/usr/bin/env python3
"""
Coverage map of the skill catalog (B2) — a factory author's tool, not installed in projects.

  python3 tools/coverage_map.py --summary                  # one line + holes, for CI (informational)
  python3 tools/coverage_map.py --out docs/coverage-map.md # full Markdown report (not committed)
  python3 tools/coverage_map.py --areas file.json --root dir

For each term from `tools/coverage_areas.json` (area → list of terms) it counts the skills of the core, overlays and modes
in whose metadata (`description`, `metadata.catalog`, `metadata.keywords`) the term appears — regardless of
letter case; a term is usually a word stem („faktur” matches „faktury”, „fakturach”). Metadata counts because
the hint and the model pick a skill by it; knowledge hidden in the body that nothing leads to is invisible to
routing. A term with no skill is a **hole**, with one skill — a **thin** spot.

The map points to candidates and does not decide: a new skill is created only when an evaluation scenario confirms that the lack
does harm (core-skill-authoring). The exit code is always 0 when the input is valid (information, not a gate); 2 — an input
error. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know „✓”, „⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
FRONT = re.compile(r"\A---\n(.*?)\n---", re.S)
FIELD = re.compile(r"^\s*(description|catalog|keywords):\s*(.*)$", re.M)


def load_skills(root: Path) -> dict[str, str]:
    """Skill name → metadata text (description, catalog, keywords) in lowercase."""
    out: dict[str, str] = {}
    files = list((root / "core" / "skills").glob("*/SKILL.md"))
    for base in ("packs", "modes"):
        files += list((root / base).glob("*/skills/*/SKILL.md"))
    for f in sorted(files):
        m = FRONT.match(f.read_text(encoding="utf-8", errors="replace"))
        if not m:
            continue
        text = " ".join(v.strip().strip('"') for _, v in FIELD.findall(m.group(1)))
        out[f.parent.name] = re.sub(r"\s+", " ", text.lower())
    return out


def coverage(skills: dict[str, str], areas: dict[str, list[str]]) -> list[tuple[str, str, list[str]]]:
    rows = []
    for area, terms in areas.items():
        for term in terms:
            t = term.lower()
            rows.append((area, term, sorted(n for n, txt in skills.items() if t in txt)))
    return rows


def report(rows, n_skills: int) -> str:
    holes = [(a, t) for a, t, s in rows if not s]
    thin = [(a, t, s[0]) for a, t, s in rows if len(s) == 1]
    out = [f"# Catalog coverage map", "",
           f"Skills: {n_skills} · terms: {len(rows)} · holes: {len(holes)} · thin: {len(thin)}.", "",
           "Only skill metadata counts (description, catalog, keywords) — what routing uses to pick a skill. A hole is "
           "a candidate for a new skill or for new keywords on an existing one; decide after an evaluation scenario.", "",
           "| Area | Term | Skills | Skills (up to 4) |", "|---|---|---|---|"]
    for area, term, s in rows:
        more = f" … +{len(s) - 4}" if len(s) > 4 else ""
        out.append(f"| {area} | `{term}` | {len(s)} | {', '.join(s[:4])}{more} |")
    out += ["", "## Holes", ""] + ([f"- {a}: `{t}`" for a, t in holes] or ["- none"])
    out += ["", "## Thin (one skill)", ""] + ([f"- {a}: `{t}` — {s}" for a, t, s in thin] or ["- none"])
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Coverage map of the skill catalog (information only, exit code 0).")
    ap.add_argument("--root", default=str(ROOT), help="factory repository directory")
    ap.add_argument("--areas", default=str(ROOT / "tools" / "coverage_areas.json"), help="areas file (JSON)")
    ap.add_argument("--out", help="write the full Markdown report")
    ap.add_argument("--summary", action="store_true", help="short summary on stdout (CI)")
    a = ap.parse_args()
    try:
        areas = json.loads(Path(a.areas).read_text(encoding="utf-8"))
        assert isinstance(areas, dict) and all(isinstance(v, list) for v in areas.values())
    except (OSError, ValueError, AssertionError) as e:
        print(f"✗ areas file {a.areas}: {e}", file=sys.stderr)
        return 2
    skills = load_skills(Path(a.root))
    rows = coverage(skills, areas)
    text = report(rows, len(skills))
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    if a.summary or not a.out:
        holes = [f"{ar}: {t}" for ar, t, s in rows if not s]
        thin = sum(1 for *_, s in rows if len(s) == 1)
        print(f"Coverage map — skills: {len(skills)}, terms: {len(rows)}, holes: {len(holes)}, thin: {thin}"
              + (" (full report: python3 tools/coverage_map.py --out docs/coverage-map.md)" if not a.out else ""))
        for h in holes:
            print(f"  ⚠ hole — {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
