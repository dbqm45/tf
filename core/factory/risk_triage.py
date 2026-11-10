#!/usr/bin/env python3
"""Triaż ryzyka zmian (B1b): co w tej gałęzi musi zobaczyć człowiek.

  python3 .tf/factory/risk_triage.py                 # diff względem origin/main (albo main/master)
  python3 .tf/factory/risk_triage.py --base develop
  python3 .tf/factory/risk_triage.py --md            # sekcja do opisu PR
  python3 .tf/factory/risk_triage.py --json
  tf risk [opcje]

Deterministycznie, bez modelu: zmienione pliki i linie diffu `base...HEAD` → poziom i lista z plikiem i powodem.
- high: uwierzytelnianie i uprawnienia, płatności i rozliczenia, schemat i migracje bazy, wdrożenie i sekrety
  (CI, IaC, Dockerfile, .env), osłabione testy (usunięte asercje, `skip`, usunięte pliki testów), zmienione
  specyfikacje i kryteria akceptacji;
- low: tylko dokumentacja albo tylko manifesty i lockfile'e zależności;
- medium: reszta — zielone testy i przegląd niezależnego recenzenta; na liście także brakujące dowody
  (nowy moduł bez ADR).
Wynik jest doradczy (nie blokuje merge'a) — mówi, co człowiek musi przejrzeć. Reguły: `autonomy.triage`
w `.tf/factory/config.yaml`, nadpisanie i nowe kategorie w `.tf/config/config.yaml`.
"""
from __future__ import annotations

import os
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne (build.py, testy, hooki) też piszą i czytają UTF-8

sys.dont_write_bytecode = True   # silnik w .tf/factory/ bez __pycache__ (jak node_modules — tylko kod)
import argparse
import copy
import importlib.util
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULT_RULES: dict = {
    "high": {
        "auth": [r"(^|[/_.-])(auth\w*|login|logout|permissions?|rbac|abac|acl|oauth\w*|jwt|passwords?|credentials?|"
                 r"security)([/_.-]|$)"],
        "payments": [r"(^|[/_.-])(payments?|billing|invoices?|refunds?|checkout|stripe|ledger|wallets?|payouts?)"
                     r"([/_.-]|$)"],
        "schema": [r"(^|/)(migrations?|alembic|flyway|liquibase|db/migrate)/", r"\.sql$",
                   r"(^|/)schema\.(prisma|graphql|sql|rb)$"],
        "deploy": [r"^\.github/workflows/", r"(^|/)\.gitlab-ci\.ya?ml$", r"(^|/)Jenkinsfile$", r"(^|/)Dockerfile",
                   r"(^|/)docker-compose[^/]*\.ya?ml$", r"\.tf$", r"(^|/)(terraform|helm|k8s|kubernetes|infra)/",
                   r"(^|/)\.env($|\.)", r"(^|/)secrets?/"],
        "spec": [r"\.feature$", r"(^|/)(acceptance|requirements?|wymagania|kryteria)[^/]*", r"(^|/)SPEC\.md$"],
    },
    "low_docs": [r"\.(md|txt|rst|adoc)$", r"^docs/", r"(^|/)LICENSE[^/]*$"],
    "low_deps": [r"(^|/)(package\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|requirements[^/]*\.txt|"
                 r"poetry\.lock|pyproject\.toml|Pipfile(\.lock)?|uv\.lock|go\.(mod|sum)|Cargo\.(toml|lock)|"
                 r"pom\.xml|build\.gradle(\.kts)?|gradle\.lockfile|Gemfile(\.lock)?|composer\.(json|lock))$"],
    "test_files": [r"(^|/)(tests?|__tests__|spec)/", r"(^|/)test_[^/]*\.py$", r"_test\.(py|go)$",
                   r"\.(test|spec)\.[cm]?[jt]sx?$", r"Tests?\.(java|kt|cs)$"],
    "assert_lines": r"\b(assert\w*|expect\s*\(|should\b|verify\s*\()",
    "skip_lines": r"(@pytest\.mark\.(skip|xfail)|pytest\.skip\(|\.skip\(|\bx(it|describe|test)\(|@Disabled|@Ignore|"
                  r"\bt\.Skip\(|\[Fact\(Skip|unittest\.skip)",
    "adr": [r"(^|/)(adr|ADR|decisions)/", r"(^|/)ADR-?\d+"],
    "new_module_skip": [r"^\.", r"^(docs|tests?|__tests__|migrations?|scripts)/"],
}

LABELS = {"auth": "uwierzytelnianie lub uprawnienia", "payments": "płatności lub rozliczenia",
          "schema": "schemat lub migracja bazy", "deploy": "wdrożenie, CI, infrastruktura lub sekrety",
          "spec": "specyfikacja lub kryteria akceptacji", "tests-weakened": "osłabione testy",
          "evidence-adr": "nowy moduł bez ADR"}
LEVEL_PL = {"high": "wysokie", "medium": "średnie", "low": "niskie"}


