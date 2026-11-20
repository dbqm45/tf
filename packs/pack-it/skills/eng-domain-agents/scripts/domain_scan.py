#!/usr/bin/env python3
"""
Domain layout of a monorepo, DETECTED from facts (Nx projects and tags, module-boundary rules, tsconfig path aliases,
real imports, CODEOWNERS, routes, generated code, feature flags) — and the per-domain agent files built from them.
Standard library only (PyYAML or the factory's bundled copy is used only to read `.tf/config/domains.yaml`).
No network. `scan` is read-only; `write` creates only the files that `plan` lists.

  python3 domain_scan.py scan  [--root .] [--json]
  python3 domain_scan.py plan  [--root .] [--pack-dir tools/tf-pack] [--project-id <id>] [--json]
  python3 domain_scan.py write [same]     # never overwrites a file a human edited: the new version goes to <file>.tf-new
  python3 domain_scan.py check [same]     # drift only; exit 1 when generated files are out of date (CI)

Exit codes: 0 found with high confidence (or the human's `.tf/config/domains.yaml`), 1 ambiguous or low confidence
(the skill asks the human ONE question with the candidates) or drift (`check`), 2 call error.

`.tf/config/domains.yaml` (the human's answer, the source of truth when present):
  layout: {glob: "domains/*"}                 # directories that are domains
  domains: {billing: {root: domains/billing, scope: "…", owner: "…", notes: "…"}}   # optional, adds facts/overrides
  exclude: [shared]
"""
from __future__ import annotations

import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import posixpath
import re
import sys
from collections import defaultdict
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".nx", ".angular", "coverage", ".tf", ".claude", ".work", ".venv",
             "venv", "__pycache__", "tmp", "out", "target", ".next", ".cache", ".idea", ".vscode", "bower_components"}
SRC_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".vue", ".svelte"}
SHARED_NAMES = {"shared", "common", "util", "utils", "ui", "core", "platform", "data-access", "feature", "styles", "assets"}
LIB_TYPES = {"feature", "data-access", "ui", "util", "utils", "shell", "domain", "api", "models", "types", "lib", "e2e",
             "testing", "test", "store", "state", "infrastructure"}
CONTAINER_WEIGHT = {"domains": 3, "domain": 3, "contexts": 3, "bounded-contexts": 3, "modules": 3, "features": 3,
                    "services": 1, "packages": 1, "libs": 1, "apps": -1}
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
MARK = "tf:domain-agents v1"
MAX_FILES = 400_000


# ---------------------------------------------------------------- files and JSON

def posix(p) -> str:
    return str(p).replace("\\", "/")


