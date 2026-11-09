#!/usr/bin/env python3
"""
Moduł `architecture` tf analyze, piętro 0 (bez modelu): graf importów z `code_graph.py` (skill eng-codebase-mapping)
zamieniony na ustalenia — cykle importów wykonywanych przy imporcie, zależności w obie strony między grupami modułów
(„pod prąd”) i huby (plik importowany przez co najmniej HUB_MIN plików produkcyjnych).

  python3 scan.py --root <repo> [--files a,b]     # JSON Lines na stdout (kontrakt: .tf/factory/analyze.py)

Graf jest całościowy, więc `--files` jest ignorowane (`incremental: false` w analyzer.yaml). Graf pomija DI,
rejestry, kolejki i HTTP między usługami (ograniczenie code_graph.py) — brak ustaleń nie dowodzi braku sprzężeń.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

HUB_MIN = 15
REL = Path("skills") / "eng-codebase-mapping" / "scripts" / "code_graph.py"


def find_graph(root: Path) -> Path:
    here = Path(__file__).resolve()
    for p in (root / ".claude" / REL, here.parents[5] / ".claude" / REL, here.parents[3] / REL):
        if p.is_file():
            return p
    raise SystemExit("brak code_graph.py (skill eng-codebase-mapping z pack-it) — tf add pack-it")


def emit(rule, title, rel, snippet, sev, conf, evidence, basis, suggestion):
    print(json.dumps({"rule": rule, "title": title, "file": rel, "line": 1, "snippet": snippet, "severity": sev,
                      "confidence": conf, "evidence": evidence, "basis": basis, "suggestion": suggestion},
                     ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--files", default="")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    r = subprocess.run([sys.executable, str(find_graph(root)), str(root), "--json", "--top", "50"],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise SystemExit(f"code_graph.py: kod {r.returncode}: {r.stderr.strip()[-300:]}")
    g = json.loads(r.stdout)
    for c in g.get("cycles", {}).get("runtime", []):
        files = sorted(c.get("files", []))
        if files:
            emit("cycle", f"cykl importów ({len(files)} plików)", files[0], " → ".join(files), "średnia", 0.9,
                 "importy wykonywane przy imporcie tworzą cykl: " + ", ".join(files),
                 "eng-codebase-mapping (cykle), ddd-connascence-analysis",
                 "przerwij cykl: wydziel wspólną część, odwróć zależność przez interfejs albo zdarzenie")
    for u in g.get("upstream", []):
        emit("upstream", f"zależność w obie strony: {u['a']} ⇄ {u['b']}", u["a"], f"{u['a']} <-> {u['b']}",
             "średnia", 0.7, f"{u['a']}→{u['b']}: {u['a_to_b']} importów, {u['b']}→{u['a']}: {u['b_to_a']}"
             + (f"; cykl {u['cycle']}" if u.get("cycle") else ""), "eng-codebase-mapping (pod prąd)",
             "ustal kierunek zależności między grupami i usuń importy przeciwne")
    for h in g.get("hubs", []):
        if h.get("in", 0) >= HUB_MIN and "_vendor" not in h["file"]:
            emit("hub", f"hub: importowany przez {h['in']} plików", h["file"], h["file"], "niska", 0.6,
                 f"{h['in']} importujących, {h.get('out', 0)} importowanych",
                 "eng-codebase-mapping (huby), arch-quality-attributes (modyfikowalność)",
                 "przejrzyj, czy plik nie łączy kilku odpowiedzialności; zmiany tu mają szeroki zasięg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
