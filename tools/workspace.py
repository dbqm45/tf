#!/usr/bin/env python3
"""
Development workspace for the factory: an installed project assembled from core/ and packs/, where the build check
and the factory tests run (tests and build expect the installed layout, not the source tree).

  python3 tools/workspace.py assemble [--packs all|none|a,b] [--out DIR] [--language pl] [--commit-language en]
  python3 tools/workspace.py check    [same options]   # assemble + build check + tests + scenario validation + gate status
  python3 tools/workspace.py matrix                    # check: core only, each pack alone, all packs
  python3 tools/workspace.py sync-gate [--out DIR]     # copy gate results from the workspace back to core/ and packs/
  python3 tools/workspace.py refs [--verbose]          # cross-layer references: core must not name pack skills,
                                                       # a pack only names skills of its required/optional packs

Default workspace: .work/<packs> (git-ignored). The workspace is recreated on every `assemble`/`check`.
Gate results (`python3 factory/skill_gate.py <skill>` run inside the workspace) land in `.claude/skill-gate.json`;
`sync-gate` moves them into `core/tests/skill_gate/core.json` or `packs/<id>/tests/skill_gate/<id>.json`.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "core" / "factory" / "install.py"


def opts_of(argv: list[str]) -> dict:
    out = {"packs": "all", "out": None, "language": None, "commit-language": None, "keep": False}
    it = iter(argv)
    for a in it:
        if a in ("--packs", "--out", "--language", "--commit-language"):
            out[a[2:]] = next(it, "")
        elif a == "--keep":
            out["keep"] = True
    return out


def workspace_dir(o: dict) -> Path:
    return Path(o["out"]).resolve() if o["out"] else ROOT / ".work" / (o["packs"].replace(",", "+") or "none")


def assemble(o: dict) -> Path:
    ws = workspace_dir(o)
    if ws.exists() and not o["keep"]:
        shutil.rmtree(ws)
    ws.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=ws, check=False)
    cmd = [sys.executable, str(INSTALL), str(ws), "--yes", "--packs", o["packs"] or "none"]
    for k in ("language", "commit-language"):
        if o[k]:
            cmd += [f"--{k}", o[k]]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:] + r.stderr[-2000:])
        sys.exit(f"✗ install failed in {ws}")
    return ws


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
    ok = run(ws, [sys.executable, "factory/build.py", "check"])
    tests = sorted((ws / ".claude" / "tests").glob("test_*.py"))
    for t in tests:
        ok &= run(ws, [sys.executable, str(t.relative_to(ws))])
    if (ws / ".claude/tests/run_skill_evals.py").exists():
        strict = {"TF_EVALS_STRICT": "1"} if o["packs"] == "all" else {}   # sąsiedzi scenariuszy ze wszystkich nakładek
        ok &= run(ws, [sys.executable, ".claude/tests/run_skill_evals.py", "--validate"], env=strict)
    ok &= run(ws, [sys.executable, "factory/skill_gate.py", "--status", "--strict"])
    return ok


def sync_gate(o: dict) -> int:
    ws = workspace_dir(o)
    reg_p = ws / ".claude" / "skill-gate.json"
    if not reg_p.exists():
        print("Nothing to sync (no .claude/skill-gate.json in the workspace).")
        return 0
    reg = json.loads(reg_p.read_text(encoding="utf-8"))
    owners = {d.name: ROOT / "core" for d in (ROOT / "core" / "skills").iterdir() if d.is_dir()}
    for p in sorted((ROOT / "packs").glob("*/skills/*")):
        owners[p.name] = p.parent.parent
    moved = 0
    for skill, rec in reg.items():
        base = owners.get(skill)
        if base is None:
            print(f"  ? {skill}: not a factory skill — skipped")
            continue
        f = base / "tests" / "skill_gate" / f"{'core' if base.name == 'core' else base.name}.json"
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        data[skill] = rec
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        moved += 1
    print(f"✓ Synced {moved} gate records into core/ and packs/")
    return 0


def skill_owners() -> dict[str, str]:
    owners = {d.name: "core" for d in (ROOT / "core" / "skills").iterdir() if d.is_dir()}
    for d in sorted((ROOT / "packs").glob("*/skills/*")):
        owners[d.name] = d.parent.parent.name
    return owners


def allowed_packs(layer: str) -> set[str]:
    if layer == "core":
        return set()
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_packs_ws", ROOT / "core" / "factory" / "packs.py")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    data = pm.load_yaml(ROOT / "packs" / layer / "pack.yaml")
    return set((data.get("requires") or {}).get("packs") or []) | set(data.get("optional_packs") or [])


def refs(verbose: bool) -> int:
    """References to skills of layers the referencing layer may not depend on. A line that names the owning pack
    (e.g. `(pack-it)`) is an explicit, conditional mention and is allowed."""
    import re
    owners = skill_owners()
    pattern = re.compile(r"(?<![\w/-])(" + "|".join(sorted(map(re.escape, owners), key=len, reverse=True)) + r")(?![\w-])")
    layers = {"core": ROOT / "core", **{p.name: p for p in sorted((ROOT / "packs").iterdir()) if p.is_dir()}}
    total = 0
    for layer, base in layers.items():
        ok = allowed_packs(layer) | {layer, "core"}
        found: dict[str, list[str]] = {}
        for f in sorted(base.rglob("*")):
            if not f.is_file() or f.suffix not in (".md", ".yaml", ".yml", ".json", ".py") or "_vendor" in f.parts \
                    or f.name == "CHANGELOG.md" or "tests" in f.relative_to(base).parts:   # testy: dane testowe; zgodność bez nakładek sprawdza matrix
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


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "check"
    o = opts_of(argv[2:])
    if cmd == "assemble":
        print(assemble(o))
        return 0
    if cmd == "check":
        return 0 if check(o) else 1
    if cmd == "matrix":
        packs = sorted(p.parent.name for p in (ROOT / "packs").glob("*/pack.yaml"))
        results = {}
        for sel in ["none", *packs, "all"]:
            # „none” = sam rdzeń: język en, bo pl dokłada pack-editorial-pl
            results[sel] = check({**o, "packs": sel, "out": None, "language": "en" if sel == "none" else o["language"]})
        print("\n".join(f"{'✓' if v else '✗'} {k}" for k, v in results.items()))
        return 0 if all(results.values()) else 1
    if cmd == "sync-gate":
        return sync_gate(o)
    if cmd == "refs":
        return refs("--verbose" in argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
