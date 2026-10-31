#!/usr/bin/env python3
"""Testy faz uruchamianych przez pdi (tryb mode-pdi, skill pdi-decisions, scripts/phase_run.py): mapa faz, prompt,
uruchomienie persony bez interakcji (podstawiony `claude`), prośba o bramkę do pdi (podpis sprawdzony lokalnym
serwerem HTTP) i instalacja szablonu workflow. python3 .claude/tests/test_phase_run.py"""
import hashlib
import hmac
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REL = Path(".claude") / "skills" / "pdi-decisions" / "scripts" / "phase_run.py"
DREC = Path(".claude") / "skills" / "pdi-decisions" / "scripts" / "decision_record.py"
ROOT = next((p for p in Path(__file__).resolve().parents if (p / REL).is_file()), None)
SCRIPT = ROOT / REL if ROOT else None
FIX = Path(__file__).resolve().parent / "fixtures" / "pdi-contract"
SECRET = "sekret-tf"
KEY_RE = r"^[A-Z][A-Z0-9]+-[0-9]+$"

FAKE_CLAUDE = """import json, os, sys
open(os.environ["FAKE_LOG"], "a").write(json.dumps(sys.argv[1:]) + "\\n")
if os.environ.get("FAKE_EXIT"):
    sys.exit(int(os.environ["FAKE_EXIT"]))
print(json.dumps({"type": "result", "subtype": os.environ.get("FAKE_SUBTYPE", "success"),
                  "is_error": bool(os.environ.get("FAKE_ERROR")), "total_cost_usd": 0.42, "result": "gotowe"}))
"""


def run(args, cwd, **env):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **env})


def jl(r):
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


class Catch(BaseHTTPRequestHandler):
    got: list = []
    status = 202

    def do_POST(self):  # noqa: N802
        body = self.rfile.read(int(self.headers["content-length"]))
        Catch.got.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "body": body})
        self.send_response(Catch.status)
        self.end_headers()
        self.wfile.write(b'{"status": "created"}')

    def log_message(self, *a):
        pass


def project(tmp: Path) -> Path:
    """Projekt z dziennikiem zmiany CHG-12 i personami ewa, tomasz, talos."""
    subprocess.run([sys.executable, str(ROOT / DREC), "change", "new", "CHG-12"], cwd=tmp, capture_output=True,
                   check=True)
    for p in ("ewa", "tomasz", "talos"):
        f = tmp / ".claude" / "agents" / "_generated" / p / f"{p}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"---\nname: {p}\n---\n", encoding="utf-8")
    return tmp


