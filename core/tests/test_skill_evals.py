#!/usr/bin/env python3
"""Testy runnera ewaluacji skilli i plików scenariuszy (bez modelu, z atrapą claude): python3 tests/test_skill_evals.py"""
import importlib.util
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("run_skill_evals", HERE / "run_skill_evals.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

FAKE = """#!/usr/bin/env python3
import json, sys
prompt = sys.argv[sys.argv.index("-p") + 1]
if "--json-schema" in sys.argv:
    schema = sys.argv[sys.argv.index("--json-schema") + 1]
    out = ({"verdicts": [{"reason": "odpowiedź opisuje zwrot", "met": "zwrot" in prompt}]} if "reason" in schema
           else {"met": ["zwrot" in prompt]})
    print(json.dumps({"type": "result", "subtype": "success", "structured_output": out, "total_cost_usd": 0.005}))
    raise SystemExit(0)
print(json.dumps({"type": "system", "subtype": "init"}))
if "UŻYJ" in prompt:
    print(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Skill", "input": {"skill": "be-api-design"}}]}}))
import os
if os.environ.get("FAKE_ARGV"):
    open(os.environ["FAKE_ARGV"], "w").write(json.dumps(sys.argv[1:]))
if "WYCIEK" in prompt:
    print(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Read", "input": {"file_path": "/home/u/tf/core/skills/be-api-design/SKILL.md"}},
        {"type": "tool_use", "name": "Grep", "input": {"pattern": "idempotency", "path": "/home/u/tf"}},
        {"type": "tool_use", "name": "Read", "input": {"file_path": "notatki.md"}}]}}))
if "CZYTAJ" in prompt:
    print(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Read", "input": {"file_path": "/tmp/x/.claude/skills/be-database/SKILL.md"}}]}}))
print(json.dumps({"type": "result", "subtype": "success", "result": "Użyj nagłówka Idempotency-Key i zwróć 409.",
                  "total_cost_usd": 0.01, "num_turns": 2}))
"""


PROTOCOL_TESTS = 4


def protocol_tests() -> list[str]:
    """Zamknięty zbiór testowy (holdout) i protokół raportu „wynik czy koszt”."""
    fails = []
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "core-grounding.json"
        bad.write_text(json.dumps({"skill": "core-grounding", "scenarios": [
            {"id": "a", "expect": "trigger", "prompt": "Jak obsłużyć ponowienia POST?", "checks": {"all": [["x"]]}},
            {"id": "b", "expect": "trigger", "prompt": "Ponowienie POST bez duplikatu?", "checks": {"all": [["x"]]},
             "holdout": "tak"},
            {"id": "c", "expect": "no-trigger", "prompt": "Indeksy w tabeli orders?", "neighbor": "be-database"}]}),
            encoding="utf-8")
        if not any("holdout" in e for e in ev.validate_file(bad)):
            fails.append("validate_file: holdout musi być true/false")
        # osobny plik holdout/<skill>.json: same scenariusze trigger ze sprawdzeniami, poza odciskiem bramki skilla
        ho = Path(d) / "holdout" / "core-grounding.json"
        ho.parent.mkdir()
        ho.write_text(json.dumps({"skill": "core-grounding", "scenarios": [
            {"id": "h1", "expect": "trigger", "prompt": "Klient ponawia płatność po timeoucie, co z duplikatem?",
             "checks": {"all": [["idempot"]]}}]}), encoding="utf-8")
        okh = ev.validate_file(ho, holdout=True)
        ho.write_text(json.dumps({"skill": "core-grounding", "scenarios": [
            {"id": "h1", "expect": "no-trigger", "prompt": "Pytanie sąsiada o indeksy", "neighbor": "be-database"}]}),
            encoding="utf-8")
        badh = ev.validate_file(ho, holdout=True)
        if okh or not badh:
            fails.append(f"validate_file(holdout): jeden scenariusz trigger wystarcza, no-trigger to błąd: {okh} {badh}")
    scs = [{"id": "a", "expect": "trigger"}, {"id": "h", "expect": "trigger", "holdout": True},
           {"id": "n", "expect": "no-trigger"}]
    if [s["id"] for s in ev.tuning_set(scs)] != ["a", "n"] or [s["id"] for s in ev.holdout_set(scs)] != ["h"]:
        fails.append("tuning_set/holdout_set: zbiór strojenia bez scenariuszy holdout, holdout osobno")
    row = lambda sid, base, passed, met, cost, ho=False, rep=0: {
        "skill": "s", "id": sid, "expect": "trigger", "model": "haiku", "baseline": base, "holdout": ho, "repeat": rep,
        "passed": passed, "triggered": passed, "checks_ok": passed, "groups_total": 2, "groups_met": met,
        "cost": cost, "error": None, "misses": [], "skills_used": []}
    res = [row("a", False, True, 2, 0.10), row("b", False, False, 1, 0.10), row("a", True, False, 1, 0.05),
           row("b", True, False, 0, 0.05), row("h", False, True, 2, 0.10, ho=True, rep=0),
           row("h", False, False, 1, 0.10, ho=True, rep=1),
           # bez skilli nic się nie uruchamia — pełną odpowiedź liczymy po kryteriach, nie po uruchomieniu
           {**row("c", True, False, 2, 0.05), "checks_ok": True}]
    rows = {(r["model"], r["baseline"], r["set"]): r for r in ev.protocol(res)}
    w = rows.get(("haiku", False, "strojenie")) or {}
    if (w.get("tasks"), w.get("full_pass"), w.get("criteria")) != (2, 1, 0.75) or abs(w.get("cost_per_solved", 0) - 0.20) > 1e-9:
        fails.append(f"protocol: ze skillami — zadania, zaliczone w całości, średnia kryteriów, koszt na rozwiązane: {w}")
    b = rows.get(("haiku", True, "strojenie")) or {}
    h = rows.get(("haiku", False, "holdout")) or {}
    if b.get("full_pass") != 1 or b.get("tasks") != 3 or h.get("unstable") != 1 or h.get("tasks") != 2:
        fails.append(f"protocol: bez skilli pełna odpowiedź po kryteriach; holdout osobno, niestabilny między powtórzeniami: {b} {h}")
    if w.get("triggered") != 1:
        fails.append(f"protocol: uruchomienie skilla raportowane osobno: {w}")
    return fails


def main() -> int:
    fails = []
    # 1–2. sprawdzenia treści
    ok, _ = ev.evaluate_checks("Nagłówek Idempotency-Key, konflikt 409", {"all": [["idempotency-key"], ["409|422"]]})
    if not ok:
        fails.append("checks.all: poprawna odpowiedź odrzucona")
    ok, miss = ev.evaluate_checks("Użyj PUT zamiast POST", {"all": [["idempotency"]], "none": ["PUT zamiast POST"]})
    if ok or len(miss) != 2:
        fails.append(f"checks: brak lub niepożądana fraza nie wykryta ({miss})")
    # 3. parsowanie strumienia: Skill z prefiksem wtyczki i Read SKILL.md
    p = ev.parse_stream([
        json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "x:be-api-design"}}]}}),
        json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": "/w/.claude/skills/qa-regression/SKILL.md"}}]}}),
        "nie-json",
        json.dumps({"type": "result", "subtype": "success", "result": "ok", "total_cost_usd": 0.02, "num_turns": 3}),
    ])
    if p["skills"] != ["be-api-design", "qa-regression"] or p["cost"] != 0.02 or p["text"] != "ok" or p["error"]:
        fails.append(f"parse_stream: {p}")
    # 4–6. przebieg z atrapą claude
    with tempfile.TemporaryDirectory() as d:
        fake = Path(d) / "claude"
        fake.write_text(FAKE, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        os.environ["CLAUDE_BIN"] = str(fake)
        args = SimpleNamespace(max_turns=4, timeout=60, isolated=False, judge="none", bare=True)
        base = {"skill": "be-api-design", "checks": {"all": [["idempotency-key"]]}}
        r = ev.run_one({**base, "id": "a", "expect": "trigger", "prompt": "UŻYJ skilla do POST /orders"}, "haiku", False, args)
        if not (r["passed"] and r["triggered"] and r["checks_ok"]):
            fails.append(f"run_one trigger: {r}")
        r = ev.run_one({**base, "id": "b", "expect": "trigger", "prompt": "bez skilla, pytanie o POST"}, "haiku", False, args)
        if r["passed"] or r["triggered"] or not r["checks_ok"]:
            fails.append(f"run_one: brak uruchomienia powinien oblać scenariusz trigger: {r}")
        r = ev.run_one({"skill": "be-api-design", "id": "c", "expect": "no-trigger", "neighbor": "be-database",
                        "prompt": "CZYTAJ indeksy w tabeli"}, "haiku", False, args)
        if not r["passed"] or r["skills_used"] != ["be-database"]:
            fails.append(f"run_one no-trigger: {r}")
        # 7. ocena modelem: wyrażenie nie trafia, oceniający uznaje wymaganie za spełnione
        args.judge = "haiku"
        r = ev.run_one({"skill": "be-api-design", "id": "d", "expect": "trigger", "prompt": "UŻYJ skilla",
                        "checks": {"all": [["zwrot\\w* tej samej odpowiedzi"]]}}, "haiku", False, args)
        if not (r["passed"] and r["judged"]) or abs(r["cost"] - 0.015) > 1e-9:
            fails.append(f"ocena modelem: {r}")
        # 7b. sędzia inny niż oceniany model (develop-tests: „use a different model to evaluate”) i uzasadnienie
        # przed oceną w schemacie odpowiedzi sędziego
        pairs = {("auto", "haiku"): "sonnet", ("auto", "sonnet"): "haiku", ("auto", "opus"): "sonnet",
                 ("auto", "claude-haiku-5-5"): "sonnet", ("haiku", "haiku"): "haiku", ("opus", "haiku"): "opus"}
        got = {k: ev.judge_model(*k) for k in pairs}
        if got != pairs:
            fails.append(f"judge_model: {got}")
        args.judge = "auto"
        r = ev.run_one({"skill": "be-api-design", "id": "e", "expect": "trigger", "prompt": "UŻYJ skilla",
                        "checks": {"all": [["zwrot\\w* tej samej odpowiedzi"]]}}, "haiku", False, args)
        if not (r["passed"] and r["judged"]) or r["judged_by"] != "sonnet" or r.get("judge_same_model"):
            fails.append(f"sędzia auto: {r}")
        args.judge = "haiku"
        r = ev.run_one({"skill": "be-api-design", "id": "f", "expect": "trigger", "prompt": "UŻYJ skilla",
                        "checks": {"all": [["zwrot\\w* tej samej odpowiedzi"]]}}, "haiku", False, args)
        if not r.get("judge_same_model"):
            fails.append(f"sędzia = oceniany model powinien być oznaczony: {r}")
        rep = Path(d) / "raport.md"
        ev.report([r], rep)
        if "tej samej rodziny" not in rep.read_text(encoding="utf-8"):
            fails.append("raport: brak ostrzeżenia o sędzi tej samej rodziny co oceniany model")
        if '"reason"' not in ev.JUDGE_SCHEMA or ev.DEFAULT_JUDGE != "auto":
            fails.append("schemat sędziego bez uzasadnienia albo domyślny sędzia nie jest 'auto'")
        # 7c. izolacja przebiegu bez skilli: --restricted (pliki tylko w katalogu testu, bez Bash, bez ustawień
        # użytkownika i projektu) i wykrycie odczytu poza katalogiem testu w strumieniu — taki przebieg to błąd
        args.judge = "none"
        argv_file = Path(d) / "argv.json"
        os.environ["FAKE_ARGV"] = str(argv_file)
        leak = {**base, "id": "g", "expect": "trigger", "prompt": "WYCIEK UŻYJ skilla"}
        r = ev.run_one(leak, "haiku", True, args)
        argv = json.loads(argv_file.read_text(encoding="utf-8")) if argv_file.is_file() else []
        if "--restricted" not in argv:
            fails.append(f"bez skilli: brak --restricted w poleceniu: {argv}")
        if r.get("outside_reads") != ["/home/u/tf/core/skills/be-api-design/SKILL.md", "/home/u/tf"]:
            fails.append(f"bez skilli: odczyty poza katalogiem testu: {r.get('outside_reads')}")
        if r["passed"] or "poza katalogiem testu" not in (r["error"] or ""):
            fails.append(f"bez skilli: odczyt poza katalogiem testu powinien być błędem przebiegu: {r}")
        r = ev.run_one(leak, "haiku", False, args)
        argv = json.loads(argv_file.read_text(encoding="utf-8")) if argv_file.is_file() else []
        if "--restricted" in argv or not r.get("outside_reads") or r["error"]:
            fails.append(f"ze skillami: bez --restricted, odczyt zapisany, ale nie błąd: {argv} {r}")
        p = ev.parse_stream([json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Glob", "input": {"pattern": "**/*.md", "path": "/w/sub"}},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/w/a.md"}}]}})])
        if p.get("paths") != ["/w/sub", "/w/a.md"]:
            fails.append(f"parse_stream: ścieżki narzędzi plikowych: {p.get('paths')}")
        if ev.outside(["/w/a.md", "rel.md", "/w2/x", "/w/../etc/passwd"], "/w") != ["/w2/x", "/w/../etc/passwd"]:
            fails.append(f"outside: {ev.outside(['/w/a.md', 'rel.md', '/w2/x', '/w/../etc/passwd'], '/w')}")
        os.environ.pop("FAKE_ARGV")
        os.environ.pop("CLAUDE_BIN")
        # 8. walidacja błędnego pliku
        bad = Path(d) / "be-api-design.json"
        bad.write_text(json.dumps({"skill": "be-api-design", "scenarios": [
            {"id": "x", "expect": "trigger", "prompt": "krótko"},
            {"id": "x", "expect": "no-trigger", "prompt": "pytanie bez sąsiada o czymś"}]}), encoding="utf-8")
        errs = ev.validate_file(bad)
        if len(errs) < 4:
            fails.append(f"validate_file: za mało błędów dla złego pliku: {errs}")
    # 8b. --ids: tylko wybrane scenariusze (id albo skill:id); nieznany identyfikator to błąd, nie cichy pusty przebieg
    scs = [{"skill": "a", "id": "x"}, {"skill": "a", "id": "y"}, {"skill": "b", "id": "x"}]
    sel, unknown = ev.select_ids(scs, "y,b:x")
    if [(c["skill"], c["id"]) for c in sel] != [("a", "y"), ("b", "x")] or unknown:
        fails.append(f"select_ids: {sel} {unknown}")
    sel, unknown = ev.select_ids(scs, "x,zzz")
    if len(sel) != 2 or unknown != ["zzz"]:
        fails.append(f"select_ids: samo id pasuje do wszystkich skilli, nieznane zgłoszone: {sel} {unknown}")
    if ev.main(["run", "--skills", "be-api-design", "--ids", "nie-ma-takiego", "--yes"]) != 2:
        fails.append("--ids z nieznanym identyfikatorem powinno dać kod 2 bez uruchamiania modelu")
    # 9. wszystkie pliki scenariuszy w repozytorium
    files = sorted(ev.EVALS.glob("*.json"))
    errs = [e for f in files for e in ev.validate_file(f)]
    if errs:
        fails.append(f"pliki scenariuszy: {len(errs)} błędów, np. {errs[:3]}")
    skills = sorted(p.parent.name for p in ev.SKILLS.glob("*/SKILL.md"))
    missing = [s for s in skills if not (ev.EVALS / f"{s}.json").exists()]
    if files and missing:
        fails.append(f"skille bez scenariuszy: {missing[:5]}{' …' if len(missing) > 5 else ''}")
    # 10. podpowiedź skilli (hook skill_hint) na scenariuszach: trafność i brak szumu na poleceniach ogólnych
    if files:
        hs = importlib.util.spec_from_file_location("skill_hint", ev.ROOT / ".claude" / "hooks" / "skill_hint.py")
        hint = importlib.util.module_from_spec(hs)
        hs.loader.exec_module(hint)
        items = hint.load_index()
        trig = [(json.loads(f.read_text(encoding="utf-8"))["skill"], s) for f in files
                for s in ev.tuning_set(json.loads(f.read_text(encoding="utf-8"))["scenarios"]) if s["expect"] == "trigger"]
        hits = sum(sk in [it["name"] for _, it in hint.select(s["prompt"], items)] for sk, s in trig)
        # polecenie ogólne → brak podpowiedzi; dla prośby o commit dopuszczalne są tylko skille commitów (w małej
        # instalacji, bez konkurencji innych skilli, podpowiedź core-git-workflow jest trafna, nie szumem)
        generic = {"hej, jak się masz?": set(), "Jaka jest stolica Francji?": set(),
                   "Przetłumacz ten akapit na angielski": set(), "Co robi ten plik?": set(),
                   "Zrób commit z tymi zmianami": {"core-git-workflow", "core-conventional-commits"}}
        def noisy(g: str, ok: set) -> bool:
            picks = [it["name"] for _, it in hint.select(g, items)]
            return bool(picks) and (not ok or picks[0] not in ok)   # przy commicie liczy się lider podpowiedzi
        noise = sum(noisy(g, ok) for g, ok in generic.items())
        if trig and hits / len(trig) < 0.8:
            fails.append(f"skill_hint: trafność {hits}/{len(trig)} < 80% — sprawdź opisy skilli lub próg")
        if noise:
            fails.append(f"skill_hint: podpowiedź przy {noise} z {len(generic)} poleceń ogólnych")
    # 11–12. logi z prawdziwej pracy: decyzje hooka (bez treści polecenia) i skille użyte w sesji → raport
    import subprocess as sp
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d)
        (proj / ".claude").mkdir()
        (proj / ".claude" / "skills").symlink_to(ev.SKILLS)
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(proj)}
        env.pop("CLAUDE_SKILL_HINT_LOG_PROMPT", None)
        hooks = ev.ROOT / ".claude" / "hooks"
        prompt = "Jak zrobić paginację GET /orders z milionami rekordów? TAJNE-SLOWO"
        sp.run([sys.executable, str(hooks / "skill_hint.py")], input=json.dumps({"prompt": prompt, "session_id": "s1"}),
               capture_output=True, text=True, env=env)
        log = proj / ".claude" / "logs" / "skill-hints.jsonl"
        rec = json.loads(log.read_text(encoding="utf-8").splitlines()[0]) if log.exists() else {}
        # pierwsza podpowiedź to skill API; kolejne mogą dojść z innych nakładek (np. paginacja w OCPI przy pack-ev)
        api = (ev.SKILLS / "be-api-design").is_dir()      # skill z pack-it; bez niego sprawdzamy tylko brak treści w logu
        if ((api and (rec.get("hinted") or [None])[0] != "be-api-design")
                or "TAJNE" in log.read_text(encoding="utf-8") if log.exists() else api):
            fails.append(f"skill_hint: log decyzji niepoprawny albo zawiera treść polecenia: {rec}")
        tr = proj / "t.jsonl"
        tr.write_text(json.dumps({"type": "assistant", "message": {"id": "m1", "model": "x", "usage": {"output_tokens": 5},
                      "content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "be-api-design"}},
                                  {"type": "tool_use", "name": "Read", "input": {"file_path": "/p/.claude/skills/be-database/SKILL.md"}}]}}) + "\n")
        sp.run([sys.executable, str(hooks / "log_usage.py")], capture_output=True, text=True, env=env,
               input=json.dumps({"hook_event_name": "SessionEnd", "session_id": "s1", "transcript_path": str(tr)}))
        hr = importlib.util.spec_from_file_location("hint_report", ev.ROOT / "factory" / "hint_report.py")
        rep_mod = importlib.util.module_from_spec(hr)
        hr.loader.exec_module(rep_mod)
        logs = proj / ".claude" / "logs"
        r = rep_mod.analyse(rep_mod.read_jsonl(logs / "skill-hints.jsonl", None), rep_mod.read_jsonl(logs / "usage.jsonl", None))
        if api and (r["hit"].get("be-api-design") != 1 or r["missed"].get("be-database") != 1):   # podpowiedź z pack-it
            fails.append(f"hint_report: trafione/przeoczone niepoprawne: {r}")
    fails += protocol_tests()
    total = 12 + PROTOCOL_TESTS
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów ewaluacji skilli ({len(files)} plików scenariuszy)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
