#!/usr/bin/env python3
"""
Skaner reguł deklaratywnych dla `tf analyze` (piętro 0, bez modelu i sieci): standardy zapisane w pliku YAML zamiast
w skrypcie. Moduł analizy ustawia w `analyzer.yaml` pole `tier0.rules: rules.yaml` — wtedy analyze.py uruchamia ten
skaner zamiast `tier0.script`. Nakładka firmowa dostarcza tylko reguły i przykłady do bramki; poprawki skanera
przychodzą z aktualizacją fabryki.

  python3 .tf/factory/rules_scan.py --rules <rules.yaml> --root <repo> [--files a,b]   # JSON Lines na stdout

Format reguły (lista `rules`):
  id          małe litery, cyfry i „-” (np. no-print)                  — wymagane
  title       krótki opis naruszenia                                   — wymagane
  files       wzorce ścieżek (`**` dowolne katalogi, `*` w nazwie)    — domyślnie wszystkie pliki
  exclude     wzorce ścieżek pomijanych
  forbid      wyrażenie regularne zakazane w linii — ustalenie na każdej pasującej linii
  require     wyrażenie regularne wymagane w pliku (albo w pierwszych `head` liniach) — ustalenie w linii 1, gdy go brak
  head        liczba linii dla `require` (domyślnie cały plik)
  severity    krytyczna | wysoka | średnia | niska (domyślnie średnia)
  suggestion  co zrobić;  basis — źródło reguły (np. dokument firmowy)
Dokładnie jedno z `forbid` i `require`. Błędna reguła → kod 2 i opis na stderr, bez częściowego wyniku.
Pomijane: zależności i wyniki budowania (node_modules, dist, build, .venv…), pliki fabryki (.tf/, .claude/), pliki
binarne i większe niż 1 MB. Tylko biblioteka standardowa + PyYAML (systemowy albo dołączony w .tf/factory/_vendor).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne też piszą i czytają UTF-8

try:
    import yaml
except ImportError:  # dołączona kopia PyYAML (licencja MIT, .tf/factory/_vendor/yaml/LICENSE)
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
    import yaml

SEVERITY = ("krytyczna", "wysoka", "średnia", "niska")
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage", ".venv", "venv", "__pycache__", ".tf", ".claude",
             ".next", "target", "_vendor", "vendor", "third_party"}
MAX_BYTES = 1_000_000
ID_RE = re.compile(r"[a-z0-9][a-z0-9-]*")


class RuleError(ValueError):
    pass


def glob_re(pattern: str) -> re.Pattern:
    """Wzorzec ścieżki → wyrażenie: `**/` dowolne katalogi (także żadne), `**` cokolwiek, `*` i `?` w jednym członie."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def load_rules(path: Path) -> list[dict]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        raise RuleError(f"{path}: nie da się wczytać reguł ({e})") from e
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, list):
        raise RuleError(f"{path}: brak listy `rules`")
    out, seen = [], set()
    for n, r in enumerate(rules, 1):
        if not isinstance(r, dict):
            raise RuleError(f"reguła {n}: to nie słownik")
        rid = str(r.get("id") or "")
        where = f"reguła {rid or n}"
        if not ID_RE.fullmatch(rid):
            raise RuleError(f"{where}: id — małe litery, cyfry i „-” (jest {rid!r})")
        if rid in seen:
            raise RuleError(f"{where}: powtórzone id")
        seen.add(rid)
        if not r.get("title"):
            raise RuleError(f"{where}: brak title")
        if bool(r.get("forbid")) == bool(r.get("require")):
            raise RuleError(f"{where}: podaj dokładnie jedno z forbid i require")
        sev = r.get("severity", "średnia")
        if sev not in SEVERITY:
            raise RuleError(f"{where}: severity — {' | '.join(SEVERITY)} (jest {sev!r})")
        try:
            pattern = re.compile(str(r.get("forbid") or r.get("require")))
        except re.error as e:
            raise RuleError(f"{where}: złe wyrażenie regularne ({e})") from e
        head = r.get("head")
        if head is not None and (not isinstance(head, int) or head < 1):
            raise RuleError(f"{where}: head — liczba linii ≥ 1")
        out.append({**r, "id": rid, "severity": sev, "_re": pattern, "_mode": "forbid" if r.get("forbid") else "require",
                    "_files": [glob_re(g) for g in (r.get("files") or ["**"])],
                    "_exclude": [glob_re(g) for g in (r.get("exclude") or [])]})
    return out


def repo_files(root: Path) -> list[str]:
    out = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]) or not p.is_file():
            continue
        out.append(rel.as_posix())
    return out


def read_text(p: Path) -> str | None:
    try:
        if p.stat().st_size > MAX_BYTES:
            return None
        data = p.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", errors="replace")


def finding(r: dict, rel: str, line: int, snippet: str) -> dict:
    evidence = snippet if r["_mode"] == "forbid" else f"brak wzorca {r['_re'].pattern!r}" + (
        f" w pierwszych {r['head']} liniach" if r.get("head") else "")
    return {"rule": r["id"], "title": r["title"], "file": rel, "line": line, "snippet": snippet[:200],
            "severity": r["severity"], "confidence": 1.0, "evidence": evidence,
            "basis": r.get("basis") or "reguła z rules.yaml", "suggestion": r.get("suggestion") or ""}


def scan(rules: list[dict], root: Path, files: list[str]) -> list[dict]:
    out = []
    for rel in files:
        wanted = [r for r in rules if any(g.match(rel) for g in r["_files"]) and not any(g.match(rel) for g in r["_exclude"])]
        if not wanted:
            continue
        text = read_text(root / rel)
        if text is None:
            continue
        lines = text.splitlines()
        for r in wanted:
            if r["_mode"] == "forbid":
                out += [finding(r, rel, i, line.strip()) for i, line in enumerate(lines, 1) if r["_re"].search(line)]
            elif not r["_re"].search("\n".join(lines[:r["head"]] if r.get("head") else lines)):
                out.append(finding(r, rel, 1, lines[0].strip() if lines else ""))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Reguły deklaratywne tf analyze (rules.yaml) — JSON Lines na stdout")
    ap.add_argument("--rules", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--files", default=None)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    try:
        rules = load_rules(Path(a.rules))
    except RuleError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    files = [f for f in (a.files or "").split(",") if f] if a.files is not None else repo_files(root)
    files = [f for f in files if not any(part in SKIP_DIRS for part in Path(f).parts[:-1])]
    for f in scan(rules, root, files):
        print(json.dumps(f, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
