#!/usr/bin/env python3
"""Tests: skill_gate --suggest (phrases for metadata.keywords from missed scenarios) and .tf/factory/facts.py
(looking up already-verified facts before new research)."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "facts.py").is_file())


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

    gate = load(ROOT / ".tf" / "factory" / "skill_gate.py", "ctf_gate_suggest")
    hint = load(ROOT / ".claude" / "hooks" / "skill_hint.py", "ctf_hint_suggest")
    hint.REF_SKILLS = 0   # an artificial corpus of 12 skills below — without normalisation to the size of a large installation

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
    check("qa-test-design" not in [it["name"] for _, it in hint.select(prompt, items)], "S-0: the starting case does not hit")
    res = gate.suggest_phrases("qa-test-design", [prompt], ["Jak zaplanować refaktoryzację starego kodu krok po kroku?"],
                               items, hint)
    words = set(re.findall(r"\w+", prompt.lower()))
    check(res["phrases"] and len(res["phrases"]) <= 4 and all(set(re.findall(r"\w+", p)) <= words for p in res["phrases"])
          and res["hits_after"] == 1 and res["hits_before"] == 0 and res["neighbor_ok"] is True,
          f"E-1: phrases from the prompt's words (≤4), after adding them the skill hits, the neighbour's question still is not its own: {res}")
    it_qa = next(i for i in items if i["name"] == "qa-test-design")
    it_qa["body"] = set(hint.stems("strategia testów priorytety ryzyko"))
    p2 = "Agent dopisuje testy do helperów i formaterów. Jaka strategia testów dla projektu?"
    res3 = gate.suggest_phrases("qa-test-design", [p2], [], items, hint)
    check(res3["phrases"] and not any(w in " ".join(res3["phrases"]) for w in ("helper", "format"))
          and set(hint.stems(res3["phrases"][0])) & it_qa["body"],
          f"E-1b: phrases from the skill's topic (SKILL.md content), without incidental words of the question: {res3}")
    it_qa["body"] = set()
    res2 = gate.suggest_phrases("qa-test-design", ["Jak dobrać klasy równoważności i wartości brzegowe dla pola wieku?"], [],
                                items, hint)
    check(res2["phrases"] == [] and res2["hits_before"] == 1, f"E-2: a scenario that hits → nothing to add: {res2}")

    # E-3…E-5 on a real skill from pack-it (qa-test-design); skipped without that overlay
    if (ROOT / ".claude" / "skills" / "qa-test-design").is_dir():
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "f"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "logs", "__pycache__", "*.zip"))
            md = root / ".claude" / "skills" / "qa-test-design" / "SKILL.md"
            s = md.read_text(encoding="utf-8")
            s = re.sub(r'^  keywords: ".*"$', '  keywords: ""', s, flags=re.M)       # without the words the scenario does not hit
            md.write_text(s, encoding="utf-8")
            r = run([root / ".tf" / "factory" / "skill_gate.py", "--hints"], cwd=root)
            check("qa-test-design" in r.stdout, f"E-3: after removing the words the scenario does not hit again: {r.stdout[-300:]}")
            r = run([root / ".tf" / "factory" / "skill_gate.py", "--suggest", "qa-test-design"], cwd=root)
            check(r.returncode == 0 and "keywords" in r.stdout and "--apply" in r.stdout and s == md.read_text(encoding="utf-8"),
                  f"E-4: --suggest without --apply only shows the proposal: {r.stdout[-500:]}{r.stderr[-300:]}")
            r = run([root / ".tf" / "factory" / "skill_gate.py", "--suggest", "qa-test-design", "--apply"], cwd=root)
            r2 = run([root / ".tf" / "factory" / "skill_gate.py", "--hints"], cwd=root)
            check(r.returncode == 0 and md.read_text(encoding="utf-8") != s and "qa-test-design" not in r2.stdout,
                  f"E-5: --apply adds the phrases and the scenario hits again: {r.stdout[-400:]} | {r2.stdout[-300:]}")

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
        (res_dir / "20261018-en.md").write_text("- contradicted (ietf.org): RFC 9999 — ISO 19112 cytowane błędnie.\n",
                                                encoding="utf-8")
        sk = root / ".claude" / "skills" / "sec-x"
        sk.mkdir(parents=True)
        (sk / "SKILL.md").write_text("---\nname: sec-x\n---\n# X\nTreść o ISO 19112 poza źródłami.\n## Sources\n"
                                     "- ISO 19112:2019 (iso.org, accessed 2026-10-10) — schemat gazetteera.\n", encoding="utf-8")
        r = run([ROOT / ".tf" / "factory" / "facts.py", "--root", root, "--today", "2026-10-17", "--json", "ISO", "19112"])
        try:
            hits = json.loads(r.stdout)
        except ValueError:
            hits = []
        by = {(h["file"].split("/")[-1], h["verdict"]) for h in hits}
        check(r.returncode == 0 and ("20261017-archetypy-zrodla.md", "confirmed") in by and ("SKILL.md", "skill-source") in by
              and not any("Treść o ISO" in h["text"] for h in hits),
              f"F-1: verification tables and the skills' “Sources” sections, with a verdict; the skill's content outside the sources skipped: {hits}")
        check(("20261018-en.md", "contradicted") in by, f"F-1b: a verdict as a word (14.x) next to the old letters P/C/N/S: {by}")
        old = [h for h in hits if h["file"].endswith("20250101-stare.md")]
        new = [h for h in hits if h["file"].endswith("20261017-archetypy-zrodla.md")]
        check(old and old[0]["stale"] is True and new and new[0]["stale"] is False and new[0]["date"] == "2026-10-17",
              f"F-2: the finding date and marking of old ones (> 180 days): {old} {new}")
        r = run([ROOT / ".tf" / "factory" / "facts.py", "--root", root, "--today", "2026-10-17", "eidas", "podpis"])
        check(r.returncode == 0 and "eIDAS 910/2014" in r.stdout and "partial" in r.stdout,
              f"F-3: all the terms at once, case-insensitive, with a word stem: {r.stdout}")
        r = run([ROOT / ".tf" / "factory" / "facts.py", "--root", root, "--today", "2026-10-17", "DORA", "terminy"])
        check(r.returncode == 0 and "no verified findings" in r.stdout.lower() and "researcher" in r.stdout,
              f"F-4: no hits → a hint that it must be checked in the sources: {r.stdout}")
        r = run([ROOT / ".tf" / "factory" / "facts.py", "--root", root, "--today", "2026-10-17", "Geographic", "Boundary"])
        check("unconfirmed" in r.stdout and "do not state it as a fact" in r.stdout,
              f"F-5: an unconfirmed finding marked as such: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} suggestion and facts tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
