#!/usr/bin/env python3
"""Tests of .tf/factory/skill_profile.py: skill description visibility (skillOverrides) fitted to the project."""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "skill_profile.py").is_file())
SCRIPT = ROOT / ".tf" / "factory" / "skill_profile.py"


def load():
    spec = importlib.util.spec_from_file_location("ctf_skill_profile", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def skill(root: Path, name: str, manual: bool = False) -> None:
    d = root / ".claude" / "skills" / name
    d.mkdir(parents=True)
    extra = "disable-model-invocation: true\n" if manual else ""
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Use for {name}.\n{extra}---\n# {name}\n")


NAME_ONLY = ("dom-", "sec-", "ai-", "ux-")   # 'name only' prefixes declared in the test by a pack


def with_pack(p: Path) -> None:
    """The factory in a test project: packs.py, config.yaml and a pack with 'name only' prefixes."""
    import shutil
    (p / ".tf" / "factory").mkdir(parents=True, exist_ok=True)
    for f in ("packs.py", "config.yaml"):
        shutil.copy(ROOT / ".tf" / "factory" / f, p / ".tf" / "factory" / f)
    if (ROOT / ".tf" / "factory" / "_vendor").is_dir():
        shutil.copytree(ROOT / ".tf" / "factory" / "_vendor", p / ".tf" / "factory" / "_vendor", dirs_exist_ok=True)
    pk = p / ".tf" / "factory" / "packs" / "pack-t"
    pk.mkdir(parents=True, exist_ok=True)
    (pk / "pack.yaml").write_text("id: pack-t\nskill_visibility:\n  name_only_prefixes: [" + ", ".join(NAME_ONLY) + "]\n")


def project(base: Path, name: str, stack: list[str] | None) -> Path:
    p = base / name
    with_pack(p)
    for s in ("eng-testing", "lang-python", "fw-angular", "dom-demo-orders", "core-factory-update", "moj-skill"):
        skill(p, s, manual=s == "core-factory-update")
    files = {f".claude/skills/{s}/SKILL.md": "x" for s in
             ("eng-testing", "lang-python", "fw-angular", "dom-demo-orders", "core-factory-update")}
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
    check(sp.desired("dom-demo-orders", set()) == "on", "SP-0: the core without packs hides no dimension")
    check(d("fw-angular", {"fw-angular"}) == "on" and d("lang-java", set()) == "name-only"
          and d("dom-demo-orders", set()) == "name-only" and d("eng-testing", set()) == "on",
          "SP-1: technologies per the detected stack, dom-* name only (a prefix from a pack), the rest with a description")
    check(d("lang-java", None) == "on", "SP-1b: unknown stack (detection did not work) -> technologies with a description")

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        skill(p, "eng-rzadki")
        md = p / ".claude" / "skills" / "eng-rzadki" / "SKILL.md"
        md.write_text(md.read_text().replace("description:", "metadata:\n  visibility: name\ndescription:"))
        check(sp.desired("eng-rzadki", set(), sp.marked_name_only(md)) == "name-only",
              "SP-1c: the skill's author marks it 'metadata.visibility: name' -> name only")

    check(d("ux-research-methods", set()) == "name-only" and d("sec-cryptography-pki", set()) == "name-only"
          and d("ai-evals", set()) == "name-only", "SP-1d: specialist dimensions (ux-, sec-, ai-) are name only by default")
    check(d("ux-research-methods", set(), describe=("ux-",)) == "on" and d("ai-evals", set(), describe=("ux-",)) == "name-only",
          "SP-1e: --describe ux- turns on the description of the whole dimension in the project")

    want = {"eng-testing": "on", "lang-java": "name-only", "dom-x": "name-only"}
    s, m, kept = sp.plan({"model": "sonnet"}, want, {})
    check(s == {"model": "sonnet", "skillOverrides": {"lang-java": "name-only", "dom-x": "name-only"}}
          and m == {"lang-java": "name-only", "dom-x": "name-only"} and kept == [],
          f"SP-2: the first run writes only deviations from 'on', the rest of the settings stay: {s} {m}")

    s, m, kept = sp.plan({"skillOverrides": {"eng-testing": "off"}}, want, {})
    check(s["skillOverrides"].get("eng-testing") == "off" and kept == ["eng-testing"],
          f"SP-3: a user's manual setting stays: {s} {kept}")

    s, m, kept = sp.plan({"skillOverrides": {"dom-x": "name-only"}}, want, {"lang-java": "name-only", "dom-x": "name-only"})
    check("lang-java" not in s["skillOverrides"] and "lang-java" in kept and m.get("lang-java") == "name-only",
          f"SP-4: the user removed a factory entry -> it does not come back on the next run: {s} {m} {kept}")

    s, m, kept = sp.plan({"skillOverrides": {"lang-java": "name-only"}}, {"lang-java": "on"}, {"lang-java": "name-only"})
    check("lang-java" not in s.get("skillOverrides", {}) and m == {} and kept == [],
          f"SP-5: the technology appeared in the project -> the factory entry removed (the description returns): {s} {m}")

    s, m, kept = sp.plan({"skillOverrides": {"stary": "name-only", "cudzy": "off"}}, {}, {"stary": "name-only"})
    check(s["skillOverrides"] == {"cudzy": "off"} and m == {},
          f"SP-6: a skill removed from the factory -> its entry disappears, others' stay: {s}")

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base, "nieznany-stack", None)
        sp.apply(p)
        st = json.loads((p / ".claude" / "settings.local.json").read_text())
        ov = st.get("skillOverrides", {})
        check(ov == {"dom-demo-orders": "name-only"},
              f"SP-7: without detect_stack technologies keep their description, manual and own skills skipped: {ov}")
        man = json.loads((p / ".claude" / "factory-manifest.json").read_text())
        check(man.get("skill_overrides") == {"dom-demo-orders": "name-only"} and man.get("version") == "1.0.0",
              f"SP-8: the manifest remembers the factory entries and keeps the rest: {man}")

        p = project(base, "python", ["lang-python"])
        (p / ".claude" / "settings.local.json").write_text(json.dumps({"permissions": {"allow": ["Bash(ls)"]}}))
        r = subprocess.run([sys.executable, str(SCRIPT), str(p), "--dry-run"], capture_output=True, text=True)
        st = json.loads((p / ".claude" / "settings.local.json").read_text())
        check(r.returncode == 0 and "skillOverrides" not in st and "fw-angular" in r.stdout,
              f"SP-9: --dry-run shows the plan and writes nothing: {r.stdout}{r.stderr}")
        r = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)
        st = json.loads((p / ".claude" / "settings.local.json").read_text())
        check(r.returncode == 0 and st.get("skillOverrides") == {"fw-angular": "name-only", "dom-demo-orders": "name-only"}
              and st.get("permissions") == {"allow": ["Bash(ls)"]},
              f"SP-10: detected Python -> lang-python with a description, Angular name only, permissions untouched: {st}")

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
              and man.get("skill_describe") == ["ux-"], f"SP-13: --describe saved in the manifest, ux- with a description: {st} {man}")
        sp.apply(p)
        st = json.loads((p / ".claude" / "settings.local.json").read_text())
        check("ux-research-methods" not in st.get("skillOverrides", {}),
              f"SP-14: the next run (e.g. an update) remembers --describe from the manifest: {st}")

    # Install and update (install.py) set visibility themselves and respect manual changes. The installer is
    # in the factory repository (core/factory/install.py) — we take the source from the manifest of the project the test runs in.
    try:
        src = Path(json.loads((ROOT / ".claude" / "factory-manifest.json").read_text())["source"])
    except (OSError, ValueError, KeyError):
        src = None
    installer = src / "core" / "factory" / "install.py" if src else None
    if not (installer and installer.is_file()):
        print("ℹ SP-11/12 skipped: no factory repository (source in the manifest)")
    else:
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "projekt"
            p.mkdir()
            (p / "pyproject.toml").write_text('[project]\nname = "x"\nrequires-python = ">=3.12"\n')
            inst = [sys.executable, str(installer), str(p), "--yes", "--packs", "pack-it"]
            r = subprocess.run(inst, capture_output=True, text=True)
            st = json.loads((p / ".claude" / "settings.local.json").read_text()) if r.returncode == 0 else {}
            ov = st.get("skillOverrides", {})
            man = json.loads((p / ".claude" / "factory-manifest.json").read_text()) if r.returncode == 0 else {}
            check(r.returncode == 0 and ov.get("fw-angular") == "name-only" and "lang-python" not in ov
                  and ov.get("sec-cryptography-pki") == "name-only"
                  and man.get("skill_overrides") == ov and "skill visibility" in r.stdout,
                  f"SP-11: installation fits visibility to the project (Python): {ov} {r.stdout[-400:]}{r.stderr[-400:]}")
            st.setdefault("skillOverrides", {})["fw-angular"] = "on"
            (p / ".claude" / "settings.local.json").write_text(json.dumps(st))
            subprocess.run([sys.executable, str(SCRIPT), str(p), "--describe", "ux-"], capture_output=True, text=True)
            st = json.loads((p / ".claude" / "settings.local.json").read_text())
            r = subprocess.run(inst + ["--update"], capture_output=True, text=True)
            st = json.loads((p / ".claude" / "settings.local.json").read_text())
            man = json.loads((p / ".claude" / "factory-manifest.json").read_text())
            check(r.returncode == 0 and st.get("skillOverrides", {}).get("fw-angular") == "on"
                  and man.get("skill_overrides", {}).get("fw-angular") == "name-only" and man.get("skill_describe") == ["ux-"],
                  f"SP-12: an update keeps the manual change and the factory's memory: {st.get('skillOverrides')} {r.stderr[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} skill_profile tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
