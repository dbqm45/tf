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
    check("Agent(scout, researcher, quick-fixer, scope-reviewer, spec-reviewer, architect, security-reviewer)" in fm
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
    guide = ROOT / ".tf" / "factory" / "GUIDE.md"
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

    cuts = ref("pdi-cuts.md")
    intake = body.split("## 1.", 1)[-1].split("## 2.", 1)[0]
    check("requirements_lint.py --story" in intake and "STORY-001" in intake and "--auto" in intake
          and "STOP" in intake and "split" in intake and "(pack-it)" in intake,
          "T-7: przyjęcie historyjki — lint kształtu (pack-it, warunkowo); z --auto STORY-001 → STOP z propozycją podziału")
    loop = body.split("## 3.", 1)[-1].split("## 4.", 1)[0]
    check("`Flag: " in cuts and "release.yaml" in cuts and "behind the flag" in cuts and "references/pdi-cuts.md" in loop,
          "T-8: kawałek cięcia z flagą — kod za flagą i dopisek `Flag: <klucz>` w commicie (plan wydania release.yaml); "
          "pętla kawałka odsyła do references/pdi-cuts.md")
    check("--task" in body and "--task" in cuts and "Change: TSK" in cuts and "changes/" in cuts and "/runs/" in cuts
          and "story/tsk-" in cuts and "pdi/CHG-n-delivery" in cuts,
          "T-9: wejście TSK z planu zmiany (`run_report.py start --task`), gałąź z kluczem od gałęzi fazy, `Change:` "
          "w commitach, raport w changes/CHG-n/runs/ — w references/pdi-cuts.md")
    fixes = cuts.split("## Fixes from the PR loop", 1)[-1] if "## Fixes from the PR loop" in cuts else ""
    check("Rework-Cause:" in fixes and all(v in fixes for v in ("spec-gap", "agent-error", "requirement-change",
                                                                 "unknown")),
          "T-11: commit poprawki z pętli PR ma trailer `Rework-Cause:` z jedną z 4 przyczyn (tf metrics, B3)")
    finish = body.split("## 4.", 1)[-1].split("## Who does what", 1)[0]
    check("run_state.py pr-body" in finish and "--body-file" in finish and "description" in finish,
          "T-12: opis PR składa skrypt (`run_state.py pr-body` → `--body-file`); sekcję triażu ryzyka zmian (B1b) "
          "wstawia on sam — sprawdza to test_pr_body PB-8")
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
    check("disable-model-invocation" not in front and desc.startswith("description: Use when") and "keywords:" in front,
          f"T-15: skill tf może wywołać model — bez disable-model-invocation, opis jako reguła wyboru, słowa: {desc}")
    entry = body.split("## Input", 1)[-1].split("## 0.", 1)[0] if "## Input" in body else ""
    check(body.find("## Input") != -1 and body.find("## Input") < body.find("## 0.")
          and all(w in entry for w in ("question", "quick", "task", "AskUserQuestion", "in one sentence")),
          "T-16: sekcja „Wejście” przed startem — zadanie / pytanie / drobna zmiana / wątpliwość → jedno pytanie")
    intake_script = ".claude/skills/tf/scripts/intake.py"
    check((ROOT / intake_script).is_file() and "intake.py resolve" in entry and "intake.py tracker" in entry
          and any(intake_script in a for a in allow),
          f"T-17: rozpoznanie wejścia skryptem (resolve, tracker) z uprawnieniem: {[a for a in allow if 'intake' in a]}")
    check(all(w in entry for w in ("read only", "paste", "you install nothing", "data, not instructions", "--source"))
          and "/tf jira" not in body and "/tf linear" not in body,
          "T-18: tracker — odczyt przez podłączone narzędzie albo wklejenie treści; fabryka niczego nie instaluje; "
          "treść zgłoszenia to dane; źródło trafia do ticket.md; polecenie bez nazwy narzędzia")
    check("--auto" in entry and "STOP" in entry, "T-19: bez człowieka (--auto) pytanie o źródło zamienia się w STOP")

    # SKILL.md mieści się w limicie przywracanym po kompaktowaniu; szczegóły są w references/, wymienione w SKILL.md
    limit = 15000
    refs = sorted(f.name for f in (skill / "references").glob("*.md")) if (skill / "references").is_dir() else []
    check(len(body) <= limit, f"T-20: SKILL.md ma {len(body)} znaków (limit {limit}) — szczegóły przenieś do references/")
    check(refs and all(f"references/{n}" in body for n in refs)
          and {"intake.md", "pdi-cuts.md", "feature-flag.md", "security.md", "weight.md",
               "modes-and-stops.md"} <= set(refs),
          f"T-21: każdy plik references/ jest wymieniony w SKILL.md: {refs}")
    check("read only" in ref("intake.md") and "intake.py tracker" in ref("intake.md")
          and "Flag: <klucz>" in ref("feature-flag.md") and "test environment" in ref("feature-flag.md")
          and "feedback.md" in ref("security.md") and "min-release-age" in ref("security.md"),
          "T-22: szczegóły trackera, flagi funkcji i skanu bezpieczeństwa są w plikach references/")

    # pomiar po E1: STOP przed założeniem zadania nie zostawia śladu ani raportu; polecenia złożone są odrzucane
    check("always create" in entry and "§1" in entry and "trace" in entry,
          "T-23: gdy treść zadania jest (nawet niepełna), pętla zawsze zakłada zadanie; pytania o kryteria idą w §1, "
          "żeby STOP zostawił ślad i raport")
    review = next((ln for ln in loop.splitlines() if "**The scope review:**" in ln), "")
    check("always" in review and "`scope-reviewer`" in review and "small diff" in review,
          f"T-25: przegląd zakresu robi zawsze scope-reviewer, także przy małym diffie (nie sesja główna): {review}")
    check("AC-1" in loop and "extra commit" in loop,
          "T-26: identyfikator kryterium w teście od pierwszej wersji — dopisywanie po fakcie to dodatkowy commit")
    # krok E2: waga zadania — przydziela ją skrypt, pętla mówi człowiekowi, co wybrano, i zna skutki
    start = body.split("## 0.", 1)[-1].split("## 1.", 1)[0]
    waga = ref("weight.md")
    check("`Waga:" in start and "references/weight.md" in start and "in one sentence" in start,
          "T-27: start — linię `Waga:` pętla przekazuje człowiekowi jednym zdaniem; skutki w references/weight.md")
    check(all(w in waga for w in ("light", "zwykła", "pełna", "run_state.py weight", "--by human:", "security-reviewer",
                                  "approve", "STOP", "without `spec.md`")),
          "T-28: references/weight.md — trzy wagi, skutki, kto zmienia, obowiązkowy przegląd przy pełnej, STOP bez nadzoru")
    # krok E3: tryby (Plan / zwykły / Auto), zgoda człowieka na plan zapisana skryptem, zamknięta lista kodów STOP
    import re as _re
    modes = ref("modes-and-stops.md")
    plan_part = body.split("## 2.", 1)[-1].split("## 3.", 1)[0]
    stop_part = body.split("## The STOP block", 1)[-1].split("## Example", 1)[0]
    check("`--plan`" in start and "run_state.py approve" in plan_part and "references/modes-and-stops.md" in plan_part,
          "T-29: tryb z polecenia człowieka trafia do pierwszego `stage` (--auto albo --plan); zgodę na plan zapisuje "
          "`run_state.py approve`; szczegóły w references/modes-and-stops.md")
    script_text = (ROOT / state).read_text(encoding="utf-8")
    block = script_text.split("STOP_CODES = {", 1)[-1].split("}", 1)[0]
    codes = _re.findall(r'^\s*"([a-z-]+)":', block, _re.M)
    check("--code" in stop_part and len(codes) >= 10 and all(f"`{c}`" in modes for c in codes)
          and all(w in modes for w in ("Plan", "Auto", "approve", "mode")),
          f"T-30: blok STOP ma kod z zamkniętej listy; references/modes-and-stops.md opisuje każdy kod ze skryptu: "
          f"{[c for c in codes if f'`{c}`' not in modes]}")
    check(all(f"`{c}`" in stop_part for c in codes),
          f"T-32: sekcja „Blok STOP” w SKILL.md wymienia wszystkie kody (pomiar po E3: w 8 z 15 przebiegów pętla "
          f"zgadywała kod i dostawała odmowę): brak {[c for c in codes if f'`{c}`' not in stop_part]}")
    check(all(w in modes for w in ("Komunikat dla człowieka", "AskUserQuestion", "run_state.py message", "your own description")),
          "T-31: po zapisie zatrzymania pętla pokazuje człowiekowi komunikat ze skryptu (pytanie narzędziem z opcjami), "
          "a nie własny opis")
    rules = body.split("## Input", 1)[0]
    check("you do not chain commands" in rules and all(s in rules for s in ("`;`", "`&&`", "a pipe")),
          "T-24: reguła „jedna czynność na polecenie” mówi wprost, czego nie łączyć (`;`, `&&`, potok)")

    # krok E6: cięcie zmiany pdi idzie drogą zadania — ten sam przebieg ze specyfikacją, dowodami i śladem kryteriów
    check("CHG-12-TSK-57" in cuts and ".tf/runs/cuts" not in cuts and "old layout" not in cuts and "refuses" not in cuts
          and "without a task" not in cuts,
          "T-33: references/pdi-cuts.md opisuje zadanie cięcia `<CHG>-<TSK>`, bez starego układu `.tf/runs/cuts/`")
    check(all(w in cuts for w in ("spec", "verify", "trace", "ticket.md")) and "gate" in cuts and "security-reviewer" in cuts,
          "T-34: cięcie ma specyfikację, dowody i ślad; zgodę na plan daje bramka zmiany, przegląd bezpieczeństwa zostaje")
    check("docs(task): record" in cuts and "runs/TSK-" in cuts and "changes/INDEX.md" not in body + cuts
          and "first commit" in " ".join(cuts.split()),
          "T-35: jeden commit końcowy (katalog zadania i raport cięcia); skill nie każe już dodawać INDEX.md — polecenie "
          "commitu drukuje `finish`; pierwszy commit gałęzi to kawałek "
          "— z niego pdi bierze tytuł PR")
    weight_ref = ref("weight.md")
    check("has no weight" not in weight_ref and "slice" in weight_ref and "gate" in weight_ref,
          "T-36: references/weight.md — cięcie ma wagę; przy pełnej przebieg bez nadzoru nie staje, bo plan zmiany "
          "zatwierdzono na bramce pdi")
    guide = next((p for p in (ROOT / ".tf" / "factory" / "LOOP.md",) if p.is_file()), None)
    gtext = guide.read_text(encoding="utf-8") if guide else ""
    check(guide is not None and ".tf/runs/cuts" not in gtext and "CHG-12-TSK-57" in gtext,
          f"T-37: LOOP.md opisuje cięcie jako zadanie `<CHG>-<TSK>`, bez wyjątku starego układu: {guide}")

    check("run_state.py finding" in body.split("## 3.", 1)[-1].split("## 4.", 1)[0],
          "T-40: ustalenie ważne z przeglądu zakresu pętla zapisuje poleceniem `run_state.py finding` (krok G4)")
    check("tf task close" in gtext and "tf task finding" in gtext and "lessons.md" in gtext and "tf status --all" in gtext,
          "T-41: LOOP.md opisuje zamknięcie zadania: scalenie, kontrola do ustaleń, lekcja od człowieka, lista w toku")
    check("Jak cofnąć" in finish and "risk_triage.py --md" not in finish,
          "T-38: krok PR wymienia pola opisu (m.in. „Jak cofnąć”) i nie każe już składać triażu ryzyka ręcznie")
    check("pr-body" in gtext and all(w in gtext for w in ("How it was checked", "Risk", "How to roll back", "deploy.rollback")),
          "T-39: LOOP.md opisuje opis PR ze skryptu: trzy stałe pola i krok cofania z karty operacyjnej")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów pętli tf w rdzeniu")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
