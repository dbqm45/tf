#!/usr/bin/env python3
"""System diff: what a change touches beyond code lines.

  python3 .tf/factory/system_diff.py                 # diff against origin/main (or main/master)
  python3 .tf/factory/system_diff.py --base develop
  python3 .tf/factory/system_diff.py --md            # section for the PR description
  python3 .tf/factory/system_diff.py --json
  tf diff [options]

Deterministic, no model, no network: the `base...HEAD` diff (names, status, changed lines and the files at both revisions)
→ per category what changed; only categories with changes appear:
- Behavior: changed source files (count, top directories), new and removed modules, tests (files and test counts);
- User interface: components, templates, styles, translation files (added and removed keys of JSON);
- Data: migrations and schema, with destructive SQL (DROP, TRUNCATE) flagged;
- API contract: OpenAPI/GraphQL/proto, controllers and routes, added and removed paths of an OpenAPI file;
- Dependencies: added, removed and changed packages of the manifests (package.json, requirements, pyproject, pom,
  gradle, csproj, go.mod), lockfile-only changes as one line;
- Configuration: configuration files, new environment variables of `.env.example`, feature flags of the operations card;
- Operations: CI, Dockerfile, compose, Kubernetes/Helm, Terraform, deploy scripts;
- Documentation: the number of files (and ADRs).
Informative: exit code 0; 2 on a call error (no git, unknown base). Patterns: `system_diff` in
`.tf/factory/config.yaml`, overrides in `.tf/config/config.yaml`.
"""
from __future__ import annotations

import os
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) does not know "→", "…" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes also write and read UTF-8

sys.dont_write_bytecode = True   # the engine in .tf/factory/ without __pycache__ (like node_modules — code only)
import argparse
import importlib.util
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD = Path(".tf") / "config" / "operations.json"
CAP = 5                       # sub-items per category in Markdown
ORDER = ("tests", "deps", "data", "api", "ops", "ui", "config", "docs")   # a file belongs to the first matching category
LABELS = {"behavior": "Behavior", "ui": "User interface", "data": "Data", "api": "API contract",
          "deps": "Dependencies", "config": "Configuration", "ops": "Operations", "docs": "Documentation"}
TEST_LINE = re.compile(r"^\s*(?:async\s+)?def test_\w*|^\s*(?:it|test)(?:\.\w+)?\s*\(|^\s*@Test\b|^\s*func Test\w+|"
                       r"^\s*\[(?:Fact|Test|Theory)\b")
DESTRUCTIVE = [
    (re.compile(r"\bDROP\s+(TABLE|COLUMN|DATABASE|SCHEMA|INDEX|CONSTRAINT|VIEW)\b", re.I), lambda m: "DROP " + m.group(1).upper()),
    (re.compile(r"\bTRUNCATE\b", re.I), lambda m: "TRUNCATE"),
    (re.compile(r"\bALTER\s+TABLE\b.*\bDROP\b", re.I), lambda m: "ALTER … DROP"),
    (re.compile(r"\b(drop_table|drop_column|dropTable|dropColumn)\b"), lambda m: m.group(1)),
]


def _packs():
    spec = importlib.util.spec_from_file_location("tf_packs_sysdiff", HERE / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_rules(repo: Path) -> dict:
    """`system_diff` of the engine's config.yaml (next to the script), then the layers: company, team, project, person
    (a list replaces the engine's list)."""
    rules: dict = {}
    try:
        packs = _packs()
        rules = dict((packs.load_yaml(HERE / "config.yaml") or {}).get("system_diff") or {})
        for _label, data in packs.config_layers(repo):
            over = (data or {}).get("system_diff")
            if isinstance(over, dict):
                rules.update({k: v for k, v in over.items() if isinstance(v, list)})
    except Exception:  # noqa: BLE001 — without a readable configuration: the patterns found so far
        pass
    return rules


def _git(repo: Path, *args) -> str:
    r = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)}: exit code {r.returncode}")
    return r.stdout


def default_base(repo: Path) -> str:
    for ref in ("origin/main", "origin/master", "main", "master"):
        if subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "-q", ref], capture_output=True).returncode == 0:
            return ref
    return "HEAD~1"


