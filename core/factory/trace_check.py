#!/usr/bin/env python3
"""
Ślad kryterium → test → commit → dowód (krok D osi przebiegu).

  tf trace <KEY> [--base <gałąź>] [--md | --json]

Kryteria `AC-n` bierze z `docs/project/changes/<KEY>/spec.md`. Testu szuka po identyfikatorze `AC-n` w nazwie albo
komentarzu, tylko w plikach testów zmienionych na gałęzi względem bazy (zacommitowanych i roboczych) — identyfikatory
innych zadań się nie mieszają, a `AC-n` w kodzie produkcyjnym testem nie jest. Commit to pierwszy commit gałęzi, który
wprowadził identyfikator do pliku. Dowód to kawałek zadania (`tf task verify`), którego pliki obejmują plik testu,
ze stanem wyliczonym teraz. „Czerwony przed kodem” mówi, czy hook TDD widział ten test jako nieprzechodzący
(zapis w dowodzie kawałka albo w `.tf/logs/tdd-red.jsonl`); „brak zapisu” znaczy tylko, że hook tego nie widział —
np. test uruchomiono poza sesją Claude Code.

Reguły:
  TRACE-001 kryterium bez testu (błąd) · TRACE-002 test wskazuje `AC-n`, którego nie ma w specyfikacji (błąd) ·
  TRACE-003 test nie należy do plików żadnego kawałka — nie ma dowodu, że przeszedł (ostrzeżenie).
Z błędem śladu `tf task stage <KEY> przeglad` (i dalsze etapy) kończy się odmową.

Baza: `--base`, inaczej pierwsza istniejąca z `main`, `origin/main`, `master`, `origin/master`.
Pliki testów: katalogi tests/, test/, __tests__/, e2e/, spec/ oraz nazwy test_*.py, *_test.py, *_test.go, *.test.*,
*.spec.*, *Test.java, *Tests.cs.

Kod wyjścia: 0 — każde kryterium ma test (albo zadanie nie ma specyfikacji); 1 — błędy śladu; 2 — brak repozytorium
git, nieznana baza albo błąd wywołania. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")

CHANGES = Path("docs") / "project" / "changes"
KEY = re.compile(r"[A-Z][A-Z0-9]*-[A-Za-z0-9][A-Za-z0-9-]*")
AC = re.compile(r"\bAC[-_ ]?(\d+)\b", re.I)
TEST = re.compile(r"(^|/)(tests?|__tests__|e2e|spec)/|\.(test|spec)\.|(^|/)test_[^/]*\.py$|_test\.(py|go)$|"
                  r"(Test|Tests)\.(java|cs)$")
BASES = ("main", "origin/main", "master", "origin/master")


def sibling(name: str):
    """Skrypt silnika obok tego pliku jako moduł (task_state, spec_check)."""
    spec = importlib.util.spec_from_file_location(f"tf_{name}", Path(__file__).resolve().with_name(f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(root: Path, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return r.returncode, r.stdout


def find_base(root: Path, base: str | None) -> str | None:
    """Baza porównania; None, gdy katalog nie jest repozytorium git albo bazy nie ma."""
    if git(root, "rev-parse", "--is-inside-work-tree")[0] != 0:
        return None
    for ref in ([base] if base else BASES):
        if git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")[0] == 0:
            return ref
    return None


def changed_tests(root: Path, base: str) -> list[str]:
    """Pliki testów zmienione na gałęzi względem bazy: zacommitowane, zmienione roboczo i nowe nieśledzone."""
    files: set[str] = set()
    for args in (("diff", "--name-only", f"{base}...HEAD"), ("diff", "--name-only", "HEAD"),
                 ("ls-files", "--others", "--exclude-standard")):
        files.update(ln.strip() for ln in git(root, *args)[1].splitlines() if ln.strip())
    return sorted(f for f in files if TEST.search(f) and (root / f).is_file())


def first_commit(root: Path, base: str, rel: str, ident: str) -> str | None:
    """Pierwszy commit gałęzi, który wprowadził identyfikator do pliku; None, gdy zmiana nie jest zacommitowana."""
    out = git(root, "log", "--reverse", "--format=%h", f"-S{ident}", f"{base}..HEAD", "--", rel)[1].split()
    return out[0] if out else None


def trace(root: Path, key: str, base: str | None = None) -> dict | None:
    """Ślad zadania. None, gdy nie da się go policzyć (brak repozytorium git albo bazy). `spec: False`, gdy zadanie
    nie ma specyfikacji."""
    spec = sibling("spec_check").check_task(root, key)
    if spec is None:
        return {"ok": True, "spec": False, "rows": [], "errors": [], "warnings": [], "base": None}
    ref = find_base(root, base)
    if ref is None:
        return None
    ts = sibling("task_state")
    task = ts.load(root, key) or {}
    states = ts.slice_states(root, task)
    owner: dict[str, str] = {}           # plik → kawałek, którego dowód go obejmuje (ostatni wygrywa)
    for sid, sl in (task.get("slices") or {}).items():
        for rel in ((ts.evidence_of(root, key, sl) or {}).get("files") or {}):
            owner[rel] = sid
    red: set[str] = set(ts.red_tests(root, changed := changed_tests(root, ref)))
    for sl in (task.get("slices") or {}).values():
        red.update((ts.evidence_of(root, key, sl) or {}).get("red_tests") or {})
    found: dict[str, list[tuple[str, int]]] = {}
    for rel in changed:
        try:
            lines = (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            for m in AC.finditer(line):
                hits = found.setdefault(f"AC-{int(m.group(1))}", [])
                if not any(f == rel for f, _ in hits):       # jeden wpis na plik: pierwsze wystąpienie
                    hits.append((rel, n))
    errors, warnings, rows = [], [], []
    for ac in spec["criteria"]:
        hits = found.get(ac, [])
        if not hits:
            errors.append({"rule": "TRACE-001", "criterion": ac,
                           "message": f"{ac} nie ma testu — dodaj test z „{ac}” w nazwie albo komentarzu"})
            rows.append({"criterion": ac, "tests": [], "commit": None, "slice": None, "evidence": "brak testu", "red": False})
            continue
        rel = hits[0][0]
        sid = next((owner[f] for f, _ in hits if f in owner), None)
        evidence = states[sid][0] if sid in states else "bez dowodu"
        if sid is None:
            warnings.append({"rule": "TRACE-003", "criterion": ac,
                             "message": f"{ac}: {rel} nie należy do plików żadnego kawałka — dopisz go do `--files` przy "
                                        "weryfikacji kawałka"})
        rows.append({"criterion": ac, "tests": [f"{f}:{n}" for f, n in hits],
                     "commit": first_commit(root, ref, rel, ac), "slice": sid, "evidence": evidence,
                     "red": any(f in red for f, _ in hits)})
    for ac in sorted(set(found) - set(spec["criteria"]), key=lambda a: int(a[3:])):
        rel, n = found[ac][0]
        errors.append({"rule": "TRACE-002", "criterion": ac,
                       "message": f"{rel}:{n} wskazuje {ac}, którego nie ma w specyfikacji — popraw identyfikator albo "
                                  "dopisz kryterium (zmiana wymagań)"})
    return {"ok": not errors, "spec": True, "rows": rows, "errors": errors, "warnings": warnings, "base": ref}


def render_md(rows: list[dict]) -> str:
    out = ["| Kryterium | Test | Czerwony przed kodem | Commit | Dowód |", "|---|---|---|---|---|"]
    for r in rows:
        tests = ", ".join(f"`{t}`" for t in r["tests"]) or "—"
        proof = f"{r['slice']}: {r['evidence']}" if r["slice"] else r["evidence"]
        out.append(f"| {r['criterion']} | {tests} | {'tak' if r.get('red') else 'brak zapisu'} | {r['commit'] or '—'} | {proof} |")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tf trace", description="Ślad kryterium → test → commit → dowód.")
    ap.add_argument("key")
    ap.add_argument("--base", default=None)
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv[1:])
    except SystemExit as e:
        return 2 if e.code else 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not KEY.fullmatch(a.key):
        print(f"✗ klucz „{a.key}” nie pasuje do wzorca (np. PROJ-123, CHG-12, T-20261113-limit)")
        return 2
    result = trace(root, a.key, a.base)
    if result is None:
        print("✗ śladu nie da się policzyć: katalog nie jest repozytorium git albo nie ma bazy porównania "
              f"({a.base or ', '.join(BASES)}) — podaj --base <gałąź>")
        return 2
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 0 if result["ok"] else 1
    if not result["spec"]:
        print(f"Zadanie {a.key} nie ma {CHANGES / a.key / 'spec.md'} — śladu kryteriów nie ma z czego policzyć.")
        return 0
    rows = result["rows"]
    if a.md:
        print(render_md(rows))
    else:
        covered = sum(1 for r in rows if r["tests"])
        print(f"{'✓' if result['ok'] else '✗'} {a.key}: kryteria z testem {covered}/{len(rows)} (baza: {result['base']})")
        for r in rows:
            proof = f"{r['slice']}: {r['evidence']}" if r["slice"] else r["evidence"]
            print(f"  {r['criterion']} → {', '.join(r['tests']) or '—'} → czerwony przed kodem: "
                  f"{'tak' if r.get('red') else 'brak zapisu'} → {r['commit'] or 'niezacommitowany'} → {proof}")
    for e in result["errors"]:
        print(f"✗ {e['rule']}  {e['message']}", file=sys.stderr if a.md else sys.stdout)
    for w in result["warnings"]:
        print(f"⚠ {w['rule']}  {w['message']}", file=sys.stderr if a.md else sys.stdout)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
