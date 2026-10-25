#!/usr/bin/env python3
"""Testy próby scenariusza symulacji ES (es_probe.py) z atrapą modelu zamiast `claude -p`: python3 tests/test_es_probe.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir()) / ".claude/skills/ddd-es-simulation"
SCRIPT = SKILL / "scripts" / "es_probe.py"

FAKE = r'''
import json, os, re, sys
sysp = sys.argv[sys.argv.index("--system-prompt") + 1]
prompt = sys.stdin.read()
log = os.environ.get("FAKE_LOG")
if log:
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"system": sysp, "prompt": prompt}) + "\n")
if "Oceniasz PROWADZENIE" in sysp:
    print(json.dumps({"result": "# Debrief\nFacylitator zderzył sprzeczność.", "total_cost_usd": 0.02}))
    sys.exit(0)
pid = re.search(r"\(id: (\w+)\)", prompt).group(1)
now = prompt.split("Facylitator mówi teraz", 1)[-1] if "Facylitator mówi teraz" in prompt else prompt
reply = {"persona": pid, "dialogue": "", "stickies": [], "memory": "", "anecdote_used": None}
if pid == "it":
    print(json.dumps({"result": "nie wiem, co powiedzieć", "total_cost_usd": 0.01}))
    sys.exit(0)
if pid == "recepcja":
    if "Beato" in now:
        reply["dialogue"] = "U nas 18% wizyt przepada. Nikt tego nie liczy."
elif pid == "lekarz" and "zakończona" in now:
    reply["dialogue"] = "Dla mnie wizyta jest zakończona po zamknięciu karty."
    reply["stickies"] = [{"type": "hot_spot", "text": "Kiedy wizyta jest zakończona?", "relates_to": None, "rationale": "spór"}]
elif pid != "hodowca":
    reply["dialogue"] = "Zgadzam się."
    reply["stickies"] = [{"type": "event", "text": "Wizyta umówiona", "relates_to": None, "rationale": "start"}]
print(json.dumps({"result": "```json\n" + json.dumps(reply, ensure_ascii=False) + "\n```", "total_cost_usd": 0.01}))
'''

PROBE = {
    "lines": [
        "Napiszcie na kartkach wszystkie zdarzenia od telefonu klienta do zapłaty.",
        "Beato, ile umówionych wizyt naprawdę się odbywa?",
        "Doktorze Pawle, kiedy dla Pana wizyta jest zakończona?",
        {"invite": "hodowca"},
        "Jolanto, jak wyglądają ceny dla hodowców?",
    ],
    "expect": {
        "hidden": [{"fact": "18% wizyt przepada", "any": ["18"]}, {"fact": "rabat za miot", "any": ["miot"]}],
        "contradictions": [{"name": "kiedy wizyta jest zakończona", "hot_spot_any": ["zakończ"]}],
        "behaviour": [{"round": 1, "persona": "recepcja", "max_sentences": 1, "why": "pytanie do całej sali → milczy"},
                      {"round": 2, "persona": "recepcja", "speaks": True, "why": "pytana po imieniu → odpowiada"}],
    },
}


def run(root: Path, fake: Path, *args: str, log: Path | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root), "ES_PROBE_CMD": json.dumps([sys.executable, str(fake)])}
    if log:
        env["FAKE_LOG"] = str(log)
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env, timeout=120)


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        fake = root / "fake_model.py"
        fake.write_text(FAKE, encoding="utf-8")
        probe = root / "proba.json"
        probe.write_text(json.dumps(PROBE, ensure_ascii=False), encoding="utf-8")
        log = root / "calls.jsonl"

        r = run(root, fake, "--variant", "pelna", "--probe", str(probe), "--id", "p1", log=log)
        sd = root / "docs/training/es-sim/p1"
        rep = sd / "probe-report.md"
        text = rep.read_text(encoding="utf-8") if rep.exists() else ""
        check(r.returncode == 1 and rep.exists(), f"EP-1: niespełnione oczekiwanie → kod 1 i raport: rc={r.returncode} {r.stderr[-400:]}")
        check("✓" in text and "18% wizyt przepada" in text and "✗" in text and "rabat za miot" in text,
              f"EP-2: raport z oczekiwaniami spełnionymi i nie: {text[:900]}")
        check(any("kiedy wizyta jest zakończona" in ln and "✓" in ln for ln in text.splitlines()),
              f"EP-3: sprzeczność zderzona (hot spot): {text[:900]}")
        check(any("pytanie do całej sali" in ln and "✓" in ln for ln in text.splitlines())
              and any("pytana po imieniu" in ln and "✓" in ln for ln in text.splitlines()),
              f"EP-4: zachowania z kart sprawdzone: {text[:900]}")
        state = json.loads((sd / "state.json").read_text(encoding="utf-8")) if (sd / "state.json").exists() else {}
        check(state.get("round") == 4 and len(list((sd / "rounds/01").glob("*.reply.json"))) == 6,
              f"EP-5: 4 rundy, odpowiedzi 6 osób w rundzie 1: {state.get('round')}")
        check("niepoprawny JSON: 4" in text, f"EP-6: brak JSON od jednej osoby w 4 rundach policzony: {text[:900]}")
        check("0,27 USD" in text and "0,27 USD" in r.stdout, f"EP-7: koszt (25 wywołań + coach): {r.stdout[-400:]}")
        calls = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
        part = [c for c in calls if "Oceniasz PROWADZENIE" not in c["system"]]
        check(part and all("Zapisz ten JSON" not in c["prompt"] and '"persona"' in c["prompt"] for c in part),
              "EP-8: uczestnik dostaje kontrakt JSON bez polecenia zapisu pliku (bez narzędzi)")
        check((sd / "debrief.md").exists() and "Debrief" in (sd / "debrief.md").read_text(encoding="utf-8"),
              "EP-9: coach zapisał debrief")
        check(len(r.stdout.splitlines()) <= 40, f"EP-10: zwięzłe wyjście: {len(r.stdout.splitlines())} linii")

        r = run(root, fake, "--variant", "pelna", "--probe", str(probe), "--id", "p2", "--budget-usd", "0.05", "--coach", "none")
        st = json.loads((root / "docs/training/es-sim/p2/state.json").read_text(encoding="utf-8"))
        check(r.returncode == 3 and "budżet" in r.stdout.lower() and st.get("round") == 1
              and not (root / "docs/training/es-sim/p2/debrief.md").exists(),
              f"EP-11: przekroczony budżet zatrzymuje próbę po rundzie: rc={r.returncode} {r.stdout[-300:]}")

        r = run(root, fake, "--variant", "pelna", "--probe", str(root / "brak.json"), "--id", "p3")
        check(r.returncode == 2, f"EP-12: brak pliku próby → 2: {r.returncode}")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów es_probe")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