def _show(repo: Path, ref: str, path: str | None) -> str | None:
    if not path:
        return None
    r = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    return r.stdout if r.returncode == 0 else None


def _any(patterns, path: str) -> bool:
    return any(re.search(p, path) for p in patterns or [])


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def _cap(items: list[str]) -> list[str]:
    return items if len(items) <= CAP else items[:CAP] + [f"… +{len(items) - CAP} more"]


def _code(text: str) -> str:
    return f"`{text}`"


# --- parsing of the files at two revisions -------------------------------------------------------------------------

def _json(text: str | None):
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def _flatten(obj, prefix="") -> set[str]:
    if isinstance(obj, dict):
        out: set[str] = set()
        for k, v in obj.items():
            out |= _flatten(v, f"{prefix}.{k}" if prefix else str(k))
        return out
    return {prefix} if prefix else set()


def _req_line(line: str) -> tuple[str, str] | None:
    line = line.split("#", 1)[0].split(";", 1)[0].strip()
    if not line or line.startswith("-"):
        return None
    m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*(.*)$", line)
    return (m.group(1).lower(), m.group(2).strip() or "*") if m else None


def _deps_package_json(text: str) -> dict:
    data = _json(text)
    if not isinstance(data, dict):
        return {}
    return {s: {k: str(v) for k, v in data[s].items()} for s in
            ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies") if isinstance(data.get(s), dict)}


def _deps_requirements(text: str) -> dict:
    return {"requirements": dict(filter(None, (_req_line(ln) for ln in text.splitlines())))}


def _deps_pyproject(text: str) -> dict:
    try:
        import tomllib
        data = tomllib.loads(text)
    except Exception:  # noqa: BLE001 — no tomllib (Python < 3.11) or a broken file: the file is only listed
        return {}
    out: dict = {}
    proj = data.get("project") or {}
    out["dependencies"] = dict(filter(None, (_req_line(x) for x in proj.get("dependencies") or [] if isinstance(x, str))))
    for grp, lst in (proj.get("optional-dependencies") or {}).items():
        out[f"optional:{grp}"] = dict(filter(None, (_req_line(x) for x in lst if isinstance(x, str))))
    for grp, lst in (data.get("dependency-groups") or {}).items():
        out[f"group:{grp}"] = dict(filter(None, (_req_line(x) for x in lst if isinstance(x, str))))
    poetry = (data.get("tool") or {}).get("poetry") or {}

    def pt(d):
        return {k: (v if isinstance(v, str) else str((v or {}).get("version", "*")) if isinstance(v, dict) else "*")
                for k, v in (d or {}).items() if k != "python"}
    if poetry.get("dependencies"):
        out["dependencies"] = {**out.get("dependencies", {}), **pt(poetry["dependencies"])}
    if poetry.get("dev-dependencies"):
        out["dev-dependencies"] = pt(poetry["dev-dependencies"])
    for grp, g in (poetry.get("group") or {}).items():
        out[f"group:{grp}"] = pt((g or {}).get("dependencies"))
    return {k: v for k, v in out.items() if v}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _deps_pom(text: str) -> dict:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {}
    out: dict = {}
    for dep in (e for e in root.iter() if _local(e.tag) == "dependency"):
        f = {_local(c.tag): (c.text or "").strip() for c in dep}
        if f.get("artifactId"):
            out.setdefault("test" if f.get("scope") == "test" else "dependencies", {})[
                f"{f.get('groupId', '')}:{f['artifactId']}"] = f.get("version") or "*"
    return out


def _deps_gradle(text: str) -> dict:
    out: dict = {}
    pat = re.compile(r"^\s*(\w+)\s*\(?\s*['\"]([^'\":\s]+):([^'\":\s]+)(?::([^'\"\s]+))?['\"]", re.M)
    for conf, grp, art, ver in pat.findall(text):
        out.setdefault("test" if conf.lower().startswith(("test", "androidtest")) else "dependencies", {})[
            f"{grp}:{art}"] = ver or "*"
    return out


def _deps_csproj(text: str) -> dict:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {}
    out: dict = {}
    for e in root.iter():
        if _local(e.tag) == "PackageReference" and e.get("Include"):
            ver = e.get("Version") or next((c.text for c in e if _local(c.tag) == "Version"), None) or "*"
            out.setdefault("dependencies", {})[e.get("Include")] = (ver or "*").strip()
    return out


def _deps_gomod(text: str) -> dict:
    out: dict = {}
    block = False
    for ln in text.splitlines():
        s = ln.split("//", 1)[0].strip()
        if s.startswith("require ("):
            block = True
            continue
        if block and s == ")":
            block = False
            continue
        m = re.match(r"^(?:require\s+)?([\w.\-/~]+\.[\w.\-/~]+)\s+(v[\w.\-+]+)$", s) if (block or s.startswith("require ")) else None
        if m:
            out[m.group(1)] = m.group(2)
    return {"require": out} if out else {}


def _parser(path: str):
    name = path.rsplit("/", 1)[-1]
    if name == "package.json":
        return _deps_package_json
    if re.match(r"requirements[^/]*\.txt$", name):
        return _deps_requirements
    if name == "pyproject.toml":
        return _deps_pyproject
    if name == "pom.xml":
        return _deps_pom
    if re.match(r"build\.gradle(\.kts)?$", name):
        return _deps_gradle
    if name.endswith(".csproj"):
        return _deps_csproj
    if name == "go.mod":
        return _deps_gomod
    return None


def _scope_diff(old: dict, new: dict) -> dict:
    return {"added": {k: v for k, v in new.items() if k not in old},
            "removed": {k: v for k, v in old.items() if k not in new},
            "changed": {k: [old[k], v] for k, v in new.items() if k in old and old[k] != v}}


def _openapi_paths(text: str | None, name: str) -> set[str] | None:
    if text is None:
        return set()
    if name.lower().endswith(".json"):
        data = _json(text)
        return set(data["paths"]) if isinstance(data, dict) and isinstance(data.get("paths"), dict) else None
    out, inside = set(), False   # a cheap look at YAML: the keys of the top-level `paths:` block
    for ln in text.splitlines():
        if re.match(r"^paths\s*:\s*$", ln):
            inside = True
        elif inside and re.match(r"^\S", ln) and not ln.startswith("#"):
            inside = False
        elif inside:
            m = re.match(r"^\s{1,4}['\"]?(/[^\s'\":]*)['\"]?\s*:\s*$", ln)
            if m:
                out.add(m.group(1))
    return out


def _flag_states(data: dict | None, envs: list[str], on) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for env in envs:
        if isinstance(data.get(env) if data else None, dict):
            for flag, v in data[env].items():
                if on(v) is not None:
                    out[f"{flag}@{env}"] = on(v)
    if data:
        for flag, d in data.items():
            if isinstance(d, dict) and flag not in envs:
                for env in envs:
                    if env in d and on(d[env]) is not None:
                        out[f"{flag}@{env}"] = on(d[env])
    return out


def _flags_diff(repo: Path, mb: str, changed: dict) -> dict | None:
    card = _json((repo / CARD).read_text(encoding="utf-8", errors="replace")) if (repo / CARD).is_file() else None
    flags = (card or {}).get("flags") if isinstance(card, dict) else None
    rel = (flags or {}).get("file") if isinstance(flags, dict) else None
    rel = rel.replace("\\", "/") if isinstance(rel, str) else None
    if not rel or rel not in changed:
        return None
    try:
        spec = importlib.util.spec_from_file_location("tf_flag_check_sysdiff", HERE / "flag_check.py")
        fc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fc)
    except Exception:  # noqa: BLE001
        return None
    envs = [e for e in (flags.get("envs") or []) if isinstance(e, str)]
    status, _old = changed[rel]
    old_text = None if status == "A" else _show(repo, mb, rel)
    new_text = None if status == "D" else _show(repo, "HEAD", rel)
    old = _flag_states(fc.parse(old_text, rel) if old_text else None, envs, fc.on)
    new = _flag_states(fc.parse(new_text, rel) if new_text else None, envs, fc.on)
    return {"file": rel, "added": sorted(k for k in new if k not in old), "removed": sorted(k for k in old if k not in new),
            "changed": sorted(f"{k} {'on' if old[k] else 'off'}→{'on' if new[k] else 'off'}" for k in new
                              if k in old and old[k] != new[k])}


