#!/usr/bin/env python3
"""
Przegląd PR przez AI w CI (skill core-git-workflow, references/ai-review-in-ci.md).

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
        print(f"✗ {WORKFLOW} already exists — not overwriting it (use --force if this is intended)")
        return 1
    text = TEMPLATE.read_text(encoding="utf-8")
    if all_prs:
        assert LABEL_IF in text, "template: the label condition is missing"
        text = text.replace(LABEL_IF, ALL_IF)
    WORKFLOW.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOW.write_text(text, encoding="utf-8")
    who = "every PR from this repository" if all_prs else "PRs with the ai-review label"
    print(f"✓ {WORKFLOW} — reviews {who}. Set the ANTHROPIC_API_KEY secret and require the "
          "ai-review/verdict status in branch protection; override: the ai-review-override label (a human adds it).")
    if not Path("REVIEW.md").is_file():
        hint = (f"the approved draft from the reconstruction: `ai_review.py review-md` ({DRAFT})" if DRAFT.is_file()
                else "template: .claude/skills/core-git-workflow/references/review-md.md; after reconstruction from the code, "
                     "`ai_review.py review-md` moves the approved draft")
        print(f"⚠ no REVIEW.md — the review will use the default passes. Rules: {hint}")
    return 0


def review_md(src: str | None, force: bool) -> int:
    draft = Path(src) if src else DRAFT
    if not draft.is_file():
        print(f"✗ no draft {draft} — it is made in reconstruction from the code (REVIEW.draft.md), or give --from FILE")
        return 1
    target = Path("REVIEW.md")
    if target.exists() and not force:
        print(f"✗ {target} already exists — not overwriting it (use --force if a human approved the change)")
        return 1
    shutil.copyfile(draft, target)
    print(f"✓ {target} ← {draft}. Change the rules later through a PR, like code changes.")
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
