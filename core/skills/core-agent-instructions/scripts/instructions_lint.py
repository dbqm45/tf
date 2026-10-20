#!/usr/bin/env python3
"""Karta kontroli plików instrukcji agenta (CLAUDE.md, AGENTS.md, CLAUDE.local.md, .claude/rules/*.md).

Liczy heurystycznie kontrole, które da się sprawdzić mechanicznie; ocenę treści (wiedza zbędna, sens reguł)
robi agent wg skilla core-agent-instructions.

  python3 instructions_lint.py CLAUDE.md                 # jeden lub kilka plików
  python3 instructions_lint.py --root .                  # wszystkie pliki instrukcji w repo + indeks i duplikaty
  python3 instructions_lint.py --root . --json           # wynik maszynowy
  python3 instructions_lint.py CLAUDE.md --warn 150 --error 300

Kontrole na plik:
  dlugosc   niepuste linie bez komentarzy HTML (Claude Code je usuwa): OK ≤ warn, UWAGA ≤ error, BŁĄD > error
  bloki     bloki ``` dłuższe niż 3 linie (bez mermaid): OK 0, UWAGA 1–2, BŁĄD ≥ 3
  intencje  sformułowania-intencje („pisz czysty kod”, „best practices”): OK 0, UWAGA 1–3, BŁĄD ≥ 4
  kolejnosc pierwsza reguła krytyczna (nigdy/zawsze/never/must…) w pierwszej trzeciej pliku; BŁĄD, gdy dopiero
            po linii 200 albo gdy plik > 30 linii nie ma nagłówków
  importy   importy @ścieżka (poza `kodem`): brakujące pliki, długość z importami (importy ładują się przy starcie)
Tryb --root dodatkowo: zagnieżdżone CLAUDE.md/AGENTS.md niewymienione w pliku głównym (indeks) i linie
skopiowane z pliku głównego do pliku modułu.

Kod wyjścia: 0 — brak BŁĘDÓW; 1 — co najmniej jeden BŁĄD (z --strict także UWAGA); 2 — błąd wywołania.
Tylko odczyt plików, bez sieci.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

NAMES = {"CLAUDE.md", "AGENTS.md", "CLAUDE.local.md"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage", ".venv", "venv", "__pycache__", "vendor", "target"}
INTENTS = [
    r"czyst\w* kod", r"dobr\w* praktyk", r"dba[jć]\w* o (jakość|czytelność|porządek|bezpieczeństwo)",
    r"b[ąa]d[źz] spójn", r"pisz czyteln", r"czytelny kod", r"wysok\w* jakoś", r"zgodnie ze sztuką",
    r"clean code", r"best practices?", r"write (clean|readable|maintainable|good) code", r"be consistent",
    r"high[- ]quality code", r"follow (good|the) conventions",
]
INTENT_RE = re.compile("|".join(INTENTS), re.IGNORECASE)
CRITICAL_RE = re.compile(r"(?i:\b(nigdy|zawsze|nie wolno|zakaz\w*|never|always|must|do not|don't)\b)|\bNIE\b")
INTRO_RE = re.compile(r"^#+\s*(o projekcie|wstęp|wprowadzenie|misja|wartości|about|overview|introduction|mission)\b",
                      re.IGNORECASE)
IMPORT_RE = re.compile(r"(?<![\w`/])@((?:~/|\.{1,2}/|/)?[\w.\-][\w.\-/]*(?:\\ [\w.\-/]+)*)")
EXCLUDED_LANGS = {"mermaid"}


def strip_comments(lines):
    """Usuwa blokowe komentarze HTML poza blokami kodu (Claude Code nie wstrzykuje ich do kontekstu)."""
    out, in_comment, in_fence = [], False, False
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not in_comment and s.startswith("```"):
            in_fence = not in_fence
            out.append((i, line))
            continue
        if in_fence:
            out.append((i, line))
            continue
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if s.startswith("<!--"):
            if "-->" not in s:
                in_comment = True
            continue
        out.append((i, line))
    return out


def verdict(value, warn, error):
    return "OK" if value <= warn else ("UWAGA" if value <= error else "BŁĄD")


def fences(numbered):
    """Bloki ``` jako (linia_startu, język, liczba_linii_treści)."""
    res, start, lang, count = [], None, "", 0
    for i, line in numbered:
        s = line.strip()
        if s.startswith("```"):
            if start is None:
                start, lang, count = i, s[3:].strip().split(" ")[0].lower(), 0
            else:
                res.append((start, lang, count))
                start = None
        elif start is not None:
            count += 1
    return res


