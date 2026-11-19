#!/usr/bin/env python3
"""Tests of the Polish hint index (`hint.pl.txt`) in the skill_hint hook: a skill translated into English keeps the
relevance for Polish prompts, because the hook adds the pre-translation text to the skill's content (the model does not load it).
The sources section (`## Sources` / `## Źródła`) does not go into the index. The owner's decision of 2026-11-17 (docs/todo.md, stage 4).
python3 core/tests/test_skill_hint_pl_index.py"""
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".claude" / "hooks" / "skill_hint.py").is_file()
            or (p / "core" / "hooks" / "skill_hint.py").is_file())
HOOKS = ROOT / ".claude" / "hooks" if (ROOT / ".claude" / "hooks" / "skill_hint.py").is_file() else ROOT / "core" / "hooks"

EN = """---
name: core-nightly
description: Use when an agent works unsupervised overnight — a contract and gates.
---
# Unsupervised work
Give the agent a contract before the start: a goal, a scope, a stop condition and a budget.

## Sources
- Harmonogram przeglądu zaległych zgłoszeń, księgowość faktur kosztowych.
"""
PL = """# Praca bez nadzoru
Agent puszczony na noc dostaje kontrakt: cel, zakres, warunek zatrzymania i budżet. Po trzeciej nieudanej
naprawie testu zatrzymuje się blokiem STOP, zamiast osłabiać asercję.
"""
OTHER = """---
name: core-other
description: Use for writing release notes and changelogs.
---
# Release notes
Write what changed for the user.
"""
PROMPT = "Puszczony na noc wykonawca trzeci raz nie przechodzi testu i chce poluzować asercję. Co ma zrobić?"
SOURCES_PROMPT = "Jak prowadzić księgowość faktur kosztowych i harmonogram przeglądu zaległych zgłoszeń?"


def load(skills: Path):
    spec = importlib.util.spec_from_file_location("hint_pl", HOOKS / "skill_hint.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SKILLS = skills
    return mod


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)
            print(f"✗ {msg}")

    with tempfile.TemporaryDirectory() as t:
        skills = Path(t) / "skills"
        for name, text in (("core-nightly", EN), ("core-other", OTHER)):
            (skills / name).mkdir(parents=True)
            (skills / name / "SKILL.md").write_text(text, encoding="utf-8")
        h = load(skills)
        picks = [it["name"] for _, it in h.select(PROMPT, h.load_index())]
        check("core-nightly" not in picks, f"HP-1: without the index a Polish prompt does not hit the English skill: {picks}")
        (skills / "core-nightly" / "hint.pl.txt").write_text(PL, encoding="utf-8")
        items = h.load_index()
        picks = [it["name"] for _, it in h.select(PROMPT, items)]
        check(picks[:1] == ["core-nightly"], f"HP-2: with hint.pl.txt a Polish prompt hits the skill: {picks}")
        nightly = next(it for it in items if it["name"] == "core-nightly")
        check("trzeci" not in nightly["excerpt"] and "Unsupervised" in nightly["excerpt"],
              f"HP-3: the excerpt shown to the model comes from SKILL.md, not from the index: {nightly['excerpt'][:120]}")
        picks = [it["name"] for _, it in h.select(SOURCES_PROMPT, items)]
        check("core-nightly" not in picks, f"HP-4: the ## Sources section does not go into the index: {picks}")
        (skills / "core-nightly" / "hint.pl.txt").write_text("head: delegacja pracy agentowi bez nadzoru, zamknięty laptop\n" + PL,
                                                             encoding="utf-8")
        nightly = next(it for it in h.load_index() if it["name"] == "core-nightly")
        check({"zamkn", "lapto"} <= nightly["head"] and "head" not in nightly["body"],
              f"HP-5: the index's 'head:' line weighs like the skill's description (the former Polish description and catalogue): {sorted(nightly['head'])[:12]}")
        # HP-6: the content length used to normalise the score is the longer of the two language versions, not their sum — otherwise
        # every translated skill raises the average length and the scores of all untranslated skills grow
        # (noise on general prompts), while the skill itself loses points for 'long' content (PR #305, pack-docs).
        en_only = set(h.stems(EN.split("---\n", 2)[2].split("## Sources")[0]))
        pl_only = set(h.stems(PL))
        check(nightly.get("blen") == max(len(en_only - nightly["head"]), len(pl_only - nightly["head"]))
              and nightly["blen"] < len(nightly["body"]),
              f"HP-6: the normalisation length = the longer language version: blen={nightly.get('blen')}, "
              f"body={len(nightly['body'])}")
        check(nightly.get("langs") == [en_only - nightly["head"], pl_only - nightly["head"]],
              f"HP-6b: the language versions of the content separately (the score counts the better-matching one): {nightly.get('langs')}")
        other = next(it for it in h.load_index() if it["name"] == "core-other")
        check(other.get("blen") == len(other["body"]), f"HP-7: a skill without an index: blen = the content length: {other.get('blen')}")
        shutil.rmtree(skills / "core-other")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the Polish hint index")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
