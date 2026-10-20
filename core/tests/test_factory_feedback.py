#!/usr/bin/env python3
"""Testy drogi powrotnej do fabryki: factory_feedback.py (zgłoszenie z projektu) i feedback_report.py (zbiorczy raport)."""
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / ".claude" / "skills" / "core-agent-retro" / "scripts" / "factory_feedback.py").is_file())
FEEDBACK = ROOT / ".claude" / "skills" / "core-agent-retro" / "scripts" / "factory_feedback.py"
REPORT = ROOT / "factory" / "feedback_report.py"


def project(base: Path, source: str | None = "https://github.com/dbqm45/claude-team-factory.git") -> Path:
    p = base / "app"
    for s in ("fe-css", "moj-skill"):
        (p / ".claude" / "skills" / s).mkdir(parents=True)
        (p / ".claude" / "skills" / s / "SKILL.md").write_text(f"---\nname: {s}\n---\n", encoding="utf-8")
    man = {"version": "2.23.0", "files": {".claude/skills/fe-css/SKILL.md": "x",
                                          ".claude/agents/_generated/ola-frontend.md": "x"}}
    if source:
        man["source"] = source
    (p / ".claude" / "factory-manifest.json").write_text(json.dumps(man), encoding="utf-8")
    retro = p / "docs" / "project" / "archive" / "retro"
    retro.mkdir(parents=True)
    (retro / "20261017-retro.json").write_text(json.dumps({
        "date": "2026-10-17", "window": {"since": "2026-10-03", "until": "2026-10-17"},
        "evidence": [
            {"id": "E-1", "kind": "cost", "key": "cost:main", "text": "main: 5000 tokenów"},
            {"id": "E-2", "kind": "hint", "key": "hint-missed:fe-css", "n": 3, "text": "fe-css: użyty bez podpowiedzi"},
            {"id": "E-3", "kind": "hint", "key": "hint-missed:moj-skill", "n": 2, "text": "moj-skill"},
            {"id": "E-4", "kind": "tier", "key": "tier:ola-frontend:za niski", "n": 2, "text": "ola-frontend"},
            {"id": "E-5", "kind": "tier", "key": "tier:obcy-agent:za niski", "n": 4, "text": "obcy"},
            {"id": "E-6", "kind": "trap", "key": "trap:vitest-trybie-watch", "text": "Vitest w /home/x/secret/app.ts"},
            {"id": "E-7", "kind": "hint", "key": "hint-ignored:fe-css", "n": 3, "text": "fe-css szum"}],
        "decisions": {"hint-missed:fe-css": "tak", "hint-ignored:fe-css": "nie"}}), encoding="utf-8")
    return p


def run(script: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, timeout=60,
                          env={**os.environ, **(env or {})})


