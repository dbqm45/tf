#!/usr/bin/env python3
"""
Kontrola dowodów w raporcie z kodu (rekonstrukcja projektu, mapa kodu, dossier): każde `plik:linia` musi wskazywać
istniejący plik i linię, a cytat podany przy dowodzie musi się znaleźć w kodzie (±2 linie). Wypunktowania bez dowodu
i bez oznaczenia [założenie] / [niezweryfikowane] / [pytanie] są zgłaszane jako twierdzenia bez dowodu.

  python3 recon_check.py <plik.md|katalog> [--repo DIR] [--json]
  python3 recon_check.py docs/project/00-reconstruction/report.md --final   # też sekcje raportu i 0 twierdzeń bez dowodu

Dowód: `ścieżka:linia` albo `ścieżka:od-do`; cytat w "…" albo „…” w tym samym wierszu, po dowodzie.
Kod wyjścia: 0 — w porządku, 1 — złe dowody (albo braki przy --final), 2 — złe wywołanie.
"""
from __future__ import annotations

import json
import os
import re
import sys

REF = re.compile(r"`?((?:[\w.@-]+/)*[\w.@-]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`?")
QUOTE = re.compile(r"\"([^\"]{3,})\"|„([^”]{3,})”")
MARK = re.compile(r"\[(założenie|niezweryfikowane|pytanie)[^\]]*\]", re.I)
SECTIONS = ("TL;DR", "Stack", "Moduły", "Domeny", "Wymagania", "Reguły", "Standardy", "Ryzyka", "Pytania",
            "Czego nie sprawdzono")
NO_EVIDENCE_SECTIONS = ("Pytania", "Czego nie sprawdzono")   # tu wypunktowania z natury nie mają dowodu


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def md_files(path: str) -> list[str]:
    if os.path.isdir(path):
        return sorted(os.path.join(dp, f) for dp, _, fn in os.walk(path) for f in fn if f.endswith(".md"))
    return [path]


def check_file(md: str, repo: str, cache: dict) -> tuple[int, list[dict], list[dict], list[str]]:
    refs, bad, unsupported, sections, section = 0, [], [], [], ""
    with open(md, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for i, line in enumerate(lines, 1):
        h = re.match(r"^#{1,6}\s+(.*)", line)
        if h:
            section = h.group(1).strip()
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
                bad.append({"ref": ref, "at": where, "problem": "brak pliku"})
                continue
            if not (1 <= a <= b <= len(src)):
                bad.append({"ref": ref, "at": where, "problem": f"linia poza plikiem ({len(src)})"})
                continue
            q = QUOTE.search(line[m.end():])
            if q:
                quote = norm(q.group(1) or q.group(2))
                lo, hi = max(1, a - 2), min(len(src), b + 2)
                if quote not in norm(" ".join(src[lo - 1:hi])):
                    bad.append({"ref": ref, "at": where, "problem": f"cytat nie pasuje do linii {lo}–{hi}"})
        bullet = re.match(r"^\s*([-*]|\d+\.)\s+(.*)", line)
        if bullet and not found and not MARK.search(line) and not any(section.startswith(s) for s in NO_EVIDENCE_SECTIONS):
            unsupported.append({"at": f"{md}:{i}", "text": bullet.group(2).strip()})
    return refs, bad, unsupported, sections


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
        print(f"✗ podaj istniejący plik lub katalog raportu i --repo (jest: {paths}, repo {repo})", file=sys.stderr)
        return 2
    cache, refs, bad, uns, sections = {}, 0, [], [], []
    for p in paths:
        for md in md_files(p):
            r, b, u, s = check_file(md, repo, cache)
            refs, bad, uns, sections = refs + r, bad + b, uns + u, sections + s
    missing = [s for s in SECTIONS if not any(h.startswith(s) for h in sections)] if final else []
    out = {"refs": refs, "bad": bad, "unsupported": uns, "missing_sections": missing}
    failed = bool(bad) or (final and (missing or uns))
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Dowody: {refs}, złe: {len(bad)}, twierdzenia bez dowodu: {len(uns)}"
              + (f", brak sekcji: {', '.join(missing)}" if missing else ""))
        for b in bad:
            print(f"  ✗ {b['at']}: `{b['ref']}` — {b['problem']}")
        for u in uns[:30]:
            print(f"  {'✗' if final else '⚠'} {u['at']}: bez dowodu — {u['text'][:100]}")
        print(("✗" if failed else "✓") + (" raport końcowy" if final else " dowody"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
