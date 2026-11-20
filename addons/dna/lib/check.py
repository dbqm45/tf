"""Check of a change against out/knowledge.json: added lines only, by the balance rule of the plan (section 4.4).

  hard (deprecated component in use)            → blocks, in new and in existing files (changed lines)
  soft (design-system component exists, token exists, own component duplicated, styling method, import form)
                                                → blocks in new files, warns in existing files (local style wins)
Formatting is the formatter's job and is not checked here. Output: {"findings": [...], "summary": ...};
the caller exits 1 when a finding blocks. No model, no network.
"""
from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from pathlib import Path

from .code import STYLING

UI_FILES = (".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss", ".less", ".ts", ".js", ".mjs", ".cjs")
RAW = {"button": ["Button", "IconButton"], "input": ["TextField", "Input", "OutlinedInput"],
       "select": ["Select"], "textarea": ["TextField", "Textarea"], "a": ["Link"], "table": ["Table"],
       "dialog": ["Dialog", "Modal"]}
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
PX = re.compile(r"(?<![\w.-])\d+(?:\.\d+)?px\b")
EXPORT = re.compile(r"^\s*export\s+(?:default\s+)?(?:const|function|class)\s+([A-Z][A-Za-z0-9]*)")
IMPORT = re.compile(r"""import\s+(?:([A-Za-z_$][\w$]*)\s*,?\s*)?(?:\{([^}]*)\})?\s*from\s*['"]([^'"]+)['"]""")


def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:200]}")
    return r.stdout


def changes(root: Path, base: str) -> tuple[dict[str, list[tuple[int, str]]], set[str]]:
    """Added lines per file (working tree against base, untracked files included) and the set of new files."""
    status = _git(root, "diff", "--name-status", base)
    new = {ln.split("\t")[-1] for ln in status.splitlines() if ln.startswith("A")}
    added: dict[str, list[tuple[int, str]]] = defaultdict(list)
    current, line = None, 0
    for ln in _git(root, "diff", "-U0", "--no-color", base).splitlines():
        if ln.startswith("+++ "):
            current = ln[6:] if ln.startswith("+++ b/") else None
        elif ln.startswith("@@"):
            m = re.search(r"\+(\d+)", ln)
            line = int(m.group(1)) if m else 0
        elif current and ln.startswith("+") and not ln.startswith("+++"):
            added[current].append((line, ln[1:]))
            line += 1
    for rel in _git(root, "ls-files", "--others", "--exclude-standard").splitlines():
        p = root / rel
        if p.is_file() and rel.endswith(UI_FILES) and ".tf/" not in rel:
            new.add(rel)
            text = p.read_text(encoding="utf-8", errors="replace")
            added[rel] = [(i, t) for i, t in enumerate(text.splitlines(), 1)]
    return dict(added), new


def check(root: Path, knowledge: dict, base: str, decisions: list[dict] | None = None) -> dict:
    items = knowledge.get("items") or []
    forbidden = {d["data"]["forbidden_import"]: d for d in decisions or []
                 if (d.get("data") or {}).get("forbidden_import")}
    by = lambda topic: [i for i in items if (i.get("data") or {}).get("topic") == topic]  # noqa: E731
    comps = by("ui-component")
    ds = [c for c in comps if c["data"]["origin"] == "design-system"]
    ds_names = {c["data"]["name"]: c for c in ds}
    own = {c["data"]["name"]: c for c in comps if c["data"]["origin"] == "own" and not c["data"].get("deprecated")}
    deprecated = {c["data"]["name"]: c for c in comps if c["data"].get("deprecated")}
    tokens = defaultdict(list)
    for t in by("token"):
        tokens[str(t["data"]["value"]).strip().lower()].append(t["data"]["name"])
    styling = sorted(by("styling"), key=lambda i: -i["data"]["share"])
    dominant = styling[0]["data"] if styling and styling[0]["data"]["share"] >= 50 else None
    shares = {s["data"]["method"]: s["data"]["share"] for s in styling}
    rare = {m for m in STYLING if m != (dominant or {}).get("method") and shares.get(m, 0) < 10} if dominant else set()
    forms = {c["data"]["name"]: c["data"]["import"] for c in ds}
    added, new = changes(root, base)
    findings = []

    def add(rule, soft, rel, line, message, suggestion):
        severity = ("block" if rel in new else "warn") if soft else "block"
        findings.append({"rule": rule, "strength": "soft" if soft else "hard", "severity": severity, "file": rel,
                         "line": line, "message": message, "suggestion": suggestion})

    for rel, lines in sorted(added.items()):
        if not rel.endswith(UI_FILES) or rel.startswith(".tf/"):
            continue
        is_markup = rel.endswith((".tsx", ".jsx", ".vue", ".svelte"))
        for line, text in lines:
            for name, c in deprecated.items():
                if re.search(rf"\b{name}\b", text):
                    add("deprecated-component", False, rel, line, f"{name} is deprecated ({c['evidence'][0]})",
                        "use the replacement named in its @deprecated note")
            if is_markup:
                for tag, alts in RAW.items():
                    if re.search(rf"<{tag}[\s>/]", text):
                        have = [a for a in alts if a in ds_names]
                        if have:
                            add("raw-element", True, rel, line, f"<{tag}> where the design system has {have[0]}",
                                ds_names[have[0]]["data"]["import"])
            m = EXPORT.match(text)
            if m and (m.group(1) in ds_names or m.group(1) in own):
                where = ds_names.get(m.group(1)) or own.get(m.group(1))
                add("duplicate-component", True, rel, line, f"new component {m.group(1)} duplicates "
                    f"{where['title']}", "reuse it or extend it instead of a copy")
            for v in HEX.findall(text) + PX.findall(text):
                names = tokens.get(v.lower())
                if names and "var(" not in text:
                    add("value-with-token", True, rel, line, f"{v} has a token: {names[0]}",
                        f"use {names[0]}" + (" (var(...))" if names[0].startswith("--") else ""))
            im = IMPORT.search(text) or re.search(r"""()()require\(['"]([^'"]+)['"]\)""", text)
            if im and forbidden:
                mod = im.group(3)
                for name, d in forbidden.items():
                    if mod == name or mod.startswith(name + "/"):
                        add("forbidden-import", d.get("strength") == "soft", rel, line, f"{d['title']}",
                            f"agreed rule {d['data'].get('rule_id') or d['id']} ({d['evidence'][0]})")
            if im:
                named = [n.strip().split(" as ")[0] for n in (im.group(2) or "").split(",") if n.strip()]
                for name in named + ([im.group(1)] if im.group(1) else []):
                    if name in forms and not _same_form(text, forms[name], name):
                        add("import-form", True, rel, line, f"{name} is imported differently from the code",
                            forms[name])
            if dominant and is_markup:
                for method in rare:
                    if STYLING[method].search(text):
                        add("styling-method", True, rel, line, f"{method} is rare here ({_share(styling, method)}%)",
                            f"style with {dominant['method']} like {dominant['share']}% of styled files")
    blocks = sum(f["severity"] == "block" for f in findings)
    return {"base": base, "findings": findings,
            "summary": f"{len(findings)} findings, {blocks} blocking (hard everywhere, soft in new files)"}


def _same_form(text: str, form: str, name: str) -> bool:  # noqa: ARG001
    """Same module path as the dominant form (named from the root vs default from a subpath)."""
    source = re.search(r"from '([^']+)'", form).group(1)
    m = re.search(r"""from\s*['"]([^'"]+)['"]""", text)
    return (m.group(1) if m else "") == source


def _share(styling, method):
    return next((s["data"]["share"] for s in styling if s["data"]["method"] == method), 0)
