#!/usr/bin/env python3
"""Testy generatora nakładki firmowej: `org/new_org_pack.py <firma> --out <katalog>` — szablon
`org/template/` z polami do uzupełnienia, odmowy (katalog w repo fabryki, istniejący katalog, zła nazwa,
zajęty prefiks) i cała droga: instalacja w projekcie przez `install.py --pack-dir` i domyślne organizacji
(`org_defaults`) w konfiguracji projektu. python3 tests/test_new_org_pack.py"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())


def gen(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "org" / "new_org_pack.py"), *args],
                          cwd=ROOT, capture_output=True, text=True, timeout=60)


def packs_mod(factory: Path):
    spec = importlib.util.spec_from_file_location(f"op_packs_{id(factory)}", factory / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(factory))
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        out = base / "acme-factory"
        r = gen("acme", "--out", str(out), "--title", "ACME Sp. z o.o.")
        check(r.returncode == 0, f"OP-1: generator działa: {r.stdout}{r.stderr}")
        files = ["pack.yaml", "README.md", "settings.json", "skills/acme-standardy/SKILL.md",
                 "tests/skill_evals/acme-standardy.json", "analyzers/acme-standardy/analyzer.yaml",
                 "analyzers/acme-standardy/rules.yaml", "analyzers/acme-standardy/fixtures/naruszenia/expected.json",
                 "analyzers/acme-standardy/fixtures/czyste/expected.json", "semgrep.yml",
                 *(f"skills/acme-standardy/references/{a}.md" for a in ("ui", "api", "data", "releases"))]
        check(all((out / f).is_file() for f in files), f"OP-1: pliki: {[f for f in files if not (out / f).is_file()]}")
        left = [str(f.relative_to(out)) for f in out.rglob("*") if f.is_file() and "{{" in f.read_text(encoding="utf-8")]
        check(not left, f"OP-2: wszystkie pola szablonu podstawione: {left}")
        pm = packs_mod(ROOT / "core" / "factory")
        pack = pm.load_yaml(out / "pack.yaml") if (out / "pack.yaml").is_file() else {}
        major = int((ROOT / "core" / "factory" / "VERSION").read_text(encoding="utf-8").split(".")[0])
        check(pack.get("id") == "pack-acme" and pack.get("title") == "ACME Sp. z o.o."
              and str(pack.get("requires", {}).get("core", "")).endswith(f"<{major + 1}.0.0")
              and isinstance(pack.get("org_defaults"), dict)
              and set(pack["org_defaults"].get("config") or {}) <= set(pm.ORG_CONFIG_KEYS),
              f"OP-3: pack.yaml z id, tytułem, zakresem rdzenia i org_defaults z dozwolonymi kluczami: {pack}")
        check("acme-standardy" in json.dumps(pack.get("contributes", {})),
              f"OP-4: standardy firmy trafiają do każdej persony (contributes): {pack.get('contributes')}")
        try:
            json.loads((out / "settings.json").read_text(encoding="utf-8"))
            ev = json.loads((out / "tests" / "skill_evals" / "acme-standardy.json").read_text(encoding="utf-8"))
            ok = ev.get("skill") == "acme-standardy" and len(ev.get("scenarios", [])) >= 3
        except (OSError, ValueError):
            ok = False
        check(ok, "OP-5: settings.json i scenariusze to poprawny JSON, scenariusze dla skilla standardów")
        spis = (out / "skills/acme-standardy/SKILL.md").read_text(encoding="utf-8") if (out / "skills/acme-standardy/SKILL.md").is_file() else ""
        check(all(f"references/{a}.md" in spis for a in ("ui", "api", "data", "releases")) and len(spis.splitlines()) < 60,
              f"OP-15: SKILL.md to krótki spis wskazujący plik każdego obszaru: {len(spis.splitlines())} linii")

        # odmowy: bez zmian na dysku
        r = gen("acme", "--out", str(out))
        check(r.returncode == 2 and "exists" in r.stdout + r.stderr, f"OP-6: istniejący katalog → kod 2: {r.stdout}{r.stderr}")
        inside = ROOT / ".work" / "org-test-should-not-exist"
        r = gen("acme", "--out", str(inside))
        check(r.returncode == 2 and not inside.exists(), f"OP-7: katalog w repo fabryki → kod 2: {r.stdout}{r.stderr}")
        r = gen("Acme Corp", "--out", str(base / "x"))
        check(r.returncode == 2 and not (base / "x").exists(), f"OP-8: zła nazwa → kod 2: {r.stdout}{r.stderr}")
        r = gen("firma", "--prefix", "core-", "--out", str(base / "y"))
        check(r.returncode == 2 and not (base / "y").exists(), f"OP-9: zajęty prefiks → kod 2: {r.stdout}{r.stderr}")

        # cała droga: instalacja w projekcie i domyślne organizacji w konfiguracji
        (out / "sources").mkdir()
        (out / "sources" / "api.md").write_text("# Standard API (poufne)\n", encoding="utf-8")
        app = base / "app"
        app.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=app, check=True)
        r = subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(app), "--yes",
                            "--language", "en", "--packs", "pack-acme", "--pack-dir", str(out)],
                           capture_output=True, text=True, timeout=300)
        check(r.returncode == 0 and (app / ".tf/factory/packs/pack-acme/pack.yaml").is_file()
              and (app / ".claude/skills/acme-standardy/SKILL.md").is_file(),
              f"OP-10: instalacja nakładki firmowej przez --pack-dir: {(r.stdout + r.stderr)[-1500:]}")
        if r.returncode == 0:
            pa = packs_mod(app / ".tf" / "factory")
            labels = [lbl for lbl, _ in pa.config_layers(app)]
            comp = pa.compose(app, pa.load_config(app))
            check(any("pack-acme" in lbl and "org_defaults" in lbl for lbl in labels)
                  and not [e for e in comp["_errors"] if "org_defaults" in e],
                  f"OP-11: warstwa organizacji w konfiguracji projektu, bez błędów składania: {labels} {comp['_errors']}")
            # standardy sprawdzane bez modelu: moduł reguł nakładki działa w projekcie i przechodzi swoją bramkę
            an = pa.load_yaml(app / ".tf/factory/analyzers/acme-standardy/analyzer.yaml") \
                if (app / ".tf/factory/analyzers/acme-standardy/analyzer.yaml").is_file() else {}
            leaked = [str(f) for f in app.rglob("*") if f.is_file() and ".git" not in f.parts
                      and "Standard API (poufne)" in f.read_text(encoding="utf-8", errors="ignore")]
            check(not leaked, f"OP-16: dokumenty źródłowe firmy (sources/) nie trafiają do projektu: {leaked}")
            check((app / ".tf/factory/packs/pack-acme/semgrep.yml").is_file(),
                  "OP-14: semgrep.yml nakładki w .tf/factory/packs/pack-acme/ (skan kawałka pętli /tf)")
            check(an.get("prefix") == "ACME" and (an.get("tier0") or {}).get("rules") == "rules.yaml",
                  f"OP-12: moduł reguł firmy zainstalowany, prefiks ustaleń z nazwy firmy: {an}")
            g = subprocess.run([sys.executable, str(app / ".tf/factory/analyze.py"), "gate", "--module", "acme-standardy"],
                               cwd=app, capture_output=True, text=True, timeout=120)
            check(g.returncode == 0, f"OP-13: bramka modułu reguł na przykładach z szablonu: {g.stdout[-600:]}{g.stderr[-300:]}")
        # warstwa zespołu: nakładka zespołu na bazie firmowej (silnik ← firma ← zespół ← projekt ← osoba)
        team = base / "acme-backend-factory"
        r = gen("acme", "--team", "backend", "--out", str(team), "--title", "ACME Backend")
        check(r.returncode == 0 and (team / "pack.yaml").is_file()
              and (team / "skills/backend-standardy/SKILL.md").is_file()
              and (team / "analyzers/acme-backend-standardy/rules.yaml").is_file(),
              f"OP-17: generator nakładki zespołu (--team): {r.stdout}{r.stderr}")
        left = [str(f.relative_to(team)) for f in team.rglob("*") if f.is_file() and "{{" in f.read_text(encoding="utf-8")]
        check(not left, f"OP-17: wszystkie pola szablonu zespołu podstawione: {left}")
        tp = pm.load_yaml(team / "pack.yaml") if (team / "pack.yaml").is_file() else {}
        check(tp.get("id") == "pack-acme-backend" and "pack-acme" in ((tp.get("requires") or {}).get("packs") or [])
              and isinstance(tp.get("team_defaults"), dict) and "org_defaults" not in tp
              and set((tp.get("team_defaults") or {}).get("config") or {}) <= set(pm.ORG_CONFIG_KEYS),
              f"OP-18: pack.yaml zespołu: id, wymaga nakładki firmy, team_defaults z dozwolonymi kluczami: {tp}")
        r = gen("acme", "--team", "Back End", "--out", str(base / "z1"))
        check(r.returncode == 2 and not (base / "z1").exists(), f"OP-19: zła nazwa zespołu → kod 2: {r.stdout}{r.stderr}")
        r = gen("acme", "--team", "web", "--prefix", "fe-", "--out", str(base / "z2"))
        check(r.returncode == 2 and not (base / "z2").exists(), f"OP-19: zajęty prefiks zespołu → kod 2: {r.stdout}{r.stderr}")
        if isinstance(tp.get("team_defaults"), dict):
            td = tp["team_defaults"]
            td["config"] = {**(td.get("config") or {}), "task": {"allowed_modes": ["plan", "zwykly"]},
                            "autonomy": {"operations": {"git_push": "deny"}}}
            td["operations"] = {"tracker": {"prefixes": {"BE": "jira"}}}
            (team / "pack.yaml").write_text(pm.yaml.safe_dump(tp, allow_unicode=True, sort_keys=False), encoding="utf-8")
        app2 = base / "app2"
        app2.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=app2, check=True)
        r = subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(app2), "--yes",
                            "--language", "en", "--packs", "pack-acme-backend", "--pack-dir", str(out),
                            "--pack-dir", str(team)], capture_output=True, text=True, timeout=300)
        check(r.returncode == 0 and (app2 / ".tf/factory/packs/pack-acme/pack.yaml").is_file()
              and (app2 / ".tf/factory/packs/pack-acme-backend/pack.yaml").is_file(),
              f"OP-20: instalacja nakładki zespołu dociąga nakładkę firmy: {(r.stdout + r.stderr)[-1500:]}")
        if r.returncode == 0:
            (app2 / ".tf/config").mkdir(parents=True, exist_ok=True)
            (app2 / ".tf/config/config.yaml").write_text("task:\n  allowed_modes: [plan, zwykly, auto]\n",
                                                         encoding="utf-8")
            pa = packs_mod(app2 / ".tf" / "factory")
            labels = [lbl for lbl, _ in pa.config_layers(app2)]
            org_i = next((i for i, l in enumerate(labels) if "org_defaults" in l), -1)
            team_i = next((i for i, l in enumerate(labels) if "team_defaults" in l), -1)
            proj_i = next((i for i, l in enumerate(labels) if l.endswith(".tf/config/config.yaml")), -1)
            check(0 < org_i < team_i < proj_i, f"OP-21: kolejność warstw silnik ← firma ← zespół ← projekt: {labels}")
            ws = pa.work_style(app2)
            check(ws["allowed_modes"] == ["plan", "zwykly"],
                  f"OP-22: dozwolone tryby to przecięcie warstw — projekt nie przywraca Auto zabranego przez zespół: {ws}")
            guard = importlib.util.spec_from_file_location("op_guard", app2 / ".claude/hooks/guard_bash.py")
            gm = importlib.util.module_from_spec(guard)
            guard.loader.exec_module(gm)
            levels, _w = gm.load_policy(app2)
            check(levels.get("git_push") == "deny", f"OP-23: zespół zaostrza politykę autonomii: {levels}")
            ops = pa.org_operations(app2)
            check((ops.get("tracker") or {}).get("prefixes") == {"BE": "jira"} and (ops.get("tracker") or {}).get("type"),
                  f"OP-24: tracker zespołu nadpisuje prefiksy firmy, reszta zostaje z firmy: {ops}")
            comp = pa.compose(app2, pa.load_config(app2))
            check(not [e for e in comp["_errors"] if "defaults" in e], f"OP-24: składanie bez błędów: {comp['_errors']}")
            env = {**os.environ, "TF_PREFERENCES": str(base / "none.yaml")}
            r = subprocess.run([sys.executable, str(app2 / ".tf/factory/tf.py"), "config", "show"], cwd=app2,
                               capture_output=True, text=True, timeout=120, env=env)
            check(any(ln.split()[:2] == ["task", "projekt"] for ln in r.stdout.splitlines())
                  and "zespół" in r.stdout, f"OP-25: tf config show zna źródło „zespół”: {r.stdout}{r.stderr}")
            g = subprocess.run([sys.executable, str(app2 / ".tf/factory/analyze.py"), "gate", "--module",
                                "acme-backend-standardy"], cwd=app2, capture_output=True, text=True, timeout=120)
            check(g.returncode == 0, f"OP-26: bramka modułu reguł zespołu: {g.stdout[-600:]}{g.stderr[-300:]}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów new-org-pack")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
