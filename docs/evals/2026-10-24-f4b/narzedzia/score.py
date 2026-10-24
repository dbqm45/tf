#!/usr/bin/env python3
"""F4-B: pokrycie złotego standardu w dokumentach narzędzia (wstępne, po słowach kluczowych).
Użycie: score.py <tool> <repo>  → JSON z trafieniami per fakt (do ręcznej weryfikacji)."""
import json
import re
import sys
from pathlib import Path

B = Path(__file__).resolve().parent
OUT_DIRS = {"tf": ["docs/project/00-reconstruction"], "maister": [".maister/docs"]}


def corpus(tool: str, repo: str) -> str:
    run = B / "runs" / f"{tool}-{repo}"
    parts = []
    for d in OUT_DIRS[tool]:
        for p in sorted((run / d).rglob("*")):
            if p.is_file() and p.suffix in (".md", ".json", ".yml", ".yaml") and "/raw/" not in p.as_posix():
                parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts).lower()


def main() -> int:
    tool, repo = sys.argv[1], sys.argv[2]
    text = corpus(tool, repo)
    gold = json.loads((B / "gold" / f"{repo}.json").read_text(encoding="utf-8"))
    rows = []
    for f in gold:
        kws = [k.lower() for k in f.get("keywords") or []]
        hits = [k for k in kws if re.search(re.escape(k), text)]
        rows.append({"id": f["id"], "category": f["category"], "fact": f["fact"], "hits": hits,
                     "auto": len(hits) >= max(1, (len(kws) + 1) // 2)})
    print(json.dumps({"tool": tool, "repo": repo, "chars": len(text),
                      "auto_covered": sum(r["auto"] for r in rows), "total": len(rows), "facts": rows},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
