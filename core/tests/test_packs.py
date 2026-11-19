#!/usr/bin/env python3
"""Tests of the packs (.tf/factory/packs.py + build.py): assembling the configuration, contributions to personas and roles, the language condition,
optional packs, consultants, the dispatcher, version compatibility, migrations. python3 tests/test_packs.py"""
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "packs.py").is_file())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def core_range() -> str:
    """A range compatible with this installation's core version (the test data does not break on the next MAJOR)."""
    major = int((ROOT / ".tf" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0])
    return f">={major}.0.0 <{major + 1}.0.0"


def project(base: Path) -> Path:
    """A project with this installation's core (.tf/factory/, core skills: core-* and tf, hooks) and two artificial packs."""
    p = base / "proj"
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("packs", "__pycache__", "personas",
                                                                                     "roles"))
    for d in [*(ROOT / ".claude" / "skills").glob("core-*"), ROOT / ".claude" / "skills" / "tf"]:   # core skills
        shutil.copytree(d, p / ".claude" / "skills" / d.name)
    skill = "---\nname: {n}\ndescription: Użyj przy {n}.\nmetadata:\n  catalog: \"Użyj przy {n}. Nie do niczego.\"\n" \
            "  review: \"2099-01-01\"\n---\n# {n}\n"
    for n in ("aa-model", "aa-extra", "bb-tekst"):
        write(p / ".claude" / "skills" / n / "SKILL.md", skill.format(n=n))
    a = p / ".tf" / "factory" / "packs" / "pack-a"
    write(a / "pack.yaml", """id: pack-a
version: 1.0.0
title: A
requires: {core: "CORE_RANGE"}
optional_packs: [pack-b, pack-c]
facets:
  - {prefix: aa-, order: 10, name: wymiar A, question: "co w A"}
always_skills: [aa-extra]
consultants:
  a-consult:
    tier: std
    description: Konsultant A — test.
    skills: [aa-model]
contributes:
  roles:
    rola-b: {skills: [aa-model]}
""")
    write(a / "roles" / "rola-a.yaml", "name: rola-a\ntitle: Rola A\ntier: std\ntriggers: a\nidentity: a\n"
                                        "tools: [Read, Skill]\nskills: [aa-model, cc-nieznany]\ngrounding: sources-only\n")
    write(a / "personas" / "ala.yaml", "name: ala\ntitle: Ala\ndescription: Persona A.\nidentity: a\ndispatcher: true\n"
                                         "roles: [rola-a, rola-c]\nskills: [aa-model]\ncore_skills: [core-git-workflow]\n"
                                         "traits: [grounded, cecha-c]\npriorities: [jakość]\n"
                                         "extra_agents: [cyryl-rola-c]\n")
    b = p / ".tf" / "factory" / "packs" / "pack-b"
    write(b / "pack.yaml", """id: pack-b
version: 1.0.0
title: B
requires: {core: "CORE_RANGE"}
facets:
  - {prefix: bb-, order: 20, name: wymiar B, question: "co w B"}
contributes_when: {targets: [claude]}
contributes:
  personas: {traits: [cecha-b], core_skills: [bb-tekst]}
routing: |
  | sygnał B | b-agent | std |
shared_agents:
  b-agent:
    tier: std
    description: Agent B.
    tools: [Read]
    prompt: Jestem B.
  b-main:
    tier: std
    main_only: true
    description: Sesja główna B.
    tools: ["Agent(scout, scope-reviewer)", Read]
    prompt: Przeczytaj `.claude/skills/bb-tekst/SKILL.md`.
consultants:
  b-consult:
    tier: std
    description: Konsultant B — test.
    skills: [bb-tekst]
""")
    write(b / "traits" / "cecha-b.md", "**Cecha B**\n- tak")
    write(b / "roles" / "rola-b.yaml", "name: rola-b\ntitle: Rola B\ntier: std\ntriggers: b\nidentity: b\n"
                                        "tools: [Read, Edit, Skill]\nskills: [bb-tekst]\n")
    write(b / "personas" / "bolek.yaml", "name: bolek\ntitle: Bolek\ndescription: Persona B.\nidentity: b\n"
                                           "roles: [rola-b]\ntraits: [grounded]\npriorities: [jakość]\n"
                                           "isolation: worktree\n"
                                           "scenarios:\n  - {situation: klient pyta o cenę, behavior: odsyłasz do cennika}\n")
    for y in (a / "pack.yaml", b / "pack.yaml"):
        y.write_text(y.read_text(encoding="utf-8").replace("CORE_RANGE", core_range()), encoding="utf-8")
    return p


