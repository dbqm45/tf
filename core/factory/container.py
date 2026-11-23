#!/usr/bin/env python3
"""The container level of isolation (plan docs/plans/2026-11-20-poziomy-izolacji.md, slice I4).

`tf code --container` (or the level `container`) runs the factory session in the image `tf-sandbox:<factory version>`
(`.tf/factory/container/Dockerfile`, built on first use) with Docker or Podman, whichever is installed
(`TF_CONTAINER_ENGINE` chooses):
- only the project is mounted (`/workspace`); Claude's own files (login, history) live in the named volume
  `tf-claude-<project>`; no home directory, no Docker socket, no ~/.ssh or ~/.gitconfig — so `git push` has no keys
  (decision D1: the container commits, a human pushes from their own computer);
- the image filesystem is read-only, the session runs as `node` without capabilities, and the firewall
  (`init_firewall.sh`) lets out only the fixed list of domains plus the project's `isolation_allow_domains`;
- the session settings carry no Bash sandbox: the container is the boundary (bubblewrap does not start under the
  default seccomp profile of Docker [assumption: not measured]).

  container.py args [--] [claude arguments]   # the engine command as JSON (for tests and for reading)
  container.py run [--] [claude arguments]    # build the image when missing, then run the session
"""
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONUTF8", "1")  # child processes also write and read UTF-8
for _stream in (sys.stdout, sys.stderr):  # Windows: the code page ≠ UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ENGINE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = ENGINE_DIR / "container"
ENGINES = ("docker", "podman")
DOMAIN = re.compile(r"^(?=.{1,253}$)([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$")
BASE_DOMAINS = ("api.anthropic.com", "statsig.anthropic.com", "claude.ai", "console.anthropic.com",
                "github.com", "api.github.com", "codeload.github.com", "objects.githubusercontent.com")


