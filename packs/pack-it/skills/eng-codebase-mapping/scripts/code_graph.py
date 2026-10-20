#!/usr/bin/env python3
"""
Graf importów kodu do mapy (kroki 2–5 skilla eng-codebase-mapping) — gdy nie ma madge, dependency-cruisera ani nx graph.
Python przez ast, TS/JS przez regex importów. Tylko biblioteka standardowa; kodu repozytorium nie uruchamia.

  python3 code_graph.py <repo>                        # punkty wejścia, pakiety, grupy, pod prąd, huby, cykle
  python3 code_graph.py <repo> --impact <plik>        # do tego zasięg zmiany pliku (2 kroki w górę + testy)
  python3 code_graph.py <repo> --focus <ścieżka>      # importy przez granicę modułu (do i od reszty repo)
  python3 code_graph.py <repo> --focus A --focus B    # tylko importy między A i B (szew pary)
  --top N (domyślnie 10) · --group-depth N (domyślnie 2; grupa z > 40% plików jest wtedy rozbijana sama) · --json (pełny wynik z listą krawędzi)

Rodzaje krawędzi: module (wykonywany przy imporcie), function (import w ciele funkcji — leniwy), type (pod
TYPE_CHECKING albo `import type` / `{ type X }`), dynamic (`import()`). Cykle runtime liczone tylko z krawędzi module;
cykle domykane dopiero przez krawędzie leniwe są osobno (closed_by). Testy, fikstury i migracje są poza grafem
produkcyjnym (ale liczą się w --impact). Barrel = plik index.* / __init__.py z samymi re-eksportami — poza hubami
i statystykami grup. Krawędzie to WYCIĄGNIĘTE z tekstu importów; DI, rejestry, kolejki, sygnały, importy po nazwie
(import_string, apps.get_model, string w settings) i HTTP między usługami graf pomija — wpisz je do unknowns.
"""
from __future__ import annotations

import ast
import collections
import json
import os
import re
import sys

SKIP_DIRS = {"node_modules", "dist", "build", "coverage", ".git", "__pycache__", ".venv", "venv", "graphify-out",
             ".next", ".nx", ".angular", "target", ".tox", ".mypy_cache", ".pytest_cache", ".tmp-map"}
TS_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".mts", ".cjs", ".cts")
KIND_RANK = {"module": 3, "dynamic": 2, "function": 1, "type": 0}
ENTRY_NAME = re.compile(r"(^|/)(main|app|server|cli|manage|wsgi|asgi|__main__|celery|celeryconf|urls|"
                        r"routes?|app\.config|app\.routes|application)\.(py|ts|tsx|js|jsx|mjs)$|(^|/)(asgi|wsgi)/__init__\.py$|"
                        r"\.routes\.(ts|js)$|Application\.java$")
MONO = ("packages", "apps", "libs", "services", "modules")


def is_test(p: str) -> bool:
    return bool(re.search(r"(^|/)(tests?|__tests__|e2e|fixtures|migrations|__mocks__)/|\.(test|spec|stories)\.|"
                          r"(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$", p))


def walk(root: str):
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(fn):
            yield os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")


