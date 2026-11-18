#!/usr/bin/env python3
"""Tests of eng-codebase-mapping/scripts/standards_scan.py: conventions from the code with a share, file:line examples
and exceptions — signals for the reconstruction standards. python3 .claude/tests/test_standards_scan.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-codebase-mapping" / "scripts" / "standards_scan.py"

REPO = {
    ".editorconfig": "root = true\n[*]\nindent_style = space\n",
    "eslint.config.js": "export default [];\n",
    "pyproject.toml": "[tool.ruff]\nline-length = 100\n[tool.pytest.ini_options]\n",
    "app/user_service.py": "import logging\nlog = logging.getLogger(__name__)\n\ndef f():\n    try:\n        pass\n"
                           "    except Exception:\n        log.exception('x')\n",
    "app/order_service.py": "import logging\n\ndef g():\n    try:\n        pass\n    except:\n        pass\n",
    "app/PaymentGateway.py": "def h():\n    print('debug')\n",
    "app/tests/test_user.py": "import pytest\n\ndef test_x():\n    assert True\n",
    "app/tests/test_order.py": "import pytest\n\ndef test_y():\n    assert True\n",
    "web/src/user-card.ts": "export const a = 1;\n// TODO: usunąć\n",
    "web/src/order-list.ts": "export const b = 2;\n",
    "web/src/OrderItem.ts": "export const c = 3;\n",
    "web/src/user-card.test.ts": "import { test } from 'vitest';\ntest('x', () => {});\n",
}


def write(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=60,
                          stdin=subprocess.DEVNULL)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        write(repo, REPO)
        r = run(str(repo), "--json")
        check(r.returncode == 0, f"S-1: runs: {r.stderr[-300:]}")
        out = json.loads(r.stdout) if r.returncode == 0 else {}
        tools = {(t["tool"], t["file"]) for t in out.get("tools", [])}
        check({("editorconfig", ".editorconfig"), ("eslint", "eslint.config.js"), ("ruff", "pyproject.toml"),
               ("pytest", "pyproject.toml")} <= tools, f"S-2: tools from the configuration: {sorted(tools)}")
        sig = {(s["area"], s["language"], s["rule"]): s for s in out.get("signals", [])}
        py = sig.get(("file names", "Python", "snake_case"))
        check(py and py["count"] == 2 and py["total"] == 3 and py["share"] == 67
              and any(e.startswith("app/PaymentGateway.py") for e in py["exceptions"]),
              f"S-3: Python file names 2/3 snake_case, exception PaymentGateway.py: {py}")
        ts = sig.get(("file names", "TypeScript", "kebab-case"))
        check(ts and ts["count"] == 2 and ts["total"] == 3 and any("OrderItem.ts" in e for e in ts["exceptions"]),
              f"S-4: TS file names kebab-case 2/3: {ts}")
        tf = sig.get(("tests", "Python", "pytest"))
        check(tf and tf["count"] == 2 and any(e.startswith("app/tests/test_user.py:1") for e in tf["examples"]),
              f"S-5: test framework with a file:line example: {tf}")
        check(("tests", "TypeScript", "vitest") in sig, f"S-6: vitest: {[k for k in sig if k[0] == 'tests']}")
        loc = sig.get(("tests", "Python", "separate tests/ directory"))
        check(loc and loc["count"] == 2, f"S-7: location of Python tests: {loc}")
        bare = sig.get(("errors", "Python", "bare except"))
        check(bare and bare["count"] == 1 and any(e.startswith("app/order_service.py:6") for e in bare["examples"]),
              f"S-8: bare except with a location: {bare}")
        lg = sig.get(("logging", "Python", "logging"))
        check(lg and lg["count"] == 2, f"S-9: logging w 2 plikach: {lg}")
        pr = sig.get(("logging", "Python", "print"))
        check(pr and pr["count"] == 1, f"S-10: print jako logowanie: {pr}")
        todo = sig.get(("debt", "TypeScript", "TODO/FIXME"))
        check(todo and any(e.startswith("web/src/user-card.ts:2") for e in todo["examples"]), f"S-11: TODO: {todo}")
        r = run(str(repo))
        check(r.returncode == 0 and "snake_case" in r.stdout and "67%" in r.stdout, f"S-12: tekst: {r.stdout[:400]}")

    # test and code idioms (layered tests, test-double libraries, case structure, production idioms)
    IDIOMS = {
        "src/main/java/app/owner/OwnerController.java": "class OwnerController {\n  @InitBinder\n  void b(WebDataBinder d) { d.setDisallowedFields(\"id\"); }\n"
                                                        "  @ModelAttribute(\"owner\") Owner o() { return null; }\n  String save() { return \"redirect:/owners/1\"; }\n}\n",
        "src/main/java/app/vet/VetController.java": "class VetController {\n  String list() { return \"vets\"; }\n}\n",
        "src/test/java/app/owner/OwnerControllerTests.java": "import org.junit.jupiter.api.Test;\n@WebMvcTest(OwnerController.class)\n"
                                                              "class OwnerControllerTests {\n  @MockitoBean OwnerRepository owners;\n}\n",
        "src/test/java/app/owner/OwnerRepositoryTests.java": "import org.junit.jupiter.api.Test;\n@DataJpaTest\nclass OwnerRepositoryTests {}\n",
        "tests/UnitTests/BasketAddItem.cs": "using Xunit;\nusing NSubstitute;\npublic class BasketAddItem {\n  [Fact]\n  public void AddsItem() {\n"
                                            "    var repo = Substitute.For<IRepository<Basket>>();\n    var b = new BasketBuilder().Build();\n  }\n}\n",
        "tests/UnitTests/Builders/BasketBuilder.cs": "public class BasketBuilder {\n  public Basket Build() => new Basket();\n}\n",
        "src/Core/Basket.cs": "public class Basket {\n  private readonly List<Item> _items = new();\n"
                              "  public IReadOnlyCollection<Item> Items => _items.AsReadOnly();\n  public void Add(int q) { Guard.Against.Negative(q, nameof(q)); }\n}\n",
        "article/service.go": "package article\n\nfunc (s *Service) Fetch(ctx context.Context, n int64) error {\n\treturn nil\n}\n"
                              "func (s *Service) Store(ctx context.Context, a *Article) error {\n\treturn nil\n}\n",
        "article/helper.go": "package article\n\nfunc encode(s string) string {\n\treturn s\n}\n",
        "article/service_test.go": "package article_test\n\nimport \"testing\"\n\nfunc TestFetch(t *testing.T) {\n"
                                   "\ttests := []struct{ name string }{{\"ok\"}}\n\tfor _, tc := range tests {\n\t\tt.Run(tc.name, func(t *testing.T) {})\n\t}\n}\n",
    }
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        write(repo, IDIOMS)
        r = run(str(repo), "--json")
        out = json.loads(r.stdout) if r.returncode == 0 else {}
        sig = {(s["area"], s["language"], s["rule"]): s for s in out.get("signals", [])}
        idi = sorted(k for k in sig if k[0].endswith("idioms"))
        w = sig.get(("test idioms", "Java", "@WebMvcTest (web layer test)"))
        check(w and w["count"] == 1 and w["total"] == 2 and any(e.startswith("src/test/java/app/owner/OwnerControllerTests.java:2") for e in w["examples"]),
              f"S-13: @WebMvcTest with a share and a location: {w} {idi}")
        check(("test idioms", "Java", "@DataJpaTest (repository test)") in sig
              and ("test idioms", "Java", "@MockitoBean/@MockBean") in sig, f"S-14: Spring layered tests: {idi}")
        ns = sig.get(("test idioms", "C#", "NSubstitute (Substitute.For)"))
        check(ns and ns["count"] == 1 and ("test idioms", "C#", "test data builder") in sig, f"S-15: C# test doubles and builders: {idi}")
        check(("test idioms", "Go", "t.Run (subtests)") in sig and ("test idioms", "Go", "table of cases ([]struct)") in sig
              and ("test idioms", "Go", "external package *_test") in sig, f"S-16: Go test idioms: {idi}")
        ctx = sig.get(("code idioms", "Go", "context.Context as first argument"))
        check(ctx and ctx["count"] == 1 and ctx["total"] == 2, f"S-17: ctx as the 1st argument (1/2 files): {ctx}")
        check(("code idioms", "C#", "AsReadOnly (read-only collections)") in sig and ("code idioms", "C#", "Guard.Against") in sig,
              f"S-18: idiomy C#: {idi}")
        prg = sig.get(("code idioms", "Java", "redirect: (Post/Redirect/Get)"))
        check(prg and prg["count"] == 1 and prg["total"] == 2 and ("code idioms", "Java", "@InitBinder") in sig
              and ("code idioms", "Java", "@ModelAttribute") in sig, f"S-19: Spring controller idioms: {prg} {idi}")

    # package layout (feature or layer) and DI lifetimes
    LAYOUT = {
        "src/main/java/app/owner/OwnerController.java": "class OwnerController {}\n",
        "src/main/java/app/owner/OwnerRepository.java": "interface OwnerRepository {}\n",
        "src/main/java/app/owner/PetValidator.java": "class PetValidator {}\n",
        "src/main/java/app/vet/VetController.java": "class VetController {}\n",
        "src/main/java/app/vet/VetRepository.java": "interface VetRepository {}\n",
        "src/main/java/app/model/BaseEntity.java": "class BaseEntity {}\n",
        "src/Web/Controllers/OrderController.cs": "public class OrderController {}\n",
        "src/Core/Services/OrderService.cs": "public class OrderService {}\n",
        "src/Core/Services/BasketService.cs": "public class BasketService {}\n",
        "src/Infrastructure/Data/Repository.cs": "public class Repository {}\n",
        "src/Core/Interfaces/IRepository.cs": "public interface IRepository {}\n",
        "src/Core/Interfaces/IOrderService.cs": "public interface IOrderService {}\n",
        "src/Infrastructure/Dependencies.cs": "public static class Dependencies {\n  public static void Add(this IServiceCollection s) {\n"
                                              "    s.AddScoped(typeof(IRepository<>), typeof(Repository<>));\n    s.AddScoped<IBasketService, BasketService>();\n"
                                              "    s.AddSingleton<IUriComposer>(new UriComposer());\n    s.AddTransient<IEmailSender, EmailSender>();\n  }\n}\n",
    }
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        write(repo, LAYOUT)
        r = run(str(repo), "--json")
        out = json.loads(r.stdout) if r.returncode == 0 else {}
        sig = {(s["area"], s["language"], s["rule"]): s for s in out.get("signals", [])}
        lay = sorted(k for k in sig if k[0] == "layout")
        feat = sig.get(("layout", "Java", "packages by feature (different roles in one directory)"))
        check(feat and feat["count"] == 2 and feat["total"] == 3 and any("app/owner" in e for e in feat["examples"]),
              f"S-20: Java: owner and vet by feature (2 of 3 directories): {feat} {lay}")
        layer = sig.get(("layout", "C#", "packages by layer (directory = layer)"))
        check(layer and layer["count"] == 4 and layer["total"] == 5 and any("Controllers" in e for e in layer["examples"])
              and not any("Data" in e for e in layer["examples"]),
              f"S-21: C#: Controllers, Services and Infrastructure as layers, Data not: {layer} {lay}")
        sc = sig.get(("code idioms", "C#", "DI: AddScoped"))
        check(sc and any(e.startswith("src/Infrastructure/Dependencies.cs:3") for e in sc["examples"])
              and ("code idioms", "C#", "DI: AddSingleton") in sig and ("code idioms", "C#", "DI: AddTransient") in sig,
              f"S-22: DI lifetimes with a location: {sc}")
        r = run(str(repo))
        check("layout · Java · packages by feature" in r.stdout, f"S-23: tekst: {r.stdout[-600:]}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of standards_scan")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
