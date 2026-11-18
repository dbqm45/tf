#!/usr/bin/env python3
"""Claude Code sandbox settings for a phase persona run by pdi (pdi step Z8a, decision DZ9).

  python3 .claude/skills/pdi-decisions/scripts/sandbox_settings.py [--nested] [--root .]
      prints the settings JSON: a Bash command sandbox (failIfUnavailable, no escape outside the sandbox), a list of network hosts,
      a ban on reading secrets from home, token variables invisible to commands in the sandbox.

The `sdlc-phase.yml` workflow writes the result as managed settings (`/etc/claude-code/managed-settings.json`) and
passes it to `claude` via `--settings` (`PDI_CLAUDE_SETTINGS` in `phase_run.py run`), so the product's `.claude/settings.json`
does not loosen the restrictions. pdi in local mode (`PDI_DISPATCH=local`) uses the same keys in the container
(`pdi.phase_sandbox.claude_settings`) and adds `--nested` (`enableWeakerNestedSandbox`: a sandbox in an unprivileged
container). Hosts: `api.anthropic.com`, package registries according to the files in the repo root, `semgrep.dev` (scanner
rules) and `PDI_DISPATCH_ALLOW_HOSTS` (comma-separated, `*.domain` allowed). Exit code: 0 — OK, 2 — bad
invocation.
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
    ap = argparse.ArgumentParser(description="Claude Code sandbox settings for a phase persona (JSON on stdout).")
    ap.add_argument("--root", default=".", help="product repo folder (default: current)")
    ap.add_argument("--nested", action="store_true", help="sandbox in an unprivileged container (pdi locally)")
    a = ap.parse_args(argv)
    allowed = hosts(Path(a.root), os.environ.get("PDI_DISPATCH_ALLOW_HOSTS") or "")
    print(json.dumps(settings(allowed, nested=a.nested), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
