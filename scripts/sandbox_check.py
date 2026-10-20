#!/usr/bin/env python3
"""Sprawdza na żywo piaskownicę Bash Claude Code z szablonem fabryki (factory/templates/sandbox.settings.json)
na tej maszynie — przede wszystkim na macOS (Seatbelt), gdzie fabryka nie ma własnego wyniku.

  python3 scripts/sandbox_check.py [--model haiku] [--budget 0.05] [--keep]

Płatne: 6 przebiegów `claude -p` (4 przypadki i 2 pomiary narzutu), każdy z limitem `--max-budget-usd`
(domyślnie 0,05 USD, czyli najwyżej 0,30 USD; typowo ok. 0,03 USD razem na haiku). Każdy przebieg działa
w świeżym repozytorium tymczasowym z `--setting-sources project,local`, więc Twoje ustawienia użytkownika nie
wpływają na wynik, a skrypt niczego w nich nie zmienia. Sonda zapisuje jeden plik w katalogu domowym
(`~/.sandbox-check-outside.tmp`) — skrypt usuwa go na końcu. Model dostaje pozwolenie tylko na `./probe.sh`
i `./noop.sh`.

Przypadki:
  A_root          start w korzeniu repozytorium z ustawieniami projektu
  B_subdir        start w podkatalogu `pkg/` (ustawienia projektu leżą w korzeniu)
  B2_subdir_flag  jak B, plus `--settings <szablon>`
  D_merge         jak A, plus `--settings` z samym `sandbox.excludedCommands` (czy scala się per klucz)
Narzut: 5 wywołań `./noop.sh` z piaskownicą i bez; czas z hooków PreToolUse→PostToolUse.

Wynik (Markdown) idzie na stdout — wklej go do rozmowy z agentem.
"""
from __future__ import annotations

import argparse
import http.server
import json
import platform
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "factory" / "templates" / "sandbox.settings.json"
OUTSIDE_NAME = ".sandbox-check-outside.tmp"

CHECKS = ("placeholders", "write_cwd", "write_root", "write_outside", "write_git", "git_config", "git_hooks",
          "git_commit", "git_add_all", "localhost")

CASES = {
    "A_root": "start w korzeniu repo",
    "B_subdir": "start w `pkg/`",
    "B2_subdir_flag": "`pkg/` + `--settings <szablon>`",
    "D_merge": "korzeń + częściowy `--settings`",
}

PROBE = """#!/bin/sh
# Sonda sandbox_check: jedna linia „klucz: wynik” na sprawdzenie.
R=$(git rev-parse --show-toplevel)
# najpierw pliki, które pojawiły się w repo przed jakimkolwiek zapisem sondy (atrapy piaskownicy)
P=$(git status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//' | tr '\\n' ' ' | sed 's/ *$//')
echo "placeholders: ${{P:-none}}"
chk() {{
  if out=$(sh -c "$2" 2>&1); then echo "$1: OK"; else echo "$1: DENIED $(printf '%s' "$out" | head -n 1)"; fi
}}
chk write_cwd "echo x > ./sbx-cwd.tmp"
chk write_root "echo x > \\"$R/sbx-root.tmp\\""
chk write_outside "echo x > {outside}"
chk write_git "echo x > \\"$R/.git/sbx-probe.tmp\\""
chk git_config "git config probe.x 1"
chk git_hooks "echo x > \\"$R/.git/hooks/sbx-probe-hook\\""
chk git_commit "git -c commit.gpgsign=false commit -q --allow-empty -m probe"
chk git_add_all "git add -A && git reset -q"
chk localhost "curl -sf -m 3 -o /dev/null http://127.0.0.1:{port}/"
"""

PROMPT = ("Run exactly this one Bash command and nothing else: ./probe.sh — then reply with its raw output only. "
          "Do not retry, do not run anything else.")
PERF_PROMPT = ("Run the Bash command ./noop.sh exactly 5 times, as 5 separate Bash tool calls one after another. "
               "Do not run anything else. Then reply: done.")