# --- the diff -------------------------------------------------------------------------------------------------------

def _changed(repo: Path, mb: str) -> dict[str, tuple[str, str | None]]:
    """path in HEAD (or the deleted one) → (status A/M/D, the old path for the base revision)."""
    out: dict[str, tuple[str, str | None]] = {}
    for line in _git(repo, "diff", "--name-status", "-M", f"{mb}...HEAD").splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            out[parts[-1]] = (parts[0][0] if parts[0][0] != "R" else "M", parts[1] if parts[0][0] == "R" else parts[-1])
    return out


def _diff_lines(repo: Path, mb: str, wanted: set[str]) -> tuple[dict, dict]:
    """Added and removed lines (-U0) of the wanted files from a single `git diff`."""
    added: dict[str, list[str]] = {}
    removed: dict[str, list[str]] = {}
    cur = None
    for line in _git(repo, "diff", "-U0", "-M", "--no-color", f"{mb}...HEAD").splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/.* b/(.*)$", line)
            cur = m.group(1) if m and m.group(1) in wanted else None
        elif cur and line.startswith("+") and not line.startswith("+++"):
            added.setdefault(cur, []).append(line[1:])
        elif cur and line.startswith("-") and not line.startswith("---"):
            removed.setdefault(cur, []).append(line[1:])
    return added, removed


