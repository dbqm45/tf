#!/usr/bin/env python3
"""Trafność podpowiedzi skilli (hook skill_hint, bez modelu) na scenariuszach strojenia i odłożonych (holdout).

  python3 tools/hint_holdout.py --out .work/all                 # wszystkie skille z workspace'u
  python3 tools/hint_holdout.py --out .work/all core-stack-sync # wybrane skille
  python3 tools/hint_holdout.py --out .work/all --json

Pomiar przy tłumaczeniu treści skilli (etap 4): polskie pytanie trafia w angielski skill przez słowa kluczowe,
więc wynik przed partią i po niej pokazuje, czy słowa nie zostały dopasowane tylko do scenariuszy strojenia.
Liczy scenariusze `expect: trigger` (skill w podpowiedzi) i `no-trigger` (skill poza podpowiedzią).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scenario_files(ws: Path) -> dict[str, list[tuple[str, dict]]]:
    """Skill → [(zbiór, scenariusz)]; zbiór: `tuning` albo `holdout`."""
    out: dict[str, list[tuple[str, dict]]] = {}
    base = ws / ".claude" / "tests" / "skill_evals"
    for kind, folder in (("tuning", base), ("holdout", base / "holdout")):
        for f in sorted(folder.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            for s in data.get("scenarios") or []:
                if s.get("expect") in ("trigger", "no-trigger"):
                    out.setdefault(data["skill"], []).append((kind, s))
    return out


def measure(ws: Path, skills: list[str]) -> dict:
    hint = load(ws / ".claude" / "hooks" / "skill_hint.py", "hh_hint")
    hint.SKILLS = ws / ".claude" / "skills"
    items = hint.load_index()
    res: dict[str, dict] = {}
    for skill, scs in scenario_files(ws).items():
        if skills and skill not in skills:
            continue
        r = res.setdefault(skill, {k: {"ok": 0, "all": 0} for k in ("tuning", "holdout")})
        for kind, s in scs:
            picks = [it["name"] for _, it in hint.select(s["prompt"], items)]
            ok = (skill in picks) if s["expect"] == "trigger" else (skill not in picks)
            r[kind]["all"] += 1
            r[kind]["ok"] += ok
    return res


def main(argv: list[str]) -> int:
    args = argv[1:]
    as_json = "--json" in args
    ws = Path(args[args.index("--out") + 1]).resolve() if "--out" in args else None
    if ws is None or not (ws / ".claude" / "hooks" / "skill_hint.py").is_file():
        print("✗ podaj workspace: --out .work/<nakładki> (tools/workspace.py assemble)")
        return 2
    skip = {"--out", str(args[args.index("--out") + 1]), "--json"}
    res = measure(ws, [a for a in args if a not in skip])
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    tot = {k: [0, 0] for k in ("tuning", "holdout")}
    for skill, r in sorted(res.items()):
        cells = []
        for k in ("tuning", "holdout"):
            tot[k][0] += r[k]["ok"]
            tot[k][1] += r[k]["all"]
            cells.append(f"{k} {r[k]['ok']}/{r[k]['all']}" if r[k]["all"] else f"{k} —")
        print(f"{skill:<36} " + " · ".join(cells))
    print("razem: " + " · ".join(f"{k} {a}/{b}" for k, (a, b) in tot.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
