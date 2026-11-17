#!/usr/bin/env python3
"""Karta kontroli plików instrukcji agenta (CLAUDE.md, AGENTS.md, CLAUDE.local.md, .claude/rules/*.md).

Liczy heurystycznie kontrole, które da się sprawdzić mechanicznie; ocenę treści (wiedza zbędna, sens reguł)
robi agent wg skilla core-agent-instructions.

  python3 instructions_lint.py CLAUDE.md                 # jeden lub kilka plików
  python3 instructions_lint.py --root .                  # wszystkie pliki instrukcji w repo + indeks i duplikaty
  python3 instructions_lint.py --root . --json           # wynik maszynowy
  python3 instructions_lint.py CLAUDE.md --warn 150 --error 300

Kontrole na plik:
  length    niepuste linie bez komentarzy HTML (Claude Code je usuwa): OK ≤ warn, WARN ≤ error, ERROR > error
  blocks    bloki ``` dłuższe niż 3 linie (bez mermaid): OK 0, WARN 1–2, ERROR ≥ 3
  intents   sformułowania-intencje („pisz czysty kod”, „best practices”): OK 0, WARN 1–3, ERROR ≥ 4
  order     pierwsza reguła krytyczna (nigdy/zawsze/never/must…) w pierwszej trzeciej pliku; ERROR, gdy dopiero
            po linii 200 albo gdy plik > 30 linii nie ma nagłówków
  imports   importy @ścieżka (poza `kodem`): brakujące pliki, długość z importami (importy ładują się przy starcie)
  stale     odwołania w `kodzie`, których w repozytorium już nie ma: ścieżki plików i katalogów, `npm run <skrypt>`
            bez skryptu w package.json, `make <cel>` bez celu w Makefile: OK 0, WARN ≥ 1 (blok fabryki
            `<!-- team-factory:begin/end -->` pominięty — jest wspólny dla wszystkich projektów)
Tryb --root dodatkowo: zagnieżdżone CLAUDE.md/AGENTS.md niewymienione w pliku głównym (indeks) i linie
skopiowane z pliku głównego do pliku modułu.

Kod wyjścia: 0 — brak ERROR; 1 — co najmniej jeden ERROR (z --strict także WARN); 2 — błąd wywołania.
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
SPAN_RE = re.compile(r"`([^`\n]+)`")
NEGATIVE_RE = re.compile(r"(?i)\b(nie czytaj|nie zmieniaj|nie edytuj|nie commituj|pomijaj|ignor\w*|skip|never|don't|do not)\b")
ON_DEMAND = ("docs/project/", ".tf/", ".claude/")   # katalogi fabryki tworzone, gdy są potrzebne
FACTORY_BLOCK = ("<!-- team-factory:begin -->", "<!-- team-factory:end -->")


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
    return "OK" if value <= warn else ("WARN" if value <= error else "ERROR")


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


def outside_factory_block(raw):
    """Numery linii poza blokiem fabryki (`<!-- team-factory:begin -->` … `<!-- team-factory:end -->`)."""
    keep, inside = set(), False
    for i, line in enumerate(raw, 1):
        s = line.strip()
        if s == FACTORY_BLOCK[0]:
            inside = True
        elif s == FACTORY_BLOCK[1]:
            inside = False
        elif not inside:
            keep.add(i)
    return keep


def manifest_names(root: Path):
    """Skrypty package.json i cele Makefile w katalogu głównym; None, gdy pliku nie ma (nie ma czego sprawdzać)."""
    try:
        scripts = json.loads((root / "package.json").read_text(encoding="utf-8")).get("scripts")
        npm = set(scripts) if isinstance(scripts, dict) else set()
    except (OSError, ValueError, AttributeError):
        npm = None
    try:
        make = set(re.findall(r"(?m)^([A-Za-z0-9][\w.\-]*)\s*:(?!=)", (root / "Makefile").read_text(encoding="utf-8")))
    except OSError:
        make = None
    return npm, make


def stale_refs(numbered, keep, path: Path, root: Path):
    """Odwołania w `kodzie` do ścieżek, skryptów npm i celów make, których nie ma. Heurystyka: pomija wzorce, adresy,
    opcje, ścieżki bezwzględne, same nazwy plików (bez `/`), katalogi fabryki tworzone na żądanie i linie z zakazem
    („nie czytaj `dist/`” — taki katalog może nie istnieć)."""
    npm, make = manifest_names(root)
    out, in_fence = [], False
    for i, line in numbered:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or i not in keep or NEGATIVE_RE.search(line):
            continue
        for m in SPAN_RE.finditer(line):
            span = m.group(1).strip()
            words = span.split()
            if len(words) >= 2 and words[0] in ("npm", "pnpm") and npm is not None:
                name = words[2] if words[1] in ("run", "run-script") and len(words) > 2 else words[1]
                if words[1] in ("run", "run-script", "test", "start") and name not in npm and not name.startswith("-"):
                    out.append({"line": i, "text": f"{span} — package.json has no script \"{name}\""})
                continue
            if len(words) == 2 and words[0] == "make" and make is not None and not words[1].startswith("-"):
                if words[1] not in make:
                    out.append({"line": i, "text": f"{span} — Makefile has no target \"{words[1]}\""})
                continue
            if len(words) != 1 or "://" in span or re.search(r"[<>{}*?$|=:@\\]", span) or span.startswith(("-", "/", "~")):
                continue                      # polecenie, adres, wzorzec, opcja albo ścieżka spoza repozytorium
            target = span.rstrip(".,;)")
            if "/" not in target or target.startswith(ON_DEMAND) or target.lstrip("./").startswith(ON_DEMAND):
                continue
            if (root / target).exists() or (path.parent / target).exists():
                continue
            out.append({"line": i, "text": f"{target} — no such path"})
    return out


def check_file(path: Path, warn: int, error: int, root: Path | None = None):
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

    checks.append({"id": "length", "value": n, "verdict": verdict(n, warn, error),
                   "detail": f"{n} non-empty lines (threshold {warn}/{error})"})

    long_blocks = [(s, lang, c) for s, lang, c in fences(numbered) if c > 3 and lang not in EXCLUDED_LANGS]
    checks.append({"id": "blocks", "value": len(long_blocks), "verdict": verdict(len(long_blocks), 0, 2),
                   "findings": [{"line": s, "text": f"block {lang or 'without language'}, {c} lines"} for s, lang, c in long_blocks],
                   "detail": "code/config blocks > 3 lines — replace them with a link to a file"})

    prose = prose_lines(numbered)
    intents = [(i, m.group(0)) for i, l in prose for m in [INTENT_RE.search(l)] if m]
    checks.append({"id": "intents", "value": len(intents), "verdict": verdict(len(intents), 0, 3),
                   "findings": [{"line": i, "text": t} for i, t in intents],
                   "detail": "intentions → behaviour you can check in a diff, or remove them"})

    headings = [(i, l) for i, l in prose if re.match(r"^#{1,6}\s", l)]
    critical = [i for i, l in prose if CRITICAL_RE.search(l)]
    pos = {i: k for k, (i, _) in enumerate(nonempty, 1)}  # numer linii pliku → pozycja wśród niepustych
    findings = []
    if n > 30 and not headings:
        v = "ERROR"
        findings.append({"line": 1, "text": "no headings in a file longer than 30 lines"})
    elif not critical:
        v = "OK"
    else:
        first = pos.get(critical[0], critical[0])
        late = [i for i in critical if pos.get(i, i) > 200]
        if late and first > 200:
            v = "ERROR"
        elif first <= max(10, n / 3) and not late:
            v = "OK"
        else:
            v = "WARN"
        for i in late:
            findings.append({"line": i, "text": "critical rule after line 200 — move it to the top"})
        if first > max(10, n / 3):
            findings.append({"line": critical[0], "text": "the first critical rule is outside the first third of the file"})
    if headings and INTRO_RE.match(headings[0][1]) and v == "OK":
        v = "WARN"
    if headings and INTRO_RE.match(headings[0][1]):
        findings.append({"line": headings[0][0], "text": "the file starts with an introduction — put bans and commands before the description"})
    checks.append({"id": "order", "value": critical[0] if critical else 0, "verdict": v, "findings": findings,
                   "detail": "critical rules in the first third, no introduction at the top",
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
    checks.append({"id": "imports", "value": len(imports), "verdict": "WARN" if missing else "OK",
                   "findings": imports, "effective_lines": effective,
                   "detail": f"length with imports: {effective} (imports load at startup — they do not save context)"})
    stale = stale_refs(numbered, outside_factory_block(raw), path, root or path.parent)
    checks.append({"id": "stale", "value": len(stale), "verdict": "WARN" if stale else "OK", "findings": stale,
                   "detail": "references to files and commands that do not exist — fix or remove the entry"})
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
    res = {"main_file": str(main.relative_to(root)) if main else None, "unindexed": [], "duplicates": []}
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
            res["unindexed"].append(rel_s)
        for k, l in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if norm(l) in main_lines:
                res["duplicates"].append({"file": rel_s, "line": k, "text": l.strip()})
    return res


def worst(results, strict):
    bad = {"ERROR"} | ({"WARN"} if strict else set())
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
        out.append(f"Instruction review — {shown.as_posix()}")
        out.append(f"  {'check':<10} {'verdict':<7} details")
        for c in r["checks"]:
            out.append(f"  {c['id']:<10} {c['verdict']:<7} {c['detail']}")
            for f in c.get("findings", [])[:10]:
                label = f.get("text") or f.get("target", "")
                if f.get("missing"):
                    label += " — file not found"
                if f.get("external"):
                    label += " — import from outside the repo (needs approval at startup)"
                out.append(f"      l.{f.get('line', '?')}: {label}")
        out.append("")
    if repo is not None:
        out.append(f"Repository — main file: {repo['main_file'] or 'none'}")
        for p in repo["unindexed"]:
            out.append(f"  WARN {p}: not listed in the main file (add it to the \"Modules with their own CLAUDE.md\" section)")
        for d in repo["duplicates"]:
            out.append(f"  WARN {d['file']}:{d['line']}: copy of a rule from the main file — {d['text'][:80]}")
        if not repo["unindexed"] and not repo["duplicates"]:
            out.append("  OK index and no copied rules")
    out.append("Assess unneeded knowledge (check 4) and the sense of the rules by hand, as the core-agent-instructions skill says.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("files", nargs="*", help="instruction files to check")
    ap.add_argument("--root", help="repo directory: find all instruction files and check the index and duplicates")
    ap.add_argument("--warn", type=int, default=200, help="WARN length threshold (default 200)")
    ap.add_argument("--error", type=int, default=500, help="ERROR length threshold (default 500)")
    ap.add_argument("--strict", action="store_true", help="exit code 1 also on WARN")
    ap.add_argument("--json", action="store_true", help="output as JSON")
    a = ap.parse_args(argv)
    if not a.files and not a.root:
        ap.print_usage(sys.stderr)
        print("give file(s) or --root", file=sys.stderr)
        return 2
    root = Path(a.root).resolve() if a.root else None
    if root and not root.is_dir():
        print(f"directory not found: {root}", file=sys.stderr)
        return 2
    paths = [Path(f) for f in a.files]
    for p in paths:
        if not p.is_file():
            print(f"file not found: {p}", file=sys.stderr)
            return 2
    if root:
        paths += [p for p in discover(root) if p.resolve() not in {x.resolve() for x in paths}]
    results = [check_file(p, a.warn, a.error, root) for p in paths]
    repo = repo_checks(root, [p.resolve() for p in paths]) if root else None
    if a.json:
        print(json.dumps({"files": results, "repo": repo}, ensure_ascii=False, indent=2))
    else:
        print(render(results, repo, root))
    return 1 if worst(results, a.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
