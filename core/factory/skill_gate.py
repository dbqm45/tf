#!/usr/bin/env python3
"""
Bramka jakości skilla — obowiązkowa przy dodaniu i każdej zmianie skilla.

  python3 factory/skill_gate.py core-grounding                 # bezpłatne sprawdzenia (bez modelu)
  python3 factory/skill_gate.py --changed                      # skille zmienione od ostatniej bramki
  python3 factory/skill_gate.py --status [--strict]            # stan bramki wszystkich skilli (--strict: kod 1 w CI)
  python3 factory/skill_gate.py core-grounding --model haiku,sonnet --budget 2 --yes   # + ewaluacja na modelu (płatna)
  python3 factory/skill_gate.py core-grounding --model sonnet --baseline --yes         # + porównanie bez skilli

Sprawdzenia bezpłatne (kolejno, każde musi przejść):
  1. struktura      — reguły `build.py check` dla tego skilla (opis ≤170 znaków, metadata.katalog z granicami, brak `paths`,
                      długość SKILL.md);
  2. scenariusze    — plik ewaluacji: ≥3 scenariusze, ≥2 „trigger” ze sprawdzeniami treści, ≥1 „no-trigger” z sąsiadem;
  3. podpowiedź     — hook skill_hint wskazuje skill przy jego pytaniach, a przy pytaniu sąsiada nie stawia go na pierwszym miejscu;
  4. regresja       — testy ewaluacji fabryki: trafność podpowiedzi dla WSZYSTKICH skilli ≥80% i brak szumu
                      (nowy skill nie może „podkradać” pytań innym);
  5. polszczyzna    — linter bez uwag wysokiej wagi w SKILL.md i references/;
  6. odwołania      — ścieżki i linki w skillu (tylko ostrzeżenia);
  7. audyt          — `skill_audit.py`: bezpieczeństwo (sieć bez deklaracji, curl | sh, wstrzyknięte polecenia,
                      dostęp do sekretów, eval, ukryte znaki, szerokie allowed-tools) i zalecenia Anthropic (opis
                      z regułą „kiedy”, przykłady, pliki, do których skill się odwołuje); wysoka i średnia waga blokują.
Opcjonalnie płatnie: ewaluacja `run_skill_evals.py` na wskazanych modelach; zaliczone muszą być wszystkie scenariusze.

Wynik trafia do rejestru bramki (`tests/skill_gate.json` w repozytorium fabryki, `.claude/skill-gate.json` w projekcie) z
odciskiem treści skilla. `build.py check` ostrzega o skillach zmienionych po ostatniej bramce, a hook skill_change_guard
przypomina o bramce po edycji skilla. Ewaluację na modelu uruchamiasz za zgodą człowieka — kosztuje (~$0,10–0,30
na scenariusz i model).
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
TESTS = ROOT / "tests" if (ROOT / "tests" / "run_skill_evals.py").exists() else ROOT / ".claude" / "tests"
EVALS = TESTS / "skill_evals"
REGISTRY = ROOT / "tests" / "skill_gate.json" if (ROOT / "tests" / "run_skill_evals.py").exists() \
    else ROOT / ".claude" / "skill-gate.json"
LINT = SKILLS / "txt-polish-correctness" / "scripts" / "polish_lint.py"   # pack-editorial-pl; bez niej krok pominięty
GROUND = SKILLS / "core-grounding" / "scripts" / "grounding_check.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fingerprint(name: str) -> str:
    return load_module(ROOT / "factory" / "build.py", "factory_build").skill_fingerprint(name)


def read_registry() -> dict:
    """Wszystkie rejestry: fabryki (`tests/` lub `.claude/tests/` po instalacji) i projektu (`.claude/skill-gate.json`)."""
    return load_module(ROOT / "factory" / "build.py", "factory_build").gate_registry()


def write_registry(reg: dict) -> None:
    """Zapis tylko do własnego rejestru; wpisy identyczne z rejestrem fabryki nie są powielane w projekcie."""
    own = {}
    try:
        own = json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else {}
    except json.JSONDecodeError:
        pass
    base = {} if REGISTRY == ROOT / "tests" / "skill_gate.json" else \
        load_module(ROOT / "factory" / "build.py", "factory_build").gate_registry_factory()
    for k, v in reg.items():
        if base.get(k) != v:
            own[k] = v
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(dict(sorted(own.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ───────────── sprawdzenia bezpłatne ─────────────

def check_structure(name: str) -> tuple[list[str], list[str]]:
    build = load_module(ROOT / "factory" / "build.py", "factory_build")
    errors, warnings = build.validate()
    mine = lambda xs: [x for x in xs if re.search(rf"\b(skill|skille?) {re.escape(name)}\b|'{re.escape(name)}'", x)]
    return mine(errors), [w for w in mine(warnings) if "bramk" not in w and "bramce" not in w]   # stan bramki to wynik, nie wejście


def check_scenarios(name: str) -> tuple[list[str], list[str], dict]:
    ev = load_module(TESTS / "run_skill_evals.py", "run_skill_evals")
    path = EVALS / f"{name}.json"
    if not path.exists():
        return [f"brak pliku scenariuszy {path.relative_to(ROOT)} — utwórz go PRZED treścią skilla "
                "(`build.py new-skill` tworzy szkielet)"], [], {}
    errs = ev.validate_file(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    sc = data.get("scenarios") or []
    manual = ev.skill_meta(name).get("disable-model-invocation") == "true"
    trig = [s for s in sc if s.get("expect") == "trigger"]
    no = [s for s in sc if s.get("expect") == "no-trigger"]
    if not manual and len(trig) < 2:
        errs.append(f"{len(trig)} scenariuszy trigger (wymagane ≥2: różne sformułowania prawdziwego problemu)")
    if not no:
        errs.append("brak scenariusza no-trigger (pytanie sąsiedniego skilla — pilnuje granic)")
    if any(n.get("neighbor") == name for n in no):
        errs.append("no-trigger wskazuje jako sąsiada ten sam skill")
    if "TODO" in path.read_text(encoding="utf-8"):
        errs.append("plik scenariuszy zawiera TODO — uzupełnij szkielet")
    warns = []
    if trig and all(len(s.get("checks", {}).get("all") or []) < 2 for s in trig):
        warns.append("sprawdzenia treści mają po jednej grupie — dodaj drugą, sprawdzającą wiedzę specyficzną dla skilla")
    return errs, warns, {"trigger": trig, "no": no, "manual": manual}


def check_hint(name: str, sc: dict) -> tuple[list[str], list[str], str]:
    hint = load_module(ROOT / ".claude" / "hooks" / "skill_hint.py", "skill_hint")
    items = hint.load_index()
    errs, warns = [], []
    if sc.get("manual"):
        return errs, ["skill ręczny (disable-model-invocation) — podpowiedź go nie dotyczy"], "—"
    hits = 0
    for s in sc.get("trigger", []):
        picks = [it["name"] for _, it in hint.select(s["prompt"], items)]
        if name in picks:
            hits += 1
        else:
            top = [it["name"] for _, it in hint.rank(s["prompt"], items)[:3]]
            warns.append(f"#{s['id']}: hook nie podpowie skilla (najbliżej: {', '.join(top)}) — dopisz słowa do "
                         "metadata.slowa albo opisu")
    if sc.get("trigger") and hits == 0:
        errs.append("hook nie podpowiada skilla przy żadnym jego pytaniu — model najpewniej go nie wczyta")
    for s in sc.get("no", []):
        picks = [it["name"] for _, it in hint.select(s["prompt"], items)]
        if picks and picks[0] == name:
            nb = s.get("neighbor")
            if nb in picks or set(s.get("accept") or []) & set(picks):
                warns.append(f"#{s['id']}: przy pytaniu sąsiada ({nb}) hook stawia ten skill przed nim (podpowiada oba — "
                             "model wybiera; rozważ słowa sąsiada w metadata.slowa)")
            else:
                errs.append(f"#{s['id']}: przy pytaniu sąsiada ({nb}) hook podpowiada ten skill, a sąsiada wcale — "
                            "zawęź opis albo dopisz słowa sąsiadowi")
    return errs, warns, f"{hits}/{len(sc.get('trigger', []))}"


def check_regression() -> list[str]:
    r = subprocess.run([sys.executable, str(TESTS / "test_skill_evals.py")], capture_output=True, text=True, timeout=600)
    return [] if r.returncode == 0 else [ln for ln in r.stdout.splitlines() if ln.startswith("✗")][:5] or [r.stdout[-500:]]


def check_polish(name: str) -> tuple[list[str], list[str]]:
    if not LINT.exists():
        return [], ["brak lintera polszczyzny — pominięto"]
    d = SKILLS / name
    targets = [str(d / "SKILL.md")] + ([str(d / "references")] if (d / "references").is_dir() else [])
    r = subprocess.run([sys.executable, str(LINT), *targets], capture_output=True, text=True, timeout=120)
    m = re.search(r"wysokich: (\d+)", r.stdout)
    high = int(m.group(1)) if m else 0
    lines = [ln for ln in r.stdout.splitlines() if "[" in ln and "|" in ln]
    if high:
        return [f"{high} uwag wysokiej wagi w polszczyźnie, np. {next((l for l in lines if 'WYSOKI' in l), '')}"], []
    return [], ([f"{len(lines)} uwag niskiej/średniej wagi (polish_lint)"] if lines else [])


def check_audit(name: str) -> tuple[list[str], list[str]]:
    audit = load_module(ROOT / "factory" / "skill_audit.py", "skill_audit")
    rep = audit.audit_skill(SKILLS / name)
    errs = [f"[{f['severity']}] {f['code']} — {f['file']}:{f['line']}: {f['message']}" for f in rep["findings"]
            if f["severity"] in ("high", "medium")]
    warns = [f"{f['code']} — {f['message']}" for f in rep["findings"] if f["severity"] == "low"]
    return errs, warns


def check_refs(name: str) -> list[str]:
    if not GROUND.exists():
        return []
    r = subprocess.run([sys.executable, str(GROUND), str(SKILLS / name), "--warn"], capture_output=True, text=True,
                       timeout=120, env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(ROOT)})
    return [ln[2:] for ln in r.stdout.splitlines() if ln.startswith("⚠ ") and "odwołania:" not in ln][:5]


# ───────────── ewaluacja na modelu (płatna) ─────────────

def report_path(out_dir: Path, name: str) -> Path:
    """Nowa nazwa raportu dla każdej rundy — runner dopisuje do istniejącego .jsonl, więc ta sama nazwa mieszałaby
    wyniki kilku rund (błąd z 2026-10-03)."""
    out = out_dir / f"{dt.date.today().isoformat()}-bramka-{name}.md"
    n = 2
    while out.exists() or out.with_suffix(".jsonl").exists():
        out = out_dir / f"{dt.date.today().isoformat()}-bramka-{name}-{n}.md"
        n += 1
    return out


def paid_eval(name: str, models: str, budget: float, baseline: bool, yes: bool) -> tuple[bool, dict]:
    out_dir = ROOT / "docs" / "evals" if (ROOT / "docs" / "evals").is_dir() else ROOT / ".claude" / "logs" / "evals"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = report_path(out_dir, name)
    cmd = [sys.executable, str(TESTS / "run_skill_evals.py"), "--skills", name, "--models", models,
           "--budget-usd", str(budget), "--out", str(out)] + (["--baseline"] if baseline else []) + (["--yes"] if yes else [])
    r = subprocess.run(cmd, text=True, timeout=3600)
    jsonl = out.with_suffix(".jsonl")
    res = [json.loads(l) for l in jsonl.read_text(encoding="utf-8").splitlines()] if jsonl.exists() else []
    limit_re = re.compile(r"usage limit|rate limit|spend limit|session limit|limit reached|quota|overloaded", re.I)
    if res and all(limit_re.search(str(x.get("error") or "")) for x in res if not x.get("passed")) \
            and any(not x.get("passed") for x in res):
        if not any(x.get("passed") for x in res):
            for f in (out, jsonl):
                f.unlink(missing_ok=True)
        return False, {"przerwano": "limit użycia lub wydatków — to nie wynik skilla; powtórz, gdy limit się odnowi"}
    summary: dict = {"report": out.relative_to(ROOT).as_posix(), "cost": round(sum(x.get("cost") or 0 for x in res), 2)}
    ok = r.returncode == 0 and bool(res)
    for m in models.split(","):
        mine = [x for x in res if x["model"] == m and not x.get("baseline")]
        if not mine:
            ok = False
            continue
        p = sum(x["passed"] for x in mine)
        summary[m] = f"{p}/{len(mine)}"
        ok = ok and p == len(mine)
        base = [x for x in res if x["model"] == m and x.get("baseline") and x["expect"] == "trigger"]
        if base:
            summary[m + "_bez_skilli"] = f"{sum(x['checks_ok'] for x in base)}/{len(base)} treści"
    return ok, summary


# ───────────── przebieg ─────────────

def gate(name: str, args) -> bool:
    print(f"\n━━ Bramka: {name}")
    if not (SKILLS / name / "SKILL.md").exists():
        print(f"✗ nie ma .claude/skills/{name}/SKILL.md")
        return False
    failed = False

    def step(label: str, errs: list[str], warns: list[str] = (), extra: str = "") -> None:
        nonlocal failed
        mark = "✗" if errs else ("⚠" if warns else "✓")
        print(f"  {mark} {label}{(' — ' + extra) if extra else ''}")
        for e in errs:
            print(f"      ✗ {e}")
        for w in warns:
            print(f"      ⚠ {w}")
        failed = failed or bool(errs)

    step("1. struktura", *check_structure(name))
    se, sw, sc = check_scenarios(name)
    step("2. scenariusze ewaluacji", se, sw)
    if sc:
        he, hw, ratio = check_hint(name, sc)
        step("3. podpowiedź (hook skill_hint)", he, hw, f"trafione {ratio}")
    step("4. regresja podpowiedzi wszystkich skilli", [] if args.fast else check_regression(),
         ["pominięto (--fast)"] if args.fast else [])
    step("5. polszczyzna", *check_polish(name))
    step("6. odwołania w skillu", [], check_refs(name))
    step("7. audyt bezpieczeństwa i zaleceń Anthropic", *check_audit(name))

    reg = read_registry()
    rec = reg.get(name, {})
    fp = fingerprint(name)
    if failed:
        print(f"  ✗ bramka NIE przeszła — popraw i uruchom ponownie (rejestr bez zmian)")
        return False
    paid = None
    if args.model:
        ok, paid = paid_eval(name, args.model, args.budget, args.baseline, args.yes)
        if paid.get("przerwano"):
            step("8. ewaluacja na modelu", [f"przerwana: {paid['przerwano']}"], [])
            print("  ✗ bramka NIE przeszła (ewaluacja przerwana); wynik bezpłatnych sprawdzeń z rejestru bez zmian")
            return False
        step("8. ewaluacja na modelu", [] if ok else [f"nie wszystkie scenariusze zaliczone: {paid}"], [],
             ", ".join(f"{k} {v}" for k, v in paid.items() if k not in ("report",)))
        if not ok:
            print(f"  ✗ bramka NIE przeszła — raport: {paid.get('report')}")
            return False
    new = {"fingerprint": fp, "offline": dt.date.today().isoformat()}
    if paid:
        new["model"] = {**paid, "date": dt.date.today().isoformat()}
    elif rec.get("model") and rec.get("fingerprint") == fp:
        new["model"] = rec["model"]
    elif rec.get("model"):
        new["model_previous"] = {**rec["model"], "uwaga": "dla wcześniejszej wersji skilla"}
    reg[name] = new
    write_registry(reg)
    tail = "" if paid or new.get("model") else " · ewaluacja na modelu: brak (za zgodą człowieka: --model haiku,sonnet)"
    print(f"  ✓ bramka przeszła, zapisano w {REGISTRY.relative_to(ROOT)}{tail}")
    return True


def status(strict: bool = False) -> int:
    reg = read_registry()
    rows = []
    for d in sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md")):
        rec = reg.get(d)
        if not rec:
            state = "brak bramki"
        elif rec.get("fingerprint") != fingerprint(d):
            state = "zmieniony po bramce"
        else:
            state = "ok"
        model = rec.get("model") if rec else None
        rows.append((d, state, ", ".join(f"{k} {v}" for k, v in (model or {}).items() if k in ("haiku", "sonnet", "opus"))))
    for d, s, m in rows:
        print(f"  {'✓' if s == 'ok' else '⚠'} {d:<36} {s:<20} {m}")
    bad = sum(s != "ok" for _, s, _ in rows)
    print(f"{'✓' if not bad else '⚠'} skilli: {len(rows)}, do przejścia przez bramkę: {bad}")
    return 1 if strict and bad else 0


def suggest_phrases(name: str, triggers: list[str], neighbors: list[str], items: list[dict], hint) -> dict:
    """Frazy do metadata.slowa ze słów nietrafionych promptów: rdzenie, których opis skilla nie ma — najpierw te z treści
    SKILL.md (temat skilla), potem najrzadsze (IDF) — z sąsiednim słowem; dopisywane po kolei, aż symulacja hooka podpowie skill. Na koniec: czy pytania sąsiada nadal nie są jego."""
    import math
    target = next(it for it in items if it["name"] == name)
    orig = set(target["head"])
    n = len(items) or 1
    df: dict[str, int] = {}
    for it in items:
        for t in it["head"] | it["body"]:
            df[t] = df.get(t, 0) + 1
    hit = lambda p: name in [it["name"] for _, it in hint.select(p, items)]
    before = sum(hit(p) for p in triggers)
    phrases: list[str] = []
    for p in triggers:
        if hit(p):
            continue
        words = re.findall(r"[a-ząćęłńóśźż0-9][a-ząćęłńóśźż0-9+#\-]*", p.lower())
        keep = [i for i, w in enumerate(words) if len(w) >= 3 and w not in hint.STOP]
        topic = target["head"] | target["body"]
        cands = sorted(dict.fromkeys(s for s in hint.stems(hint.intent(p))
                                     if s not in target["head"] and df.get(s, 0) <= 0.3 * n),   # bez słów ogólnych
                       key=lambda s: (s not in target["body"], -math.log(1 + n / df.get(s, 0.5))))   # temat skilla najpierw
        for st in cands:
            if len(phrases) >= 4:
                break
            i = next((i for i in keep if words[i][:hint.STEM] == st), None)
            if i is None:
                continue
            on_topic = [j for j in keep if words[j][:hint.STEM] in topic]          # sąsiad tylko z tematu skilla
            nxt = next((j for j in on_topic if j > i), None)
            prv = next((j for j in reversed(on_topic) if j < i), None)
            phrase = " ".join(words[i:nxt + 1]) if nxt is not None and nxt - i <= 2 else \
                " ".join(words[prv:i + 1]) if prv is not None and i - prv <= 2 else words[i]
            if phrase in phrases:
                continue
            phrases.append(phrase)
            target["head"] |= set(hint.stems(phrase))
            if hit(p):
                break
    after = sum(hit(p) for p in triggers)
    neighbor_ok = all(not (picks := hint.select(q, items)) or picks[0][1]["name"] != name for q in neighbors)
    target["head"] = orig
    return {"phrases": phrases, "hits_before": before, "hits_after": after, "neighbor_ok": neighbor_ok}


def suggest(name: str, apply: bool) -> int:
    hint = load_module(ROOT / ".claude" / "hooks" / "skill_hint.py", "skill_hint")
    se, _, sc = check_scenarios(name)
    if se:
        print("✗ " + "; ".join(se))
        return 2
    triggers = [s["prompt"] for s in sc.get("trigger", [])]
    res = suggest_phrases(name, triggers, [s["prompt"] for s in sc.get("no", [])], hint.load_index(), hint)
    print(f"Podpowiedź {name}: trafione {res['hits_before']}/{len(triggers)} → po dopisaniu {res['hits_after']}/{len(triggers)}"
          + ("" if res["neighbor_ok"] else " · UWAGA: przy pytaniu sąsiada skill wychodzi na pierwsze miejsce"))
    if not res["phrases"]:
        print("✓ Nic do dopisania.")
        return 0
    line = ", ".join(res["phrases"])
    print(f'Propozycja do metadata.slowa: "{line}"')
    if not apply:
        print(f"Dopisz: python3 factory/skill_gate.py --suggest {name} --apply (potem bramka: python3 factory/skill_gate.py {name})")
        return 0
    md = SKILLS / name / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    m = re.search(r'^  slowa: "(.*)"$', text, re.M)
    if m:
        text = text[:m.start(1)] + (m.group(1) + ", " if m.group(1) else "") + line + text[m.end(1):]
    else:
        text = re.sub(r"^(  katalog: .*\n)", lambda mm: mm.group(1) + f'  slowa: "{line}"\n', text, count=1, flags=re.M)
    md.write_text(text, encoding="utf-8")
    print(f"✓ Dopisano do {md.relative_to(ROOT)} — teraz bramka: python3 factory/skill_gate.py {name}")
    return 0


def hints_all() -> int:
    """Krok 3 bramki dla każdego skilla naraz: scenariusz „trigger”, którego hook nie podpowie, to błąd."""
    misses, narrow, n = [], 0, 0
    for d in sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md")):
        if not (EVALS / f"{d}.json").exists():
            continue
        _, _, sc = check_scenarios(d)
        n += 1
        errs, warns, _ = check_hint(d, sc)
        misses += [f"{d}: {x}" for x in errs + warns if "nie podpowie" in x]
        narrow += sum("nie podpowie" not in x and "ręczny" not in x for x in warns)
    for m in misses:
        print(f"  ✗ {m}")
    print(f"{'✓' if not misses else '✗'} podpowiedzi: {n} skilli, nietrafione scenariusze: {len(misses)}, wąski zapas: {narrow}")
    return 1 if misses else 0


def changed() -> list[str]:
    reg = read_registry()
    return [d for d in sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
            if reg.get(d, {}).get("fingerprint") != fingerprint(d)]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skills", nargs="*")
    ap.add_argument("--changed", action="store_true", help="skille zmienione od ostatniej bramki")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--strict", action="store_true", help="z --status: kod 1, gdy któryś skill nie ma aktualnej bramki (CI)")
    ap.add_argument("--model", default="", help="ewaluacja na modelu (płatna): haiku,sonnet,opus")
    ap.add_argument("--budget", type=float, default=2.0, help="limit kosztu ewaluacji w USD")
    ap.add_argument("--baseline", action="store_true", help="dodatkowo przebieg bez skilli (czy skill coś wnosi)")
    ap.add_argument("--yes", action="store_true", help="bez pytania o zgodę na koszt")
    ap.add_argument("--fast", action="store_true", help="pomiń regresję wszystkich skilli (krok 4)")
    ap.add_argument("--hints", action="store_true",
                    help="trafienia hooka skill_hint dla scenariuszy WSZYSTKICH skilli (nowy skill nie podkrada podpowiedzi)")
    ap.add_argument("--suggest", metavar="SKILL", help="frazy do metadata.slowa z nietrafionych scenariuszy skilla")
    ap.add_argument("--apply", action="store_true", help="z --suggest: dopisz frazy do SKILL.md")
    args = ap.parse_args(argv[1:])
    if args.suggest:
        return suggest(args.suggest, args.apply)
    if args.status:
        return status(args.strict)
    if args.hints:
        return hints_all()
    names = list(args.skills) + (changed() if args.changed else [])
    if not names:
        print("Nic do sprawdzenia." if args.changed else __doc__)
        return 0
    results = {n: gate(n, args) for n in dict.fromkeys(names)}
    bad = [n for n, ok in results.items() if not ok]
    print(f"\n{'✓' if not bad else '✗'} bramka: przeszło {len(results) - len(bad)}/{len(results)}"
          + (f"; nie przeszły: {', '.join(bad)}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