def link_body(out: str) -> str:
    url = next((w for w in out.split() if w.startswith("https://github.com/") and "/issues/new?" in w), "")
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("body", [""])[0]


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        p = project(base)
        r = run(FEEDBACK, "--root", str(p))
        body = link_body(r.stdout)
        check(r.returncode == 0 and "https://github.com/dbqm45/claude-team-factory/issues/new?" in r.stdout
              and "hint-missed:fe-css" in body and "tier:ola-frontend:za niski" in body and "2.23.0" in body,
              f"FF-1: domyślnie link „nowe zgłoszenie” z gotową treścią: {r.stdout[-500:]}{r.stderr[-300:]}")
        check(not any(x in body for x in ("moj-skill", "obcy-agent", "vitest", "/home/x", "cost:main", "hint-ignored")),
              f"FF-2: tylko sygnały o skillach i agentach fabryki, bez pułapek, ścieżek, kosztów i odrzuconych: {body}")
        r = run(FEEDBACK, "--root", str(p), "--json")
        try:
            out = json.loads(r.stdout)
            payload = json.loads(out["body"].split("```json\n", 1)[1].split("\n```", 1)[0])
        except (ValueError, KeyError, IndexError):
            out, payload = {}, {}
        check(payload.get("factory_feedback") == 1 and payload.get("factory_version") == "2.23.0"
              and len(payload.get("project", "")) == 10
              and {s["key"]: s["n"] for s in payload.get("signals", [])} == {"hint-missed:fe-css": 3,
                                                                           "tier:ola-frontend:za niski": 2},
              f"FF-3: treść ma blok JSON do zbiorczego raportu (anonimowy projekt, wersja, sygnały z liczbami): {payload}")

        r = run(FEEDBACK, "--root", str(p), "--json", "--item", "skill:fe-css: brak przykładu siatki formularza")
        items = json.loads(r.stdout or "{}").get("payload", {}).get("items", [])
        check(r.returncode == 0 and items == [{"target": "skill:fe-css", "text": "brak przykładu siatki formularza"}],
              f"FF-4: własna uwaga o skillu fabryki dołączona: {items} {r.stderr}")
        for bad, why in (("skill:fe-css: błąd w /home/x/src/app.ts", "ścieżka"),
                         ("skill:fe-css: zobacz https://intranet.firma.pl/x", "adres"),
                         ("skill:fe-css: pisz do jan@firma.pl", "e-mail"),
                         ("skill:moj-skill: coś", "spoza fabryki")):
            r = run(FEEDBACK, "--root", str(p), "--item", bad)
            check(r.returncode == 2, f"FF-5 ({why}): uwaga z danymi projektu odrzucona: {r.stdout}{r.stderr}")

        q = project(base / "bez-zrodla", source="/home/x/fabryka")
        r = run(FEEDBACK, "--root", str(q))
        check(r.returncode == 2 and "--repo" in r.stdout + r.stderr, f"FF-6: źródło nie na GitHubie → wymagane --repo: {r.stdout}")
        r = run(FEEDBACK, "--root", str(q), "--repo", "ja/fabryka")
        check(r.returncode == 0 and "https://github.com/ja/fabryka/issues/new?" in r.stdout, f"FF-6b: --repo: {r.stdout[-300:]}")

        fake = base / "bin" / "gh"
        fake.parent.mkdir()
        log = base / "gh.log"
        fake.write_text(f"#!/bin/sh\necho \"$@\" > {log}\ncat > {log}.body\n"
                        "echo https://github.com/dbqm45/claude-team-factory/issues/99\n")
        fake.chmod(0o755)
        r = run(FEEDBACK, "--root", str(p), "--gh", env={"CTF_GH": str(fake)})
        check(r.returncode == 0 and "gh issue create" in r.stdout and not log.exists(),
              f"FF-7: --gh bez --yes pokazuje plan i nic nie wysyła: {r.stdout[-300:]}")
        r = run(FEEDBACK, "--root", str(p), "--gh", "--yes", env={"CTF_GH": str(fake)})
        args = log.read_text() if log.exists() else ""
        saved = json.loads((p / "docs/project/archive/retro/20261017-retro.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and "--repo dbqm45/claude-team-factory" in args and "issue create" in args
              and "hint-missed:fe-css" in (Path(str(log) + ".body").read_text() if log.exists() else "")
              and set(saved.get("reported", {})) == {"hint-missed:fe-css", "tier:ola-frontend:za niski"},
              f"FF-8: --gh --yes zakłada zgłoszenie i zapamiętuje zgłoszone klucze: {args} {saved.get('reported')} {r.stderr}")
        r = run(FEEDBACK, "--root", str(p))
        check(r.returncode == 0 and "issues/new?" not in r.stdout and "nic nowego" in r.stdout,
              f"FF-9: drugi raz bez duplikatów: {r.stdout[-300:]}")
        r = run(FEEDBACK, "--root", str(p), "--force")
        check("issues/new?" in r.stdout, "FF-9b: --force zgłasza ponownie")
        r = run(FEEDBACK, "--root", str(p), "--gh", "--yes", "--force", env={"CTF_GH": str(base / "brak-gh")})
        check(r.returncode == 1 and "issues/new?" in r.stdout, f"FF-10: brak gh → link zamiast wysyłki, kod 1: {r.stdout[-300:]}")

        # Zbiorczy raport w repozytorium fabryki: zgłoszenia to niezaufane dane — tylko walidowany blok JSON.
        def issue(n: int, proj: str, signals: list) -> dict:
            pl = {"factory_feedback": 1, "project": proj, "factory_version": "2.23.0", "signals": signals}
            return {"number": n, "body": f"Opis\n```json\n{json.dumps(pl)}\n```\n"}
        issues = [issue(1, "aaaaaaaaaa", [{"key": "hint-missed:fe-css", "n": 3}]),
                  issue(2, "bbbbbbbbbb", [{"key": "hint-missed:fe-css", "n": 2},
                                          {"key": "tier:ola-frontend:za niski", "n": 2}]),
                  issue(3, "aaaaaaaaaa", [{"key": "hint-missed:fe-css", "n": 1}]),
                  {"number": 4, "body": "```json\n{zepsute\n```"},
                  issue(5, "cccccccccc", [{"key": "hint-missed:$(rm -rf ~)", "n": 9}])]
        f = base / "issues.json"
        f.write_text(json.dumps(issues), encoding="utf-8")
        r = run(REPORT, "--from-file", str(f), "--json")
        try:
            rep = json.loads(r.stdout)
        except ValueError:
            rep = {}
        keys = {k["key"]: k for k in rep.get("keys", [])}
        check(r.returncode == 0 and keys.get("hint-missed:fe-css", {}).get("projects") == 2
              and keys["hint-missed:fe-css"].get("candidate") is True and keys["hint-missed:fe-css"].get("issues") == [1, 2, 3]
              and keys.get("tier:ola-frontend:za niski", {}).get("candidate") is False
              and rep.get("ignored") == 2 and not any("rm -rf" in k for k in keys),
              f"FF-11: klucze z ≥2 projektów to kandydaci; zepsute i podejrzane wpisy pominięte: {rep} {r.stderr}")
        r = run(REPORT, "--from-file", str(f))
        check(r.returncode == 0 and "kandydat" in r.stdout and "#1" in r.stdout, f"FF-12: raport markdown: {r.stdout}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów factory_feedback")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
