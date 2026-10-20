#!/usr/bin/env python3
"""
Audyt skilli: bezpieczeństwo (zwłaszcza skilli z obcych źródeł) i zalecenia Anthropic dla dobrych skilli.
Bez modelu, bez sieci, tylko biblioteka standardowa — audyt czyta pliki, niczego nie uruchamia.

  python3 factory/skill_audit.py <katalog-skilla | katalog-ze-skillami> [--json] [--strict]

Kody wyjścia: 2 — są ustalenia wysokiej wagi (nie instaluj bez wyjaśnienia), 1 — średniej wagi (albo niskiej
z --strict), 0 — brak. Audyt automatyczny NIE zastępuje przeczytania SKILL.md i każdego skryptu przez człowieka:
wykrywa typowe wzorce, a nie każdą złośliwość.

Bezpieczeństwo (Anthropic: „Review all files bundled in the Skill … unexpected network calls, file access patterns,
or operations that don't match the Skill's stated purpose”):
  high    prompt-injection, curl-pipe-shell, secret-access, network-undocumented, hidden-unicode
  medium  dynamic-exec, broad-allowed-tools, shell-injection (!`…` uruchamiane przy wczytaniu), frontmatter-hooks,
          missing-file (skill obiecuje plik, którego nie ma), long-base64, binary-file, name-invalid,
          description-missing, description-too-long, xml-in-frontmatter
  low     network (udokumentowana), description-no-when, no-examples, body-too-long, ref-no-toc, ref-nested, ref-ambiguous, pycache,
          windows-path, vague-name, suppressed
Skrypt łączący się z siecią musi to deklarować w SKILL.md wprost: „Sieć: … (dokąd i co wysyła)”.
Linia z komentarzem `audit-ok` jest pomijana, ale każde takie pominięcie trafia do raportu jako `suppressed` —
w skillu z obcego źródła traktuj je jak czerwoną flagę.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TEXT_EXT = {".md", ".txt", ".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".json", ".yaml", ".yml", ".toml",
            ".ps1", ".rb", ".pl", ".html"}
SCRIPT_EXT = {".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".ps1", ".rb", ".pl"}
BINARY_EXT = {".exe", ".dll", ".so", ".dylib", ".bin", ".jar", ".class", ".pyc", ".com", ".msi", ".scr"}
SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}

INJECTION_RE = re.compile(
    r"(ignore|disregard)\s+(all\s+|any\s+)?(previous|prior|above|earlier)\s+(instructions|rules|messages)"
    r"|zignoruj\s+(wszystkie\s+|wcześniejsze\s+|poprzednie\s+)+(instrukcje|polecenia|zasady)"
    r"|nie\s+(mów|informuj|wspominaj|pokazuj)\w*\s+(o\s+tym\s+)?użytkownik"
    r"|do\s+not\s+(tell|inform|mention\s+this\s+to|show\s+this\s+to)\s+the\s+user"
    r"|without\s+(telling|asking|notifying)\s+the\s+user|bez\s+(wiedzy|pytania|zgody)\s+użytkownika"
    r"|you\s+are\s+now\s+(in\s+)?(developer|unrestricted|jailbreak)|jesteś\s+teraz\s+bez\s+ograniczeń",
    re.I)
CURL_SH_RE = re.compile(r"\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba|z|k)?sh\b|\$\(\s*(curl|wget)\b"
                        r"|base64\s+(-d|--decode)[^\n|]*\|\s*(ba)?sh|iex\s*\(\s*(iwr|irm|new-object\s+net\.webclient)",
                        re.I)
SECRET_RE = re.compile(r"\.ssh/|id_rsa|id_ed25519|\.aws/credentials|\.kube/config|\.docker/config\.json|\.netrc"
                       r"|/etc/shadow|\.git-credentials|open\([^)\n]*['\"][^'\"]*\.env['\"]|Keychain|login\.keychain",
                       re.I)
NETWORK_RE = re.compile(r"urllib\.request|urlopen\(|\brequests\.(get|post|put|patch|delete|request|Session)\b"
                        r"|http\.client|socket\.socket|\bhttpx\b|\baiohttp\b|\bfetch\(|\baxios\b|XMLHttpRequest"
                        r"|\b(curl|wget|nc|ncat|scp|rsync|ftp)\s|Invoke-WebRequest|Invoke-RestMethod|\bsmtplib\b")
EXEC_RE = re.compile(r"(?<![\w.])eval\s*\(|(?<![\w.])exec\s*\(|os\.system\s*\(|shell\s*=\s*True|new\s+Function\s*\("
                     r"|pickle\.loads?\s*\(|marshal\.loads\s*\(|yaml\.load\s*\((?![^)\n]*SafeLoader)|child_process"
                     r"|__import__\s*\(\s*['\"]os|Invoke-Expression|\bIEX\b")
HIDDEN_RE = re.compile("[‪-‮⁦-⁩​-‍⁠­]")
BASE64_RE = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")
URL_HOST_RE = re.compile(r"https?://([A-Za-z0-9.-]+)")
WHEN_RE = re.compile(r"\b(użyj|używaj|gdy|kiedy|przy\s|use\s+when|use\s+this\s+when|when\s+the\s+user|when\s+working)",
                     re.I)
VAGUE_PARTS = {"helper", "helpers", "utils", "util", "tools", "tool", "misc", "stuff", "documents", "docs", "data",
               "files", "general", "common", "productivity", "assistant"}
NETWORK_DOC_RE = re.compile(r"\b(sieć|network)\s*:", re.I)   # jawna deklaracja: „Sieć: skrypt łączy się z …”
PATH_REF_RE = re.compile(r"(?<![\w/.-])((?:scripts|references|reference|templates|assets|examples)/[\w./-]+\.[A-Za-z0-9]+)")


def finding(sev: str, code: str, file: str, line: int, msg: str) -> dict:
    return {"severity": sev, "code": code, "file": file, "line": line, "message": msg}


def split_frontmatter(text: str) -> tuple[str, str, int]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return "", text, 0
    return m.group(1), text[m.end():], m.group(0).count("\n")


def fm_value(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.*)$", fm, re.M)
    return m.group(1).strip().strip('"').strip("'") if m else None


def scan_lines(rel: str, text: str, is_script: bool, out: list[dict], suppressed: list[dict]) -> bool:
    """Zwraca True, gdy plik łączy się z siecią."""
    net = False
    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if "audit-ok" in line:
            suppressed.append(finding("low", "suppressed", rel, i, "linia pominięta komentarzem audit-ok — sprawdź ręcznie"))
            continue
        if HIDDEN_RE.search(line):
            out.append(finding("high", "hidden-unicode", rel, i,
                               "niewidoczne znaki lub znaki zmiany kierunku tekstu — mogą ukrywać treść przed człowiekiem"))
        if INJECTION_RE.search(line):
            out.append(finding("high", "prompt-injection", rel, i,
                               "polecenie omijające instrukcje lub ukrywające działanie przed użytkownikiem"))
        if CURL_SH_RE.search(line):
            out.append(finding("high", "curl-pipe-shell", rel, i, "pobieranie i wykonywanie kodu z sieci"))
        if BASE64_RE.search(line):
            out.append(finding("medium", "long-base64", rel, i, "długi ciąg base64 — możliwa zaciemniona treść"))
        if is_script:
            if SECRET_RE.search(line):
                out.append(finding("high", "secret-access", rel, i, "dostęp do plików z poświadczeniami"))
            if EXEC_RE.search(line):
                out.append(finding("medium", "dynamic-exec", rel, i,
                                   "dynamiczne wykonanie kodu lub powłoka (eval/exec/shell=True/os.system/pickle)"))
            if NETWORK_RE.search(line):
                net = True
    return net


def audit_skill(d: Path) -> dict:
    name_dir = d.name
    findings: list[dict] = []
    suppressed: list[dict] = []
    skill_md = d / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fm, body, fm_lines = split_frontmatter(text)
    name = fm_value(fm, "name") or name_dir
    desc = fm_value(fm, "description")

    # ── frontmatter (wymagania Anthropic) ──
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name) or re.search(r"anthropic|claude", name):
        findings.append(finding("medium", "name-invalid", "SKILL.md", 2,
                                "nazwa: do 64 znaków, małe litery, cyfry i myślniki, bez słów „anthropic” i „claude”"))
    parts = set(name.split("-"))
    if parts and parts <= VAGUE_PARTS:
        findings.append(finding("low", "vague-name", "SKILL.md", 2, f"ogólnikowa nazwa „{name}” — nazwij zadanie"))
    if not desc:
        findings.append(finding("medium", "description-missing", "SKILL.md", 3, "brak opisu — model nie wie, kiedy użyć skilla"))
    else:
        if len(desc) > 1024:
            findings.append(finding("medium", "description-too-long", "SKILL.md", 3, f"opis ma {len(desc)} znaków (> 1024)"))
        if not WHEN_RE.search(desc):
            findings.append(finding("low", "description-no-when", "SKILL.md", 3,
                                    "opis nie mówi, KIEDY użyć skilla (reguła wyboru: „Użyj, gdy …”)"))
    if re.search(r"<[A-Za-z][^>]*>", fm):
        findings.append(finding("medium", "xml-in-frontmatter", "SKILL.md", 1, "znaczniki XML w nagłówku"))
    allowed = fm_value(fm, "allowed-tools") or ""
    if re.search(r"Bash\(\s*\*\s*\)|(^|[\s,])Bash($|[\s,])|Bash\((curl|wget|sudo|rm)\b|WebFetch|Write\(\s*\*", allowed):
        findings.append(finding("medium", "broad-allowed-tools", "SKILL.md", 1,
                                f"allowed-tools „{allowed}” — szerokie uprawnienia bez pytania (nie zależą od zaufania do katalogu)"))
    if re.search(r"^hooks\s*:", fm, re.M):
        findings.append(finding("medium", "frontmatter-hooks", "SKILL.md", 1,
                                "skill rejestruje hooki — działają do końca sesji; przeczytaj ich polecenia"))

    # ── treść SKILL.md ──
    for i, line in enumerate(body.splitlines(), fm_lines + 1):
        if re.match(r"^\s*!`|.*\s!`[^`]+`|^```!", line) and "audit-ok" not in line:
            findings.append(finding("medium", "shell-injection", "SKILL.md", i,
                                    "polecenie !`…` wykonywane przy wczytaniu skilla, zanim zobaczy je model"))
    if body.count("\n") > 500:
        findings.append(finding("low", "body-too-long", "SKILL.md", 1,
                                f"SKILL.md ma {body.count(chr(10))} linii (> 500) — przenieś szczegóły do references/"))
    for ref in sorted(set(PATH_REF_RE.findall(body))):
        if not (d / ref).exists():
            findings.append(finding("medium", "missing-file", "SKILL.md", 1,
                                    f"skill odwołuje się do `{ref}`, którego nie ma — obiecuje coś, czego nie dostarcza"))
    if re.search(r"\b[\w.-]+\\[\w.-]+\.(py|md|sh|js|json)\b", body):
        findings.append(finding("low", "windows-path", "SKILL.md", 1, "ścieżka z ukośnikiem wstecznym — używaj „/”"))

    # ── wszystkie pliki skilla ──
    net_files = []
    all_md = body
    for p in sorted(d.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(d).as_posix()
        if p.suffix.lower() in BINARY_EXT:
            if "__pycache__" in p.parts and p.suffix.lower() == ".pyc":
                findings.append(finding("low", "pycache", rel, 0, "skompilowany cache Pythona — usuń przed instalacją lub publikacją"))
            else:
                findings.append(finding("medium", "binary-file", rel, 0, "plik binarny lub wykonywalny w skillu"))
            continue
        if p.suffix.lower() not in TEXT_EXT or p.stat().st_size > 2_000_000:
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        is_script = p.suffix.lower() in SCRIPT_EXT
        if rel == "SKILL.md":
            t_scan = text
        else:
            t_scan = t
        if scan_lines(rel, t_scan, is_script, findings, suppressed):
            net_files.append((rel, t))
        if p.suffix.lower() == ".md" and rel != "SKILL.md":
            all_md += "\n" + t
            lines = t.splitlines()
            if len(lines) > 100 and not re.search(r"spis treści|table of contents|^## contents", "\n".join(lines[:15]), re.I):
                findings.append(finding("low", "ref-no-toc", rel, 1, "plik > 100 linii bez spisu treści na początku"))
            if rel.startswith(("references/", "reference/")):
                for target in sorted(set(re.findall(r"(?<![\w/.-])((?:references?)/[\w./-]+\.md)", t))):
                    if not (d / target).exists():
                        findings.append(finding("low", "ref-ambiguous", rel, 1,
                                                f"`{target}` nie istnieje w tym skillu — przy pliku z innego skilla podaj pełną "
                                                "ścieżkę `.claude/skills/<skill>/…`"))
                    elif target not in body:
                        findings.append(finding("low", "ref-nested", rel, 1,
                                                f"`{target}` jest osiągalny tylko z innego pliku referencji — wymień go w SKILL.md "
                                                "(odwołania jeden poziom od SKILL.md)"))

    documented = bool(NETWORK_DOC_RE.search(text))
    for rel, t in net_files:
        hosts = set(URL_HOST_RE.findall(t))
        if documented:
            findings.append(finding("low", "network", rel, 0,
                                    "skrypt łączy się z siecią — opisane w SKILL.md; sprawdź, dokąd i co wysyła"))
        else:
            findings.append(finding("high", "network-undocumented", rel, 0,
                                    "skrypt łączy się z siecią, a SKILL.md tego nie opisuje"
                                    + (f" (hosty: {', '.join(sorted(hosts))})" if hosts else "")))

    if not re.search(r"^```|przykład|example|wejście:|input:", all_md, re.I | re.M):
        findings.append(finding("low", "no-examples", "SKILL.md", 1,
                                "brak przykładu — konkretne przykłady działają lepiej niż lista reguł"))

    findings += suppressed
    worst = max((SEVERITY_ORDER[f["severity"]] for f in findings), default=0)
    return {"name": name, "path": str(d), "findings": findings, "worst": worst}


def find_skills(path: Path) -> list[Path]:
    if (path / "SKILL.md").is_file():
        return [path]
    return sorted({p.parent for p in path.glob("*/SKILL.md")} | {p.parent for p in path.glob("*/*/SKILL.md")}
                  | {p.parent for p in path.glob("*/*/*/SKILL.md")})


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__)
        return 2
    path = Path(args[0]).expanduser()
    skills = [audit_skill(d) for d in find_skills(path)]
    worst = max((s["worst"] for s in skills), default=0)
    code = 2 if worst >= 3 else 1 if worst == 2 or ("--strict" in flags and worst == 1) else 0
    if "--json" in flags:
        print(json.dumps({"skills": skills, "exit": code}, ensure_ascii=False, indent=1))
        return code
    if not skills:
        print(f"Nie znaleziono SKILL.md w {path}")
        return 2
    counts = {"high": 0, "medium": 0, "low": 0}
    for s in skills:
        for f in s["findings"]:
            counts[f["severity"]] += 1
    for s in skills:
        if not s["findings"]:
            continue
        print(f"━━ {s['name']}")
        for f in sorted(s["findings"], key=lambda f: -SEVERITY_ORDER[f["severity"]]):
            mark = {"high": "✗", "medium": "⚠", "low": "·"}[f["severity"]]
            loc = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
            print(f"  {mark} [{f['severity']}] {f['code']} — {loc}: {f['message']}")
    print(f"\nSkilli: {len(skills)} · wysokiej wagi: {counts['high']} · średniej: {counts['medium']} · niskiej: {counts['low']}")
    print("Audyt automatyczny nie zastępuje przeczytania SKILL.md i każdego skryptu (zalecenie Anthropic dla skilli "
          "spoza zaufanych źródeł).")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
