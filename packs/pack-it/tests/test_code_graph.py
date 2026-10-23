#!/usr/bin/env python3
"""Testy eng-codebase-mapping/scripts/code_graph.py na fikstur w katalogu tymczasowym (Python ast + TS/JS)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts" / "code_graph.py"


def write(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60,
                          encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)


def graph(root: Path, *args) -> dict:
    r = run(str(root), "--json", *args)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(r.stdout)


PY = {
    "app/__init__.py": "",
    "app/a.py": "from typing import TYPE_CHECKING\nfrom . import b\nif TYPE_CHECKING:\n    from .c import C\n",
    "app/b.py": "from .a import x\n",                       # a <-> b: cykl runtime
    "app/c.py": "def f():\n    from .a import y\n",         # c -> a tylko w funkcji
    "app/d.py": "import app.e\n",
    "app/e.py": "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from app.d import D\n",  # d <-> e przez typy
    "app/f.py": "from app.g import z\n",
    "app/g.py": "def h():\n    import app.f\n",           # f <-> g przez import w funkcji
    "app/tests/test_a.py": "from app import a\n",
    "app/migrations/0001.py": "from app import a\n",
    "manage.py": "import os\n",
    "app/asgi.py": "from app import a\n",
    "app/h.py": "import typing\nif typing.TYPE_CHECKING is True:\n    from app.i import I\n",
    "app/i.py": "from app import h\n",                     # h <-> i: TYPE_CHECKING is True to też typy
    "app/sub/__init__.py": "from .x import X\n",
    "app/sub/x.py": "from . import y\n",                   # from . import y → sub/y.py, nie sub/__init__.py
    "app/sub/y.py": "Y = 1\n",
    "app/schema.py": "from app import a\n",               # schema.py to nie punkt wejścia procesu
    "app/graphql/loaders/app.py": "x = 1\n",                # ogólna nazwa głęboko w drzewie to nie wejście
    "app/jobs.py": "from app.celeryconf import app\n\n@app.task(bind=True)\ndef a(self): pass\n\n@shared_task\ndef b(): pass\n",
    "app/celeryconf.py": "app = object()\n",
    "app/management/commands/reindex.py": "class Command: pass\n",
    "app/management/commands/__init__.py": "",
    "app/api_schema.py": "import graphene\nschema = graphene.Schema(query=None)\n",
    "app/http.py": "from fastapi import FastAPI\napi = FastAPI()\n\n@api.get('/x')\ndef x(): pass\n\n@api.post('/y')\ndef y(): pass\n",
}

TS = {
    "package.json": json.dumps({"name": "root", "private": True, "workspaces": ["packages/*"],
                                "scripts": {"tool": "node scripts/tool.mjs"}}),
    "scripts/tool.mjs": "import { q } from './lib/q.mjs'\n",
    "scripts/lib/q.mjs": "export const q = 1\n",
    "packages/core/package.json": json.dumps({"name": "@x/core", "main": "src/index.ts"}),
    "packages/core/src/index.ts": "export { model } from './model'\nexport * from './text'\nexport type { T } from './types'\n",
    "packages/core/src/model.ts": "export const model = 1\n",
    "packages/core/src/text.ts": "import { model } from './model'\nexport const t = model\n",
    "packages/core/src/types.ts": "export type T = number\n",
    "packages/core/src/analysis/rules.ts": "import { model } from '../model'\nimport { t } from '../text'\n",
    "packages/core/src/analysis/claims.ts": "import { model } from '../model'\nimport { r } from './rules'\n",
    "packages/core/src/project.ts": "import { r } from './analysis/rules'\n",  # core ⇄ core/analysis bez cyklu
    "packages/core/test/text.test.ts": "import { t } from '../src/text'\n",
    "packages/web/package.json": json.dumps({"name": "@x/web", "scripts": {"dev": "vite"}}),
    "packages/web/src/main.tsx": "import { App } from './App'\nimport './styles.css'\n",
    "packages/web/src/App.tsx": "import { Page } from './pages/Page'\nimport type { T } from '@x/core'\n",
    "packages/web/src/pages/Page.tsx": "import { useApp } from '../App'\n",   # cykl runtime App <-> Page
    "packages/web/src/api.ts": "import { type T, type U } from '@x/core'\n",  # tylko typy
    "packages/web/src/lazy.ts": "const m = import('./api')\n",
    "packages/server/package.json": json.dumps({"name": "@x/server", "scripts": {"start": "tsx src/index.ts"},
                                                "bin": {"srv": "src/cli.ts"}}),
    "packages/server/src/index.ts": "import { app } from './app'\napp.listen()\n",
    "packages/server/src/app.ts": "import { model, T } from '@x/core'\nexport const app = {}\n// trasy API\nconst glob = 'src/**/*.ts', re = /a\\/*b/\napp.get('/api/a', h)\nrouter.post(\"/api/b\", h)\nlist.get(key)\n",
    "packages/server/src/cli.ts": "import { app } from './app.js'\n",
    "packages/server/src/tool.ts": "import { q } from '../../../scripts/lib/q.mjs'\n",
    "packages/sandbox/src/a.ts": "import type { B } from './b'\n",
    "packages/sandbox/src/b.ts": "import { type A } from './a'\n",          # cykl tylko typów
    "packages/server/src/users.controller.ts": "@Controller('users')\nexport class UsersController {}\n",
    "packages/server/src/jobs.ts": "export class Jobs {\n  @Cron('0 * * * *')\n  run() {}\n}\n",
}

BIG = {f"svc/api/m{i}/v{j}.py": "x = 1\n" for i in range(6) for j in range(5)}   # 30 plików pod svc/api
BIG.update({"svc/core/a.py": "x = 1\n", "svc/core/b.py": "from svc.api.m0 import v0\n", "svc/web/c.py": "x = 1\n"})

JAVA = {
    "pom.xml": "<project/>",
    "src/main/java/com/acme/Application.java":
        "package com.acme;\nimport org.springframework.boot.autoconfigure.SpringBootApplication;\n"
        "import com.acme.billing.InvoiceService;\n@SpringBootApplication\npublic class Application {\n"
        "  public static void main(String[] args) {}\n}\n",
    "src/main/java/com/acme/billing/InvoiceService.java":
        "package com.acme.billing;\nimport com.acme.common.*;\nimport static com.acme.common.Money.zero;\n"
        "/* import com.acme.billing.Ghost; */\npublic class InvoiceService {}\n",
    "src/main/java/com/acme/common/Money.java": "package com.acme.common;\npublic final class Money {}\n",
    "src/main/java/com/acme/common/Currency.java":
        "package com.acme.common;\nimport com.acme.billing.InvoiceService;\npublic enum Currency { PLN }\n",
    "src/main/java/com/acme/tools/Cli.java":
        "package com.acme.tools;\npublic class Cli {\n  public static void main(String... a) {}\n}\n",
    "src/test/java/com/acme/billing/InvoiceServiceTest.java":
        "package com.acme.billing;\nimport com.acme.common.Money;\nclass InvoiceServiceTest {}\n",
}

CS = {
    "Shop.sln": "",
    "src/Shop.Api/Program.cs": "using Shop.Orders;\nvar app = WebApplication.Create(args);\napp.Run();\n",
    "src/Shop.Orders/OrderService.cs":
        "using System;\nusing Shop.Common;\nnamespace Shop.Orders\n{\n  public class OrderService {}\n}\n",
    "src/Shop.Orders/Order.cs": "namespace Shop.Orders;\npublic record Order(int Id);\n",
    "src/Shop.Common/Clock.cs": "namespace Shop.Common;\nusing Shop.Orders;\npublic class Clock {}\n",
    "src/Shop.Worker/Worker.cs":
        "using static Shop.Common.Clock;\nnamespace Shop.Worker;\npublic static class Worker {\n"
        "  static async Task Main(string[] args) {}\n}\n",
    "tests/Shop.Orders.Tests/OrderServiceTests.cs": "using Shop.Orders;\nnamespace Shop.Orders.Tests;\n",
}

GO = {
    "go.mod": "module example.com/shop\n\ngo 1.22\n",
    "cmd/api/main.go": "package main\n\nimport (\n\t\"fmt\"\n\t\"example.com/shop/internal/orders\"\n)\n\n"
                       "func main() { fmt.Println(orders.New()) }\n",
    "internal/orders/orders.go": "package orders\n\nimport db \"example.com/shop/internal/store\"\n\nfunc New() int { return db.X }\n",
    "internal/orders/model.go": "package orders\n",
    "internal/store/store.go": "package store\n\nimport _ \"example.com/shop/internal/orders\"\n\nvar X = 1\n",
    "internal/orders/orders_test.go": "package orders\n\nimport \"example.com/shop/internal/store\"\n",
    "tools/gen/gen.go": "package main\n\nimport \"os\"\n\nfunc main() { _ = os.Args }\n",
}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    # T9 pomoc i zła ścieżka
    r = run("--help")
    check(r.returncode == 0 and "--impact" in r.stdout and "--json" in r.stdout, f"T9 --help: {r.stdout[:200]}")
    r = run("/nie/ma/takiej/sciezki")
    check(r.returncode == 2, f"T9 zła ścieżka rc={r.returncode}")

    with tempfile.TemporaryDirectory() as d:
        py = Path(d) / "py"
        write(py, PY)
        g = graph(py)
        kinds = {(e["from"], e["to"]): e["kind"] for e in g["edges"]}
        # T1 rodzaje importów
        check(kinds.get(("app/a.py", "app/b.py")) == "module", f"T1 a->b module: {kinds.get(('app/a.py', 'app/b.py'))}")
        check(kinds.get(("app/a.py", "app/c.py")) == "type", f"T1 a->c type: {kinds.get(('app/a.py', 'app/c.py'))}")
        check(kinds.get(("app/c.py", "app/a.py")) == "function", f"T1 c->a function: {kinds.get(('app/c.py', 'app/a.py'))}")
        check(kinds.get(("app/b.py", "app/a.py")) == "module", "T1 względny from .a")
        check(kinds.get(("app/h.py", "app/i.py")) == "type", "T1 if typing.TYPE_CHECKING is True")
        check(kinds.get(("app/sub/x.py", "app/sub/y.py")) == "module" and ("app/sub/x.py", "app/sub/__init__.py") not in kinds,
              f"T1 from . import y: {[k for k in kinds if k[0] == 'app/sub/x.py']}")
        check(not any(f.startswith(("app/tests/", "app/migrations/")) for f, _ in kinds), "T8 testy i migracje poza grafem")
        # T2 cykle runtime osobno
        rt = [sorted(c["files"]) for c in g["cycles"]["runtime"]]
        check(rt == [["app/a.py", "app/b.py"]], f"T2 cykle runtime: {rt}")
        wide = [sorted(c["files"]) for c in g["cycles"]["with_lazy"]]
        check(["app/d.py", "app/e.py"] in wide, f"T2 cykl przez typy w with_lazy: {wide}")
        check(["app/f.py", "app/g.py"] in wide, f"T2 cykl przez import w funkcji w with_lazy: {wide}")
        lazy = {tuple(sorted(c["files"])): c["closed_by"] for c in g["cycles"]["with_lazy"]}
        check("type" in lazy.get(("app/d.py", "app/e.py"), []), f"T2 closed_by type: {lazy}")
        check("function" in lazy.get(("app/f.py", "app/g.py"), []), f"T2 closed_by function: {lazy}")
        # T7 wejścia Python
        ent = {e["file"]: e["score"] for e in g["entry_points"]}
        check(ent.get("manage.py", 0) >= 3 and ent.get("app/asgi.py", 0) >= 3, f"T7 manage/asgi: {ent}")
        check("app/schema.py" not in ent, "T7 schema.py nie jest wejściem")
        check("app/graphql/loaders/app.py" not in ent, f"T7 głęboki app.py: {ent}")
        # T11 wejścia z rejestrów (osobno od punktacji nazw)
        reg = {(x["kind"], x["file"]): x["count"] for x in g["registries"]}
        check(reg.get(("celery", "app/jobs.py")) == 2, f"T11 celery: {reg}")
        check(reg.get(("django-command", "app/management/commands/reindex.py")) == 1, f"T11 komenda: {reg}")
        check(("django-command", "app/management/commands/__init__.py") not in reg, "T11 __init__ komend pominięty")
        check(reg.get(("graphql-schema", "app/api_schema.py")) == 1, f"T11 schemat: {reg}")
        check(reg.get(("http", "app/http.py")) == 3, f"T11 http (aplikacja + 2 trasy): {reg}")
        r = run(str(py))
        check("Wejścia z rejestrów" in r.stdout and "app/jobs.py" in r.stdout, f"T11 tekst: {r.stdout[:600]}")

        ts = Path(d) / "ts"
        write(ts, TS)
        g = graph(ts)
        kinds = {(e["from"], e["to"]): e["kind"] for e in g["edges"]}
        # T3 rodzaje importów TS
        check(kinds.get(("packages/sandbox/src/a.ts", "packages/sandbox/src/b.ts")) == "type", "T3 import type")
        check(kinds.get(("packages/sandbox/src/b.ts", "packages/sandbox/src/a.ts")) == "type", "T3 { type A }")
        check(kinds.get(("packages/server/src/app.ts", "packages/core/src/index.ts")) == "module", "T3 mieszany = module")
        check(kinds.get(("packages/core/src/index.ts", "packages/core/src/text.ts")) == "module", "T3 export * from")
        check(kinds.get(("packages/web/src/lazy.ts", "packages/web/src/api.ts")) == "dynamic", "T3 import()")
        check(kinds.get(("packages/server/src/cli.ts", "packages/server/src/app.ts")) == "module", "T3 './app.js' -> app.ts")
        check(kinds.get(("scripts/tool.mjs", "scripts/lib/q.mjs")) == "module", "T3 .mjs")
        check(not any(f.endswith(".test.ts") for f, _ in kinds), "T8 testy TS poza grafem")
        # T4 pakiety workspace
        pk = {(p["from"], p["to"]): p for p in g["packages"]}
        check(("@x/web", "@x/core") in pk and pk[("@x/web", "@x/core")]["type_only"], f"T4 web->core tylko typy: {pk}")
        check(("@x/server", "@x/core") in pk and not pk[("@x/server", "@x/core")]["type_only"], "T4 server->core runtime")
        check(("@x/server", "root (korzeń repo)") in pk, f"T4 pakiet korzenia opisany: {list(pk)}")
        # T2/T3 cykle TS
        rt = [sorted(c["files"]) for c in g["cycles"]["runtime"]]
        check(rt == [["packages/web/src/App.tsx", "packages/web/src/pages/Page.tsx"]], f"T2 TS runtime: {rt}")
        lazy = {tuple(sorted(c["files"])): c["closed_by"] for c in g["cycles"]["with_lazy"]}
        check(lazy.get(("packages/sandbox/src/a.ts", "packages/sandbox/src/b.ts")) == ["type"], f"T2 TS typy: {lazy}")
        # T5 barrele
        hubs = [h["file"] for h in g["hubs"]]
        check("packages/core/src/index.ts" in [b["file"] for b in g["barrels"]] and "packages/core/src/index.ts" not in hubs,
              "T5 barrel")
        check(hubs and hubs[0] == "packages/core/src/model.ts", f"T5 hub model.ts: {hubs}")
        # T6 grupy: rodzic ⇄ podkatalog nie jest „pod prąd”
        up = [(m["a"], m["b"]) for m in g["upstream"]]
        check(not any({a, b} == {"packages/core", "packages/core/analysis"} for a, b in up), f"T6 rodzic/dziecko: {up}")
        check(any({a, b} == {"packages/web", "packages/web/pages"} for a, b in up), f"T6 web⇄pages zostaje: {up}")
        cyc = {frozenset((m["a"], m["b"])): m["cycle"] for m in g["upstream"]}
        check(cyc.get(frozenset(("packages/web", "packages/web/pages"))) == "runtime", f"T6 cykl runtime: {cyc}")
        bar = {b["file"]: b["in"] for b in g["barrels"]}
        check(bar.get("packages/core/src/index.ts", 0) >= 2, f"T5 barrel z liczbą importujących: {bar}")
        # T7 wejścia TS
        ent = {e["file"]: e for e in g["entry_points"]}
        check(ent.get("packages/server/src/index.ts", {}).get("score", 0) >= 3, f"T7 scripts start: {list(ent)}")
        check(ent.get("packages/server/src/cli.ts", {}).get("score", 0) >= 3, "T7 bin")
        check(ent.get("packages/web/src/main.tsx", {}).get("score", 0) >= 3, "T7 main.tsx")
        check(ent.get("scripts/tool.mjs", {}).get("score", 0) >= 3, "T7 skrypt z root package.json")
        check("packages/core/src/index.ts" not in ent, "T7 barrel nie jest wejściem")
        # T8 zasięg zmiany
        reg = {(x["kind"], x["file"]): x["count"] for x in g["registries"]}
        check(reg.get(("http", "packages/server/src/users.controller.ts")) == 1, f"T11 Nest controller: {reg}")
        check(reg.get(("cron", "packages/server/src/jobs.ts")) == 1, f"T11 Nest cron: {reg}")
        check(reg.get(("http", "packages/server/src/app.ts")) == 2, f"T11 trasy express/fastify (bez list.get): {reg}")
        g = graph(ts, "--impact", "packages/core/src/model.ts")
        imp = g["impact"]
        check(set(imp["direct"]) >= {"packages/core/src/text.ts", "packages/core/src/index.ts",
                                     "packages/core/src/analysis/rules.ts"}, f"T8 direct: {imp['direct']}")
        check("packages/server/src/app.ts" in imp["second"], f"T8 second: {imp['second']}")
        check("packages/core/test/text.test.ts" in imp["tests"], f"T8 testy: {imp['tests']}")
        r = run(str(ts))
        check(r.returncode == 0 and "Cykle runtime" in r.stdout and "Punkty wejścia" in r.stdout, f"T8 tekst: {r.stdout[:300]}")
        # T10 --focus: krawędzie przecinające granicę zakresu; dwa zakresy = tylko między nimi
        g = graph(ts, "--focus", "packages/core/src/analysis")
        fo = g["focus"]
        out = {(e["from"], e["to"], e["kind"]) for e in fo["outgoing"]}
        inc = {(e["from"], e["to"]) for e in fo["incoming"]}
        check(("packages/core/src/analysis/rules.ts", "packages/core/src/model.ts", "module") in out, f"T10 out: {out}")
        check(("packages/core/src/project.ts", "packages/core/src/analysis/rules.ts") in inc, f"T10 in: {inc}")
        check(not any(f.startswith("packages/core/src/analysis/") and t.startswith("packages/core/src/analysis/")
                      for f, t, _ in out), "T10 krawędzie wewnętrzne zakresu pominięte")
        check(fo["files"] == 2, f"T10 liczba plików zakresu: {fo['files']}")
        g = graph(ts, "--focus", "packages/web", "--focus", "packages/core")
        fo = g["focus"]
        pairs = {(e["from"], e["to"], e["kind"]) for e in fo["outgoing"] + fo["incoming"]}
        check(pairs == {("packages/web/src/App.tsx", "packages/core/src/index.ts", "type"),
                        ("packages/web/src/api.ts", "packages/core/src/index.ts", "type")}, f"T10 para web↔core: {pairs}")
        check(fo["type_only"] is True, f"T10 para tylko typy: {fo}")
        r = run(str(ts), "--focus", "packages/web", "--focus", "packages/core")
        check(r.returncode == 0 and "Granica" in r.stdout and "api.ts" in r.stdout, f"T10 tekst: {r.stdout[-400:]}")
        # T12 automatyczny podział grupy z > 40% plików; --group-depth wyłącza
        big = Path(d) / "big"
        write(big, BIG)
        g = graph(big)
        names = {x["group"] for x in g["groups"]}
        check("svc/api" not in names and "svc/api/m0" in names, f"T12 podział svc/api: {sorted(names)}")
        check(g["groups_split"] == ["svc/api"], f"T12 lista podzielonych: {g.get('groups_split')}")
        g = graph(big, "--group-depth", "2")
        check("svc/api" in {x["group"] for x in g["groups"]} and not g["groups_split"], "T12 --group-depth wyłącza podział")
        r = run(str(ts), "--focus", "nie/ma")
        check(r.returncode == 2, f"T10 zły zakres rc={r.returncode}")

        # T13 Java: package/import, import *, import static, komentarze, main, testy poza grafem
        jv = Path(d) / "java"
        write(jv, JAVA)
        g = graph(jv)
        J = "src/main/java/com/acme/"
        ed = {(e["from"], e["to"]) for e in g["edges"]}
        check((J + "Application.java", J + "billing/InvoiceService.java") in ed, f"T13 import klasy: {sorted(ed)}")
        check({(J + "billing/InvoiceService.java", J + "common/Money.java"),
               (J + "billing/InvoiceService.java", J + "common/Currency.java")} <= ed, "T13 import pakietu.*")
        check(not any(t.endswith("Ghost.java") for _, t in ed), "T13 import w komentarzu pominięty")
        check(g["files"].get("java") == 5, f"T13 liczba plików Java (bez testów): {g['files']}")
        rt = [sorted(c["files"]) for c in g["cycles"]["runtime"]]
        check([J + "billing/InvoiceService.java", J + "common/Currency.java"] in rt, f"T13 cykl Java: {rt}")
        ent = {e["file"] for e in g["entry_points"]}
        check({J + "Application.java", J + "tools/Cli.java"} <= ent, f"T13 punkty wejścia main: {ent}")
        r = run(str(jv), "--impact", J + "common/Money.java")
        check(r.returncode == 0 and "InvoiceServiceTest.java" in r.stdout, f"T13 test w --impact: {r.stdout[-300:]}")

        # T14 C#: using → pliki przestrzeni nazw, namespace blokowy i plikowy, using static, Main i Program.cs
        cs = Path(d) / "cs"
        write(cs, CS)
        g = graph(cs)
        ed = {(e["from"], e["to"]) for e in g["edges"]}
        check({("src/Shop.Api/Program.cs", "src/Shop.Orders/OrderService.cs"),
               ("src/Shop.Api/Program.cs", "src/Shop.Orders/Order.cs")} <= ed, f"T14 using → namespace: {sorted(ed)}")
        check(("src/Shop.Orders/OrderService.cs", "src/Shop.Common/Clock.cs") in ed, "T14 namespace blokowy")
        check(("src/Shop.Worker/Worker.cs", "src/Shop.Common/Clock.cs") in ed, "T14 using static")
        check(not any(t.startswith("System") for _, t in ed) and not any("Tests" in f for f, _ in ed),
              "T14 bez zewnętrznych i testów")
        check(g["files"].get("csharp") == 5, f"T14 liczba plików C#: {g['files']}")
        ent = {e["file"] for e in g["entry_points"]}
        check({"src/Shop.Api/Program.cs", "src/Shop.Worker/Worker.cs"} <= ent, f"T14 wejścia: {ent}")

        # T15 Go: go.mod, import ścieżki pakietu → pliki katalogu, alias i import pusty, package main
        go = Path(d) / "go"
        write(go, GO)
        g = graph(go)
        ed = {(e["from"], e["to"]) for e in g["edges"]}
        check({("cmd/api/main.go", "internal/orders/orders.go"), ("cmd/api/main.go", "internal/orders/model.go"),
               ("internal/orders/orders.go", "internal/store/store.go")} <= ed, f"T15 importy Go: {sorted(ed)}")
        check(not any(f.endswith("_test.go") for f, _ in ed) and not any(t == "fmt" for _, t in ed), "T15 bez testów i stdlib")
        rt = [sorted(c["files"]) for c in g["cycles"]["runtime"]]
        check(["internal/orders/orders.go", "internal/store/store.go"] in rt, f"T15 cykl Go: {rt}")
        check(g["files"].get("go") == 5, f"T15 liczba plików Go: {g['files']}")
        ent = {e["file"] for e in g["entry_points"]}
        check({"cmd/api/main.go", "tools/gen/gen.go"} <= ent and "internal/store/store.go" not in ent, f"T15 wejścia: {ent}")
        r = run(str(go))
        check(r.returncode == 0 and "Go 5" in r.stdout, f"T15 tekst z liczbą plików Go: {r.stdout[:200]}")

    for f in fails:
        print("✗", f)
    print(f"{total - len(fails)}/{total} testów code_graph zielonych")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