def parse_probe(text: str) -> dict[str, str]:
    """Linie „klucz: wartość” sondy → słownik; inne linie pomija."""
    out = {}
    for line in text.splitlines():
        key, sep, value = line.partition(": ")
        if sep and key in CHECKS:
            out[key] = value.strip()
    return out


def read_stream(text: str) -> tuple[dict[str, str], float]:
    """Strumień `--output-format stream-json` → (wynik pierwszego wywołania sondy, koszt w USD)."""
    probe: dict[str, str] | None = None
    cost = 0.0
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "result":
            cost = float(event.get("total_cost_usd") or 0.0)
        if probe is not None or event.get("type") != "user":
            continue
        content = (event.get("message") or {}).get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                body = block.get("content")
                if isinstance(body, list):
                    body = "\n".join(b.get("text", "") for b in body if isinstance(b, dict))
                probe = parse_probe(body or "")
                break
    return probe or {}, cost


def perf_medians(log: str) -> dict[str, float]:
    """Log hooków „pre|post <ns> <etykieta>” → mediana czasu wywołania w ms dla każdej etykiety."""
    start: dict[str, int] = {}
    times: dict[str, list[float]] = {}
    for line in log.splitlines():
        parts = line.split()
        if len(parts) != 3 or not parts[1].isdigit():
            continue
        kind, ns, label = parts[0], int(parts[1]), parts[2]
        if kind == "pre":
            start[label] = ns
        elif kind == "post" and label in start:
            times.setdefault(label, []).append((ns - start.pop(label)) / 1e6)
    return {label: round(statistics.median(v), 1) for label, v in times.items()}


