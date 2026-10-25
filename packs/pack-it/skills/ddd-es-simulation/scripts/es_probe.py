#!/usr/bin/env python3
"""
Próba scenariusza symulacji ES bez człowieka i bez gospodarza: gotowe wypowiedzi facylitatora z pliku próby, rundy
przez es_sim.py, uczestnicy jako osobne wywołania modelu bez narzędzi (`claude -p`), na końcu coach. Sprawdza, czy
scenariusz działa: czy wiedza ukryta wychodzi, czy celowe sprzeczności dają hot spoty, czy karty osób zachowują się
zgodnie z opisem, ile odpowiedzi to niepoprawny JSON. Płatne — uruchamiaj tylko za zgodą człowieka.

  es_probe.py --variant pelna|oszczedna [--scenario weterynaria] [--probe <proba.json>] [--id <id>]
              [--coach full|light|none] [--budget-usd 2.5]

Plik próby (domyślnie scenarios/<scenariusz>/proba.json):
  {"lines": ["<wypowiedź facylitatora>", {"invite": "<id osoby>"}, …],
   "expect": {"hidden": [{"fact": "…", "any": ["słowo", …]}],
              "contradictions": [{"name": "…", "hot_spot_any": ["słowo", …]}],
              "behaviour": [{"round": 1, "persona": "<id>", "speaks": true | "max_sentences": 1, "why": "…",
                             "skip_variants": [<nr wariantu dnia od 0>, …]}]}}

Model: zmienna ES_PROBE_CMD (lista JSON, np. atrapa w testach) zastępuje `claude -p` bez narzędzi i bez MCP; skrypt
dokłada `--model` i `--system-prompt`. Wynik: docs/training/es-sim/<id>/probe-report.md (+ debrief.md coacha).
Kod wyjścia: 0 — wszystkie oczekiwania spełnione, 1 — nie wszystkie, 2 — złe wywołanie, 3 — przekroczony budżet.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ES_SIM = HERE / "es_sim.py"
DEFAULT_CMD = ["claude", "-p", "--tools", "", "--strict-mcp-config", "--no-session-persistence", "--output-format", "json"]
MODELS = {"pelna": "sonnet", "oszczedna": "haiku"}
PARTICIPANT_SYS = ("Jesteś uczestnikiem symulacji warsztatu Event Storming. Zagraj osobę (albo osoby) opisaną w wiadomości "
                   "dokładnie według karty i zasad. Odpowiedz wyłącznie blokiem JSON w podanym kształcie. Nie komentuj symulacji.")
COACH_SYS = ("Oceniasz PROWADZENIE sesji, nie treść domenową. Wejście: transkrypcja, statystyki (JSON ze skryptu), brief "
             "scenariusza (celowe sprzeczności, oczekiwane zdarzenia przełomowe, kto trenuje jaki anty-wzorzec). Tryb light: tylko "
             "dominacja, milczący uczestnicy, niesprawdzony język. Tryb full: 10 anty-wzorców facylitacji, każdy "
             "zielony/żółty/czerwony z dowodem (runda, cytat). Uczestnicy reagują na echo z opóźnieniem jednej rundy. Nie zaczynaj "
             "od pochwał. Format: 3 zdania podsumowania · tabela anty-wzorców · 3 mocne momenty i 3 do pracy · czy facylitator "
             "zderzył celowe sprzeczności · jeden cytat. Dodatkowo, bo to próba scenariusza: czy karty osób i sprzeczności "
             "zadziałały jak w briefie. Zwróć sam debrief w Markdownie.")
WRITE_FILE = re.compile(r"\n*Zapisz (?:ten JSON|tablicę) do pliku `[^`]+` i odpowiedz(?: jednym słowem)?: ok\.\s*$")


def sim(env: dict, *args: str) -> str:
    r = subprocess.run([sys.executable, str(ES_SIM), *args], capture_output=True, text=True, env=env)
    if r.returncode:
        sys.exit(f"✗ es_sim.py {args[0]}: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def call_model(system: str, prompt: str, model: str) -> tuple[str, float]:
    base = json.loads(os.environ["ES_PROBE_CMD"]) if os.environ.get("ES_PROBE_CMD") else DEFAULT_CMD
    with tempfile.TemporaryDirectory() as cwd:   # poza projektem: bez hooków i plików projektu
        r = subprocess.run([*base, "--model", model, "--system-prompt", system], input=prompt, capture_output=True,
                           text=True, cwd=cwd, timeout=600)
    try:
        out = json.loads(r.stdout)
        return str(out.get("result") or ""), float(out.get("total_cost_usd") or 0)
    except (ValueError, TypeError):
        return r.stdout, 0.0


def sentences(text: str) -> int:
    return len([s for s in re.split(r"[.!?…]+", text or "") if s.strip()])


def usd(x: float) -> str:
    return f"{x:.2f}".replace(".", ",") + " USD"


def evaluate(st: dict, transcript: str, expect: dict) -> list[tuple[bool | None, str, str]]:
    low = transcript.lower()
    hs = " ".join(h["text"] for h in st.get("hot_spots", [])).lower()
    out = []
    for h in expect.get("hidden", []):
        ok = any(k.lower() in low for k in h["any"])
        out.append((ok, "wiedza ukryta", h["fact"]))
    for c in expect.get("contradictions", []):
        ok = any(k.lower() in hs for k in c["hot_spot_any"])
        out.append((ok, "sprzeczność (hot spot)", c["name"]))
    rounds = {r["n"]: r for r in st.get("rounds", [])}
    for b in expect.get("behaviour", []):
        var = st.get("day_variant", {}).get(b["persona"])
        what = f"runda {b['round']}, {b['persona']} (wariant dnia {'—' if var is None else var + 1}): {b.get('why', '')}"
        if var in b.get("skip_variants", []):   # wariant dnia z karty zmienia temperament — zachowanie może być inne
            out.append((None, "karta osoby", what + " — pominięte przy tym wariancie dnia"))
            continue
        d = (rounds.get(b["round"], {}).get("replies", {}).get(b["persona"], {}) or {}).get("dialogue", "")
        ok = bool(d.strip()) if b.get("speaks") else sentences(d) <= b.get("max_sentences", 0)
        out.append((ok, "karta osoby", what))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["pelna", "oszczedna"], required=True)
    ap.add_argument("--scenario", default="weterynaria")
    ap.add_argument("--probe")
    ap.add_argument("--id")
    ap.add_argument("--coach", choices=["full", "light", "none"], default="full")
    ap.add_argument("--budget-usd", type=float, default=2.5)
    a = ap.parse_args()
    probe_path = Path(a.probe) if a.probe else SKILL / "scenarios" / a.scenario / "proba.json"
    try:
        probe = json.loads(probe_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"✗ plik próby: {e}", file=sys.stderr)
        return 2
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    init = ["init", "--variant", a.variant, "--scenario", a.scenario] + (["--id", a.id] if a.id else [])
    sid = json.loads(sim(env, *init).splitlines()[0])["id"]
    sd = root / "docs" / "training" / "es-sim" / sid
    model, cost, calls, stopped = MODELS[a.variant], 0.0, 0, False
    for line in probe.get("lines", []):
        if isinstance(line, dict) and line.get("invite"):
            sim(env, "invite", "--id", sid, "--persona", line["invite"])
            continue
        plan = json.loads(sim(env, "round-begin", "--id", sid, "--text", str(line)))

        def one(c):
            pf = root / c["prompt_file"]
            prompt = WRITE_FILE.sub("\n\nOdpowiedz wyłącznie tym blokiem JSON.", pf.read_text(encoding="utf-8"))
            text, usd_ = call_model(PARTICIPANT_SYS, prompt, model)
            (pf.parent / pf.name.replace(".prompt.md", ".reply.json")).write_text(text, encoding="utf-8")
            return usd_

        with ThreadPoolExecutor(max_workers=8) as ex:
            spent = list(ex.map(one, plan["calls"]))
        cost, calls = cost + sum(spent), calls + len(spent)
        sim(env, "round-end", "--id", sid)
        if cost > a.budget_usd:
            stopped = True
            break
    st = json.loads((sd / "state.json").read_text(encoding="utf-8"))
    transcript = (sd / "transcript.md").read_text(encoding="utf-8")
    if a.coach != "none" and not stopped:
        stats = sim(env, "stats", "--id", sid, "--json")
        brief = (SKILL / "scenarios" / st["scenario"] / "brief.md").read_text(encoding="utf-8")
        debrief, c_usd = call_model(COACH_SYS, f"Tryb: {a.coach} (końcowy).\n\n## Brief scenariusza\n{brief}\n\n"
                                               f"## Statystyki\n{stats}\n\n## Transkrypcja\n{transcript}", "sonnet")
        cost, calls = cost + c_usd, calls + 1
        (sd / "debrief.md").write_text(debrief, encoding="utf-8")
    checks = evaluate(st, transcript, probe.get("expect", {}))
    bad_json = transcript.count("brak lub niepoprawny JSON")
    silent = [p for p in st["present"]
              if not any((r.get("replies", {}).get(p, {}) or {}).get("dialogue", "").strip() for r in st["rounds"])]
    counted = [ok for ok, _, _ in checks if ok is not None]
    met = sum(counted)
    L = [f"# Próba scenariusza „{st['scenario']}” — {sid}", "",
         f"Wariant {a.variant} (model uczestników: {model}), rundy {st['round']}, wywołania modelu {calls}, "
         f"koszt {usd(cost)}{' — przerwana: przekroczony budżet' if stopped else ''}.",
         f"Zdarzenia {len(st['events'])}, hot spoty {len(st['hot_spots'])}, odrzucone kartki {len(st['rejected'])}, "
         f"niepoprawny JSON: {bad_json}, osoby bez ani jednej wypowiedzi: {', '.join(silent) or '—'}.", "",
         f"## Oczekiwania ({met}/{len(counted)})", "| | Rodzaj | Oczekiwanie |", "|---|---|---|"]
    L += [f"| {'—' if ok is None else '✓' if ok else '✗'} | {kind} | {what} |" for ok, kind, what in checks]
    L += ["", "Transkrypcja: `transcript.md` · tablica: `board.md`" + (" · debrief coacha: `debrief.md`" if (sd / "debrief.md").exists() else "")]
    (sd / "probe-report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:4] + [ln for ln in L[6:] if ln.startswith("| ✗")] + [f"Raport: {sd / 'probe-report.md'}"]))
    if stopped:
        print(f"⚠ budżet {usd(a.budget_usd)} przekroczony — próba przerwana po rundzie {st['round']}")
        return 3
    return 0 if met == len(counted) else 1


if __name__ == "__main__":
    raise SystemExit(main())
