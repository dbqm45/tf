#!/usr/bin/env python3
"""Testy factory/skill_profile.py: widoczność opisów skilli (skillOverrides) dopasowana do projektu."""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "skill_profile.py").is_file())
SCRIPT = ROOT / "factory" / "skill_profile.py"


def load():
    spec = importlib.util.spec_from_file_location("ctf_skill_profile", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def skill(root: Path, name: str, manual: bool = False) -> None:
    d = root / ".claude" / "skills" / name
    d.mkdir(parents=True)
    extra = "disable-model-invocation: true\n" if manual else ""
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Użyj przy {name}.\n{extra}---\n# {name}\n")


NAME_ONLY = ("dom-", "sec-", "ai-", "ux-")   # prefiksy „sama nazwa” deklarowane w teście przez nakładkę


def with_pack(p: Path) -> None:
    """Fabryka w projekcie testowym: packs.py, config.yaml i nakładka z prefiksami „sama nazwa”."""
    import shutil
    (p / "factory").mkdir(parents=True, exist_ok=True)
    for f in ("packs.py", "config.yaml"):
        shutil.copy(ROOT / "factory" / f, p / "factory" / f)
    if (ROOT / "factory" / "_vendor").is_dir():
        shutil.copytree(ROOT / "factory" / "_vendor", p / "factory" / "_vendor", dirs_exist_ok=True)
    pk = p / "factory" / "packs" / "pack-t"
    pk.mkdir(parents=True, exist_ok=True)
    (pk / "pack.yaml").write_text("id: pack-t\nskill_visibility:\n  name_only_prefixes: [" + ", ".join(NAME_ONLY) + "]\n")


def project(base: Path, name: str, stack: list[str] | None) -> Path:
    p = base / name
    with_pack(p)
    for s in ("eng-testing", "lang-python", "fw-angular", "dom-ev-charging", "core-factory-update", "moj-skill"):
        skill(p, s, manual=s == "core-factory-update")
    files = {f".claude/skills/{s}/SKILL.md": "x" for s in
             ("eng-testing", "lang-python", "fw-angular", "dom-ev-charging", "core-factory-update")}
    (p / ".claude" / "factory-manifest.json").write_text(json.dumps({"version": "1.0.0", "files": files}))
    if stack is not None:
        (p / ".claude" / "hooks").mkdir()
        (p / ".claude" / "hooks" / "detect_stack.py").write_text(
            f"def analyze(root, with_latest=False):\n    return {{'suggested_stack': {stack!r}}}\n")
    return p


def main() -> int:
    sp = load()
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    d = lambda name, stack, *a, **k: sp.desired(name, stack, *a, **{"name_only": NAME_ONLY, **k})
    check(sp.desired("dom-ev-charging", set()) == "on", "SP-0: rdzeń bez nakładek nie ukrywa żadnego wymiaru")
    check(d("fw-angular", {"fw-angular"}) == "on" and d("lang-java", set()) == "name-only"
          and d("dom-ev-charging", set()) == "name-only" and d("eng-testing", set()) == "on",
          "SP-1: technologie wg wykrytego stacku, dom-* tylko nazwa (prefiks z nakładki), reszta z opisem")
    check(d("lang-java", None) == "on", "SP-1b: stack nieznany (wykrywanie nie zadziałało) → technologie z opisem")

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        skill(p, "eng-rzadki")
        md = p / ".claude" / "skills" / "eng-rzadki" / "SKILL.md"
        md.write_text(md.read_text().replace("description:", "metadata:\n  widocznosc: nazwa\ndescription:"))
        check(sp.desired("eng-rzadki", set(), sp.marked_name_only(md)) == "name-only",
              "SP-1c: autor skilla oznacza go „metadata.widocznosc: nazwa” → sama nazwa")

    check(d("ux-research-methods", set()) == "name-only" and d("sec-cryptography-pki", set()) == "name-only"
          and d("ai-evals", set()) == "name-only", "SP-1d: wymiary specjalistyczne (ux-, sec-, ai-) domyślnie tylko nazwa")
    check(d("ux-research-methods", set(), describe=("ux-",)) == "on" and d("ai-evals", set(), describe=("ux-",)) == "name-only",
          "SP-1e: --describe ux- włącza opis całego wymiaru w projekcie")

    want = {"eng-testing": "on", "lang-java": "name-only", "dom-x": "name-only"}
    s, m, kept = sp.plan({"model": "sonnet"}, want, {})
    check(s == {"model": "sonnet", "skillOverrides": {"lang-java": "name-only", "dom-x": "name-only"}}
          and m == {"lang-java": "name-only", "dom-x": "name-only"} and kept == [],
          f"SP-2: pierwsze uruchomienie zapisuje tylko odstępstwa od „on”, reszta ustawień zostaje: {s} {m}")

    s, m, kept = sp.plan({"skillOverrides": {"eng-testing": "off"}}, want, {})
    check(s["skillOverrides"].get("eng-testing") == "off" and kept == ["eng-testing"],
          f"SP-3: ręczne ustawienie użytkownika zostaje: {s} {kept}")

    s, m, kept = sp.plan({"skillOverrides": {"dom-x": "name-only"}}, want, {"lang-java": "name-only", "dom-x": "name-only"})
    check("lang-java" not in s["skillOverrides"] and "lang-java" in kept and m.get("lang-java") == "name-only",
          f"SP-4: użytkownik usunął wpis fabryki → nie wraca przy kolejnym uruchomieniu: {s} {m} {kept}")

    s, m, kept = sp.plan({"skillOverrides": {"lang-java": "name-only"}}, {"lang-java": "on"}, {"lang-java": "name-only"})
    check("lang-java" not in s.get("skillOverrides", {}) and m == {} and kept == [],
          f"SP-5: technologia pojawiła się w projekcie → wpis fabryki usunięty (opis wraca): {s} {m}")

    s, m, kept = sp.plan({"skillOverrides": {"stary": "name-only", "cudzy": "off"}}, {}, {"stary": "name-only"})
    check(s["skillOverrides"] == {"cudzy": "off"} and m == {},
          f"SP-6: skill usunięty z fabryki → jego wpis znika, cudze zostają: {s}")

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base, "nieznany-stack", None)
        sp.apply(p)
        st = json.loads((p / ".claude" / "settings.local.json").read_text())
        ov = st.get("skillOverrides", {})
        check(ov == {"dom-ev-charging": "name-only"},
              f"SP-7: bez detect_stack technologie zostają z opisem, ręczne skille i własne pominięte: {ov}")
        man = json.loads((p / ".claude" / "factory-manifest.json").read_text())
        check(man.get("skill_overrides") == {"dom-ev-charging": "name-only"} and man.get("version") == "1.0.0",
              f"SP-8: manifest pamięta wpisy fabryki i zachowuje resztę: {man}")

        p = project(base, "python", ["lang-python"])
        (p / ".claude" / "settings.local.json").write_text(json.dumps({"permissions": {"allow": ["Bash(ls)"]}}))
        r = subprocess.run([sys.executable, str(SCRIPT), str(p), "--dry-run"], capture_output=True, text=True)
        st = json.loads((p / ".claude" / "settings.local.json").read_text())
        check(r.returncode == 0 and "skillOverrides" not in st and "fw-angular" in r.stdout,
              f"SP-9: --dry-run pokazuje plan i nic nie zapisuje: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)
        st = json.loads((p / ".claude" / "settings.local.json").read_text())
        check(r.returncode == 0 and st.get("skillOverrides") == {"fw-angular": "name-only", "dom-ev-charging": "name-only"}
              and st.get("permissions") == {"allow": ["Bash(ls)"]},
              f"SP-10: wykryty Python → lang-python z opisem, Angular tylko nazwa, uprawnienia nietknięte: {st}")

    with tempfile.TemporaryDirectory() as t:
        p = project(Path(t), "ux", None)
        skill(p, "ux-research-methods")
        man_p = p / ".claude" / "factory-manifest.json"
        man = json.loads(man_p.read_text())
        man["files"][".claude/skills/ux-research-methods/SKILL.md"] = "x"
        man_p.write_text(json.dumps(man))
        r = subprocess.run([sys.executable, str(SCRIPT), str(p), "--describe", "ux-"], capture_output=True, text=True)
        st = json.loads((p / ".claude" / "settings.local.json").read_text())
        man = json.loads(man_p.read_text())
        check(r.returncode == 0 and "ux-research-methods" not in st.get("skillOverrides", {})
              and man.get("skill_describe") == ["ux-"], f"SP-13: --describe zapisany w manifeście, ux- z opisem: {st} {man}")
        sp.apply(p)
        st = json.loads((p / ".claude" / "settings.local.json").read_text())
        check("ux-research-methods" not in st.get("skillOverrides", {}),
              f"SP-14: kolejne uruchomienie (np. aktualizacja) pamięta --describe z manifestu: {st}")

    # Instalacja i aktualizacja (install.py) ustawiają widoczność same i szanują ręczne zmiany. Instalator jest
    # w repozytorium fabryki (core/factory/install.py) — źródło bierzemy z manifestu projektu, w którym działa test.
    try:
        src = Path(json.loads((ROOT / ".claude" / "factory-manifest.json").read_text())["source"])
    except (OSError, ValueError, KeyError):
        src = None
    installer = src / "core" / "factory" / "install.py" if src else None
    if not (installer and installer.is_file()):
        print("ℹ SP-11/12 pominięte: brak repozytorium fabryki (source w manifeście)")
    else:
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "projekt"
            p.mkdir()
            (p / "pyproject.toml").write_text('[project]\nname = "x"\nrequires-python = ">=3.12"\n')
            inst = [sys.executable, str(installer), str(p), "--yes", "--packs", "pack-it,pack-ev"]
            r = subprocess.run(inst, capture_output=True, text=True)
            st = json.loads((p / ".claude" / "settings.local.json").read_text()) if r.returncode == 0 else {}
            ov = st.get("skillOverrides", {})
            man = json.loads((p / ".claude" / "factory-manifest.json").read_text()) if r.returncode == 0 else {}
            check(r.returncode == 0 and ov.get("fw-angular") == "name-only" and "lang-python" not in ov
                  and ov.get("sec-cryptography-pki") == "name-only" and "dom-ev-ocpi" not in ov
                  and man.get("skill_overrides") == ov and "skill visibility" in r.stdout,
                  f"SP-11: instalacja dopasowuje widoczność do projektu (Python): {ov} {r.stdout[-400:]}{r.stderr[-400:]}")
            st.setdefault("skillOverrides", {})["fw-angular"] = "on"
            (p / ".claude" / "settings.local.json").write_text(json.dumps(st))
            subprocess.run([sys.executable, str(SCRIPT), str(p), "--describe", "ux-"], capture_output=True, text=True)
            st = json.loads((p / ".claude" / "settings.local.json").read_text())
            r = subprocess.run(inst + ["--update"], capture_output=True, text=True)
            st = json.loads((p / ".claude" / "settings.local.json").read_text())
            man = json.loads((p / ".claude" / "factory-manifest.json").read_text())
            check(r.returncode == 0 and st.get("skillOverrides", {}).get("fw-angular") == "on"
                  and man.get("skill_overrides", {}).get("fw-angular") == "name-only" and man.get("skill_describe") == ["ux-"],
                  f"SP-12: aktualizacja zachowuje ręczną zmianę i pamięć fabryki: {st.get('skillOverrides')} {r.stderr[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów skill_profile")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
