#!/usr/bin/env python3
"""
Standard repozytorium w jednym wyniku: czy projekt trzyma to, czego fabryka oczekuje od repo dla agentów.

  python3 .tf/factory/standard.py                    # tabela kontroli i werdykt
  python3 .tf/factory/standard.py --json             # wynik maszynowy (np. dla CI)
  python3 .tf/factory/standard.py --strict           # kod 1 także przy ostrzeżeniach
  python3 .tf/factory/standard.py --only journal,instructions
  --root <katalog projektu>

Niczego nowego nie ocenia — zbiera istniejące kontrole fabryki:
  install       `.tf/factory/build.py check` — instalacja, wersje, odwołania, lista zatwierdzonych modeli
  journal       dziennik projektu `docs/project/` (`.claude/hooks/project_record.py`: nagłówki, TL;DR, Przekazanie)
  instructions  pliki instrukcji agenta (CLAUDE.md, AGENTS.md; `core-agent-instructions/scripts/instructions_lint.py`)
  readiness     gotowość repo dla agentów (`eng-repo-readiness/scripts/readiness_check.py`, pack-it; bez niej pominięta)
  hooks         czy hooki fabryki działały przy ostatnich commitach (`.tf/factory/hooks_status.py`)

Status kontroli: ok, warn, fail albo skip (nie dotyczy). Werdykt to najgorszy status. Kod wyjścia: 0 — brak `fail`
(ze `--strict` także brak `warn`); 1 — jest; 2 — błąd wywołania. Kontrole tylko czytają pliki; `install` uruchamia
`build.py check`. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne (build.py, testy, hooki) też piszą i czytają UTF-8

sys.dont_write_bytecode = True   # silnik w .tf/factory/ bez __pycache__ (jak node_modules — tylko kod)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RANK = {"skip": 0, "ok": 0, "warn": 1, "fail": 2}
MARK = {"ok": "✓", "warn": "⚠", "fail": "✗", "skip": "·"}
DETAILS_MAX = 20   # tyle szczegółów na kontrolę w wyniku; reszta jako licznik


def result(check_id: str, status: str, summary: str, details: list[str] | None = None) -> dict:
    details = [str(d) for d in (details or [])]
    more = len(details) - DETAILS_MAX
    return {"id": check_id, "status": status, "summary": summary,
            "details": details[:DETAILS_MAX] + ([f"… i {more} kolejnych"] if more > 0 else [])}


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env={**os.environ, "CLAUDE_PROJECT_DIR": str(cwd)})


def check_install(root: Path) -> dict:
    build = root / ".tf" / "factory" / "build.py"
    if not build.is_file():
        return result("install", "fail", "brak .tf/factory/build.py — fabryka nie jest zainstalowana (tf install)")
    r = _run(build, "check", cwd=root)
    errors = [ln[2:] for ln in r.stdout.splitlines() if ln.startswith("✗ ") and not ln.endswith("błędów")]
    if r.returncode != 0:
        return result("install", "fail", f"build.py check: {len(errors) or 1} błędów (szczegóły: tf doctor)",
                      errors or [(r.stderr or r.stdout).strip()[-300:]])
    return result("install", "ok", "build.py check bez błędów")


def check_journal(root: Path) -> dict:
    script = root / ".claude" / "hooks" / "project_record.py"
    if not script.is_file():
        return result("journal", "skip", "brak .claude/hooks/project_record.py — instalacja bez hooków rdzenia")
    pr = _module(script, "tf_standard_project_record")
    rec = pr.record_dir(root)
    if not rec.exists():
        return result("journal", "fail", f"brak {rec.relative_to(root).as_posix()}/ — dziennik projektu nie istnieje "
                                         f"(python3 .claude/hooks/project_record.py init)")
    errors, warnings = pr.check(root)   # tylko odczyt; indeks przebudowuje dopiero `project_record.py check`
    if errors:
        return result("journal", "fail", f"dziennik projektu: {len(errors)} błędów (python3 .claude/hooks/"
                                         f"project_record.py check)", errors + [f"(ostrzeżenie) {w}" for w in warnings])
    if warnings:
        return result("journal", "warn", f"dziennik projektu poprawny, {len(warnings)} ostrzeżeń", warnings)
    return result("journal", "ok", "dziennik projektu poprawny")


def check_instructions(root: Path) -> dict:
    lint = root / ".claude" / "skills" / "core-agent-instructions" / "scripts" / "instructions_lint.py"
    names = ("CLAUDE.md", "AGENTS.md", "CLAUDE.local.md")
    if not any((root / n).is_file() for n in names):
        return result("instructions", "fail", "brak pliku instrukcji agenta w katalogu głównym (CLAUDE.md albo AGENTS.md)")
    if not lint.is_file():
        return result("instructions", "ok", "plik instrukcji jest; karta kontroli niedostępna (brak core-agent-instructions)")
    r = _run(lint, "--root", str(root), "--json", cwd=root)
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return result("instructions", "warn", "instructions_lint.py nie zwrócił wyniku", [(r.stderr or r.stdout).strip()[-300:]])
    bad, soft = [], []
    for f in data.get("files") or []:
        rel = os.path.relpath(f.get("path", "?"), root).replace("\\", "/")
        for c in f.get("checks") or []:
            line = f"{rel}: {c.get('id')} = {c.get('value')} ({c.get('verdict')})"
            if c.get("verdict") == "BŁĄD":
                bad.append(line)
            elif c.get("verdict") == "UWAGA":
                soft.append(line)
    if bad:
        return result("instructions", "fail", f"pliki instrukcji: {len(bad)} kontroli z błędem (instructions_lint.py --root .)",
                      bad + soft)
    if soft:
        return result("instructions", "warn", f"pliki instrukcji: {len(soft)} uwag (instructions_lint.py --root .)", soft)
    return result("instructions", "ok", f"pliki instrukcji w normie ({len(data.get('files') or [])})")


def check_readiness(root: Path) -> dict:
    script = root / ".claude" / "skills" / "eng-repo-readiness" / "scripts" / "readiness_check.py"   # skill z pack-it
    if not script.is_file():
        return result("readiness", "skip", "gotowość repo sprawdza eng-repo-readiness (pack-it) — nakładka nie jest zainstalowana")
    r = _run(script, str(root), "--json", cwd=root)
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return result("readiness", "warn", "readiness_check.py nie zwrócił wyniku", [(r.stderr or r.stdout).strip()[-300:]])
    findings = data.get("findings") or []
    lines = [f"[{f.get('severity')}] {f.get('message')}" + (f" → {f['fix']}" if f.get("fix") else "") for f in findings]
    high = [f for f in findings if f.get("severity") == "wysoka"]
    medium = [f for f in findings if f.get("severity") == "średnia"]
    verdict = data.get("verdict", "?")
    if high:
        return result("readiness", "fail", f"gotowość repo: {verdict}, {len(high)} ustaleń wysokiej wagi", lines)
    if medium:
        return result("readiness", "warn", f"gotowość repo: {verdict}, {len(medium)} ustaleń średniej wagi", lines)
    return result("readiness", "ok", f"gotowość repo: {verdict}", lines)


def check_hooks(root: Path) -> dict:
    script = root / ".tf" / "factory" / "hooks_status.py"
    if not script.is_file():
        return result("hooks", "skip", "brak .tf/factory/hooks_status.py")
    s = _module(script, "tf_standard_hooks_status").status(root)
    if s.get("active") is None:
        return result("hooks", "skip", "brak hooków w .claude/settings.json albo CI — nic do sprawdzenia")
    if s["active"]:
        return result("hooks", "ok", "hooki fabryki działały przy ostatnich commitach")
    return result("hooks", "warn", f"hooki fabryki prawdopodobnie nieaktywne: {s.get('after_commits')} commitów bez "
                                   f"śladu w .tf/logs (python3 .tf/factory/hooks_status.py)")


CHECKS = {"install": check_install, "journal": check_journal, "instructions": check_instructions,
          "readiness": check_readiness, "hooks": check_hooks}


def verdict(results: list[dict]) -> str:
    worst = max((RANK[r["status"]] for r in results), default=0)
    return {0: "ok", 1: "warn", 2: "fail"}[worst]


def exit_code(results: list[dict], strict: bool) -> int:
    v = verdict(results)
    return 1 if v == "fail" or (strict and v == "warn") else 0


def run(root: Path, only: list[str] | None = None) -> list[dict]:
    out = []
    for check_id in only or list(CHECKS):
        try:
            out.append(CHECKS[check_id](root))
        except Exception as e:  # noqa: BLE001 — awaria jednej kontroli nie ukrywa pozostałych
            out.append(result(check_id, "warn", f"kontrola nie zadziałała: {type(e).__name__}: {e}"))
    return out


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv[1:])
    for a in it:
        if a in ("--root", "--only"):
            opts[a] = next(it, "")
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            opts[a] = True
    root = Path(opts.get("--root") or ROOT).resolve()
    only = [c.strip() for c in str(opts.get("--only") or "").split(",") if c.strip()] or None
    unknown = [c for c in only or [] if c not in CHECKS]
    if unknown or not root.is_dir():
        print(f"✗ nieznana kontrola: {', '.join(unknown)} (dostępne: {', '.join(CHECKS)})" if unknown
              else f"✗ {root} nie jest katalogiem")
        return 2
    results = run(root, only)
    v = verdict(results)
    if opts.get("--json"):
        print(json.dumps({"verdict": v, "checks": results}, ensure_ascii=False, indent=2))
        return exit_code(results, bool(opts.get("--strict")))
    print(f"Standard repozytorium: {v}")
    for r in results:
        print(f"{MARK[r['status']]} {r['id']:<13} {r['summary']}")
        if r["status"] in ("warn", "fail"):
            for d in r["details"]:
                print(f"    {d}")
    return exit_code(results, bool(opts.get("--strict")))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
