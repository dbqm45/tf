"""Stack, exact versions, repository layout and commands, read from manifests and lockfiles. No model, no network.

Every fact carries evidence `path:line` (relative to the repository root). A version comes from the lockfile when
there is one; the range declared in the manifest is kept next to it. Only technologies listed in
registry/detectors/*.yaml are reported (see that file for why).
"""
from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

import yaml

SKIP_DIRS = {".git", "node_modules", "dist", "build", "out", "target", "coverage", ".venv", "venv", "vendor",
             "__pycache__", ".next", ".nuxt", ".tf", ".claude", ".idea", ".gradle", "bin", "obj"}
MAX_DEPTH = 6
JS_LOCKS = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")
PY_LOCKS = ("uv.lock", "poetry.lock")


# ---------------------------------------------------------------- helpers

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _line_of(text: str, needle: str | re.Pattern, start: int = 0) -> int:
    """1-based line of the first match of `needle` at or after character `start`; 0 when absent."""
    if isinstance(needle, str):
        i = text.find(needle, start)
    else:
        m = needle.search(text, start)
        i = m.start() if m else -1
    return text.count("\n", 0, i) + 1 if i >= 0 else 0


def _ev(root: Path, path: Path, line: int) -> str:
    rel = path.relative_to(root).as_posix()
    return f"{rel}:{max(line, 1)}"


def _walk(root: Path, names: set[str], suffixes: tuple[str, ...] = ()) -> list[Path]:
    found = []

    def rec(d: Path, depth: int):
        try:
            entries = sorted(d.iterdir())
        except OSError:
            return
        for e in entries:
            if e.is_dir():
                if e.name not in SKIP_DIRS and not e.name.startswith(".") and depth < MAX_DEPTH:
                    rec(e, depth + 1)
            elif e.name in names or (suffixes and e.name.endswith(suffixes)):
                found.append(e)
    rec(root, 0)
    return found


def _nearest(start: Path, root: Path, names: tuple[str, ...]) -> Path | None:
    d = start
    while True:
        for n in names:
            if (d / n).is_file():
                return d / n
        if d == root or root not in d.parents:
            return None
        d = d.parent


def load_detectors(registry: Path) -> list[dict]:
    techs = []
    for f in sorted((registry / "detectors").glob("*.yaml")):
        techs += (yaml.safe_load(_read(f)) or {}).get("technologies", [])
    return techs


def _match(techs: list[dict], eco: str, name: str) -> dict | None:
    for t in techs:
        for pat in t.get("match", {}).get(eco, []):
            if name == pat or (pat.endswith("*") and fnmatch.fnmatchcase(name, pat)):
                return t
    return None


# ---------------------------------------------------------------- JavaScript

def _npm_lock(lock: Path, pkg_rel: str, name: str) -> tuple[str, str] | None:
    """(version, needle) for `name` as resolved for the workspace at `pkg_rel` in package-lock.json v2/v3."""
    data = json.loads(_read(lock) or "{}")
    pkgs = data.get("packages") or {}
    lock_rel = lock.parent
    keys = []
    if pkg_rel not in ("", "."):
        keys.append(f"{pkg_rel}/node_modules/{name}")
    keys.append(f"node_modules/{name}")
    for k in keys:
        if k in pkgs and pkgs[k].get("version"):
            return pkgs[k]["version"], f'"{k}"'
    deps = data.get("dependencies") or {}          # lockfile v1
    if name in deps and deps[name].get("version"):
        return deps[name]["version"], f'"{name}"'
    return None


def _pnpm_lock(lock: Path, pkg_rel: str, name: str) -> tuple[str, str] | None:
    data = yaml.safe_load(_read(lock) or "") or {}
    imp = (data.get("importers") or {}).get(pkg_rel or ".") or ({} if data.get("importers") else data)
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        entry = (imp.get(section) or {}).get(name)
        if entry is None:
            continue
        version = entry.get("version") if isinstance(entry, dict) else str(entry)
        version = re.split(r"[(_]", str(version))[0]
        if version.startswith("link:"):
            return None
        return version, f"{name}@{version}"
    return None