def _module(name: str):
    spec = importlib.util.spec_from_file_location(f"tf_{name}_container", ENGINE_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def engine() -> str | None:
    """`TF_CONTAINER_ENGINE` when given and installed, else Docker, else Podman."""
    wanted = os.environ.get("TF_CONTAINER_ENGINE")
    for name in ([wanted] if wanted else ENGINES):
        path = shutil.which(name)
        if path:
            return path
    return None


def image(root: Path) -> str:
    version = (root / ".tf" / "factory" / "VERSION")
    return f"tf-sandbox:{version.read_text(encoding='utf-8').strip() if version.is_file() else 'dev'}"


def allow_domains(root: Path) -> list[str]:
    """The fixed list, the sandbox template's registries and the project's `isolation_allow_domains` (valid names only)."""
    out = list(BASE_DOMAINS)
    try:
        out += json.loads((IMAGE_DIR.parent / "templates" / "sandbox.settings.json").read_text(encoding="utf-8")
                          )["sandbox"]["network"]["allowedDomains"]
    except (OSError, ValueError, KeyError):
        pass
    extra = {}
    for _label, data in _module("packs").config_layers(root):
        if isinstance(data, dict) and isinstance(data.get("isolation_allow_domains"), list):
            extra = data["isolation_allow_domains"]
    out += [d for d in extra if isinstance(d, str)]
    return list(dict.fromkeys(d.lower() for d in out if DOMAIN.match(d)))


def pinned_hosts(domains: list[str]) -> list[str]:
    """`--add-host <domain>:<address>` for each domain resolved here, on the host: the engine writes them into the
    container's /etc/hosts (read-only inside), so the firewall and every program use one address per domain."""
    out = []
    for d in domains:
        try:
            infos = socket.getaddrinfo(d, 443, socket.AF_INET, socket.SOCK_STREAM)
        except (socket.gaierror, OSError, UnicodeError):
            continue                       # not resolvable here: the firewall resolves it itself at the start
        if infos:
            out += ["--add-host", f"{d}:{infos[0][4][0]}"]
    return out


def volume(root: Path) -> str:
    name = re.sub(r"[^a-z0-9_.-]", "-", root.resolve().name.lower()).strip("-.") or "project"
    return f"tf-claude-{name}"


def git_identity() -> list[str]:
    """The human's name and e-mail for commits made in the container (values only, ~/.gitconfig is not mounted)."""
    out = []
    for key, names in (("user.name", ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME")),
                       ("user.email", ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"))):
        try:
            value = subprocess.run(["git", "config", "--get", key], capture_output=True, text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            value = ""
        if value:
            for n in names:
                out += ["-e", f"{n}={value}"]
    return out


def session_settings(root: Path) -> Path | None:
    """`.tf/cache/session-settings.json` for the container: the plugin's settings without a Bash sandbox."""
    plugin = root / ".tf" / "plugin" / "session-settings.json"
    if not plugin.is_file():
        return None
    iso = _module("isolation")
    out = root / iso.LAUNCH
    out.parent.mkdir(parents=True, exist_ok=True)
    data = iso.with_level(json.loads(plugin.read_text(encoding="utf-8")), "basic")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def run_args(root: Path, rest: list[str]) -> list[str]:
    """The engine's `run` arguments (without the engine itself)."""
    root = root.resolve()
    inside = ["claude"]
    if session_settings(root):
        inside += ["--plugin-dir", "/workspace/.tf/plugin", "--settings", "/workspace/.tf/cache/session-settings.json"]
    tty = ["-t"] if sys.stdin.isatty() and sys.stdout.isatty() else []
    domains = allow_domains(root)
    return ["run", "--rm", "-i", *tty,
            "--cap-drop", "ALL", "--cap-add", "NET_ADMIN", "--cap-add", "NET_RAW", "--cap-add", "SETUID",
            "--cap-add", "SETGID", "--cap-add", "SETPCAP", "--security-opt", "no-new-privileges",
            "--read-only", "--tmpfs", "/tmp", "--tmpfs", "/run", "--tmpfs", "/home/node:mode=1777",
            "-v", f"{root}:/workspace", "-w", "/workspace", "-v", f"{volume(root)}:/home/node/.claude",
            "-e", "TF_ISOLATION=container", "-e", "CLAUDE_CONFIG_DIR=/home/node/.claude",
            "-e", f"TF_ALLOW_DOMAINS={','.join(domains)}", *pinned_hosts(domains), *git_identity(),
            image(root), *inside, *rest]


def run(root: Path, rest: list[str]) -> int:
    if os.environ.get("TF_CONTAINER") == "1":
        print("✗ This session already runs in the factory's container — start `tf code --container` on your computer.",
              file=sys.stderr)
        return 2
    eng = engine()
    if not eng:
        print("✗ The container level needs Docker or Podman (neither is in PATH). Install one of them, or choose "
              "another level in a terminal: `tf isolation sandbox`.", file=sys.stderr)
        return 2
    tag = image(root)
    if subprocess.run([eng, "image", "inspect", tag], capture_output=True).returncode != 0:
        print(f"ℹ Building the image {tag} (first start, a few minutes)…", file=sys.stderr)
        b = subprocess.run([eng, "build", "-t", tag, str(IMAGE_DIR)])
        if b.returncode != 0:
            print(f"✗ The image {tag} did not build (exit {b.returncode}).", file=sys.stderr)
            return b.returncode
    try:
        code = subprocess.run([eng, *run_args(root, rest)]).returncode
    except KeyboardInterrupt:
        code = 130
    unpushed_hint(root)
    return code


def unpushed_hint(root: Path) -> None:
    """After the session: the container has no git keys (D1), so the commits made there wait for a push from here."""
    try:
        r = subprocess.run(["git", "rev-list", "--count", "HEAD", "--not", "--remotes"], cwd=root, capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return
    n = int(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip().isdigit() else 0
    if n:
        print(f"ℹ {n} commit{'s' if n != 1 else ''} from the session not pushed yet — the container has no git keys; "
              "review them (`git log --stat @{u}..`) and push from this terminal: `git push`.", file=sys.stderr)


def main(argv: list[str]) -> int:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    rest = rest[1:] if rest[:1] == ["--"] else rest
    if cmd == "args":
        print(json.dumps(run_args(root, rest), ensure_ascii=False))
        return 0
    if cmd == "run":
        return run(root, rest)
    print(__doc__, file=sys.stderr if cmd not in ("-h", "--help") else sys.stdout)
    return 0 if cmd in ("-h", "--help") else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