def prose_lines(numbered):
    """Linie poza blokami kodu, z usuniętymi fragmentami `kodu`."""
    out, in_fence = [], False
    for i, line in numbered:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i, re.sub(r"`[^`]*`", "", line)))
    return out


def check_file(path: Path, warn: int, error: int):
    text = path.read_text(encoding="utf-8", errors="replace")
    raw = text.splitlines()
    # frontmatter reguły (.claude/rules) nie trafia do kontekstu
    if raw and raw[0].strip() == "---":
        end = next((k for k in range(1, len(raw)) if raw[k].strip() == "---"), None)
        if end is not None:
            raw = [""] * (end + 1) + raw[end + 1:]
    numbered = strip_comments(raw)
    nonempty = [(i, l) for i, l in numbered if l.strip()]
    n = len(nonempty)
    checks = []

    checks.append({"id": "dlugosc", "value": n, "verdict": verdict(n, warn, error),
                   "detail": f"{n} niepustych linii (próg {warn}/{error})"})

    long_blocks = [(s, lang, c) for s, lang, c in fences(numbered) if c > 3 and lang not in EXCLUDED_LANGS]
    checks.append({"id": "bloki", "value": len(long_blocks), "verdict": verdict(len(long_blocks), 0, 2),
                   "findings": [{"line": s, "text": f"blok {lang or 'bez języka'}, {c} linii"} for s, lang, c in long_blocks],
                   "detail": "bloki kodu/konfiguracji > 3 linii — zamień na odnośnik do pliku"})

    prose = prose_lines(numbered)
    intents = [(i, m.group(0)) for i, l in prose for m in [INTENT_RE.search(l)] if m]
    checks.append({"id": "intencje", "value": len(intents), "verdict": verdict(len(intents), 0, 3),
                   "findings": [{"line": i, "text": t} for i, t in intents],
                   "detail": "intencje → zachowanie sprawdzalne w diffie albo usuń"})

    headings = [(i, l) for i, l in prose if re.match(r"^#{1,6}\s", l)]
    critical = [i for i, l in prose if CRITICAL_RE.search(l)]
    pos = {i: k for k, (i, _) in enumerate(nonempty, 1)}  # numer linii pliku → pozycja wśród niepustych
    findings = []
    if n > 30 and not headings:
        v = "BŁĄD"
        findings.append({"line": 1, "text": "brak nagłówków w pliku dłuższym niż 30 linii"})
    elif not critical:
        v = "OK"
    else:
        first = pos.get(critical[0], critical[0])
        late = [i for i in critical if pos.get(i, i) > 200]
        if late and first > 200:
            v = "BŁĄD"
        elif first <= max(10, n / 3) and not late:
            v = "OK"
        else:
            v = "UWAGA"
        for i in late:
            findings.append({"line": i, "text": "reguła krytyczna po 200. linii — przenieś na górę"})
        if first > max(10, n / 3):
            findings.append({"line": critical[0], "text": "pierwsza reguła krytyczna poza pierwszą trzecią pliku"})
    if headings and INTRO_RE.match(headings[0][1]) and v == "OK":
        v = "UWAGA"
    if headings and INTRO_RE.match(headings[0][1]):
        findings.append({"line": headings[0][0], "text": "plik zaczyna się wstępem — zakazy i polecenia przed opisem"})
    checks.append({"id": "kolejnosc", "value": critical[0] if critical else 0, "verdict": v, "findings": findings,
                   "detail": "krytyczne reguły w pierwszej trzeciej, bez wstępu na górze",
                   "headings": [{"line": i, "text": l.strip()} for i, l in headings]})

    imports, effective = [], n
    for i, l in prose:
        for m in IMPORT_RE.finditer(l):
            target = m.group(1).replace("\\ ", " ").rstrip(".,;:)")
            if "/" not in target and "." not in target:
                continue  # @nazwa (np. wzmianka) — nie ścieżka
            if target.startswith("~/"):
                imports.append({"line": i, "target": target, "external": True})
                continue
            dest = Path(target) if target.startswith("/") else path.parent / target
            if dest.is_file():
                extra = sum(1 for x in dest.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip())
                effective += extra
                imports.append({"line": i, "target": target, "lines": extra})
            else:
                imports.append({"line": i, "target": target, "missing": True})
    missing = [x for x in imports if x.get("missing")]
    checks.append({"id": "importy", "value": len(imports), "verdict": "UWAGA" if missing else "OK",
                   "findings": imports, "effective_lines": effective,
                   "detail": f"długość z importami: {effective} (importy ładują się przy starcie — nie oszczędzają kontekstu)"})
    return {"path": str(path), "checks": checks}