def _yarn_lock(lock: Path, name: str, spec: str) -> tuple[str, str] | None:
    text = _read(lock)
    for block in re.split(r"\n(?=\S)", text):
        head, _, body = block.partition("\n")
        specs = [s.strip().strip('"') for s in head.rstrip(":").split(",")]
        wanted = {f"{name}@{spec}", f"{name}@npm:{spec}"}
        if wanted & set(specs):
            m = re.search(r'^\s+version:?\s+"?([^"\s]+)"?', body, re.M)
            if m:
                return m.group(1), head.strip()
    return None


def _js(root: Path, techs: list[dict], facts: list, coverage: dict):
    manifests = _walk(root, {"package.json"})
    workspaces = []
    for mf in manifests:
        text = _read(mf)
        try:
            pkg = json.loads(text)
        except json.JSONDecodeError:
            coverage["skipped"].append({"source": mf.relative_to(root).as_posix(), "reason": "invalid JSON"})
            continue
        pkg_dir = mf.parent
        rel_dir = pkg_dir.relative_to(root).as_posix()
        if rel_dir != ".":
            workspaces.append(rel_dir)
        lock = _nearest(pkg_dir, root, JS_LOCKS)
        coverage["read"].append(mf.relative_to(root).as_posix())
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            for name, spec in (pkg.get(section) or {}).items():
                tech = _match(techs, "npm", name)
                if not tech or (section == "peerDependencies" and name in (pkg.get("devDependencies") or {})):
                    continue
                declared_line = _line_of(text, f'"{name}"', text.find(f'"{section}"'))
                version, evidence = None, [_ev(root, mf, declared_line)]
                if lock is not None:
                    pkg_rel = pkg_dir.relative_to(lock.parent).as_posix()
                    pkg_rel = "" if pkg_rel == "." else pkg_rel
                    hit = None
                    if lock.name == "package-lock.json":
                        hit = _npm_lock(lock, pkg_rel, name)
                    elif lock.name == "pnpm-lock.yaml":
                        hit = _pnpm_lock(lock, pkg_rel, name)
                    elif lock.name == "yarn.lock":
                        hit = _yarn_lock(lock, name, str(spec))
                    if hit:
                        version = hit[0]
                        evidence.insert(0, _ev(root, lock, _line_of(_read(lock), hit[1])))
                _stack_fact(facts, tech, "npm", name, version, str(spec), rel_dir, evidence,
                            "lockfile" if version else "manifest-range")
        _js_commands(root, mf, text, pkg, lock, facts)
        engines = (pkg.get("engines") or {}).get("node")
        if engines:
            _add(facts, {"id": f"F-RUNTIME-node-{_slug(rel_dir)}", "kind": "fact", "title": f"Node.js {engines}",
                         "data": {"topic": "runtime", "tech": "node", "declared": engines, "package_dir": rel_dir},
                         "evidence": [_ev(root, mf, _line_of(text, '"node"', text.find('"engines"')))]})
    nvmrc = root / ".nvmrc"
    if nvmrc.is_file() and _read(nvmrc).strip():
        v = _read(nvmrc).strip()
        _add(facts, {"id": "F-RUNTIME-node-nvmrc", "kind": "fact", "title": f"Node.js {v}",
                     "data": {"topic": "runtime", "tech": "node", "version": v.lstrip("v")},
                     "evidence": [_ev(root, nvmrc, 1)]})
    return workspaces


def _js_commands(root: Path, mf: Path, text: str, pkg: dict, lock: Path | None, facts: list):
    if mf.parent != root:
        return
    runner = {"pnpm-lock.yaml": "pnpm", "yarn.lock": "yarn"}.get(lock.name if lock else "", "npm")
    scripts = pkg.get("scripts") or {}
    kinds = {"test": ["test"], "lint": ["lint"], "build": ["build"], "typecheck": ["typecheck", "type-check", "tsc"],
             "format": ["format", "fmt"]}
    for kind, names in kinds.items():
        for n in names:
            if n in scripts:
                cmd = f"{runner} test" if n == "test" and runner != "yarn" else f"{runner} run {n}"
                _add(facts, {"id": f"F-CMD-{kind}", "kind": "fact", "title": f"{kind}: {cmd}",
                             "data": {"topic": "command", "command_kind": kind, "command": cmd,
                                      "script": scripts[n]},
                             "evidence": [_ev(root, mf, _line_of(text, f'"{n}"', text.find('"scripts"')))]})
                break


