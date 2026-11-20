"""Building blocks of the UI as the team uses them: design-system and own components, tokens, the styling method.
No model, no network. Everything is counted in the code, with `path:line` evidence:

- design-system components: imports from the design-system packages of the stack (category design-system), from
  workspace packages named like a UI library (ui, design-system, ds, components) and from packages listed in
  dna.yaml `design_system.packages`; the canon is what the code imports, ordered by the number of importing files;
- own components: PascalCase exports from shared directories (components, shared, ui, common) imported by at least
  two files; `@deprecated` in the JSDoc above the definition marks a component as deprecated;
- tokens: CSS custom properties (with use counts), SCSS variables in variables/tokens files, DTCG `$value` entries;
  the theme files (tailwind.config, createTheme, extendTheme) are reported as places, not parsed;
- styling: how component files style themselves (CSS Modules, styled/emotion, `sx`, Tailwind classes, inline
  `style`, plain CSS imports), as shares of the files that style at all.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .detect import SKIP_DIRS

CODE_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".vue", ".svelte")
STYLE_EXT = (".css", ".scss", ".sass", ".less")
MAX_FILES = 8000
MAX_BYTES = 512 * 1024
SHARED_DIRS = {"components", "shared", "ui", "common"}
UI_PKG = re.compile(r"(^|[/@-])(ui|design-system|designsystem|ds|components)$")
IMPORT = re.compile(r"""import\s+(type\s+)?(?:([A-Za-z_$][\w$]*)\s*,?\s*)?(?:\{([^}]*)\})?\s*from\s*['"]([^'"]+)['"]""",
                    re.S)
EXPORT = re.compile(r"^export\s+(?:default\s+)?(?:const|function|class)\s+([A-Z][A-Za-z0-9]*)", re.M)
STYLING = {
    "css-modules": re.compile(r"""import\s+\w+\s+from\s+['"][^'"]+\.module\.(?:s?css|sass|less)['"]"""),
    "styled": re.compile(r"""\bstyled(?:\.\w+|\()|from\s+['"](?:styled-components|@emotion/styled)['"]"""),
    "sx-prop": re.compile(r"\bsx=\{"),
    "tailwind": re.compile(r"""className=(?:"|'|\{`)[^"'`]*\b(?:flex|grid|gap-\d|p[xytrbl]?-\d|m[xytrbl]?-\d|"""
                           r"""text-(?:xs|sm|base|lg|xl)|bg-[a-z]|rounded(?:-\w+)?|w-\d|h-\d)\b"""),
    "inline-style": re.compile(r"\bstyle=\{\{"),
    "plain-css": re.compile(r"""import\s+['"][^'"]+(?<!\.module)\.(?:s?css|sass|less)['"]"""),
}
CSS_VAR = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;}{]+);")
SCSS_VAR = re.compile(r"^\s*\$([A-Za-z0-9_-]+)\s*:\s*([^;]+);", re.M)
THEME_FILES = re.compile(r"\b(createTheme|extendTheme|defineConfig\(\s*\{[^}]*theme|createStitches|tokens\s*=)\b")


def _files(root: Path) -> tuple[list[Path], list[Path], list[Path]]:
    code, styles, tokens = [], [], []

    def rec(d: Path, depth: int):
        try:
            entries = sorted(d.iterdir())
        except OSError:
            return
        for e in entries:
            if e.is_dir():
                if e.name not in SKIP_DIRS and not e.name.startswith(".") and depth < 12:
                    rec(e, depth + 1)
            elif len(code) + len(styles) < MAX_FILES:
                try:
                    if e.stat().st_size > MAX_BYTES:
                        continue
                except OSError:
                    continue
                if e.name.endswith(CODE_EXT) and ".d.ts" not in e.name:
                    code.append(e)
                elif e.name.endswith(STYLE_EXT):
                    styles.append(e)
                elif e.suffix == ".json" and "token" in e.as_posix().lower():
                    tokens.append(e)
    rec(root, 0)
    return code, styles, tokens


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", ".", s).strip(".") or "x"


