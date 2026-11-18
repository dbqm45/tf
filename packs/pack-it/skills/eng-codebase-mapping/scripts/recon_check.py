#!/usr/bin/env python3
"""
Evidence check in a report built from code (project reconstruction, code map, dossier): every `file:line` must point to
an existing file and line, and the quote given with the evidence must be found in the code (±2 lines). Bullets without
evidence and without a [assumption] / [unverified] / [question] mark are reported as claims without evidence.

  python3 recon_check.py <file.md|directory> [--repo DIR] [--json]
  python3 recon_check.py docs/project/00-reconstruction/report.md --final   # also report sections and 0 claims without evidence

--final also checks:
- the table in the "Stack" section with the rows Language, Framework, Data, Build, Tests, CI, Configuration (each row with
  evidence or a mark); when the repo has pipeline files (e.g. .github/workflows/), the CI row must point to one of them;
- that the "Modules" section lists every module from the `modules/*.json` cards next to the report, and every card has a
  current `modules/<card>.md` from `recon_cards.py` (a digest of the card content in the first line).

Evidence: `path:line` or `path:from-to`; a quote in "…" or „…” in the same row, after the evidence.
Exit code: 0 — OK, 1 — bad evidence (or gaps with --final), 2 — bad invocation.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import sys

REF = re.compile(r"`?((?:[\w.@-]+/)*[\w.@-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`?")
QUOTE = re.compile(r"\"([^\"]{3,})\"|„([^”]{3,})”")
MARK = re.compile(r"\[(assumption|unverified|question|założenie|niezweryfikowane|pytanie)[^\]]*\]", re.I)
SECTIONS = ("TL;DR", "Stack", "Modules", "Domains", "Requirements", "Rules", "Standards", "Risks", "Questions",
            "Not checked")
NO_EVIDENCE_SECTIONS = ("Questions", "Not checked")   # bullets here have no evidence by nature
STACK_ROWS = ("Language", "Framework", "Data", "Build", "Tests", "CI", "Configuration")   # required rows of the stack table
# Reports from before 14.x: Polish section and stack row headings accepted as English equivalents.
HEADING_ALIASES = {"Moduły": "Modules", "Domeny": "Domains", "Wymagania": "Requirements", "Reguły": "Rules",
                   "Standardy": "Standards", "Ryzyka": "Risks", "Pytania": "Questions", "Czego nie sprawdzono": "Not checked"}
ROW_ALIASES = {"język": "Language", "dane": "Data", "testy": "Tests", "konfiguracja": "Configuration"}


def canon(heading: str) -> str:
    """Section heading in its English form (Polish from a pre-14.x report → the equivalent)."""
    for pl, en in HEADING_ALIASES.items():
        if heading.startswith(pl):
            return en + heading[len(pl):]
    return heading
CI_FILES = (".github/workflows/*.yml", ".github/workflows/*.yaml", ".gitlab-ci.yml", "Jenkinsfile",
            "azure-pipelines.yml", ".circleci/config.yml", "bitbucket-pipelines.yml", ".travis.yml", ".drone.yml",
            ".buildkite/pipeline.yml")
CARD_MARK = re.compile(r"^<!-- (?:card|karta): \S+ sha256:([0-9a-f]{12}) -->")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def md_files(path: str) -> list[str]:
    if os.path.isdir(path):
        out = []
        for dp, dn, fn in os.walk(path):
            dn[:] = [x for x in dn if x != "raw"]   # raw/: scan results and work orders, not documentation
            out += [os.path.join(dp, f) for f in fn if f.endswith(".md")]
        return sorted(out)
    return [path]


def check_file(md: str, repo: str, cache: dict) -> tuple[int, list[dict], list[dict], list[str], list[tuple], str]:
    """Evidence, bad evidence, claims without evidence, headings, stack table rows (name, line), the Modules section text."""
    refs, bad, unsupported, sections, section = 0, [], [], [], ""
    stack_rows, modules_text, row_at = [], [], None
    with open(md, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for i, line in enumerate(lines, 1):
        h = re.match(r"^#{1,6}\s+(.*)", line)
        if h:
            section = canon(h.group(1).strip())
            sections.append(section)
            continue
        found = [m for m in REF.finditer(line) if not re.match(r"https?$", m.group(1).split("/")[0])]
        for m in found:
            refs += 1
            path, a, b = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
            ref = m.group(0).strip("`")
            full = os.path.join(repo, path)
            if path not in cache:
                try:
                    with open(full, encoding="utf-8", errors="replace") as fh:
                        cache[path] = fh.read().splitlines()
                except OSError:
                    cache[path] = None
            src = cache[path]
            where = f"{md}:{i}"
            if src is None:
                bad.append({"ref": ref, "at": where, "problem": "no such file"})
                continue
            if not (1 <= a <= b <= len(src)):
                bad.append({"ref": ref, "at": where, "problem": f"line outside the file ({len(src)})"})
                continue
            q = QUOTE.search(line[m.end():])
            if q:
                quote = norm(q.group(1) or q.group(2))
                lo, hi = max(1, a - 2), min(len(src), b + 2)
                if quote not in norm(" ".join(src[lo - 1:hi])):
                    bad.append({"ref": ref, "at": where, "problem": f"quote does not match lines {lo}–{hi}"})
        bullet = re.match(r"^\s*([-*]|\d+\.)\s+(.*)", line)
        if bullet and not found and not MARK.search(line) and not any(section.startswith(s) for s in NO_EVIDENCE_SECTIONS):
            unsupported.append({"at": f"{md}:{i}", "text": bullet.group(2).strip()})
        if section.startswith("Modules"):
            modules_text.append(line)
        if section.startswith("Stack") and line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                if stack_rows:   # the row above the separator is the table header
                    stack_rows.pop()
                    if row_at is not None:
                        unsupported[:] = [u for u in unsupported if u["at"] != row_at]
                continue
            stack_rows.append((ROW_ALIASES.get(cells[0].lower(), cells[0]), line))
            row_at = None
            if not found and not MARK.search(line):
                row_at = f"{md}:{i}"
                unsupported.append({"at": row_at, "text": " | ".join(cells)})
    return refs, bad, unsupported, sections, stack_rows, "\n".join(modules_text)


def ci_files(repo: str) -> list[str]:
    """CI pipeline files in the repo (relative paths)."""
    found = {os.path.relpath(p, repo).replace(os.sep, "/") for pat in CI_FILES for p in glob.glob(os.path.join(repo, pat))}
    return sorted(found)


def stale_cards(md: str) -> list[str]:
    """`modules/*.json` cards without `modules/<card>.md` or with an .md generated from older card content."""
    d = os.path.join(os.path.dirname(md), "modules")
    stale = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith(".json"):
            continue
        with open(os.path.join(d, f), "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()[:12]
        try:
            with open(os.path.join(d, f[:-5] + ".md"), encoding="utf-8") as fh:
                m = CARD_MARK.match(fh.readline())
        except OSError:
            m = None
        if not m or m.group(1) != digest:
            stale.append(f[:-5])
    return stale


def module_names(md: str) -> list[str]:
    """Module names from the `modules/*.json` cards next to the report (the `module` field)."""
    d = os.path.join(os.path.dirname(md), "modules")
    names = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".json"):
            try:
                with open(os.path.join(d, f), encoding="utf-8") as fh:
                    names.append(str(json.load(fh).get("module") or f[:-5]))
            except (OSError, ValueError, AttributeError):
                names.append(f[:-5])
    return names


def main(argv: list[str]) -> int:
    repo, as_json, final, paths = ".", False, False, []
    it = iter(argv)
    for a in it:
        if a == "--repo":
            repo = next(it, ".")
        elif a == "--json":
            as_json = True
        elif a == "--final":
            final = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            paths.append(a)
    if not paths or not all(os.path.exists(p) for p in paths) or not os.path.isdir(repo):
        print(f"✗ give an existing report file or directory and --repo (got: {paths}, repo {repo})", file=sys.stderr)
        return 2
    cache, refs, bad, uns, sections = {}, 0, [], [], []
    stack_missing, modules_missing, cards_stale, ci_unreferenced = [], [], [], []
    repo_ci = ci_files(repo) if final else []
    for p in paths:
        for md in md_files(p):
            r, b, u, s, rows, mods = check_file(md, repo, cache)
            refs, bad, uns, sections = refs + r, bad + b, uns + u, sections + s
            if final and any(h.startswith("Stack") for h in s):
                low = [name.lower() for name, _ in rows]
                stack_missing += [w for w in STACK_ROWS if not any(x.startswith(w.lower()) for x in low)]
                ci_row = next((line for name, line in rows if name.lower().startswith("ci")), None)
                if ci_row is not None and repo_ci and not any(f in ci_row for f in repo_ci):
                    ci_unreferenced += repo_ci
            if final and any(h.startswith("Modules") for h in s):
                modules_missing += [m for m in module_names(md) if m not in mods]
                cards_stale += stale_cards(md)
    missing = [s for s in SECTIONS if not any(h.startswith(s) for h in sections)] if final else []
    out = {"refs": refs, "bad": bad, "unsupported": uns, "missing_sections": missing,
           "stack_missing": stack_missing, "modules_missing": modules_missing, "cards_stale": cards_stale,
           "ci_unreferenced": ci_unreferenced}
    failed = bool(bad) or (final and (missing or uns or stack_missing or modules_missing or cards_stale
                                      or ci_unreferenced))
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Evidence: {refs}, bad: {len(bad)}, claims without evidence: {len(uns)}"
              + (f", missing sections: {', '.join(missing)}" if missing else ""))
        if stack_missing:
            print(f"  ✗ stack: missing rows: {', '.join(stack_missing)} (table in the Stack section)")
        if ci_unreferenced:
            print(f"  ✗ CI: the repo has pipeline files, but the CI row points to none of them: {', '.join(ci_unreferenced)}")
        if modules_missing:
            print(f"  ✗ modules with no entry in the Modules section: {', '.join(modules_missing)}")
        if cards_stale:
            print(f"  ✗ cards without an up-to-date .md (recon_cards.py): {', '.join(cards_stale)}")
        for b in bad:
            print(f"  ✗ {b['at']}: `{b['ref']}` — {b['problem']}")
        for u in uns[:30]:
            print(f"  {'✗' if final else '⚠'} {u['at']}: no evidence — {u['text'][:100]}")
        print(("✗" if failed else "✓") + (" final report" if final else " evidence"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
