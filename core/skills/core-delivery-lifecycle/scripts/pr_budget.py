#!/usr/bin/env python3
"""
Budżet artefaktów w PR: czy plany, raporty i dowody przebiegu nie zagłuszają zmiany kodu w przeglądzie.

  python3 .claude/skills/core-delivery-lifecycle/scripts/pr_budget.py --base main [--json]

Liczy dodane linie gałęzi względem punktu rozejścia z --base (commity, bez zmian niezatwierdzonych) i dzieli je na
kod i artefakty. Artefakty: docs/project/**, docs/test/**, docs/work/**, .claude/runs/**, **/evidence/** oraz wzorce
z `.claude/pr-budget.json` ({"artifacts": [...], "max_share": 0.5, "max_artifact": 600, "max_plan": 300}).
Przekroczenie:
- artefakty > max_share (domyślnie 50%) dodanych linii, gdy PR zmienia też kod (PR z samą dokumentacją nie podlega);
- pojedynczy artefakt > max_artifact linii (domyślnie 600), plan (`plan.md`, `*-plan.md`) > max_plan (300).
Pierwsza linia: `Werdykt: OK | PRZEKROCZONY`; kod wyjścia 1 przy przekroczeniu. Co zrobić: zostaw w PR to, czego
przegląd potrzebuje (plan, raport cięcia), resztę (surowe logi, dowody, zrzuty) przenieś poza repozytorium albo
skróć; przy uzasadnionym wyjątku opisz go w PR. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_ARTIFACTS = ["docs/project/**", "docs/test/**", "docs/work/**", ".claude/runs/**", "**/evidence/**"]
PLAN = re.compile(r"(^|/)([\w.-]*-)?plan\.md$")


def glob_re(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(f"^{out}$")


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, errors="replace", timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)} zakończony kodem {r.returncode}")
    return r.stdout


def budget(root: Path, base: str) -> dict:
    cfg_path = root / ".claude" / "pr-budget.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    patterns = [glob_re(p) for p in DEFAULT_ARTIFACTS + list(cfg.get("artifacts") or [])]
    max_share = float(cfg.get("max_share", 0.5))
    max_artifact = int(cfg.get("max_artifact", 600))
    max_plan = int(cfg.get("max_plan", 300))
    merge_base = git(root, "merge-base", base, "HEAD").strip()
    code = art = 0
    artifacts, problems, sizes = [], [], {}
    for line in git(root, "diff", "--numstat", f"{merge_base}..HEAD").splitlines():
        added, _deleted, path = line.split("\t", 2)
        if added == "-":          # plik binarny
            continue
        n = int(added)
        if any(p.match(path) for p in patterns):
            art += n
            artifacts.append(path)
            sizes[path] = n
            size = len(git(root, "show", f"HEAD:{path}").splitlines()) if n else 0
            limit = max_plan if PLAN.search(path) else max_artifact
            if size > limit:
                kind = "plan" if limit == max_plan else "artefakt"
                problems.append(f"{path}: {size} linii — {kind} ponad limit {limit}")
        else:
            code += n
    total = code + art
    share = art / total if total else 0.0
    if code and share > max_share:
        top = ", ".join(f"{p} (+{n})" for p, n in sorted(sizes.items(), key=lambda kv: -kv[1])[:3])
        problems.append(f"artefakty to {share:.0%} dodanych linii ({art} z {total}) — limit {max_share:.0%}; "
                        f"największe: {top}")
    return {"verdict": "PRZEKROCZONY" if problems else "OK", "base": base, "code_lines": code,
            "artifact_lines": art, "share": round(share, 3), "artifacts": artifacts, "problems": problems}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", default="main")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = budget(Path.cwd(), a.base)
    except (RuntimeError, OSError, ValueError) as e:
        print(f"✗ {e}")
        return 2
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(f"Werdykt: {res['verdict']} — kod: {res['code_lines']} linii, artefakty: {res['artifact_lines']} linii "
              f"({res['share']:.0%}), baza: {a.base}")
        for p in res["problems"]:
            print(f"✗ {p}")
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
