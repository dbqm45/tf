#!/usr/bin/env python3
"""
Manifest rekonstrukcji projektu i odświeżanie przyrostowe: zapisuje commit, datę, koszt, partie z `repo_inventory`
z hashem sha256 i hashe plików; po zmianach w repozytorium mówi, które partie (karty modułów) zrobić od nowa.
Tylko biblioteka standardowa; kodu nie uruchamia, repozytorium nie zmienia.

  python3 recon_manifest.py write <repo> --out <manifest.json> [--budget-tokens 60000] [--cost-usd 1.25]
  python3 recon_manifest.py diff <repo> --manifest <manifest.json> [--json]

`diff` liczy partie tym samym budżetem co manifest. Wynik: partie do odświeżenia (zmieniony hash albo nowe),
partie usunięte (ich karty do skasowania), bez zmian, pliki zmienione, dodane i usunięte, zmienione testy (wymagania
z testów do przejrzenia) i udział zmienionych plików w %. Kod 0; 2 — złe wywołanie.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True   # bez __pycache__ w katalogu skilla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_inventory  # noqa: E402


def file_hash(root: str, rel: str) -> str:
    h = hashlib.sha256()
    try:
        with open(os.path.join(root, rel), "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def snapshot(root: str, budget: int) -> dict:
    files, _, _ = repo_inventory.scan(root)
    inv = repo_inventory.inventory(root, budget)
    prod = {f["path"]: file_hash(root, f["path"]) for f in files if not f["test"]}
    tests = {f["path"]: file_hash(root, f["path"]) for f in files if f["test"]}
    batches = []
    for b in inv["batches"]:
        h = hashlib.sha256()
        for p in sorted(b["files"]):
            h.update(f"{p}\0{prod.get(p, '')}\n".encode())
        batches.append({"name": b["name"], "files": sorted(b["files"]), "tokens": b["tokens"], "hash": h.hexdigest()})
    return {"files": prod, "tests": tests, "batches": batches}


def commit_of(root: str) -> str:
    r = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def diff(old: dict, new: dict) -> dict:
    of, nf = old.get("files", {}), new["files"]
    added = sorted(set(nf) - set(of))
    removed = sorted(set(of) - set(nf))
    modified = sorted(p for p in set(of) & set(nf) if of[p] != nf[p])
    ot, nt = old.get("tests", {}), new["tests"]
    tests = sorted(p for p in set(ot) | set(nt) if ot.get(p) != nt.get(p))
    ob = {b["name"]: b["hash"] for b in old.get("batches", [])}
    nb = {b["name"]: b["hash"] for b in new["batches"]}
    changed = sorted(set(added) | set(removed) | set(modified))
    return {"refresh": sorted(n for n in nb if ob.get(n) != nb[n]),
            "new_batches": sorted(set(nb) - set(ob)),
            "removed_batches": sorted(set(ob) - set(nb)),
            "unchanged": sorted(n for n in nb if ob.get(n) == nb[n]),
            "changed_files": changed, "added_files": added, "removed_files": removed, "tests_changed": tests,
            "share": round(100 * len(changed) / max(1, len(of)))}


def render(d: dict, base: str) -> str:
    L = [f"Względem manifestu (commit {base or '—'}): zmienione pliki {len(d['changed_files'])} ({d['share']}%), "
         f"testy {len(d['tests_changed'])}",
         "Odśwież: " + (", ".join(d["refresh"]) or "nic")]
    if d["new_batches"]:
        L.append("  w tym nowe partie: " + ", ".join(d["new_batches"]))
    if d["removed_batches"]:
        L.append("Partie usunięte (skasuj ich karty): " + ", ".join(d["removed_batches"]))
    L.append("Bez zmian: " + (", ".join(d["unchanged"]) or "—"))
    if d["tests_changed"]:
        L.append("Zmienione testy (przejrzyj wymagania): " + ", ".join(d["tests_changed"]))
    if d["share"] > 50:
        L.append("Zmieniło się ponad połowę plików — rozważ pełny przebieg zamiast odświeżania.")
    return "\n".join(L)


def opt(args: list[str], name: str, default=None):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return default


def main(argv: list[str]) -> int:
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    repo = rest[0] if rest and not rest[0].startswith("--") else ""
    if cmd not in ("write", "diff") or not os.path.isdir(repo):
        print(f"✗ użycie: write|diff <repo> … (jest: {argv})", file=sys.stderr)
        return 2
    try:
        if cmd == "write":
            out = opt(rest, "--out")
            if not out:
                print("✗ podaj --out <manifest.json>", file=sys.stderr)
                return 2
            budget = int(opt(rest, "--budget-tokens", 60000))
            cost = opt(rest, "--cost-usd")
            m = {"commit": commit_of(repo), "date": datetime.date.today().isoformat(), "budget_tokens": budget,
                 "cost_usd": float(cost) if cost is not None else None, **snapshot(repo, budget)}
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(m, fh, ensure_ascii=False, indent=2)
            print(f"✓ manifest: {out} — partie {len(m['batches'])}, pliki {len(m['files'])}")
            return 0
        path = opt(rest, "--manifest")
        if not path or not os.path.isfile(path):
            print(f"✗ brak manifestu: {path}", file=sys.stderr)
            return 2
        with open(path, encoding="utf-8") as fh:
            old = json.load(fh)
        d = diff(old, snapshot(repo, int(old.get("budget_tokens") or 60000)))
    except (ValueError, json.JSONDecodeError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    print(json.dumps(d, ensure_ascii=False, indent=2) if "--json" in rest else render(d, old.get("commit", "")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
