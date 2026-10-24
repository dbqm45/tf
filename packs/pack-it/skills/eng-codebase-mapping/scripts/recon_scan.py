#!/usr/bin/env python3
"""
Krok 1 rekonstrukcji jednym poleceniem, bez modelu: repo_inventory, code_graph, git_territory, standards_scan
i schema_scan zapisują pełne wyniki JSON do --out, a na ekran trafia tylko zwięzłe streszczenie (≤ 60 linii).
Model czyta streszczenie, a po szczegóły sięga do plików JSON. To oszczędza tury i kontekst głównego modelu.

  python3 recon_scan.py <repo> --out docs/project/00-reconstruction/raw
  python3 recon_scan.py <repo> --out <dir> --budget-tokens 60000   # budżet partii jawnie

Budżet partii domyślnie: 12000 tokenów dla repo < 150 tys. tokenów kodu (partia ≈ pakiet, karta na pakiet),
60000 dla większych. Bez gita historia jest pominięta. Kod wyjścia: 0 — w porządku, 2 — złe wywołanie.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SMALL_REPO_TOKENS = 150_000
CI_FILES = (".github/workflows/*.yml", ".github/workflows/*.yaml", ".gitlab-ci.yml", "Jenkinsfile",
            "azure-pipelines.yml", ".circleci/config.yml", "bitbucket-pipelines.yml", ".travis.yml", ".drone.yml",
            ".buildkite/pipeline.yml")


def run_json(script: str, *args: str) -> dict | None:
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *args, "--json"], capture_output=True, text=True,
                       stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def save(out: str, name: str, data: dict) -> None:
    with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)


def short(items: list, n: int) -> str:
    items = [str(i) for i in items]
    return ", ".join(items[:n]) + (f" … (+{len(items) - n})" if len(items) > n else "")


def main(argv: list[str]) -> int:
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    repo, out, budget, it = None, None, None, iter(argv)
    for a in it:
        if a == "--out":
            out = next(it, None)
        elif a == "--budget-tokens":
            budget = next(it, None)
        elif repo is None:
            repo = a
    if not repo or not out or not os.path.isdir(repo) or (budget is not None and not str(budget).isdigit()):
        print(f"✗ użycie: recon_scan.py <repo> --out <katalog> [--budget-tokens N] (jest: {argv})", file=sys.stderr)
        return 2
    os.makedirs(out, exist_ok=True)
    inv = run_json("repo_inventory.py", repo, "--budget-tokens", str(budget or 60000))
    if inv and budget is None and inv.get("totals", {}).get("tokens", 0) < SMALL_REPO_TOKENS:
        inv = run_json("repo_inventory.py", repo, "--budget-tokens", "12000") or inv
    results = {"inventory.json": inv, "graph.json": run_json("code_graph.py", repo),
               "standards.json": run_json("standards_scan.py", repo), "schema.json": run_json("schema_scan.py", repo)}
    is_git = subprocess.run(["git", "-C", repo, "rev-parse", "--is-inside-work-tree"], capture_output=True,
                            text=True).stdout.strip() == "true"
    results["territory.json"] = run_json("git_territory.py", "--repo", repo, "--all") if is_git else None
    for name, data in results.items():
        if data is not None:
            save(out, name, data)

    L = []
    if inv:
        langs = [f"{x['language']} ({x['files']} plików, {x.get('test_files', 0)} testów)" for x in inv.get("languages", [])]
        L.append("Języki: " + short(langs, 6))
        L.append("Pliki budowania: " + (short([b["file"] for b in inv.get("build_files", [])], 8) or "brak"))
        batches = inv.get("batches", [])
        L.append(f"Partie ({len(batches)}, budżet {inv.get('budget_tokens')} tokenów, razem "
                 f"{inv.get('totals', {}).get('tokens')} tokenów): "
                 + short([f"{b['name']} ({len(b['files'])})" for b in batches], 20))
    ci = sorted({os.path.relpath(p, repo).replace(os.sep, "/") for pat in CI_FILES for p in glob.glob(os.path.join(repo, pat))})
    L.append("CI: " + (", ".join(ci) if ci else "brak plików pipeline'u"))
    g = results["graph.json"]
    if g:
        L.append("Wejścia: " + short([e["file"] for e in g.get("entry_points", [])], 5))
        L.append("Huby: " + short([f"{h['file']} (in {h['in']})" for h in g.get("hubs", [])], 5))
        cyc = g.get("cycles") or {}
        n = sum(len(v) for v in cyc.values()) if isinstance(cyc, dict) else len(cyc)
        L.append(f"Cykle: {n}")
    t = results["territory.json"]
    if t:
        L.append(f"Historia: {t.get('commits')} commitów od {t.get('since')}; hotspoty: "
                 + short([h["path"] for h in t.get("hotspots", [])], 5))
    else:
        L.append("Historia: pominięta (historia: brak gita)" if not is_git else "Historia: błąd git_territory")
    sc = results["schema.json"]
    if sc:
        L.append("Tabele: " + (short([x["name"] for x in sc.get("tables", [])], 15) or "brak"))
    st = results["standards.json"]
    if st:
        L.append("Narzędzia: " + (short([f"{x['tool']} ({x['file']})" for x in st.get("tools", [])], 8) or "brak"))
        sig = [s for s in st.get("signals", []) if s["share"] >= 50 or s["area"].startswith("idiomy")]
        sig.sort(key=lambda s: (-s["count"], s["area"]))
        L.append(f"Standardy (sygnały ≥ 50% i idiomy; {len(sig)} z {len(st.get('signals', []))}):")
        L += [f"  {s['area']} · {s['language']} · {s['rule']}: {s['count']}/{s['total']} = {s['share']}%"
              for s in sig[:25]]
    L.append(f"Pełne wyniki: {out}/ ({', '.join(n for n, d in results.items() if d is not None)})")
    print("\n".join(L[:60]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
