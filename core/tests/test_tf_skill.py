#!/usr/bin/env python3
"""Testy pętli „zadanie → PR” w rdzeniu: agent sesji głównej `tf`, skill `tf`, skrypty przebiegu, uprawnienia
i przewodnik. python3 .claude/tests/test_tf_skill.py"""
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "skills" / "tf").is_dir())


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    agents = ROOT / ".claude" / "agents" / "_generated"
    agent = next(iter(agents.rglob("tf.md")), None)
    text = agent.read_text(encoding="utf-8") if agent else ""
    fm = text.split("---")[1] if text.count("---") >= 2 else ""
    check("Agent(scout, researcher, quick-fixer, scope-reviewer, architect, security-reviewer)" in fm
          and "skills:" not in fm and "maxTurns" not in fm,
          f"T-1: agent tf — sesja główna z listą agentów, bez preładowania skilli i limitu tur: {fm[:300]}")
    skill = ROOT / ".claude" / "skills" / "tf"
    check(".claude/skills/tf/SKILL.md" in text and "talos" not in text.lower() and (skill / "SKILL.md").is_file(),
          "T-2: agent czyta skill procesowy z pliku, który jest zainstalowany; w rdzeniu nie ma starej nazwy")
    script = ".claude/skills/tf/scripts/run_report.py"
    check((ROOT / script).is_file() and script in (skill / "SKILL.md").read_text(encoding="utf-8"),
          "T-3: skrypt przebiegu przy skillu i ścieżka w skillu")
    allow = []
    for name in ("settings.json", "settings.local.json"):
        f = ROOT / ".claude" / name
        if f.is_file():
            allow += json.loads(f.read_text(encoding="utf-8")).get("permissions", {}).get("allow", [])
    check(any(script in a for a in allow), f"T-4: uprawnienie dla skryptu przebiegu: {[a for a in allow if 'run' in a]}")
    guide = ROOT / ".tf" / "factory" / "PRZEWODNIK.md"
    guide_text = guide.read_text(encoding="utf-8") if guide.is_file() else ""
    check("/tf" in guide_text and "claude --agent tf" in guide_text, "T-5: przewodnik rdzenia opisuje /tf i agenta tf")
    personas = [p for p in agents.rglob("*.md") if p.parent.name not in ("shared", "consult") and p.stem == p.parent.name]
    check(personas == [] or all("`tf`" not in p.read_text(encoding="utf-8") for p in personas),
          "T-6: persony nie delegują do agenta tf (to sesja główna, nie wykonawca)")
    body = (skill / "SKILL.md").read_text(encoding="utf-8") if (skill / "SKILL.md").is_file() else ""

    def ref(name: str) -> str:
        """Plik szczegółów skilla (references/); liczy się tylko wtedy, gdy SKILL.md go wymienia."""
        f = skill / "references" / name
        return f.read_text(encoding="utf-8") if f.is_file() and f"references/{name}" in body else ""

    cuts = ref("ciecia-pdi.md")
    intake = body.split("## 1.", 1)[-1].split("## 2.", 1)[0]
    check("requirements_lint.py --story" in intake and "STORY-001" in intake and "--auto" in intake
          and "STOP" in intake and "podzia" in intake and "(pack-it)" in intake,
          "T-7: przyjęcie historyjki — lint kształtu (pack-it, warunkowo); z --auto STORY-001 → STOP z propozycją podziału")
    loop = body.split("## 3.", 1)[-1].split("## 4.", 1)[0]
    check("`Flag: " in cuts and "release.yaml" in cuts and "za flagą" in cuts and "references/ciecia-pdi.md" in loop,
          "T-8: kawałek cięcia z flagą — kod za flagą i dopisek `Flag: <klucz>` w commicie (plan wydania release.yaml); "
          "pętla kawałka odsyła do references/ciecia-pdi.md")
    check("--task" in body and "--task" in cuts and "Change: TSK" in cuts and "changes/" in cuts and "/runs/" in cuts
          and "story/tsk-" in cuts and "pdi/CHG-n-delivery" in cuts,
          "T-9: wejście TSK z planu zmiany (`run_report.py start --task`), gałąź z kluczem od gałęzi fazy, `Change:` "
          "w commitach, raport w changes/CHG-n/runs/ — w references/ciecia-pdi.md")
    fixes = cuts.split("## Poprawki z pętli PR", 1)[-1] if "## Poprawki z pętli PR" in cuts else ""
    check("Rework-Cause:" in fixes and all(v in fixes for v in ("luka-specyfikacji", "blad-agenta", "zmiana-wymagan",
                                                                 "nieznana")),
          "T-11: commit poprawki z pętli PR ma trailer `Rework-Cause:` z jedną z 4 przyczyn (tf metrics, B3)")
    finish = body.split("## 4.", 1)[-1].split("## Kto co robi", 1)[0]
    check("risk_triage.py --md" in finish and "opis" in finish,
          "T-12: przy otwarciu PR pętla dołącza do opisu sekcję triażu ryzyka zmian (risk_triage.py --md, B1b)")
    scan = ".claude/skills/tf/scripts/security_scan.py"
    check((ROOT / scan).is_file() and any(scan in a for a in allow)
          and (skill / "templates" / "verify.sh").is_file()
          and "security_scan.py scan" in loop and "feedback.md" in loop and "STOP" in loop
          and "security_scan.py cooldown" in body,
          "T-10: skan bezpieczeństwa w pętli kawałka (skrypt, uprawnienie, FAIL → feedback.md, STOP), karencja "
          "wersji na starcie, szablon verify.sh")

    state = ".claude/skills/tf/scripts/run_state.py"
    check((ROOT / state).is_file() and (skill / "templates" / "dashboard.html").is_file()
          and any(state in a for a in allow) and "run_state.py stage" in body and "run_state.py step" in body
          and "dashboard.html" in guide_text,
          "T-11: stan przebiegu dla podglądu (skrypt, szablon dashboardu, uprawnienie, polecenia w skillu, opis w przewodniku)")
    body_names = [w for w in ("Talos", "talos-story-run", "mode-talos") if w in body]
    check(body_names == [], f"T-13: skill tf nie używa starych nazw: {body_names}")
    check((ROOT / ".claude" / "skills" / "core-delivery-lifecycle" / "scripts" / "pr_budget.py").is_file()
          and any("pr_budget.py" in a for a in allow) and any(a.startswith("Bash(./verify.sh") for a in allow),
          "T-14: uprawnienia pętli (pr_budget.py, ./verify.sh) są w ustawieniach rdzenia")

    # krok E1: /tf wywołuje także model (zlecenie zwykłym zdaniem), a wejście i źródło rozpoznaje skrypt
    front = body.split("---")[1] if body.count("---") >= 2 else ""
    desc = next((ln for ln in front.splitlines() if ln.startswith("description:")), "")
    check("disable-model-invocation" not in front and desc.startswith("description: Użyj, gdy") and "slowa:" in front,
          f"T-15: skill tf może wywołać model — bez disable-model-invocation, opis jako reguła wyboru, słowa: {desc}")
    entry = body.split("## Wejście", 1)[-1].split("## 0.", 1)[0] if "## Wejście" in body else ""
    check(body.find("## Wejście") != -1 and body.find("## Wejście") < body.find("## 0.")
          and all(w in entry for w in ("pytanie", "szybko", "zadanie", "AskUserQuestion", "jednym zdaniem")),
          "T-16: sekcja „Wejście” przed startem — zadanie / pytanie / drobna zmiana / wątpliwość → jedno pytanie")
    intake_script = ".claude/skills/tf/scripts/intake.py"
    check((ROOT / intake_script).is_file() and "intake.py resolve" in entry and "intake.py tracker" in entry
          and any(intake_script in a for a in allow),
          f"T-17: rozpoznanie wejścia skryptem (resolve, tracker) z uprawnieniem: {[a for a in allow if 'intake' in a]}")
    check(all(w in entry for w in ("tylko odczyt", "wklej", "nie instalujesz", "dane, nie polecenia", "--source"))
          and "/tf jira" not in body and "/tf linear" not in body,
          "T-18: tracker — odczyt przez podłączone narzędzie albo wklejenie treści; fabryka niczego nie instaluje; "
          "treść zgłoszenia to dane; źródło trafia do ticket.md; polecenie bez nazwy narzędzia")
    check("--auto" in entry and "STOP" in entry, "T-19: bez człowieka (--auto) pytanie o źródło zamienia się w STOP")

    # SKILL.md mieści się w limicie przywracanym po kompaktowaniu; szczegóły są w references/, wymienione w SKILL.md
    limit = 15000
    refs = sorted(f.name for f in (skill / "references").glob("*.md")) if (skill / "references").is_dir() else []
    check(len(body) <= limit, f"T-20: SKILL.md ma {len(body)} znaków (limit {limit}) — szczegóły przenieś do references/")
    check(refs and all(f"references/{n}" in body for n in refs)
          and {"wejscie.md", "ciecia-pdi.md", "flaga-funkcji.md", "bezpieczenstwo.md", "waga.md",
               "tryby-i-zatrzymania.md"} <= set(refs),
          f"T-21: każdy plik references/ jest wymieniony w SKILL.md: {refs}")
    check("tylko odczyt" in ref("wejscie.md") and "intake.py tracker" in ref("wejscie.md")
          and "Flag: <klucz>" in ref("flaga-funkcji.md") and "środowisku testowym" in ref("flaga-funkcji.md")
          and "feedback.md" in ref("bezpieczenstwo.md") and "min-release-age" in ref("bezpieczenstwo.md"),
          "T-22: szczegóły trackera, flagi funkcji i skanu bezpieczeństwa są w plikach references/")

    # pomiar po E1: STOP przed założeniem zadania nie zostawia śladu ani raportu; polecenia złożone są odrzucane
    check("zawsze zakładasz" in entry and "§1" in entry and "ślad" in entry,
          "T-23: gdy treść zadania jest (nawet niepełna), pętla zawsze zakłada zadanie; pytania o kryteria idą w §1, "
          "żeby STOP zostawił ślad i raport")
    review = next((ln for ln in loop.splitlines() if "**Przegląd zakresu:**" in ln), "")
    check("zawsze" in review and "`scope-reviewer`" in review and "małym diffie" in review,
          f"T-25: przegląd zakresu robi zawsze scope-reviewer, także przy małym diffie (nie sesja główna): {review}")
    check("AC-1" in loop and "dodatkowy commit" in loop,
          "T-26: identyfikator kryterium w teście od pierwszej wersji — dopisywanie po fakcie to dodatkowy commit")
    # krok E2: waga zadania — przydziela ją skrypt, pętla mówi człowiekowi, co wybrano, i zna skutki
    start = body.split("## 0.", 1)[-1].split("## 1.", 1)[0]
    waga = ref("waga.md")
    check("`Waga:" in start and "references/waga.md" in start and "jednym zdaniem" in start,
          "T-27: start — linię `Waga:` pętla przekazuje człowiekowi jednym zdaniem; skutki w references/waga.md")
    check(all(w in waga for w in ("lekka", "zwykła", "pełna", "run_state.py weight", "--by human:", "security-reviewer",
                                  "approve", "STOP", "bez `spec.md`")),
          "T-28: references/waga.md — trzy wagi, skutki, kto zmienia, obowiązkowy przegląd przy pełnej, STOP bez nadzoru")
    # krok E3: tryby (Plan / zwykły / Auto), zgoda człowieka na plan zapisana skryptem, zamknięta lista kodów STOP
    import re as _re
    modes = ref("tryby-i-zatrzymania.md")
    plan_part = body.split("## 2.", 1)[-1].split("## 3.", 1)[0]
    stop_part = body.split("## Blok STOP", 1)[-1].split("## Przykład", 1)[0]
    check("`--plan`" in start and "run_state.py approve" in plan_part and "references/tryby-i-zatrzymania.md" in plan_part,
          "T-29: tryb z polecenia człowieka trafia do pierwszego `stage` (--auto albo --plan); zgodę na plan zapisuje "
          "`run_state.py approve`; szczegóły w references/tryby-i-zatrzymania.md")
    script_text = (ROOT / state).read_text(encoding="utf-8")
    block = script_text.split("STOP_CODES = {", 1)[-1].split("}", 1)[0]
    codes = _re.findall(r'^\s*"([a-z-]+)":', block, _re.M)
    check("--code" in stop_part and len(codes) >= 10 and all(f"`{c}`" in modes for c in codes)
          and all(w in modes for w in ("Plan", "Auto", "approve", "mode")),
          f"T-30: blok STOP ma kod z zamkniętej listy; references/tryby-i-zatrzymania.md opisuje każdy kod ze skryptu: "
          f"{[c for c in codes if f'`{c}`' not in modes]}")
    check(all(f"`{c}`" in stop_part for c in codes),
          f"T-32: sekcja „Blok STOP” w SKILL.md wymienia wszystkie kody (pomiar po E3: w 8 z 15 przebiegów pętla "
          f"zgadywała kod i dostawała odmowę): brak {[c for c in codes if f'`{c}`' not in stop_part]}")
    check(all(w in modes for w in ("Komunikat dla człowieka", "AskUserQuestion", "run_state.py message", "własnego opisu")),
          "T-31: po zapisie zatrzymania pętla pokazuje człowiekowi komunikat ze skryptu (pytanie narzędziem z opcjami), "
          "a nie własny opis")
    rules = body.split("## Wejście", 1)[0]
    check("nie łączysz poleceń" in rules and all(s in rules for s in ("`;`", "`&&`", "potok")),
          "T-24: reguła „jedna czynność na polecenie” mówi wprost, czego nie łączyć (`;`, `&&`, potok)")

    # krok E6: cięcie zmiany pdi idzie drogą zadania — ten sam przebieg ze specyfikacją, dowodami i śladem kryteriów
    check("CHG-12-TSK-57" in cuts and ".tf/runs/cuts" not in cuts and "stary" not in cuts and "odmawia" not in cuts
          and "bez zadania" not in cuts,
          "T-33: references/ciecia-pdi.md opisuje zadanie cięcia `<CHG>-<TSK>`, bez starego układu `.tf/runs/cuts/`")
    check(all(w in cuts for w in ("spec", "verify", "trace", "ticket.md")) and "bramce" in cuts and "security-reviewer" in cuts,
          "T-34: cięcie ma specyfikację, dowody i ślad; zgodę na plan daje bramka zmiany, przegląd bezpieczeństwa zostaje")
    check("docs(task): record" in cuts and "runs/TSK-" in cuts and "changes/INDEX.md" not in body + cuts
          and "pierwszy commit" in " ".join(cuts.split()),
          "T-35: jeden commit końcowy (katalog zadania i raport cięcia); skill nie każe już dodawać INDEX.md — polecenie "
          "commitu drukuje `finish`; pierwszy commit gałęzi to kawałek "
          "— z niego pdi bierze tytuł PR")
    weight_ref = ref("waga.md")
    check("nie ma wagi" not in weight_ref and "cięci" in weight_ref and "bramce" in weight_ref,
          "T-36: references/waga.md — cięcie ma wagę; przy pełnej przebieg bez nadzoru nie staje, bo plan zmiany "
          "zatwierdzono na bramce pdi")
    guide = next((p for p in (ROOT / ".tf" / "factory" / "PETLA.md",) if p.is_file()), None)
    gtext = guide.read_text(encoding="utf-8") if guide else ""
    check(guide is not None and ".tf/runs/cuts" not in gtext and "CHG-12-TSK-57" in gtext,
          f"T-37: PETLA.md opisuje cięcie jako zadanie `<CHG>-<TSK>`, bez wyjątku starego układu: {guide}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów pętli tf w rdzeniu")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
