#!/usr/bin/env python3
"""Tests of build.py: skills without a role and persona (standalone_skills), the delegation rule in the orchestrator prompt."""
import importlib.util
import re
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "build.py").is_file())


def load():
    spec = importlib.util.spec_from_file_location("ctf_build", ROOT / ".tf" / "factory" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    b = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    skills = ["a", "b", "dom-x"]
    errors, warnings = b.skill_usage(skills, {"a"}, {})
    check(errors == [] and len(warnings) == 2 and all("not used by" in w for w in warnings),
          f"SU-1: unused skills → warnings: {errors} {warnings}")
    errors, warnings = b.skill_usage(skills, {"a"}, {"standalone_skills": ["dom-x"]})
    check(errors == [] and warnings == ["skill b: not used by any role or persona"],
          f"SU-2: a standalone skill without a warning: {errors} {warnings}")
    errors, _ = b.skill_usage(skills, {"a"}, {"standalone_skills": ["brak"]})
    check(errors == ["standalone_skills: unknown skill 'brak'"], f"SU-3: an unknown standalone skill → error: {errors}")
    _, warnings = b.skill_usage(skills, {"a", "dom-x"}, {"standalone_skills": ["dom-x"]})
    check(any("dom-x" in w and "standalone_skills" in w for w in warnings),
          f"SU-4: a standalone skill used by a persona → warning about a redundant entry: {warnings}")

    # The skill list budget computed as in the project (skill_profile): technologies and dom-* without a description, plus a reserve
    # for technologies detected in a typical project (the N longest technology entries).
    entries = {"eng-a": 100, "core-b": 50, "dom-x": 400, "fw-angular": 300, "lang-java": 200, "tool-nx": 120}
    check(b.skill_listing(entries, 2, name_only=("dom-",)) == 100 + 50 + 300 + 200,
          f"LB-1: described skills + the 2 longest technologies, without dom-* (the pack's 'name only' prefix): "
          f"{b.skill_listing(entries, 2, name_only=('dom-',))}")
    check(b.skill_listing(entries, 0, name_only=("dom-",)) == 150, "LB-2: without the technology reserve")
    check(b.skill_listing(entries, 0) == 550, f"LB-3: without the packs' prefixes dom-* with a description: {b.skill_listing(entries, 0)}")

    # Review deadline (metadata.review): the date format is checked; changing only the deadline does not invalidate the gate.
    check(b.check_review_date("eng-a", {"review": "2027-04-17"}) == ([], []), "RD-1: poprawna data bez uwag")
    errors, _ = b.check_review_date("eng-a", {"review": "kwiecień"})
    check(len(errors) == 1 and "review" in errors[0], f"RD-2: a bad date format → error: {errors}")
    errors, warnings = b.check_review_date("eng-a", {"review": __import__("datetime").date(2027, 4, 17)})
    check(errors == [] and len(warnings) == 1 and "without quotes" in warnings[0],
          f"RD-2b: an unquoted YAML date → warning (Agent Skills specification: metadata is text): {errors} {warnings}")
    errors, warnings = b.check_review_date("eng-a", {})
    check(errors == [] and len(warnings) == 1 and "freshness.py" in warnings[0],
          f"RD-3: no deadline → a warning with a command: {warnings}")
    with tempfile.TemporaryDirectory() as t:
        old = b.SKILLS_DIR
        b.SKILLS_DIR = Path(t)
        md = Path(t) / "eng-odcisk" / "SKILL.md"
        md.parent.mkdir()
        head = "---\nname: eng-odcisk\nmetadata:\n  catalog: \"x\"\n  review: {}\n---\n# Treść\n"
        md.write_text(head.format("2026-10-17"))
        f1 = b.skill_fingerprint("eng-odcisk")
        md.write_text(head.format("2027-10-17"))
        f2 = b.skill_fingerprint("eng-odcisk")
        md.write_text(head.format("2027-10-17") + "Nowy akapit.\n")
        f3 = b.skill_fingerprint("eng-odcisk")
        b.SKILLS_DIR = old
    check(f1 == f2 and f2 != f3, f"RD-4: the gate fingerprint ignores the review deadline but not the content: {f1} {f2} {f3}")

    # The core version range required by a pack (pack.yaml → requires.core).
    check(b.version_ok("3.0.0", ">=3.0.0 <4.0.0") and b.version_ok("3.9.1", ">=3.0.0 <4.0.0"),
          "VR-1: wersja w zakresie")
    check(not b.version_ok("4.0.0", ">=3.0.0 <4.0.0") and not b.version_ok("2.45.0", ">=3.0.0"),
          "VR-2: wersja poza zakresem")

    # The orchestrator does the task itself; it delegates only when handing over pays off (cost and quality).
    rendered = b.render_all()
    orchestrators = {k: v for k, v in rendered.items() if not k.startswith(("shared/", "consult/"))
                     and Path(k).stem == Path(k).parent.name}
    check(orchestrators or not b.load_dir("personas"), "OR-0: orchestrator prompts exist (when packs provide personas)")
    for k, t in orchestrators.items():
        check("Resztę delegujesz" not in t, f"OR-1 {k}: the 'delegate the rest' rule is gone")
        check("By default you do the task yourself" in t, f"OR-2 {k}: the default rule — you do the task yourself")
        check("## Language" in t, f"OR-4 {k}: the work and commit language section")
        sec = re.search(r"^## When you delegate\n(.*?)(?=^## )", t, re.M | re.S)
        body = sec.group(1) if sec else ""
        check(sec and all(w in body for w in ("scout", "in parallel", "fresh look", "Do not split")),
              f"OR-3 {k}: the 'When you delegate' section with the cases where handing over pays off")

    # A disabled skill (metadata.status: inactive, docs/inactive-skills.md): stays in the installation but disappears from the lists
    # of role skills, personas, shared agents, consultants and always_skills — without changing the packs' YAML files.
    skills_meta = {"a": {}, "b": {"metadata": {"status": "inactive"}}, "c": {"metadata": {"status": "aktywny"}}}
    check(b.inactive_skills(skills_meta) == {"b"}, f"IN-1: only a skill with the status inactive is disabled: "
          f"{b.inactive_skills(skills_meta)}")
    cfg_in = {"always_skills": ["a", "b"], "_packs": {"p": {"always_skills": ["b", "c"]}},
              "shared_agents": {"s": {"skills": ["b", "c"]}}, "consultants": {"k": {"skills": ["a", "b"]}}}
    roles_in = {"r": {"skills": ["a", "b"], "preload": ["b"]}}
    personas_in = {"x": {"skills": ["b", "c"], "methods": ["b"], "role_skills": {"r": ["a", "b"]}}}
    b.drop_inactive(cfg_in, roles_in, personas_in, {"b"})
    check(cfg_in["always_skills"] == ["a"] and cfg_in["_packs"]["p"]["always_skills"] == ["c"],
          f"IN-2: the core's and packs' always_skills without the disabled ones: {cfg_in}")
    check(cfg_in["shared_agents"]["s"]["skills"] == ["c"] and cfg_in["consultants"]["k"]["skills"] == ["a"],
          f"IN-3: shared agents and consultants without the disabled ones: {cfg_in}")
    check(roles_in["r"] == {"skills": ["a"], "preload": []}, f"IN-4: a role without the disabled ones: {roles_in}")
    check(personas_in["x"]["skills"] == ["c"] and personas_in["x"]["methods"] == []
          and personas_in["x"]["role_skills"] == {"r": ["a"]}, f"IN-5: a persona without the disabled ones: {personas_in}")
    check(cfg_in["_inactive"] == ["b"], f"IN-6: the list of disabled skills in the configuration: {cfg_in.get('_inactive')}")
    _, warnings = b.skill_usage(["a", "b"], {"a"}, {"_inactive": ["b"]})
    check(warnings == [], f"IN-7: a disabled skill without the 'is not used' warning: {warnings}")
    texts = {"s/SKILL.md": "Zobacz tool-nx.\nInne: tool-nxx, my-tool-nx, tool-nx-plus.\n(**tool-nx**), lista: a, tool-nx"}
    hits = b.inactive_mentions({"tool-nx"}, texts)
    check(hits == ["s/SKILL.md:1: tool-nx", "s/SKILL.md:3: tool-nx", "s/SKILL.md:3: tool-nx"],
          f"IN-10: a mention of a disabled skill only as a whole word, with the line number: {hits}")
    # The factory content (active skills and generated agents) does not point to disabled skills.
    left = b.inactive_mentions(set(b.inactive_skills(b.load_skills())), b.active_texts())
    check(not left, f"IN-11: active skills and agents point to disabled skills: {left[:5]}")
    catalog = b.render_catalog()
    for n in b.inactive_skills(b.load_skills()):
        check(f"- `{n}` —" not in catalog, f"IN-8: the disabled skill {n} is outside the catalog's facet list")
        check(n in catalog.split("## Disabled skills", 1)[-1], f"IN-9: the disabled skill {n} in the 'Disabled skills' section")

    # An agent's own `maxTurns` beats its tier's (mcp-runner: a brief is a few MCP calls, not a search); main_only has none.
    cfg_mt = {"tiers": {"fast": {"model": "haiku", "effort": "low", "maxTurns": 15}}}
    _, own = b.render_shared("r", {"tier": "fast", "description": "d", "tools": [], "prompt": "p", "maxTurns": 6}, cfg_mt)
    _, tier = b.render_shared("s", {"tier": "fast", "description": "d", "tools": [], "prompt": "p"}, cfg_mt)
    _, main = b.render_shared("m", {"tier": "fast", "description": "d", "tools": [], "prompt": "p", "maxTurns": 6,
                                    "main_only": True}, cfg_mt)
    check("maxTurns: 6" in own and "maxTurns: 15" in tier and "maxTurns" not in main,
          f"MT-1: maxTurns per agent over the tier, none for main_only: {own[:200]} | {tier[:200]} | {main[:200]}")
    runner = b.load_config()["shared_agents"]["mcp-runner"]
    check(runner.get("maxTurns") == 6 and "at most 3 tool calls" in runner["prompt"] and "one tool search" in runner["prompt"]
          and "never page" in runner["prompt"] and "never delete" in runner["prompt"],
          f"MT-2: mcp-runner has a turn limit of 6, a call budget, one tool search, no paging beyond the brief, read-only by default: "
          f"{runner.get('maxTurns')}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} build.py tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
