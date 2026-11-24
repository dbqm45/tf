#!/usr/bin/env python3
"""
Development workspace for the factory: an installed project assembled from core/, packs/ and modes/, where the build check
and the factory tests run (tests and build expect the installed layout, not the source tree).

  python3 tools/workspace.py assemble [--packs all|none|a,b] [--out DIR]
                                     [--pack-dir DIR|git URL]   # also packs from outside packs/ (install.py --pack-dir)
  python3 tools/workspace.py check    [same options]   # assemble + build check + tests + scenario validation + gate status
                                     [--shard i/n]     # only the i-th of n duration-balanced slices of the tests (CI);
                                                       # the cheap checks run in slice 1 only
                                     [--changed-from SHA]  # only the tests related to `git diff SHA...HEAD` (PRs);
                                                       # falls back to the full suite when unsure, and says why
                                     [--no-tests]      # assemble + the cheap checks only (the release job)
                                     [--list]          # print the selected tests and stop
                                     [--timings] [--save-durations]   # per-test times; save them to tools/test-durations.json
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
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "core" / "factory" / "install.py"
ITEM_ROOTS = (ROOT / "packs", ROOT / "modes")   # overlays and modes — the same directory layout


def item_dirs() -> list[Path]:
    """Overlay and mode directories (with pack.yaml), by name."""
    return sorted((p.parent for r in ITEM_ROOTS for p in r.glob("*/pack.yaml")), key=lambda d: d.name)


def opts_of(argv: list[str]) -> dict:
    out = {"packs": "all", "out": None, "keep": False, "pack-dir": None, "shard": None, "changed-from": None,
           "no-tests": False, "list": False, "timings": False, "save-durations": False}
    it = iter(argv)
    for a in it:
        if a in ("--packs", "--out", "--shard", "--changed-from"):
            out[a[2:]] = next(it, "")
        elif a in ("--no-tests", "--list", "--timings", "--save-durations"):
            out[a[2:]] = True
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
    # the factory's own test suite reads skills and hooks from .claude/ (the old layout); the factory mode (the default
    # layout of installs since T5) is covered by tests/test_plugin_*.py
    cmd = [sys.executable, str(INSTALL), str(ws), "--yes", "--packs", o["packs"] or "none", "--layout", "default"]
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


def run(ws: Path, cmd: list[str], env: dict | None = None, times: dict | None = None) -> bool:
    t0 = time.monotonic()
    r = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, env={**os.environ, **(env or {})})
    took = time.monotonic() - t0
    ok = r.returncode == 0
    label = " ".join(Path(c).name if "/" in c else c for c in cmd[1:3])
    if times is not None:
        times[Path(cmd[1]).name] = took
    print(f"  {'✓' if ok else '✗'} {label}" + (f"  {took:.1f} s" if times is not None else ""))
    if not ok:
        print("    " + "\n    ".join((r.stdout + r.stderr).strip().splitlines()[-25:]))
    return ok


# --- Which tests a check runs: sharding (CI matrix) and selection by changed files (PRs) --------------------------

DURATIONS = ROOT / "tools" / "test-durations.json"   # seconds per test file (`check --timings --save-durations`)


def test_files(ws: Path) -> dict[str, tuple[Path, Path]]:
    """Test name → (cwd, script): the workspace tests and the factory-only ones (run from the factory source)."""
    out = {t.name: (ws, t) for t in sorted((ws / ".claude" / "tests").glob("test_*.py"))}
    for t in factory_only_tests():
        out[t.name] = (ROOT, t)
    return out


def parse_shard(spec: str | None) -> tuple[int, int]:
    if not spec:
        return 1, 1
    try:
        i, n = (int(x) for x in spec.split("/"))
    except ValueError:
        sys.exit(f"✗ --shard {spec!r}: expected i/n, e.g. 2/3")
    if not 1 <= i <= n:
        sys.exit(f"✗ --shard {spec!r}: i must be between 1 and n")
    return i, n


def load_durations() -> dict[str, float]:
    try:
        return {k: float(v) for k, v in json.loads(DURATIONS.read_text(encoding="utf-8")).items()}
    except (OSError, ValueError, AttributeError):
        return {}


def shards(names: list[str], n: int, durations: dict[str, float] | None = None) -> list[list[str]]:
    """Split the tests into n disjoint slices whose union is all of them. Balanced by the recorded durations (longest
    first onto the least loaded slice; an unknown test counts as the median); without durations, every n-th by name.
    Deterministic: the same names and durations always give the same slices."""
    names = sorted(set(names))
    if not durations:
        return [names[k::n] for k in range(n)]
    known = sorted(durations.values())
    default = known[len(known) // 2] if known else 1.0
    load, out = [0.0] * n, [[] for _ in range(n)]
    for name in sorted(names, key=lambda x: (-durations.get(x, default), x)):
        k = min(range(n), key=lambda j: (load[j], j))
        out[k].append(name)
        load[k] += durations.get(name, default)
    return [sorted(x) for x in out]


# Shared infrastructure: a change here can break any test, so the full suite runs.
FULL_PREFIXES = (".github/", "tools/workspace.py", "core/factory/build.py",
                 "core/factory/install.py", "core/factory/packs.py", "core/factory/config.yaml", "core/factory/update.py",
                 "core/factory/_vendor/", "core/settings.json")
# Not installed into the project; the `repo` and `addons` jobs always run their tests in full. A workspace test is
# selected only if it names the file.
OUTSIDE_PREFIXES = ("docs/", "tests/", "tools/", "scripts/", "addons/", "org/", ".githooks/")
OUTSIDE_FILES = ("README.md", ".gitignore", ".gitattributes")
# Tests of the skill gate, scenarios and hints: every skill change can move them.
SKILL_TESTS = ("test_dev_tools.py", "test_skill_evals.py", "test_skill_gate.py", "test_skill_audit.py")
FULL_SHARE = 0.4   # when the selection is this large anyway, the full suite runs


def stem_pattern(stem: str) -> re.Pattern:
    """How a test or a module refers to the module or script `stem`: x.py, /x.py, "x", import x, from x import."""
    s = re.escape(stem)
    return re.compile(rf"(?<![\w-]){s}\.py\b|[\"']{s}[\"']|\bimport\s+{s}\b|\bfrom\s+{s}\s+import\b")


def name_pattern(name: str) -> re.Pattern:
    return re.compile(rf"(?<![\w-]){re.escape(name)}(?![\w-])")


LOAD_LINE = re.compile(r"spec_from_file_location|^\s*\w+\s*=.*/\s*[\"']\w+\.py[\"']|^\s*(?:from|import)\s+\w", re.M)


def loads(text: str) -> set[str]:
    """Module stems a source imports or loads by path (import x, from x import, spec_from_file_location(… "x.py"),
    a `name = … / "x.py"` path)."""
    out: set[str] = set()
    for line in text.splitlines():
        if LOAD_LINE.search(line):
            out |= set(re.findall(r"(\w+)\.py\b", line)) | set(re.findall(r"^\s*(?:from|import)\s+(\w+)", line))
    return out


def loaded_by_infrastructure(modules: dict[str, str] | None = None) -> set[str]:
    """Modules that the shared infrastructure (install, build, update, packs) imports or loads, directly or through
    each other: a change to one of them reaches every installed project, so it gets the full suite too."""
    if modules is None:
        modules = {}
        for f in (*(ROOT / "core").rglob("*.py"), *(f for r in ITEM_ROOTS for f in r.rglob("*.py"))):
            if "tests" not in f.parts and "_vendor" not in f.parts:
                modules[f.stem] = modules.get(f.stem, "") + "\n" + f.read_text(encoding="utf-8", errors="ignore")
    todo = [Path(rel).stem for rel in FULL_PREFIXES if rel.endswith(".py")]
    out = set(todo)
    while todo:
        for m in loads(modules.get(todo.pop(), "")):
            if m in modules and m not in out:
                out.add(m)
                todo.append(m)
    return out


def select_tests(changed: list[str], tests: dict[str, str], packs: set[str], modules: dict[str, str] | None = None,
                 infra: set[str] | None = None) -> tuple[set[str] | None, list[str]]:
    """The tests (names from `tests`: name → source text) related to the changed files (repository paths), or None for
    the full suite; plus the reasons. `packs`: the overlays and modes installed in this workspace; `modules`: the
    installed modules and scripts (stem → source), to follow the modules that use a changed one; `infra`: the modules
    the shared infrastructure loads (loaded_by_infrastructure)."""
    modules = modules or {}
    infra = infra or set()
    picked: set[str] = set()
    why: list[str] = []

    def refs(pattern: re.Pattern) -> set[str]:
        return {n for n, text in tests.items() if pattern.search(text)}

    loaded = {m: loads(text) for m, text in modules.items()}

    def users(stem: str) -> set[str]:
        """The stem and, transitively, the modules that import or load it."""
        seen, todo = {stem}, [stem]
        while todo:
            cur = todo.pop()
            for m, deps in loaded.items():
                if cur in deps and m not in seen:
                    seen.add(m)
                    todo.append(m)
        return seen

    def module_tests(stem: str) -> set[str] | None:
        if stem in infra:
            return None
        return set().union(*(refs(stem_pattern(m)) for m in users(stem)))

    for path in changed:
        parts = path.split("/")
        name = parts[-1]
        if path.startswith(FULL_PREFIXES):
            return None, [f"{path}: shared infrastructure"]
        layer_pack = parts[1] if parts[0] in ("packs", "modes") and len(parts) > 2 else None
        if layer_pack and layer_pack not in packs:
            why.append(f"{path}: {layer_pack} is not in this pack set")
            continue
        if layer_pack and parts[2] == "pack.yaml":
            return None, [f"{path}: the overlay's manifest (install, dependencies)"]
        in_layer = parts[0] == "core" or layer_pack is not None
        outside = path.startswith(OUTSIDE_PREFIXES) or path in OUTSIDE_FILES
        if not in_layer and not outside:
            return None, [f"{path}: matches no selection rule"]
        rel = parts[1:] if parts[0] == "core" else parts[2:]   # the path inside the layer (skills/x/…, tests/…)
        hits: set[str] | None = set()
        if in_layer and rel[0] == "tests" and len(rel) == 2 and name.startswith("test_") and name.endswith(".py"):
            hits = {name} & set(tests)
            if not hits:   # a deleted or renamed test: nothing to run for it
                why.append(f"{path}: not a test of this workspace")
                continue
        elif in_layer and rel[:2] == ["tests", "skill_gate"]:   # gate records (also checked by skill_gate --status)
            hits = {t for t in tests if t in SKILL_TESTS}
        elif in_layer and (rel[0] == "skills" or rel[:2] == ["tests", "skill_evals"]):
            skill = rel[1] if rel[0] == "skills" else name.rsplit(".", 1)[0]
            hits = refs(name_pattern(skill)) | {t for t in tests if t in SKILL_TESTS or "hint" in t}
            if name.endswith(".py"):
                more = module_tests(name[:-3])
                if more is None:
                    return None, [f"{path}: loaded by the shared infrastructure (install, build, update)"]
                hits |= more
        elif name.endswith(".py"):
            hits = module_tests(name[:-3])
            if hits is None:
                return None, [f"{path}: loaded by the shared infrastructure (install, build, update)"]
        else:
            hits = refs(re.compile(rf"(?<![\w-]){re.escape(name)}\b"))
            if len(rel) > 1:
                hits |= refs(re.compile(re.escape("/".join(rel))))
        if not hits:
            if outside:
                why.append(f"{path}: not installed, no workspace test names it")
                continue
            return None, [f"{path}: no test refers to it, so the selection is unsure"]
        why.append(f"{path} → {', '.join(sorted(hits)[:6])}{' …' if len(hits) > 6 else ''}")
        picked |= hits
    if tests and len(picked) > FULL_SHARE * len(tests):
        return None, why + [f"{len(picked)} of {len(tests)} tests selected (over {FULL_SHARE:.0%}) — the full suite is simpler"]
    return picked, why


def changed_files(base: str) -> list[str] | None:
    """`git diff --name-only base...HEAD` in the factory repository, or None when git cannot tell."""
    r = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  (git diff {base}...HEAD failed: {r.stderr.strip()[:200]})")
        return None
    return [x for x in r.stdout.splitlines() if x.strip()]


def installed_packs(ws: Path) -> set[str]:
    try:
        return set(json.loads((ws / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get("packs") or {})
    except (OSError, ValueError):
        return set()


def installed_modules(ws: Path) -> dict[str, str]:
    """Stem → source of the installed modules and scripts (not the tests), plus the factory's scripts/."""
    out: dict[str, str] = {}
    files = [*(p for d in (".claude", ".tf") for p in (ws / d).rglob("*.py")), *(ROOT / "scripts").glob("*.py")]
    skip = {Path(rel).stem for rel in FULL_PREFIXES}   # their users are everything; loaded_by_infrastructure covers them
    for p in files:
        if "tests" in p.parts or "_vendor" in p.parts or p.stem in skip:
            continue
        out[p.stem] = out.get(p.stem, "") + "\n" + p.read_text(encoding="utf-8", errors="ignore")
    return out