def strip_jsonc(s: str) -> str:
    out, i, n, instr = [], 0, len(s), False
    while i < n:
        c = s[i]
        if instr:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(s[i + 1])
                i += 2
                continue
            if c == '"':
                instr = False
            i += 1
            continue
        if c == '"':
            instr = True
            out.append(c)
            i += 1
        elif s.startswith("//", i):
            while i < n and s[i] not in "\r\n":
                i += 1
        elif s.startswith("/*", i):
            j = s.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            out.append(c)
            i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def read_text(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8-sig", errors="replace").replace("\r\n", "\n")
    except OSError:
        return ""


def load_jsonc(path: Path):
    try:
        data = json.loads(strip_jsonc(read_text(path)))
    except (ValueError, OSError):
        return None
    return data if isinstance(data, dict) else None


def list_files(root: Path) -> list[str]:
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
        rel = posix(os.path.relpath(dp, root))
        for f in sorted(fns):
            out.append(f if rel == "." else f"{rel}/{f}")
        if len(out) > MAX_FILES:
            break
    return out


def under(path: str, root: str) -> bool:
    return root == "." or path == root or path.startswith(root + "/")


# ---------------------------------------------------------------- Nx projects, boundaries, aliases

def load_projects(root: Path, files: list[str]) -> list[dict]:
    projects = []
    for f in files:
        base = posixpath.basename(f)
        d = posixpath.dirname(f) or "."
        if base == "project.json":
            j = load_jsonc(root / f)
            if j is None:
                continue
            projects.append({"name": j.get("name") or posixpath.basename(d) or "root", "root": d, "tags": list(j.get("tags") or []),
                             "targets": {k: (v.get("executor") or ("nx:run-commands" if v.get("command") else "")) if isinstance(v, dict) else ""
                                         for k, v in (j.get("targets") or {}).items()},
                             "sourceRoot": j.get("sourceRoot", ""), "file": f})
        elif base == "package.json" and d != ".":
            j = load_jsonc(root / f)
            nx = j.get("nx") if j else None
            if isinstance(nx, dict):
                projects.append({"name": j.get("name") or posixpath.basename(d), "root": d, "tags": list(nx.get("tags") or []),
                                 "targets": {k: (v.get("executor") or "") if isinstance(v, dict) else "" for k, v in (nx.get("targets") or {}).items()},
                                 "sourceRoot": "", "file": f})
    return [p for p in projects if p["root"] != "."]


def balanced(text: str, start: int, open_c: str, close_c: str) -> str:
    """Text of the balanced block that opens at text[start] (quotes respected)."""
    depth, i, q = 0, start, ""
    while i < len(text):
        c = text[i]
        if q:
            if c == "\\":
                i += 1
            elif c == q:
                q = ""
        elif c in "'\"`":
            q = c
        elif c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return text[start:]


def split_objects(block: str) -> list[str]:
    out, i = [], 0
    while True:
        j = block.find("{", i)
        if j < 0:
            return out
        obj = balanced(block, j, "{", "}")
        out.append(obj)
        i = j + len(obj)


STR = re.compile(r"""(['"`])((?:\\.|(?!\1).)*)\1""")


def parse_boundaries(root: Path, files: list[str]) -> dict | None:
    cands = [f for f in files if "/" not in f and re.match(r"(eslint\.config\.(mjs|js|cjs|ts|mts)|\.eslintrc(\.json|\.js|\.cjs)?)$", f)]
    for f in cands:
        text = read_text(root / f)
        k = text.find("enforce-module-boundaries")
        if k < 0:
            continue
        j = text.find("{", k)
        if j < 0:
            continue
        opts = balanced(text, j, "{", "}")
        constraints = []
        m = re.search(r"depConstraints[\"']?\s*:\s*\[", opts)
        if m:
            arr = balanced(opts, m.end() - 1, "[", "]")
            for obj in split_objects(arr[1:-1]):
                src = re.search(r"""["']?sourceTag["']?\s*:\s*["']([^"']+)["']""", obj)
                only = re.search(r"""["']?onlyDependOnLibsWithTags["']?\s*:\s*\[([^\]]*)\]""", obj)
                if src and only:
                    constraints.append({"sourceTag": src.group(1), "only": [x.group(2) for x in STR.finditer(only.group(1))]})
        allow = []
        m = re.search(r"""["']?allow["']?\s*:\s*\[""", opts)
        if m:
            arr = balanced(opts, m.end() - 1, "[", "]")
            allow = [x.group(2) for x in STR.finditer(arr)]
            allow += [x.group(1) for x in re.finditer(r"(?<![\w'\"/])/((?:\\.|[^/\n])+)/[a-z]*", re.sub(STR, "", arr))]
        return {"file": f, "constraints": constraints, "allow": allow}
    return None


def load_paths(root: Path) -> dict[str, list[str]]:
    for name in ("tsconfig.base.json", "tsconfig.json", "jsconfig.json"):
        seen, cur = set(), name
        while cur and cur not in seen and (root / cur).is_file():
            seen.add(cur)
            j = load_jsonc(root / cur)
            if not j:
                break
            co = j.get("compilerOptions") or {}
            paths = co.get("paths")
            if isinstance(paths, dict) and paths:
                base_url = co.get("baseUrl", ".")
                out = {}
                for alias, targets in paths.items():
                    out[alias] = [posixpath.normpath(posixpath.join(posixpath.dirname(cur) or ".", base_url, t)) for t in targets
                                  if isinstance(t, str)]
                return out
            ext = j.get("extends")
            cur = posixpath.normpath(posixpath.join(posixpath.dirname(cur), ext)) if isinstance(ext, str) and ext.startswith(".") else ""
    return {}


def resolve_alias(spec: str, aliases: dict[str, list[str]]) -> str | None:
    """Path an import specifier points to (via tsconfig paths) or None."""
    if spec in aliases and aliases[spec]:
        return aliases[spec][0]
    for key, tg in aliases.items():
        if "*" in key and tg:
            pre, post = key.split("*", 1)
            if spec.startswith(pre) and spec.endswith(post) and len(spec) >= len(pre) + len(post):
                mid = spec[len(pre):len(spec) - len(post)] if post else spec[len(pre):]
                return tg[0].replace("*", mid)
    return None


# ---------------------------------------------------------------- candidates

def common_dir(paths: list[str]) -> str:
    parts = [p.split("/") for p in paths]
    out = []
    for seg in zip(*parts):
        if len(set(seg)) == 1:
            out.append(seg[0])
        else:
            break
    return "/".join(out) or "."


def domain_tag_names(tags: list[str]) -> set[str]:
    return {t.split(":", 1)[1] for t in tags if t.startswith(("scope:", "domain:"))}


def build_candidates(ctx: dict) -> list[dict]:
    projects, files = ctx["projects"], ctx["files"]
    cands: dict[frozenset, dict] = {}

    def add(kind, glob, domains, evidence, nx=True):
        key = frozenset(domains.items())
        if len(domains) < 2:
            return
        if key in cands:
            cands[key]["evidence"] += evidence
            return
        cands[key] = {"kind": kind, "glob": glob, "domains": dict(sorted(domains.items())), "evidence": list(evidence), "nx": nx,
                      "score": 0, "excluded": []}

    if projects:
        by_parent = defaultdict(list)
        for p in projects:
            by_parent[posixpath.dirname(p["root"]) or "."].append(p)
        for parent, ps in by_parent.items():
            doms = {posixpath.basename(p["root"]): p["root"] for p in ps if posixpath.basename(p["root"]) not in SHARED_NAMES}
            if len(doms) >= 2:
                add("dir-per-project", f"{parent}/*" if parent != "." else "*", doms,
                    [f"{len(ps)} Nx projects are direct children of {parent}/: {', '.join(sorted(posixpath.basename(p['root']) for p in ps))}"])
        for k in (1, 2):
            groups = defaultdict(lambda: defaultdict(list))
            for p in projects:
                parts = p["root"].split("/")
                if len(parts) > k + 1:
                    groups["/".join(parts[:k])][parts[k]].append(p)
            for top, ds in groups.items():
                doms = {d: f"{top}/{d}" for d in ds if d not in SHARED_NAMES}
                if len(doms) >= 2 and any(len(v) >= 2 for d, v in ds.items() if d in doms):
                    add("grouped-libs", f"{top}/*", doms,
                        [f"{top}/<domain>/<lib> grouping: " + ", ".join(f"{d} ({len(ds[d])} projects)" for d in sorted(doms))])
        for pref in ("domain:", "scope:"):
            by_tag = defaultdict(list)
            for p in projects:
                for t in p["tags"]:
                    if t.startswith(pref) and t.split(":", 1)[1] not in SHARED_NAMES | {"app", "apps"}:
                        by_tag[t.split(":", 1)[1]].append(p["root"])
            doms = {v: common_dir(r) for v, r in by_tag.items()}
            doms = {v: r for v, r in doms.items() if r != "."}
            if len(doms) >= 2:
                add("tag", f"tag:{pref}*", doms, [f"tag values {pref}* name {len(doms)} domains with their own project roots"])
    else:
        dirs = defaultdict(set)
        for f in files:
            parts = f.split("/")
            for k in (1, 2):
                if len(parts) > k + 1:
                    dirs["/".join(parts[:k])].add(parts[k])
        containers = [c for c in dirs if posixpath.basename(c) in CONTAINER_WEIGHT]
        for c in containers:
            doms = {d: f"{c}/{d}" for d in dirs[c] if d not in SHARED_NAMES and d not in LIB_TYPES}
            add("directories", f"{c}/*", doms, [f"{len(doms)} directories under {c}/ (no Nx project files found)"], nx=False)
        pj = load_jsonc(ctx["root"] / "package.json") or {}
        ws = pj.get("workspaces")
        ws = ws.get("packages") if isinstance(ws, dict) else ws
        for pat in ws or []:
            if isinstance(pat, str) and pat.endswith("/*"):
                top = pat[:-2]
                doms = {posixpath.basename(posixpath.dirname(f)): posixpath.dirname(f) for f in files
                        if posixpath.basename(f) == "package.json" and posixpath.dirname(posixpath.dirname(f)) == top}
                add("workspaces", pat, doms, [f"package.json workspaces entry {pat}: {len(doms)} packages"], nx=False)
    return list(cands.values())


def score_candidate(c: dict, ctx: dict) -> None:
    s, ev = 0, c["evidence"]
    names, roots = list(c["domains"]), c["domains"]
    base = c["glob"].split("/*")[0].split("/")[-1] if "/*" in c["glob"] else ""
    w = CONTAINER_WEIGHT.get(base, 0)
    if w:
        s += w
        ev.append(f"container name '{base}' {'looks like' if w > 0 else 'is not'} a domain container ({w:+d})")
    if base in SHARED_NAMES:
        s -= 3
        ev.append(f"container '{base}' is a shared-code name (-3)")
    if sum(1 for n in names if n in LIB_TYPES or n.startswith(("feature-", "data-access-"))) * 3 >= len(names) * 2:
        s -= 6
        ev.append("the entries look like library types (feature, ui, data-access…), not domains (-6)")
    own = 0
    for n, r in roots.items():
        tags = set().union(*[set(p["tags"]) for p in ctx["projects"] if under(p["root"], r)] or [set()])
        if f"scope:{n}" in tags or f"domain:{n}" in tags:
            own += 1
    if own and own == len(names):
        s += 3
        ev.append(f"every domain has its own scope:/domain: tag ({own}/{len(names)}) (+3)")
    elif own * 2 >= len(names):
        s += 1
        ev.append(f"{own}/{len(names)} domains have their own scope:/domain: tag (+1)")
    b = ctx["boundaries"]
    if b and b["constraints"]:
        srcs = {x["sourceTag"] for x in b["constraints"]}
        hit = sum(1 for n, r in roots.items()
                  if srcs & set().union(*[set(p["tags"]) for p in ctx["projects"] if under(p["root"], r)] or [set()]))
        if hit * 2 >= len(names):
            s += 3
            ev.append(f"module-boundary rules ({b['file']}) name tags of {hit}/{len(names)} domains (+3)")
    al = sum(1 for n, r in roots.items() if any(under(t, r) for ts in ctx["aliases"].values() for t in ts[:1]))
    if al and al * 2 >= len(names):
        s += 2
        ev.append(f"tsconfig path aliases point into {al}/{len(names)} domains (+2)")
    if len(names) >= 3:
        s += 1
    if not c["nx"]:
        s = min(s, 5)
        ev.append("no Nx project files: score capped, low confidence")
    c["score"] = s


# ---------------------------------------------------------------- facts per domain

def human_config(root: Path) -> dict | None:
    p = root / ".tf" / "config" / "domains.yaml"
    if not p.is_file():
        return None
    try:
        import yaml
    except ImportError:
        for anc in Path(__file__).resolve().parents:
            if (anc / ".tf" / "factory" / "_vendor").is_dir():
                sys.path.insert(0, str(anc / ".tf" / "factory" / "_vendor"))
                break
        try:
            import yaml
        except ImportError:
            raise SystemExit("domain_scan: cannot read .tf/config/domains.yaml (PyYAML missing, no .tf/factory/_vendor)")
    try:
        data = yaml.safe_load(read_text(p)) or {}
    except yaml.YAMLError as e:
        raise SystemExit(f"domain_scan: .tf/config/domains.yaml is not valid YAML: {e}")
    if not isinstance(data, dict):
        raise SystemExit("domain_scan: .tf/config/domains.yaml must be a mapping")
    return data


def config_domains(cfg: dict, files: list[str]) -> dict[str, str]:
    doms: dict[str, str] = {}
    glob = (cfg.get("layout") or {}).get("glob") if isinstance(cfg.get("layout"), dict) else None
    if glob:
        parent = posixpath.dirname(glob)
        pat = posixpath.basename(glob)
        for d in sorted({posixpath.dirname(f) for f in files if posixpath.dirname(posixpath.dirname(f)) == parent}
                        | {"/".join(f.split("/")[:len(parent.split("/")) + 1]) for f in files if under(f, parent) and f != parent}):
            if posixpath.dirname(d) == parent and fnmatch.fnmatch(posixpath.basename(d), pat) and any(under(f, d) for f in files):
                doms[posixpath.basename(d)] = d
    for n, v in (cfg.get("domains") or {}).items():
        v = v or {}
        doms[str(n)] = posix(v.get("root") or doms.get(str(n)) or (f"{posixpath.dirname(glob)}/{n}" if glob else str(n)))
    for n in cfg.get("exclude") or []:
        doms.pop(str(n), None)
    return dict(sorted(doms.items()))


def match_allow(spec: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if pat == spec or fnmatch.fnmatch(spec, pat):
            return True
        try:
            if re.search(pat, spec):
                return True
        except re.error:
            pass
    return False


def domain_facts(ctx: dict, name: str, root: str, human: dict | None) -> dict:
    projects = [p for p in ctx["projects"] if under(p["root"], root)]
    tags = sorted({t for p in projects for t in p["tags"]})
    ents = [{"alias": a, "path": ts[0]} for a, ts in sorted(ctx["aliases"].items()) if "*" not in a and ts and under(ts[0], root)]
    f = {"name": name, "root": root, "projects": [p["name"] for p in projects], "tags": tags, "entrypoints": ents,
         "human": {k: v for k, v in (human or {}).items() if k in ("scope", "owner", "notes") and v}}
    # commands
    cmds: dict = {}
    primary = next((p for p in projects if p["root"] == root), projects[0] if len(projects) == 1 else None)
    nx_exec = lambda p, t: p["targets"].get(t, "")  # noqa: E731
    if primary:
        n = primary["name"]
        explicit = primary["targets"]
        if not explicit or "test" in explicit:
            cmds["test"] = f"npx nx test {n}"
            if "jest" in nx_exec(primary, "test") or (not explicit and "jest" in ctx["stack_text"]):
                cmds["test_file"] = f"npx nx run {n}:test --testFile=<path>"
        if not explicit or "lint" in explicit:
            cmds["lint"] = f"npx nx lint {n}"
        cmds["generate"] = [f"npx nx run {n}:{t}" for t in explicit if re.match(r"(generate|codegen|openapi)", t)]
    elif projects:
        sel = next((t for t in tags if t in (f"scope:{name}", f"domain:{name}")), None)
        names = ",".join(p["name"] for p in projects)
        cmds["test"] = f"npx nx run-many -t test --projects={'tag:' + sel if sel else names}"
        cmds["lint"] = f"npx nx run-many -t lint --projects={'tag:' + sel if sel else names}"
        cmds["generate"] = sorted({f"npx nx run {p['name']}:{t}" for p in projects for t in p["targets"]
                                   if re.match(r"(generate|codegen|openapi)", t)})
    else:
        pj = load_jsonc(ctx["root"] / root / "package.json") or {}
        for t in ("test", "lint"):
            if t in (pj.get("scripts") or {}):
                cmds[t] = f"npm --prefix {root} run {t}"
        cmds["generate"] = []
    f["commands"] = cmds
    # boundaries
    b = ctx["boundaries"]
    allowed = {"known": False, "tags": [], "domains": [], "allow_entrypoints": [], "allow": b["allow"] if b else []}
    if b and b["constraints"]:
        mine = [c for c in b["constraints"] if c["sourceTag"] in tags or c["sourceTag"] == "*"]
        if mine:
            allowed["known"] = True
            at = sorted({t for c in mine for t in c["only"]})
            allowed["tags"] = at
            for on, oroot in ctx["current_domains"].items():
                if on == name:
                    continue
                otags = {t for p in ctx["projects"] if under(p["root"], oroot) for t in p["tags"]}
                if "*" in at or otags & set(at):
                    allowed["domains"].append(on)
    f["allowed"] = allowed
    # actual imports
    counts: dict = defaultdict(lambda: {"files": set()})
    for src in ctx["src_files"]:
        if not under(src, root) or ctx["owner_of"](src) != name:
            continue
        for spec in ctx["imports"](src):
            tgt = None
            rel = False
            if spec.startswith("."):
                tgt, rel = posixpath.normpath(posixpath.join(posixpath.dirname(src), spec)), True
            else:
                tgt = resolve_alias(spec, ctx["aliases"])
                if tgt is None and spec.startswith("@") and spec.count("/") >= 1:
                    seg = spec.split("/")[1]
                    if seg in ctx["current_domains"]:
                        tgt = ctx["current_domains"][seg] + "/"
            if not tgt:
                continue
            dst = ctx["owner_of"](tgt.rstrip("/") if not tgt.endswith("/") else tgt[:-1])
            if dst and dst != name:
                counts[(dst, spec, rel)]["files"].add(src)
    imports, viol = [], []
    for (dst, spec, rel), v in sorted(counts.items()):
        entry = {"to": dst, "spec": spec, "files": len(v["files"]), "relative": rel}
        imports.append(entry)
        if allowed["known"] and (rel or not (dst in allowed["domains"] or match_allow(spec, allowed["allow"]))):
            viol.append(entry)
    f["imports"], f["violations"] = imports, viol
    allowed["allow_entrypoints"] = sorted({e["alias"] for on, orr in ctx["current_domains"].items() if on != name
                                           for e in [{"alias": a} for a, ts in ctx["aliases"].items()
                                                     if "*" not in a and ts and under(ts[0], orr)]
                                           if match_allow(e["alias"], allowed["allow"])})
    allowed.pop("allow", None)
    # signals
    dfiles = [x for x in ctx["files"] if under(x, root)]
    rel_of = lambda x: x[len(root) + 1:] if root != "." else x  # noqa: E731
    sig = {"owners": [], "docs": [], "routes": [], "generated": [], "flags": [], "instructions": []}
    for line in ctx["codeowners"]:
        parts = line.split()
        pat = parts[0].strip("/").rstrip("*").rstrip("/") if parts else ""
        if len(parts) > 1 and pat and (pat == root or root.startswith(pat + "/") or pat.startswith(root + "/")):
            sig["owners"] += [o for o in parts[1:] if o not in sig["owners"]]
    for x in dfiles:
        r = rel_of(x)
        b_ = posixpath.basename(x)
        if b_.lower() in ("readme.md",) and "/" not in r:
            sig["docs"].append(r)
        elif r.startswith("docs/") and r.endswith(".md") and r.count("/") == 1:
            sig["docs"].append(r)
        if b_ in ("AGENTS.md", "CLAUDE.md") and "/" not in r:
            sig["instructions"].append(b_)
        if re.search(r"\.routes\.(ts|js)$", b_) or b_ in ("routes.ts", "app.routes.ts"):
            sig["routes"].append(r)
        parts = r.split("/")
        gen = next((i for i, s_ in enumerate(parts[:-1]) if s_ in ("generated", "generated-api", "__generated__", "openapi", "gen")), None)
        if gen is not None:
            g = "/".join(parts[:gen + 1]) + "/"
            sig["generated"].append(g)
        elif re.search(r"\.generated\.\w+$", b_):
            sig["generated"].append("*.generated.*")
        fl = next((i for i, s_ in enumerate(parts) if re.search(r"flag", s_, re.I)), None)
        if fl is not None:
            sig["flags"].append("/".join(parts[:fl + 1]) + ("/" if fl < len(parts) - 1 else ""))
    for k in ("docs", "routes", "generated", "flags", "instructions"):
        sig[k] = sorted(set(sig[k]))[:8]
    f["signals"] = sig
    return f


def make_ctx(root: Path) -> dict:
    files = list_files(root)
    projects = load_projects(root, files)
    pj = load_jsonc(root / "package.json") or {}
    stack_text = json.dumps({k: pj.get(k) for k in ("dependencies", "devDependencies")}) if pj else ""
    ctx = {"root": root, "files": files, "projects": projects, "boundaries": parse_boundaries(root, files), "aliases": load_paths(root),
           "stack_text": stack_text, "pkg": pj, "current_domains": {},
           "codeowners": [l.strip() for f in ("CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS") if f in files
                          for l in read_text(root / f).splitlines() if l.strip() and not l.strip().startswith("#")],
           "src_files": [f for f in files if posixpath.splitext(f)[1] in SRC_EXT]}
    cache: dict = {}
    rx = re.compile(r"""(?:\bfrom\s*|\bimport\s*\(?\s*|\brequire\s*\(\s*)['"]([^'"\n]+)['"]""")

    def imports(src: str) -> set[str]:
        if src not in cache:
            try:
                txt = (root / src).read_bytes()[:1_000_000].decode("utf-8", errors="replace")
            except OSError:
                txt = ""
            cache[src] = set(rx.findall(txt))
        return cache[src]

    ctx["imports"] = imports

    def owner_of(path: str) -> str | None:
        best = None
        for n, r in ctx["current_domains"].items():
            if under(path, r) and (best is None or len(r) > len(ctx["current_domains"][best])):
                best = n
        return best

    ctx["owner_of"] = owner_of
    return ctx


def facts_for(ctx: dict, domains: dict[str, str], human: dict) -> dict:
    ctx["current_domains"] = dict(domains)
    return {n: domain_facts(ctx, n, r, human.get(n)) for n, r in domains.items()}


def scan(root: Path) -> dict:
    cfg = human_config(root)
    ctx = make_ctx(root)
    notes = []
    if cfg is not None:
        domains = config_domains(cfg, ctx["files"])
        if not domains:
            raise SystemExit("domain_scan: .tf/config/domains.yaml gives no domains (check layout.glob / domains / exclude)")
        human = {str(k): (v or {}) for k, v in (cfg.get("domains") or {}).items()}
        facts = facts_for(ctx, domains, human)
        best = {"kind": "config", "glob": (cfg.get("layout") or {}).get("glob", ""), "score": None,
                "evidence": [".tf/config/domains.yaml is the source of truth; facts are filled from the code"], "domains": facts}
        return {"status": "found", "source": "config", "confidence": "high", "best": best, "alternatives": [], "notes": notes,
                "nx": bool(ctx["projects"]), "boundaries": ctx["boundaries"] and {"file": ctx["boundaries"]["file"]},
                "stack": detect_stack(ctx)}
    cands = build_candidates(ctx)
    for c in cands:
        score_candidate(c, ctx)
    cands.sort(key=lambda c: (-c["score"], c["glob"]))
    if not cands:
        return {"status": "none", "source": "detected", "confidence": "low", "best": None, "alternatives": [],
                "nx": bool(ctx["projects"]), "notes": ["no domain layout found: ask the human where the domains are"]}
    top = cands[0]
    ok = top["nx"] and top["score"] >= 6 and (len(cands) == 1 or top["score"] - cands[1]["score"] >= 3)
    facts = facts_for(ctx, top["domains"], {})
    best = {"kind": top["kind"], "glob": top["glob"], "score": top["score"], "evidence": top["evidence"], "domains": facts}
    alts = [{"kind": c["kind"], "glob": c["glob"], "score": c["score"], "domains": c["domains"], "evidence": c["evidence"]}
            for c in cands[1:6] if c["score"] > -3]
    if not ok:
        notes.append("low confidence" if not top["nx"] else "ambiguous: the best layout does not clearly beat the alternatives")
    return {"status": "found" if ok else "ambiguous", "source": "detected", "confidence": "high" if ok else "low", "best": best,
            "alternatives": alts, "notes": notes, "nx": bool(ctx["projects"]),
            "boundaries": ctx["boundaries"] and {"file": ctx["boundaries"]["file"]}, "stack": detect_stack(ctx)}


def detect_stack(ctx: dict) -> list[str]:
    t, out = ctx["stack_text"], []
    rules = [("@angular/core", "fw-angular"), ('"react"', "fw-react"), ('"next"', "fw-nextjs"), ("@nestjs/core", "fw-nestjs"),
             ('"nx"', "tool-nx"), ("@nx/", "tool-nx"), ('"jest"', "tool-jest"), ('"vitest"', "tool-vitest"),
             ("@playwright/test", "tool-playwright"), ('"typescript"', "lang-typescript")]
    for needle, skill in rules:
        if needle in t and skill not in out:
            out.append(skill)
    if ctx["projects"] and "tool-nx" not in out:
        out.append("tool-nx")
    if any(f.endswith((".ts", ".tsx")) for f in ctx["src_files"][:2000]) and "lang-typescript" not in out:
        out.append("lang-typescript")
    return out


# ---------------------------------------------------------------- rendering and file states

def sha(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def part_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:8]


def marker_line(body: str, parts: dict) -> str:
    ps = ",".join(f"{k}:{part_hash(v)}" for k, v in sorted(parts.items()))
    return f"{MARK} sha256={sha(body)} parts={ps}"


MARK_RE = re.compile(r"tf:domain-agents v1 sha256=([0-9a-f]{64}) parts=(\S*)")


def parse_marker(kind: str, text: str):
    """(body without the marker, {sha, parts}) or (text, None)."""
    text = text.replace("\r\n", "\n")
    if kind == "md":
        lines = text.rstrip("\n").split("\n")
        m = MARK_RE.search(lines[-1]) if lines else None
        if m and lines[-1].startswith("<!--"):
            return "\n".join(lines[:-1]).rstrip("\n") + "\n", {"sha": m.group(1), "parts": dict(x.split(":") for x in m.group(2).split(",") if x)}
    elif kind == "yaml":
        first, _, rest = text.partition("\n")
        m = MARK_RE.search(first)
        if m and first.startswith("#"):
            return rest, {"sha": m.group(1), "parts": dict(x.split(":") for x in m.group(2).split(",") if x)}
    elif kind == "json":
        try:
            data = json.loads(text)
        except ValueError:
            return text, None
        m = MARK_RE.search(str(data.pop("generated_by", "")) if isinstance(data, dict) else "")
        if m:
            return json.dumps(data, ensure_ascii=False, indent=2) + "\n", {"sha": m.group(1),
                                                                            "parts": dict(x.split(":") for x in m.group(2).split(",") if x)}
    return text, None


def with_marker(kind: str, body: str, parts: dict) -> str:
    ml = marker_line(body, parts)
    if kind == "md":
        return f"{body.rstrip(chr(10))}\n<!-- {ml} -->\n"
    if kind == "yaml":
        return f"# {ml}\n{body}"
    data = json.loads(body)
    data["generated_by"] = ml
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def tpl(name: str) -> str:
    return read_text(TEMPLATES / name)


def fill(template: str, **kw) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(kw.get(m.group(1), m.group(0))), template)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"


def q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def code(s: str) -> str:
    return f"`{s}`"


def render_agents_md(f: dict) -> tuple[str, dict]:
    h, ents, al = f["human"], f["entrypoints"], f["allowed"]
    scope = h.get("scope") or "TODO(human): one sentence"
    b = []
    dom_e = [e for e in ents if e["alias"].count("/") == 1]
    sh_e = [e for e in ents if e["alias"].count("/") > 1]
    if dom_e:
        b.append("- Entrypoint: " + ", ".join(code(e["alias"]) for e in dom_e) + ("; shared entrypoint: " + ", ".join(code(e["alias"]) for e in sh_e) if sh_e else "") + ".")
    elif sh_e:
        b.append("- Entrypoints: " + ", ".join(code(e["alias"]) for e in sh_e) + ".")
    else:
        b.append(f"- Code lives in {code(f['root'] + '/')}; no tsconfig path alias points into it.")
    if al["known"]:
        parts = []
        if al["tags"]:
            parts.append("libs tagged " + ", ".join(code(t) for t in al["tags"]))
        if al["allow_entrypoints"]:
            parts.append("these entrypoints of other domains: " + ", ".join(code(a) for a in al["allow_entrypoints"]))
        b.append("- Allowed imports (module-boundary rules): " + "; ".join(parts or ["only its own libs"]) + ".")
    else:
        b.append("- No module-boundary rule found for this domain; treat every import of another domain as a boundary change.")
    if f["imports"]:
        b.append("- Imports of other domains today: " + ", ".join(
            f"{code(i['spec'])} ({i['files']} file{'s' if i['files'] != 1 else ''})" for i in f["imports"]) + ".")
    else:
        b.append("- No import of another domain today.")
    if f["violations"]:
        b.append("- Already outside the allowed set (do not copy, do not extend): " + ", ".join(code(v["spec"]) for v in f["violations"]) + ".")
    b.append("- Do not add a new cross-domain import or boundary exception. Report the need to the dispatcher instead.")
    rules = []
    if f["signals"]["generated"]:
        regen = f["commands"].get("generate") or []
        rules.append("- Never edit generated code (" + ", ".join(code(g) for g in f["signals"]["generated"][:4]) + ")."
                     + (" Regenerate with " + ", ".join(code(c) for c in regen) + "." if regen else " Find the generator in the project's README before changing it."))
    elif f["commands"].get("generate"):
        rules.append("- Generated code is never edited by hand. Regenerate with " + ", ".join(code(c) for c in f["commands"]["generate"]) + ".")
    if f["signals"]["flags"]:
        rules.append("- Feature flags live in " + ", ".join(code(x) for x in f["signals"]["flags"][:3]) + "; new user-facing code ships behind a flag [to confirm].")
    cmds = []
    c = f["commands"]
    if c.get("test"):
        cmds.append(f"- Tests: {code(c['test'])}." + (f" Single file: {code(c['test_file'])}." if c.get("test_file") else ""))
    if c.get("lint"):
        cmds.append(f"- Lint: {code(c['lint'])}.")
    docs = [d for d in f["signals"]["docs"]]
    parts_ = {"scope": [scope], "boundaries": [f["entrypoints"], al, f["imports"], f["violations"]],
              "rules": [f["signals"]["generated"], f["signals"]["flags"], c.get("generate")],
              "commands": [c], "docs": docs}
    text = fill(tpl("AGENTS.md.tmpl"), name=f["name"], scope=scope, boundaries="\n".join(b))
    if rules:
        text += "\n## Rules\n" + "\n".join(rules) + "\n"
    if cmds:
        text += "\n## Commands\n" + "\n".join(cmds) + "\n"
    if docs:
        text += "\n## Humans' docs\n" + ", ".join(code(d) for d in docs) + "\n"
    if f["human"].get("owner") or f["signals"]["owners"]:
        text += "\nOwners: " + ", ".join(([f["human"]["owner"]] if f["human"].get("owner") else []) + f["signals"]["owners"]) + "\n"
    return text, parts_


def installed_skills(root: Path) -> set[str]:
    d = root / ".claude" / "skills"
    return {p.name for p in d.iterdir() if p.is_dir()} if d.is_dir() else set()


def core_version(root: Path, given: str | None) -> str:
    if given:
        return given
    for base in [root, *Path(__file__).resolve().parents]:
        v = base / ".tf" / "factory" / "VERSION"
        if v.is_file():
            return read_text(v).strip()
    raise SystemExit("domain_scan: factory VERSION not found (.tf/factory/VERSION); pass --core-version X.Y.Z")


def render_persona(f: dict, stack: list[str], installed: set[str], ids: dict) -> tuple[str, dict]:
    role = "frontend" if any(s in stack for s in ("fw-angular", "fw-react", "fw-nextjs")) else "backend"
    skills = [s for s in stack if s in installed] + [s for s in ("core-git-workflow", "core-conventional-commits")]
    c, al, sig, root = f["commands"], f["allowed"], f["signals"], f["root"]
    habits = [f"Read `{root}/AGENTS.md` before changing anything; it has this domain's boundaries and commands.",
              f"Edit only `{root}/**`; read other domains and shared libs, but do not edit them without the human's approval.",
              "Import other projects only through their public entrypoints. A new cross-domain import or boundary exception: stop and report it to the dispatcher."]
    if sig["generated"] or c.get("generate"):
        habits.append("Generated code is never edited by hand" + (": regenerate with " + ", ".join(f"`{x}`" for x in c.get("generate", [])) if c.get("generate") else "")
                      + "; commands that need credentials: ask the human to run them.")
    if sig["flags"]:
        habits.append(f"New user-facing code goes behind a feature flag (look in `{sig['flags'][0]}`) [to confirm the rule with the owners].")
    if c.get("test"):
        habits.append(f"Test first, then code. Tests: `{c['test']}`" + (f"; one file: `{c['test_file']}`" if c.get("test_file") else "") + ".")
    habits.append("Call MCP tools (Jira, Figma, Confluence) through the `mcp-runner` agent. A Figma link in the ticket: ask it to save the design context to `.tf/cache/mcp/` and treat the result as a pattern to adapt, not final code; if MCP is unavailable, say so in the report and do not guess the look.")
    habits.append("Commits: type(KEY-123): subject, in English (core-conventional-commits).")
    scope = f["human"].get("scope") or f"the code in {root}"
    name = ids["slug"][f["name"]]
    body = fill(tpl("persona-domain.yaml.tmpl"), name=name, title=q(f"{f['name']} - domain agent ({role})"),
                description=q(f"Domain agent for {f['name']} ({root}). Run `claude --agent {name}`."),
                identity="\n".join("  " + l for l in (f"You are responsible for the {f['name']} domain of this monorepo ({scope}). You change code only in {root}; you read other domains and libs, but do not edit them without the human's approval. Before anything else you read {root}/AGENTS.md.").splitlines()),
                role=role, skills=json.dumps(skills), habits="\n".join("  - " + h for h in habits),
                priorities=json.dumps(["domain boundaries and dependencies", "tests first", "cost", "speed of delivery"]),
                scenarios="\n".join([
                    "  - " + json.dumps({"situation": "the task needs code from another domain", "behavior": "you stop, name the symbol and its owner, and report it to the dispatcher instead of importing it"}, ensure_ascii=False),
                    "  - " + json.dumps({"situation": "the file to change is generated code", "behavior": "you do not edit it; you change the source or regenerate it with the project's command"}, ensure_ascii=False)]))
    return body, {"identity": [root, scope], "commands": [c], "boundaries": [f["allowed"], f["entrypoints"]], "stack": [skills, role]}


def render_dispatcher(facts: dict, ids: dict, role_of: dict) -> tuple[str, dict]:
    pid = ids["dispatcher"]
    agents = [f"{ids['slug'][n]}-{role_of[n]}" for n in facts]
    habits = [f"Start with the skill {ids['prefix']}domain-routing: assign the task to domains and confirm it with `grep` in the domain roots.",
              "A task in one domain goes to one agent; do not assemble a team for a small change.",
              "Several domains: the one that exposes a new shared entrypoint goes first; independent assignments run in parallel, in one message. Put the first result (export path, symbol, signature) into the next brief.",
              "A new cross-domain import, a new boundary exception or a new shared export: stop and ask the human with the consequences; do not edit the module-boundary rules.",
              "MCP calls (Jira, Figma) go through the `mcp-runner` agent; pass Figma links from the ticket on to the domain agent in the brief.",
              "Brief to a domain agent: ticket key, goal, acceptance criteria, scope `<domain root>/**`, data from the previous domain, tests first, the domain's test command.",
              "Final report: which domains, who did what, test and lint results, open questions. One PR through the tf skill; commit and PR only when the human asks."]
    body = fill(tpl("persona-dispatcher.yaml.tmpl"), name=pid, title=q(f"{pid} - domain dispatcher"),
                description=q(f"Dispatcher of the {pid} domains: finds the domains of a task and assigns it to the domain agents. Run `claude --agent {pid}`."),
                domains=", ".join(facts), agents=", ".join(agents),
                skills=json.dumps([f"{ids['prefix']}domain-routing", "core-plan-interview", "core-git-workflow", "core-conventional-commits"]),
                extra_agents=json.dumps(agents), habits="\n".join("  - " + h for h in habits),
                scenarios="\n".join("  - " + json.dumps(s, ensure_ascii=False) for s in [
                    {"situation": "the task touches one domain", "behavior": "you assign it to that domain's agent only"},
                    {"situation": "the task touches two domains", "behavior": "you decide which exposes a shared entrypoint, run it first and pass its result to the second"},
                    {"situation": "the task needs a new cross-domain import", "behavior": "you stop and ask the human about the consequences; you do not change the boundary rules"}]))
    return body, {"domains": [{n: f["root"]} for n, f in facts.items()], "agents": agents}


def render_routing_skill(facts: dict, ids: dict, role_of: dict, today: datetime.date) -> tuple[str, dict]:
    rows, order_hint = [], []
    for n, f in facts.items():
        ents = ", ".join(code(e["alias"]) for e in f["entrypoints"]) or "-"
        al = f["allowed"]
        imp = ", ".join(al["domains"] + [a for a in al["allow_entrypoints"]]) or ("own libs" if al["known"] else "unknown")
        c = f["commands"].get("test", "-")
        rows.append(f"| {n} | `{ids['slug'][n]}-{role_of[n]}` | `{f['root']}` | {ents} | {imp} | `{c}` |" if c != "-" else
                    f"| {n} | `{ids['slug'][n]}-{role_of[n]}` | `{f['root']}` | {ents} | {imp} | - |")
    consumers = sorted({i["to"] for f in facts.values() for i in f["imports"]})
    viol = [(n, v) for n, f in facts.items() for v in f["violations"]]
    names = list(facts)
    text = fill(tpl("routing-skill.md.tmpl"), skill=f"{ids['prefix']}domain-routing", prefix=ids["prefix"], review=str((today + datetime.timedelta(days=180)).isoformat()),
                names=", ".join(names), rows="\n".join(rows), today=str(today),
                consumed=(", ".join(code(c) for c in consumers) if consumers else "none yet"),
                violations=("\n".join(f"- {n} imports `{v['spec']}` ({v['files']} files) although the boundary rules do not allow it." for n, v in viol)
                            if viol else "- None found by the scan."),
                keywords=", ".join(names))
    return text, {"table": rows, "imports": consumers, "violations": [[n, v["spec"]] for n, v in viol]}


def render_evals(facts: dict, ids: dict) -> tuple[str, dict]:
    names = list(facts)
    a, b = names[0], names[1] if len(names) > 1 else names[0]
    sk = f"{ids['prefix']}domain-routing"
    data = {"skill": sk, "scenarios": [
        {"id": "one-domain", "expect": "trigger",
         "prompt": f"A ticket asks for a change inside the {a} domain only. Which agent should I run and what is its scope?",
         "checks": {"all": [[re.escape(a)], [re.escape(f"{ids['slug'][a]}-")]]}},
        {"id": "two-domains", "expect": "trigger",
         "prompt": f"A ticket touches both the {a} and the {b} domains. In which order do I assign the work and what do I pass between the agents?",
         "checks": {"all": [[re.escape(a)], [re.escape(b)], ["shared|entrypoint"]]}},
        {"id": "neighbor-claude-md", "expect": "no-trigger",
         "prompt": "Our root CLAUDE.md has grown to 400 lines; help me shorten it and decide which rules to drop.",
         "neighbor": "core-agent-instructions"}]}
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n", {"scenarios": [s["id"] for s in data["scenarios"]], "names": names}


def render_pack_yaml(facts: dict, ids: dict, role_of: dict, cver: str, project: str) -> tuple[str, dict]:
    major = int(cver.split(".")[0])
    names = list(facts)
    routing = (f"  | a change in the domain {', '.join(names[:-1]) + ' or ' + names[-1] if len(names) > 1 else names[0]} | the domain's agent (`claude --agent <domain>`) | std |\n"
               f"  | a ticket with unknown or several domains | the dispatcher `claude --agent {ids['dispatcher']}` (assigns to the domain agents) | std |")
    text = fill(tpl("pack.yaml.tmpl"), id=f"pack-{ids['project']}", project=project, title=q(project.upper() if len(project) < 6 else project.title()),
                description=q(f"Domain agents ({', '.join(names)}) and the routing skill for the {project} monorepo; generated by eng-domain-agents."),
                lo=f"{major}.0.0", hi=f"{major + 2}.0.0", prefix=ids["prefix"], question=q(f"how this repository's domains ({', '.join(names)}) are assigned and where their boundaries are"),
                routing=routing)
    return text, {"names": names, "core": [major]}


def render_readme(facts: dict, ids: dict, pack_dir: str) -> tuple[str, dict]:
    names = list(facts)
    text = fill(tpl("README.md.tmpl"), project=ids["project"], pack=f"pack-{ids['project']}", pack_dir=pack_dir,
                names=", ".join(names), dispatcher=ids["dispatcher"])
    return text, {"names": names}


# ---------------------------------------------------------------- plan / write / check

def build_plan(root: Path, result: dict, pack_dir: str, project_id: str | None, core_ver: str | None) -> dict:
    facts = result["best"]["domains"]
    ids = {"project": slug(project_id or root.name)}
    ids["prefix"] = ids["project"] + "-"
    ids["slug"] = {n: slug(n) for n in facts}
    ids["dispatcher"] = ids["project"] if ids["project"] not in ids["slug"].values() else ids["project"] + "-domains"
    installed = installed_skills(root)
    stack = result.get("stack", [])
    items: list[dict] = []
    advice = []
    role_of = {}
    for n, f in facts.items():
        if not (root / f["root"]).is_dir():
            advice.append(f"domain {n}: directory {f['root']} does not exist, skipped")
            continue
        t, parts = render_agents_md(f)
        items.append({"path": f"{f['root']}/AGENTS.md", "kind": "md", "body": t, "parts": parts, "domain": n})
        items.append({"path": f"{f['root']}/CLAUDE.md", "kind": "claude", "body": "@AGENTS.md\n", "parts": {}, "domain": n})
    live = {n: f for n, f in facts.items() if (root / f["root"]).is_dir()}
    pack_base = pack_dir.rstrip("/") + f"/pack-{ids['project']}"
    if live:
        for n, f in live.items():
            body, parts = render_persona(f, stack, installed, ids)
            role_of[n] = "frontend" if any(s in stack for s in ("fw-angular", "fw-react", "fw-nextjs")) else "backend"
            items.append({"path": f"{pack_base}/personas/{ids['slug'][n]}.yaml", "kind": "yaml", "body": body, "parts": parts, "domain": n})
        today = datetime.date.today()
        gens = [("personas/" + ids["dispatcher"] + ".yaml", "yaml", render_dispatcher(live, ids, role_of)),
                (f"skills/{ids['prefix']}domain-routing/SKILL.md", "md", render_routing_skill(live, ids, role_of, today)),
                (f"tests/skill_evals/{ids['prefix']}domain-routing.json", "json", render_evals(live, ids)),
                ("pack.yaml", "yaml", render_pack_yaml(live, ids, role_of, core_version(root, core_ver), ids["project"])),
                ("README.md", "md", render_readme(live, ids, pack_dir))]
        for rel, kind, (body, parts) in gens:
            items.append({"path": f"{pack_base}/{rel}", "kind": kind, "body": body, "parts": parts, "domain": None})
    return {"items": items, "advice": advice, "ids": ids, "live": list(live)}


def classify(root: Path, it: dict) -> dict:
    path = root / it["path"]
    out = {"path": it["path"], "state": "new", "reason": "", "write": None, "new_file": None, "drift": False}
    if it["kind"] == "claude":
        if not path.is_file():
            out.update(state="new", write=it["body"], drift=True, reason="CLAUDE.md with the import")
        elif any(l.strip() == "@AGENTS.md" for l in read_text(path).splitlines()):
            out["state"] = "unchanged"
        else:
            out.update(state="kept", reason="existing CLAUDE.md has no import: add the line `@AGENTS.md` yourself (not modified)")
        return out
    full = with_marker(it["kind"], it["body"], it["parts"])
    out["write"] = full
    if not path.is_file():
        out.update(state="new", drift=True, reason=f"new domain {it['domain']}" if it["domain"] and it["kind"] == "md" else "new file")
        return out
    existing = read_text(path)
    body, mk = parse_marker(it["kind"], existing)
    if mk and sha(body) == mk["sha"]:
        if sha(body) == sha(parse_marker(it["kind"], full)[0]) and mk["parts"] == {k: part_hash(v) for k, v in it["parts"].items()}:
            out["state"] = "unchanged"
        else:
            diff = sorted(k for k in set(mk["parts"]) | set(it["parts"]) if mk["parts"].get(k) != (part_hash(it["parts"][k]) if k in it["parts"] else None))
            out.update(state="changed", drift=True, reason="changed: " + (", ".join(diff) or "text"))
        return out
    if existing.replace("\r\n", "\n") == full:
        out["state"] = "unchanged"
        return out
    diff = sorted(k for k in it["parts"] if (mk or {}).get("parts", {}).get(k) != part_hash(it["parts"][k])) if mk else []
    drift = bool(mk) and bool(diff)
    out.update(state="kept", drift=drift, new_file=it["path"] + ".tf-new",
               reason=("edited by a human; facts changed: " + ", ".join(diff) if drift else "edited by a human") + "; new version in " + posixpath.basename(it["path"]) + ".tf-new")
    return out


def orphans(root: Path, plan: dict, files: list[str], pack_dir: str) -> list[str]:
    own = {i["path"] for i in plan["items"]}
    out = []
    pack_base = pack_dir.rstrip("/") + f"/pack-{plan['ids']['project']}"
    for f in files:
        if f in own:
            continue
        if posixpath.basename(f) == "AGENTS.md" and MARK in read_text(root / f)[-400:]:
            out.append(f"removed domain: {f} was generated, but its directory is no longer a domain")
    pdir = root / pack_base / "personas"
    if pdir.is_dir():
        for p in sorted(pdir.glob("*.yaml")):
            rel = posix(p.relative_to(root))
            if rel not in own and MARK in read_text(p)[:200]:
                out.append(f"removed domain: {rel} was generated for a domain that is gone")
    return out


def run_plan(args, write: bool) -> tuple[int, dict]:
    root = Path(args.root).resolve()
    result = scan(root)
    if result["confidence"] != "high" or not result["best"]:
        return 1, {"error": "layout not confirmed: ask the human and write .tf/config/domains.yaml", "scan": result}
    plan = build_plan(root, result, args.pack_dir, args.project_id, args.core_version)
    rows = [classify(root, it) for it in plan["items"]]
    orph = orphans(root, plan, list_files(root) if True else [], args.pack_dir)
    if write:
        for r in rows:
            p = root / r["path"]
            if r["state"] in ("new", "changed") and r["write"] is not None:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(r["write"].encode("utf-8"))
            elif r["state"] == "kept" and r["new_file"]:
                nf = root / r["new_file"]
                it = next(i for i in plan["items"] if i["path"] == r["path"])
                nf.write_bytes(with_marker(it["kind"], it["body"], it["parts"]).encode("utf-8"))
    for r in rows:
        r.pop("write", None)
    advice = plan["advice"] + [f"{r['path']}: {r['reason']}" for r in rows if r["state"] == "kept" and r["path"].endswith("CLAUDE.md")]
    drift = any(r["drift"] for r in rows) or bool(orph)
    return 0, {"files": rows, "orphans": orph, "advice": advice, "drift": drift, "domains": plan["live"],
               "ids": {k: v for k, v in plan["ids"].items() if k != "slug"}}


def show_plan(res: dict, verb: str) -> None:
    for r in res["files"]:
        print(f"{r['state']:<10} {r['path']}" + (f"  ({r['reason']})" if r["reason"] else ""))
    for o in res["orphans"]:
        print(f"orphan     {o}")
    for a in res["advice"]:
        print(f"advice     {a}")
    n = {s: sum(1 for r in res["files"] if r["state"] == s) for s in ("new", "changed", "kept", "unchanged")}
    print(f"{verb}: " + ", ".join(f"{v} {k}" for k, v in n.items() if v) + (f", {len(res['orphans'])} orphan(s)" if res["orphans"] else ""))


def show_scan(res: dict) -> None:
    b = res["best"]
    if not b:
        print("No domain layout found. " + "; ".join(res["notes"]))
        return
    print(f"Layout: {b['kind']}  glob: {b['glob'] or '-'}  confidence: {res['confidence']}  source: {res['source']}"
          + (f"  score: {b['score']}" if b["score"] is not None else ""))
    for e in b["evidence"]:
        print(f"  evidence: {e}")
    for n, d in b["domains"].items():
        print(f"- {n}: {d['root']}  projects: {', '.join(d['projects']) or '-'}")
        print(f"    entrypoints: {', '.join(e['alias'] for e in d['entrypoints']) or '-'}")
        al = d["allowed"]
        print(f"    allowed: " + (f"tags {al['tags']}, domains {al['domains']}, allow {al['allow_entrypoints']}" if al["known"] else "unknown (no boundary rule)"))
        imps = ", ".join("{}: {} x{}".format(i["to"], i["spec"], i["files"]) for i in d["imports"])
        print(f"    imports: {imps or '-'}")
        if d["violations"]:
            print(f"    OUTSIDE boundaries: {', '.join(v['spec'] for v in d['violations'])}")
        print(f"    commands: {d['commands'].get('test', '-')} | {d['commands'].get('lint', '-')}")
    if res["alternatives"]:
        print("Alternatives:")
        for a in res["alternatives"]:
            print(f"  {a['glob']} ({a['kind']}, score {a['score']}): {', '.join(a['domains'])}")
    for n in res["notes"]:
        print(f"note: {n}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Detect the domain layout of a monorepo and generate domain agents.")
    ap.add_argument("cmd", choices=["scan", "plan", "write", "check"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--pack-dir", default="tools/tf-pack")
    ap.add_argument("--project-id")
    ap.add_argument("--core-version")
    args = ap.parse_args(argv)
    if not Path(args.root).is_dir():
        print(f"domain_scan: no such directory: {args.root}", file=sys.stderr)
        return 2
    try:
        if args.cmd == "scan":
            res = scan(Path(args.root).resolve())
            print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else "", end="" if args.json else "")
            if args.json:
                print()
            else:
                show_scan(res)
            return 0 if res["confidence"] == "high" else 1
        code_, res = run_plan(args, write=args.cmd == "write")
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            return 2
        raise
    if code_:
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(res["error"])
            show_scan(res["scan"])
        return code_
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        show_plan(res, {"plan": "plan", "write": "written", "check": "check"}[args.cmd])
    if args.cmd == "check":
        return 1 if res["drift"] else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
