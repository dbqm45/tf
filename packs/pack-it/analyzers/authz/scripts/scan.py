#!/usr/bin/env python3
"""
The `authz` module of tf analyze, tier 0 (no model): data-changing endpoints (POST/PUT/PATCH/DELETE) without a visible
server-side permission check. Hiding a button in the UI is not protection — the server must check
the permission on every operation (be-auth-security, be-business-app-patterns).

  python3 scan.py --root <repo> [--files a,b]     # JSON Lines on stdout (contract: .tf/factory/analyze.py)

Recognises: Express/similar (`router.post(…)` without a permission middleware and without `router.use(auth…)` in the file), NestJS
(`@Post`/`@Put`/`@Patch`/`@Delete` without `@UseGuards`/`@Roles` on the method or the class), Next.js route handlers
(`export function POST/PUT/PATCH/DELETE` without a call that checks the session or the permission), FastAPI
(`@router.post(…)` without an authenticating `Depends(…)` in the signature or the router's `dependencies=`), Spring
(`@PostMapping`… without `@PreAuthorize`/`@Secured`/`@RolesAllowed`). This is a heuristic: a finding = "check it", not proof
— the permission may be checked in a layer the scanner does not see (a network gateway, a global filter). Tests
and documentation are skipped. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the code page (cp1250) has no "✓", "⚠" — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage", ".venv", "venv", "__pycache__", ".tf", ".next",
             "target", "_vendor", "vendor"}
FACTORY_OWNED = (".tf/factory/", ".claude/")
TEST_OR_DOC = re.compile(r"(^|/)(tests?|__tests__|e2e|fixtures|spec|examples?|docs?)/|\.(test|spec)\.|"
                         r"(^|/)test_[^/]*$|\.(md|rst|txt|adoc)$")
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"}
# Names by which we recognise an identity or permission check (middleware, guard, dependency, call).
AUTH = re.compile(r"(auth\w*|authori[sz]\w*|require_?(user|role|admin|permission|login|scope)\w*|ensure_?\w*|"
                  r"permission\w*|is_?admin|\bcan\s*\(|guard\w*|verify_?\w*token|jwt\w*|current_?user|"
                  r"getServerSession|get_current\w*|login_required|requires_auth|@Roles|PreAuthorize|Secured|"
                  r"RolesAllowed|UseGuards|protect\w*|checkAccess|check_access|has_?role\w*)", re.I)
WRITE = r"(post|put|patch|delete)"
EXPRESS = re.compile(rf"\b(router|app|api|r)\.{WRITE}\s*\(", re.I)
EXPRESS_USE = re.compile(r"\b(router|app|api|r)\.use\s*\(([^)]*)\)")
NEXT_ROUTE = re.compile(r"(^|/)app/(.+/)?route\.[cm]?[jt]sx?$")
NEXT_HANDLER = re.compile(r"^export\s+(async\s+)?function\s+(POST|PUT|PATCH|DELETE)\b|"
                          r"^export\s+const\s+(POST|PUT|PATCH|DELETE)\s*=", re.M)
NEST_WRITE = re.compile(r"^\s*@(Post|Put|Patch|Delete)\s*\(")
SPRING_WRITE = re.compile(r"^\s*@(PostMapping|PutMapping|PatchMapping|DeleteMapping)\b|"
                          r"^\s*@RequestMapping\([^)]*RequestMethod\.(POST|PUT|PATCH|DELETE)")
FASTAPI_WRITE = re.compile(rf"^\s*@\w+\.{WRITE}\s*\(", re.I)


def emit(rel: str, line: int, snippet: str, framework: str) -> None:
    print(json.dumps({"rule": "write-without-authz", "title": f"endpoint that changes data without a permission check "
                      f"({framework})", "file": rel, "line": line, "snippet": snippet.strip()[:160],
                      "severity": "high", "confidence": 0.6,
                      "evidence": "no visible middleware, guard or dependency that checks the permission",
                      "basis": "OWASP API1/API5 (BOLA, BFLA), CWE-862 (missing authorization)",
                      "suggestion": "check the permission on the server for this operation (middleware, guard, "
                                    "dependency); if a higher layer does it, say so in the code and mark it in the report"},
                     ensure_ascii=False))


def _decorator_blocks(lines: list[str]):
    """Decorator/annotation blocks: (index of the first line, list of the block's lines) before the declaration."""
    block, start = [], 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("@"):
            if not block:
                start = i
            block.append(s)
        elif s and block:
            yield start, block, s
            block = []
        elif not s:
            continue


def scan_express(rel: str, text: str) -> None:
    lines = text.splitlines()
    file_auth = any(AUTH.search(m.group(2)) for m in EXPRESS_USE.finditer(text))
    for i, line in enumerate(lines):
        m = EXPRESS.search(line)
        if not m or file_auth:
            continue
        call = " ".join(lines[i:i + 4])[m.end():]
        head = re.split(r"=>|\bfunction\b", call, maxsplit=1)[0]
        args = head.split(",", 1)[1] if "," in head else ""   # the first argument is the path
        if not AUTH.search(args):
            emit(rel, i + 1, line, "Express")


def scan_nest(rel: str, text: str) -> None:
    lines = text.splitlines()
    class_guard = False
    for start, block, decl in _decorator_blocks(lines):
        if re.search(r"\bclass\b", decl):
            class_guard = any(re.search(r"@(UseGuards|Roles)\b", b) for b in block)
            continue
        if any(NEST_WRITE.match(b) for b in block) and not class_guard \
                and not any(re.search(r"@(UseGuards|Roles|Permissions?|Auth\w*)\b", b) for b in block):
            emit(rel, start + 1, block[0], "NestJS")


def scan_spring(rel: str, text: str) -> None:
    lines = text.splitlines()
    class_guard = False
    sec = re.compile(r"@(PreAuthorize|Secured|RolesAllowed|PostAuthorize)\b")
    for start, block, decl in _decorator_blocks(lines):
        if re.search(r"\bclass\b", decl):
            class_guard = any(sec.search(b) for b in block)
            continue
        if any(SPRING_WRITE.match(b) for b in block) and not class_guard and not any(sec.search(b) for b in block):
            emit(rel, start + 1, block[0], "Spring")


def scan_next(rel: str, text: str) -> None:
    starts = [m for m in NEXT_HANDLER.finditer(text)]
    for k, m in enumerate(starts):
        end = text.find("\nexport ", m.end())
        body = text[m.start():end if end != -1 else len(text)]
        if not AUTH.search(body):
            emit(rel, text[:m.start()].count("\n") + 1, m.group(0), "Next.js")


def scan_fastapi(rel: str, text: str) -> None:
    if re.search(r"APIRouter\([^)]*dependencies\s*=", text, re.S) and AUTH.search(
            "".join(re.findall(r"APIRouter\(([^)]*\)[^)]*)\)", text, re.S))):
        return
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not FASTAPI_WRITE.match(line):
            continue
        sig = []
        for j in range(i, min(i + 15, len(lines))):
            sig.append(lines[j])
            if lines[j].lstrip().startswith(("def ", "async def ")) and re.search(r"\)\s*(->[^:]*)?:\s*$", lines[j]):
                break
        if not AUTH.search(" ".join(sig)):
            emit(rel, i + 1, line, "FastAPI")


def list_files(root: Path) -> list[str]:
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True)
    if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root.resolve():
        r = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True)
        return [f for f in r.stdout.splitlines() if f and not set(Path(f).parts) & SKIP_DIRS
                and not f.startswith(FACTORY_OWNED)]
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        out += [str((Path(dp) / f).relative_to(root)) for f in fns]
    return sorted(out)


def scan(root: Path, files: list[str]) -> None:
    for rel in files:
        rel = rel.replace(os.sep, "/")
        p = root / rel
        if TEST_OR_DOC.search(rel) or not p.is_file() or p.stat().st_size > 1_000_000:
            continue
        ext = p.suffix.lower()
        if ext not in JS_EXT | {".py", ".java", ".kt"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if ext in JS_EXT:
            if NEXT_ROUTE.search(rel):
                scan_next(rel, text)
            elif "@Controller(" in text:
                scan_nest(rel, text)
            else:
                scan_express(rel, text)
        elif ext == ".py":
            scan_fastapi(rel, text)
        else:
            scan_spring(rel, text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--files", default="")
    a = ap.parse_args()
    root = Path(a.root)
    files = [f for f in a.files.split(",") if f] or list_files(root)
    scan(root, files)
    return 0


if __name__ == "__main__":
    sys.exit(main())
