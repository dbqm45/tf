#!/usr/bin/env python3
"""dna — project knowledge for writing code like the team (factory add-on, contract 1).

  python3 dna.py learn  [--root <repo>] [--out <dir>]   # build out/ from the repository
  python3 dna.py refresh [--quiet]                      # learn again only when the inputs changed (fingerprint)
  python3 dna.py verify [--root <repo>] [--out <dir>]   # check out/ against the contract
  python3 dna.py status [--root <repo>] [--out <dir>]   # what out/ holds, when it was built
  python3 dna.py docs query <tech> "<topic>" [--version <v>] [--max-chars N] [--json]
                                                        # official docs of the project's version (local index)
  python3 dna.py check [--base <ref>] [--json]          # the change against the guidelines; exit 1 = blocking
  python3 dna.py standards add <git URL> [--ref <tag>] [--dir <skills dir>] [--scope fe|be|mutual] | list | remove
                                                        # standards skills from a repository (cloned in cache/)

--root: the repository to learn (default: the git top level of the current directory).
--out: the output directory (default: out/ next to this file). --cache: fetched sources (default: cache/ here).
--offline: `learn` uses only installed packages for documentation (no network).

`learn` builds the new output in a temporary directory, checks it (`verify`) and only then replaces out/;
a failed check leaves the previous out/ untouched. Exit codes: 0 ok, 1 check failed, 2 usage error or no index; `docs query` 3: the version asked for is not the one
in the project (the answer is still given). Standard library and PyYAML only. Network: only `learn` without
--offline, only to package registries and the hosts in registry/docs-sources.yaml (see lib/docs.py).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
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

from lib import check, code, decide, detect, docs, emit, exemplars, sources, verify  # noqa: E402


def config_path() -> Path:
    """dna.yaml next to this file; DNA_CONFIG points elsewhere (tests, a shared configuration)."""
    return Path(os.environ.get("DNA_CONFIG") or ADDON / "dna.yaml")


def load_config() -> dict:
    p = config_path()
    try:
        return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.is_file() else {}
    except (OSError, yaml.YAMLError):
        return {}


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


def build(root: Path, today: str | None = None, online: bool = False, cache: Path | None = None,
          docs_opts: dict | None = None) -> dict:
    today = today or dt.date.today().isoformat()
    found = detect.detect(root, ADDON / "registry")
    items, coverage = found["items"], found["coverage"]
    config = load_config()
    found, cov = sources.collect(root, config, online, today, {**(docs_opts or {}), "cache": cache or ADDON / "cache"})
    decisions = decide.decide(found)
    items += decisions
    coverage["read"] += cov["read"]
    coverage["skipped"] += cov["skipped"]
    blocks, cov = code.ui(root, items, config)
    items += blocks
    coverage["read"] += cov["read"]
    coverage["skipped"] += cov["skipped"]
    examples, cov = exemplars.exemplars(root, items)
    items += examples
    coverage["read"] += cov["read"]
    facts, cov = docs.build(root, items, ADDON / "registry", cache or ADDON / "cache", online, today, docs_opts)
    items += facts
    coverage["read"] += [s for s in cov["read"] if s not in coverage["read"]]
    coverage["skipped"] += cov["skipped"]
    return {
        "contract": 1,
        "generator": f"dna {_version()}",
        "generated": today,
        "commit": _commit(root),
        "fingerprint": fingerprint(root),
        "items": items,
        "coverage": coverage,
        "layers": {"stack": True, "decisions": bool(decisions), "ui": bool(blocks), "exemplars": bool(examples), "docs": bool(facts)},
    }


def cmd_learn(root: Path, out: Path, online: bool = True, cache: Path | None = None) -> int:
    k = build(root, online=online, cache=cache)
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
    docs_n = sum(1 for i in k["items"] if i.get("data", {}).get("topic") == "docs")
    print(f"✓ dna learn: {len(k['items'])} items ({len(stack)} stack, {docs_n} documentation indexes), "
          f"{len(k['coverage']['read'])} sources read, {len(k['coverage']['skipped'])} not read → {out}")
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


def fingerprint(root: Path) -> str:
    """What `learn` depends on: HEAD, the changed and untracked files (path, size, mtime), the standards skills,
    dna.yaml and the add-on version. Same fingerprint → `refresh` does nothing."""
    import hashlib
    h = hashlib.sha256(_version().encode())
    h.update((_commit(root) or "").encode())
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=20)
        changed = [ln[3:].strip().strip('"') for ln in r.stdout.splitlines()] if r.returncode == 0 else []
    except (OSError, subprocess.TimeoutExpired):
        changed = []
    extra = [p for p in (root / ".claude" / "skills").glob("*standard*/**/*") if p.is_file()] \
        if (root / ".claude" / "skills").is_dir() else []
    own = (".tf/", ".claude/rules/addon-", ".claude/settings.local.json")   # written by the factory and add-ons
    cfg = load_config()   # standards repositories: their current commit (a cheap ls-remote; offline: ignored)
    if os.environ.get("DNA_OFFLINE") != "1":
        for s in cfg.get("standards") or []:
            if s.get("git"):
                try:
                    r = subprocess.run(["git", "ls-remote", s["git"], s.get("ref") or "HEAD"], capture_output=True,
                                       text=True, timeout=15, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
                    h.update(r.stdout.split("\t")[0].encode())
                except (OSError, subprocess.TimeoutExpired):
                    pass
    for p in sorted({*(root / c for c in changed if not c.startswith(own)), *extra, config_path()}):
        try:
            if p.name in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md"):   # a source, but the factory writes blocks in it
                text = sources.FACTORY_BLOCK.sub("", p.read_text(encoding="utf-8", errors="replace"))
                if not text.strip():
                    continue   # only the factory's block: as if the file were absent
                h.update(f"{p.name}|{hashlib.sha256(text.encode()).hexdigest()}".encode())
                continue
            st = p.stat()
            h.update(f"{p.relative_to(root) if root in p.parents else p}|{st.st_size}|{st.st_mtime_ns}".encode())
        except OSError:
            h.update(str(p).encode())
    return h.hexdigest()[:16]


def cmd_refresh(root: Path, out: Path, online: bool, cache: Path, quiet: bool) -> int:
    try:
        old = json.loads((out / "knowledge.json").read_text(encoding="utf-8")).get("fingerprint")
    except (OSError, ValueError):
        old = None
    if old and old == fingerprint(root):
        if not quiet:
            print("dna refresh: up to date")
        return 0
    return cmd_learn(root, out, online=online, cache=cache)


def cmd_standards(args: list[str], ref: str | None, sub_dir: str | None, scope: str | None) -> int:
    """dna.yaml `standards`: add a repository with standards skills by URL, or list what is configured."""
    cfg_path = config_path()
    cfg = load_config()
    entries = cfg.setdefault("standards", [])
    if args[:1] == ["list"] or not args:
        for e in entries:
            print(f"- {e.get('git') or e.get('path')}" + (f" @{e['ref']}" if e.get("ref") else "")
                  + (f" dir={e['dir']}" if e.get("dir") else "") + (f" scope={e['scope']}" if e.get("scope") else ""))
        if not entries:
            print("dna: no standards configured — skills named *standards* in .claude/skills/ are used")
        return 0
    if args[0] == "add" and len(args) == 2:
        src = args[1]
        entry = {"git": src} if re.match(r"^(https://|git@|ssh://|file://)", src) else {"path": src}
        entry.update({k: v for k, v in (("ref", ref), ("dir", sub_dir), ("scope", scope)) if v})
        entries[:] = [e for e in entries if (e.get("git"), e.get("path"), e.get("dir")) !=
                      (entry.get("git"), entry.get("path"), entry.get("dir"))] + [entry]
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(f"✓ dna: standards source added ({src}) in {cfg_path.name} — run: tf learn")
        return 0
    if args[0] == "remove" and len(args) == 2:
        entries[:] = [e for e in entries if args[1] not in (e.get("git"), e.get("path"))]
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(f"✓ dna: standards source removed ({args[1]})")
        return 0
    print("✗ Usage: dna.py standards add <git URL | path> [--ref <branch|tag>] [--dir <path in repo>] "
          "[--scope fe|be|mutual] | list | remove <git URL | path>", file=sys.stderr)
    return 2


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


def cmd_docs(out: Path, cache: Path, args: list[str], version: str | None, max_chars: int, as_json: bool) -> int:
    if len(args) != 3 or args[0] != "query":
        print('✗ Usage: dna.py docs query <tech> "<topic>" [--version <v>]', file=sys.stderr)
        return 2
    tech, topic = args[1], args[2]
    try:
        k = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        k = {"items": []}
    project = sorted({i["data"]["version"] for i in k["items"] if i.get("data", {}).get("topic") == "docs"
                      and i["data"]["tech"] == tech})
    if not version:
        if len(project) != 1:
            print(f"✗ dna docs: {tech}: " + (f"several versions in the project {project} — add --version"
                                             if project else "no documentation index — run: dna.py learn"),
                  file=sys.stderr)
            return 2
        version = project[0]
    res = docs.query(cache, tech, version, topic, max_chars)
    if res.get("code") == 2:
        print(f"✗ dna docs: {res['error']} — run: dna.py learn", file=sys.stderr)
        return 2
    code = 0 if version in project else 3
    if code == 3:
        print(f"⚠ dna docs: {tech}@{version} is not the version in this project ({project or 'none indexed'})",
              file=sys.stderr)
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return code
    print(f"{tech}@{version} — official documentation, fetched {res['fetched']} — {res['marker']}")
    for h in res["hits"] or []:
        print(f"\n## {h['title']}  [{h['source']}{'' if h['match'] == 'exact' else ', ' + h['match']}]\n{h['text']}")
    if not res["hits"]:
        print("(no matching fragment)")
    return code


def cmd_check(root: Path, out: Path, base: str, as_json: bool) -> int:
    try:
        k = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("dna check: no guidelines yet — run: dna.py learn", file=sys.stderr)
        return 0
    try:
        res = check.check(root, k, base)
    except RuntimeError as e:
        print(f"dna check: {e}", file=sys.stderr)
        return 2
    blocking = [f for f in res["findings"] if f["severity"] == "block"]
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for f in res["findings"]:
            mark = "✗" if f["severity"] == "block" else "⚠"
            print(f"{mark} {f['file']}:{f['line']} [{f['rule']}, {f['strength']}] {f['message']} → {f['suggestion']}")
        print(res["summary"])
    return 1 if blocking else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="dna.py", description=__doc__.split("\n")[1])
    ap.add_argument("command", choices=["learn", "refresh", "verify", "status", "docs", "check", "standards"])
    ap.add_argument("--ref")
    ap.add_argument("--dir", dest="sub_dir")
    ap.add_argument("--scope", choices=["fe", "be", "mutual"])
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--root", type=Path)
    ap.add_argument("--out", type=Path, default=ADDON / "out")
    ap.add_argument("--cache", type=Path, default=ADDON / "cache")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--version")
    ap.add_argument("--max-chars", type=int, default=6000)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--base", default="HEAD")
    args = ap.parse_args(argv)
    out, cache = args.out.resolve(), args.cache.resolve()
    if args.command == "standards":
        return cmd_standards(args.args, args.ref, args.sub_dir, args.scope)
    if args.command == "docs":
        return cmd_docs(out, cache, args.args, args.version, args.max_chars, args.json)
    root = (args.root or _git_root(Path.cwd()) or Path.cwd()).resolve()
    if not root.is_dir():
        print(f"dna: not a directory: {root}", file=sys.stderr)
        return 2
    if args.command == "check":
        return cmd_check(root, out, args.base, args.json)
    offline = args.offline or os.environ.get("DNA_OFFLINE") == "1"   # DNA_OFFLINE=1: tests, air-gapped machines
    if args.command == "learn":
        return cmd_learn(root, out, online=not offline, cache=cache)
    if args.command == "refresh":
        return cmd_refresh(root, out, not offline, cache, args.quiet)
    return {"verify": cmd_verify, "status": cmd_status}[args.command](root, out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
