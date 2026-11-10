#!/usr/bin/env python3
"""
Moduł `data-classification` tf analyze, piętro 0 (bez modelu): szkic inwentarza danych osobowych i pilnowanie,
żeby pole osobowe nie powstawało bez klasy (arch-privacy-compliance, references/lad-danych.md).

  python3 scan.py --root <repo> [--files a,b]     # JSON Lines na stdout (kontrakt: .tf/factory/analyze.py)

Reguły:
- `pii-field-unclassified` — pole o nazwie typowej dla danych osobowych (e-mail, telefon, PESEL, IBAN, data
  urodzenia, imię, nazwisko, adres, IP, dokument tożsamości, zdrowie; nazwy angielskie i polskie, camelCase
  i snake_case) w migracji SQL, `schema.prisma`, modelu Django/SQLAlchemy, encji TypeORM lub JPA, bez znacznika klasy
  (komentarz `pii`, `confidential`, `klasa:` itp. w tej samej linii albo w liniach komentarza lub adnotacji tuż nad
  polem, `COMMENT ON COLUMN … 'pii'`) i bez wiersza w tabeli inwentarza (`docs/**/data-inventory*.md`,
  `docs/**/privacy.md`, `docs/**/inwentarz*.md`);
- `pii-in-logs` — logger, `console.*` albo `print` z identyfikatorem osobowym w argumentach;
- `pii-to-analytics` — wywołanie narzędzia analityki z identyfikatorem osobowym.
W argumentach liczą się wyrażenia, a nie treść napisów (interpolacje `${…}` i f-stringi tak). Wywołania funkcji
maskujących lub skracających (`mask…`, `hash…`, `hmac…`, `redact…`, `pseudonym…`) nie są zgłaszane. To heurystyka:
nazwa pola nie dowodzi, że są w nim dane osobowe, a pole o niewinnej nazwie (`notes`, `payload`) może je mieć.
Znalezienie = „sprawdź i nadaj klasę”. Testy i dokumentacja są pomijane. Tylko biblioteka standardowa.
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
CODE_EXT = JS_EXT | {".py", ".java", ".kt"}

# Nazwy po normalizacji (małe litery, bez `_` i `-`): angielskie i polskie.
PII = {
    "email", "emailaddress", "mail", "phone", "phonenumber", "telephone", "mobile", "mobilephone", "mobilenumber",
    "telefon", "nrtelefonu", "numertelefonu", "pesel", "iban", "accountnumber", "bankaccount", "nrkonta",
    "numerkonta", "cardnumber", "creditcard", "birthdate", "dateofbirth", "dob", "birthday", "dataurodzenia",
    "firstname", "lastname", "surname", "fullname", "givenname", "familyname", "imie", "nazwisko",
    "address", "streetaddress", "homeaddress", "street", "adres", "ulica", "postalcode", "postcode", "zipcode",
    "kodpocztowy", "ipaddress", "clientip", "remoteip", "idcard", "idnumber", "passport", "passportnumber",
    "nrdowodu", "dowodosobisty", "ssn", "nationalid", "taxid", "diagnosis", "healthstatus", "medicalhistory",
}
MARK = re.compile(r"\bpii\b|personal[ _]?data|dane osobowe|\bconfidential\b|\bsensitive\b|\bpoufne\b|"
                  r"\bklasa\s*[:=]|\bclassification\b|@(Pii|Sensitive|PersonalData)\b", re.I)
COMMENT_LINE = re.compile(r"^\s*(--|//|#|/\*|\*|@)")
INVENTORY = re.compile(r"(data-inventory[^/]*|privacy|inwentarz[^/]*)\.md$", re.I)
MASKED = re.compile(r"\b\w*(mask|hash|hmac|redact|pseudonym|anonymi[sz]e|sha256|truncate)\w*\s*\([^()]*\)", re.I)

SQL_KEYWORDS = {"primary", "constraint", "foreign", "unique", "check", "index", "key", "create", "references"}
SQL_COLUMN = re.compile(r"^\s*[`\"\[]?(\w+)[`\"\]]?\s+[A-Za-z]")
SQL_ADD = re.compile(r"\bADD\s+(?:COLUMN\s+)?(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?(\w+)", re.I)
SQL_COMMENT_ON = re.compile(r"COMMENT\s+ON\s+COLUMN\s+[\w.\"`]*?\.?[`\"]?(\w+)[`\"]?\s+IS\s+'([^']*)'", re.I)
PRISMA_FIELD = re.compile(r"^\s*(\w+)\s+[A-Z]\w*")
PY_FIELD = re.compile(r"^\s*(\w+)\s*(?::\s*[^=]+)?=\s*(?:models\.\w*Field|(?:db\.|sa\.)?Column|mapped_column)\(|"
                      r"^\s*(\w+)\s*:\s*Mapped\[")
TS_FIELD = re.compile(r"^\s*(?:(?:public|private|protected|readonly)\s+)*(\w+)[!?]?\s*:\s*[\w\[\]<>|. ]+;")
JAVA_FIELD = re.compile(r"^\s*(?:(?:private|protected|public|final)\s+)+[\w<>\[\], ]+?\s+(\w+)\s*(?:=[^;]*)?;")
KT_FIELD = re.compile(r"^\s*(?:(?:private|protected|public)\s+)?va[lr]\s+(\w+)\s*:")

LOG_CALL = re.compile(r"\b(?:console\.(?:log|info|warn|error|debug|trace)|(?:this\.|self\.)?(?:logger|log|logging|"
                      r"LOG|LOGGER|_logger|_log)\.(?:info|debug|warn|warning|error|trace|log|exception|critical|"
                      r"fatal)|print|println|System\.(?:out|err)\.println)\s*\(")
ANALYTICS_CALL = re.compile(r"\b(?:analytics|segment|mixpanel|posthog|amplitude|rudderanalytics|heap)\."
                            r"(?:track|identify|capture|page|logEvent|people\.set|setUserProperties)\s*\(|"
                            r"\bgtag\s*\(|\bdataLayer\.push\s*\(")
STRING = re.compile(r"([fFrRbBuU]{0,2})(\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*')|`(?:[^`\\]|\\.)*`", re.S)


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def is_pii(name: str) -> bool:
    n = norm(name)
    return n in PII or (n[:3] in ("get", "set") and n[3:] in PII)


def emit(rule: str, rel: str, line: int, snippet: str, title: str, severity: str, evidence: str,
         suggestion: str) -> None:
    print(json.dumps({"rule": rule, "title": title, "file": rel, "line": line, "snippet": snippet.strip()[:160],
                      "severity": severity, "confidence": 0.5 if rule == "pii-field-unclassified" else 0.6,
                      "evidence": evidence, "basis": "RODO art. 5 ust. 1 lit. c i f, art. 25, art. 30, art. 32",
                      "suggestion": suggestion}, ensure_ascii=False))


# ---- pola w schematach i modelach -------------------------------------------------------------------------------

def marked(lines: list[str], i: int) -> bool:
    if MARK.search(lines[i]):
        return True
    j = i - 1
    while j >= 0 and i - j <= 3 and COMMENT_LINE.match(lines[j]):
        if MARK.search(lines[j]):
            return True
        j -= 1
    return False


def schema_fields(rel: str, text: str) -> list[tuple[int, str]]:
    """(indeks linii, nazwa pola) dla plików ze schematem albo modelem danych."""
    lines, out, ext = text.splitlines(), [], Path(rel).suffix.lower()
    if ext == ".sql":
        in_table = False
        for i, line in enumerate(lines):
            code = line.split("--", 1)[0]
            if re.search(r"\bCREATE\s+TABLE\b", code, re.I):
                in_table = True
                continue
            if in_table:
                m = SQL_COLUMN.match(code)
                if m and m.group(1).lower() not in SQL_KEYWORDS:
                    out.append((i, m.group(1)))
                if re.search(r"\)\s*;", code):
                    in_table = False
            for m in SQL_ADD.finditer(code):
                if m.group(1).lower() != "constraint":
                    out.append((i, m.group(1)))
    elif ext == ".prisma":
        in_model = False
        for i, line in enumerate(lines):
            if re.match(r"^\s*model\s+\w+\s*\{", line):
                in_model = True
            elif in_model and line.strip().startswith("}"):
                in_model = False
            elif in_model and (m := PRISMA_FIELD.match(line)):
                out.append((i, m.group(1)))
    elif ext == ".py":
        for i, line in enumerate(lines):
            if m := PY_FIELD.match(line):
                out.append((i, m.group(1) or m.group(2)))
    elif ext in JS_EXT and re.search(r"@Entity\s*\(", text):
        start = text[:text.index("@Entity")].count("\n")
        for i, line in enumerate(lines[start:], start):
            if m := TS_FIELD.match(line):
                out.append((i, m.group(1)))
    elif ext in (".java", ".kt") and re.search(r"@Entity\b", text):
        pat = JAVA_FIELD if ext == ".java" else KT_FIELD
        for i, line in enumerate(lines):
            if (m := pat.match(line)) and "static" not in line:
                out.append((i, m.group(1)))
    return out


def inventory_names(root: Path) -> set[str]:
    names: set[str] = set()
    docs = [d for d in (root / "docs", root / "doc") if d.is_dir()]
    for d in docs:
        for dp, dns, fns in os.walk(d):
            dns[:] = [x for x in dns if x not in SKIP_DIRS]
            for f in fns:
                if not INVENTORY.search(f):
                    continue
                try:
                    text = (Path(dp) / f).read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                for line in text.splitlines():
                    if line.lstrip().startswith("|"):
                        names |= {norm(t) for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", line)}
    return names


# ---- logi i analityka -------------------------------------------------------------------------------------------

def call_args(text: str, start: int) -> str:
    depth, i = 1, start
    while i < len(text) and depth and i - start < 600:
        depth += {"(": 1, ")": -1}.get(text[i], 0)
        i += 1
    return text[start:i - 1]


def expressions(args: str) -> str:
    """Argumenty bez treści napisów; interpolacje `${…}` i pola f-stringów zostają."""
    kept: list[str] = []

    def repl(m: re.Match) -> str:
        whole = m.group(0)
        if whole.startswith("`"):
            kept.extend(re.findall(r"\$\{([^}]*)\}", whole))
        elif "f" in (m.group(1) or "").lower():
            kept.extend(re.findall(r"\{([^{}]*)\}", whole))
        return " "

    rest = STRING.sub(repl, args)
    inner = STRING.sub(" ", " ".join(kept))  # napisy zagnieżdżone w interpolacji to też tylko tekst
    return MASKED.sub(" ", rest + " " + inner)


def scan_calls(rel: str, text: str) -> None:
    for pat, rule, title, sev, sugg in (
            (LOG_CALL, "pii-in-logs", "dane osobowe w logu", "wysoka",
             "loguj identyfikator techniczny albo pseudonim (HMAC) zamiast danej; logi z danymi osobowymi mają "
             "klasę zbioru i retencję"),
            (ANALYTICS_CALL, "pii-to-analytics", "dane osobowe wysyłane do analityki", "wysoka",
             "wysyłaj pseudonim (HMAC) albo agregat; dostawca analityki to procesor z umową powierzenia")):
        for m in pat.finditer(text):
            expr = expressions(call_args(text, m.end()))
            hits = sorted({t for t in re.findall(r"[A-Za-z_]\w*", expr) if is_pii(t)})
            if hits:
                line = text[:m.start()].count("\n")
                emit(rule, rel, line + 1, text.splitlines()[line], f"{title}: {', '.join(hits)}", sev,
                     f"identyfikator osobowy w argumentach wywołania: {', '.join(hits)}", sugg)


# ---- przebieg ---------------------------------------------------------------------------------------------------

def list_files(root: Path) -> list[str]:
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root.resolve():
        r = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        return [f for f in r.stdout.splitlines() if f and not set(Path(f).parts) & SKIP_DIRS
                and not f.startswith(FACTORY_OWNED)]
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        out += [str((Path(dp) / f).relative_to(root)) for f in fns]
    return sorted(out)


def scan(root: Path, files: list[str]) -> None:
    inventory = inventory_names(root)
    texts: dict[str, str] = {}
    for rel in files:
        rel = rel.replace(os.sep, "/")
        p = root / rel
        ext = p.suffix.lower()
        if TEST_OR_DOC.search(rel) or ext not in CODE_EXT | {".sql", ".prisma"} or not p.is_file() \
                or p.stat().st_size > 1_000_000:
            continue
        try:
            texts[rel] = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    commented = {norm(m.group(1)) for rel, t in texts.items() if rel.endswith(".sql")
                 for m in SQL_COMMENT_ON.finditer(t) if MARK.search(m.group(2))}
    for rel, text in texts.items():
        lines = text.splitlines()
        for i, name in schema_fields(rel, text):
            if is_pii(name) and not marked(lines, i) and norm(name) not in inventory | commented:
                emit("pii-field-unclassified", rel, i + 1, lines[i], f"pole z danymi osobowymi bez klasy: {name}",
                     "średnia", "nazwa pola typowa dla danych osobowych; brak znacznika klasy i wpisu w inwentarzu",
                     "nadaj klasę przy polu (komentarz `pii` lub adnotacja) i dopisz wiersz do "
                     "docs/project/04-architecture/data-inventory.md (klasa, cel, retencja, właściciel)")
        if Path(rel).suffix.lower() in CODE_EXT:
            scan_calls(rel, text)


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
