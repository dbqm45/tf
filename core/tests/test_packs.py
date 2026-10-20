#!/usr/bin/env python3
"""Testy nakładek (factory/packs.py + build.py): składanie konfiguracji, wkład do person i ról, warunek języka,
nakładki opcjonalne, konsultanci, dyspozytor, zgodność wersji, migracje. python3 tests/test_packs.py"""
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "packs.py").is_file())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def project(base: Path) -> Path:
    """Projekt z rdzeniem tej instalacji (factory/, skille core-*, hooki) i dwiema sztucznymi nakładkami."""
    p = base / "proj"
    shutil.copytree(ROOT / "factory", p / "factory", ignore=shutil.ignore_patterns("packs", "__pycache__", "personas",
                                                                                     "roles"))
    for d in (ROOT / ".claude" / "skills").glob("core-*"):
        shutil.copytree(d, p / ".claude" / "skills" / d.name)
    skill = "---\nname: {n}\ndescription: Użyj przy {n}.\nmetadata:\n  katalog: \"Użyj przy {n}. Nie do niczego.\"\n" \
            "  przeglad: 2099-01-01\n---\n# {n}\n"
    for n in ("aa-model", "aa-extra", "bb-tekst"):
        write(p / ".claude" / "skills" / n / "SKILL.md", skill.format(n=n))
    a = p / "factory" / "packs" / "pack-a"
    write(a / "pack.yaml", """id: pack-a
version: 1.0.0
title: A
requires: {core: ">=3.0.0 <4.0.0"}
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
                                        "tools: [Read, Skill]\nskills: [aa-model, cc-nieznany]\n")
    write(a / "personas" / "ala.yaml", "name: ala\ntitle: Ala\ndescription: Persona A.\nidentity: a\ndispatcher: true\n"
                                         "roles: [rola-a, rola-c]\nskills: [aa-model]\ncore_skills: [core-git-workflow]\n"
                                         "traits: [grounded, cecha-c]\npriorities: [jakość]\n"
                                         "extra_agents: [cyryl-rola-c]\n")
    b = p / "factory" / "packs" / "pack-b"
    write(b / "pack.yaml", """id: pack-b
version: 1.0.0
title: B
language: pl
requires: {core: ">=3.0.0 <4.0.0"}
facets:
  - {prefix: bb-, order: 20, name: wymiar B, question: "co w B"}
contributes_when: {language: pl}
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
consultants:
  b-consult:
    tier: std
    description: Konsultant B — test.
    skills: [bb-tekst]
""")
    write(b / "traits" / "cecha-b.md", "**Cecha B**\n- tak")
    write(b / "roles" / "rola-b.yaml", "name: rola-b\ntitle: Rola B\ntier: std\ntriggers: b\nidentity: b\n"
                                        "tools: [Read, Skill]\nskills: [bb-tekst]\n")
    write(b / "personas" / "bolek.yaml", "name: bolek\ntitle: Bolek\ndescription: Persona B.\nidentity: b\n"
                                           "roles: [rola-b]\ntraits: [grounded]\npriorities: [jakość]\n")
    return p


def load(p: Path, name: str):
    spec = importlib.util.spec_from_file_location(f"tp_{name}_{id(p)}", p / "factory" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(p / "factory"))
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
        check([f["prefix"] for f in cfg["facets"]][:2] == ["aa-", "bb-"], f"P-1: wymiary nakładek po order: {cfg['facets'][:2]}")
        check("b-agent" in cfg["shared_agents"] and "| sygnał B |" in cfg["routing"],
              "P-2: agent i wiersz routingu nakładki przy spełnionym contributes_when (język pl domyślnie)")
        roles, personas, traits, skills, errors = b.load_team(cfg)
        ala = personas["ala"]
        check(ala["roles"] == ["rola-a"] and "rola rola-c" in ala["_dropped"] and "cecha cecha-c" in ala["_dropped"]
              and ala["extra_agents"] == [], f"P-3: odwołania do nakładki opcjonalnej (pack-c) pominięte: {ala}")
        check("cc-nieznany" not in roles["rola-a"]["skills"], "P-4: nieznany skill roli nakładki z brakującą opcjonalną pominięty")
        check("cecha-b" in ala["traits"] and "bb-tekst" in ala["core_skills"], f"P-5: wkład pack-b do person innych nakładek: {ala}")
        check("aa-model" in roles["rola-b"]["skills"], f"P-6: wkład pack-a do roli z pack-b: {roles['rola-b']['skills']}")
        check("aa-extra" in b.persona_skills(ala, roles, cfg) and "aa-extra" not in b.persona_skills(personas["bolek"], roles, cfg),
              "P-7: always_skills nakładki tylko dla jej person")
        rendered = b.render_all()
        ala_md, bolek_md = rendered["ala/ala.md"], rendered["bolek/bolek.md"]
        check("b-consult" in ala_md and "a-consult" not in ala_md and "a-consult" in bolek_md and "b-consult" not in bolek_md,
              "P-8: persona widzi konsultantów innych nakładek, nie swojej")
        check("consult/a-consult.md" in rendered and "tools: Read, Grep, Glob, Skill" in rendered["consult/a-consult.md"],
              "P-9: konsultant tylko do odczytu")
        check("specialist" in ala_md.split("\n")[3] and "specialist" not in bolek_md.split("\n")[3],
              "P-10: specialist (@dispatcher) tylko u persony z dispatcher: true")
        check("## Język" in ala_md and "po polsku" in ala_md and "commitów" in ala_md, "P-11: sekcja języka w personie")
        e, _ = b.validate()
        check(not [x for x in e if "nieaktualn" not in x],   # pliki agentów nie są zbudowane — tu bez znaczenia
              f"P-12: złożona konfiguracja bez błędów: {e}")

        # język en: pack-b uśpiona — bez wkładu, agenta i wiersza routingu
        pm.save_settings(p, language="en", commit_language="pl")
        cfg = b.load_config()
        roles, personas, traits, skills, errors = b.load_team(cfg)
        check("b-agent" not in cfg["shared_agents"] and "sygnał B" not in cfg["routing"]
              and "cecha-b" not in personas["ala"]["traits"] and "b-consult" not in cfg["consultants"],
              "P-13: contributes_when niespełniony → nakładka uśpiona")
        md = b.render_all()["ala/ala.md"]
        check("po angielsku" in md and "commitów, tytuły i opisy pull requestów oraz wpisy CHANGELOG piszesz po polsku" in md,
              "P-14: język pracy en i commitów pl w prompcie")

        # zgodność wersji rdzenia i wymagane nakładki
        y = p / "factory" / "packs" / "pack-a" / "pack.yaml"
        y.write_text(y.read_text().replace('requires: {core: ">=3.0.0 <4.0.0"}', 'requires: {core: ">=9.0.0", packs: [pack-z]}'))
        e, _ = b.check_packs(b.load_config())
        check(any("wymaga rdzenia" in x for x in e) and any("tf add pack-z" in x for x in e),
              f"P-15: niezgodny rdzeń i brakująca wymagana nakładka → błędy: {e}")

        # migracje: własna persona projektu ze starą nazwą skilla
        write(p / "factory" / "personas" / "moja.yaml", "name: moja\nskills: [core-tech-docs, fe-ux-design]\n")
        mig = load(p, "migrations")
        todo = mig.apply(p, dry=True)
        check(todo and "docs-tech-writing" in todo[0] and "core-tech-docs" in (p / "factory/personas/moja.yaml").read_text(),
              f"P-16: migracja na sucho pokazuje zmianę, nic nie zapisuje: {todo}")
        mig.apply(p, dry=False)
        text = (p / "factory/personas/moja.yaml").read_text()
        check("docs-tech-writing" in text and "ux-feature-design" in text, f"P-17: migracja poprawia plik projektu: {text}")

        # sekcja języka w CLAUDE.local.md
        md_p = p / "CLAUDE.local.md"
        md_p.write_text("x\n<!-- team-factory:begin -->\n## Zespół\n### Język\n- stare\n<!-- team-factory:end -->\n")
        changed = pm.write_language_lines(md_p, pm.load_yaml(p / "factory" / "config.yaml"),
                                          {"language": "pl", "commit_language": "en"})
        txt = md_p.read_text()
        check(changed and "- stare" not in txt and "po polsku" in txt and txt.startswith("x\n"),
              f"P-18: podmiana sekcji języka w bloku fabryki: {txt}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów nakładek")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
