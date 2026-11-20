#!/usr/bin/env python3
"""Polish hint index for skills translated into English (stage 4, owner decision 2026-11-17).

  python3 tools/hint_pl_index.py core/skills/core-grounding core/skills/core-knowledge   # writes hint.pl.txt
  python3 tools/hint_pl_index.py --all                       # every English skill with Polish history
  python3 tools/hint_pl_index.py --all --check               # exit 1 when any is missing the index

The skill_hint hook matches a prompt by words. Polish prompts used to hit the Polish skill body; after translation
the body is English, so accuracy drops (measurement 4b-3: holdout 6/8 → 2/8). The script takes from git history the last
SKILL.md version with a Polish body and writes it next to the skill as `hint.pl.txt`: a `head:` line (the former description and catalog —
description weight) and the body (without the YAML header). The hook adds them to the index; the model does not load it (it is not a reference in SKILL.md). No model and no network.
Exit 0 — done; 1 — no index (--check) or no Polish version in history; 2 — bad invocation.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = "hint.pl.txt"
PL_LETTERS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")
LAYERS = ("core/skills", "packs/*/skills", "modes/*/skills")


def language(text: str) -> str:
    """The same rule as `skill_gate.content_language`: the share of Polish letters in the body without the header and code."""
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    body = re.sub(r"```.*?```|`[^`\n]*`", " ", body, flags=re.S)
    letters = [c for c in body if c.isalpha()]
    return "pl" if letters and sum(c in PL_LETTERS for c in letters) / len(letters) >= 0.004 else "en"


def body_of(text: str) -> str:
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).lstrip()


def head_of(text: str) -> str:
    """The former description and catalog (one line) — the hook counts them with the skill description weight, as before translation."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    fm = m.group(1) if m else ""
    desc = (re.search(r"^description:\s*(.*)$", fm, re.M) or [None, ""])[1].strip()
    kat = (re.search(r"^\s+catalog:\s*(.*)$", fm, re.M) or [None, ""])[1].strip().strip('"')
    return " ".join(f"{desc} {kat}".split())


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else ""


def polish_version(skill_md: Path) -> tuple[str, str] | None:
    """(sha, body) of the last file version with a Polish body; follows renames (`--follow`)."""
    rel = skill_md.relative_to(ROOT).as_posix()
    for entry in git("log", "--follow", "--format=%x00%H", "--name-only", "--", rel).split("\0")[1:]:
        parts = [x for x in entry.splitlines() if x.strip()]
        if len(parts) < 2:
            continue
        sha, path = parts[0], parts[-1]
        text = git("show", f"{sha}:{path}")
        if text and language(text) == "pl":
            return sha, text
    return None


def skills_all() -> list[Path]:
    return sorted(p.parent for pattern in LAYERS for p in ROOT.glob(f"{pattern}/*/SKILL.md"))


def write(skill: Path) -> str:
    md = skill / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    if language(text) == "pl":
        return f"• {skill.relative_to(ROOT)}: content is in Polish — no index needed"
    found = polish_version(md)
    if not found:
        return f"• {skill.relative_to(ROOT)}: no Polish version in history — skipped"
    sha, old = found
    (skill / INDEX).write_text(f"head: {head_of(old)}\n" + body_of(old), encoding="utf-8")
    return f"✓ {skill.relative_to(ROOT)}/{INDEX} ← {sha[:7]}"


def missing(skills: list[Path]) -> list[str]:
    """English skills that have a Polish version in history and have no index."""
    out = []
    for s in skills:
        if (s / INDEX).is_file() or language((s / "SKILL.md").read_text(encoding="utf-8")) == "pl":
            continue
        if polish_version(s / "SKILL.md"):
            out.append(s.relative_to(ROOT).as_posix())
    return out


def main(argv: list[str]) -> int:
    args = argv[1:]
    check = "--check" in args
    paths = [a for a in args if not a.startswith("--")]
    if "--all" in args:
        skills = skills_all()
    elif paths:
        skills = [(ROOT / p).resolve() for p in paths]
    else:
        print(__doc__)
        return 2
    if check:
        gaps = missing(skills)
        for g in gaps:
            print(f"✗ {g}: English content without {INDEX} — run python3 tools/hint_pl_index.py {g}")
        print("✓ every translated skill has a Polish hint index" if not gaps else f"✗ missing: {len(gaps)}")
        return 1 if gaps else 0
    for s in skills:
        print(write(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
