#!/usr/bin/env python3
"""Translation fidelity of factory content (stage 4), no model: the version before translation versus after.

  python3 tools/translation_check.py core/skills/core-stack-sync            # a skill directory against origin/main
  python3 tools/translation_check.py core/skills/core-x --ref HEAD~1        # a different reference point
  python3 tools/translation_check.py core/factory/traits/grounded.md        # a single file

Translation changes the language of the prose, not the facts. For each .md file it compares:
- code blocks with a language (```bash … ```) — identical and in the same order (comments and the content of <placeholders>
  are prose); a block without a language (or `text`, `markdown`) is an output example — compared as prose;
- fragments in `…` (commands, paths, fields, thresholds) — the same set with multiplicity;
- numbers — the same digit strings (0,8 and 0.8 are the same number);
- markdown links and URLs — the same targets;
- structure — the number of headings, list items, table rows;
- YAML header — the same `name`; all former `metadata.keywords` stay (English ones are added).
Exit 0 — no differences; 1 — differences (listed in the output); 2 — bad invocation.
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

CODE_BLOCK = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`([^`\n]+)`")
NUMBER = re.compile(r"\d+")
LINK = re.compile(r"\]\(([^)\s]+)\)")
URL = re.compile(r"https?://[^\s)>\]\"'`]+")


def _front(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    fm = m.group(1)
    name = (re.search(r"^name:\s*(.*)$", fm, re.M) or [None, ""])[1].strip()
    kw = (re.search(r"^\s+keywords:\s*(.*)$", fm, re.M) or [None, ""])[1].strip().strip('"')
    return {"name": name, "keywords": {k.strip().lower() for k in kw.split(",") if k.strip()}}, text[m.end():]


COMMENT = re.compile(r"(?m)(^|\s)(#|//|--)\s.*$")   # a comment in code is prose — it gets translated
PLACEHOLDER = re.compile(r"<[^<>\n]+>")              # <technologia> → <technology>: the placeholder content is prose


def _code(block: str) -> str:
    return PLACEHOLDER.sub("<>", COMMENT.sub(r"\1", block)).rstrip()


PROSE_LANGS = ("", "text", "markdown", "md")   # a block without a language = an output example (prose), it gets translated


def _is_code(block: str) -> bool:
    return block[3:].split("\n", 1)[0].strip().lower() not in PROSE_LANGS


def facts(text: str) -> dict:
    fm, body = _front(text)
    raw = CODE_BLOCK.findall(body)
    blocks = [_code(b) for b in raw if _is_code(b)]
    prose = CODE_BLOCK.sub(lambda m: " " if _is_code(m.group(0)) else m.group(0).strip("`"), body)
    lines = prose.splitlines()
    return {
        "front": fm,
        "blocks": blocks,
        "inline": Counter(PLACEHOLDER.sub("<>", x) for x in INLINE.findall(prose)),
        "numbers": Counter(NUMBER.findall(INLINE.sub(" ", URL.sub(" ", LINK.sub(" ", prose))))),
        "links": Counter(LINK.findall(prose)) + Counter(URL.findall(prose)),
        "headings": sum(1 for ln in lines if re.match(r"^#{1,6}\s", ln)),
        "items": sum(1 for ln in lines if re.match(r"^\s*([-*]|\d+\.)\s", ln)),
        "rows": sum(1 for ln in lines if ln.lstrip().startswith("|")),
    }


def _diff(label: str, old: Counter, new: Counter) -> list[str]:
    gone, added = old - new, new - old
    out = []
    if gone:
        out.append(f"{label}: removed {', '.join(sorted(gone))[:300]}")
    if added:
        out.append(f"{label}: added {', '.join(sorted(added))[:300]}")
    return out


def compare(old_text: str, new_text: str) -> list[str]:
    """Differences in facts between the version before translation and after; an empty list — a faithful translation."""
    a, b = facts(old_text), facts(new_text)
    out = []
    if a["front"].get("name") != b["front"].get("name"):
        out.append(f"name: {a['front'].get('name')} → {b['front'].get('name')}")
    lost_kw = a["front"].get("keywords", set()) - b["front"].get("keywords", set())
    if lost_kw:
        out.append(f"keywords: removed {', '.join(sorted(lost_kw))[:300]} (Polish keywords must stay)")
    if a["blocks"] != b["blocks"]:
        out.append(f"code blocks: {len(a['blocks'])} → {len(b['blocks'])} or changed content")
    out += _diff("`…`", a["inline"], b["inline"])
    out += _diff("numbers", a["numbers"], b["numbers"])
    out += _diff("links", a["links"], b["links"])
    for k, label in (("headings", "headings"), ("items", "list items"), ("rows", "table rows")):
        if a[k] != b[k]:
            out.append(f"{label}: {a[k]} → {b[k]}")
    return out


def files_of(target: Path) -> list[Path]:
    return [target] if target.is_file() else sorted(p for p in target.rglob("*.md"))


def at_ref(path: Path, ref: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{path.as_posix()}"], capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def main(argv: list[str]) -> int:
    args = argv[1:]
    ref = args[args.index("--ref") + 1] if "--ref" in args else "origin/main"
    paths = [a for i, a in enumerate(args) if a != "--ref" and (i == 0 or args[i - 1] != "--ref")]
    if not paths:
        print(__doc__)
        return 2
    bad = 0
    for raw in paths:
        for f in files_of(Path(raw)):
            old = at_ref(f, ref)
            if old is None:
                print(f"• {f}: new file (not in {ref}) — skipped")
                continue
            diffs = compare(old, f.read_text(encoding="utf-8"))
            if diffs:
                bad += 1
                print(f"✗ {f}")
                for d in diffs:
                    print(f"    {d}")
            else:
                print(f"✓ {f}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