def _dirs(paths) -> set[str]:
    out: set[str] = set()
    for p in paths:
        parts = p.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            out.add("/".join(parts[:i]))
    return out


def _shallowest(dirs: set[str]) -> list[str]:
    return sorted(d for d in dirs if not any(d.startswith(o + "/") for o in dirs))


def _top_dir(path: str) -> str:
    parts = path.split("/")[:-1][:2]
    return "/".join(parts) + "/" if parts else "./"


def system_diff(repo: Path, base: str | None = None, rules: dict | None = None) -> dict:
    rules = rules if rules is not None else load_rules(repo)
    base = base or default_base(repo)
    _git(repo, "rev-parse", "--verify", "-q", f"{base}^{{commit}}")   # unknown base → RuntimeError
    try:
        mb = _git(repo, "merge-base", base, "HEAD").strip() or base
    except RuntimeError:
        mb = base
    changed = _changed(repo, mb)
    cats: dict[str, list[str]] = {c: [] for c in ORDER}
    source: list[str] = []
    for path in sorted(changed):
        for c in ORDER:
            if _any(rules.get(c), path):
                cats[c].append(path)
                break
        else:
            if _any(rules.get("source"), path):
                source.append(path)
    # the flag file of the operations card counts as configuration even outside `config/`
    flags = _flags_diff(repo, mb, changed)
    if flags and flags["file"] not in cats["config"]:
        for c in ORDER:
            if flags["file"] in cats[c]:
                cats[c].remove(flags["file"])
        cats["config"].append(flags["file"])
    needs = set(cats["tests"]) | set(cats["data"])
    added, removed = _diff_lines(repo, mb, needs) if needs else ({}, {})
    res: dict[str, dict] = {}

    # Behavior
    tests_added = [p for p in cats["tests"] if changed[p][0] == "A"]
    tests_removed = [p for p in cats["tests"] if changed[p][0] == "D"]
    tests_mod = [p for p in cats["tests"] if changed[p][0] == "M"]
    n_added = sum(bool(TEST_LINE.search(x)) for p in cats["tests"] for x in added.get(p, []))
    n_removed = sum(bool(TEST_LINE.search(x)) for p in cats["tests"] for x in removed.get(p, []))
    new_mod = removed_mod = []
    if source:
        base_dirs = _dirs(_git(repo, "ls-tree", "-r", "--name-only", mb).splitlines())
        head_dirs = _dirs(_git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
        new_mod = _shallowest({d for d in _dirs(p for p in source if changed[p][0] == "A") if d not in base_dirs})
        removed_mod = _shallowest({d for d in _dirs(p for p in source if changed[p][0] == "D") if d not in head_dirs})
    if source or cats["tests"]:
        tops: dict[str, int] = {}
        for p in source:
            tops[_top_dir(p)] = tops.get(_top_dir(p), 0) + 1
        res["behavior"] = {
            "source_files": len(source), "top_dirs": sorted(tops.items(), key=lambda kv: (-kv[1], kv[0]))[:3],
            "new_modules": [d + "/" for d in new_mod], "removed_modules": [d + "/" for d in removed_mod],
            "tests": {"files_added": len(tests_added), "files_removed": len(tests_removed), "files_modified": len(tests_mod),
                      "tests_added": n_added, "tests_removed": n_removed}}

    # User interface (with the keys of translation files)
    if cats["ui"]:
        i18n = []
        for p in cats["ui"]:
            if _any(rules.get("i18n"), p):
                st, old_path = changed[p]
                old = _flatten(_json(_show(repo, mb, old_path))) if st != "A" else set()
                new = _flatten(_json(_show(repo, "HEAD", p))) if st != "D" else set()
                i18n.append({"file": p, "keys_added": len(new - old), "keys_removed": len(old - new)})
        res["ui"] = {"files": list(cats["ui"]), "i18n": i18n}

    # Data (destructive SQL in added lines)
    if cats["data"]:
        destructive = []
        for p in cats["data"]:
            seen = set()
            for line in added.get(p, []):
                for rx, label in DESTRUCTIVE:
                    m = rx.search(line)
                    if m and label(m) not in seen:
                        seen.add(label(m))
                        destructive.append({"file": p, "match": label(m)})
                        break
        res["data"] = {"files": list(cats["data"]), "destructive": destructive}

    # API contract (paths of an OpenAPI file)
    if cats["api"]:
        paths = {}
        for p in cats["api"]:
            if re.search(r"(^|/)(openapi|swagger)[^/]*\.(json|ya?ml)$", p, re.I):
                st, old_path = changed[p]
                old = _openapi_paths(_show(repo, mb, old_path) if st != "A" else None, p)
                new = _openapi_paths(_show(repo, "HEAD", p) if st != "D" else None, p)
                if old is not None and new is not None and (old != new):
                    paths[p] = {"added": sorted(new - old), "removed": sorted(old - new)}
        res["api"] = {"files": list(cats["api"]), "paths": paths}

    # Dependencies
    if cats["deps"]:
        locks = [p for p in cats["deps"] if _any(rules.get("lockfiles"), p)]
        manifests = [p for p in cats["deps"] if p not in locks]
        entries = []
        for p in manifests:
            st, old_path = changed[p]
            parse = _parser(p)
            entry: dict = {"file": p, "scopes": {}}
            if parse is None:
                entry["unparsed"] = True
            else:
                old = parse(_show(repo, mb, old_path) or "") if st != "A" else {}
                new = parse(_show(repo, "HEAD", p) or "") if st != "D" else {}
                for scope in sorted(set(old) | set(new)):
                    d = _scope_diff(old.get(scope, {}), new.get(scope, {}))
                    if any(d.values()):
                        entry["scopes"][scope] = d
            entries.append(entry)
        res["deps"] = {"changes": entries, "lockfile_only": locks if not manifests else [], "lockfiles": locks}

    # Configuration
    if cats["config"]:
        env_added, env_removed = [], []
        for p in cats["config"]:
            if _any(rules.get("env_example"), p):
                st, old_path = changed[p]
                rx = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", re.M)
                old = set(rx.findall(_show(repo, mb, old_path) or "")) if st != "A" else set()
                new = set(rx.findall(_show(repo, "HEAD", p) or "")) if st != "D" else set()
                env_added += sorted(new - old)
                env_removed += sorted(old - new)
        res["config"] = {"files": list(cats["config"]), "env_added": env_added, "env_removed": env_removed, "flags": flags}

    if cats["ops"]:
        res["ops"] = {"files": list(cats["ops"])}
    if cats["docs"]:
        res["docs"] = {"files": list(cats["docs"]), "count": len(cats["docs"]),
                       "adr": sum(_any(rules.get("adr"), p) for p in cats["docs"])}
    order = list(LABELS)
    return {"base": base, "categories": {k: res[k] for k in order if k in res}}


# --- Markdown -------------------------------------------------------------------------------------------------------

def _file_items(files: list[str], status: dict | None = None) -> list[str]:
    return [_code(f) for f in files]


def _dep_items(entry: dict) -> str:
    if entry.get("unparsed"):
        return f"{_code(entry['file'])} (changed)"
    parts = []
    for scope, d in entry["scopes"].items():
        its = [f"+{_code(n)} {v}" for n, v in d["added"].items()] + [f"-{_code(n)}" for n in d["removed"]] \
            + [f"{_code(n)} {o}→{v}" for n, (o, v) in d["changed"].items()]
        parts.append(f"{scope}: " + ", ".join(_cap(its) if len(its) <= 8 else its[:8] + [f"… +{len(its) - 8} more"]))
    return f"{_code(entry['file'])}: " + "; ".join(parts) if parts else f"{_code(entry['file'])} (changed)"


def _items(key: str, c: dict) -> list[str]:
    if key == "behavior":
        out = []
        if c["source_files"]:
            tops = ", ".join(f"{_code(d)} {n}" for d, n in c["top_dirs"])
            out.append(f"{_plural(c['source_files'], 'source file')} ({tops})")
        out += [f"new module {_code(d)}" for d in c["new_modules"]] + [f"removed module {_code(d)}" for d in c["removed_modules"]]
        t = c["tests"]
        parts = []
        for n, sign, word in ((t["files_added"], "+", "file"), (t["files_removed"], "-", "file")):
            if n:
                parts.append(f"{sign}{_plural(n, word)}")
        if t["files_modified"]:
            parts.append(f"~{t['files_modified']} changed")
        for n, sign in ((t["tests_added"], "+"), (t["tests_removed"], "-")):
            if n:
                parts.append(f"{sign}{_plural(n, 'test')}")
        if parts:
            out.append("tests: " + ", ".join(parts))
        return out
    if key == "ui":
        i18n = {i["file"]: i for i in c["i18n"]}
        return [f"{_code(f)} (+{i18n[f]['keys_added']}/-{i18n[f]['keys_removed']} keys)" if f in i18n else _code(f)
                for f in c["files"]]
    if key == "data":
        return _file_items(c["files"]) + [f"destructive {_code(d['match'])} in {_code(d['file'])}" for d in c["destructive"]]
    if key == "api":
        out = []
        for f in c["files"]:
            p = c["paths"].get(f)
            ch = ([f"+{_code(x)}" for x in p["added"]] + [f"-{_code(x)}" for x in p["removed"]]) if p else []
            out.append(f"{_code(f)} ({', '.join(_cap(ch))})" if ch else _code(f))
        return out
    if key == "deps":
        out = [_dep_items(e) for e in c["changes"]]
        return out or [f"lockfile only: {', '.join(_code(p) for p in c['lockfile_only'])}"]
    if key == "config":
        out = _file_items(c["files"])
        if c["env_added"]:
            out.append("new variables " + ", ".join(_code(n) for n in c["env_added"]))
        if c["env_removed"]:
            out.append("removed variables " + ", ".join(_code(n) for n in c["env_removed"]))
        f = c.get("flags")
        if f and (f["added"] or f["removed"] or f["changed"]):
            out.append("flags " + ", ".join([f"+{_code(x)}" for x in f["added"]] + [f"-{_code(x)}" for x in f["removed"]]
                                            + [_code(x) for x in f["changed"]]))
        return out
    if key == "docs":
        return [f"{_plural(c['count'], 'file')}" + (f" ({c['adr']} ADR)" if c["adr"] else "")]
    return _file_items(c["files"])


def to_markdown(res: dict) -> str:
    lines = ["## System diff", ""]
    for key, c in res["categories"].items():
        lines.append(f"- **{LABELS[key]}**: " + "; ".join(_cap(_items(key, c))))
    if not res["categories"]:
        lines.append("- No changes against the base.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=None, help="base branch (default: origin/main, main or master)")
    ap.add_argument("--json", action="store_true", help="result as JSON")
    ap.add_argument("--md", action="store_true", help="section for the PR description (Markdown, the default)")
    args = ap.parse_args(argv)
    repo = Path.cwd()
    try:
        res = system_diff(repo, base=args.base)
    except (RuntimeError, OSError, subprocess.SubprocessError) as e:
        print(f"✗ System diff not possible: {e}", file=sys.stderr)
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=1) if args.json else to_markdown(res))
    return 0   # informative: exit code 0


if __name__ == "__main__":
    sys.exit(main())