# ---------------------------------------------------------------- Python

def _py_lock_versions(lock: Path) -> dict[str, tuple[str, int]]:
    text = _read(lock)
    out = {}
    for m in re.finditer(r'^\[\[package\]\]\s*\nname\s*=\s*"([^"]+)"\s*\nversion\s*=\s*"([^"]+)"', text, re.M):
        out[_pyname(m.group(1))] = (m.group(2), text.count("\n", 0, m.start()) + 2)
    return out


def _pyname(n: str) -> str:
    return re.sub(r"[-_.]+", "-", n).lower()


def _python(root: Path, techs: list[dict], facts: list, coverage: dict):
    for mf in _walk(root, {"pyproject.toml"}) + _walk(root, set(), ("requirements.txt",)):
        text = _read(mf)
        coverage["read"].append(mf.relative_to(root).as_posix())
        rel_dir = mf.parent.relative_to(root).as_posix()
        lock = _nearest(mf.parent, root, PY_LOCKS)
        locked = _py_lock_versions(lock) if lock else {}
        names = set()
        for m in re.finditer(r'^\s*"?([A-Za-z0-9][A-Za-z0-9_.-]*)\s*(\[[^\]]*\])?\s*(==|>=|~=|<|\^|=|")', text, re.M):
            names.add(m.group(1))
        for raw in sorted(names):
            tech = _match(techs, "pypi", _pyname(raw))
            if not tech:
                continue
            decl_line = _line_of(text, re.compile(rf'^\s*"?{re.escape(raw)}\b', re.M | re.I))
            evidence = [_ev(root, mf, decl_line)]
            version, how = None, "manifest-range"
            if _pyname(raw) in locked:
                version, line = locked[_pyname(raw)]
                evidence.insert(0, _ev(root, lock, line))
                how = "lockfile"
            else:
                pin = re.search(rf'^\s*{re.escape(raw)}\s*(?:\[[^\]]*\])?\s*==\s*([\w.]+)', text, re.M | re.I)
                if pin:
                    version, how = pin.group(1), "pinned"
            line = text.splitlines()[decl_line - 1] if decl_line else ""
            _stack_fact(facts, tech, "pypi", _pyname(raw), version, line.strip().strip('",'), rel_dir, evidence, how)
        rp = re.search(r'requires-python\s*=\s*"([^"]+)"', text)
        if rp:
            _add(facts, {"id": f"F-RUNTIME-python-{_slug(rel_dir)}", "kind": "fact", "title": f"Python {rp.group(1)}",
                         "data": {"topic": "runtime", "tech": "python", "declared": rp.group(1)},
                         "evidence": [_ev(root, mf, _line_of(text, "requires-python"))]})
        if mf.name == "pyproject.toml" and mf.parent == root:
            if "pytest" in text:
                _cmd(facts, "test", "pytest", root, mf, _line_of(text, "pytest"))
            if "[tool.ruff" in text:
                _cmd(facts, "lint", "ruff check .", root, mf, _line_of(text, "[tool.ruff"))
    pv = root / ".python-version"
    if pv.is_file() and _read(pv).strip():
        _add(facts, {"id": "F-RUNTIME-python-file", "kind": "fact", "title": f"Python {_read(pv).strip()}",
                     "data": {"topic": "runtime", "tech": "python", "version": _read(pv).strip()},
                     "evidence": [_ev(root, pv, 1)]})


# ---------------------------------------------------------------- Go, Rust

