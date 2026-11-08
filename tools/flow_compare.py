#!/usr/bin/env python3
"""
Narzędzie fabryki: porównanie przepływów pracy (np. sam tryb planu, talos, mode-pdi) na tych samych zgłoszeniach.

  python3 tools/flow_compare.py prepare flows.json --out <katalog> [--seed N]
      zanonimizowane diffy przebiegów (<zgłoszenie>/A.diff, B.diff…) i szablon oceny ocena.json dla oceniającego;
      klucz przypisania liter do przepływów w <katalog>/key.json (nie dawaj go oceniającemu)
  python3 tools/flow_compare.py report flows.json --key <katalog>/key.json [--verdicts oceny.json] --out raport.md
      tabela na zgłoszenie: koszt, czas, commity, linie kodu i artefaktów (udział), ocena, gotowy do merge, koszt na
      punkt oceny, krotność kosztu wobec przepływu bazowego; werdykt: najwyższa ocena wśród gotowych do merge, przy
      remisie tańszy

flows.json: {"repo": ŚCIEŻKA, "base": "main", "baseline": "plan",
             "tickets": [{"id": "T-1", "runs": [{"flow": "talos", "branch": "story/x", "cost_usd": 14.0,
                                                   "minutes": 45}, …]}]}
oceny.json (od ślepego oceniającego, po literach): {"T-1": {"A": {"score": 8, "mergeable": true, "uwagi": "…"}, …}}
Artefakty liczone tymi samymi wzorcami co pr_budget.py (core-delivery-lifecycle). Protokół:
docs/evals/protokol-porownania-przeplywow.md. Bez sieci i bez modelu; tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import string
import subprocess
import sys
from pathlib import Path

TF = Path(__file__).resolve().parents[1]
CRITERIA = ["poprawność wobec kryteriów zgłoszenia", "testy sprawdzają zachowanie", "zgodność z konwencjami repo",
            "rozmiar i czytelność zmiany", "gotowe do merge bez dalszych poprawek (tak/nie)"]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


budget = _load("pr_budget", TF / "core" / "skills" / "core-delivery-lifecycle" / "scripts" / "pr_budget.py")


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, errors="replace", timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)}: kod {r.returncode}")
    return r.stdout


def measure(repo: Path, base: str, branch: str) -> dict:
    mb = git(repo, "merge-base", base, branch).strip()
    pats = [budget.glob_re(p) for p in budget.DEFAULT_ARTIFACTS]
    code = art = 0
    for line in git(repo, "diff", "--numstat", f"{mb}..{branch}").splitlines():
        added, _d, path = line.split("\t", 2)
        if added == "-":
            continue
        if any(p.match(path) for p in pats):
            art += int(added)
        else:
            code += int(added)
    commits = int(git(repo, "rev-list", "--count", f"{mb}..{branch}").strip() or 0)
    return {"code": code, "artifacts": art, "commits": commits}


def num(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def cmd_prepare(m: dict, out: Path, seed: int) -> int:
    repo, base = Path(m["repo"]), m.get("base", "main")
    rng = random.Random(seed)
    key = {}
    for t in m["tickets"]:
        runs = list(t["runs"])
        rng.shuffle(runs)
        d = out / t["id"]
        d.mkdir(parents=True, exist_ok=True)
        key[t["id"]] = {}
        for letter, run in zip(string.ascii_uppercase, runs):
            mb = git(repo, "merge-base", base, run["branch"]).strip()
            diff = git(repo, "diff", f"{mb}..{run['branch']}")
            (d / f"{letter}.diff").write_text(diff, encoding="utf-8")
            key[t["id"]][letter] = run["flow"]
        tmpl = {"zgloszenie": t["id"], "kryteria": CRITERIA, "skala": "score 1–10 (całość), mergeable: true/false",
                "oceny": {letter: {"score": None, "mergeable": None, "uwagi": ""} for letter in key[t["id"]]}}
        (d / "ocena.json").write_text(json.dumps(tmpl, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"✓ {len(key)} zgłoszeń: diffy i szablony ocen w {out}/<zgłoszenie>/; klucz: {out / 'key.json'} "
          f"(nie przekazuj oceniającemu)")
    return 0


def cmd_report(m: dict, mf: Path, key: dict, verdicts: dict, out: Path) -> int:
    repo, base, baseline = Path(m["repo"]), m.get("base", "main"), m.get("baseline")
    lines = ["# Porównanie przepływów na tych samych zgłoszeniach", "",
             f"Pliki: manifest przebiegów `{mf.name}`, klucz `{Path(key.get('_path', 'key.json')).name}`"
             + (", oceny ślepe z pliku przekazanego przez --verdicts" if verdicts else ", bez ocen") + ".", ""]
    wins: dict[str, int] = {}
    for t in m["tickets"]:
        flow_of = key.get(t["id"], {})
        letter_of = {v: k for k, v in flow_of.items()}
        ver = verdicts.get(t["id"], {})
        base_cost = next((r["cost_usd"] for r in t["runs"] if r["flow"] == baseline), None)
        lines += [f"## {t['id']}", "",
                  "| Przepływ | Koszt USD | × bazy | Czas min | Commity | Kod | Artefakty | Udział artefaktów "
                  "| Ocena | Gotowy do merge | USD na punkt |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        best = None
        for run in t["runs"]:
            ms = measure(repo, base, run["branch"])
            v = ver.get(letter_of.get(run["flow"], ""), {})
            score, merge = v.get("score"), v.get("mergeable")
            total = ms["code"] + ms["artifacts"]
            share = f"{ms['artifacts'] / total:.0%}" if total else "—"
            ratio = f"{num(run['cost_usd'] / base_cost, 1)}×" if base_cost else "—"
            per = num(run["cost_usd"] / score) if score else "—"
            lines.append(f"| {run['flow']} | {num(run['cost_usd'])} | {ratio} | {run.get('minutes', '—')} | "
                         f"{ms['commits']} | {ms['code']} | {ms['artifacts']} | {share} | "
                         f"{score if score is not None else 'bez oceny'} | "
                         f"{'tak' if merge else ('nie' if merge is False else '—')} | {per} |")
            if merge and score is not None:
                cand = (-score, run["cost_usd"], run["flow"])
                best = min(best, cand) if best else cand
        if best:
            wins[best[2]] = wins.get(best[2], 0) + 1
            lines += ["", f"Werdykt: {best[2]} — najwyższa ocena wśród gotowych do merge ({-best[0]}), przy remisie "
                          f"tańszy.", ""]
        else:
            lines += ["", "Werdykt: brak — żaden przebieg nie ma oceny „gotowy do merge” (oceny ślepe nie wpłynęły "
                          "albo nic nie nadaje się do merge).", ""]
    if wins:
        lines += ["## Podsumowanie", "", ", ".join(f"{f}: {n}" for f, n in sorted(wins.items(), key=lambda x: -x[1]))
                  + " wygranych.", ""]
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"✓ raport: {out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("manifest")
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=0)
    r = sub.add_parser("report")
    r.add_argument("manifest")
    r.add_argument("--key", required=True)
    r.add_argument("--verdicts")
    r.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    mf = Path(a.manifest)
    try:
        m = json.loads(mf.read_text(encoding="utf-8"))
        if a.cmd == "prepare":
            return cmd_prepare(m, Path(a.out), a.seed)
        key = json.loads(Path(a.key).read_text(encoding="utf-8"))
        key["_path"] = a.key
        verdicts = json.loads(Path(a.verdicts).read_text(encoding="utf-8")) if a.verdicts else {}
        return cmd_report(m, mf, key, verdicts, Path(a.out))
    except (OSError, ValueError, KeyError, RuntimeError) as e:
        print(f"✗ {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