def discover(root: Path):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        rel = Path(dirpath).relative_to(root)
        for f in sorted(filenames):
            p = Path(dirpath) / f
            if f in NAMES or (f.endswith(".md") and "rules" in rel.parts and ".claude" in rel.parts):
                found.append(p)
    return found


def norm(line):
    return re.sub(r"\s+", " ", line.strip().lstrip("-*0123456789. ")).lower()


def repo_checks(root: Path, files):
    main = next((root / n for n in ("CLAUDE.md", ".claude/CLAUDE.md", "AGENTS.md") if (root / n).is_file()), None)
    res = {"plik_glowny": str(main.relative_to(root)) if main else None, "poza_indeksem": [], "duplikaty": []}
    if not main:
        return res
    main_text = main.read_text(encoding="utf-8", errors="replace")
    main_lines = {norm(l): l.strip() for l in main_text.splitlines() if len(norm(l)) >= 20}
    for f in files:
        rel = f.relative_to(root)
        if f.name not in ("CLAUDE.md", "AGENTS.md") or len(rel.parts) == 1 or rel.parts[0] == ".claude":
            continue
        rel_s = rel.as_posix()
        if rel_s not in main_text and rel.parent.as_posix() + "/" not in main_text:
            res["poza_indeksem"].append(rel_s)
        for k, l in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if norm(l) in main_lines:
                res["duplikaty"].append({"plik": rel_s, "line": k, "text": l.strip()})
    return res


def worst(results, strict):
    bad = {"BŁĄD"} | ({"UWAGA"} if strict else set())
    return any(c["verdict"] in bad for r in results for c in r["checks"])


def render(results, repo, root):
    out = []
    for r in results:
        shown = Path(r["path"])
        if root:
            try:
                shown = shown.relative_to(root)
            except ValueError:
                pass
        out.append(f"Przegląd instrukcji — {shown.as_posix()}")
        out.append(f"  {'kontrola':<10} {'werdykt':<7} szczegóły")
        for c in r["checks"]:
            out.append(f"  {c['id']:<10} {c['verdict']:<7} {c['detail']}")
            for f in c.get("findings", [])[:10]:
                label = f.get("text") or f.get("target", "")
                if f.get("missing"):
                    label += " — brak pliku"
                if f.get("external"):
                    label += " — import spoza repo (wymaga zgody przy starcie)"
                out.append(f"      l.{f.get('line', '?')}: {label}")
        out.append("")
    if repo is not None:
        out.append(f"Repozytorium — plik główny: {repo['plik_glowny'] or 'brak'}")
        for p in repo["poza_indeksem"]:
            out.append(f"  UWAGA {p}: niewymieniony w pliku głównym (dopisz do sekcji „Moduły z własnym CLAUDE.md”)")
        for d in repo["duplikaty"]:
            out.append(f"  UWAGA {d['plik']}:{d['line']}: kopia reguły z pliku głównego — {d['text'][:80]}")
        if not repo["poza_indeksem"] and not repo["duplikaty"]:
            out.append("  OK indeks i brak kopii reguł")
    out.append("Ocenę wiedzy zbędnej (kontrola 4) i sensu reguł zrób ręcznie wg skilla core-agent-instructions.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("files", nargs="*", help="pliki instrukcji do sprawdzenia")
    ap.add_argument("--root", help="katalog repo: znajdź wszystkie pliki instrukcji i sprawdź indeks oraz duplikaty")
    ap.add_argument("--warn", type=int, default=200, help="próg UWAGA długości (domyślnie 200)")
    ap.add_argument("--error", type=int, default=500, help="próg BŁĄD długości (domyślnie 500)")
    ap.add_argument("--strict", action="store_true", help="kod 1 także przy UWAGA")
    ap.add_argument("--json", action="store_true", help="wynik w JSON")
    a = ap.parse_args(argv)
    if not a.files and not a.root:
        ap.print_usage(sys.stderr)
        print("podaj plik(i) albo --root", file=sys.stderr)
        return 2
    root = Path(a.root).resolve() if a.root else None
    if root and not root.is_dir():
        print(f"brak katalogu: {root}", file=sys.stderr)
        return 2
    paths = [Path(f) for f in a.files]
    for p in paths:
        if not p.is_file():
            print(f"brak pliku: {p}", file=sys.stderr)
            return 2
    if root:
        paths += [p for p in discover(root) if p.resolve() not in {x.resolve() for x in paths}]
    results = [check_file(p, a.warn, a.error) for p in paths]
    repo = repo_checks(root, [p.resolve() for p in paths]) if root else None
    if a.json:
        print(json.dumps({"files": results, "repo": repo}, ensure_ascii=False, indent=2))
    else:
        print(render(results, repo, root))
    return 1 if worst(results, a.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
