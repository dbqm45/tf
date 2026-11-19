#!/usr/bin/env python3
"""
Development workspace for the factory: an installed project assembled from core/, packs/ and modes/, where the build check
and the factory tests run (tests and build expect the installed layout, not the source tree).

  python3 tools/workspace.py assemble [--packs all|none|a,b] [--out DIR]
                                     [--pack-dir DIR|git URL]   # also packs from outside packs/ (install.py --pack-dir)
  python3 tools/workspace.py check    [same options]   # assemble + build check + tests + scenario validation + gate status
  python3 tools/workspace.py matrix                    # check: core only, each pack and mode alone, all
  python3 tools/workspace.py sync-gate [--out DIR]     # copy gate results back to core/, packs/ and modes/
  python3 tools/workspace.py refs [--verbose]          # cross-layer references: core must not name pack skills,
                                                       # a pack only names skills of its required/optional packs
  python3 tools/workspace.py new-pack <name> [--kind pack|mode] [--prefix p-] [--title T] [--description D]
                                     [--skill p-name] [--role role-name] [--no-check]
                                                       # skeleton of packs/pack-<name>/ or modes/mode-<name>/, CI matrix
                                                       # entry, then check + refs and a to-do list (guide: docs/new-pack.md)
  python3 tools/workspace.py flow-evals [--validate | --all | --ids <id>,<glob>] [--budget-usd N] [--baseline previous]
                                                       # flow evals (N5, DZ13): gate for model/skill/persona/phase prompt
                                                       # changes; the report compares score and cost with the previous run

Default workspace: .work/<packs> (git-ignored; `+ext` appended with --pack-dir). The workspace is recreated on every `assemble`/`check`.
Gate results (`python3 .tf/factory/skill_gate.py <skill>` run inside the workspace) land in `.claude/skill-gate.json`;
`sync-gate` moves them into `core/tests/skill_gate/core.json` or `{packs,modes}/<id>/tests/skill_gate/<id>.json`.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "core" / "factory" / "install.py"
ITEM_ROOTS = (ROOT / "packs", ROOT / "modes")   # overlays and modes — the same directory layout


def item_dirs() -> list[Path]:
    """Overlay and mode directories (with pack.yaml), by name."""
    return sorted((p.parent for r in ITEM_ROOTS for p in r.glob("*/pack.yaml")), key=lambda d: d.name)


def opts_of(argv: list[str]) -> dict:
    out = {"packs": "all", "out": None, "keep": False, "pack-dir": None}
    it = iter(argv)
    for a in it:
        if a in ("--packs", "--out"):
            out[a[2:]] = next(it, "")
        elif a == "--pack-dir":     # overlays from outside packs/ (e.g. ../ev-intelligence/factory-pack); may be repeated
            out["pack-dir"] = ",".join(x for x in (out["pack-dir"], next(it, "")) if x)
        elif a == "--keep":
            out["keep"] = True
    return out


def workspace_dir(o: dict) -> Path:
    if o["out"]:
        return Path(o["out"]).resolve()
    name = o["packs"].replace(",", "+") or "none"
    return ROOT / ".work" / (name + "+ext" if o.get("pack-dir") else name)


def install_cmd(ws: Path, o: dict) -> list[str]:
    cmd = [sys.executable, str(INSTALL), str(ws), "--yes", "--packs", o["packs"] or "none"]
    if o.get("pack-dir"):
        cmd += ["--pack-dir", o["pack-dir"]]
    return cmd


def external_dirs(o: dict) -> list[Path]:
    """Local directories of external overlays from --pack-dir (for sync-gate); git addresses have nowhere to be recorded."""
    out = []
    for src in (o.get("pack-dir") or "").split(","):
        base = Path(src).expanduser() if src and "://" not in src else None
        if base and base.is_dir():
            out += [base] if (base / "pack.yaml").is_file() else sorted(p.parent for p in base.glob("*/pack.yaml"))
    return out


def assemble(o: dict) -> Path:
    ws = workspace_dir(o)
    if ws.exists() and not o["keep"]:
        shutil.rmtree(ws)
    ws.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=ws, check=False)
    r = subprocess.run(install_cmd(ws, o), capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:] + r.stderr[-2000:])
        sys.exit(f"✗ install failed in {ws}")
    return ws


def factory_only_tests() -> list[Path]:
    """Core tests that the installer does not copy into the project (install.py: FACTORY_ONLY) — run from the source."""
    spec = importlib.util.spec_from_file_location("tf_install_ws", INSTALL)
    inst = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inst)
    return sorted(ROOT / "core" / rel for rel in inst.FACTORY_ONLY
                  if Path(rel).name.startswith("test_") and rel.endswith(".py"))


def run(ws: Path, cmd: list[str], env: dict | None = None) -> bool:
    r = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, env={**os.environ, **(env or {})})
    ok = r.returncode == 0
    label = " ".join(Path(c).name if "/" in c else c for c in cmd[1:3])
    print(f"  {'✓' if ok else '✗'} {label}")
    if not ok:
        print("    " + "\n    ".join((r.stdout + r.stderr).strip().splitlines()[-25:]))
    return ok


def check(o: dict) -> bool:
    ws = assemble(o)
    print(f"Workspace {ws.relative_to(ROOT) if ws.is_relative_to(ROOT) else ws} — packs: {o['packs'] or 'none'}")
    ok = run(ws, [sys.executable, ".tf/factory/build.py", "check"])
    tests = sorted((ws / ".claude" / "tests").glob("test_*.py"))
    for t in tests:
        ok &= run(ws, [sys.executable, str(t.relative_to(ws))])
    for t in factory_only_tests():   # only in the factory workspace (they import modules from the factory source)
        ok &= run(ROOT, [sys.executable, str(t.relative_to(ROOT))])
    if (ws / ".claude/tests/run_skill_evals.py").exists():
        strict = {"TF_EVALS_STRICT": "1"} if o["packs"] == "all" else {}   # scenario neighbors from all overlays
        ok &= run(ws, [sys.executable, ".claude/tests/run_skill_evals.py", "--validate"], env=strict)
    ok &= run(ws, [sys.executable, ".tf/factory/skill_gate.py", "--status", "--strict"])
    return ok


def sync_gate(o: dict) -> int:
    ws = workspace_dir(o)
    reg_p = ws / ".claude" / "skill-gate.json"
    if not reg_p.exists():
        print("Nothing to sync (no .claude/skill-gate.json in the workspace).")
        return 0
    reg = json.loads(reg_p.read_text(encoding="utf-8"))
    owners = {d.name: ROOT / "core" for d in (ROOT / "core" / "skills").iterdir() if d.is_dir()}
    for p in (s for d in [*item_dirs(), *external_dirs(o)] for s in sorted(d.glob("skills/*"))):
        owners[p.name] = p.parent.parent
    moved = 0
    for skill, rec in reg.items():
        base = owners.get(skill)
        if base is None:
            print(f"  ? {skill}: not a factory skill — skipped")
            continue
        gid = "core" if base == ROOT / "core" else pack_id(base)
        f = base / "tests" / "skill_gate" / f"{gid}.json"
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        data[skill] = rec
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        moved += 1
    print(f"✓ Synced {moved} gate records into core/, packs/ and modes/"
          + (" and the external packs" if external_dirs(o) else ""))
    return 0


def pack_id(base: Path) -> str:
    """The overlay id from pack.yaml (an external overlay's directory may be named differently, e.g. factory-pack/)."""
    import re
    m = re.search(r"^id:\s*(\S+)", (base / "pack.yaml").read_text(encoding="utf-8"), re.M) if (base / "pack.yaml").is_file() else None
    return m.group(1) if m else base.name


def skill_owners() -> dict[str, str]:
    owners = {d.name: "core" for d in (ROOT / "core" / "skills").iterdir() if d.is_dir()}
    for d in (s for i in item_dirs() for s in sorted(i.glob("skills/*"))):
        owners[d.name] = d.parent.parent.name
    return owners


def allowed_packs(layer: str) -> set[str]:
    if layer == "core":
        return set()
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_packs_ws", ROOT / "core" / "factory" / "packs.py")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    data = pm.load_yaml(next(d for d in item_dirs() if d.name == layer) / "pack.yaml")
    return set((data.get("requires") or {}).get("packs") or []) | set(data.get("optional_packs") or [])


def refs(verbose: bool) -> int:
    """References to skills of layers the referencing layer may not depend on. A line that names the owning pack
    (e.g. `(pack-it)`) is an explicit, conditional mention and is allowed."""
    import re
    owners = skill_owners()
    pattern = re.compile(r"(?<![\w/-])(" + "|".join(sorted(map(re.escape, owners), key=len, reverse=True)) + r")(?![\w-])")
    layers = {"core": ROOT / "core", **{p.name: p for p in item_dirs()}}
    total = 0
    for layer, base in layers.items():
        ok = allowed_packs(layer) | {layer, "core"}
        found: dict[str, list[str]] = {}
        for f in sorted(base.rglob("*")):
            if not f.is_file() or f.suffix not in (".md", ".yaml", ".yml", ".json", ".py", ".js") or "_vendor" in f.parts \
                    or f.name == "CHANGELOG.md" or "tests" in f.relative_to(base).parts:   # tests: test data; compatibility without overlays is checked by matrix
                continue
            for n, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                for m in pattern.finditer(line):
                    owner = owners[m.group(1)]
                    if owner in ok or owner in line:
                        continue
                    found.setdefault(owner, []).append(f"{f.relative_to(ROOT)}:{n}: {m.group(1)}")
        for owner, hits in found.items():
            total += len(hits)
            print(f"✗ {layer} → {owner}: {len(hits)} references")
            for h in hits[: (None if verbose else 5)]:
                print(f"    {h}")
    print("✓ no cross-layer references" if not total else f"✗ {total} cross-layer references")
    return 1 if total else 0


CI_FILE = ROOT / ".github" / "workflows" / "factory-checks.yml"


def taken_prefixes() -> dict[str, str]:
    """Dimension prefixes of the core, overlays and modes → owner (simple matching of `prefix: x-`)."""
    import re
    out = {}
    for f in [ROOT / "core" / "factory" / "config.yaml", *(r / "pack.yaml" for r in item_dirs())]:
        if f.is_file():
            for p in re.findall(r"prefix:\s*([a-z0-9]+-)", f.read_text(encoding="utf-8")):
                out.setdefault(p, f.parent.name)
    return out


SKILL_TPL = """---
name: {skill}
description: Use for TODO — the situation and key terms (a selection rule, up to 170 characters).
metadata:
  review: "{review}"
  catalog: "Use when TODO — full description with boundaries. Not for TODO (neighbor-skill)."
  keywords: "TODO: words people use to describe the problem, in Polish and in English"
---

# TODO: title

Goal: TODO — why the skill exists and what result it gives (core-skill-authoring: evaluation scenarios first, then content).

## Procedure
1. TODO

## Example
TODO: input → result, with specific names and numbers.

## Sources
- TODO: a source with a date.
"""

GUIDE_TPL = """# {title}

TODO: what this mode is, when to turn it on and how to turn it off (`tf add {pid}`, `tf remove {pid}`), what it adds
(agents, skills, scripts, permissions) and what it does not change in the core.
"""


def new_pack(argv: list[str]) -> int:
    import datetime
    import re
    args, opts = [], {"kind": "pack", "prefix": None, "title": None, "description": None, "skill": None, "role": None}
    it = iter(argv)
    for a in it:
        if a.startswith("--") and a[2:] in opts:
            opts[a[2:]] = next(it, "")
        elif a != "--no-check":
            args.append(a)
    name = args[0] if args else ""
    if not re.fullmatch(r"[a-z][a-z0-9-]*[a-z0-9]", name) or opts["kind"] not in ("pack", "mode"):
        print(f"✗ name: lowercase letters, digits and '-' (got {name!r}); --kind pack|mode", file=sys.stderr)
        return 2
    pid = f"{opts['kind']}-{name}"
    base = ROOT / ("packs" if opts["kind"] == "pack" else "modes") / pid
    prefix = opts["prefix"] or f"{name}-"
    skill = opts["skill"] or f"{prefix}podstawy"
    taken = taken_prefixes()
    problems = []
    if base.exists():
        problems.append(f"{base.relative_to(ROOT)} already exists — nothing overwritten")
    if not re.fullmatch(r"[a-z][a-z0-9]*-", prefix):
        problems.append(f"prefix must look like 'abc-' (got {prefix!r})")
    elif prefix in taken:
        problems.append(f"prefix {prefix} is already used by {taken[prefix]}")
    if not skill.startswith(prefix):
        problems.append(f"skill {skill} must start with the prefix {prefix}")
    if problems:
        print("✗ " + "\n✗ ".join(problems), file=sys.stderr)
        return 2
    def q(v: str) -> str:   # a quoted YAML value (a description with „: ” breaks the parser)
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'

    version = (ROOT / "core" / "factory" / "VERSION").read_text(encoding="utf-8").strip()
    major = int(version.split(".")[0])
    title = opts["title"] or name.replace("-", " ").title()
    desc = opts["description"] or f"TODO: one-sentence description of {pid} (English, shown by tf list)."
    files = {
        "pack.yaml": f"# TODO: comment — what this {'mode' if opts['kind'] == 'mode' else 'pack'} is and who it is for.\n"
                     f"id: {pid}\n" + ("kind: mode\n" if opts["kind"] == "mode" else "")
                     + f"version: 0.1.0\ntitle: {q(title)}\ndescription: {q(desc)}\ncontent_language: en\ndefault: false\n"
                     f"requires:\n  core: \">={version} <{major + 1}.0.0\"\n\nfacets:\n"
                     f"  - {{prefix: {prefix}, order: 500, name: {title.lower()}, question: \"TODO: which question the {prefix}* skills answer\"}}\n",
        f"skills/{skill}/SKILL.md": SKILL_TPL.format(skill=skill, review=(datetime.date.today() + datetime.timedelta(days=365)).isoformat()),
        f"tests/skill_evals/{skill}.json": json.dumps({"skill": skill, "scenarios": [
            {"id": "TODO-problem-1", "expect": "trigger", "prompt": "TODO: a real human question from a gap the model has without the skill",
             "checks": {"all": [["TODO: specific knowledge"], ["TODO: a second independent thing"]], "none": ["TODO: a typical mistake"]}},
            {"id": "TODO-problem-2", "expect": "trigger", "prompt": "TODO: the same area, different words",
             "checks": {"all": [["TODO"], ["TODO"]]}},
            {"id": "TODO-sasiad", "expect": "no-trigger", "neighbor": "TODO-sasiedni-skill",
             "prompt": "TODO: a borderline question that belongs to the neighboring skill"}]}, ensure_ascii=False, indent=2) + "\n",
    }
    if opts["role"]:
        files[f"roles/{opts['role']}.yaml"] = (f"name: {opts['role']}\ntitle: TODO\ntier: std\ntriggers: TODO\nidentity: |\n"
                                              f"  TODO: who the role is and how it works.\ntools: [Read, Grep, Glob, Edit, Write, Bash, Skill]\n"
                                              f"skills: [{skill}]\npreload: []\nverify: \"TODO — how to recognise a good result\"\n")
    if opts["kind"] == "mode":
        files["GUIDE.md"] = GUIDE_TPL.format(title=title, pid=pid)
    for rel, text in files.items():
        f = base / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    ci_note = "CI matrix: no `packs: [...]` line found — add the id by hand"
    if CI_FILE.is_file():
        ci = CI_FILE.read_text(encoding="utf-8")
        m = re.search(r"^(\s*packs: \[)(.*)\]$", ci, re.M)
        if m:
            items = [x.strip() for x in m.group(2).split(",") if x.strip()]
            if pid not in items:
                items.insert(items.index("all") if "all" in items else len(items), pid)
            CI_FILE.write_text(ci[:m.start()] + m.group(1) + ", ".join(items) + "]" + ci[m.end():], encoding="utf-8")
            ci_note = f"CI matrix: {pid} added"
    print(f"✓ {base.relative_to(ROOT)}: " + ", ".join(files) + f"\n✓ {ci_note}")
    ok = True
    if "--no-check" not in argv:
        ok = check({"packs": pid, "out": None, "keep": False})
        ok &= refs(False) == 0
    print(f"""To do (skill core-skill-authoring, guide docs/new-pack.md):
  1. pack.yaml: comment, description, facets.question, order; dependencies (requires.packs, optional_packs).
  2. Scenarios in tests/skill_evals/{skill}.json — real ones, before the content (the skeleton fails the gate on purpose).
  3. Content of skills/{skill}/SKILL.md; role/persona (roles/, personas/).
  4. In the workspace: python3 .tf/factory/skill_gate.py {skill}, then python3 tools/workspace.py sync-gate --out .work/{pid}.
  5. python3 tools/workspace.py check --packs {pid} and refs; a PR titled feat({pid}): …""")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "check"
    o = opts_of(argv[2:])
    if cmd == "assemble":
        print(assemble(o))
        return 0
    if cmd == "check":
        return 0 if check(o) else 1
    if cmd == "matrix":
        packs = [d.name for d in item_dirs()]
        results = {}
        for sel in ["none", *packs, "all"]:
            results[sel] = check({**o, "packs": sel, "out": None})
        print("\n".join(f"{'✓' if v else '✗'} {k}" for k, v in results.items()))
        return 0 if all(results.values()) else 1
    if cmd == "sync-gate":
        return sync_gate(o)
    if cmd == "refs":
        return refs("--verbose" in argv)
    if cmd == "new-pack":
        return new_pack(argv[2:])
    if cmd == "flow-evals":
        # Run evals (N5, DZ13): a gate for changes to the model/skill/persona/phase prompt.
        # The report compares the result and cost with the previous run; validation (--validate) does not touch the model.
        sys.path.insert(0, str(ROOT / "core" / "tests"))
        import flow_evals_runner
        return flow_evals_runner.main(argv[2:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
