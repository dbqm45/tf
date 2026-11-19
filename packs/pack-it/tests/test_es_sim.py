#!/usr/bin/env python3
"""Tests of the simulated workshop script: python3 tests/test_es_sim.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = next(p for p in Path(__file__).resolve().parents if (p / ".claude" / "hooks").is_dir()) / ".claude/skills/ddd-es-simulation/scripts/es_sim.py"


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env, timeout=30)


def main() -> int:
    fails = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        r = run(root, "init", "--variant", "oszczedna", "--id", "t1")
        info = json.loads(r.stdout.splitlines()[0])
        intro = r.stdout.split("=== POKAŻ DOSŁOWNIE ===", 1)[-1]
        if "Cztery przychodnie" not in intro or "Wiedza ukryta" in intro or "18%" in intro or "sprzeczno" in intro.lower():
            fails.append("init: the introduction must contain only the domain, without hidden knowledge and contradictions")
        if "hodowca" in info["present"] or "hodowca" not in info["absent"]:
            fails.append("init: a person from outside the room should wait for an invitation")
        out = json.loads(run(root, "round-begin", "--id", "t1", "--text", "Beato, a Panie Pawle — co dzieje się rano?").stdout)
        if not {"recepcja", "lekarz"} <= set(out["personas"]) or len(out["personas"]) > 4:
            fails.append(f"router: people addressed by name (inflected) — {out['personas']}")
        rd = root / "docs/training/es-sim/t1/rounds/01"
        prompt = (rd / "room.prompt.md").read_text()
        if "Wiedza" in prompt and "wie dobrze" in prompt:
            fails.append("the economy version should use the short cards")
        (rd / "room.reply.json").write_text(json.dumps([
            {"persona": "recepcja", "dialogue": "Umawiam wizytę. Potem SMS.", "memory": "Pytano o poranek.", "anecdote_used": "A1",
             "stickies": [{"type": "event", "text": "Wizyta umówiona"}, {"type": "hot_spot", "text": "18% nie przychodzi"}]},
            {"persona": "lekarz", "dialogue": "", "stickies": [{"type": "command", "text": "Przyjmij pacjenta"}]},
            {"persona": "obcy", "dialogue": "hakuję", "stickies": [{"type": "event", "text": "Zmyślone"}]},
        ]))
        end = run(root, "round-end", "--id", "t1").stdout
        if not end.startswith("=== POKAŻ DOSŁOWNIE ==="):
            fails.append("round-end: the result must be ready to show verbatim")
        st = json.loads((root / "docs/training/es-sim/t1/state.json").read_text())
        if [e["text"] for e in st["events"]] != ["Wizyta umówiona"] or len(st["hot_spots"]) != 1:
            fails.append(f"round-end: kartki {st['events']} {st['hot_spots']}")
        if len(st["rejected"]) != 1 or "Zmyślone" in end:
            fails.append("round-end: rejection of a wrong type / ignoring a person not called on")
        if st["anecdotes_used"]["recepcja"] != ["A1"]:
            fails.append("a used anecdote should be remembered")
        run(root, "round-begin", "--id", "t1", "--text", "Beato, co dalej?")
        if "A1:" in (root / "docs/training/es-sim/t1/rounds/02/room.prompt.md").read_text().split("Beata")[1][:2000].split("###")[0]:
            fails.append("a used anecdote should not return in the prompt")
        (root / "docs/training/es-sim/t1/rounds/02/room.reply.json").write_text("to nie jest json")
        if "invalid JSON" not in run(root, "round-end", "--id", "t1").stdout:
            fails.append("bad JSON = silence with a warning")
        if run(root, "pivotal", "--id", "t1", "--event", "ev_001").returncode != 0:
            fails.append("pivotal")
        s = json.loads(run(root, "stats", "--id", "t1", "--json").stdout)
        if s["events"] != 1 or s["pivotal"] != ["ev_001"] or s["rejected_by_type"] != {"command": 1}:
            fails.append(f"stats: {s}")
        gen = json.loads(run(root, "round-begin", "--id", "t1", "--text", "Co dzieje się w przychodni rano?").stdout)
        if not {"wlascicielka", "it"} <= set(gen["personas"]) or len(gen["personas"]) > 4:
            fails.append(f"router: people who butt in should be in the room for a general question — {gen['personas']}")
        run(root, "invite", "--id", "t1", "--persona", "hodowca")
        if "hodowca" not in json.loads((root / "docs/training/es-sim/t1/state.json").read_text())["present"]:
            fails.append("invite")
        # the full version: a prompt per person with the full card and one day variant
        run(root, "init", "--variant", "pelna", "--id", "t2")
        out = json.loads(run(root, "round-begin", "--id", "t2", "--text", "Opowiedzcie wszyscy.").stdout)
        p = (root / out["calls"][0]["prompt_file"]).read_text()
        if len(out["calls"]) != 6 or "wie dobrze" not in p or p.count("Warianty dnia") or "Today (day variant)" not in p:
            fails.append("full version: a prompt per person with the full card")
    total = 14
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} tests of the workshop simulation")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