def _go(root: Path, techs: list[dict], facts: list, coverage: dict):
    for mf in _walk(root, {"go.mod"}):
        text = _read(mf)
        coverage["read"].append(mf.relative_to(root).as_posix())
        rel_dir = mf.parent.relative_to(root).as_posix()
        gv = re.search(r"^go\s+([\d.]+)", text, re.M)
        if gv:
            _add(facts, {"id": f"F-RUNTIME-go-{_slug(rel_dir)}", "kind": "fact", "title": f"Go {gv.group(1)}",
                         "data": {"topic": "runtime", "tech": "go", "version": gv.group(1)},
                         "evidence": [_ev(root, mf, _line_of(text, gv.group(0)))]})
        for m in re.finditer(r"^\s*(?:require\s+)?([\w./-]+\.[\w./-]+)\s+(v[\w.+-]+)(\s*//\s*indirect)?", text, re.M):
            if m.group(3):
                continue
            tech = _match(techs, "go", m.group(1))
            if tech:
                _stack_fact(facts, tech, "go", m.group(1), m.group(2).lstrip("v"), m.group(2), rel_dir,
                            [_ev(root, mf, text.count("\n", 0, m.start()) + 1)], "go.mod")
        if mf.parent == root:
            _cmd(facts, "test", "go test ./...", root, mf, 1)


def _rust(root: Path, techs: list[dict], facts: list, coverage: dict):
    for mf in _walk(root, {"Cargo.toml"}):
        text = _read(mf)
        coverage["read"].append(mf.relative_to(root).as_posix())
        rel_dir = mf.parent.relative_to(root).as_posix()
        lock = _nearest(mf.parent, root, ("Cargo.lock",))
        locked = _py_lock_versions(lock) if lock else {}
        for m in re.finditer(r'^([A-Za-z0-9_-]+)\s*=\s*(?:"([^"]+)"|\{[^}\n]*?version\s*=\s*"([^"]+)")', text, re.M):
            tech = _match(techs, "cargo", m.group(1))
            if not tech:
                continue
            evidence = [_ev(root, mf, text.count("\n", 0, m.start()) + 1)]
            version, how = None, "manifest-range"
            if _pyname(m.group(1)) in locked:
                version, line = locked[_pyname(m.group(1))]
                evidence.insert(0, _ev(root, lock, line))
                how = "lockfile"
            _stack_fact(facts, tech, "cargo", m.group(1), version, m.group(2) or m.group(3), rel_dir, evidence, how)
        if mf.parent == root:
            _cmd(facts, "test", "cargo test", root, mf, 1)


# ---------------------------------------------------------------- JVM, .NET

def _jvm(root: Path, techs: list[dict], facts: list, coverage: dict):
    for mf in _walk(root, {"pom.xml"}):
        text = _read(mf)
        coverage["read"].append(mf.relative_to(root).as_posix())
        rel_dir = mf.parent.relative_to(root).as_posix()
        props = dict(re.findall(r"<([\w.-]+)>([^<]+)</\1>",
                                (re.search(r"<properties>(.*?)</properties>", text, re.S) or [None, ""])[1]))
        blocks = [(m.start(), m.group(0), m.group(1)) for m in
                  re.finditer(r"<(parent|dependency|plugin)>.*?</\1>", text, re.S)]
        for start, block, _kind in blocks:
            g = re.search(r"<groupId>([^<]+)</groupId>", block)
            a = re.search(r"<artifactId>([^<]+)</artifactId>", block)
            if not (g and a):
                continue
            tech = _match(techs, "maven", f"{g.group(1)}:{a.group(1)}")
            if not tech:
                continue
            v = re.search(r"<version>([^<]+)</version>", block)
            version = v.group(1) if v else None
            if version and version.startswith("${"):
                version = props.get(version[2:-1])
            line = text.count("\n", 0, start + block.find("<artifactId>")) + 1
            _stack_fact(facts, tech, "maven", f"{g.group(1)}:{a.group(1)}", version, v.group(1) if v else "",
                        rel_dir, [_ev(root, mf, line)], "pom" if version else "managed")
        jv = props.get("java.version") or props.get("maven.compiler.release")
        if jv:
            _add(facts, {"id": f"F-RUNTIME-java-{_slug(rel_dir)}", "kind": "fact", "title": f"Java {jv}",
                         "data": {"topic": "runtime", "tech": "java", "version": jv},
                         "evidence": [_ev(root, mf, _line_of(text, jv, text.find("<properties>")))]})
        if mf.parent == root:
            _cmd(facts, "test", "./mvnw test" if (root / "mvnw").exists() else "mvn test", root, mf, 1)
    for cat in _walk(root, {"libs.versions.toml"}):
        text = _read(cat)
        coverage["read"].append(cat.relative_to(root).as_posix())
        versions = dict(re.findall(r'^([\w.-]+)\s*=\s*"([^"]+)"', text.split("[libraries]")[0], re.M))
        for m in re.finditer(r'^[\w.-]+\s*=\s*\{[^}\n]*module\s*=\s*"([^"]+)"[^}\n]*?(?:version\.ref\s*=\s*"([^"]+)"'
                             r'|version\s*=\s*"([^"]+)")', text, re.M):
            tech = _match(techs, "maven", m.group(1))
            if tech:
                version = versions.get(m.group(2)) if m.group(2) else m.group(3)
                _stack_fact(facts, tech, "maven", m.group(1), version, version or "", ".",
                            [_ev(root, cat, text.count("\n", 0, m.start()) + 1)], "version-catalog")
    for gf in _walk(root, {"build.gradle", "build.gradle.kts"}):
        text = _read(gf)
        coverage["read"].append(gf.relative_to(root).as_posix())
        m = re.search(r'id\s*\(?\s*["\']org\.springframework\.boot["\']\s*\)?\s*version\s*["\']([^"\']+)', text)
        if m:
            tech = next(t for t in techs if t["id"] == "spring-boot") if any(t["id"] == "spring-boot" for t in techs) \
                else None
            if tech:
                _stack_fact(facts, tech, "maven", "org.springframework.boot", m.group(1), m.group(1),
                            gf.parent.relative_to(root).as_posix(), [_ev(root, gf, _line_of(text, m.group(0)))],
                            "gradle-plugin")
        if gf.parent == root:
            _cmd(facts, "test", "./gradlew test" if (root / "gradlew").exists() else "gradle test", root, gf, 1)


