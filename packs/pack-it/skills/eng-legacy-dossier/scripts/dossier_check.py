#!/usr/bin/env python3
"""
Checks the completeness of a legacy system dossier (skill eng-legacy-dossier) — standard library only, no network.

  python3 .claude/skills/eng-legacy-dossier/scripts/dossier_check.py docs/project/04-architecture/legacy-dossier
  python3 … <dossier directory> --root <repository directory>   # file:line evidence is checked relative to it (default .)
  python3 … <dossier directory> --json

Architecture audit mode (optional files next to the index): `assessment.md` — findings `### ARCH-NNN — title` with the fields
Area, Category, Current state, Expected state, Gap, Evidence, Impact; `recommendations.md` — `### REC-NNN — title`
with the fields Addresses, Decision, Priority, Effort, Risk, Verification. A confirmed problem and an inconsistency require
evidence; every confirmed problem — a recommendation; preference alone does not justify a structural refactoring.

It checks: the markers and sections of README.md and of the module cards (modules/*.md), the card's `State:` field, modules from the index without a
file (an error) and files outside the index (a warning), business rules — a unique ID, a known confidence (test / code /
to verify), evidence `path:line` or `path:from-to` pointing to an existing file and line; a rule without evidence
must have the confidence "to verify". The first output line: `legacy-dossier-check: OK` or `… ERRORS`; code 0 / 1.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

INDEX_MARK, MODULE_MARK = "<!-- legacy-dossier -->", "<!-- legacy-dossier:module -->"
INDEX_SECTIONS = ["TL;DR", "Modules", "Flows", "Glossary", "State and refactoring candidates", "Open questions",
                  "Limitations"]
MODULE_SECTIONS = ["Purpose", "Responsibilities", "Inputs and outputs", "Business rules", "Data", "Dependencies",
                   "Pitfalls", "Tests", "Questions"]
CONFIDENCE = {"test", "code", "to verify"}
STATES = ("green", "yellow", "red")
ASSESS_MARK, RECS_MARK = "<!-- legacy-dossier:assessment -->", "<!-- legacy-dossier:recommendations -->"
ASSESS_SECTIONS = ["Summary", "Scope and method", "Assessment criteria", "Findings", "Strengths", "To investigate"]
RECS_SECTIONS = ["Target principles", "Recommendations", "Roadmap", "Success criteria"]
FINDING_FIELDS = ["Area", "Category", "Current state", "Expected state", "Gap", "Evidence", "Impact"]
REC_FIELDS = ["Addresses", "Decision", "Priority", "Effort", "Risk", "Verification"]
CATEGORIES = ["confirmed problem", "risk", "inconsistency", "improvement", "preference"]
NEED_EVIDENCE = {"confirmed problem", "inconsistency"}
DECISIONS = ["no change", "documentation", "configuration", "incremental refactoring", "structural refactoring",
             "redesign"]
HEAVY = {"structural refactoring", "redesign"}
PRIORITIES = ("P1", "P2", "P3")
# Pre-14.x dossiers (in Polish): section, field and value names are accepted as English equivalents; the same map
# rewrites existing dossiers during migration (`migrations.migrate_values`).
ALIASES = {
    "Moduły": "Modules", "Przepływy": "Flows", "Słownik": "Glossary",
    "Stan i kandydaci do refaktoru": "State and refactoring candidates", "Pytania otwarte": "Open questions",
    "Ograniczenia": "Limitations", "Po co": "Purpose", "Odpowiedzialności": "Responsibilities",
    "Wejścia i wyjścia": "Inputs and outputs", "Reguły biznesowe": "Business rules", "Dane": "Data",
    "Zależności": "Dependencies", "Pułapki": "Pitfalls", "Testy": "Tests", "Pytania": "Questions",
    "Podsumowanie": "Summary", "Zakres i metoda": "Scope and method", "Kryteria oceny": "Assessment criteria",
    "Ustalenia": "Findings", "Mocne strony": "Strengths", "Do dalszego zbadania": "To investigate",
    "Docelowe zasady": "Target principles", "Rekomendacje": "Recommendations", "Roadmapa": "Roadmap",
    "Kryteria sukcesu": "Success criteria",
    "Obszar": "Area", "Kategoria": "Category", "Stan obecny": "Current state", "Stan oczekiwany": "Expected state",
    "Luka": "Gap", "Dowód": "Evidence", "Wpływ": "Impact", "Dotyczy": "Addresses", "Decyzja": "Decision",
    "Priorytet": "Priority", "Wysiłek": "Effort", "Ryzyko": "Risk", "Weryfikacja": "Verification",
}
VALUE_ALIASES = {
    "potwierdzony problem": "confirmed problem", "ryzyko": "risk", "niespójność": "inconsistency",
    "możliwość poprawy": "improvement", "preferencja": "preference", "bez zmian": "no change",
    "dokumentacja": "documentation", "konfiguracja": "configuration",
    "refaktoryzacja przyrostowa": "incremental refactoring", "refaktoryzacja strukturalna": "structural refactoring",
    "przeprojektowanie": "redesign", "kod": "code", "do weryfikacji": "to verify",
    "zielony": "green", "żółty": "yellow", "czerwony": "red",
}
STATE_LINE = re.compile(r"^(?:State|Stan): (\S+) — \S", re.M)


def en(name: str) -> str:
    return ALIASES.get(name, name)


def value(v: str) -> str:
    return VALUE_ALIASES.get(v, v)


EVIDENCE = re.compile(r"`?([^\s`:|]+):(\d+)(?:-(\d+))?`?")


def sections(text: str) -> dict[str, str]:
    out, name = {}, None
    for line in text.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            name = en(m.group(1))
            out[name] = ""
        elif name:
            out[name] += line + "\n"
    return out


def table_rows(body: str) -> list[list[str]]:
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in body.splitlines()
            if line.strip().startswith("|")]
    return [r for r in rows[2:] if any(r)] if len(rows) > 2 else []


def check_evidence(ev: str, root: Path) -> str | None:
    m = EVIDENCE.fullmatch(ev.strip())
    if not m:
        return f"evidence \"{ev}\" is not in path:line form"
    path, start, end = root / m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
    if not path.resolve().is_relative_to(root.resolve()):
        return f"evidence {m.group(1)} points to a file outside the repository"
    if not path.is_file():
        return f"evidence points to a missing file {m.group(1)}"
    lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    if not 1 <= start <= end <= lines:
        return f"evidence {m.group(0)} goes past the end of the file ({lines} lines)"
    return None


def blocks(body: str, prefix: str) -> list[tuple[str, dict[str, str]]]:
    """Blocks `### <prefix>-NNN — title` with `Key: value` fields (block order preserved)."""
    out = []
    for part in re.split(rf"^### (?={prefix}-)", body, flags=re.M)[1:]:
        head, _, rest = part.partition("\n")
        fields = {en(k): v for k, v in (m.groups() for m in re.finditer(r"^([^:\n]+?):\s*(.*?)\s*$", rest, re.M))}
        out.append((head.split(" ")[0].strip(), fields))
    return out


def evidence_problems(ev: str, root: Path) -> list[str]:
    return [p for one in re.split(r"[,;]\s*", ev) if (p := check_evidence(one, root))]


def check_audit(dossier: Path, root: Path, errors: list[str]) -> tuple[int, int]:
    a_p, r_p = dossier / "assessment.md", dossier / "recommendations.md"
    if not a_p.is_file():
        if r_p.is_file():
            errors.append("recommendations.md without assessment.md — recommendations follow from assessment findings")
        return 0, 0
    at = a_p.read_text(encoding="utf-8")
    if not at.startswith(ASSESS_MARK):
        errors.append(f"assessment.md: missing marker {ASSESS_MARK} on the first line")
    asec = sections(at)
    errors += [f"assessment.md: missing section \"## {s}\"" for s in ASSESS_SECTIONS if s not in asec]
    findings: dict[str, str] = {}
    for fid, f in blocks(asec.get("Findings", ""), "ARCH"):
        if fid in findings:
            errors.append(f"assessment.md: {fid} duplicated")
        missing = [k for k in FINDING_FIELDS if not f.get(k)]
        if missing:
            errors.append(f"assessment.md: {fid} — missing fields: {', '.join(missing)}")
        cat = value(f.get("Category", ""))
        if cat and cat not in CATEGORIES:
            errors.append(f"assessment.md: {fid} — unknown category \"{cat}\" (allowed: {', '.join(CATEGORIES)})")
        ev = f.get("Evidence", "")
        if ev in ("", "—", "-"):
            if cat in NEED_EVIDENCE:
                errors.append(f"assessment.md: {fid} — \"{cat}\" needs evidence (file:line); without it, it is a risk or a question")
        else:
            errors += [f"assessment.md: {fid} — {p}" for p in evidence_problems(ev, root)]
        findings[fid] = cat
    if not r_p.is_file():
        return len(findings), 0
    rt = r_p.read_text(encoding="utf-8")
    if not rt.startswith(RECS_MARK):
        errors.append(f"recommendations.md: missing marker {RECS_MARK} on the first line")
    rsec = sections(rt)
    errors += [f"recommendations.md: missing section \"## {s}\"" for s in RECS_SECTIONS if s not in rsec]
    covered, recs = set(), blocks(rsec.get("Recommendations", ""), "REC")
    for rid, r in recs:
        missing = [k for k in REC_FIELDS if not r.get(k)]
        if missing:
            errors.append(f"recommendations.md: {rid} — missing fields: {', '.join(missing)}")
        refs = re.findall(r"ARCH-\d+", r.get("Addresses", ""))
        for ref in refs:
            if ref not in findings:
                errors.append(f"recommendations.md: {rid} refers to {ref}, which is not in assessment.md")
        covered.update(refs)
        dec, pri = value(r.get("Decision", "")), r.get("Priority", "")
        if dec and dec not in DECISIONS:
            errors.append(f"recommendations.md: {rid} — unknown decision \"{dec}\" (allowed: {', '.join(DECISIONS)})")
        if pri and pri not in PRIORITIES:
            errors.append(f"recommendations.md: {rid} — unknown priority \"{pri}\" (allowed: P1, P2, P3)")
        if dec in HEAVY and refs and all(findings.get(x) == "preference" for x in refs):
            errors.append(f"recommendations.md: {rid} — \"{dec}\" justified by preference alone; it needs a problem or a risk")
    for fid, cat in findings.items():
        if cat == "confirmed problem" and fid not in covered:
            errors.append(f"recommendations.md: confirmed problem {fid} has no recommendation (\"no change\" with a reason also counts)")
    return len(findings), len(recs)


def check(dossier: Path, root: Path) -> dict:
    errors, warnings, rules, unverified, ids = [], [], 0, 0, {}
    index = dossier / "README.md"
    if not index.is_file():
        return {"status": "ERRORS", "errors": [f"missing {index}"], "warnings": [], "modules": 0, "rules": 0,
                "unverified": 0}
    text = index.read_text(encoding="utf-8")
    if not text.startswith(INDEX_MARK):
        errors.append(f"README.md: missing marker {INDEX_MARK} on the first line")
    secs = sections(text)
    errors += [f"README.md: missing section \"## {s}\"" for s in INDEX_SECTIONS if s not in secs]
    listed = set(re.findall(r"\]\((modules/[^)]+\.md)\)", secs.get("Modules", "")))
    for rel in sorted(listed):
        if not (dossier / rel).is_file():
            errors.append(f"README.md: module {rel} is in the index, but the file does not exist")
    files = sorted(p.relative_to(dossier).as_posix() for p in (dossier / "modules").glob("*.md")) \
        if (dossier / "modules").is_dir() else []
    warnings += [f"{rel}: module card not in the index (add it under \"## Modules\")" for rel in files if rel not in listed]
    for rel in files:
        mt = (dossier / rel).read_text(encoding="utf-8")
        if not mt.startswith(MODULE_MARK):
            errors.append(f"{rel}: missing marker {MODULE_MARK} on the first line")
        st = STATE_LINE.search(mt)
        if not st or value(st.group(1)) not in STATES:
            errors.append(f"{rel}: missing field \"State: green|yellow|red — <reason>\"")
        ms = sections(mt)
        errors += [f"{rel}: missing section \"## {s}\"" for s in MODULE_SECTIONS if s not in ms]
        for row in table_rows(ms.get("Business rules", "")):
            if len(row) < 4:
                errors.append(f"{rel}: rule row has {len(row)} columns instead of 4 (ID | Rule | Evidence | Confidence)")
                continue
            rid, _, ev, conf = row[:4]
            conf = value(conf)
            rules += 1
            if rid in ids:
                errors.append(f"{rel}: {rid} duplicated (first seen in {ids[rid]})")
            ids.setdefault(rid, rel)
            if conf not in CONFIDENCE:
                errors.append(f"{rel}: {rid} — unknown confidence \"{conf}\" (allowed: {', '.join(sorted(CONFIDENCE))})")
            if conf == "to verify":
                unverified += 1
            if ev in ("", "—", "-"):
                if conf != "to verify":
                    errors.append(f"{rel}: {rid} without evidence must have confidence \"to verify\"")
            else:
                for one in re.split(r"[,;]\s*", ev):
                    problem = check_evidence(one, root)
                    if problem:
                        errors.append(f"{rel}: {rid} — {problem}")
    n_find, n_recs = check_audit(dossier, root, errors)
    return {"status": "ERRORS" if errors else "OK", "errors": errors, "warnings": warnings, "modules": len(files),
            "rules": rules, "unverified": unverified, "findings": n_find, "recommendations": n_recs}


def main(argv: list[str]) -> int:
    args, root, as_json = [], Path("."), False
    it = iter(argv[1:])
    for a in it:
        if a in ("-h", "--help"):
            print(__doc__)
            return 0
        if a == "--root":
            root = Path(next(it, "."))
        elif a == "--json":
            as_json = True
        else:
            args.append(a)
    if len(args) != 1:
        print(__doc__)
        return 2
    res = check(Path(args[0]), root)
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"legacy-dossier-check: {res['status']}")
        print(f"modules: {res['modules']} · rules: {res['rules']} · to verify: {res['unverified']}"
              + (f" · findings: {res['findings']} · recommendations: {res['recommendations']}" if res["findings"] else ""))
        for e in res["errors"]:
            print(f"✗ {e}")
        for w in res["warnings"]:
            print(f"⚠ {w}")
    return 0 if res["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
