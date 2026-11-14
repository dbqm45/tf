#!/usr/bin/env python3
"""Testy wagi zadania (`tf task weight`, .tf/factory/task_weight.py): propozycja z treści zgłoszenia i ścieżek planu,
kto może zmienić wagę, skutki wagi w bramkach etapów. python3 .claude/tests/test_task_weight.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
TASK = ROOT / ".tf" / "factory" / "task_state.py"
CHANGES = Path("docs") / "project" / "changes"
SPEC = ("# Specyfikacja\n\n## Kryteria\n\n- AC-1: Zakładając postój 12 godzin, gdy kierowca płaci, wtedy opłata wynosi 45 zł.\n"
        "\n## Bez zmian\n\n- Pierwsze 30 minut jest bezpłatne.\n\n## Poza zakresem\n\n- Abonamenty.\n")
TICKETS = {
    "LOG-1": "# Reset hasła\n\nJako użytkownik chcę zresetować hasło linkiem z maila. AC1: link ważny 30 minut.\n",
    "TYP-1": "# Literówka w README\n\nPopraw literówkę w README: „instlacja” na „instalacja”.\n",
    "REG-1": ("# Limit dobowy 45 zł\n\nJako operator parkingu chcę podnieść limit dobowy opłaty z 40 zł do 45 zł. "
              "AC1: 12 h = 45 zł. AC2: 11 h = 44 zł.\n"),
    "CSV-1": ("# Eksport sesji\n\nJako operator chcę wyeksportować sesje ładowania z wybranego dnia do CSV. "
              "Kryteria akceptacji: plik ma nagłówek i jeden wiersz na sesję.\n"),
    "ENG-1": "# Fix typo in README\n\nFix a typo in the README heading.\n",
    "ENG-2": "# Password reset\n\nAs a user I want to reset my password by email. AC: the link expires after 30 minutes.\n",
}


def tf(project: Path, *args: str):
    return subprocess.run([sys.executable, str(TASK), *args], cwd=project, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def weight(project: Path, key: str, *args: str) -> tuple[int, dict, str]:
    r = tf(project, "weight", key, *args, "--json")
    try:
        return r.returncode, json.loads(r.stdout), r.stdout + r.stderr
    except ValueError:
        return r.returncode, {}, r.stdout + r.stderr


def task(project: Path, key: str) -> dict:
    return json.loads((project / CHANGES / key / "task.json").read_text(encoding="utf-8"))


def main() -> int:
    fails = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        for key, text in TICKETS.items():
            tf(p, "start", key, "--title", text.splitlines()[0].lstrip("# "))
            (p / CHANGES / key / "ticket.md").write_text(text, encoding="utf-8")

        # propozycja z treści zgłoszenia, zawsze z powodem; samo pytanie o wagę niczego nie zapisuje
        before = (p / CHANGES / "LOG-1" / "task.json").read_text(encoding="utf-8")
        code, out, raw = weight(p, "LOG-1")
        check(code == 0 and out.get("proposal") == "pelna" and any("hasł" in r for r in out.get("reasons", []))
              and out.get("weight") == "zwykla" and out.get("assigned") is False,
              f"W-1: zgłoszenie o haśle → propozycja pelna z powodem; waga jeszcze nieprzydzielona: {raw}")
        check((p / CHANGES / "LOG-1" / "task.json").read_text(encoding="utf-8") == before,
              "W-2: tf task weight bez opcji niczego nie zapisuje")
        code, out, raw = weight(p, "TYP-1")
        check(out.get("proposal") == "lekka" and out.get("reasons"), f"W-3: literówka → lekka: {raw}")
        code, out, raw = weight(p, "REG-1")
        check(out.get("proposal") == "zwykla", f"W-4: nowa reguła z kryteriami → zwykla: {raw}")
        code, out, raw = weight(p, "CSV-1")
        check(out.get("proposal") == "zwykla", f"W-5: „sesje ładowania” to nie logowanie — zwykla: {raw}")
        code, out, raw = weight(p, "ENG-1")
        code2, out2, raw2 = weight(p, "ENG-2")
        check(out.get("proposal") == "lekka" and out2.get("proposal") == "pelna",
              f"W-6: zgłoszenia po angielsku (typo → lekka, password → pelna): {raw} {raw2}")

        # pierwszy przydział robi fabryka; potem --apply tylko podnosi
        code, out, raw = weight(p, "TYP-1", "--apply")
        data = task(p, "TYP-1")
        check(code == 0 and data.get("weight") == "lekka" and data.get("weight_log")
              and data["weight_log"][-1].get("by") == "process:tf" and data["weight_log"][-1].get("reasons"),
              f"W-7: --apply przydziela propozycję (także niższą niż domyślna) i zapisuje powód: {raw} {data.get('weight_log')}")
        (p / CHANGES / "TYP-1" / "plan.md").write_text(
            "# Plan\n- [ ] K1 — poprawka · pliki: README.md, db/migrations/0007_add_index.sql · weryfikacja: `make test`\n",
            encoding="utf-8")
        code, out, raw = weight(p, "TYP-1", "--apply")
        data = task(p, "TYP-1")
        check(data.get("weight") == "pelna" and any("db/migrations/0007_add_index.sql" in r for r in out.get("reasons", [])),
              f"W-8: plan dotyka migracji → --apply podnosi wagę do pelna, powód wskazuje ścieżkę: {raw}")
        (p / CHANGES / "TYP-1" / "plan.md").write_text("# Plan\n- [ ] K1 — poprawka · pliki: README.md\n", encoding="utf-8")
        code, out, raw = weight(p, "TYP-1", "--apply")
        check(code == 0 and task(p, "TYP-1").get("weight") == "pelna" and out.get("proposal") == "lekka"
              and "human:" in raw,
              f"W-9: propozycja niższa niż przydzielona waga niczego nie zmienia; komunikat mówi, kto może obniżyć: {raw}")
        (p / CHANGES / "ENG-1" / "plan.md").write_text(
            "# Plan\n- [ ] K1 — poprawka · pliki: README.md, docs/a.md, docs/b.md\n", encoding="utf-8")
        code, out, raw = weight(p, "ENG-1")
        check(out.get("proposal") == "zwykla", f"W-10: literówka, ale plan na 3 pliki → zwykla: {raw}")

        # ręczna zmiana: podnieść może każdy, obniżyć tylko człowiek z powodem
        r = tf(p, "weight", "REG-1", "--set", "pelna")
        check(r.returncode == 0 and task(p, "REG-1").get("weight") == "pelna", f"W-11: podniesienie bez człowieka: {r.stdout}")
        r = tf(p, "weight", "REG-1", "--set", "zwykla")
        check(r.returncode == 1 and task(p, "REG-1").get("weight") == "pelna" and "human:" in r.stdout,
              f"W-12: obniżenie bez człowieka → odmowa: {r.returncode} {r.stdout}")
        r = tf(p, "weight", "REG-1", "--set", "zwykla", "--by", "human:anna")
        check(r.returncode == 2 and "--reason" in r.stdout, f"W-13: obniżenie wymaga powodu: {r.returncode} {r.stdout}")
        r = tf(p, "weight", "REG-1", "--set", "zwykla", "--by", "human:anna", "--reason", "zmiana tylko w kalkulatorze")
        log = task(p, "REG-1").get("weight_log") or []
        check(r.returncode == 0 and task(p, "REG-1").get("weight") == "zwykla" and log and log[-1].get("by") == "human:anna"
              and "kalkulatorze" in log[-1].get("reason", "") and log[-1].get("from") == "pelna",
              f"W-14: człowiek obniża z powodem, zapis w historii: {r.stdout} {log[-1:]}")
        (p / CHANGES / "REG-1" / "plan.md").write_text(
            "# Plan\n- [ ] K1 — limit · pliki: parking/fees.py, db/migrations/0008_limit.sql\n", encoding="utf-8")
        code, out, raw = weight(p, "REG-1", "--apply")
        check(task(p, "REG-1").get("weight") == "zwykla" and out.get("proposal") == "pelna" and "człowiek" in out.get("note", ""),
              f"W-14a: po decyzji człowieka --apply nie zmienia wagi, tylko mówi o propozycji: {raw}")
        tf(p, "start", "TYP-9", "--title", "Literówka w stopce", "--weight", "pelna")
        (p / CHANGES / "TYP-9" / "ticket.md").write_text("# Literówka w stopce\n\nPopraw literówkę w stopce.\n", encoding="utf-8")
        code, out, raw = weight(p, "TYP-9", "--apply")
        check(task(p, "TYP-9").get("weight") == "pelna" and out.get("proposal") == "lekka",
              f"W-14b: waga podana przy zakładaniu zadania nie jest obniżana przez --apply: {raw}")
        r = tf(p, "weight", "REG-1", "--set", "ogromna")
        check(r.returncode == 2, f"W-15: nieznana waga → kod 2: {r.returncode} {r.stdout}")
        r = tf(p, "weight", "NIE-1")
        check(r.returncode != 0 and "Traceback" not in r.stderr, f"W-16: brak zadania → błąd bez wyjątku: {r.returncode}")
        r = tf(p, "weight", "LOG-1")
        check(r.returncode == 0 and "pełna" in r.stdout and "hasł" in r.stdout,
              f"W-17: wyjście tekstowe nazywa propozycję i powód: {r.stdout}")

        # skutek wagi pelna: realizacja dopiero po zatwierdzeniu planu przez człowieka (tryb bez nadzoru tego nie obejdzie)
        folder = p / CHANGES / "LOG-1"
        (folder / "spec.md").write_text(SPEC, encoding="utf-8")
        (folder / "plan.md").write_text("# Plan\n- [ ] K1 — reset · pliki: src/reset.py\n", encoding="utf-8")
        tf(p, "weight", "LOG-1", "--apply")
        tf(p, "stage", "LOG-1", "plan")
        tf(p, "artifact", "LOG-1", "plan.md", "--stage", "plan", "--by", "process:tf", "--inputs", "spec.md")
        r = tf(p, "stage", "LOG-1", "realizacja")
        check(r.returncode == 1 and "approve LOG-1 plan.md" in r.stdout and "człowiek" in r.stdout,
              f"W-18: waga pelna — realizacja odrzucona bez planu zatwierdzonego przez człowieka: {r.returncode} {r.stdout}")
        tf(p, "approve", "LOG-1", "plan.md", "--by", "human:anna")
        r = tf(p, "stage", "LOG-1", "realizacja")
        check(r.returncode == 0, f"W-19: po zatwierdzeniu planu realizacja przechodzi: {r.stdout}")
        # odhaczenie kawałka w zatwierdzonym planie nie unieważnia zgody człowieka; zmiana treści planu — tak
        (folder / "plan.md").write_text("# Plan\n- [x] K1 — reset · pliki: src/reset.py\n", encoding="utf-8")
        state = json.loads(tf(p, "status", "LOG-1", "--json").stdout).get("artifact_states", {}).get("plan.md")
        r = tf(p, "stage", "LOG-1", "realizacja", "--force")
        check(state == "zatwierdzony", f"W-19a: odhaczony kawałek — plan nadal zatwierdzony: {state}")
        (folder / "plan.md").write_text("# Plan\n- [x] K1 — reset · pliki: src/reset.py\n- [ ] K2 — mail · pliki: src/mail.py\n",
                                        encoding="utf-8")
        state = json.loads(tf(p, "status", "LOG-1", "--json").stdout).get("artifact_states", {}).get("plan.md")
        check(state == "zmieniony po zatwierdzeniu", f"W-19b: nowy kawałek w planie wymaga ponownej zgody: {state}")
        tf(p, "artifact", "REG-1", "plan.md", "--stage", "plan", "--by", "process:tf")
        r = tf(p, "stage", "REG-1", "realizacja")
        check(r.returncode == 0, f"W-20: waga zwykla nie wymaga zatwierdzenia planu: {r.stdout}")

        # skutek wagi lekka: jeden kawałek, specyfikacja nie jest potrzebna
        tf(p, "start", "TYP-2", "--title", "Literówka w stopce")
        (p / CHANGES / "TYP-2" / "ticket.md").write_text("# Literówka w stopce\n\nPopraw literówkę w stopce strony.\n",
                                                         encoding="utf-8")
        tf(p, "weight", "TYP-2", "--apply")
        (p / CHANGES / "TYP-2" / "plan.md").write_text(
            "# Plan\n- [ ] K1 — stopka · pliki: web/footer.html\n- [ ] K2 — test · pliki: web/footer.test.js\n", encoding="utf-8")
        r = tf(p, "stage", "TYP-2", "plan")
        check(task(p, "TYP-2").get("weight") == "lekka" and r.returncode == 1 and "jeden kawałek" in r.stdout
              and "weight TYP-2 --set zwykla" in r.stdout,
              f"W-21: waga lekka z planem na dwa kawałki → odmowa z podpowiedzią: {r.returncode} {r.stdout}")
        (p / CHANGES / "TYP-2" / "plan.md").write_text("# Plan\n- [ ] K1 — stopka · pliki: web/footer.html\n", encoding="utf-8")
        r = tf(p, "stage", "TYP-2", "plan")
        check(r.returncode == 0 and not (p / CHANGES / "TYP-2" / "spec.md").exists(),
              f"W-22: waga lekka z jednym kawałkiem przechodzi do planu bez spec.md: {r.stdout}")
        r = tf(p, "status", "TYP-2")
        check("waga: lekka" in r.stdout, f"W-23: status pokazuje wagę: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów wagi zadania")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
