"""Decisions (standards, rules, agreements) from the project's sources, as candidates with a quote and evidence.

Sources, in the order of the hierarchy:
  standards  — standards skills (standards.yaml `sources`, or skills named like *standards* in .claude/skills/), their
               references/ and rules/; skills may come from a git repository by URL (cloned in cache/standards/);
               the Confluence pages they link to are read through the session's MCP tool (see `pending` below);
  adr        — architecture decision records (docs/adr, docs/decisions, adr, doc/adr);
  lint       — restricted imports in ESLint configuration (`no-restricted-imports` with a message);
  doc        — README, CONTRIBUTING, docs/**/*.md;
  tool-rules — instruction files of other agents: CLAUDE.md, AGENTS.md (without the factory's generated blocks),
               .cursor/rules/*.mdc, .github/copilot-instructions.md, .github/instructions/*.instructions.md.

Confluence through MCP: a script cannot use the session's tools. For every linked page without a fresh copy the
add-on lists a pending read (cache/pending.json, `provides.pending`): the agent reads the page with the Confluence
tool connected in the session (read-only) and saves its text to the given file with the header lines
`Source: <url>`, `Fetched: YYYY-MM-DD` (and `Version: <n>` when the tool gives it), then the next learn/refresh uses
the copy. A copy older than `confluence.stale_after_days` (default 14) is used and listed for a re-read.
A decision is a list item or a rule-ID line with normative words (must, never, always, should, prefer, avoid, use…,
also Polish). No model: the quote is the line itself, evidence is `path:line` or the page URL with the fetch date.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
from pathlib import Path

HARD = re.compile(r"\b(must|must not|never|do not|don't|shall|is required|are required|forbidden|not allowed|always|"
                  r"nie wolno|musi|muszą|nigdy|zawsze|wymagane|zakazane|zabronione)\b", re.I)
SOFT = re.compile(r"\b(should|prefer|avoid|use|recommended|należy|powinien|powinna|powinno|unikaj|używaj|stosuj|"
                  r"preferuj|zalecane)\b", re.I)
RULE_ID = re.compile(r"^\s*(?:[-*]\s+)?\**([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+)\**\s*[:—–-]\s*(.+)")
ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+)")
LINK = re.compile(r"https?://[^\s)>\]\"'`]+")
FACTORY_BLOCK = re.compile(r"<!-- (team-factory|tf-addons):begin.*?<!-- \1:end -->", re.S)
FE_PATHS = ["**/*.tsx", "**/*.jsx", "**/*.ts", "**/*.js", "**/*.vue", "**/*.svelte", "**/*.css", "**/*.scss",
            "**/*.less", "**/*.html"]
BE_PATHS = ["**/*.py", "**/*.java", "**/*.kt", "**/*.go", "**/*.cs", "**/*.rs", "**/*.rb", "**/*.php", "**/*.sql"]
RANK = {"standards": 1, "adr": 2, "lint": 3, "doc": 4, "tool-rules": 4}
MAX_PAGE_BYTES = 2 * 1024 * 1024


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _clean(s: str) -> str:
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\*\*|__|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", s)
    return re.sub(r"\s+", " ", s).strip(" .;")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9ąćęłńóśźż ]+", "", _clean(s).lower()).strip()


def _scope_paths(scope: str | None, paths: list | None) -> list[str]:
    if paths:
        return [str(p) for p in paths]
    return {"fe": FE_PATHS, "be": BE_PATHS}.get((scope or "mutual").lower(), ["**"])


def _guess_scope(name: str) -> str:
    n = name.lower()
    if re.search(r"(^|[-_])(fe|frontend|front|web|ui|mobile)([-_]|$)", n):
        return "fe"
    if re.search(r"(^|[-_])(be|backend|back|api|server|service)([-_]|$)", n):
        return "be"
    return "mutual"


def extract(text: str, origin: str, kind: str, paths: list[str]) -> list[dict]:
    """Candidates from Markdown-like text; `origin` is the evidence prefix (path) or a URL."""
    out, fence = [], False
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        rid = RULE_ID.match(line)
        m = ITEM.match(line)
        body = rid.group(2) if rid else (m.group(1) if m else None)
        if not body:
            continue
        body = _clean(body)
        if not 12 <= len(body) <= 400:
            continue
        hard, soft = HARD.search(body), SOFT.search(body)
        if not (rid or hard or soft):
            continue
        out.append({"text": body, "rule_id": rid.group(1) if rid else None, "kind": kind,
                    "strength": "hard" if hard else "soft", "paths": paths,
                    "evidence": origin if origin.startswith(("https://", "http://")) else f"{origin}:{n}"})
    return out


# ---------------------------------------------------------------- Confluence (through MCP)

def page_key(url: str) -> str:
    m = re.search(r"/pages/(\d+)", url) or re.search(r"[?&]pageId=(\d+)", url)
    return m.group(1) if m else re.sub(r"[^A-Za-z0-9]+", "_", url.split("://", 1)[-1])[:80]


def read_copy(path: Path) -> tuple[str, str, str] | None:
    """(body, fetched, version) of a page copy saved by the agent; None when absent or without a header."""
    text = _read(path)
    head, _, body = text.partition("\n\n")
    fields = dict(re.findall(r"(?m)^(Source|Fetched|Version):\s*(.+)$", head))
    if not text or not re.match(r"^\d{4}-\d{2}-\d{2}$", fields.get("Fetched", "").strip()):
        return None
    return body, fields["Fetched"].strip(), fields.get("Version", "").strip()


# ---------------------------------------------------------------- collection

def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")[:80]


def clone(url: str, ref: str | None, cache: Path, online: bool) -> tuple[Path | None, str]:
    """A shallow clone of a standards repository in cache/standards/ (updated when online). (dir, note)."""
    import subprocess
    target = cache / "standards" / f"{_slug(url)}@{_slug(ref or 'default')}"
    if not online:
        return (target, "cached clone (network off)") if (target / ".git").is_dir() else (None, "network off, no clone")
    target.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    if (target / ".git").is_dir():
        args = ["git", "-C", str(target), "fetch", "-q", "--depth", "1", "origin", ref or "HEAD"]
        r = subprocess.run(args, capture_output=True, text=True, timeout=120, env=env)
        if r.returncode == 0:
            subprocess.run(["git", "-C", str(target), "checkout", "-q", "--force", "FETCH_HEAD"], capture_output=True,
                           timeout=60, env=env)
            return target, "updated"
        return target, f"update failed, cached clone used: {r.stderr.strip()[-150:]}"
    args = ["git", "clone", "-q", "--depth", "1"] + (["--branch", ref] if ref else []) + [url, str(target)]
    r = subprocess.run(args, capture_output=True, text=True, timeout=300, env=env)
    if r.returncode != 0:
        return None, f"git clone failed: {r.stderr.strip()[-200:]}"
    return target, "cloned"


def _skill_dirs(base: Path) -> list[Path]:
    if (base / "SKILL.md").is_file():
        return [base]
    return sorted(d.parent for d in base.glob("**/SKILL.md") if ".git" not in d.parts)


def _standards_skills(root: Path, config: dict, cache: Path | None = None, online: bool = False,
                      coverage: dict | None = None) -> list[dict]:
    listed = config.get("standards") or []
    found = []
    for s in listed:
        if s.get("path") and (root / s["path"] / "SKILL.md").is_file():
            found.append({"dir": root / s["path"], "scope": s.get("scope"), "paths": s.get("paths"), "git": None})
        elif s.get("git") and cache is not None:
            repo, note = clone(str(s["git"]), s.get("ref"), cache, online)
            if coverage is not None and repo is None:
                coverage["skipped"].append({"source": str(s["git"]), "reason": note})
                continue
            base = repo / s.get("dir", "") if s.get("dir") else repo
            dirs = _skill_dirs(base)
            if not dirs and coverage is not None:
                coverage["skipped"].append({"source": str(s["git"]), "reason": f"no SKILL.md under {s.get('dir') or '/'}"})
            for d in dirs:
                found.append({"dir": d, "scope": s.get("scope") or _guess_scope(d.name), "paths": s.get("paths"),
                              "git": {"url": str(s["git"]), "ref": s.get("ref") or "default", "root": repo}})
    if listed:
        return found
    base = root / ".claude" / "skills"
    if not base.is_dir():
        return []
    return [{"dir": d, "scope": _guess_scope(d.name), "paths": None, "git": None} for d in sorted(base.iterdir())
            if (d / "SKILL.md").is_file() and re.search(r"standard", d.name, re.I)]


def collect(root: Path, config: dict, online: bool, today: str, opts: dict | None = None) -> tuple[list[dict], dict]:
    opts = opts or {}
    found, coverage = [], {"read": [], "skipped": []}
    rel = lambda p: p.relative_to(root).as_posix()  # noqa: E731
    # standards skills and their links
    cache = opts.get("cache")
    for s in _standards_skills(root, config, cache, online, coverage):
        paths = _scope_paths(s["scope"] or _guess_scope(s["dir"].name), s["paths"])
        files = [s["dir"] / "SKILL.md"] + sorted((s["dir"] / "references").glob("**/*.md")) \
            + sorted((s["dir"] / "rules").glob("**/*.md"))
        links = []
        for f in files:
            text = _read(f)
            if s["git"]:   # outside the project: evidence is the repository URL, ref, path and line
                g = s["git"]
                src = f"{g['url']}#{g['ref']}:{f.relative_to(g['root']).as_posix()}"
                coverage["read"].append(src)
                cands = extract(text, "x", "standards", paths)
                for c in cands:
                    line = c["evidence"].rsplit(":", 1)[1]
                    c["evidence"] = f"{src}:L{line} (fetched {today})"
            else:
                coverage["read"].append(rel(f))
                cands = extract(text, rel(f), "standards", paths)
            for c in cands:
                c["skill"] = s["dir"].name
                found.append(c)
            links += LINK.findall(text)
        conf = config.get("confluence") or {}
        stale = int(conf.get("stale_after_days", 14))
        copies = Path(opts.get("copies") or (cache or root) / "sources" / "confluence")
        for url in dict.fromkeys(links):
            if "/wiki/" not in url and "atlassian.net" not in url:
                coverage["skipped"].append({"source": url, "reason": "link outside Confluence: not followed"})
                continue
            save_to = copies / f"{page_key(url)}.md"
            copy = read_copy(save_to)
            if copy is None:
                coverage.setdefault("pending", []).append({"url": url, "tool": "confluence", "save_to": str(save_to),
                                                           "reason": "not read yet"})
                coverage["skipped"].append({"source": url, "reason": "pending: read through the session's Confluence "
                                                                     "tool (MCP) — see pending.json"})
                continue
            body, fetched, version = copy
            age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(fetched)).days
            if age > stale:
                coverage.setdefault("pending", []).append({"url": url, "tool": "confluence", "save_to": str(save_to),
                                                           "reason": f"copy from {fetched} is older than {stale} days"})
            coverage["read"].append(f"{url} (copy {fetched}" + (f", version {version})" if version else ")"))
            for c in extract(body, f"{url} (fetched {fetched})", "standards", paths):
                c["skill"] = s["dir"].name
                found.append(c)
    # ADR
    for d in ("docs/adr", "docs/decisions", "adr", "doc/adr", "docs/architecture/decisions"):
        for f in sorted((root / d).glob("*.md")):
            text = _read(f)
            coverage["read"].append(rel(f))
            accepted = re.search(r"(?im)^\W*status\W*:?\W*(accepted|approved|przyjęt)", text) is not None
            for c in extract(text, rel(f), "adr", ["**"]):
                c["adr_accepted"] = accepted
                found.append(c)
    # lint: restricted imports
    for name in (".eslintrc.json", ".eslintrc", "eslint.config.js", "eslint.config.mjs", "eslint.config.cjs",
                 ".eslintrc.js", ".eslintrc.cjs"):
        f = root / name
        if not f.is_file():
            continue
        text = _read(f)
        coverage["read"].append(name)
        block = text[text.find("no-restricted-imports"):] if "no-restricted-imports" in text else ""
        for m in re.finditer(r"""name\s*['"]?\s*:\s*['"]([^'"]+)['"][^}]*?message\s*['"]?\s*:\s*['"]([^'"]+)['"]""",
                             block[:20000], re.S):
            line = text.count("\n", 0, text.find(m.group(0))) + 1
            found.append({"text": f"Do not import {m.group(1)}: {_clean(m.group(2))}", "rule_id": None,
                          "forbidden_import": m.group(1),
                          "kind": "lint", "strength": "hard", "paths": ["**"], "evidence": f"{name}:{line}"})
    # project documentation
    docs_files = [p for p in sorted(root.glob("*.md")) if re.match(r"(README|CONTRIBUTING|STYLEGUIDE|CODING)", p.name, re.I)]
    docs_files += [p for p in sorted((root / "docs").glob("**/*.md")) if "adr" not in p.parts and "decisions" not in p.parts]
    for f in docs_files[:200]:
        text = _read(f)
        coverage["read"].append(rel(f))
        found += extract(text, rel(f), "doc", ["**"])
    # other agents' instruction files
    tool_files = [(root / n, ["**"]) for n in ("CLAUDE.md", "AGENTS.md", ".github/copilot-instructions.md",
                                               ".windsurfrules", ".cursorrules")]
    for f in sorted((root / ".cursor" / "rules").glob("**/*.mdc")):
        g = re.search(r"(?m)^globs:\s*(.+)$", _read(f))
        tool_files.append((f, [x.strip(" '\"") for x in g.group(1).strip("[]").split(",") if x.strip()] if g else ["**"]))
    for f in sorted((root / ".github" / "instructions").glob("*.instructions.md")):
        g = re.search(r"(?m)^applyTo:\s*(.+)$", _read(f))
        tool_files.append((f, [x.strip(" '\"") for x in g.group(1).split(",") if x.strip()] if g else ["**"]))
    for f, paths in tool_files:
        if not f.is_file():
            continue
        text = FACTORY_BLOCK.sub(lambda m: "\n" * m.group(0).count("\n"), _read(f))   # keep line numbers
        coverage["read"].append(rel(f))
        found += extract(text, rel(f), "tool-rules", paths)
    return found, coverage


def candidate_id(c: dict) -> str:
    return "D-" + hashlib.sha256(norm(c["text"]).encode()).hexdigest()[:8]
