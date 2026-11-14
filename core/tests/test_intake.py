#!/usr/bin/env python3
"""Testy rozpoznania wejścia polecenia /tf (skill tf, scripts/intake.py): rodzaj wejścia, klucz, tracker
z adresu albo z karty operacyjnej, cięcie z planu zmiany, wznowienie, opcje.
python3 .claude/tests/test_intake.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REL = Path(".claude") / "skills" / "tf" / "scripts" / "intake.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills" / "tf").is_dir()), None)
SCRIPT = (ROOT / REL) if ROOT else REL
CHANGES = Path("docs") / "project" / "changes"
CARD = Path(".tf") / "config" / "operations.json"

PLAN = """---
artifact: plan
change: {change}
tasks: [{tasks}]
---
# Plan zmiany {change}

| Cięcie | Wydanie | Flaga | Wartość | Pliki | Weryfikacja |
|---|---|---|---|---|---|
{rows}
"""


def run(project: Path, *args: str):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=project, capture_output=True, text=True,
                          timeout=60, env=env)


def resolve(project: Path, *words: str) -> tuple[int, dict, str]:
    r = run(project, "resolve", "--json", *words)
    try:
        return r.returncode, json.loads(r.stdout), r.stdout + r.stderr
    except ValueError:
        return r.returncode, {}, r.stdout + r.stderr


def snapshot(project: Path) -> dict:
    return {p.relative_to(project).as_posix(): p.read_bytes() for p in sorted(project.rglob("*")) if p.is_file()}


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if not SCRIPT.is_file():
        print(f"✗ brak skryptu {REL}")
        return 1

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        for change, tasks in (("CHG-12", ("TSK-57", "TSK-58")), ("CHG-13", ("TSK-58",))):
            d = p / CHANGES / change
            d.mkdir(parents=True)
            rows = "\n".join(f"| {k} | R1 | — | wartość {k} | src/a.ts | `npm test` |" for k in tasks)
            (d / "plan.md").write_text(PLAN.format(change=change, tasks=", ".join(tasks), rows=rows), encoding="utf-8")
        for key, stage in (("PROJ-7", "realizacja"), ("PROJ-8", "zamkniecie")):
            d = p / CHANGES / key
            d.mkdir(parents=True)
            (d / "task.json").write_text(json.dumps({"key": key, "title": f"Zadanie {key}", "stage": stage}),
                                         encoding="utf-8")
        (p / "docs" / "story.md").write_text("# Eksport\n\nJako operator chcę eksport.\n", encoding="utf-8")
        (p / CARD).parent.mkdir(parents=True)
        (p / CARD).write_text(json.dumps({"flags": {"file": "config/flags.json", "envs": ["test", "prod"],
                                                    "test_env": "test"}}), encoding="utf-8")

        # zgłoszenie po kluczu: tracker nieznany → pytanie, a droga przez wklejenie zawsze jest podana
        before = snapshot(p)
        code, out, raw = resolve(p, "EBO-1236")
        check(code == 0 and out.get("kind") == "zgloszenie" and out.get("key") == "EBO-1236"
              and out.get("tracker") is None and out.get("ask") == "tracker" and "wklej" in out.get("next", "").lower(),
              f"I-1: klucz bez trackera w karcie → zgłoszenie, pytanie o tracker, droga przez wklejenie: {raw}")
        check(snapshot(p) == before, "I-2: resolve niczego nie zapisuje (karta i pliki projektu bez zmian)")
        code, out, raw = resolve(p, "ebo-1236")
        check(out.get("kind") == "zgloszenie" and out.get("key") == "EBO-1236", f"I-3: klucz małymi literami: {raw}")

        # tracker zapamiętany w karcie nie jest pytany ponownie; karta zachowuje sekcję flag
        r = run(p, "tracker", "jira", "--prefix", "EBO")
        card = json.loads((p / CARD).read_text(encoding="utf-8"))
        check(r.returncode == 0 and card.get("tracker", {}).get("prefixes") == {"EBO": "jira"}
              and card.get("flags", {}).get("test_env") == "test",
              f"I-4: tracker <typ> --prefix zapisuje kartę i nie rusza flag: {r.stdout}{r.stderr} {card}")
        code, out, raw = resolve(p, "EBO-1236")
        check(out.get("tracker") == "jira" and out.get("tracker_from") == "karta" and out.get("ask") is None
              and "EBO-1236" in out.get("next", "") and "--key EBO-1236" in out.get("next", ""),
              f"I-5: tracker z karty → bez pytania, następny krok z kluczem: {raw}")
        code, out, raw = resolve(p, "ENG-5")
        check(out.get("tracker") is None and out.get("ask") == "tracker", f"I-6: inny prefiks nadal nieznany: {raw}")
        r = run(p, "tracker", "linear")
        code, out, raw = resolve(p, "ENG-5")
        code2, out2, _ = resolve(p, "EBO-1")
        check(r.returncode == 0 and out.get("tracker") == "linear" and out2.get("tracker") == "jira",
              f"I-7: tracker domyślny dla pozostałych prefiksów, prefiks wygrywa: {raw}")
        r = run(p, "tracker")
        check(r.returncode == 0 and "linear" in r.stdout and "EBO" in r.stdout and "jira" in r.stdout,
              f"I-8: tracker bez argumentów pokazuje zapis: {r.stdout}")
        r = run(p, "tracker", "Jira Cloud!")
        check(r.returncode == 2, f"I-9: nazwa trackera spoza wzorca → kod 2: {r.returncode} {r.stdout}")

        # adres zgłoszenia: tracker i klucz z adresu, adres jako źródło
        for url, tracker, key in (
                ("https://acme.atlassian.net/browse/EBO-1236", "jira", "EBO-1236"),
                ("https://jira.acme.example/browse/OPS-9?focusedId=1", "jira", "OPS-9"),
                ("https://linear.app/acme/issue/ENG-42/add-csv-export", "linear", "ENG-42"),
                ("https://github.com/acme/app/issues/17", "github", "GH-17"),
                ("https://gitlab.com/acme/app/-/issues/9", "gitlab", "GL-9")):
            code, out, raw = resolve(p, url)
            check(out.get("kind") == "zgloszenie" and out.get("tracker") == tracker and out.get("key") == key
                  and out.get("source") == url and out.get("tracker_from") == "adres" and out.get("ask") is None,
                  f"I-10: adres {url} → {tracker} {key}: {raw}")
        code, out, raw = resolve(p, "https://tracker.example.com/t/ABC-5")
        check(out.get("kind") == "zgloszenie" and out.get("key") == "ABC-5" and out.get("tracker") == "linear"
              and out.get("tracker_from") == "karta",
              f"I-11: nieznany host z kluczem w adresie → klucz, tracker z karty: {raw}")
        code, out, raw = resolve(p, "https://tracker.example.com/tickets/5512")
        check(out.get("kind") == "zgloszenie" and out.get("key") is None and out.get("ask") == "content"
              and "wklej" in out.get("next", "").lower(),
              f"I-12: adres bez rozpoznanego klucza → prośba o wklejenie treści: {raw}")

        # cięcie z planu zmiany
        code, out, raw = resolve(p, "TSK-57")
        check(out.get("kind") == "ciecie" and out.get("key") == "TSK-57" and out.get("changes") == ["CHG-12"]
              and out.get("ask") is None and "start --task TSK-57 --change CHG-12" in out.get("next", ""),
              f"I-13: klucz z nagłówka tasks → cięcie z gotowym poleceniem: {raw}")
        code, out, raw = resolve(p, "TSK-58")
        check(out.get("kind") == "ciecie" and out.get("changes") == ["CHG-12", "CHG-13"] and out.get("ask") == "change",
              f"I-14: klucz w dwóch planach → pytanie o zmianę: {raw}")
        code, out, raw = resolve(p, "TSK-58", "--change", "CHG-13", "--auto", "--budget", "3")
        check(out.get("changes") == ["CHG-13"] and out.get("ask") is None
              and out.get("options") == {"auto": True, "plan": False, "budget": 3.0, "change": "CHG-13"},
              f"I-15: --change wybiera zmianę; opcje odcięte i zwrócone: {raw}")
        r = run(p, "resolve", "TSK-99", "--change", "CHG-12")
        check(r.returncode == 2 and "TSK-99" in r.stdout and "CHG-12" in r.stdout,
              f"I-16: klucz spoza planu wskazanej zmiany → kod 2: {r.returncode} {r.stdout}")

        # wznowienie, plik, treść
        code, out, raw = resolve(p, "PROJ-7")
        check(out.get("kind") == "wznowienie" and out.get("stage") == "realizacja" and "PROJ-7" in out.get("next", ""),
              f"I-17: klucz istniejącego zadania → wznowienie z etapem: {raw}")
        code, out, raw = resolve(p, "docs/story.md")
        check(out.get("kind") == "plik" and out.get("file") == "docs/story.md"
              and "--story-file docs/story.md" in out.get("next", ""), f"I-18: ścieżka istniejącego pliku: {raw}")
        code, out, raw = resolve(p, "PROJ-12: Eksport sesji do CSV\nJako operator chcę pobrać sesje.")
        check(out.get("kind") == "tresc" and out.get("key") == "PROJ-12" and out.get("title") == "Eksport sesji do CSV"
              and "--key PROJ-12" in out.get("next", ""), f"I-19: klucz i treść → treść z kluczem i tytułem: {raw}")
        code, out, raw = resolve(p, "dodaj", "eksport", "sesji", "do", "CSV")
        check(out.get("kind") == "tresc" and out.get("key") is None and out.get("title") == "dodaj eksport sesji do CSV"
              and out.get("intent") is None, f"I-20: zwykłe zdanie → treść bez klucza: {raw}")

        code, out, raw = resolve(p, "X-ray")
        check(out.get("kind") == "tresc" and out.get("key") is None and out.get("title") == "X-ray",
              f"I-20a: jedno słowo z łącznikiem, które nie jest zadaniem ani numerem zgłoszenia → treść bez klucza: {raw}")
        code, out, raw = resolve(p, "PROJ-7", "dokończ", "eksport")
        check(out.get("kind") == "wznowienie" and out.get("text") == "dokończ eksport",
              f"I-20b: klucz istniejącego zadania z dopiskiem → wznowienie, dopisek zachowany: {raw}")

        # brak wejścia: zadania w toku do wznowienia (zamknięte pominięte)
        code, out, raw = resolve(p)
        keys = [x.get("key") for x in out.get("tasks", [])]
        check(out.get("kind") == "brak" and keys == ["PROJ-7"], f"I-21: bez wejścia → lista zadań w toku: {raw}")

        # słowo wymuszające sposób pracy
        code, out, raw = resolve(p, "pytanie", "jak", "działa", "logowanie?")
        check(out.get("intent") == "pytanie" and out.get("kind") == "tresc" and out.get("title") == "jak działa logowanie?",
              f"I-22: „pytanie …” → wymuszona odpowiedź bez pętli: {raw}")
        code, out, raw = resolve(p, "szybko", "popraw", "literówkę", "w", "README")
        check(out.get("intent") == "szybko" and "bez" in out.get("next", "").lower(), f"I-23: „szybko …”: {raw}")
        code, out, raw = resolve(p, "zadanie", "EBO-1236")
        check(out.get("intent") == "zadanie" and out.get("kind") == "zgloszenie" and out.get("key") == "EBO-1236",
              f"I-24: „zadanie <klucz>”: {raw}")

        # wyjście dla człowieka i błędy wywołania
        r = run(p, "resolve", "EBO-1236")
        check(r.returncode == 0 and all(s in r.stdout for s in ("Wejście: zgłoszenie", "Klucz: EBO-1236",
                                                                "Tracker: jira", "Dalej: ")),
              f"I-25: wyjście tekstowe ze stałymi polami: {r.stdout}")
        r = run(p, "nieznane")
        check(r.returncode == 2 and "Traceback" not in r.stderr, f"I-26: nieznane polecenie → kod 2: {r.returncode} {r.stderr[-200:]}")
        (p / CARD).write_text("{nie json", encoding="utf-8")
        code, out, raw = resolve(p, "EBO-1236")
        check(code == 0 and out.get("tracker") is None and "Traceback" not in raw,
              f"I-27: uszkodzona karta nie wywraca skryptu: {raw}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów rozpoznania wejścia /tf")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
