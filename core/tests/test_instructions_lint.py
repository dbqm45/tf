#!/usr/bin/env python3
"""Testy skryptu instructions_lint (skill core-agent-instructions): karta kontroli plików instrukcji agenta."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills").is_dir())
LINT = ROOT / ".claude" / "skills" / "core-agent-instructions" / "scripts" / "instructions_lint.py"


def run(*args):
    return subprocess.run([sys.executable, str(LINT), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", timeout=30)


def checks(data, name):
    """Zwraca słownik kontroli dla pliku o nazwie kończącej się na `name`."""
    for f in data["files"]:
        if f["path"].replace("\\", "/").endswith(name):
            return {c["id"]: c for c in f["checks"]}
    raise KeyError(name)


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main() -> int:
    fails = []
    total = 0

    def ok(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        # 1. dobry, krótki plik: wszystko OK, kod 0
        good = root / "good" / "CLAUDE.md"
        write(good, "# Zasady\n- Nigdy nie commituj `.env`.\n- Test: `npm test`.\n\n## Konwencje\n"
                    "- Błędy API: `{ error: { code, message } }` (wzorzec: `src/api/errors.ts`).\n")
        r = run(good, "--json")
        ok(r.returncode == 0, f"dobry plik: oczekiwany kod 0, jest {r.returncode}: {r.stdout}{r.stderr}")
        try:
            data = json.loads(r.stdout)
            c = checks(data, "good/CLAUDE.md")
            ok(all(c[k]["verdict"] == "OK" for k in ("length", "blocks", "intents", "order")),
               f"dobry plik: oczekiwane same OK: {c}")
        except Exception as e:  # noqa: BLE001
            ok(False, f"dobry plik: niepoprawny JSON ({e}): {r.stdout[:300]}")

        # 2. długość: 520 niepustych linii → ERROR, kod 1; komentarze HTML nie liczą się do długości
        long_ = root / "long" / "CLAUDE.md"
        write(long_, "# Zasady\n" + "".join(f"- reguła {i}\n" for i in range(520)))
        r = run(long_, "--json")
        ok(r.returncode == 1, f"długi plik: oczekiwany kod 1, jest {r.returncode}")
        c = checks(json.loads(r.stdout), "long/CLAUDE.md")
        ok(c["length"]["verdict"] == "ERROR" and c["length"]["value"] >= 520, f"długi plik: {c['length']}")
        commented = root / "comm" / "CLAUDE.md"
        write(commented, "# Zasady\n<!--\n" + "notatka dla ludzi\n" * 300 + "-->\n- Nigdy nie loguj danych klienta.\n")
        c = checks(json.loads(run(commented, "--json").stdout), "comm/CLAUDE.md")
        ok(c["length"]["verdict"] == "OK", f"komentarz HTML liczony do długości: {c['length']}")

        # 3. bloki kodu > 3 linii (mermaid pominięty) → 3 bloki = ERROR
        block = "```json\n{\n  \"a\": 1,\n  \"b\": 2\n}\n```\n"
        mermaid = "```mermaid\ngraph TD\nA-->B\nB-->C\nC-->D\n```\n"
        blocks = root / "blocks" / "AGENTS.md"
        write(blocks, "# Zasady\n- Nigdy nie edytuj `generated/`.\n" + block * 3 + mermaid + "```bash\nnpm test\n```\n")
        c = checks(json.loads(run(blocks, "--json").stdout), "blocks/AGENTS.md")
        ok(c["blocks"]["value"] == 3 and c["blocks"]["verdict"] == "ERROR", f"bloki kodu: {c['blocks']}")

        # 4. intencje PL/EN → 4 trafienia = ERROR, z numerami linii
        intents = root / "intents" / "CLAUDE.md"
        write(intents, "# Zasady\n- Pisz czysty kod.\n- Stosuj dobre praktyki.\n- Follow best practices.\n"
                       "- Write clean code always.\n- Nigdy nie usuwaj migracji.\n")
        c = checks(json.loads(run(intents, "--json").stdout), "intents/CLAUDE.md")
        ok(c["intents"]["value"] == 4 and c["intents"]["verdict"] == "ERROR", f"intencje: {c['intents']}")
        ok(any(f.get("line") == 2 for f in c["intents"].get("findings", [])), f"intencje bez numeru linii: {c['intents']}")

        # 5. kolejność: krytyczna reguła po linii 200 → ERROR; brak nagłówków w długim pliku → ERROR
        late = root / "late" / "CLAUDE.md"
        write(late, "# O projekcie\n" + "".join(f"Opis {i}.\n" for i in range(240)) + "- Nigdy nie wysyłaj danych klienta do logów.\n")
        c = checks(json.loads(run(late, "--json").stdout), "late/CLAUDE.md")
        ok(c["order"]["verdict"] == "ERROR", f"kolejność (reguła po linii 200): {c['order']}")
        flat = root / "flat" / "CLAUDE.md"
        write(flat, "- Nigdy nie commituj sekretów.\n" + "".join(f"- punkt {i}\n" for i in range(60)))
        c = checks(json.loads(run(flat, "--json").stdout), "flat/CLAUDE.md")
        ok(c["order"]["verdict"] == "ERROR", f"kolejność (brak nagłówków): {c['order']}")

        # 6. importy @: brakujący wykryty, w odwrotnych apostrofach pominięty, istniejący doliczony do długości efektywnej
        imp = root / "imp"
        write(imp / "docs" / "api.md", "".join(f"linia {i}\n" for i in range(30)))
        write(imp / "CLAUDE.md", "# Zasady\n- Nigdy nie zmieniaj API bez ADR.\n- API: @docs/api.md\n"
                                 "- Brak: @docs/nie-ma.md\n- Tekst: `@README.md` (bez importu)\n")
        c = checks(json.loads(run(imp / "CLAUDE.md", "--json").stdout), "imp/CLAUDE.md")
        imports = c["imports"]
        missing = [f["target"] for f in imports.get("findings", []) if f.get("missing")]
        ok(missing == ["docs/nie-ma.md"], f"importy: brakujące {missing}")
        ok("README.md" not in json.dumps(imports), f"import w odwrotnych apostrofach nie powinien się liczyć: {imports}")
        ok(imports.get("effective_lines", 0) >= 30 + 4, f"długość z importami nie dolicza importu: {imports}")

        # 7. tryb katalogu: znajduje pliki (także .claude/rules), pomija node_modules, sprawdza indeks i duplikaty
        repo = root / "repo"
        write(repo / "CLAUDE.md", "# Zasady\n- Nigdy nie edytuj plików w packages/*/generated/.\n"
                                  "- Commity z prefiksem pakietu, np. `api: dodaj limit`.\n\n## Moduły z własnym CLAUDE.md\n"
                                  "- `packages/api/CLAUDE.md` — API i baza.\n")
        write(repo / "packages" / "api" / "CLAUDE.md", "Tylko kontekst api.\n- Zapytania przez Knex, bez surowego SQL.\n")
        write(repo / "packages" / "cli" / "CLAUDE.md", "Tylko kontekst cli.\n"
                                                       "- Commity z prefiksem pakietu, np. `api: dodaj limit`.\n")
        write(repo / ".claude" / "rules" / "tests.md", "---\npaths:\n  - \"**/*.test.ts\"\n---\n- Testy bez sieci.\n")
        write(repo / "node_modules" / "x" / "CLAUDE.md", "# obce\n")
        r = run("--root", repo, "--json")
        data = json.loads(r.stdout)
        paths = sorted(f["path"].replace("\\", "/") for f in data["files"])
        ok(any(p.endswith(".claude/rules/tests.md") for p in paths), f"tryb katalogu: brak reguły z .claude/rules: {paths}")
        ok(not any("node_modules" in p for p in paths), f"tryb katalogu: node_modules nie pominięte: {paths}")
        repo_issues = json.dumps(data.get("repo", {}), ensure_ascii=False)
        ok("packages/cli/CLAUDE.md" in repo_issues and "packages/api/CLAUDE.md" not in repo_issues.split("unindexed")[-1][:200],
           f"tryb katalogu: indeks roota — oczekiwany tylko cli poza indeksem: {repo_issues}")
        ok("Commity z prefiksem" in repo_issues, f"tryb katalogu: duplikat linii root↔moduł niewykryty: {repo_issues}")

        # 8. wyjście tekstowe: tabela z werdyktami; --help; zła ścieżka → kod 2
        r = run(intents)
        ok("intents" in r.stdout and "ERROR" in r.stdout and "intents/CLAUDE.md" in r.stdout.replace("\\", "/"),
           f"wyjście tekstowe: {r.stdout[:400]}")
        ok(run("--help").returncode == 0, "--help powinien kończyć się kodem 0")
        ok(run(root / "nie-ma.md").returncode == 2, "nieistniejący plik: oczekiwany kod 2")

    # nieaktualne odwołania (krok H21): ścieżki i polecenia, których w repozytorium już nie ma; blok fabryki pominięty
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        write(r / "src" / "app.py", "x = 1\n")
        write(r / "package.json", json.dumps({"scripts": {"test": "vitest", "lint": "eslint ."}}))
        write(r / "Makefile", "build:\n\techo b\n")
        write(r / "CLAUDE.md", "# Zasady\n\n## Komendy\n- Test: `npm test` · Lint: `npm run lint` · Typy: `npm run typecheck`\n"
              "- Build: `make build` · Wydanie: `make release`\n\n## Mapa\n- Kod w `src/app.py`, stare w `src/legacy.py` "
              "i `lib/old/`; adres `https://example.com/a/b`, wzór `src/<moduł>/*.py`, opcja `--dry-run`\n"
              "- Nie czytaj: `vendor/`, `dist/` · skrypt `semver.py` · punkt kontrolny w `docs/project/wip/`\n\n"
              "<!-- team-factory:begin -->\n- Nie czytaj `node_modules/` ani `.tf/wip/nie-ma.md`\n<!-- team-factory:end -->\n")
        res = run("--root", r, "--json")
        data = json.loads(res.stdout)
        c = checks(data, "CLAUDE.md").get("stale") or {}
        found = sorted(f.get("text", "") for f in c.get("findings") or [])
        ok(c.get("verdict") == "WARN" and any("src/legacy.py" in x for x in found) and any("lib/old/" in x for x in found)
           and any("typecheck" in x for x in found) and any("release" in x for x in found) and len(found) == 4,
           f"nieaktualne: brakujące pliki, katalogi, skrypt npm i cel make; bez adresów, wzorców, opcji i bloku fabryki: {c}")
        ok(res.returncode == 0, f"stale to WARN, nie ERROR (kod 0 bez --strict): {res.returncode}")
        write(r / "CLAUDE.md", "# Zasady\n\n- Kod w `src/app.py`, test: `npm test`, build: `make build`\n")
        c = checks(json.loads(run("--root", r, "--json").stdout), "CLAUDE.md").get("stale") or {}
        ok(c.get("verdict") == "OK" and not c.get("findings"), f"nieaktualne: aktualne odwołania → OK: {c}")

    # tf doctor pokazuje kartę instrukcji projektu w jednej linii na plik (informacja; krok H21)
    ctf = ROOT / ".tf" / "factory" / "tf.py"
    if ctf.is_file():
        import os
        import shutil
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            shutil.copytree(ROOT / ".tf" / "factory", r / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(LINT.parent.parent, r / ".claude" / "skills" / "core-agent-instructions")
            write(r / ".claude" / "factory-manifest.json", json.dumps({"version": "0", "packs": {}, "files": {}}))
            write(r / "CLAUDE.md", "# Zasady\n\n- Kod w `src/stary.py`\n")
            res = subprocess.run([sys.executable, str(r / ".tf" / "factory" / "tf.py"), "doctor"], cwd=r, capture_output=True,
                                 text=True, encoding="utf-8", timeout=300, env={**os.environ, "CLAUDE_PROJECT_DIR": str(r)})
            line = next((ln for ln in res.stdout.splitlines() if "instrukcje" in ln), "")
            ok("CLAUDE.md" in line and "stale" in line and "instructions_lint.py --root" in res.stdout
               and "Traceback" not in res.stderr,
               f"tf doctor: linia o instrukcjach projektu z nazwą kontroli i poleceniem szczegółów: {res.stdout[-800:]} {res.stderr[-300:]}")
            write(r / "CLAUDE.md", "# Zasady\n\n- Testy: `python3 -m unittest`\n")
            res = subprocess.run([sys.executable, str(r / ".tf" / "factory" / "tf.py"), "doctor"], cwd=r, capture_output=True,
                                 text=True, encoding="utf-8", timeout=300, env={**os.environ, "CLAUDE_PROJECT_DIR": str(r)})
            ok(any("instrukcje" in ln and "✓" in ln for ln in res.stdout.splitlines()),
               f"tf doctor: instrukcje bez uwag → jedna linia ✓: {res.stdout[-600:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów instructions_lint")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
