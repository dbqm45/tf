#!/usr/bin/env python3
"""Testy: skill_gate --suggest (frazy do metadata.slowa z nietrafionych scenariuszy) i factory/facts.py
(szukanie już zweryfikowanych faktów przed nowym researchem)."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "factory" / "facts.py").is_file())


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(args, cwd=None):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=cwd, timeout=600)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    gate = load(ROOT / "factory" / "skill_gate.py", "ctf_gate_suggest")
    hint = load(ROOT / ".claude" / "hooks" / "skill_hint.py", "ctf_hint_suggest")

    def item(name, text):
        return {"name": name, "desc": text, "kat": "", "excerpt": "", "head": set(hint.stems(text)), "body": set()}
    filler = ["kubernetes klaster sondy repliki", "faktury księgowanie salda konta", "kolory kontrast typografia siatka",
              "kryptografia klucze certyfikaty tls", "kolejka wiadomości outbox idempotencja", "migracje bazy indeksy zapytania",
              "persony wywiady badania użytkowników", "docker obrazy warstwy rozmiar", "monitoring alerty dashboardy logi",
              "umowy aneksy warunki zamówienia"]
    items = [item(f"x-f{i}", t) for i, t in enumerate(filler)]
    items += [item("qa-test-design", "projekt przypadków testowych klasy równoważności wartości brzegowe tablice decyzyjne"),
              item("eng-refactor-planning", "plan refaktoryzacji projektu od czego zacząć strategia całego kodu dług")]
    prompt = "Chcę strategię testów dla całego projektu prawie bez testów. Od czego zacząć i co ma się znaleźć w strategii testów?"
    check("qa-test-design" not in [it["name"] for _, it in hint.select(prompt, items)], "S-0: przypadek startowy nie trafia")
    res = gate.suggest_phrases("qa-test-design", [prompt], ["Jak zaplanować refaktoryzację starego kodu krok po kroku?"],
                               items, hint)
    words = set(re.findall(r"\w+", prompt.lower()))
    check(res["phrases"] and len(res["phrases"]) <= 4 and all(set(re.findall(r"\w+", p)) <= words for p in res["phrases"])
          and res["hits_after"] == 1 and res["hits_before"] == 0 and res["neighbor_ok"] is True,
          f"E-1: frazy ze słów promptu (≤4), po dopisaniu skill trafia, pytanie sąsiada nadal nie jego: {res}")
    it_qa = next(i for i in items if i["name"] == "qa-test-design")
    it_qa["body"] = set(hint.stems("strategia testów priorytety ryzyko"))
    p2 = "Agent dopisuje testy do helperów i formaterów. Jaka strategia testów dla projektu?"
    res3 = gate.suggest_phrases("qa-test-design", [p2], [], items, hint)
    check(res3["phrases"] and not any(w in " ".join(res3["phrases"]) for w in ("helper", "format"))
          and set(hint.stems(res3["phrases"][0])) & it_qa["body"],
          f"E-1b: frazy z tematu skilla (treść SKILL.md), bez przypadkowych słów pytania: {res3}")
    it_qa["body"] = set()
    res2 = gate.suggest_phrases("qa-test-design", ["Jak dobrać klasy równoważności i wartości brzegowe dla pola wieku?"], [],
                                items, hint)
    check(res2["phrases"] == [] and res2["hits_before"] == 1, f"E-2: trafiony scenariusz → nic do dopisania: {res2}")

    if importlib.util.find_spec("yaml"):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "f"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "logs", "__pycache__", "*.zip"))
            md = root / ".claude" / "skills" / "qa-test-design" / "SKILL.md"
            s = md.read_text(encoding="utf-8")
            s = re.sub(r'^  slowa: ".*"$', '  slowa: ""', s, flags=re.M)       # bez słów scenariusz nie trafia
            md.write_text(s, encoding="utf-8")
            r = run([root / "factory" / "skill_gate.py", "--hints"], cwd=root)
            check("qa-test-design" in r.stdout, f"E-3: po usunięciu słów scenariusz znów nie trafia: {r.stdout[-300:]}")
            r = run([root / "factory" / "skill_gate.py", "--suggest", "qa-test-design"], cwd=root)
            check(r.returncode == 0 and "slowa" in r.stdout and "--apply" in r.stdout and s == md.read_text(encoding="utf-8"),
                  f"E-4: --suggest bez --apply tylko pokazuje propozycję: {r.stdout[-500:]}{r.stderr[-300:]}")
            r = run([root / "factory" / "skill_gate.py", "--suggest", "qa-test-design", "--apply"], cwd=root)
            r2 = run([root / "factory" / "skill_gate.py", "--hints"], cwd=root)
            check(r.returncode == 0 and md.read_text(encoding="utf-8") != s and "qa-test-design" not in r2.stdout,
                  f"E-5: --apply dopisuje frazy i scenariusz znów trafia: {r.stdout[-400:]} | {r2.stdout[-300:]}")

    # ── F: facts.py ──
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        res_dir = root / "docs" / "project" / "archive" / "research"
        res_dir.mkdir(parents=True)
        (res_dir / "20261017-archetypy-zrodla.md").write_text(
            "# Weryfikacja\n## Geografia\n- P (iso.org): ISO 19112:2019 (wyd. 2, zastąpiło 2003) — gazetteer.\n"
            "- N: przynależność Geographic Boundary do Vol. 1.\n- C: eIDAS 910/2014 — pieczęć elektroniczna i podpis.\n",
            encoding="utf-8")
        (res_dir / "20250101-stare.md").write_text("- P: ISO 19112:2003 — stare wydanie.\n", encoding="utf-8")
        sk = root / ".claude" / "skills" / "sec-x"
        sk.mkdir(parents=True)
        (sk / "SKILL.md").write_text("---\nname: sec-x\n---\n# X\nTreść o ISO 19112 poza źródłami.\n## Źródła\n"
                                     "- ISO 19112:2019 (iso.org, odczyt 2026-10-10) — schemat gazetteera.\n", encoding="utf-8")
        r = run([ROOT / "factory" / "facts.py", "--root", root, "--today", "2026-10-17", "--json", "ISO", "19112"])
        try:
            hits = json.loads(r.stdout)
        except ValueError:
            hits = []
        by = {(h["file"].split("/")[-1], h["verdict"]) for h in hits}
        check(r.returncode == 0 and ("20261017-archetypy-zrodla.md", "potwierdzone") in by and ("SKILL.md", "źródło skilla") in by
              and not any("Treść o ISO" in h["text"] for h in hits),
              f"F-1: tabele weryfikacji i sekcje „Źródła” skilli, z werdyktem; treść skilla poza źródłami pominięta: {hits}")
        old = [h for h in hits if h["file"].endswith("20250101-stare.md")]
        new = [h for h in hits if h["file"].endswith("20261017-archetypy-zrodla.md")]
        check(old and old[0]["stale"] is True and new and new[0]["stale"] is False and new[0]["date"] == "2026-10-17",
              f"F-2: data ustalenia i oznaczenie starych (> 180 dni): {old} {new}")
        r = run([ROOT / "factory" / "facts.py", "--root", root, "--today", "2026-10-17", "eidas", "podpis"])
        check(r.returncode == 0 and "eIDAS 910/2014" in r.stdout and "częściowo" in r.stdout,
              f"F-3: wszystkie hasła naraz, bez wielkości liter, z rdzeniem słowa: {r.stdout}")
        r = run([ROOT / "factory" / "facts.py", "--root", root, "--today", "2026-10-17", "DORA", "terminy"])
        check(r.returncode == 0 and "brak" in r.stdout.lower() and "researcher" in r.stdout,
              f"F-4: brak trafień → wskazówka, że trzeba sprawdzić w źródłach: {r.stdout}")
        r = run([ROOT / "factory" / "facts.py", "--root", root, "--today", "2026-10-17", "Geographic", "Boundary"])
        check("niepotwierdzone" in r.stdout and "nie podawaj jako faktu" in r.stdout,
              f"F-5: ustalenie niepotwierdzone oznaczone jako takie: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów sugestii i faktów")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
