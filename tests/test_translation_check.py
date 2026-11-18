#!/usr/bin/env python3
"""tools/translation_check.py: a translation of skill content (stage 4) neither loses nor adds facts — code blocks,
fragments in `…`, numbers, links, structure (sections, bullets, table rows); Polish keywords stay."""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tc", REPO / "tools" / "translation_check.py")
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)

PL = """---
name: core-x
description: Użyj przy księgowaniu — dekretacja.
metadata:
  keywords: "księgowanie, dekretacja"
---
# Księga

## 1. Zasady
- Limit 200 linii; próg 0,8 (patrz [przewodnik](references/a.md)).
- Uruchom `python3 tool.py --check` przed commitem.

| Status | Co |
|---|---|
| `OK` | dalej |

```bash
python3 tool.py            # raport tekstowy
```
Wzorzec: `tool.py new <nazwa>`.

```
**P1 — Kto eksportuje**: a) admin → Rekomendacja: a, limit 50 tys.
```
"""
EN = """---
name: core-x
description: Use for ledger postings — double entry.
metadata:
  keywords: "księgowanie, dekretacja, ledger posting"
---
# Ledger

## 1. Rules
- Limit 200 lines; threshold 0.8 (see [guide](references/a.md)).
- Run `python3 tool.py --check` before committing.

| Status | What |
|---|---|
| `OK` | continue |

```bash
python3 tool.py            # text report
```
Pattern: `tool.py new <name>`.

```
**P1 — Who exports**: a) admin → Recommendation: a, limit 50k.
```
"""


def main() -> int:
    fails = []
    if tc.compare(PL, EN):
        fails.append(f"TC-1: a faithful translation (0,8 = 0.8, code comments and <placeholders> translated) without remarks: {tc.compare(PL, EN)}")
    cases = {
        "TC-2 number": EN.replace("Limit 200", "Limit 300"),
        "TC-3 command": EN.replace("--check", "--fix"),
        "TC-4 code block": EN.replace("python3 tool.py            #", "python3 tool.py --all      #"),
        "TC-5 list item": EN.replace("- Run `python3 tool.py --check` before committing.\n", ""),
        "TC-6 link": EN.replace("references/a.md", "references/b.md"),
        "TC-7 table row": EN.replace("| `OK` | continue |\n", ""),
        "TC-8 PL keywords": EN.replace("księgowanie, ", ""),
        "TC-9 name": EN.replace("name: core-x", "name: core-y"),
        "TC-10 number in an example": EN.replace("limit 50k", "limit 60k"),
    }
    for label, bad in cases.items():
        if not tc.compare(PL, bad):
            fails.append(f"{label}: difference not detected")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {10 - len(fails)}/10 translation_check tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
