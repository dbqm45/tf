#!/usr/bin/env python3
"""
Development workspace for the factory: an installed project assembled from core/ and packs/, where the build check
and the factory tests run (tests and build expect the installed layout, not the source tree).

  python3 tools/workspace.py assemble [--packs all|none|a,b] [--out DIR] [--language pl] [--commit-language en]
  python3 tools/workspace.py check    [same options]   # assemble + build check + tests + scenario validation + gate status
  python3 tools/workspace.py matrix                    # check: core only, each pack alone, all packs
  python3 tools/workspace.py sync-gate [--out DIR]     # copy gate results from the workspace back to core/ and packs/

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
        ok &= run(ws, [sys.executable, ".claude/tests/run_skill_evals.py", "--validate"])
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
            results[sel] = check({**o, "packs": sel, "out": None})
        print("\n".join(f"{'✓' if v else '✗'} {k}" for k, v in results.items()))
        return 0 if all(results.values()) else 1
    if cmd == "sync-gate":
        return sync_gate(o)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