def selection(ws: Path, o: dict, names: list[str]) -> list[str]:
    """The tests to run: all of them, or (with --changed-from) the related ones; the reason is printed."""
    base = o.get("changed-from")
    if not base:
        return names
    changed = changed_files(base)
    if changed is None:
        print("  Selection: full suite (the changed files are unknown)")
        return names
    files = test_files(ws)
    texts = {n: files[n][1].read_text(encoding="utf-8", errors="ignore") for n in names}
    picked, why = select_tests(changed, texts, installed_packs(ws), installed_modules(ws), loaded_by_infrastructure())
    print(f"  Changed since {base[:12] if re.fullmatch(r'[0-9a-f]{40}', base) else base}: {len(changed)} file(s)")
    for w in why[:40]:
        print(f"    {w}")
    if picked is None:
        print("  Selection: full suite")
        return names
    print(f"  Selection: {len(picked)} of {len(names)} tests")
    return sorted(picked)


def check(o: dict) -> bool:
    ws = assemble(o)
    print(f"Workspace {ws.relative_to(ROOT) if ws.is_relative_to(ROOT) else ws} — packs: {o['packs'] or 'none'}")
    i, n = parse_shard(o.get("shard"))
    files = test_files(ws)
    names = [] if o.get("no-tests") else selection(ws, o, sorted(files))
    if n > 1:
        names = shards(names, n, load_durations())[i - 1]
        print(f"  Shard {i}/{n}: {len(names)} tests" + ("" if i == 1 else " (the cheap checks run in shard 1)"))
    if o.get("list"):
        print("\n".join(f"    {x}" for x in names))
        return True
    cheap = i == 1
    times: dict[str, float] | None = {} if o.get("timings") or o.get("save-durations") else None
    ok = run(ws, [sys.executable, ".tf/factory/build.py", "check"]) if cheap else True
    for name in names:
        cwd, t = files[name]
        ok &= run(cwd, [sys.executable, str(t.relative_to(cwd))], times=times)
    if cheap and (ws / ".claude/tests/run_skill_evals.py").exists():
        strict = {"TF_EVALS_STRICT": "1"} if o["packs"] == "all" else {}   # scenario neighbors from all overlays
        ok &= run(ws, [sys.executable, ".claude/tests/run_skill_evals.py", "--validate"], env=strict)
    if cheap:
        ok &= run(ws, [sys.executable, ".tf/factory/skill_gate.py", "--status", "--strict"])
    print(f"  {len(names)} test file(s) run" + (f" (shard {i}/{n})" if n > 1 else ""))
    if times:
        print("  Slowest tests:")
        for name, took in sorted(times.items(), key=lambda x: -x[1])[:15]:
            print(f"    {took:7.1f} s  {name}")
        print(f"  Total {sum(times.values()):.0f} s in {len(times)} tests")
        if o.get("save-durations"):
            data = {**load_durations(), **{k: round(v, 1) for k, v in times.items()}}
            DURATIONS.write_text(json.dumps(dict(sorted(data.items())), indent=1) + "\n", encoding="utf-8")
            print(f"  ✓ {DURATIONS.relative_to(ROOT)} updated")
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