def _packs():
    spec = importlib.util.spec_from_file_location("tf_packs_risk", HERE / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_rules(repo: Path) -> dict:
    """Reguły domyślne + `autonomy.triage` z konfiguracji silnika i projektu (`.tf/config/config.yaml`)."""
    rules = copy.deepcopy(DEFAULT_RULES)
    try:
        load_yaml = _packs().load_yaml
    except Exception:   # bez packs.py (np. sam skrypt) — tylko reguły domyślne
        return rules
    for p in (repo / ".tf" / "factory" / "config.yaml", repo / ".tf" / "config" / "config.yaml"):
        if p.is_file():
            over = ((load_yaml(p) or {}).get("autonomy") or {}).get("triage") or {}
            rules = _merge(rules, over)
    return rules


def _git(repo: Path, *args) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)}: kod {r.returncode}")
    return r.stdout


def default_base(repo: Path) -> str:
    for ref in ("origin/main", "origin/master", "main", "master"):
        if subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "-q", ref], capture_output=True).returncode == 0:
            return ref
    return "HEAD~1"


def _any(patterns, path: str) -> bool:
    return any(re.search(p, path) for p in patterns)


def _changed(repo: Path, base: str) -> list[tuple[str, str]]:
    out = []
    for line in _git(repo, "diff", "--name-status", "-M", f"{base}...HEAD").splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            out.append((parts[0][0], parts[-1]))
    return out


def _lines(repo: Path, base: str, path: str) -> tuple[list[str], list[str]]:
    added, removed = [], []
    for line in _git(repo, "diff", "-U0", f"{base}...HEAD", "--", path).splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
    return added, removed


def triage(repo: Path, base: str | None = None, rules: dict | None = None) -> dict:
    rules = rules or DEFAULT_RULES
    base = base or default_base(repo)
    changed = _changed(repo, base)
    items: list[dict] = []
    for status, path in changed:
        for cat, pats in (rules.get("high") or {}).items():
            if _any(pats, path):
                items.append({"level": "high", "category": cat, "file": path,
                              "reason": LABELS.get(cat, cat) + (" (usunięty)" if status == "D" else "")})
        if _any(rules["test_files"], path):
            if status == "D":
                items.append({"level": "high", "category": "tests-weakened", "file": path,
                              "reason": "usunięty plik testów"})
                continue
            added, removed = _lines(repo, base, path)
            a_re, s_re = re.compile(rules["assert_lines"]), re.compile(rules["skip_lines"])
            lost = sum(bool(a_re.search(x)) for x in removed) - sum(bool(a_re.search(x)) for x in added)
            if lost > 0:
                items.append({"level": "high", "category": "tests-weakened", "file": path,
                              "reason": f"ubyło asercji: {lost}"})
            if any(s_re.search(x) for x in added):
                items.append({"level": "high", "category": "tests-weakened", "file": path,
                              "reason": "dodane pominięcie testu (skip)"})
    # D3: dowód — nowy katalog w kodzie (moduł) bez ADR w tej samej zmianie
    base_dirs = {str(Path(p).parent) for p in _git(repo, "ls-tree", "-r", "--name-only", base).splitlines()}
    has_adr = any(_any(rules["adr"], p) for _, p in changed)
    if not has_adr:
        new_dirs = sorted({str(Path(p).parent) for s, p in changed if s == "A" and str(Path(p).parent) not in base_dirs
                           and str(Path(p).parent) != "." and not _any(rules["new_module_skip"], p)
                           and not _any(rules["low_docs"], p) and not _any(rules["test_files"], p)})
        for d in new_dirs:
            items.append({"level": "medium", "category": "evidence-adr", "file": d + "/",
                          "reason": "nowy moduł bez ADR (czy to decyzja architektoniczna?)"})
    files = [p for _, p in changed]
    if any(i["level"] == "high" for i in items):
        level = "high"
    elif files and not items and (all(_any(rules["low_docs"], p) for p in files)
                                  or all(_any(rules["low_deps"], p) for p in files)):
        level = "low"
    else:
        level = "medium"
    return {"base": base, "level": level, "files": files, "items": items}


def to_markdown(res: dict) -> str:
    lines = [f"## Ryzyko zmiany: {LEVEL_PL[res['level']]}", "",
             "Triaż doradczy (`tf risk`): nie blokuje merge'a, mówi, co musi przejrzeć człowiek."]
    if res["level"] == "high":
        lines.append("Zmiana dotyka obszarów wysokiego ryzyka — wymaga zatwierdzenia człowieka po przejrzeniu poniższych.")
    elif res["level"] == "medium":
        lines.append("Wymagane: zielone testy i przegląd niezależnego recenzenta.")
    else:
        lines.append("Tylko dokumentacja albo zależności — przy zielonych testach wystarczy szybki przegląd.")
    if res["items"]:
        lines += ["", "| Poziom | Plik | Powód |", "|---|---|---|"]
        lines += [f"| {LEVEL_PL[i['level']]} | `{i['file']}` | {i['reason']} |" for i in res["items"]]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=None, help="gałąź bazowa (domyślnie origin/main, main albo master)")
    ap.add_argument("--json", action="store_true", help="wynik jako JSON")
    ap.add_argument("--md", action="store_true", help="sekcja do opisu PR (Markdown)")
    args = ap.parse_args(argv)
    repo = Path.cwd()
    try:
        res = triage(repo, base=args.base, rules=load_rules(repo))
    except (RuntimeError, OSError, subprocess.SubprocessError) as e:
        print(f"✗ Triaż niemożliwy: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(to_markdown(res))
    return 0   # doradczy: także przy high kod 0


if __name__ == "__main__":
    sys.exit(main())
