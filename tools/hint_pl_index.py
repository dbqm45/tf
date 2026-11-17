#!/usr/bin/env python3
"""Polski indeks podpowiedzi dla skilli przetłumaczonych na angielski (etap 4, decyzja właściciela 2026-11-17).

  python3 tools/hint_pl_index.py core/skills/core-grounding core/skills/core-knowledge   # zapis hint.pl.txt
  python3 tools/hint_pl_index.py --all                       # każdy angielski skill z polską historią
  python3 tools/hint_pl_index.py --all --check               # kod 1, gdy któremuś brakuje indeksu

Hook skill_hint dopasowuje polecenie słowami. Polskie polecenia trafiały w polską treść skilla; po tłumaczeniu
treść jest angielska, więc trafność spada (pomiar 4b-3: holdout 6/8 → 2/8). Skrypt bierze z historii gita ostatnią
wersję SKILL.md z polską treścią i zapisuje jej treść (bez nagłówka YAML) obok skilla jako `hint.pl.txt`. Hook
dokłada ten tekst do indeksu; model go nie wczytuje (nie jest odwołaniem w SKILL.md). Bez modelu i bez sieci.
Kod 0 — gotowe; 1 — brak indeksu (--check) albo brak polskiej wersji w historii; 2 — złe wywołanie.
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
    """Ta sama reguła co `skill_gate.content_language`: udział polskich liter w treści bez nagłówka i kodu."""
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    body = re.sub(r"```.*?```|`[^`\n]*`", " ", body, flags=re.S)
    letters = [c for c in body if c.isalpha()]
    return "pl" if letters and sum(c in PL_LETTERS for c in letters) / len(letters) >= 0.004 else "en"


def body_of(text: str) -> str:
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).lstrip()


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else ""


def polish_version(skill_md: Path) -> tuple[str, str] | None:
    """(sha, treść) ostatniej wersji pliku z polską treścią; śledzi zmiany nazw (`--follow`)."""
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
        return f"• {skill.relative_to(ROOT)}: treść po polsku — indeks niepotrzebny"
    found = polish_version(md)
    if not found:
        return f"• {skill.relative_to(ROOT)}: brak polskiej wersji w historii — pominięty"
    sha, old = found
    (skill / INDEX).write_text(body_of(old), encoding="utf-8")
    return f"✓ {skill.relative_to(ROOT)}/{INDEX} ← {sha[:7]}"


def missing(skills: list[Path]) -> list[str]:
    """Angielskie skille, które mają polską wersję w historii, a nie mają indeksu."""
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
            print(f"✗ {g}: angielska treść bez {INDEX} — uruchom python3 tools/hint_pl_index.py {g}")
        print("✓ każdy przetłumaczony skill ma polski indeks podpowiedzi" if not gaps else f"✗ braków: {len(gaps)}")
        return 1 if gaps else 0
    for s in skills:
        print(write(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