def _dotnet(root: Path, techs: list[dict], facts: list, coverage: dict):
    projects = _walk(root, set(), (".csproj", ".fsproj"))
    for mf in projects:
        text = _read(mf)
        coverage["read"].append(mf.relative_to(root).as_posix())
        rel_dir = mf.parent.relative_to(root).as_posix()
        lock = mf.parent / "packages.lock.json"
        locked = {}
        if lock.is_file():
            for _fw, deps in (json.loads(_read(lock) or "{}").get("dependencies") or {}).items():
                for n, d in deps.items():
                    locked.setdefault(n.lower(), d.get("resolved"))
        for m in re.finditer(r'<PackageReference\s+Include="([^"]+)"(?:\s+Version="([^"]+)")?', text):
            tech = _match(techs, "nuget", m.group(1))
            if not tech:
                continue
            evidence = [_ev(root, mf, text.count("\n", 0, m.start()) + 1)]
            version, how = m.group(2), "project"
            if locked.get(m.group(1).lower()):
                version, how = locked[m.group(1).lower()], "lockfile"
                evidence.insert(0, _ev(root, lock, _line_of(_read(lock), f'"{m.group(1)}"')))
            _stack_fact(facts, tech, "nuget", m.group(1), version, m.group(2) or "", rel_dir, evidence, how)
        fw = re.search(r"<TargetFrameworks?>([^<]+)</TargetFrameworks?>", text)
        if fw:
            _add(facts, {"id": f"F-RUNTIME-dotnet-{_slug(rel_dir)}", "kind": "fact", "title": f".NET {fw.group(1)}",
                         "data": {"topic": "runtime", "tech": "dotnet", "version": fw.group(1)},
                         "evidence": [_ev(root, mf, _line_of(text, fw.group(0)))]})
    if projects:
        anchor = next(iter(_walk(root, set(), (".sln",))), projects[0])
        _cmd(facts, "test", "dotnet test", root, anchor, 1)


# ---------------------------------------------------------------- tooling, Makefile

