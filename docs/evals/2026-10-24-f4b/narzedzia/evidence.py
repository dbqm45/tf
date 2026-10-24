#!/usr/bin/env python3
"""F4-B: dowody w dokumentach narzędzia. Użycie: evidence.py <tool> <repo> [--sample N]
Liczy odwołania plik:linia (istnieje plik i linia), wypunktowania z dowodem i bez; losuje próbkę do ręcznej oceny."""
import json
import random
import re
import sys
from pathlib import Path

B = Path(__file__).resolve().parent
OUT_DIRS = {"tf": ["docs/project/00-reconstruction"], "maister": [".maister/docs"]}
REF = re.compile(r"`?([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+):(\d+)(?:[-–](\d+))?`?")


def main() -> int:
    tool, repo = sys.argv[1], sys.argv[2]
    n = int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0
    run = B / "runs" / f"{tool}-{repo}"
    refs, ok, bullets, with_ev, claims = 0, 0, 0, 0, []
    for d in OUT_DIRS[tool]:
        for p in sorted((run / d).rglob("*.md")):
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                found = REF.findall(line)
                if re.match(r"\s*([-*]|\d+\.|\|)\s", line) and len(line.strip()) > 20:
                    bullets += 1
                    if found:
                        with_ev += 1
                        claims.append({"doc": p.relative_to(run).as_posix(), "line": line.strip()[:300]})
                for path, a, b in found:
                    refs += 1
                    f = run / path
                    if not f.is_file():
                        hits = [x for x in run.rglob(Path(path).name) if ".maister" not in x.parts and "docs" not in x.parts[:2]]
                        f = hits[0] if len(hits) == 1 else f
                    if f.is_file() and int(b or a) <= len(f.read_text(errors="replace").splitlines()):
                        ok += 1
    random.seed(42)
    out = {"tool": tool, "repo": repo, "refs": refs, "refs_resolved": ok, "bullets": bullets,
           "bullets_with_evidence": with_ev, "sample": random.sample(claims, min(n, len(claims)))}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