def _rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def _ds_packages(root: Path, items: list[dict], config: dict) -> dict[str, str]:
    """package → origin ("stack" | "workspace" | "config")."""
    pkgs = {}
    for i in items:
        d = i.get("data") or {}
        if d.get("topic") == "stack" and d.get("category") == "design-system":
            pkgs[d["package"]] = "stack"
    for i in items:
        d = i.get("data") or {}
        if d.get("topic") == "layout":
            for rel in d.get("packages", []):
                try:
                    name = json.loads(_read(root / rel / "package.json")).get("name") or ""
                except ValueError:
                    continue
                if name and UI_PKG.search(name):
                    pkgs[name] = "workspace"
    for name in (config.get("design_system") or {}).get("packages") or []:
        pkgs[str(name)] = "config"
    return pkgs


def _ds_of(source: str, pkgs: dict[str, str]) -> str | None:
    for p in pkgs:
        if source == p or source.startswith(p + "/"):
            return p
    return None


_ALIASES: dict[str, list[tuple[str, Path]]] = {}


def aliases(root: Path) -> list[tuple[str, Path]]:
    """Path aliases from tsconfig.json / jsconfig.json `compilerOptions.paths` (e.g. "@/*" → ./src/*)."""
    key = str(root)
    if key in _ALIASES:
        return _ALIASES[key]
    out = []
    for name in ("tsconfig.json", "jsconfig.json"):
        text = _read(root / name)
        if not text:
            continue
        text = re.sub(r",(\s*[}\]])", r"\1", _strip_json_comments(text))
        try:
            opts = json.loads(text).get("compilerOptions") or {}
        except ValueError:
            continue
        base = root / (opts.get("baseUrl") or ".")
        for pattern, targets in (opts.get("paths") or {}).items():
            if targets:
                out.append((pattern.rstrip("*"), (base / str(targets[0]).rstrip("*")).resolve()))
        break
    _ALIASES[key] = sorted(out, key=lambda a: -len(a[0]))
    return _ALIASES[key]


