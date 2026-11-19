#!/usr/bin/env python3
"""dna — project knowledge for writing code like the team (factory add-on, contract 1).

  python3 dna.py learn  [--root <repo>] [--out <dir>]   # build out/ from the repository
  python3 dna.py verify [--root <repo>] [--out <dir>]   # check out/ against the contract
  python3 dna.py status [--root <repo>] [--out <dir>]   # what out/ holds, when it was built

--root: the repository to learn (default: the git top level of the current directory).
--out: the output directory (default: out/ next to this file).

`learn` builds the new output in a temporary directory, checks it (`verify`) and only then replaces out/;
a failed check leaves the previous out/ untouched. Exit codes: 0 ok, 1 check failed, 2 usage error.
Standard library and PyYAML only; no network in this version (0.1.0: stack and versions, commands, tooling).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ADDON = Path(__file__).resolve().parent
sys.path.insert(0, str(ADDON))
sys.dont_write_bytecode = True

try:
    import yaml  # noqa: E402
except ImportError:  # the factory ships PyYAML in .tf/factory/_vendor; outside it, install it
    print("dna: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

from lib import detect, emit, verify  # noqa: E402


def _version() -> str:
    return str((yaml.safe_load((ADDON / "addon.yaml").read_text(encoding="utf-8")) or {}).get("version", "0.0.0"))


def _git_root(start: Path) -> Path | None:
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start, capture_output=True, text=True,
                           timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def _commit(root: Path) -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() or None if r.returncode == 0 else None


def build(root: Path, today: str | None = None) -> dict:
    found = detect.detect(root, ADDON / "registry")
    return {
        "contract": 1,
        "generator": f"dna {_version()}",
        "generated": today or dt.date.today().isoformat(),
        "commit": _commit(root),
        "items": found["items"],
        "coverage": found["coverage"],
        "layers": {"stack": True},
    }


def cmd_learn(root: Path, out: Path) -> int:
    k = build(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".dna-new-", dir=out.parent))
    try:
        emit.write(k, tmp)
        problems = verify.check_out(tmp, root)
        if problems:
            print("✗ dna learn: the new output fails the check; out/ left unchanged:", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            return 1
        old = out.with_name(out.name + ".old")
        if old.exists():
            shutil.rmtree(old)
        if out.exists():
            out.rename(old)
        tmp.rename(out)
        if old.exists():
            shutil.rmtree(old)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
    stack = [i for i in k["items"] if i.get("data", {}).get("topic") == "stack"]
    print(f"✓ dna learn: {len(k['items'])} items ({len(stack)} stack), {len(k['coverage']['read'])} sources read"
          f" → {out}")
    return 0


def cmd_verify(root: Path, out: Path) -> int:
    problems = verify.check_out(out, root)
    if problems:
        print("✗ dna verify:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"✓ dna verify: {out} matches contract 1")
    return 0


def cmd_status(root: Path, out: Path) -> int:
    kf = out / "knowledge.json"
    if not kf.is_file():
        print(f"dna: no output yet in {out} — run: python3 {Path(__file__).name} learn")
        return 0
    k = json.loads(kf.read_text(encoding="utf-8"))
    head = _commit(root)
    fresh = "up to date with HEAD" if head and head == k.get("commit") else "built on another commit"
    print(f"dna: {len(k['items'])} items, generated {k['generated']} by {k['generator']}, {fresh}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="dna.py", description=__doc__.split("\n")[1])
    ap.add_argument("command", choices=["learn", "verify", "status"])
    ap.add_argument("--root", type=Path)
    ap.add_argument("--out", type=Path, default=ADDON / "out")
    args = ap.parse_args(argv)
    root = (args.root or _git_root(Path.cwd()) or Path.cwd()).resolve()
    if not root.is_dir():
        print(f"dna: not a directory: {root}", file=sys.stderr)
        return 2
    out = args.out.resolve()
    return {"learn": cmd_learn, "verify": cmd_verify, "status": cmd_status}[args.command](root, out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
