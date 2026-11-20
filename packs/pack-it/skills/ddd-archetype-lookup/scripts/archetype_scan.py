#!/usr/bin/env python3
"""
Archetype scan for ddd-archetype-lookup (no model, no network): finds places in a code base where a business archetype
may apply — code signals (lines that look like a known archetype smell) and domain vocabulary (files whose identifiers
use an archetype's words). The result is a list of CANDIDATES with evidence `file:line`; deciding the fit is the
model's job (the signal questions of ddd-archetypes).

  python3 .claude/skills/ddd-archetype-lookup/scripts/archetype_scan.py [--root DIR] [--files a,b] [--limit N] [--json]
                                                                        [--include-tests]

Exit codes: 0 — candidates found; 1 — no code signal and no vocabulary (or no code files); 2 — call error.
Text output: the first line is `Archetype scan: <n> code files, <m> findings, <k> archetypes`, then one section per
archetype ordered by the number of findings. `--json`: {"files_scanned", "findings", "vocabulary", "summary"}.
Skipped: test files (unless --include-tests), dependencies and build output (node_modules, dist, build, target, .venv…), factory files (.tf/, .claude/),
minified files, binary files and files larger than 1 MB. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks some characters — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

REFERENCES = ".claude/skills/ddd-archetypes/references"
MAX_BYTES = 1_000_000
VOCAB_MIN_HITS = 2       # a file counts as archetype vocabulary from this many term hits
VOCAB_FILES_SHOWN = 5    # vocabulary files listed per archetype in the text report

# Tests repeat the production code (signals and vocabulary skip them unless --include-tests); migrations and generated
# designer files only repeat the production vocabulary (signals keep them: a migration declares the column types).
TEST_PATH = re.compile(r"/(tests?|specs?|__tests__|test_?data|fixtures)/|[._-](tests?|spec)\.|/tests?_[^/]*$", re.IGNORECASE)
NOT_VOCAB = re.compile(r"/migrations?/|\.designer\.|snapshot", re.IGNORECASE)
CODE_EXT = {
    ".py", ".java", ".kt", ".kts", ".scala", ".groovy", ".cs", ".fs", ".vb", ".ts", ".tsx", ".js", ".jsx", ".mjs",
    ".cjs", ".vue", ".svelte", ".go", ".rb", ".php", ".rs", ".swift", ".dart", ".ex", ".exs", ".erl", ".clj",
    ".c", ".h", ".cpp", ".hpp", ".cc", ".m", ".sql", ".prisma", ".graphql", ".gql", ".cob", ".cbl", ".abap", ".pls",
}
SKIP_DIRS = {
    "node_modules", "dist", "build", "out", "target", ".venv", "venv", "env", "__pycache__", ".git", ".tf", ".claude",
    "vendor", "coverage", ".next", ".nuxt", ".gradle", ".idea", ".mvn", "bin", "obj", "site-packages", ".terraform",
    ".tox", ".mypy_cache", ".pytest_cache", "bower_components", "generated", "__generated__",
}

MONEY = r"(price|amount|total|cost|fee|salary|balance|payment|revenue|tax)"
# One entry per code signal. `patterns`: any match on a line is a finding. `file_requires`: the file must also contain
# this pattern somewhere. `skip_file`: files whose name matches are the modelled concept itself (the remedy, not
# the smell). `min_distinct`: the file needs that many distinct matched words before its lines count.
SIGNALS = [
    {"id": "float-money", "archetype": "quantities-and-money",
     "title": "money held in a binary floating-point type",
     "remedy": "a money value object (decimal + ISO 4217 currency), one rounding policy",
     "patterns": [rf"\b(float|double|f32|f64)\b[\s\w<>\[\],]*?\b\w*{MONEY}\w*",
                  rf"\b\w*{MONEY}\w*\s*\??\s*:\s*(number|float)\b",
                  rf"\b\w*{MONEY}\w*\s+(float|double|real)\b",
                  rf"\b\w*{MONEY}\w*\s*=\s*float\(",
                  rf"\b(float|double|parse_?float|to_?double)\(\s*[\w.]*{MONEY}"]},
    {"id": "currency-as-string", "archetype": "quantities-and-money",
     "title": "currency kept as a free string next to an amount",
     "remedy": "currency inside the money value object, validated against ISO 4217",
     "patterns": [r"\b(string|str)\s+currency\w*\b", r"\bcurrency\w*\s*\??\s*:\s*(string|str)\b",
                  r"\bcurrency\w*\s+(varchar|char|text)\b"]},
    {"id": "unit-in-name", "archetype": "quantities-and-money",
     "title": "the unit encoded in a field name, the value a bare number",
     "remedy": "a quantity value object (amount + unit); convert on read",
     "patterns": [r"\b[a-z]\w{2,}?_(kg|mg|lbs?|oz|cm|mm|km|ml|kwh|mwh|wh|pct|percent)\b",
                  r"\b[a-z]\w*?(Kg|Mg|Lbs|Cm|Mm|Km|Ml|Kwh|Mwh|Pct|Percent)\b"],
     "case_sensitive": True},
    {"id": "balance-in-place", "archetype": "value-ledger",
     "title": "a balance changed in place, without entries",
     "remedy": "transactions with entries, reversals instead of edits, the balance derived",
     "patterns": [r"\bset\s+(\w+)\s*=\s*\1\s*[+-]",
                  r"\b\w*(balance|points|credits|stock)\w*\s*[+-]=(?!\s*[\[{(])",
                  r"\.(balance|points|credits|stock)\w*\s*=\s*[\w.]*\.(balance|points|credits|stock)\w*\s*[+-]"]},
    {"id": "role-flags", "archetype": "parties-and-relationships",
     "title": "party roles as boolean flags",
     "remedy": "one party with roles and relationships",
     "patterns": [r"\bis_?(customer|supplier|vendor|client|company|person|employee|partner|lead|contractor|"
                  r"individual|organi[sz]ation)\b"]},
    {"id": "overlap-check", "archetype": "resource-holds",
     "title": "a hand-written interval overlap check",
     "remedy": "one hold model with a database guard against overlapping holds",
     "patterns": [r"start\w*\s*[<>]=?\s*[\w.]*end\w*.{0,80}(start\w*\s*[<>]=?\s*[\w.]*end|end\w*\s*[<>]=?\s*[\w.]*start)",
                  r"\b(is_?)?overlap(s|ping)?\w*\s*\("]},
    {"id": "booking-flags", "archetype": "resource-holds",
     "title": "availability as status flags on the resource",
     "remedy": "holds with an interval and a reason; availability derived from holds",
     "patterns": [r"\bis_?(reserved|booked|blocked|occupied|in_?maintenance)\b",
                  r"\b(boolean|bool)\s+(reserved|booked|occupied|blocked)\b",
                  r"\bstatus\w*\s*={1,3}\s*['\"](reserved|booked|occupied)['\"]"]},
    {"id": "wait-order-by-time", "archetype": "waiting-lists",
     "title": "waiting order taken from the creation time",
     "remedy": "an explicit priority policy, offers with a deadline",
     "patterns": [r"\border\s+by\s+\w*(created|inserted|joined|signed_?up|registered|requested)\w*",
                  r"\border_?by\(\s*['\"{]?\s*-?\w*(created|inserted|joined|registered)"],
     "file_requires": r"wait_?list|waiting|standby|reserve_?list|queue_?position"},
    {"id": "rate-literal", "archetype": "price-calculation",
     "title": "a price rule hard-coded as a literal rate",
     "remedy": "a calculator with a versioned price list; the rate as data",
     "patterns": [r"\b\w*(price|total|amount|cost|fee|net|gross)\w*\s*\*\s*\(?\s*(0?\.\d+|1\.\d+)\b",
                  r"\b\w*(discount|rebate|vat|tax_?rate|commission|markup|surcharge)\w*\s*=\s*0?\.\d*[1-9]\d*\b"]},
    {"id": "address-fields", "archetype": "places-and-zones",
     "title": "address kept as loose columns on another entity",
     "remedy": "an address value with a country template; zones as data",
     "patterns": [r"\b(street|city|zip_?code|postal_?code|post_?code|house_?number)\b"],
     "min_distinct": 2, "skip_file": r"address|location|place|geo"},
    {"id": "external-ids", "archetype": "identity-and-references",
     "title": "identifiers of other systems as loose columns",
     "remedy": "identifiers as scheme + value, unique per scheme, never reused",
     "patterns": [r"\b(legacy|external|old|crm|erp|sap|salesforce|hubspot|supplier|vendor|partner)_?(id|code|number|no)\b"]},
    {"id": "reading-overwrite", "archetype": "observations-and-measurements",
     "title": "a recorded reading or result overwritten in place",
     "remedy": "reject the wrong observation with a link to its correction; keep both",
     "patterns": [r"\bupdate\s+\w*(reading|measurement|observation|result|sample|metric)s?\s+set\b",
                  r"\b\w*(reading|measurement|observation)\w*\.(value|result|amount)\s*=(?!=)"]},
    {"id": "type-branch", "archetype": "product-definitions",
     "title": "behaviour branched on a product type literal",
     "remedy": "product definitions and features as data",
     "patterns": [r"\b\w*(product_?type|item_?type|product_?kind|variant_?type)\w*\s*(={2,3}|\.equals\()\s*['\"]",
                  r"\bswitch\s*\(\s*[\w.]*(product_?type|item_?type|product_?kind)\b"]},
]
for _s in SIGNALS:
    _s["compiled"] = [re.compile(p, 0 if _s.get("case_sensitive") else re.IGNORECASE) for p in _s["patterns"]]
    _s["requires"] = re.compile(_s["file_requires"], re.IGNORECASE) if _s.get("file_requires") else None
    _s["skip"] = re.compile(_s["skip_file"], re.IGNORECASE) if _s.get("skip_file") else None

# Domain words per archetype, matched against identifier words (camelCase and snake_case split, lowercase).
# Two-word terms are written with "_" and match adjacent words.
VOCABULARY = {
    "quantities-and-money": {"currency", "money", "exchange_rate", "unit_of_measure", "uom", "minor_units"},
    "value-ledger": {"ledger", "loyalty", "points", "credits", "wallet", "accrual", "redeem", "posting", "journal"},
    "price-calculation": {"pricing", "tariff", "discount", "rebate", "surcharge", "commission", "price_list",
                          "pricelist"},
    "parties-and-relationships": {"party", "supplier", "vendor", "counterparty", "contractor", "subsidiary",
                                  "organization", "organisation"},
    "places-and-zones": {"address", "postal", "zipcode", "zone", "latitude", "longitude", "geocode", "region"},
    "product-definitions": {"product", "sku", "variant", "catalog", "catalogue", "lot", "serial_number"},
    "option-constraints": {"configurator", "compatible", "incompatible", "compatibility", "excludes", "requires_option"},
    "resource-holds": {"booking", "reservation", "availability", "hold", "slot", "double_booking"},
    "waiting-lists": {"waitlist", "wait_list", "waiting_list", "standby", "queue_position"},
    "task-selection": {"assignment", "staffing", "allocation", "dispatch", "skills_matrix"},
    "stage-scheduling": {"milestone", "predecessor", "successor", "critical_path", "gantt", "dependency_graph"},
    "assets-and-services": {"asset", "equipment", "fleet", "maintenance"},
    "work-execution": {"work_order", "workorder", "timesheet", "job_card", "procedure", "checklist"},
    "commitments": {"contract", "agreement", "amendment", "quote", "quotation", "purchase_order", "framework_agreement"},
    "evidence-documents": {"retention", "legal_hold", "attachment", "signature", "document_version"},
    "observations-and-measurements": {"measurement", "observation", "sensor", "telemetry", "sensor_reading",
                                      "meter_reading", "lab_result", "test_result"},
    "identity-and-references": {"external_id", "legacy_id", "dedup", "deduplicate", "deduplication", "merged_into",
                                "golden_record", "master_data", "identification_scheme"},
    "production-traceability": {"bill_of_materials", "bom", "recipe", "genealogy", "recall", "traceability",
                                "production_order"},
}


def words(text: str) -> list[str]:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    return re.findall(r"[a-z0-9]+", text.lower())


def vocab_hits(text: str) -> dict[str, int]:
    ws = words(text)
    grams = ws + [f"{a}_{b}" for a, b in zip(ws, ws[1:])] + [f"{a}_{b}_{c}" for a, b, c in zip(ws, ws[1:], ws[2:])]
    hits: dict[str, int] = {}
    for g in grams:
        for arch, terms in VOCABULARY.items():
            if g in terms:
                hits[arch] = hits.get(arch, 0) + 1
    return hits


def code_files(root: Path, only: list[str] | None) -> list[Path]:
    if only:
        out = []
        for rel in only:
            p = (root / rel).resolve()
            if p.is_file():
                out.append(p)
        return sorted(out)
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if p.suffix.lower() in CODE_EXT and ".min." not in name:
                out.append(p)
    return out


def read_text(p: Path) -> str | None:
    try:
        if p.stat().st_size > MAX_BYTES:
            return None
        data = p.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace")


def scan(root: Path, only: list[str] | None, include_tests: bool = False) -> dict:
    findings, vocabulary = [], []
    files = code_files(root, only)
    for p in files:
        text = read_text(p)
        if text is None:
            continue
        rel = p.relative_to(root).as_posix()
        if not include_tests and TEST_PATH.search("/" + rel):
            continue
        lines = text.splitlines()
        for sig in SIGNALS:
            if sig["requires"] and not sig["requires"].search(text) or sig["skip"] and sig["skip"].search(p.stem):
                continue
            hits, distinct = [], set()
            for no, line in enumerate(lines, 1):
                matched = [m.group(0).lower() for rx in sig["compiled"] for m in rx.finditer(line)]
                if matched:
                    hits.append((no, line))
                    distinct.update(re.sub(r"_", "", w) for w in matched)
            if sig.get("min_distinct") and len(distinct) < sig["min_distinct"]:
                continue
            for no, line in hits:
                findings.append({"signal": sig["id"], "archetype": sig["archetype"], "file": rel, "line": no,
                                 "text": line.strip()[:120]})
        if NOT_VOCAB.search("/" + rel):
            continue
        for arch, n in vocab_hits(rel + "\n" + text).items():
            if n >= VOCAB_MIN_HITS:
                vocabulary.append({"archetype": arch, "file": rel, "hits": n})
    summary = {}
    for f in findings:
        s = summary.setdefault(f["archetype"], {"archetype": f["archetype"], "findings": 0, "vocabulary_files": 0})
        s["findings"] += 1
    for v in vocabulary:
        s = summary.setdefault(v["archetype"], {"archetype": v["archetype"], "findings": 0, "vocabulary_files": 0})
        s["vocabulary_files"] += 1
    for s in summary.values():
        s["reference"] = f"{REFERENCES}/{s['archetype']}.md"
    ordered = sorted(summary.values(), key=lambda s: (-s["findings"], -s["vocabulary_files"], s["archetype"]))
    vocabulary.sort(key=lambda v: (v["archetype"], -v["hits"], v["file"]))
    return {"files_scanned": len(files), "findings": findings, "vocabulary": vocabulary, "summary": ordered}


def text_report(data: dict, limit: int) -> str:
    out = [f"Archetype scan: {data['files_scanned']} code files, {len(data['findings'])} findings, "
           f"{len(data['summary'])} archetypes"]
    titles = {s["id"]: s for s in SIGNALS}
    for s in data["summary"]:
        arch = s["archetype"]
        out.append("")
        out.append(f"## {arch} ({s['findings']} findings, {s['vocabulary_files']} vocabulary files) — {s['reference']}")
        for sig in SIGNALS:
            if sig["archetype"] != arch:
                continue
            rows = [f for f in data["findings"] if f["signal"] == sig["id"]]
            if not rows:
                continue
            out.append(f"- {sig['id']}: {titles[sig['id']]['title']} → {sig['remedy']}")
            for f in rows[:limit]:
                out.append(f"  {f['file']}:{f['line']}  {f['text']}")
            if len(rows) > limit:
                out.append(f"  … {len(rows) - limit} more")
        vocab = [v for v in data["vocabulary"] if v["archetype"] == arch]
        if vocab:
            shown = ", ".join(f"{v['file']} ({v['hits']})" for v in vocab[:VOCAB_FILES_SHOWN])
            more = f", … {len(vocab) - VOCAB_FILES_SHOWN} more" if len(vocab) > VOCAB_FILES_SHOWN else ""
            out.append(f"- vocabulary: {shown}{more}")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Code signals and vocabulary of business archetypes (candidates only).")
    ap.add_argument("--root", default=".", help="repository root (default: the current directory)")
    ap.add_argument("--files", help="comma-separated paths relative to --root; scan only these")
    ap.add_argument("--limit", type=int, default=5, help="lines shown per signal in the text report (default 5)")
    ap.add_argument("--json", action="store_true", help="full result as JSON")
    ap.add_argument("--include-tests", action="store_true", help="also scan test files (skipped by default)")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"archetype_scan: --root {args.root} is not a directory", file=sys.stderr)
        return 2
    if args.limit < 1:
        print("archetype_scan: --limit must be at least 1", file=sys.stderr)
        return 2
    only = [x.strip() for x in args.files.split(",") if x.strip()] if args.files else None
    data = scan(root, only, args.include_tests)
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else text_report(data, args.limit), end="")
    return 0 if data["findings"] or data["vocabulary"] else 1


if __name__ == "__main__":
    sys.exit(main())
