#!/usr/bin/env python3
"""
Przegląd PR przez AI w CI (skill core-git-workflow, references/przeglad-ai-w-ci.md).

  python3 .claude/skills/core-git-workflow/scripts/ai_review.py install [--force] [--all-prs]
      zapisuje .github/workflows/ai-review.yml z szablonu obok skryptu: przegląd PR z etykietą ai-review
      (--all-prs: każdego PR z tego repo), werdykt jako status ai-review/verdict, jeden komentarz zbiorczy,
      obejście etykietą ai-review-override; istniejącego pliku nie nadpisuje bez --force
  python3 .claude/skills/core-git-workflow/scripts/ai_review.py review-md [--from PLIK] [--force]
      zatwierdzony szkic zasad (domyślnie docs/project/00-reconstruction/REVIEW.draft.md z rekonstrukcji z kodu)
      → REVIEW.md w katalogu głównym; istniejącego REVIEW.md nie nadpisuje bez --force

Szkic zatwierdza człowiek — polecenie review-md uruchamiasz po jego zgodzie. Kod wyjścia: 0 — zapisane,
1 — odmowa (plik istnieje, brak szkicu), 2 — złe wywołanie. Tylko biblioteka standardowa Pythona 3.9+.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "ai-review.yml"
WORKFLOW = Path(".github") / "workflows" / "ai-review.yml"
DRAFT = Path("docs") / "project" / "00-reconstruction" / "REVIEW.draft.md"
LABEL_IF = ("      contains(github.event.pull_request.labels.*.name, 'ai-review') &&\n"
            "      (github.event.action != 'labeled' && github.event.action != 'unlabeled' || "
            "github.event.label.name == 'ai-review')\n")
ALL_IF = "      github.event.action != 'labeled' && github.event.action != 'unlabeled'\n"


def install(force: bool, all_prs: bool) -> int:
    if WORKFLOW.exists() and not force:
        print(f"✗ {WORKFLOW} już istnieje — nie nadpisuję (--force, jeśli to celowe)")
        return 1
    text = TEMPLATE.read_text(encoding="utf-8")
    if all_prs:
        assert LABEL_IF in text, "szablon: brak warunku etykiety"
        text = text.replace(LABEL_IF, ALL_IF)
    WORKFLOW.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOW.write_text(text, encoding="utf-8")
    who = "każdego PR z tego repozytorium" if all_prs else "PR z etykietą ai-review"
    print(f"✓ {WORKFLOW} — przegląd {who}. Ustaw sekret ANTHROPIC_API_KEY i w ochronie gałęzi wymagaj statusu "
          "ai-review/verdict; obejście: etykieta ai-review-override (dodaje człowiek).")
    if not Path("REVIEW.md").is_file():
        hint = (f"zatwierdzony szkic z rekonstrukcji: `ai_review.py review-md` ({DRAFT})" if DRAFT.is_file()
                else "szablon: .claude/skills/core-git-workflow/references/review-md.md; po rekonstrukcji z kodu "
                     "`ai_review.py review-md` przenosi zatwierdzony szkic")
        print(f"⚠ brak REVIEW.md — przegląd użyje przebiegów domyślnych. Zasady: {hint}")
    return 0


def review_md(src: str | None, force: bool) -> int:
    draft = Path(src) if src else DRAFT
    if not draft.is_file():
        print(f"✗ brak szkicu {draft} — powstaje w rekonstrukcji z kodu (REVIEW.draft.md) albo podaj --from PLIK")
        return 1
    target = Path("REVIEW.md")
    if target.exists() and not force:
        print(f"✗ {target} już istnieje — nie nadpisuję (--force, jeśli człowiek zatwierdził zmianę)")
        return 1
    shutil.copyfile(draft, target)
    print(f"✓ {target} ← {draft}. Zmiany zasad dalej przez PR, jak zmiany kodu.")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("install")
    i.add_argument("--force", action="store_true")
    i.add_argument("--all-prs", action="store_true")
    r = sub.add_parser("review-md")
    r.add_argument("--from", dest="src")
    r.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    return install(a.force, a.all_prs) if a.cmd == "install" else review_md(a.src, a.force)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