def _strip_json_comments(text: str) -> str:
    """// and /* */ comments outside strings (tsconfig.json is JSON with comments)."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            out.append(c)
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        else:
            out.append(c)
        i += 1
    return "".join(out)


def is_local(spec: str, root: Path) -> bool:
    return spec.startswith(".") or any(spec.startswith(prefix) for prefix, _ in aliases(root) if prefix)


def _resolve(importer: Path, spec: str, root: Path | None = None) -> Path | None:
    base = (importer.parent / spec).resolve()
    if not spec.startswith(".") and root is not None:
        for prefix, target in aliases(root):
            if prefix and spec.startswith(prefix):
                base = (target / spec[len(prefix):]).resolve()
                break
        else:
            return None
    for cand in [base] + [base.with_name(base.name + ext) for ext in CODE_EXT] + \
                [base / f"index{ext}" for ext in CODE_EXT]:
        if cand.is_file():
            return cand
    return None


def _deprecated(text: str, pos: int) -> bool:
    before = text[max(0, pos - 600):pos]
    m = list(re.finditer(r"/\*\*.*?\*/\s*$", before, re.S))
    return bool(m) and "@deprecated" in m[-1].group(0)


def ui(root: Path, items: list[dict], config: dict | None = None) -> tuple[list[dict], dict]:
    config = config or {}
    pkgs = _ds_packages(root, items, config)
    code, styles, token_files = _files(root)
    out: list[dict] = []
    coverage = {"read": [], "skipped": []}
    ds_use: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)   # (pkg, comp) → [(file, line)]
    ds_form: dict[tuple[str, str], Counter] = defaultdict(Counter)            # (pkg, comp) → import line → count
    own_use: dict[tuple[Path, str], set[str]] = defaultdict(set)              # (definition file, comp) → importers
    style_hits: dict[str, list[tuple[str, int]]] = defaultdict(list)
    styled_files = 0
    css_var_use: Counter = Counter()
    style_texts = {f: _read(f) for f in styles}
    for text in style_texts.values():
        for m in re.finditer(r"var\((--[A-Za-z0-9_-]+)", text):
            css_var_use[m.group(1)] += 1
    for f in code:
        text = _read(f)
        rel = _rel(root, f)
        for m in IMPORT.finditer(text):
            if m.group(1):   # `import type { … }` — types, not components
                continue
            default, named, source = m.group(2), m.group(3), m.group(4)
            names = [n.strip().split(" as ")[0].strip() for n in (named or "").split(",")
                     if n.strip() and not n.strip().startswith("type ")]
            if default:
                names.append(default)
            comps = [n for n in names if re.match(r"^[A-Z][A-Za-z0-9]*$", n)]
            if not comps:
                continue
            pkg = _ds_of(source, pkgs)
            line = _line(text, m.start())
            if pkg:
                subpath = default and not named and source != pkg
                if subpath:   # '@mui/material/Button' → Button
                    last = source.rsplit("/", 1)[-1]
                    if not re.match(r"^[A-Z][A-Za-z0-9]*$", last):
                        continue
                    comps = [last]
                for c in comps:
                    if c.endswith(("Props", "Options", "Theme")) or c in ("Components", "Theme"):
                        continue   # types imported without `type`
                    ds_use[(pkg, c)].append((rel, line))
                    ds_form[(pkg, c)][f"import {c} from '{source}'" if subpath else f"import {{ {c} }} from '{source}'"] += 1
            elif is_local(source, root):
                target = _resolve(f, source, root)
                if target and SHARED_DIRS & set(_rel(root, target).split("/")[:-1]):
                    for c in comps:
                        own_use[(target, c)].add(rel)
        hits = [k for k, rx in STYLING.items() if rx.search(text)]
        if hits:
            styled_files += 1
        for k in hits:
            m = STYLING[k].search(text)
            style_hits[k].append((rel, _line(text, m.start())))
        for m in re.finditer(r"var\((--[A-Za-z0-9_-]+)", text):
            css_var_use[m.group(1)] += 1
    # design-system components, ordered by importing files
    by_files = {k: len({f for f, _ in v}) for k, v in ds_use.items()}
    for (pkg, comp), uses in sorted(ds_use.items(), key=lambda kv: (-by_files[kv[0]], kv[0])):
        out.append({"id": f"B-UI-{_slug(pkg)}-{comp}", "kind": "block", "title": f"{comp} from {pkg}",
                    "scope": {"paths": ["**"]}, "status": "auto-accepted", "acceptance": f"used in {by_files[(pkg, comp)]} files",
                    "data": {"topic": "ui-component", "origin": "design-system", "package": pkg,
                             "package_origin": pkgs[pkg], "name": comp,
                             "import": ds_form[(pkg, comp)].most_common(1)[0][0],
                             "files": by_files[(pkg, comp)]},
                    "evidence": [f"{f}:{ln}" for f, ln in uses[:3]]})
    # own shared components imported by ≥ 2 files
    for (target, comp), importers in sorted(own_use.items(), key=lambda kv: (-len(kv[1]), kv[0][1])):
        if len(importers) < 2:
            continue
        text = _read(target)
        m = re.search(rf"^export\s+(?:default\s+)?(?:const|function|class)\s+{comp}\b", text, re.M) or \
            re.search(rf"\b(?:const|function|class)\s+{comp}\b", text)
        line = _line(text, m.start()) if m else 1
        deprecated = bool(m) and _deprecated(text, m.start())
        rel = _rel(root, target)
        out.append({"id": f"B-UI-own-{_slug(rel)}-{comp}", "kind": "block",
                    "title": f"{comp} ({rel})" + (" — deprecated" if deprecated else ""),
                    "scope": {"paths": ["**"]}, "status": "abandoned" if deprecated else "auto-accepted",
                    "acceptance": "@deprecated" if deprecated else f"used in {len(importers)} files",
                    "data": {"topic": "ui-component", "origin": "own", "name": comp, "path": rel,
                             "deprecated": deprecated, "files": len(importers)},
                    "evidence": [f"{rel}:{line}"]})
    # tokens
    seen = set()
    for f in styles:
        text = style_texts[f]
        rel = _rel(root, f)
        for m in CSS_VAR.finditer(text):
            name = m.group(1)
            if name in seen:
                continue
            seen.add(name)
            out.append({"id": f"B-TOKEN-{_slug(name)}", "kind": "block", "title": f"{name}: {m.group(2).strip()}",
                        "scope": {"paths": ["**"]}, "status": "auto-accepted", "acceptance": "defined",
                        "data": {"topic": "token", "name": name, "value": m.group(2).strip(), "syntax": "css-var",
                                 "uses": css_var_use[name]},
                        "evidence": [f"{rel}:{_line(text, m.start())}"]})
        if re.search(r"(variables|tokens|theme|_vars)", f.stem, re.I):
            for m in SCSS_VAR.finditer(text):
                name = "$" + m.group(1)
                if name in seen:
                    continue
                seen.add(name)
                out.append({"id": f"B-TOKEN-scss.{_slug(m.group(1))}", "kind": "block",
                            "title": f"{name}: {m.group(2).strip()}", "scope": {"paths": ["**"]},
                            "status": "auto-accepted", "acceptance": "defined",
                            "data": {"topic": "token", "name": name, "value": m.group(2).strip(), "syntax": "scss"},
                            "evidence": [f"{rel}:{_line(text, m.start())}"]})
    for f in token_files:
        text = _read(f)
        try:
            data = json.loads(text)
        except ValueError:
            continue
        rel = _rel(root, f)

        def walk(node, path):
            if isinstance(node, dict):
                if "$value" in node:
                    name = ".".join(path)
                    if name not in seen:
                        seen.add(name)
                        key = f'"{path[-1]}"'
                        out.append({"id": f"B-TOKEN-dtcg.{_slug(name)}", "kind": "block",
                                    "title": f"{name}: {node['$value']}", "scope": {"paths": ["**"]},
                                    "status": "auto-accepted", "acceptance": "defined",
                                    "data": {"topic": "token", "name": name, "value": node["$value"],
                                             "syntax": "dtcg", "type": node.get("$type")},
                                    "evidence": [f"{rel}:{_line(text, max(text.find(key), 0))}"]})
                    return
                for k, v in node.items():
                    if not k.startswith("$"):
                        walk(v, path + [k])
        walk(data, [])
    themes = []
    for f in code:
        name = f.name
        text = _read(f) if name.startswith(("tailwind.config", "theme", "tokens")) or "theme" in f.stem.lower() else ""
        if name.startswith("tailwind.config"):
            themes.append((_rel(root, f), 1, "tailwind"))
        elif text and THEME_FILES.search(text):
            m = THEME_FILES.search(text)
            themes.append((_rel(root, f), _line(text, m.start()), "theme"))
    for rel, line, kind in themes[:10]:
        out.append({"id": f"F-THEME-{_slug(rel)}", "kind": "fact", "title": f"theme definition: {rel}",
                    "scope": {"paths": ["**"]}, "status": "auto-accepted", "acceptance": kind,
                    "data": {"topic": "theme", "path": rel, "kind": kind}, "evidence": [f"{rel}:{line}"]})
    # styling method
    for method, hits in sorted(style_hits.items(), key=lambda kv: -len(kv[1])):
        share = round(100 * len(hits) / styled_files) if styled_files else 0
        out.append({"id": f"C-STYLE-{method}", "kind": "convention",
                    "title": f"styling with {method}: {share}% of styled files ({len(hits)}/{styled_files})",
                    "scope": {"paths": ["**"]}, "status": "auto-accepted", "acceptance": f"share {share}%",
                    "data": {"topic": "styling", "method": method, "share": share, "files": len(hits),
                             "of": styled_files},
                    "evidence": [f"{f}:{ln}" for f, ln in hits[:3]]})
    coverage["read"].append(f"{len(code)} code files, {len(styles)} style files, {len(token_files)} token files "
                            f"(UI catalog)")
    if len(code) + len(styles) >= MAX_FILES:
        coverage["skipped"].append({"source": "UI catalog", "reason": f"stopped at {MAX_FILES} files"})
    return out, coverage
