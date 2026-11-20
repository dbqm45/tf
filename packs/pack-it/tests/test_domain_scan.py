#!/usr/bin/env python3
"""Tests of eng-domain-agents/scripts/domain_scan.py: domain layout detected from facts (Nx projects, module boundaries,
tsconfig paths, real imports), the human's override `.tf/config/domains.yaml`, the plan/write/check cycle that never
overwrites a human-edited file, and a generated project pack that installs and passes `build.py check`.
python3 .claude/tests/test_domain_scan.py"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = next(p for p in HERE.parents if (p / ".claude" / "skills").is_dir())
SCRIPT = ROOT / ".claude" / "skills" / "eng-domain-agents" / "scripts" / "domain_scan.py"

TSCONFIG = """{
  // comments and trailing commas are legal in tsconfig
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@acme/billing": ["domains/billing/src/index.ts"],
      "@acme/catalog": ["domains/catalog/src/index.ts"],
      "@acme/catalog/shared": ["domains/catalog/shared/src/index.ts"],
      "@acme/shipping": ["domains/shipping/src/index.ts"],
      "@acme/shared/ui": ["libs/shared/ui/src/index.ts"], /* shared */
    },
  },
}
"""
ESLINT = """import nx from '@nx/eslint-plugin';
export default [{
  rules: {
    '@nx/enforce-module-boundaries': ['error', {
      enforceBuildableLibDependency: true,
      allow: ['@acme/catalog/shared'],
      depConstraints: [
        { sourceTag: 'scope:billing', onlyDependOnLibsWithTags: ['scope:billing', 'scope:shared'] },
        { sourceTag: 'scope:catalog', onlyDependOnLibsWithTags: ['scope:catalog', 'scope:shared'] },
        { sourceTag: 'scope:shipping', onlyDependOnLibsWithTags: ['scope:shipping', 'scope:shared', 'scope:catalog'] },
        { sourceTag: 'scope:shared', onlyDependOnLibsWithTags: ['scope:shared'] },
      ],
    }],
  },
}];
"""


def put(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def project(name, tags, targets=None):
    return json.dumps({"name": name, "tags": tags, "targets": targets or {"test": {"executor": "@nx/jest:jest"}, "lint": {}}})


def domains_repo() -> dict:
    f = {
        "package.json": json.dumps({"name": "acme", "devDependencies": {"nx": "20.0.0", "@angular/core": "20.0.0",
                                                                         "jest": "29.0.0", "typescript": "5.5.0"}}),
        "nx.json": "{}", "tsconfig.base.json": TSCONFIG, "eslint.config.mjs": ESLINT,
        "CODEOWNERS": "# owners\n/domains/billing/ @acme/billing-team\n",
        "libs/shared/ui/project.json": project("shared-ui", ["scope:shared", "type:ui"]),
        "libs/shared/ui/src/index.ts": "export const ui = 1;\n",
        "libs/shared/util/project.json": project("shared-util", ["scope:shared", "type:util"]),
        "apps/web/project.json": project("web", ["scope:app"]),
        "apps/api/project.json": project("api", ["scope:app"]),
        "domains/catalog/shared/src/index.ts": "export const price = 1;\n",
    }
    for d in ("billing", "catalog", "shipping"):
        extra = {"generate-api": {"executor": "nx:run-commands"}} if d == "billing" else {}
        f[f"domains/{d}/project.json"] = project(d, [f"scope:{d}", "type:domain"],
                                                 {"test": {"executor": "@nx/jest:jest"}, "lint": {}, **extra})
        f[f"domains/{d}/src/index.ts"] = f"export const {d} = 1;\n"
        f[f"domains/{d}/README.md"] = f"# {d}\n"
    f["domains/billing/src/pay.ts"] = ("import { ui } from '@acme/shared/ui';\nimport { price } from '@acme/catalog/shared';\n"
                                       "import { shipping } from '@acme/shipping';\n")
    f["domains/shipping/src/ship.ts"] = "import { catalog } from '@acme/catalog';\n"
    f["domains/billing/src/generated-api/api.ts"] = "// generated\n"
    f["domains/billing/src/config/flag-parts/billing.ts"] = "export const f = 1;\n"
    f["domains/billing/src/app.routes.ts"] = "export const routes = [];\n"
    return f


def libs_repo() -> dict:
    f = {"package.json": json.dumps({"name": "acme", "devDependencies": {"nx": "20.0.0"}}), "nx.json": "{}",
         "eslint.config.mjs": ESLINT, "libs/shared/ui/project.json": project("shared-ui", ["scope:shared"]),
         "libs/shared/util/project.json": project("shared-util", ["scope:shared"])}
    for d in ("billing", "catalog", "shipping"):
        for lib in ("feature", "data-access"):
            f[f"libs/{d}/{lib}/project.json"] = project(f"{d}-{lib}", [f"scope:{d}"])
            f[f"libs/{d}/{lib}/src/index.ts"] = "export {};\n"
    return f


def ambiguous_repo() -> dict:
    f = {"package.json": "{}", "nx.json": "{}"}
    for parent in ("domains", "modules"):
        for d in ("a", "b", "c"):
            f[f"{parent}/{d}/project.json"] = project(f"{parent}-{d}", [])
    return f


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", cwd=cwd)


def scan_json(repo: Path):
    r = run("scan", "--root", repo, "--json")
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}), r


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)

        # DS-1: Nx domains/* — high confidence, facts from boundaries, paths, imports, targets
        a = base / "a"
        put(a, domains_repo())
        code, out, r = scan_json(a)
        check(code == 0, f"DS-1: exit 0, got {code}: {r.stderr[-400:]}")
        best = out.get("best", {})
        check(best.get("glob") == "domains/*" and best.get("kind") == "dir-per-project", f"DS-1: layout {best.get('glob')}")
        doms = best.get("domains", {})
        check(sorted(doms) == ["billing", "catalog", "shipping"], f"DS-1: domains {sorted(doms)}")
        b = doms.get("billing", {})
        check(b.get("root") == "domains/billing", "DS-1: root with slash")
        check(any(e["alias"] == "@acme/billing" for e in b.get("entrypoints", [])), "DS-1: entrypoint alias")
        check(any(e["alias"] == "@acme/catalog/shared" for e in doms["catalog"]["entrypoints"]), "DS-1: shared entrypoint")
        check("scope:shared" in b.get("allowed", {}).get("tags", []), "DS-1: allowed tags from depConstraints")
        check("@acme/catalog/shared" in b["allowed"].get("allow_entrypoints", []), "DS-1: allow list")
        check("catalog" in doms["shipping"]["allowed"].get("domains", []), "DS-1: shipping may import catalog")
        viol = [(v["to"], v["spec"]) for v in b.get("violations", [])]
        check(viol == [("shipping", "@acme/shipping")], f"DS-1: violations {viol}")
        check(not doms["shipping"].get("violations"), "DS-1: no false violation for shipping")
        check(any(i["to"] == "catalog" for i in b.get("imports", [])), "DS-1: actual import counted")
        check(b["commands"].get("test") == "npx nx test billing", f"DS-1: test command {b['commands']}")
        check("--testFile" in b["commands"].get("test_file", ""), "DS-1: single test command")
        check(any("generate-api" in c for c in b["commands"].get("generate", [])), "DS-1: generate target")
        check(any("generated-api" in g for g in b["signals"].get("generated", [])), "DS-1: generated dir")
        check(any("flag-parts" in g for g in b["signals"].get("flags", [])), "DS-1: flags dir")
        check(any("routes" in g for g in b["signals"].get("routes", [])), "DS-1: routes")
        check(b["signals"].get("owners") == ["@acme/billing-team"], f"DS-1: owners {b['signals'].get('owners')}")
        check("README.md" in b["signals"].get("docs", []), "DS-1: docs")
        check(any(alt.get("glob") == "apps/*" for alt in out.get("alternatives", [])), "DS-1: alternatives listed")
        check(all("\\" not in json.dumps(d) for d in doms.values()), "DS-1: POSIX paths only")

        # DS-2: libs/<domain>/<lib> is a different layout
        c = base / "c"
        put(c, libs_repo())
        code, out, r = scan_json(c)
        best = out.get("best", {})
        check(code == 0 and best.get("kind") == "grouped-libs" and best.get("glob") == "libs/*",
              f"DS-2: {code} {best.get('kind')} {best.get('glob')}")
        check(sorted(best.get("domains", {})) == ["billing", "catalog", "shipping"], f"DS-2: domains {sorted(best.get('domains', {}))}")

        # DS-3: ambiguous layouts and no Nx -> exit 1 with candidates
        d = base / "d"
        put(d, ambiguous_repo())
        code, out, r = scan_json(d)
        check(code == 1 and len(out.get("alternatives", [])) + (1 if out.get("best") else 0) >= 2, f"DS-3: exit {code}")
        e = base / "e"
        put(e, {"package.json": json.dumps({"workspaces": ["packages/*"]}), "packages/x/package.json": '{"name":"x"}',
                "packages/y/package.json": '{"name":"y"}', "packages/x/a.ts": "", "packages/y/a.ts": ""})
        code, out, r = scan_json(e)
        check(code == 1 and out.get("confidence") == "low", f"DS-3: no Nx is low confidence, exit {code}")
        put(e, {".tf/config/domains.yaml": "layout: {glob: \"packages/*\"}\ndomains:\n  x: {scope: \"Owns X.\", owner: \"team-x\"}\nexclude: [y]\n"})
        code, out, r = scan_json(e)
        check(code == 0 and out.get("source") == "config", f"DS-3: domains.yaml gives exit 0, got {code}: {r.stderr[-300:]}")
        check(list(out.get("best", {}).get("domains", {})) == ["x"], f"DS-3: exclude honoured {out.get('best', {}).get('domains', {}).keys()}")
        check(out.get("best", {}).get("domains", {}).get("x", {}).get("human", {}).get("scope") == "Owns X.", "DS-3: scope from config")
        check(run("scan", "--root", base / "nonexistent").returncode == 2, "DS-3: call error -> exit 2")

        # DS-4: plan / write / write again / human edit / drift / CLAUDE.md
        pk = "tools/tf-pack"
        args = ("--root", a, "--pack-dir", pk, "--project-id", "acme", "--core-version", "20.2.0")
        p = run("plan", *args, "--json")
        check(p.returncode == 0, f"DS-4: plan exit {p.returncode}: {p.stderr[-300:]}")
        plan = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {"files": [{"state": "?"}]}
        check(all(f["state"] == "new" for f in plan["files"]) and not (a / "domains/billing/AGENTS.md").exists(),
              "DS-4: plan is a dry run")
        put(a, {"domains/catalog/CLAUDE.md": "# my own\n"})
        w = run("write", *args)
        check(w.returncode == 0, f"DS-4: write exit {w.returncode}: {w.stderr[-300:]}")
        ag = a / "domains/billing/AGENTS.md"
        txt = ag.read_text(encoding="utf-8") if ag.is_file() else ""
        check("tf:domain-agents v1 sha256=" in txt, "DS-4: AGENTS.md with a marker")
        check("TODO(human): one sentence" in txt and "npx nx test billing" in txt and "@acme/shipping" in txt
              and "generate-api" in txt, "DS-4: AGENTS.md content")
        cm = a / "domains/billing/CLAUDE.md"
        check(cm.is_file() and cm.read_text(encoding="utf-8").strip() == "@AGENTS.md", "DS-4: CLAUDE.md import")
        check((a / "domains/catalog/CLAUDE.md").read_text(encoding="utf-8") == "# my own\n", "DS-4: existing CLAUDE.md untouched")
        check("@AGENTS.md" in w.stdout and "catalog/CLAUDE.md" in w.stdout, "DS-4: advice about CLAUDE.md without import")
        for rel in ("pack.yaml", "personas/billing.yaml", "personas/acme.yaml", "skills/acme-domain-routing/SKILL.md",
                    "tests/skill_evals/acme-domain-routing.json", "README.md"):
            check((a / pk / "pack-acme" / rel).is_file(), f"DS-4: pack file {rel}")
        pyp = a / pk / "pack-acme" / "pack.yaml"
        pj = pyp.read_text(encoding="utf-8") if pyp.is_file() else ""
        check('">=20.0.0 <22.0.0"' in pj and "optional_packs: [pack-it]" in pj, "DS-4: requires from the core version")
        w2 = run("write", *args, "--json")
        files2 = json.loads(w2.stdout)["files"] if w2.stdout.strip().startswith("{") else []
        check(files2 and all(f["state"] == "unchanged" for f in files2 if f["path"] != "domains/catalog/CLAUDE.md"), f"DS-4: second write unchanged: {w2.stdout[:300]}")
        ag.write_text(txt.replace("TODO(human): one sentence", "Billing. [to confirm]"), encoding="utf-8")
        w3 = run("write", *args, "--json")
        st = {f["path"]: f["state"] for f in json.loads(w3.stdout)["files"]} if w3.stdout.strip().startswith("{") else {}
        check(st.get("domains/billing/AGENTS.md") == "kept", f"DS-4: human edit kept: {st}")
        check((a / "domains/billing/AGENTS.md.tf-new").is_file() and "Billing. [to confirm]" in ag.read_text(encoding="utf-8"),
              "DS-4: .tf-new written, edit preserved")
        ck = run("check", *args)
        check(ck.returncode == 0, f"DS-4: a human edit alone is not drift: {ck.stdout[-300:]}")
        put(a, {"domains/inventory/project.json": project("inventory", ["scope:inventory"]),
                "domains/inventory/src/index.ts": "export {};\n"})
        ck = run("check", *args)
        check(ck.returncode == 1 and "inventory" in ck.stdout, f"DS-4: new domain is drift: {ck.stdout[-300:]}")
        shutil.rmtree(a / "domains/inventory")
        shutil.rmtree(a / "domains/shipping")
        ck = run("check", *args)
        check(ck.returncode == 1 and "shipping" in ck.stdout, f"DS-4: removed domain reported: {ck.stdout[-300:]}")

        # DS-5: the generated pack installs and passes build.py check
        if (ROOT / ".tf" / "factory" / "install.py").is_file():
            proj = base / "proj"
            shutil.copytree(ROOT / ".tf", proj / ".tf", ignore=shutil.ignore_patterns("__pycache__", "backup", "cache", "logs", "runs"))
            shutil.copytree(ROOT / ".claude", proj / ".claude", ignore=shutil.ignore_patterns("__pycache__", "logs"))
            subprocess.run(["git", "init", "-q"], cwd=proj, check=False)
            put(proj, domains_repo())
            pa = ("--root", proj, "--pack-dir", pk, "--project-id", "acme")
            w = run("write", *pa)
            check(w.returncode == 0, f"DS-5: write in the project: {w.stderr[-300:]}")
            ins = subprocess.run([sys.executable, ".tf/factory/update.py", "--yes", "--pack-dir", pk, "--add", "pack-acme"],
                                 cwd=proj, capture_output=True, text=True, encoding="utf-8", timeout=600)
            check(ins.returncode == 0, f"DS-5: install: {(ins.stdout + ins.stderr)[-800:]}")
            bc = subprocess.run([sys.executable, ".tf/factory/build.py", "check"], cwd=proj, capture_output=True,
                                text=True, encoding="utf-8", timeout=600)
            check(bc.returncode == 0, f"DS-5: build.py check: {(bc.stdout + bc.stderr)[-1200:]}")
            gen = proj / ".claude" / "agents" / "_generated"
            for ag_name in ("billing-frontend", "catalog-frontend", "shipping-frontend", "acme"):
                check(any(gen.glob(f"**/{ag_name}.md")), f"DS-5: generated agent {ag_name}")
            check((proj / ".claude/skills/acme-domain-routing/SKILL.md").is_file(), "DS-5: routing skill installed")
            disp = next(iter(gen.glob("**/acme.md")), None)
            check(disp is not None and "billing-frontend" in disp.read_text(encoding="utf-8"), "DS-5: dispatcher reaches domain agents")
        else:
            print("  (DS-5 skipped: no .tf/factory in this tree)")

    for m in fails:
        print(f"✗ {m}")
    print(f"{'✓' if not fails else '✗'} domain_scan: {total - len(fails)}/{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