def read(root: str, p: str) -> str:
    try:
        with open(os.path.join(root, p), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def add(edges: dict, s: str, t: str, kind: str) -> None:
    if s != t and KIND_RANK[kind] > KIND_RANK.get(edges[s].get(t, ""), -1):
        edges[s][t] = kind


# ---------- Python ----------
def py_modules(files: list[str]) -> dict[str, str]:
    mods = {}
    for p in files:
        m = p[:-3].replace("/", ".")
        if m.endswith(".__init__"):
            m = m[:-9]
        mods[m] = p
        if m.startswith("src."):
            mods.setdefault(m[4:], p)
    return mods


def is_type_checking(test: ast.AST) -> bool:
    """`if TYPE_CHECKING`, `if typing.TYPE_CHECKING`, `if TYPE_CHECKING is True` — bez `not`."""
    if isinstance(test, ast.UnaryOp):
        return False
    return any(isinstance(n, ast.Name) and n.id == "TYPE_CHECKING" or
               isinstance(n, ast.Attribute) and n.attr == "TYPE_CHECKING" for n in ast.walk(test))


def py_imports(tree: ast.AST):
    """(węzeł importu, rodzaj) z kontekstem: funkcja → function, if TYPE_CHECKING → type, reszta → module."""
    def visit(node, kind):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                yield child, kind
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                yield from visit(child, "type" if kind == "type" else "function")
            elif isinstance(child, ast.If) and is_type_checking(child.test):
                for n in child.body:
                    yield from visit(ast.Module(body=[n], type_ignores=[]), "type")
                for n in child.orelse:
                    yield from visit(ast.Module(body=[n], type_ignores=[]), kind)
            else:
                yield from visit(child, kind)
    yield from visit(tree, "module")


TASK_DECOS = {"task", "shared_task", "periodic_task"}
ROUTE_DECOS = {"get", "post", "put", "delete", "patch", "route", "api_route", "websocket"}
HTTP_APPS = {"FastAPI", "Flask", "APIRouter", "Blueprint", "Starlette"}
SCHEMA_CALLS = {"Schema", "build_federated_schema", "make_executable_schema"}


def call_name(node: ast.AST) -> str:
    node = node.func if isinstance(node, ast.Call) else node
    return node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else ""


def py_registries(p: str, tree: ast.AST) -> collections.Counter:
    """Wejścia z rejestrów: zadania Celery, aplikacje i trasy HTTP, schemat GraphQL, komendy Django."""
    c = collections.Counter()
    if re.search(r"/management/commands/[^/]+\.py$", p) and not p.endswith("__init__.py"):
        c["django-command"] += 1
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in n.decorator_list:
                name = call_name(d)
                if name in TASK_DECOS:
                    c["celery"] += 1
                elif name in ROUTE_DECOS and isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
                    c["http"] += 1
        elif isinstance(n, ast.Call):
            name = call_name(n)
            if name in HTTP_APPS:
                c["http"] += 1
            elif name in SCHEMA_CALLS:
                c["graphql-schema"] += 1
    return c


def py_graph(root: str, files: list[str], edges: dict, barrels: set, registries: dict | None = None) -> None:
    mods = py_modules(files)

    def target(name: str):
        while name:
            if name in mods:
                return mods[name]
            name = name.rpartition(".")[0]
        return None
    for p in files:
        try:
            tree = ast.parse(read(root, p))
        except (SyntaxError, ValueError):
            continue
        m = p[:-3].replace("/", ".")
        pkg = m[:-9] if m.endswith(".__init__") else m.rpartition(".")[0]
        for node, kind in py_imports(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            else:
                base = node.module or ""
                if node.level:
                    parts = pkg.split(".") if pkg else []
                    parts = parts[:len(parts) - (node.level - 1)] if node.level > 1 else parts
                    base = ".".join(parts + ([base] if base else []))
                names = [f"{base}.{a.name}" if f"{base}.{a.name}" in mods else base for a in node.names]
            for nm in names:
                t = target(nm)
                if t:
                    add(edges, p, t, kind)
        if registries is not None and not is_test(p):
            found = py_registries(p, tree)
            if found:
                registries[p] = found
        if p.endswith("__init__.py"):
            body = [n for n in tree.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
            if body and all(isinstance(n, (ast.Import, ast.ImportFrom)) or
                            isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and
                            "__all__" in ast.unparse(n).split("=")[0] for n in body):
                barrels.add(p)


# ---------- TS/JS ----------
FROM = re.compile(r"(?m)^[ \t]*(import|export)\s+(type\s+)?([^'\";]*?)\s*from\s*['\"]([^'\"]+)['\"]")
SIDE = re.compile(r"(?m)^[ \t]*import\s*['\"]([^'\"]+)['\"]")
DYN = re.compile(r"\bimport\(\s*['\"]([^'\"]+)['\"]\s*\)")
REQ = re.compile(r"\brequire\(\s*['\"]([^'\"]+)['\"]\s*\)")
COMMENT = re.compile(r"(?<![\w'\"*/\\])/\*.*?\*/|^[ \t]*//[^\n]*", re.S | re.M)   # // tylko do końca linii


def load_json(root: str, p: str) -> dict:
    try:
        d = json.loads(read(root, p) or "{}")
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


def ts_resolve(root: str, src: str, spec: str, aliases: dict[str, str]):
    if spec in aliases:
        return aliases[spec]
    for name, entry in aliases.items():   # @x/core/sub → katalog pakietu
        if spec.startswith(name + "/"):
            spec = os.path.relpath(os.path.join(os.path.dirname(entry), spec[len(name) + 1:]), os.path.dirname(src))
            spec = spec if spec.startswith(".") else "./" + spec
            break
    if not spec.startswith("."):
        return None
    base = os.path.normpath(os.path.join(os.path.dirname(src), spec)).replace(os.sep, "/")
    stem = re.sub(r"\.(js|mjs|cjs|jsx|ts|tsx|mts|cts)$", "", base)
    for c in [base] + [stem + e for e in TS_EXT] + [f"{stem}/index{e}" for e in TS_EXT]:
        if os.path.isfile(os.path.join(root, c)) and not c.endswith(".d.ts"):
            return c
    return None


def ts_kind(kw: str, typ: str | None, clause: str) -> str:
    if typ:
        return "type"
    c = clause.strip()
    if kw == "import" and c.startswith("{") and c.endswith("}"):
        items = [i.strip() for i in c.strip("{}").split(",") if i.strip()]
        if items and all(i.startswith("type ") for i in items):
            return "type"
    if kw == "export" and c.startswith("{") and c.endswith("}"):
        items = [i.strip() for i in c.strip("{}").split(",") if i.strip()]
        if items and all(i.startswith("type ") for i in items):
            return "type"
    return "module"


TS_REGISTRY = {"http": re.compile(r"@Controller\(|\b(?:app|router|server|fastify|api)\.(?:get|post|put|patch|delete|"
                                   r"all|route)(?:<[^>]*>)?\(\s*['\"`]/"),
               "graphql-schema": re.compile(r"@Resolver\("),
               "cron": re.compile(r"@(Cron|Interval|Timeout|Processor|Process)\(")}


def ts_graph(root: str, files: list[str], aliases: dict, edges: dict, barrels: set,
             registries: dict | None = None) -> None:
    for p in files:
        text = COMMENT.sub("", read(root, p))
        found = [(m.group(4), ts_kind(m.group(1), m.group(2), m.group(3))) for m in FROM.finditer(text)]
        found += [(m.group(1), "module") for m in SIDE.finditer(text)]
        found += [(m.group(1), "module") for m in REQ.finditer(text)]
        found += [(m.group(1), "dynamic") for m in DYN.finditer(text)]
        for spec, kind in found:
            t = ts_resolve(root, p, spec, aliases)
            if t:
                add(edges, p, t, kind)
        if registries is not None and not is_test(p):
            found = collections.Counter({k: len(rx.findall(text)) for k, rx in TS_REGISTRY.items()})
            found = +found
            if found:
                registries[p] = found
        if re.search(r"(^|/)index\.(ts|tsx|js|mjs|cjs)$", p):
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            joined = " ".join(lines)
            stmts = [s for s in re.split(r";|\n", "\n".join(lines)) if s.strip()]
            if stmts and all(re.match(r"\s*(export\s+(\*|\{|type\s)|import\s|[}\w ,]*\}?\s*from\s)", s) or
                             re.match(r"\s*[\w ,{}]*$", s) for s in stmts) and "export" in joined:
                barrels.add(p)


# ---------- pakiety i punkty wejścia ----------
def workspaces(root: str, all_files: list[str]):
    """{katalog pakietu: (nazwa, plik wejścia lub None, pliki z scripts/main/bin)}."""
    out = {}
    for p in all_files:
        if not p.endswith("package.json") or "/node_modules/" in p:
            continue
        d, base = load_json(root, p), os.path.dirname(p)
        refs = []
        for cmd in (d.get("scripts") or {}).values() if isinstance(d.get("scripts"), dict) else []:
            for tok in re.findall(r"[\w./@-]+\.(?:py|ts|tsx|js|mjs|cjs|mts)\b", str(cmd)):
                refs.append(os.path.normpath(os.path.join(base, tok)).replace(os.sep, "/"))
        bins = d.get("bin")
        for b in (bins.values() if isinstance(bins, dict) else [bins] if isinstance(bins, str) else []):
            refs.append(os.path.normpath(os.path.join(base, str(b))).replace(os.sep, "/"))
        exp = d.get("exports")
        if isinstance(exp, dict):
            exp = exp.get(".", exp)
            if isinstance(exp, dict):
                exp = exp.get("types") or exp.get("import") or exp.get("default")
        entry = None
        for cand in [d.get("types"), d.get("main"), d.get("module"), exp if isinstance(exp, str) else None,
                     "src/index.ts", "src/index.tsx", "index.ts", "src/index.js", "index.js"]:
            if not isinstance(cand, str):
                continue
            c = os.path.normpath(os.path.join(base, cand)).replace(os.sep, "/")
            for v in (c, re.sub(r"\.d\.ts$", ".ts", c), re.sub(r"^(.*?)(dist|build|lib)/(.*)\.(d\.ts|js)$", r"\1src/\3.ts", c)):
                if os.path.isfile(os.path.join(root, v)) and not v.endswith(".d.ts"):
                    entry = v
                    break
            if entry:
                break
        name = d.get("name") or base or "(bez nazwy)"
        out[base] = (f"{name} (korzeń repo)" if not base else name, entry, refs)
    return out


def package_of(p: str, pkgs: dict) -> str | None:
    d = os.path.dirname(p)
    while True:
        if d in pkgs:
            return pkgs[d][0]
        if not d:
            return None
        d = os.path.dirname(d)


def group_of(p: str, depth: int) -> str:
    parts = p.split("/")[:-1]
    if len(parts) > 1 and parts[0] in MONO:
        rest = [x for x in parts[2:] if x not in ("src", "lib", "app")]
        return "/".join(parts[:2] + rest[:depth - 1])
    return "/".join(parts[:depth]) or "."


def sccs(nodes, succ):
    idx, low, st, on, out, c = {}, {}, [], set(), [], [0]
    for start in nodes:
        if start in idx:
            continue
        idx[start] = low[start] = c[0]; c[0] += 1; st.append(start); on.add(start)
        stack = [(start, iter(succ(start)))]
        while stack:
            v, it = stack[-1]
            w = next(it, None)
            if w is not None:
                if w not in idx:
                    idx[w] = low[w] = c[0]; c[0] += 1; st.append(w); on.add(w)
                    stack.append((w, iter(succ(w))))
                elif w in on:
                    low[v] = min(low[v], idx[w])
                continue
            stack.pop()
            if stack:
                low[stack[-1][0]] = min(low[stack[-1][0]], low[v])
            if low[v] == idx[v]:
                comp = []
                while True:
                    w = st.pop(); on.discard(w); comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1:
                    out.append(sorted(comp))
    return sorted(out, key=lambda c: (-len(c), c))


def in_scope(p: str, scope: str) -> bool:
    scope = scope.rstrip("/")
    return p == scope or p.startswith(scope + "/")


def analyze(root: str, top: int = 10, impact: str | None = None, gdepth: int | None = None,
            focus: list[str] | None = None) -> dict:
    all_files = list(walk(root))
    py = [p for p in all_files if p.endswith(".py")]
    ts = [p for p in all_files if p.endswith(TS_EXT) and not p.endswith(".d.ts")]
    pkgs = workspaces(root, all_files)
    aliases = {d.get("name"): e for d, e in ((load_json(root, os.path.join(b, "package.json")), v[1])
                                            for b, v in pkgs.items()) if e and d.get("name")}
    E, barrels, reg = collections.defaultdict(dict), set(), {}
    auto = gdepth is None
    gdepth = gdepth or 2
    if py:
        py_graph(root, py, E, barrels, reg)
    if ts:
        ts_graph(root, ts, aliases, E, barrels, reg)
    nodes = sorted(p for p in py + ts if not is_test(p))
    ns = set(nodes)
    prod_edges = [(s, t, k) for s in nodes for t, k in sorted(E.get(s, {}).items()) if t in ns]
    rev = collections.defaultdict(set)
    for s, tt in E.items():
        for t in tt:
            rev[t].add(s)
    indeg = {n: sum(1 for s in rev[n] if s in ns) for n in nodes}
    outdeg = collections.Counter(s for s, _, _ in prod_edges)
    barrels &= ns
    hubs = sorted((n for n in nodes if n not in barrels and indeg[n]), key=lambda n: (-indeg[n], n))[:top]

    # cykle: runtime (tylko module) i domykane leniwie
    succ_rt = lambda v: [t for t, k in E.get(v, {}).items() if t in ns and k == "module"]
    succ_all = lambda v: [t for t in E.get(v, {}) if t in ns]
    rt = sccs(nodes, succ_rt)
    rt_keys = {tuple(c) for c in rt}
    lazy = []
    for c in sccs(nodes, succ_all):
        if tuple(c) in rt_keys:
            continue
        cs = set(c)
        closed = sorted({k for s in c for t, k in E.get(s, {}).items() if t in cs and k != "module"})
        groups = collections.Counter(group_of(f, gdepth) for f in c)
        lazy.append({"files": c, "size": len(c), "closed_by": closed, "groups": groups.most_common(5)})
    comp = {}   # plik -> (rodzaj cyklu, nr składowej): runtime ma pierwszeństwo
    for i, c in enumerate(lazy):
        for f in c["files"]:
            comp[f] = ("lazy", i)
    for i, c in enumerate(rt):
        for f in c:
            comp[f] = ("runtime", i)

    # punkty wejścia
    refs = {r for _, _, rr in pkgs.values() for r in rr}
    outs, ins = sorted(outdeg[n] for n in nodes), sorted(indeg[n] for n in nodes)
    q = lambda arr, f: arr[min(len(arr) - 1, int(len(arr) * f))] if arr else 0
    o90, i25 = q(outs, 0.9), q(ins, 0.25)

    def score(n):
        why, s = [], 0
        depth = n.count("/") - (2 if n.split("/")[0] in MONO else 0) - (1 if "/src/" in "/" + n else 0) - \
            (1 if n.endswith("/__init__.py") else 0)
        if n in refs:
            s += 3; why.append("package.json")
        elif ENTRY_NAME.search(n) and depth <= 1:   # app.py czy urls.py głęboko w drzewie to zwykle moduł, nie wejście
            s += 3; why.append("nazwa")
        if depth <= 1:
            s += 1; why.append("płytko")
        if outdeg[n] and outdeg[n] >= o90:
            s += 1; why.append("dużo importuje")
        if indeg[n] <= i25:
            s += 1; why.append("mało importowany")
        return s, why
    cand = []
    for n in nodes:
        if n in barrels:
            continue
        s, why = score(n)
        if s >= 3 and why[0] in ("nazwa", "package.json"):   # bez sygnału nazwy płytki liść to jeszcze nie wejście
            cand.append({"file": n, "score": s, "out": outdeg[n], "in": indeg[n], "why": why})
    cand.sort(key=lambda e: (-e["score"], -e["out"], e["file"]))

    # pakiety workspace
    pk = collections.defaultdict(lambda: {"edges": 0, "type": 0})
    for s, t, k in prod_edges:
        a, b = package_of(s, pkgs), package_of(t, pkgs)
        if a and b and a != b:
            pk[(a, b)]["edges"] += 1
            pk[(a, b)]["type"] += k == "type"
    packages = [{"from": a, "to": b, "edges": v["edges"], "type_only": v["edges"] == v["type"]}
                for (a, b), v in sorted(pk.items(), key=lambda x: (-x[1]["edges"], x[0]))]

    # grupy (bez barreli) i zależności pod prąd
    grp = {n: group_of(n, gdepth) for n in nodes}
    split = []
    if auto:   # grupa z > 40% plików produkcyjnych nic nie mówi o warstwach — rozbij ją o poziom (najwyżej 2 razy)
        for extra in (1, 2):
            sizes = collections.Counter(grp.values())
            big = [g for g, n in sizes.items() if n >= 20 and n > 0.4 * len(nodes)]
            changed = False
            for g in big:
                for n in nodes:
                    if grp[n] == g:
                        new = group_of(n, gdepth + extra)
                        changed |= new != g
                        grp[n] = new
                if changed and g not in split:
                    split.append(g)
            if not changed:
                break
    members = collections.Counter(grp.values())
    inner, ge, gcyc = collections.Counter(), collections.Counter(), {}
    for s, t, k in prod_edges:
        if s in barrels:
            continue
        a, b = grp[s], grp[t]
        if a == b:
            inner[a] += 1
        else:
            ge[(a, b)] += 1
            cs, ct = comp.get(s), comp.get(t)
            if cs and cs == ct:   # oba końce w tym samym cyklu plików
                key = frozenset((a, b))
                gcyc[key] = "runtime" if "runtime" in (gcyc.get(key), cs[0]) else "lazy"
    groups = []
    for g, n in members.most_common():
        gin = sum(v for (a, b), v in ge.items() if b == g)
        gout = sum(v for (a, b), v in ge.items() if a == g)
        role = "fundament" if gin > 2 * max(gout, 1) else ("góra" if gout > 2 * max(gin, 1) else "środek")
        groups.append({"group": g, "files": n, "density": round(inner[g] / (n * (n - 1)), 2) if n > 1 else 0.0,
                       "in": gin, "out": gout, "role": role})
    nested = lambda a, b: a.startswith(b + "/") or b.startswith(a + "/")
    upstream = []
    for (a, b), x in ge.items():
        y = ge.get((b, a), 0)
        if a < b and y:
            cyc = gcyc.get(frozenset((a, b)))
            if nested(a, b) and not cyc:
                continue   # katalog i jego podkatalog bez cyklu: artefakt grupowania, nie strzałka pod prąd
            upstream.append({"a": a, "b": b, "a_to_b": x, "b_to_a": y, "cycle": cyc})
    upstream.sort(key=lambda u: (-min(u["a_to_b"], u["b_to_a"]), u["a"]))

    res = {"root": os.path.abspath(root),
           "files": {"python": sum(p.endswith(".py") for p in nodes), "ts_js": sum(not p.endswith(".py") for p in nodes),
                     "edges": len(prod_edges),
                     "by_kind": dict(collections.Counter(k for _, _, k in prod_edges))},
           "entry_points": cand[:max(top, 15)],
           "packages": packages,
           "groups": groups[:max(top, 12)],
           "groups_split": split,
           "registries": [{"kind": k, "file": f, "count": n} for f, c in reg.items() for k, n in c.items()],
           "upstream": upstream[:top * 2],
           "hubs": [{"file": h, "in": indeg[h], "out": outdeg[h]} for h in hubs],
           "barrels": [{"file": b, "in": indeg[b]} for b in sorted(barrels, key=lambda n: (-indeg[n], n))],
           "cycles": {"runtime": [{"files": c, "size": len(c)} for c in rt], "with_lazy": lazy},
           "edges": [{"from": s, "to": t, "kind": k} for s, t, k in prod_edges]}
    if impact:
        seen, frontier, levels = {impact}, {impact}, []
        for _ in range(2):
            nxt = {s for f in frontier for s in rev.get(f, ())} - seen
            levels.append(nxt); seen |= nxt; frontier = nxt
        res["impact"] = {"file": impact, "direct": sorted(f for f in levels[0] if not is_test(f)),
                         "second": sorted(f for f in levels[1] if not is_test(f)),
                         "tests": sorted(f for f in seen if is_test(f))}
    if focus:
        a, b = focus[0], (focus[1] if len(focus) > 1 else None)
        inside_b = (lambda p: in_scope(p, b)) if b else (lambda p: not in_scope(p, a))
        edge = lambda s, t, k: {"from": s, "to": t, "kind": k}
        out = [edge(s, t, k) for s, t, k in prod_edges if in_scope(s, a) and not in_scope(t, a) and inside_b(t)]
        inc = [edge(s, t, k) for s, t, k in prod_edges if in_scope(t, a) and not in_scope(s, a) and inside_b(s)]
        crossing = out + inc
        res["focus"] = {"scope": a, "other": b, "files": sum(in_scope(n, a) for n in nodes),
                        "outgoing": out, "incoming": inc,
                        "type_only": bool(crossing) and all(e["kind"] == "type" for e in crossing),
                        "by_kind": dict(collections.Counter(e["kind"] for e in crossing))}
    return res


def render(r: dict, top: int) -> str:
    f = r["files"]
    L = [f"Pliki produkcyjne: Python {f['python']}, TS/JS {f['ts_js']}; krawędzie {f['edges']} {f['by_kind']} "
         "(WYCIĄGNIĘTE z importów)"]
    L.append("Punkty wejścia (wynik, out, in, dlaczego):")
    L += [f"  - {e['file']} ({e['score']}, {e['out']}, {e['in']}; {', '.join(e['why'])})" for e in r["entry_points"]]
    if r["registries"]:
        kinds = collections.defaultdict(list)
        for x in r["registries"]:
            kinds[x["kind"]].append(x)
        L.append("Wejścia z rejestrów (dekoratory, wywołania, konwencje frameworka; plik liczba):")
        for k in sorted(kinds):
            xs = sorted(kinds[k], key=lambda x: (-x["count"], x["file"]))
            L.append(f"  - {k}: {sum(x['count'] for x in xs)} w {len(xs)} plikach: " +
                     "; ".join(f"{x['file']} {x['count']}" for x in xs[:top]) + (" …" if len(xs) > top else ""))
    if r["packages"]:
        L.append("Pakiety workspace (krawędzie; „typy” = tylko importy typów):")
        L += [f"  - {p['from']} → {p['to']}: {p['edges']}{' (typy)' if p['type_only'] else ''}" for p in r["packages"]]
    L.append("Grupy (pliki, gęstość, in, out, rola)" +
             (f"; rozbite automatycznie (> 40% plików): {', '.join(r['groups_split'])}" if r["groups_split"] else "") + ":")
    L += [f"  - {g['group']}: {g['files']}, {g['density']}, {g['in']}, {g['out']}, {g['role']}" for g in r["groups"]]
    if r["upstream"]:
        L.append("Pod prąd — zależności w obie strony między grupami (A→B / B→A; [cykl runtime|lazy] = oba końce "
                 "w jednym cyklu plików):")
        L += [f"  - {u['a']} ⇄ {u['b']} ({u['a_to_b']}/{u['b_to_a']})" + (f" [cykl {u['cycle']}]" if u["cycle"] else "")
              for u in r["upstream"]]
    L.append("Huby (importujący pliki produkcyjne, bez barreli): " +
             "; ".join(f"{h['file']} {h['in']}" for h in r["hubs"]))
    if r["barrels"]:
        b = r["barrels"]
        L.append(f"Barrele ({len(b)}; re-eksporty, poza hubami i grupami; importujący): " +
                 "; ".join(f"{x['file']} {x['in']}" for x in b[:top]) + (" …" if len(b) > top else ""))
    rt, lz = r["cycles"]["runtime"], r["cycles"]["with_lazy"]
    L.append(f"Cykle runtime (tylko importy wykonywane przy imporcie modułu): {len(rt)}")
    L += [f"  - {c['size']}: " + ", ".join(c["files"][:10]) + (" …" if c["size"] > 10 else "") for c in rt[:top * 2]]
    L.append(f"Cykle domykane dopiero importami leniwymi (w funkcji, typy, import()): {len(lz)}")
    for c in lz[:top]:
        body = ", ".join(c["files"]) if c["size"] <= 6 else \
            f"grupy: {', '.join(f'{g} {n}' for g, n in c['groups'])}"
        L.append(f"  - {c['size']} przez {'+'.join(c['closed_by'])}: {body}")
    if "impact" in r:
        i = r["impact"]
        L.append(f"Zasięg {i['file']}: bezpośrednio {len(i['direct'])}: {', '.join(i['direct'][:20])}")
        L.append(f"  2. krok {len(i['second'])}: {', '.join(i['second'][:20])}{' …' if len(i['second']) > 20 else ''}")
        L.append(f"  testy {len(i['tests'])}: {', '.join(i['tests'][:20])}{' …' if len(i['tests']) > 20 else ''}")
    if "focus" in r:
        fo = r["focus"]
        side = f"{fo['scope']} ↔ {fo['other']}" if fo["other"] else f"{fo['scope']} ↔ reszta repo"
        L.append(f"Granica {side} ({fo['files']} plików w zakresie; rodzaje {fo['by_kind']}"
                 f"{'; tylko typy' if fo['type_only'] else ''}):")
        for title, key, end in (("  wychodzące", "outgoing", "to"), ("  przychodzące", "incoming", "from")):
            es = fo[key]
            L.append(f"{title} {len(es)}:")
            L += [f"    - {e['from']} → {e['to']} ({e['kind']})" for e in es[:top * 3]]
            if len(es) > top * 3:
                L.append(f"    … +{len(es) - top * 3} (pełna lista: --json)")
    L.append("Graf nie widzi: DI, rejestrów, kolejek, sygnałów, importów po nazwie, HTTP między usługami — do unknowns.")
    return "\n".join(L)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    root, opts, focus, it = argv[1], {}, [], iter(argv[2:])
    for a in it:
        if a == "--focus":
            focus.append(next(it, "").strip("/"))
        else:
            opts[a] = next(it, "") if a in ("--top", "--impact", "--group-depth") else True
    if not os.path.isdir(root):
        print(f"✗ Nie ma katalogu: {root}")
        return 2
    for f in focus:
        if not f or not os.path.exists(os.path.join(root, f)):
            print(f"✗ Nie ma zakresu --focus: {f or '(pusty)'}")
            return 2
    top = int(opts.get("--top") or 10)
    gd = int(opts["--group-depth"]) if opts.get("--group-depth") else None
    r = analyze(root, top, opts.get("--impact") or None, gd, focus[:2] or None)
    print(json.dumps(r, ensure_ascii=False, indent=1) if opts.get("--json") else render(r, top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
