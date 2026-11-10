#!/usr/bin/env python3
"""
Moduł `authz` tf analyze, piętro 0 (bez modelu): endpointy zmieniające dane (POST/PUT/PATCH/DELETE) bez widocznego
sprawdzenia uprawnień po stronie serwera. Ukrycie przycisku w UI nie jest zabezpieczeniem — serwer musi sprawdzić
uprawnienie przy każdej operacji (be-auth-security, be-business-app-patterns).

  python3 scan.py --root <repo> [--files a,b]     # JSON Lines na stdout (kontrakt: .tf/factory/analyze.py)

Rozpoznaje: Express/podobne (`router.post(…)` bez middleware'u uprawnień i bez `router.use(auth…)` w pliku), NestJS
(`@Post`/`@Put`/`@Patch`/`@Delete` bez `@UseGuards`/`@Roles` na metodzie ani klasie), Next.js route handlers
(`export function POST/PUT/PATCH/DELETE` bez wywołania sprawdzającego sesję lub uprawnienie), FastAPI
(`@router.post(…)` bez `Depends(…)` uwierzytelniającego w sygnaturze ani `dependencies=` routera), Spring
(`@PostMapping`… bez `@PreAuthorize`/`@Secured`/`@RolesAllowed`). To heurystyka: znalezienie = „sprawdź”, nie dowód
— uprawnienie może być sprawdzane w warstwie, której skaner nie widzi (bramka sieciowa, globalny filtr). Testy
i dokumentacja są pomijane. Tylko biblioteka standardowa.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
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
# Nazwy, po których rozpoznajemy sprawdzenie tożsamości lub uprawnienia (middleware, guard, zależność, wywołanie).
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
    print(json.dumps({"rule": "write-without-authz", "title": f"endpoint zmieniający dane bez sprawdzenia uprawnień "
                      f"({framework})", "file": rel, "line": line, "snippet": snippet.strip()[:160],
                      "severity": "wysoka", "confidence": 0.6,
                      "evidence": "brak widocznego middleware'u, guarda lub zależności sprawdzającej uprawnienie",
                      "basis": "OWASP API1/API5 (BOLA, BFLA), CWE-862 (brak autoryzacji)",
                      "suggestion": "sprawdzaj uprawnienie na serwerze przy tej operacji (middleware, guard, "
                                    "zależność); jeśli robi to warstwa wyżej — opisz to w kodzie i oznacz w raporcie"},
                     ensure_ascii=False))


def _decorator_blocks(lines: list[str]):
    """Bloki dekoratorów/adnotacji: (indeks pierwszej linii, lista linii bloku) przed deklaracją."""
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
        args = head.split(",", 1)[1] if "," in head else ""   # pierwszy argument to ścieżka
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