TOOLING = [
    ("prettier", "format", (".prettierrc", ".prettierrc.json", ".prettierrc.js", ".prettierrc.cjs", ".prettierrc.yaml",
                            ".prettierrc.yml", "prettier.config.js", "prettier.config.mjs", "prettier.config.cjs")),
    ("eslint", "lint", ("eslint.config.js", "eslint.config.mjs", "eslint.config.cjs", "eslint.config.ts",
                        ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json", ".eslintrc.yml")),
    ("biome", "lint", ("biome.json", "biome.jsonc")),
    ("stylelint", "lint", (".stylelintrc", ".stylelintrc.json", "stylelint.config.js", "stylelint.config.mjs")),
    ("ruff", "lint", ("ruff.toml", ".ruff.toml")),
    ("editorconfig", "format", (".editorconfig",)),
    ("golangci-lint", "lint", (".golangci.yml", ".golangci.yaml")),
    ("checkstyle", "lint", ("checkstyle.xml",)),
]


def _tooling(root: Path, facts: list):
    for tool, role, names in TOOLING:
        for n in names:
            if (root / n).is_file():
                _add(facts, {"id": f"F-TOOL-{tool}", "kind": "fact", "title": f"{role}: {tool} ({n})",
                             "data": {"topic": "tooling", "tool": tool, "role": role, "config": n},
                             "evidence": [_ev(root, root / n, 1)]})
                break
    mk = root / "Makefile"
    if mk.is_file():
        text = _read(mk)
        for kind in ("test", "lint", "build", "format"):
            if re.search(rf"^{kind}\s*:", text, re.M):
                _cmd(facts, kind, f"make {kind}", root, mk, _line_of(text, re.compile(rf"^{kind}\s*:", re.M)))


# ---------------------------------------------------------------- facts

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "root"


def _add(facts: list, item: dict):
    item.setdefault("scope", {"paths": ["**"]})
    item.setdefault("status", "auto-accepted")
    item.setdefault("acceptance", "manifest")
    if any(f["id"] == item["id"] for f in facts):
        return
    facts.append(item)


def _cmd(facts, kind, command, root, path, line):
    """A command fact; the first source found wins (package.json scripts before Makefile)."""
    _add(facts, {"id": f"F-CMD-{kind}", "kind": "fact", "title": f"{kind}: {command}",
                 "data": {"topic": "command", "command_kind": kind, "command": command},
                 "evidence": [_ev(root, path, line)]})


def _stack_fact(facts, tech, eco, package, version, declared, rel_dir, evidence, how):
    scope = ["**"] if rel_dir in (".", "") else [f"{rel_dir}/**"]
    _add(facts, {
        "id": f"F-STACK-{tech['id']}-{_slug(rel_dir)}",
        "kind": "fact",
        "title": f"{tech['name']} {version or declared or '?'}",
        "scope": {"paths": scope},
        "acceptance": how,
        "data": {"topic": "stack", "tech": tech["id"], "name": tech["name"], "category": tech.get("category"),
                 "ecosystem": eco, "package": package, "version": version, "declared": declared,
                 "package_dir": rel_dir or "."},
        "evidence": evidence,
    })


def detect(root: Path, registry: Path) -> dict:
    """Facts about the repository: {"items": [...], "coverage": {"read": [...], "skipped": [...]}}."""
    techs = load_detectors(registry)
    facts: list[dict] = []
    coverage = {"read": [], "skipped": []}
    workspaces = _js(root, techs, facts, coverage)
    _python(root, techs, facts, coverage)
    _go(root, techs, facts, coverage)
    _rust(root, techs, facts, coverage)
    _jvm(root, techs, facts, coverage)
    _dotnet(root, techs, facts, coverage)
    _tooling(root, facts)
    if workspaces:
        _add(facts, {"id": "F-REPO-packages", "kind": "fact", "title": f"monorepo: {len(workspaces)} packages",
                     "data": {"topic": "layout", "packages": sorted(workspaces)},
                     "evidence": [_ev(root, root / p / "package.json", 1) for p in sorted(workspaces)[:20]]})
    versions: dict[str, set] = {}
    for f in facts:
        d = f.get("data", {})
        if d.get("topic") == "stack" and d.get("version"):
            versions.setdefault(d["tech"], set()).add(d["version"])
    for tech, vs in sorted(versions.items()):
        if len(vs) > 1:
            coverage.setdefault("notes", []).append(f"{tech}: several versions in the repository: {sorted(vs)}")
    return {"items": facts, "coverage": coverage}
