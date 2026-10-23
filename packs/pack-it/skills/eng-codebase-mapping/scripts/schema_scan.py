#!/usr/bin/env python3
"""
Schemat danych z kodu (rekonstrukcja projektu, model domeny): tabele, kolumny, ograniczenia i powiązania z migracji SQL
(w tym Flyway `V*__*.sql`) oraz z encji JPA (`@Entity`) i EF Core (`DbSet<T>`, atrybuty) — każde z miejscem plik:linia.
Ograniczenia (NOT NULL, UNIQUE, CHECK, długość, walidacja) to kandydaci na reguły biznesowe. Tylko biblioteka
standardowa; kodu nie uruchamia.

  python3 schema_scan.py <repo>          # tekst
  python3 schema_scan.py <repo> --json   # pełny wynik

Zgrubnie: parser SQL czyta CREATE TABLE i ALTER TABLE ADD COLUMN/CONSTRAINT, nie wykonuje migracji; Liquibase XML/YAML
i ORM-y bez adnotacji (np. konfiguracja Fluent API) — do unknowns.
"""
from __future__ import annotations

import json
import os
import re
import sys

SKIP = {"node_modules", "vendor", "dist", "build", "target", "out", "bin", "obj", ".git", "__pycache__", ".venv", "venv"}
SQL_COMMENT = re.compile(r"--[^\n]*")
IDENT = r"[\"`\[]?(\w+)[\"`\]]?"


def walk(root: str):
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in SKIP and not d.startswith("."))
        for f in sorted(fn):
            yield os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")


def read(root: str, p: str) -> str:
    try:
        with open(os.path.join(root, p), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def split_top(body: str) -> list[tuple[str, int]]:
    """Elementy listy w nawiasie CREATE TABLE rozdzielone przecinkami na poziomie 0, z przesunięciem w tekście."""
    out, depth, start = [], 0, 0
    for i, ch in enumerate(body):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append((body[start:i], start))
            start = i + 1
    out.append((body[start:], start))
    return out


def col_constraints(spec: str) -> tuple[list[str], list[str]]:
    s = spec.upper()
    cons = [c for c, rx in (("primary key", r"PRIMARY\s+KEY"), ("not null", r"NOT\s+NULL"), ("unique", r"\bUNIQUE\b"))
            if re.search(rx, s)]
    m = re.search(r"\bCHECK\s*(\(.*\))", spec, re.I | re.S)
    if m:
        cons.append("check " + re.sub(r"\s+", " ", m.group(1)))
    refs = re.findall(r"REFERENCES\s+" + IDENT, spec, re.I)
    return cons, refs


def sql_scan(root: str, p: str, tables: dict, rules: list) -> None:
    raw = read(root, p)
    text = SQL_COMMENT.sub(lambda m: " " * len(m.group(0)), raw)
    for m in re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\w+\.)?" + IDENT + r"\s*\(", text, re.I):
        name, start = m.group(1).lower(), m.end()
        depth, i = 1, start
        while i < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        t = tables.setdefault(name, {"name": name, "source": "sql", "at": f"{p}:{line_of(text, m.start())}",
                                     "columns": [], "references": []})
        for item, off in split_top(text[start:i - 1]):
            stripped = item.strip()
            if not stripped:
                continue
            pos = start + off + (len(item) - len(item.lstrip()))
            head = stripped.split()[0].upper()
            if head in ("PRIMARY", "UNIQUE", "CHECK", "CONSTRAINT", "FOREIGN", "INDEX", "KEY"):
                refs = re.findall(r"REFERENCES\s+" + IDENT, stripped, re.I)
                t["references"] += [r.lower() for r in refs if r.lower() not in t["references"]]
                rules.append({"table": name, "rule": re.sub(r"\s+", " ", stripped), "at": f"{p}:{line_of(text, pos)}"})
                continue
            cm = re.match(IDENT + r"\s+([\w]+(?:\s*\([^)]*\))?)", stripped)
            if not cm:
                continue
            cons, refs = col_constraints(stripped)
            t["columns"].append({"name": cm.group(1), "type": cm.group(2), "constraints": cons,
                                 "at": f"{p}:{line_of(text, pos)}"})
            t["references"] += [r.lower() for r in refs if r.lower() not in t["references"]]
            rules += [{"table": name, "rule": f"{cm.group(1)}: {c}", "at": f"{p}:{line_of(text, pos)}"}
                      for c in cons if c.startswith("check")]
    for m in re.finditer(r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:\w+\.)?" + IDENT + r"\s+ADD\s+(COLUMN\s+|CONSTRAINT\s+)?([^;]+);",
                         text, re.I):
        name, kind, rest = m.group(1).lower(), (m.group(2) or "").strip().upper(), m.group(3).strip()
        at = f"{p}:{line_of(text, m.start())}"
        t = tables.setdefault(name, {"name": name, "source": "sql", "at": at, "columns": [], "references": []})
        refs = re.findall(r"REFERENCES\s+" + IDENT, rest, re.I)
        t["references"] += [r.lower() for r in refs if r.lower() not in t["references"]]
        if kind == "CONSTRAINT" or rest.split()[0].upper() in ("PRIMARY", "UNIQUE", "CHECK", "FOREIGN"):
            rules.append({"table": name, "rule": re.sub(r"\s+", " ", rest), "at": at})
            continue
        cm = re.match(IDENT + r"\s+([\w]+(?:\s*\([^)]*\))?)", rest)
        if cm:
            cons, _ = col_constraints(rest)
            t["columns"].append({"name": cm.group(1), "type": cm.group(2), "constraints": cons, "at": at})


