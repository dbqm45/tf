#!/usr/bin/env python3
"""Ustawienia sandboxu Claude Code dla persony fazy uruchamianej przez pdi (krok Z8a pdi, decyzja DZ9).

  python3 .claude/skills/pdi-decisions/scripts/sandbox_settings.py [--nested] [--root .]
      wypisuje JSON ustawień: sandbox poleceń Bash (failIfUnavailable, bez wyjścia poza sandbox), lista hostów sieci,
      zakaz czytania sekretów z domu, zmienne z tokenami niewidoczne dla poleceń w sandboxie.

Workflow `sdlc-phase.yml` zapisuje wynik jako ustawienia zarządzane (`/etc/claude-code/managed-settings.json`) i
podaje go `claude` przez `--settings` (`PDI_CLAUDE_SETTINGS` w `phase_run.py run`), więc `.claude/settings.json`
produktu nie poluzuje ograniczeń. pdi w trybie lokalnym (`PDI_DISPATCH=local`) używa tych samych kluczy w kontenerze
(`pdi.phase_sandbox.claude_settings`) i dodaje `--nested` (`enableWeakerNestedSandbox`: sandbox w nieuprzywilejowanym
kontenerze). Hosty: `api.anthropic.com`, rejestry pakietów według plików w katalogu głównym repo, `semgrep.dev` (reguły
skanera) i `PDI_DISPATCH_ALLOW_HOSTS` (po przecinku, `*.domena` dozwolone). Kod wyjścia: 0 — w porządku, 2 — złe
wywołanie.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ALWAYS = ("api.anthropic.com",)
SCANNER = ("semgrep.dev",)
REGISTRIES = {
    "package.json": ("registry.npmjs.org",),
    "pyproject.toml": ("pypi.org", "files.pythonhosted.org"),
    "requirements.txt": ("pypi.org", "files.pythonhosted.org"),
    "go.mod": ("proxy.golang.org", "sum.golang.org"),
    "Cargo.toml": ("index.crates.io", "static.crates.io"),
    "Gemfile": ("rubygems.org", "index.rubygems.org"),
    "pom.xml": ("repo.maven.apache.org", "repo1.maven.org"),
    "build.gradle": ("repo.maven.apache.org", "repo1.maven.org", "plugins.gradle.org"),
    "build.gradle.kts": ("repo.maven.apache.org", "repo1.maven.org", "plugins.gradle.org"),
}
TOKENS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
HOME_SECRETS = ("~/.claude.json", "~/.claude", "~/.ssh", "~/.sdlc", "~/.aws", "~/.config")
HOST = re.compile(r"^(\*\.)?[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?)+$")


def hosts(root: Path, extra: str) -> list[str]:
    out = list(ALWAYS)
    found = [h for name, hs in REGISTRIES.items() if (root / name).is_file() for h in hs]
    for host in [*found, *SCANNER, *(h.strip().lower() for h in extra.split(","))]:
        if host and HOST.match(host) and host not in out:
            out.append(host)
    return out


def settings(allowed: list[str], *, nested: bool) -> dict:
    return {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "autoAllowBashIfSandboxed": False,
            "enableWeakerNestedSandbox": nested,
            "filesystem": {"denyRead": list(HOME_SECRETS), "allowWrite": ["/tmp"]},
            "network": {"allowedDomains": allowed, "allowManagedDomainsOnly": True},
            "credentials": {"envVars": [{"name": n, "mode": "deny"} for n in TOKENS]},
        },
        "permissions": {"deny": ["Read(//proc/**)", "Read(~/.claude.json)", "Read(~/.claude/**)", "Read(~/.ssh)",
                                 "Read(~/.sdlc/**)"]},
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Ustawienia sandboxu Claude Code dla persony fazy (JSON na stdout).")
    ap.add_argument("--root", default=".", help="katalog repo produktu (domyślnie bieżący)")
    ap.add_argument("--nested", action="store_true", help="sandbox w nieuprzywilejowanym kontenerze (pdi lokalnie)")
    a = ap.parse_args(argv)
    allowed = hosts(Path(a.root), os.environ.get("PDI_DISPATCH_ALLOW_HOSTS") or "")
    print(json.dumps(settings(allowed, nested=a.nested), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