class _Ok(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 — nazwa wymagana przez http.server
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def serve_localhost() -> tuple[http.server.HTTPServer, int]:
    """Serwer HTTP na 127.0.0.1 poza piaskownicą — czy sonda go osiągnie (`allowLocalBinding`, sieć)."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Ok)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "sandbox-check")
    _git(repo, "config", "user.email", "sandbox-check@example.invalid")
    _git(repo, "config", "commit.gpgsign", "false")


def _write_exec(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def prepare(workdir: Path, template: Path, port: int, outside: Path) -> Path:
    """Repo tymczasowe: ustawienia projektu = szablon, sonda w korzeniu i w `pkg/`, wszystko w commicie."""
    repo = Path(workdir) / "repo"
    _init_repo(repo)
    (repo / ".claude").mkdir()
    shutil.copyfile(template, repo / ".claude" / "settings.json")
    probe = PROBE.format(outside=shlex.quote(str(outside)), port=port)
    _write_exec(repo / "probe.sh", probe)
    _write_exec(repo / "pkg" / "probe.sh", probe)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _perf_repo(workdir: Path, template: Path, label: str, log: Path) -> Path:
    """Repo do pomiaru narzutu: szablon (z piaskownicą albo bez) + hooki zapisujące znacznik czasu."""
    repo = Path(workdir) / f"perf-{label}"
    _init_repo(repo)
    settings = json.loads(template.read_text(encoding="utf-8"))
    settings["sandbox"]["enabled"] = label == "on"

    def hook(kind: str) -> list[dict]:
        code = f"import sys,time;open(sys.argv[1],'a').write('{kind} %d {label}\\n' % time.time_ns())"
        cmd = f"{shlex.quote(sys.executable)} -c {shlex.quote(code)} {shlex.quote(str(log))}"
        return [{"matcher": "Bash", "hooks": [{"type": "command", "command": cmd}]}]

    settings["hooks"] = {"PreToolUse": hook("pre"), "PostToolUse": hook("post")}
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
    _write_exec(repo / "noop.sh", "#!/bin/sh\nexit 0\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _claude(cwd: Path, prompt: str, tool: str, args: argparse.Namespace, extra: list[str]) -> str:
    cmd = ["claude", "-p", prompt, "--model", args.model, "--max-budget-usd", str(args.budget),
           "--allowedTools", f"Bash({tool})", "--setting-sources", "project,local",
           "--output-format", "stream-json", "--verbose", *extra]
    try:
        p = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print(f"  ✗ przekroczony czas: {cwd}", file=sys.stderr)
        return ""
    if p.returncode != 0:
        print(f"  ! claude zakończył się kodem {p.returncode}: {p.stderr.strip()[:200]}", file=sys.stderr)
    return p.stdout


def _cell(value: str | None) -> str:
    return "—" if not value else value.replace("|", "\\|")


def report(results: dict[str, dict[str, str]], perf: dict[str, float], meta: dict) -> str:
    """Raport Markdown: tabela sprawdzenie × przypadek, narzut, system i wersja Claude Code."""
    cases = list(results)
    lines = [
        "## Piaskownica Bash — sandbox_check",
        "",
        f"- system: {meta.get('os', '?')} {meta.get('os_version', '')}".rstrip()
        + f" · claude: {meta.get('claude', '?')} · model: {meta.get('model', '?')}"
        + f" · koszt: {float(meta.get('cost', 0.0)):.4f} USD",
        "- przypadki: " + "; ".join(f"`{c}` {CASES.get(c, '')}".rstrip() for c in cases),
        "",
        "| sprawdzenie | " + " | ".join(cases) + " |",
        "|---" * (len(cases) + 1) + "|",
    ]
    for key in CHECKS:
        lines.append(f"| {key} | " + " | ".join(_cell(results[c].get(key)) for c in cases) + " |")
    on, off = perf.get("on"), perf.get("off")
    lines.append("")
    if on is not None and off is not None:
        lines.append(f"- narzut na wywołanie Bash (mediana, hook pre→post): z piaskownicą {on:g} ms, "
                     f"bez {off:g} ms, różnica {on - off:g} ms")
    else:
        lines.append(f"- narzut: brak pełnego pomiaru ({perf or 'brak danych'})")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--budget", type=float, default=0.05, help="limit USD na jeden przebieg claude -p")
    ap.add_argument("--keep", action="store_true", help="zostaw katalog roboczy (strumienie JSON) do wglądu")
    args = ap.parse_args(argv)

    if not shutil.which("claude") or not shutil.which("git"):
        print("✗ potrzebne polecenia `claude` i `git` w PATH", file=sys.stderr)
        return 1
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    meta = {"os": platform.system(), "os_version": platform.release(), "claude": version, "model": args.model}

    workdir = Path(tempfile.mkdtemp(prefix="sandbox-check-"))
    outside = Path.home() / OUTSIDE_NAME
    server, port = serve_localhost()
    results: dict[str, dict[str, str]] = {}
    total = 0.0
    try:
        runs = {
            "A_root": ("", []),
            "B_subdir": ("pkg", []),
            "B2_subdir_flag": ("pkg", ["--settings", str(TEMPLATE)]),
            "D_merge": ("", ["--settings", json.dumps({"sandbox": {"excludedCommands": ["foo *"]}})]),
        }
        for case, (sub, extra) in runs.items():
            print(f"… {case}", file=sys.stderr)
            repo = prepare(workdir / case, TEMPLATE, port, outside)
            stream = _claude(repo / sub, PROMPT, "./probe.sh", args, extra)
            (workdir / f"{case}.jsonl").write_text(stream, encoding="utf-8")
            results[case], cost = read_stream(stream)
            total += cost
            if outside.exists():
                outside.unlink()

        log = workdir / "perf.log"
        for label in ("on", "off"):
            print(f"… narzut: {label}", file=sys.stderr)
            stream = _claude(_perf_repo(workdir, TEMPLATE, label, log), PERF_PROMPT, "./noop.sh", args, [])
            (workdir / f"perf-{label}.jsonl").write_text(stream, encoding="utf-8")
            total += read_stream(stream)[1]
        perf = perf_medians(log.read_text(encoding="utf-8") if log.exists() else "")
    finally:
        server.shutdown()
        if outside.exists():
            outside.unlink()
        if args.keep:
            print(f"katalog roboczy: {workdir}", file=sys.stderr)
        else:
            shutil.rmtree(workdir, ignore_errors=True)

    meta["cost"] = total
    print(report(results, perf, meta))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