ANNOT_JPA = [("not null", r"@NotNull\b|@NotBlank\b|@Column\([^)]*nullable\s*=\s*false"),
             ("unique", r"@Column\([^)]*unique\s*=\s*true"), ("primary key", r"@Id\b"), ("email", r"@Email\b")]


def jpa_scan(root: str, p: str, tables: dict) -> None:
    text = read(root, p)
    if not re.search(r"^\s*@Entity\b", text, re.M):
        return
    cls = re.search(r"\bclass\s+(\w+)", text)
    if not cls:
        return
    tm = re.search(r"@Table\s*\(\s*name\s*=\s*\"(\w+)\"", text)
    name = tm.group(1) if tm else cls.group(1)
    t = tables.setdefault(name, {"name": name, "source": "jpa", "at": f"{p}:{line_of(text, cls.start())}",
                                 "columns": [], "references": []})
    pending, start = [], cls.end()
    for m in re.finditer(r"(@\w+(?:\([^)]*\))?)|\b(?:private|protected|public)\s+([\w<>, ?]+?)\s+(\w+)\s*[;=]",
                         text[start:]):
        if m.group(1):
            pending.append(m.group(1))
            continue
        typ, field, ann = m.group(2), m.group(3), " ".join(pending)
        pending = []
        if re.search(r"@(ManyToOne|OneToOne|OneToMany|ManyToMany)\b", ann):
            target = re.sub(r".*<\s*(\w+)\s*>.*", r"\1", typ)
            if target not in t["references"]:
                t["references"].append(target)
            continue
        cons = [c for c, rx in ANNOT_JPA if re.search(rx, ann)]
        size = re.search(r"@Size\([^)]*max\s*=\s*(\d+)", ann) or re.search(r"@Column\([^)]*length\s*=\s*(\d+)", ann)
        if size:
            cons.append(f"max {size.group(1)}")
        t["columns"].append({"name": field, "type": typ, "constraints": cons,
                             "at": f"{p}:{line_of(text, start + m.start())}"})


def ef_scan(root: str, cs_files: list[str], tables: dict) -> None:
    entities = set()
    for p in cs_files:
        entities |= set(re.findall(r"\bDbSet<(\w+)>", read(root, p)))
    for p in cs_files:
        text = read(root, p)
        cls = re.search(r"\bclass\s+(\w+)", text)
        if not cls or cls.group(1) not in entities:
            continue
        tm = re.search(r"\[Table\(\"(\w+)\"", text)
        name = tm.group(1) if tm else cls.group(1)
        t = tables.setdefault(name, {"name": name, "source": "ef", "at": f"{p}:{line_of(text, cls.start())}",
                                     "columns": [], "references": []})
        for m in re.finditer(r"((?:\[[^\]]+\]\s*)*)public\s+([\w<>?]+)\s+(\w+)\s*\{\s*get;", text):
            attrs, typ, prop = m.group(1), m.group(2), m.group(3)
            simple = typ.rstrip("?") in ("int", "long", "string", "decimal", "bool", "DateTime", "Guid", "double")
            if not simple and not attrs:
                if typ not in t["references"]:
                    t["references"].append(typ)
                continue
            cons = [c for c, rx in (("primary key", r"\bKey\b"), ("required", r"\bRequired\b")) if re.search(rx, attrs)]
            ml = re.search(r"MaxLength\((\d+)\)|StringLength\((\d+)", attrs)
            if ml:
                cons.append(f"max {ml.group(1) or ml.group(2)}")
            t["columns"].append({"name": prop, "type": typ, "constraints": cons, "at": f"{p}:{line_of(text, m.start())}"})


def scan(root: str) -> dict:
    tables, rules = {}, []
    paths = list(walk(root))
    for p in paths:
        if p.endswith(".sql"):
            sql_scan(root, p, tables, rules)
        elif p.endswith(".java"):
            jpa_scan(root, p, tables)
    ef_scan(root, [p for p in paths if p.endswith(".cs")], tables)
    for t in tables.values():
        rules += [{"table": t["name"], "rule": f"{c['name']}: {k}", "at": c["at"]}
                  for c in t["columns"] if t["source"] != "sql" for k in c["constraints"] if k != "primary key"]
    return {"root": os.path.abspath(root), "tables": sorted(tables.values(), key=lambda t: t["name"]), "rules": rules}


def render(r: dict) -> str:
    L = [f"Tabele i encje: {len(r['tables'])}; kandydaci na reguły: {len(r['rules'])}"]
    for t in r["tables"]:
        refs = f" → {', '.join(t['references'])}" if t["references"] else ""
        L.append(f"  - {t['name']} ({t['source']}, {t['at']}){refs}: " +
                 ", ".join(c["name"] + (f" [{'; '.join(c['constraints'])}]" if c["constraints"] else "") for c in t["columns"]))
    L.append("Reguły (ograniczenia) z miejscem:")
    L += [f"  - {x['table']}: {x['rule']} — {x['at']}" for x in r["rules"]]
    L.append("Ograniczenia to kandydaci na reguły biznesowe — potwierdź znaczenie w kodzie i u ludzi.")
    return "\n".join(L)


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if args[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    if len(args) != 1 or not os.path.isdir(args[0]):
        print(f"✗ podaj katalog repozytorium (jest: {args})", file=sys.stderr)
        return 2
    r = scan(args[0])
    print(json.dumps(r, ensure_ascii=False, indent=2) if as_json else render(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
