"""Decisions (standards, rules, agreements) from the project's sources, as candidates with a quote and evidence.

Sources, in the order of the hierarchy (plan, section 4.3):
  standards  — standards skills (dna.yaml `standards`, or skills named like *standards* in .claude/skills/), their
               references/ and rules/, and the Confluence pages they link to (REST API, credentials from the
               environment, sent only to the Atlassian site);
  adr        — architecture decision records (docs/adr, docs/decisions, adr, doc/adr);
  lint       — restricted imports in ESLint configuration (`no-restricted-imports` with a message);
  doc        — README, CONTRIBUTING, docs/**/*.md;
  tool-rules — instruction files of other agents: CLAUDE.md, AGENTS.md (without the factory's generated blocks),
               .cursor/rules/*.mdc, .github/copilot-instructions.md, .github/instructions/*.instructions.md.
A decision is a list item or a rule-ID line with normative words (must, never, always, should, prefer, avoid, use…,
also Polish). No model: the quote is the line itself, evidence is `path:line` or the page URL with the fetch date.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from .docs import _html_to_text, _public

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


# ---------------------------------------------------------------- Confluence

def _confluence_auth() -> tuple[str, str] | None:
    email = next((os.environ[k] for k in ("CONFLUENCE_EMAIL", "ATLASSIAN_EMAIL", "JIRA_EMAIL", "ATLASSIAN_ADMIN_EMAIL")
                  if os.environ.get(k)), None)
    token = next((os.environ[k] for k in ("CONFLUENCE_API_TOKEN", "ATLASSIAN_API_TOKEN", "JIRA_API_TOKEN")
                  if os.environ.get(k)), None)
    return (email, token) if email and token else None


def _site_host() -> str | None:
    site = os.environ.get("ATLASSIAN_SITE") or os.environ.get("CONFLUENCE_BASE_URL") or os.environ.get("JIRA_BASE_URL")
    if not site:
        return None
    return urllib.parse.urlsplit(site if "://" in site else f"https://{site}").hostname


def confluence_page(url: str, opts: dict) -> tuple[str, str]:
    """(text, version) of a Confluence page; credentials go only to the configured Atlassian site."""
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    allowed = opts.get("confluence_host") or _site_host()
    if not opts.get("allow_private"):
        if parts.scheme != "https":
            raise ValueError("only https")
        if not (host == allowed or (allowed is None and host.endswith(".atlassian.net"))):
            raise ValueError(f"{host} is not the Atlassian site ({allowed or '*.atlassian.net'}); credentials not sent")
        if not _public(host):
            raise ValueError("not a public address")
    m = re.search(r"/pages/(\d+)", url) or re.search(r"[?&]pageId=(\d+)", url)
    if not m:
        raise ValueError("no page id in the link")
    auth = opts.get("confluence_auth") or _confluence_auth()
    if not auth:
        raise ValueError("no Confluence credentials (CONFLUENCE_API_TOKEN or JIRA_API_TOKEN, and an e-mail variable)")
    api = f"{parts.scheme}://{parts.netloc}/wiki/rest/api/content/{m.group(1)}?expand=body.storage,version"
    req = urllib.request.Request(api, headers={
        "Accept": "application/json", "User-Agent": "dna-sources",
        "Authorization": "Basic " + base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 — host checked above
        data = json.loads(r.read(MAX_PAGE_BYTES))
    html = ((data.get("body") or {}).get("storage") or {}).get("value") or ""
    return _html_to_text(html), str((data.get("version") or {}).get("number", ""))


# ---------------------------------------------------------------- collection

def _standards_skills(root: Path, config: dict) -> list[dict]:
    listed = config.get("standards") or []
    if listed:
        return [{"dir": root / s["path"], "scope": s.get("scope"), "paths": s.get("paths")}
                for s in listed if s.get("path") and (root / s["path"] / "SKILL.md").is_file()]
    base = root / ".claude" / "skills"
    if not base.is_dir():
        return []
    return [{"dir": d, "scope": _guess_scope(d.name), "paths": None} for d in sorted(base.iterdir())
            if (d / "SKILL.md").is_file() and re.search(r"standard", d.name, re.I)]


def collect(root: Path, config: dict, online: bool, today: str, opts: dict | None = None) -> tuple[list[dict], dict]:
    opts = opts or {}
    found, coverage = [], {"read": [], "skipped": []}
    rel = lambda p: p.relative_to(root).as_posix()  # noqa: E731
    # standards skills and their links
    for s in _standards_skills(root, config):
        paths = _scope_paths(s["scope"] or _guess_scope(s["dir"].name), s["paths"])
        files = [s["dir"] / "SKILL.md"] + sorted((s["dir"] / "references").glob("**/*.md")) \
            + sorted((s["dir"] / "rules").glob("**/*.md"))
        links = []
        for f in files:
            text = _read(f)
            coverage["read"].append(rel(f))
            for c in extract(text, rel(f), "standards", paths):
                c["skill"] = s["dir"].name
                found.append(c)
            links += LINK.findall(text)
        depth = int((config.get("confluence") or {}).get("max_depth", 0))  # 0: only the linked page
        for url in dict.fromkeys(links):
            if "/wiki/" not in url and "atlassian.net" not in url:
                coverage["skipped"].append({"source": url, "reason": "link outside Confluence: not followed"})
                continue
            if not online:
                coverage["skipped"].append({"source": url, "reason": "network off (learn --offline)"})
                continue
            try:
                text, version = confluence_page(url, opts)
            except Exception as e:  # noqa: BLE001 — reported, never fatal
                coverage["skipped"].append({"source": url, "reason": str(e)[:200]})
                continue
            coverage["read"].append(f"{url} (version {version})")
            for c in extract(text, f"{url} (fetched {today})", "standards", paths):
                c["skill"] = s["dir"].name
                found.append(c)
            _ = depth   # child pages: a later version (depth > 0)
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
