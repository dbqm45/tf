#!/usr/bin/env python3
"""
PreToolUse (Read|Edit|Write|NotebookEdit|Grep|Glob): chroni pliki z sekretami
i konfigurację zabezpieczeń przed zmianą przez samego agenta.
"""
from __future__ import annotations

import json
import os
import re
import sys

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SECRET_PATHS = re.compile(
    r"(^|/)(\.env(\.[\w-]+)?|id_rsa|id_ed25519|credentials(\.json)?|\.npmrc|\.pypirc|\.netrc|"
    r"[\w.-]+\.(pem|key|p12|pfx|jks|tfstate(\.backup)?)|secrets?(/|$)|"
    r"\.ssh/|\.aws/|\.kube/config|\.git-credentials|\.docker/config\.json|\.config/gh/hosts\.yml|\.config/gcloud/|\.azure/)",
    re.IGNORECASE,
)
SAFE_ENV = re.compile(r"\.env\.(example|sample|template|dist)$", re.IGNORECASE)

# Samomodyfikacja zabezpieczeń wymaga zgody człowieka
GUARDRAILS = re.compile(r"(^|/)\.claude/(settings(\.local)?\.json|hooks/|cleanroom\.json)|(^|/)\.git/")

# Ekonomia kontekstu: zależności, artefakty i lockfile'e nie trafiają do okna modelu. Tu, a nie w permissions.deny,
# bo piaskownica Bash zamienia reguły Read(...) deny w zakaz odczytu dla programów (npm test, build).
CONTEXT_ANY = re.compile(r"(^|/)node_modules(/|$)")
CONTEXT_ROOT = re.compile(r"^(dist|build|coverage)(/|$)")
LOCKFILES = re.compile(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock)$")
CONTEXT_TOOLS = ("Read", "Grep", "Glob")


def project_relative(norm: str, root: str) -> str | None:
    """Ścieżka względem katalogu projektu; None, gdy leży poza nim albo katalog jest nieznany."""
    if not norm.startswith("/") and not re.match(r"^[A-Za-z]:/", norm):
        return norm[2:] if norm.startswith("./") else norm
    root = root.replace("\\", "/").rstrip("/")
    if root and norm.startswith(root + "/"):
        return norm[len(root) + 1:]
    return None


def decide(decision: str, reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": f"[guard_paths] {reason}",
    }}, ensure_ascii=False))
    sys.exit(0)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not isinstance(data, dict):   # dane spoza formatu Claude Code: decyzja, nie awaria (onFailure: block)
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
    pattern = ti.get("pattern") or ""  # Glob/Grep
    targets = [p for p in (path, pattern if tool == "Glob" else "") if p and isinstance(p, str)]
    if not isinstance(data.get("cwd"), (str, type(None))):
        data["cwd"] = None

    for p in targets:
        norm = p.replace("\\", "/")
        if SECRET_PATHS.search(norm) and not SAFE_ENV.search(norm):
            decide("deny", f"Dostęp do pliku z sekretami ({p}) jest zablokowany. Używaj zmiennych środowiskowych i plików *.example.")
        if tool in ("Edit", "Write", "NotebookEdit") and GUARDRAILS.search(norm):
            decide("ask", f"Zmiana konfiguracji zabezpieczeń lub .git ({p}) wymaga zgody człowieka.")
        if tool in CONTEXT_TOOLS:
            rel = project_relative(norm, data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", ""))
            if (CONTEXT_ANY.search(norm) or (rel is not None and CONTEXT_ROOT.search(rel))
                    or (tool == "Read" and LOCKFILES.search(norm))):
                decide("deny", f"Ekonomia kontekstu: {p} to zależności, artefakt builda lub lockfile. Szukaj konkretnego "
                               "miejsca (Grep po pliku źródłowym, grep -n nazwy paczki w lockfile'u); gdy naprawdę "
                               "potrzebujesz tego pliku, poproś człowieka.")
    sys.exit(0)


if __name__ == "__main__":
    main()
