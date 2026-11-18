#!/usr/bin/env python3
"""Tests of the ES simulation scenario probe (es_probe.py) with a model stub instead of `claude -p`: python3 tests/test_es_probe.py"""
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
if "You assess how the session was RUN" in sysp:
    print(json.dumps({"result": "# Debrief\nFacylitator zderzył sprzeczność.", "total_cost_usd": 0.02}))
    sys.exit(0)
pid = re.search(r"\(id: (\w+)\)", prompt).group(1)
now = prompt.split("The facilitator says now", 1)[-1] if "The facilitator says now" in prompt else prompt
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
                      {"round": 2, "persona": "recepcja", "speaks": True, "why": "pytana po imieniu → odpowiada"},
                      {"round": 1, "persona": "hodowca", "speaks": True, "why": "wariant dnia wyłączony",
                       "skip_variants": [0, 1, 2, 3, 4, 5, 6, 7]}],
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
        probe = root / "trial.json"
        probe.write_text(json.dumps(PROBE, ensure_ascii=False), encoding="utf-8")
        log = root / "calls.jsonl"

        r = run(root, fake, "--variant", "pelna", "--probe", str(probe), "--id", "p1", log=log)
        sd = root / "docs/training/es-sim/p1"
        rep = sd / "probe-report.md"
        text = rep.read_text(encoding="utf-8") if rep.exists() else ""
        check(r.returncode == 1 and rep.exists(), f"EP-1: an unmet expectation → code 1 and a report: rc={r.returncode} {r.stderr[-400:]}")
        check("✓" in text and "18% wizyt przepada" in text and "✗" in text and "rabat za miot" in text,
              f"EP-2: a report with met and unmet expectations: {text[:900]}")
        check(any("kiedy wizyta jest zakończona" in ln and "✓" in ln for ln in text.splitlines()),
              f"EP-3: contradiction confronted (hot spot): {text[:900]}")
        check(any("pytanie do całej sali" in ln and "✓" in ln for ln in text.splitlines())
              and any("pytana po imieniu" in ln and "✓" in ln for ln in text.splitlines()),
              f"EP-4: zachowania z kart sprawdzone: {text[:900]}")
        state = json.loads((sd / "state.json").read_text(encoding="utf-8")) if (sd / "state.json").exists() else {}
        check(state.get("round") == 4 and len(list((sd / "rounds/01").glob("*.reply.json"))) == 6,
              f"EP-5: 4 rounds, replies of 6 people in round 1: {state.get('round')}")
        check(any("wariant dnia wyłączony" in ln and "skipped" in ln and "✗" not in ln for ln in text.splitlines())
              and "## Expectations (4/5)" in text,
              f"EP-13: the expectation skipped for the given day variant, does not count towards the result: {text[:900]}")
        check("invalid JSON: 4" in text, f"EP-6: missing JSON from one person counted over 4 rounds: {text[:900]}")
        check("0.27 USD" in text and "0.27 USD" in r.stdout, f"EP-7: cost (25 calls + coach): {r.stdout[-400:]}")
        calls = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
        part = [c for c in calls if "You assess how the session was RUN" not in c["system"]]
        check(part and all("Save this JSON" not in c["prompt"] and '"persona"' in c["prompt"] for c in part),
              "EP-8: the participant gets the JSON contract without a file-write command (without tools)")
        check((sd / "debrief.md").exists() and "Debrief" in (sd / "debrief.md").read_text(encoding="utf-8"),
              "EP-9: the coach saved the debrief")
        check(len(r.stdout.splitlines()) <= 40, f"EP-10: concise output: {len(r.stdout.splitlines())} lines")

        r = run(root, fake, "--variant", "pelna", "--probe", str(probe), "--id", "p2", "--budget-usd", "0.05", "--coach", "none")
        st = json.loads((root / "docs/training/es-sim/p2/state.json").read_text(encoding="utf-8"))
        check(r.returncode == 3 and "budget" in r.stdout.lower() and st.get("round") == 1
              and not (root / "docs/training/es-sim/p2/debrief.md").exists(),
              f"EP-11: an exceeded budget stops the probe after the round: rc={r.returncode} {r.stdout[-300:]}")

        r = run(root, fake, "--variant", "pelna", "--probe", str(root / "brak.json"), "--id", "p3")
        check(r.returncode == 2, f"EP-12: missing probe file → 2: {r.returncode}")

    # backward compatibility (pl: sprzed 14.x): the Polish write command in the prompt and the Polish bad-JSON message
    import importlib.util
    spec = importlib.util.spec_from_file_location("es_probe", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    old = "kontrakt\n\nZapisz ten JSON do pliku `docs/x/a.reply.json` i odpowiedz jednym słowem: ok.\n"
    new = "kontrakt\n\nSave this JSON to the file `docs/x/a.reply.json` and reply with one word: ok.\n"
    check(mod.WRITE_FILE.sub("|", old) == "kontrakt|" and mod.WRITE_FILE.sub("|", new) == "kontrakt|",
          "EP-14: the file-write command removed from the prompt in Polish and in English")
    tr = "> problem: a: brak lub niepoprawny JSON — x\n> problem: b: missing or invalid JSON; y\n"
    check(sum(tr.count(m) for m in mod.BAD_JSON) == 2, "EP-15: bad JSON counted in the old and the new transcript")

    for f in fails:
        print("✗", f)
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of es_probe")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