def load(p: Path, name: str):
    spec = importlib.util.spec_from_file_location(f"tp_{name}_{id(p)}", p / ".tf" / "factory" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(p / ".tf" / "factory"))
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p = project(Path(t))
        b = load(p, "build")
        pm = b.packs_mod
        cfg = b.load_config()
        check([f["prefix"] for f in cfg["facets"]][:2] == ["aa-", "bb-"], f"P-1: the packs' facets by order: {cfg['facets'][:2]}")
        check("b-agent" in cfg["shared_agents"] and "| sygnał B |" in cfg["routing"],
              "P-2: the pack's agent and routing row when contributes_when is met (default targets: [claude])")
        roles, personas, traits, skills, errors = b.load_team(cfg)
        ala = personas["ala"]
        check(ala["roles"] == ["rola-a"] and "rola rola-c" in ala["_dropped"] and "cecha cecha-c" in ala["_dropped"]
              and ala["extra_agents"] == [], f"P-3: references to the optional pack (pack-c) skipped: {ala}")
        check("cc-nieznany" not in roles["rola-a"]["skills"], "P-4: an unknown skill of a role from a pack with a missing optional pack is skipped")
        check("cecha-b" in ala["traits"] and "bb-tekst" in ala["core_skills"], f"P-5: pack-b's contribution to other packs' personas: {ala}")
        check("aa-model" in roles["rola-b"]["skills"], f"P-6: pack-a's contribution to a role from pack-b: {roles['rola-b']['skills']}")
        check("aa-extra" in b.persona_skills(ala, roles, cfg) and "aa-extra" not in b.persona_skills(personas["bolek"], roles, cfg),
              "P-7: a pack's always_skills only for its own personas")
        rendered = b.render_all()
        ala_md, bolek_md = rendered["ala/ala.md"], rendered["bolek/bolek.md"]
        check("b-consult" in ala_md and "a-consult" not in ala_md and "a-consult" in bolek_md and "b-consult" not in bolek_md,
              "P-8: a persona sees the consultants of other packs, not of its own")
        check("consult/a-consult.md" in rendered and "tools: Read, Grep, Glob, Skill" in rendered["consult/a-consult.md"],
              "P-9: konsultant tylko do odczytu")
        check("specialist" in ala_md.split("\n")[3] and "specialist" not in bolek_md.split("\n")[3],
              "P-10: specialist (@dispatcher) only for a persona with dispatcher: true")
        check("## Language" in ala_md and "in the language the human writes in" in ala_md and "commit messages" in ala_md,
              "P-11: the language section in a persona (conversation rule, commits)")
        # 3.1.0: executors ask consultants themselves (nesting subagents), consultants do not delegate further
        rendered = b.render_all()
        ala_w, bolek_w = rendered["ala/ala-rola-a.md"], rendered["bolek/bolek-rola-b.md"]
        check("Agent" in ala_w.split("---")[1] and "b-consult" in ala_w and "a-consult" not in ala_w,
              "P-19: an executor has the Agent tool and sees the consultants of other packs")
        cons = rendered["consult/a-consult.md"].split("---")[1]
        check("disallowedTools: Agent" in cons and "omitClaudeMd: true" in cons,
              f"P-20: a consultant without Agent and without CLAUDE.md: {cons}")
        check("nie wywołują konsultantów" not in " ".join(rendered["ala/ala.md"].split()), "P-21: the persona does not forbid executors to consult")
        check("isolation: worktree" in bolek_w.split("---")[1] and "isolation" not in ala_w.split("---")[1],
              "P-22: a persona's isolation only for executors that edit files")
        cfg0 = b.load_config()
        for key in ("work_contract", "style_note", "untrusted_note"):
            txt = cfg0.get(key, "").strip()
            check(txt and all(txt.splitlines()[0] in rendered[f] for f in
                              ("ala/ala.md", "ala/ala-rola-a.md", "shared/scout.md", "consult/a-consult.md")),
                  f"P-23: `{key}` in the persona, executor, shared agent and consultant")
        rc = cfg0["report_contract"]
        check(all(s in rc for s in ("**Result:**", "**Changed files:**", "**Verification:**", "**Uncertain:**",
                                    "**To decide:**")), "P-24: the fixed executor report template")
        check("## Typical situations" in rendered["bolek/bolek.md"] and "odsyłasz do cennika" in rendered["bolek/bolek.md"]
              and "## Typical situations" not in rendered["ala/ala.md"], "P-25: the persona field `scenarios`")
        check("effort: low" in rendered["shared/scout.md"].split("---")[1], "P-26: tier fast with effort low")
        main = rendered.get("shared/b-main.md", "")
        mfm = main.split("---")[1] if main else ""
        check("Agent(scout, scope-reviewer)" in mfm and "skills:" not in mfm and "maxTurns" not in mfm
              and "`b-main`" not in rendered["ala/ala.md"] and "`scope-reviewer`" in rendered["ala/ala.md"],
              "P-30: a main_only pack agent — a main session with a list of agents, without maxTurns, not for personas; "
              "scope-reviewer for personas")
        so = (cfg0.get("sources_only_note") or "").strip()
        check(so and so.splitlines()[0] in rendered["ala/ala-rola-a.md"] and so.splitlines()[0] in rendered["consult/a-consult.md"]
              and so.splitlines()[0] not in rendered["bolek/bolek-rola-b.md"],
              "P-29: grounding: a role's sources-only and consultants → the 'only from the given materials' section")
        e, _ = b.validate()
        check(not [x for x in e if "stale" not in x],   # the agent files are not built — irrelevant here
              f"P-12: the assembled configuration without errors: {e}")

        # other targets: pack-b dormant — no contribution, agent or routing row
        pm.save_settings(p, targets=["claude", "managed-agents"])
        cfg = b.load_config()
        roles, personas, traits, skills, errors = b.load_team(cfg)
        check("b-agent" not in cfg["shared_agents"] and "sygnał B" not in cfg["routing"]
              and "cecha-b" not in personas["ala"]["traits"] and "b-consult" not in cfg["consultants"],
              "P-13: contributes_when not met → the pack is dormant")
        md = b.render_all()["ala/ala.md"]
        check("in the language the human writes in" in md and "CHANGELOG entries in English" in md,
              "P-14: the conversation language rule and commits of a new repository (no history) in English in the prompt")
        pm.save_settings(p, targets=["claude"])   # back to the default — further steps without the managed-agents target

        # bad isolation and scenarios → validation errors
        bp = p / ".tf" / "factory" / "packs" / "pack-b" / "personas" / "bolek.yaml"
        saved = bp.read_text()
        bp.write_text(saved.replace("isolation: worktree", "isolation: kontener").replace("behavior: odsyłasz do cennika", "x: y"))
        rp = p / ".tf" / "factory" / "packs" / "pack-a" / "roles" / "rola-a.yaml"
        rsaved = rp.read_text()
        rp.write_text(rsaved.replace("grounding: sources-only", "grounding: pamiec"))
        e, _ = b.validate()
        check(any("isolation" in x for x in e) and any("scenarios[0]" in x for x in e) and any("grounding" in x for x in e),
              f"P-27: walidacja isolation, scenarios i grounding: {e}")
        bp.write_text(saved)
        rp.write_text(rsaved)

        # a skill does not set model, effort or paths (cache and skill visibility)
        sk = p / ".claude" / "skills" / "aa-extra" / "SKILL.md"
        saved = sk.read_text()
        sk.write_text(saved.replace("name: aa-extra\n", "name: aa-extra\nmodel: haiku\npaths: src/**\n"))
        _, w = b.validate()
        check(any("aa-extra" in x and "field model" in x for x in w) and any("aa-extra" in x and "paths" in x for x in w),
              f"P-28: a skill with model/paths → validation warning: {w}")
        sk.write_text(saved)

        # core version compatibility and required packs
        y = p / ".tf" / "factory" / "packs" / "pack-a" / "pack.yaml"
        y.write_text(y.read_text().replace(f'requires: {{core: "{core_range()}"}}', 'requires: {core: ">=' + str(int((ROOT / ".tf" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0]) + 1)
                     + '.0.0", packs: [pack-z]}'))   # always a newer major than the installed core
        e, _ = b.check_packs(b.load_config())
        check(any("requires core" in x for x in e) and any("tf add pack-z" in x for x in e),
              f"P-15: an incompatible core and a missing required pack → errors: {e}")

        # migrations: the project's own persona with an old skill name
        write(p / ".tf" / "config" / "personas" / "moja.yaml", "name: moja\nskills: [core-tech-docs, fe-ux-design]\n")
        mig = load(p, "migrations")
        todo = mig.apply(p, dry=True)
        check(todo and "docs-tech-writing" in todo[0] and "core-tech-docs" in (p / ".tf/config/personas/moja.yaml").read_text(),
              f"P-16: a dry-run migration shows the change and writes nothing: {todo}")
        mig.apply(p, dry=False)
        text = (p / ".tf/config/personas/moja.yaml").read_text()
        check("docs-tech-writing" in text and "ux-feature-design" in text, f"P-17: migracja poprawia plik projektu: {text}")
        # renames from a pack (`renames` in pack.yaml) — the core does not list the packs' skills
        y = p / ".tf" / "factory" / "packs" / "pack-a" / "pack.yaml"
        y.write_text(y.read_text() + 'renames:\n  "1.0.0": {aa-stary: aa-model}\n')
        write(p / ".tf" / "config" / "personas" / "moja2.yaml", "name: moja2\nskills: [aa-stary]\n")
        mig = load(p, "migrations")
        mig.apply(p, dry=False)
        text = (p / ".tf/config/personas/moja2.yaml").read_text()
        check("aa-model" in text and "aa-stary" not in text, f"P-17b: migration per the pack's `renames`: {text}")

        # the language section in CLAUDE.local.md
        md_p = p / "CLAUDE.local.md"
        md_p.write_text("x\n<!-- team-factory:begin -->\n## Agent team\n### Language\n- stare\n<!-- team-factory:end -->\n")
        changed = pm.write_language_lines(md_p, pm.load_yaml(p / ".tf" / "factory" / "config.yaml"), p)
        txt = md_p.read_text()
        check(changed and "- stare" not in txt and "in the language the human writes in" in txt and "### Language\n" in txt and txt.startswith("x\n"),
              f"P-18: replacing the language section in the factory block: {txt}")

    # Company pack (org_defaults): the organization's defaults between the engine and the project.
    with tempfile.TemporaryDirectory() as t:
        p = project(Path(t))
        pm = load(p, "build").packs_mod
        org = p / ".tf" / "factory" / "packs" / "pack-firma"
        write(org / "pack.yaml", f"""id: pack-firma
version: 0.1.0
title: Firma
requires: {{core: "{core_range()}"}}
org_defaults:
  config:
    work: {{budget_usd: 3, task_budget_usd: 9}}
    autonomy: {{operations: {{git_push: deny}}}}
    facets: [{{prefix: zz-}}]
  operations:
    tracker: {{type: jira, prefixes: {{ACME: jira}}, url: "https://evil.example"}}
""")
        write(p / ".tf" / "config" / "config.yaml", "work:\n  budget_usd: 5\n")
        cfg = pm.load_config(p)
        total += 1
        if cfg.get("work", {}).get("budget_usd") != 5 or cfg.get("work", {}).get("task_budget_usd") != 9 \
                or cfg.get("autonomy", {}).get("operations", {}).get("git_push") != "deny":
            fails.append(f"ORG-1: silnik ← organizacja ← projekt (projekt wygrywa, reszta z organizacji): {cfg.get('work')}")
        labels = [lbl for lbl, _ in pm.config_layers(p)]
        total += 1
        if len(labels) != 3 or "pack-firma" not in labels[1]:
            fails.append(f"ORG-2: configuration layers labelled with their source: {labels}")
        comp = pm.compose(p, cfg)
        total += 1
        if not any("facets" in e and "org_defaults" in e for e in comp["_errors"]) \
                or any(f.get("prefix") == "zz-" for f in comp["facets"]):
            fails.append(f"ORG-3: a key outside the list in org_defaults.config — an error with no effect: {comp['_errors']}")
        ops = pm.org_operations(p)
        total += 1
        if ops.get("tracker", {}).get("prefixes") != {"ACME": "jira"} or "url" in ops.get("tracker", {}):
            fails.append(f"ORG-4: the organization's default tracker without an address (the address only from the JIRA_BASE_URL variable): {ops}")
        wcfg = load(p, "work").config(p)
        total += 1
        if wcfg.get("budget_usd") != 5 or wcfg.get("task_budget_usd") != 9:
            fails.append(f"ORG-6: the unsupervised work budget (work.py) with the organization layer: {wcfg}")
        write(p / ".tf" / "factory" / "packs" / "pack-firma2" / "pack.yaml", f"""id: pack-firma2
version: 0.1.0
title: Firma 2
requires: {{core: "{core_range()}"}}
org_defaults: {{config: {{work: {{budget_usd: 1}}}}}}
""")
        comp = pm.compose(p, pm.load_config(p))
        total += 1
        if not any("org_defaults" in e and "pack-firma2" in e for e in comp["_errors"]):
            fails.append(f"ORG-5: two packs with org_defaults → error: {comp['_errors']}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} pack tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