def TEMPLATE_BODY() -> str:  # noqa: N802
    f = SCRIPT.parent.parent / "templates" / "sdlc-phase.yml"
    return f.read_text(encoding="utf-8") if f.is_file() else ""


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    if SCRIPT is None:
        print(f"✗ brak skryptu {REL}")
        return 1

    with tempfile.TemporaryDirectory() as t:
        repo = project(Path(t))

        # --- prompt i mapa faz ---
        r = run(["prompt", "--change", "CHG-12", "--phase", "requirements"], repo)
        p = jl(r) or {}
        check(r.returncode == 0 and (p.get("persona"), p.get("gate"), p.get("artifact")) == (
            "ewa", "B2", "docs/project/changes/CHG-12/requirements.md"), f"R-1: faza → persona, bramka, artefakt: {r.stdout}{r.stderr}")
        text = p.get("prompt", "")
        check("CHG-12" in text and "requirements.md" in text and "docs/project/changes/CHG-12" in text
              and "bez interakcji" in text and "Pytania do bramki" in text and "decision_record.py check" in text,
              f"R-2: prompt mówi, co i gdzie zrobić, bez pytań do człowieka: {text[:500]}")
        check("## Bramka" in text and "wiążące" in text and "rozstrzygnięte" in text,
              f"R-2a: decyzje z bramek w decisions.md są wiążące, a odpowiedziane pytania rozstrzygnięte: {text[:900]}")
        r = run(["prompt", "--change", "CHG-12", "--phase", "architecture", "--rework", "--gate", "B3",
                 "--decision", "DEC-41"], repo)
        text = (jl(r) or {}).get("prompt", "")
        check("DEC-41" in text and "B3" in text and "poprawk" in text and "decisions.md" in text,
              f"R-3: ponowna praca wskazuje decyzję i decisions.md: {text[:500]}")
        r = run(["prompt", "--change", "CHG-12", "--phase", "delivery", "--budget-usd", "5"], repo)
        p = jl(r) or {}
        check(p.get("persona") == "talos" and p.get("gate") is None and "/talos-story-run" in p.get("prompt", "")
              and "--auto" in p.get("prompt", "") and "--budget 5" in p.get("prompt", ""),
              f"R-4: delivery przez Talosa, bez bramki po fazie: {r.stdout}")
        r = run(["prompt", "--change", "CHG-12", "--phase", "intent"], repo)
        check(r.returncode != 0 and "maja" in r.stdout and "pdi-phases.json" in r.stdout,
              f"R-5: brak persony → błąd z podpowiedzią: {r.stdout}{r.stderr}")
        (repo / ".claude" / "pdi-phases.json").write_text('{"intent": {"persona": "ewa"}}', encoding="utf-8")
        r = run(["prompt", "--change", "CHG-12", "--phase", "intent"], repo)
        check((jl(r) or {}).get("persona") == "ewa", f"R-6: mapa nadpisana z .claude/pdi-phases.json: {r.stdout}")
        (repo / ".claude" / "pdi-phases.json").unlink()
        for args, why in ((["--phase", "testing"], "nieznana faza"), (["--phase", "requirements", "--change", "chg"],
                                                                      "zły klucz zmiany")):
            r = run(["prompt", "--change", "CHG-12", *args], repo)
            check(r.returncode != 0, f"R-7: {why} → błąd: {r.stdout}")
        r = run(["prompt", "--change", "CHG-77", "--phase", "requirements"], repo)
        check(r.returncode != 0 and "change new" in r.stdout, f"R-8: brak dziennika zmiany → błąd: {r.stdout}")

        # --- run z podstawionym claude ---
        fake = Path(t) / "fake_claude.py"
        fake.write_text(FAKE_CLAUDE, encoding="utf-8")
        launcher = Path(t) / "claude"
        launcher.write_text(f"#!/bin/sh\nexec {sys.executable} {fake} \"$@\"\n", encoding="utf-8")
        launcher.chmod(0o755)
        log = Path(t) / "calls.log"
        env = {"PDI_CLAUDE_BIN": str(launcher), "FAKE_LOG": str(log)}
        r = run(["run", "--change", "CHG-12", "--phase", "requirements", "--budget-usd", "3"], repo, **env)
        res = jl(r) or {}
        calls = [json.loads(x) for x in log.read_text().splitlines()] if log.is_file() else []
        argv = calls[-1] if calls else []
        check(r.returncode == 0 and res.get("status") == "waiting_gate" and res.get("gate") == "B2"
              and res.get("cost_usd") == 0.42, f"R-9: udany przebieg czeka na bramkę: {r.stdout}{r.stderr}")
        check("--print" in argv and argv[argv.index("--agent") + 1] == "ewa" and "--output-format" in argv
              and argv[argv.index("--max-budget-usd") + 1] == "3" and argv[argv.index("--permission-mode") + 1] == "acceptEdits",
              f"R-10: claude bez interakcji, persona i budżet: {argv}")
        r = run(["run", "--change", "CHG-12", "--phase", "delivery"], repo, **env)
        res = jl(r) or {}
        argv = [json.loads(x) for x in log.read_text().splitlines()][-1]
        check(r.returncode == 0 and res.get("status") == "done" and "--max-budget-usd" not in argv,
              f"R-11: delivery bez bramki kończy się done, bez budżetu nie ma limitu: {r.stdout}")
        r = run(["run", "--change", "CHG-12", "--phase", "requirements"], repo, FAKE_ERROR="1", **env)
        check(r.returncode == 1 and (jl(r) or {}).get("status") == "failed", f"R-12: błąd modelu → failed: {r.stdout}")
        r = run(["run", "--change", "CHG-12", "--phase", "requirements"], repo, FAKE_EXIT="2", **env)
        check(r.returncode == 1 and (jl(r) or {}).get("status") == "failed", f"R-13: kod ≠ 0 → failed: {r.stdout}")
        n = len(log.read_text().splitlines())
        r = run(["run", "--change", "CHG-12", "--phase", "requirements", "--dry-run"], repo, **env)
        check(r.returncode == 0 and len(log.read_text().splitlines()) == n and "ewa" in r.stdout,
              f"R-14: --dry-run nie uruchamia modelu: {r.stdout}")
        r = run(["run", "--change", "CHG-12", "--phase", "requirements", "--budget-usd", "abc"], repo, **env)
        check(r.returncode != 0 and len(log.read_text().splitlines()) == n, "R-15: zły budżet → błąd bez modelu")

        # --- gate request ---
        req = repo / "docs" / "project" / "changes" / "CHG-12" / "requirements.md"
        req.write_text("---\nartifact: requirements\n---\n# Wymagania\n\n## Pytania do bramki\n- Limit ponowień: 3 czy 5?\n"
                       "- Czy płatności BLIK też?\n\n## Inne\n- nie pytanie\n", encoding="utf-8")
        srv = HTTPServer(("127.0.0.1", 0), Catch)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        genv = {"PDI_EVENTS_URL": url, "PDI_TF_SIGNING_SECRET": SECRET}
        r = run(["gate", "request", "--change", "CHG-12", "--phase", "requirements",
                 "--url", "https://github.com/acme/shop/pull/7"], repo, **genv)
        got = Catch.got[-1] if Catch.got else {}
        event = json.loads(got.get("body") or b"{}")
        h = got.get("headers", {})
        check(r.returncode == 0 and got.get("path") == "/events/tf", f"G-1: POST na /events/tf: {r.stdout}{r.stderr}")
        example = json.loads((FIX / "event-gate.requested.json").read_text(encoding="utf-8"))
        check(set(event) == set(example) and event.get("type") == "gate.requested" and event.get("source") == "tf"
              and event.get("contract_version") == example["contract_version"], f"G-2: koperta jak w przykładzie kontraktu: {event}")
        pl = event.get("payload", {})
        check(pl.get("change") == "CHG-12" and pl.get("gate") == "B2" and pl.get("artifact") == str(req.relative_to(repo))
              and pl.get("url") == "https://github.com/acme/shop/pull/7"
              and pl.get("questions") == ["Limit ponowień: 3 czy 5?", "Czy płatności BLIK też?"]
              and pl.get("summary"), f"G-3: treść prośby z pytaniami z artefaktu: {pl}")
        ts = h.get("x-pdi-timestamp", "")
        want = "v1=" + hmac.new(SECRET.encode(), f"{ts}.".encode() + got.get("body", b""), hashlib.sha256).hexdigest()
        check(h.get("x-pdi-signature") == want and h.get("x-pdi-event") == "gate.requested" and ts.isdigit(),
              f"G-4: podpis v1 HMAC-SHA256 i nagłówki X-PDI-*: {h}")
        import re
        check(re.match(r"^[A-Za-z0-9._-]{1,128}$", event.get("id", "")) and re.match(KEY_RE, pl.get("change", "")),
              f"G-5: id zdarzenia bezpieczne dla nazwy pliku w pdi: {event.get('id')}")
        r = run(["gate", "request", "--change", "CHG-12", "--gate", "design-review", "--summary", "Projekt ekranów."],
                repo, **genv)
        pl = json.loads(Catch.got[-1]["body"]).get("payload", {})
        check(r.returncode == 0 and pl.get("gate") == "design-review" and pl.get("summary") == "Projekt ekranów."
              and "artifact" not in pl, f"G-6: bramka podana wprost: {pl}")
        n = len(Catch.got)
        r = run(["gate", "request", "--change", "CHG-12", "--phase", "requirements", "--dry-run"], repo, **genv)
        check(r.returncode == 0 and len(Catch.got) == n and SECRET not in r.stdout and "gate.requested" in r.stdout,
              f"G-7: --dry-run bez wysyłki i bez sekretu: {r.stdout}")
        r = run(["gate", "request", "--change", "CHG-12", "--phase", "requirements"], repo, PDI_EVENTS_URL=url,
                PDI_TF_SIGNING_SECRET="")
        check(r.returncode != 0 and len(Catch.got) == n and "PDI_TF_SIGNING_SECRET" in r.stdout, "G-8: brak sekretu → błąd")
        r = run(["gate", "request", "--change", "CHG-12", "--phase", "requirements"], repo, PDI_EVENTS_URL="",
                PDI_TF_SIGNING_SECRET=SECRET)
        check(r.returncode != 0 and "PDI_EVENTS_URL" in r.stdout, "G-9: brak adresu → błąd")
        r = run(["gate", "request", "--change", "CHG-12", "--phase", "requirements"], repo,
                PDI_EVENTS_URL="http://pdi.example.com", PDI_TF_SIGNING_SECRET=SECRET)
        check(r.returncode != 0 and "https" in r.stdout, f"G-10: http poza localhost → błąd: {r.stdout}")
        r = run(["gate", "request", "--change", "CHG-12", "--phase", "delivery"], repo, **genv)
        check(r.returncode != 0 and "--gate" in r.stdout, f"G-11: faza bez bramki → błąd z podpowiedzią: {r.stdout}")
        Catch.status = 400
        r = run(["gate", "request", "--change", "CHG-12", "--phase", "requirements"], repo, **genv)
        check(r.returncode != 0 and "400" in r.stdout, f"G-12: odmowa pdi → błąd z kodem: {r.stdout}")
        Catch.status = 202
        srv.shutdown()

        # --- F3: faza intent ze zgłoszenia z pdi ---
        (repo / ".claude" / "pdi-phases.json").write_text('{"intent": {"persona": "ewa"}}', encoding="utf-8")
        problem = json.dumps({"title": "Brak operacji masowych", "who": "operator", "cannot": "zmienić wielu ładowarek",
                              "impact": "dzień pracy", "proposed_solution": "przycisk bulk update"})
        r = run(["prompt", "--change", "CHG-12", "--phase", "intent"], repo, PDI_SOURCE="PRB-3", PDI_PROBLEM=problem)
        text = (jl(r) or {}).get("prompt", "")
        check(r.returncode == 0 and "PRB-3" in text and "operator" in text and "zmienić wielu ładowarek" in text
              and "dzień pracy" in text and "przycisk bulk update" in text and "nie wymaganie" in text,
              f"I-1: prompt fazy intent niesie treść zgłoszenia, a pomysł zgłaszającego jako nie-wymaganie: {text[:600]}")
        r = run(["prompt", "--change", "CHG-12", "--phase", "intent"], repo, PDI_PROBLEM="[1, 2]")
        check(r.returncode != 0 and "PDI_PROBLEM" in r.stdout, f"I-2: zły PDI_PROBLEM → błąd: {r.stdout}")
        r = run(["prompt", "--change", "CHG-12", "--phase", "requirements"], repo, PDI_SOURCE="PRB-3", PDI_PROBLEM=problem)
        check("bulk update" not in (jl(r) or {}).get("prompt", ""), "I-3: treść zgłoszenia tylko w fazie intent")
        (repo / ".claude" / "pdi-phases.json").unlink()

        # --- workflow install ---
        r = run(["workflow", "install"], repo)
        wf = repo / ".github" / "workflows" / "sdlc-phase.yml"
        body = wf.read_text(encoding="utf-8") if wf.is_file() else ""
        check(r.returncode == 0 and "workflow_dispatch" in body, f"W-1: szablon w .github/workflows: {r.stdout}{r.stderr}")
        for name in ("change", "phase", "gate", "outcome", "decision", "rework", "budget_usd", "source", "problem"):
            check(f"      {name}:" in body, f"W-2: wejście {name} z pdi (dbqm45/pdi src/pdi/dispatch.py)")
        check("phase_run.py run" in body and "phase_run.py gate request" in body and "decision_record.py decision gate" in body
              and "ANTHROPIC_API_KEY" in body and "PDI_TF_SIGNING_SECRET" in body and "PDI_EVENTS_URL" in body,
              "W-3: kroki: decyzja, faza, prośba o bramkę; sekrety")
        import re as _re
        bad = [ln for ln in body.splitlines() if "${{ inputs." in ln
               and not _re.match(r"^\s+[A-Z_]+: \$\{\{ inputs\.\w+ \}\}$", ln) and not ln.startswith("run-name:")]
        check(body and not bad, f"W-4: wejścia z pdi trafiają do poleceń tylko przez env (wstrzyknięcie): {bad}")
        check("--source-reported-at" in body and "reported_at" in body,
              "W-8: szablon przekazuje datę zgłoszenia z treści zgłoszenia do nagłówka zmiany")
        check("decision_record.py change new" in body and "--source" in body and "PDI_PROBLEM" in body,
              "W-7: faza intent z pdi zakłada dziennik zmiany ze zgłoszenia i dostaje jego treść (F3)")
        wf.write_text("moje\n", encoding="utf-8")
        r = run(["workflow", "install"], repo)
        check(r.returncode != 0 and wf.read_text(encoding="utf-8") == "moje\n", "W-5: bez nadpisania")
        r = run(["workflow", "install", "--force"], repo)
        check(r.returncode == 0 and "workflow_dispatch" in wf.read_text(encoding="utf-8"), "W-6: --force nadpisuje")

    # --- PR-y cięć po fazie delivery: persona w --print nie może pushować ani otwierać PR-ów (pdi PRB-4) ---
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        remote, repo, log = t / "remote.git", t / "repo", t / "gh.log"

        def git(*args, cwd=None):
            return subprocess.run(["git", *args], cwd=cwd or repo, capture_output=True, text=True, check=True).stdout

        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
        subprocess.run(["git", "clone", "-q", str(remote), str(repo)], check=True, capture_output=True)
        for k, v in (("user.name", "t"), ("user.email", "t@example.com"), ("commit.gpgsign", "false")):
            git("config", k, v)
        (repo / "a.txt").write_text("a\n")
        git("add", "-A")
        git("commit", "-qm", "init")
        git("push", "-q", "origin", "main")
        git("branch", "story/stara")
        gh = t / "gh"
        gh.write_text(f"""#!{sys.executable}
import json, os, sys
open({str(log)!r}, "a").write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["pr", "view"]:
    if "tsk-9" not in sys.argv[3]:
        sys.exit(1)
    print("https://github.com/o/r/pull/9")
if sys.argv[1:3] == ["pr", "create"]:
    n = 1 if "tsk-1" in sys.argv[sys.argv.index("--head") + 1] else 2
    print(f"https://github.com/o/r/pull/{{n}}")
""")
        gh.chmod(0o755)
        env = {"PDI_GH_BIN": str(gh)}
        r = run(["cuts", "list"], repo, **env)
        before = t / "before.json"
        before.write_text(r.stdout)
        check(r.returncode == 0 and jl(r) == ["story/stara"], f"C-1: cuts list podaje gałęzie story/*: {r.stdout}{r.stderr}")
        r = run(["cuts", "publish", "--before", str(before), "--base", "main"], repo, **env)
        out = jl(r) or {}
        check(r.returncode == 1 and out.get("status") == "failed" and "story/" in out.get("error", ""),
              f"C-2: bez nowych cięć z commitami → błąd: {r.stdout}{r.stderr}")
        git("switch", "-qc", "story/tsk-1-fundament")
        (repo / "b.txt").write_text("b\n")
        git("add", "-A")
        git("commit", "-qm", "feat: b", "-m", "Change: TSK-1")
        git("switch", "-qc", "story/tsk-2-data")
        (repo / "c.txt").write_text("c\n")
        git("add", "-A")
        git("commit", "-qm", "feat: c", "-m", "Change: TSK-2")
        git("branch", "story/pusta", "main")
        git("switch", "-q", "main")
        r = run(["cuts", "publish", "--before", str(before), "--base", "main", "--dry-run"], repo, **env)
        check(r.returncode == 0 and not log.exists() and "story/tsk-1-fundament" not in git("ls-remote", "--heads", "origin"),
              f"C-3: --dry-run niczego nie wypycha ani nie otwiera: {r.stdout}{r.stderr}")
        r = run(["cuts", "publish", "--before", str(before), "--base", "main"], repo, **env)
        out = jl(r) or {}
        calls = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
        creates = [c for c in calls if c[:2] == ["pr", "create"]]
        heads = git("ls-remote", "--heads", "origin")
        check(r.returncode == 0 and out.get("status") == "done" and out.get("prs") == [
            {"branch": "story/tsk-1-fundament", "pr": "https://github.com/o/r/pull/1"},
            {"branch": "story/tsk-2-data", "pr": "https://github.com/o/r/pull/2"}],
              f"C-4: nowe cięcia z commitami → push i PR każdego: {r.stdout}{r.stderr}")
        check("story/tsk-1-fundament" in heads and "story/tsk-2-data" in heads and "story/pusta" not in heads
              and "story/stara" not in heads, f"C-5: wypchnięte tylko nowe gałęzie z commitami: {heads}")
        check(["pr", "create", "--fill", "--head", "story/tsk-1-fundament", "--base", "main"] in creates
              and ["pr", "create", "--fill", "--head", "story/tsk-2-data", "--base", "story/tsk-1-fundament"] in creates,
              f"C-6: cięcie zbudowane na poprzednim ma PR do niego: {creates}")
        git("branch", "story/tsk-9-ma-pr", "story/tsk-2-data")
        git("switch", "-q", "story/tsk-9-ma-pr")
        (repo / "d.txt").write_text("d\n")
        git("add", "-A")
        git("commit", "-qm", "feat: d")
        git("switch", "-q", "main")
        before.write_text(json.dumps(["story/stara", "story/tsk-1-fundament", "story/tsk-2-data"]))
        r = run(["cuts", "publish", "--before", str(before), "--base", "main"], repo, **env)
        check(r.returncode == 0 and (jl(r) or {}).get("prs") == [
            {"branch": "story/tsk-9-ma-pr", "pr": "https://github.com/o/r/pull/9"}],
              f"C-7: istniejący PR cięcia zostaje: {r.stdout}{r.stderr}")
        r = run(["cuts", "publish", "--before", str(t / "brak.json"), "--base", "main"], repo, **env)
        check(r.returncode == 1 and "brak.json" in r.stdout, f"C-8: brak pliku sprzed fazy → błąd: {r.stdout}")

    body = TEMPLATE_BODY()
    check("phase_run.py cuts list" in body and "phase_run.py cuts publish" in body and "DEFAULT_BRANCH" in body,
          "W-9: workflow w fazie delivery zapisuje gałęzie cięć przed fazą i wystawia ich PR-y po niej")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów faz uruchamianych przez pdi (mode-pdi)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
