#!/usr/bin/env python3
"""The container level (plan docs/plans/2026-11-20-poziomy-izolacji.md, slice I4): `tf code --container` (or the level
`container`) runs the session in the factory image with only the project mounted — no home directory, no Docker socket,
no ~/.ssh — a named volume for Claude's own files, the firewall's allowed domains (the fixed list plus
`isolation_allow_domains`), and Docker or Podman, whichever is installed. A stand-in engine records the command.
python3 .claude/tests/test_isolation_container.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
CLEAN = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "TF_ISOLATION",
                                                          "TF_CONTAINER", "TF_CONTAINER_ENGINE")}
FAKE = ("#!/bin/sh\n"
        "if [ \"$1\" = image ]; then exit 0; fi\n"            # `image inspect`: the image is there
        "printf '%s\\n' \"$@\" > \"$TF_FAKE_OUT\"\n")


def project(base: Path, name: str, config: str = "") -> Path:
    p = base / name
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__", "packs"))
    (p / ".claude").mkdir(parents=True)
    shutil.copy(ROOT / ".claude" / "factory-manifest.json", p / ".claude" / "factory-manifest.json")
    m = json.loads((p / ".claude" / "factory-manifest.json").read_text(encoding="utf-8"))
    (p / ".claude" / "factory-manifest.json").write_text(json.dumps({**m, "layout": "plugin"}), encoding="utf-8")
    (p / ".tf" / "plugin" / ".claude-plugin").mkdir(parents=True)
    (p / ".tf" / "plugin" / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (p / ".tf" / "plugin" / "session-settings.json").write_text(json.dumps({"env": {"A": "1"}}), encoding="utf-8")
    (p / ".tf" / "config").mkdir(parents=True)
    (p / ".tf" / "config" / "config.yaml").write_text(config, encoding="utf-8")
    return p


def bindir(base: Path, *engines: str) -> Path:
    d = base / ("bin-" + "-".join(engines or ("none",)))
    d.mkdir(exist_ok=True)
    for e in engines:
        (d / e).write_text(FAKE, encoding="utf-8")
        (d / e).chmod(0o755)
    return d


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    script = ROOT / ".tf" / "factory" / "container.py"
    check(script.is_file(), "IC-0: the engine has .tf/factory/container.py")
    check((ROOT / ".tf" / "factory" / "container" / "Dockerfile").is_file()
          and (ROOT / ".tf" / "factory" / "container" / "init_firewall.sh").is_file(),
          "IC-0b: the image files (Dockerfile, init_firewall.sh) are in the engine")
    if fails:
        for f in fails:
            print(f"✗ {f}")
        return 1
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        out = base / "argv.txt"

        def tf(p: Path, path: Path, *args: str, **extra: str) -> tuple[subprocess.CompletedProcess, list[str]]:
            out.unlink(missing_ok=True)
            env = {**CLEAN, "PATH": str(path), "TF_FAKE_OUT": str(out),
                   "HOME": str(base / "home"), **extra}
            r = subprocess.run([sys.executable, str(p / ".tf" / "factory" / "tf.py"), *args], cwd=p, capture_output=True,
                               text=True, timeout=120, env=env, stdin=subprocess.DEVNULL)
            return r, (out.read_text(encoding="utf-8").splitlines() if out.is_file() else [])

        p = project(base, "plain", "isolation_allow_domains:\n  - api.example.org\n  - 'bad domain; rm -rf /'\n")
        r, argv = tf(p, bindir(base, "docker"), "code", "--container", "--continue")
        joined = "\n".join(argv)
        mounts = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a in ("-v", "--volume")]
        env = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a in ("-e", "--env")]
        allow = next((e.split("=", 1)[1] for e in env if e.startswith("TF_ALLOW_DOMAINS=")), "")
        check(r.returncode == 0 and argv[:1] == ["run"] and "--rm" in argv,
              f"IC-1: tf code --container → `docker run --rm …`: {r.returncode} {argv[:6]} {r.stdout[-300:]}{r.stderr[-300:]}")
        check(f"{p.resolve()}:/workspace" in mounts and len([m for m in mounts if not m.startswith("tf-claude")]) == 1,
              f"IC-2: only the project is mounted from the host (plus the named volume): {mounts}")
        check(not any(s in joined for s in ("docker.sock", "/.ssh", "/.aws", "/.gitconfig", str(base / "home"))),
              f"IC-3: no Docker socket, home directory, ~/.ssh or ~/.gitconfig: {joined}")
        check(any(m.startswith("tf-claude") and m.endswith(":/home/node/.claude") for m in mounts),
              f"IC-4: a named volume for Claude's own files (login, history): {mounts}")
        check("--read-only" in argv and "NET_ADMIN" in joined and "--privileged" not in argv
              and "no-new-privileges" in joined,
              f"IC-5: read-only image filesystem, NET_ADMIN for the firewall only, no --privileged: {argv}")
        check("api.anthropic.com" in allow and "github.com" in allow and "api.example.org" in allow and "rm" not in allow,
              f"IC-6: allowed domains = fixed list + isolation_allow_domains (invalid entries dropped): {allow}")
        img = next((a for a in argv if a.startswith("tf-sandbox:")), "")
        version = (ROOT / ".tf" / "factory" / "VERSION").read_text(encoding="utf-8").strip()
        check(img == f"tf-sandbox:{version}", f"IC-7: the image is tf-sandbox:<factory version>: {img}")
        after = argv[argv.index(img) + 1:] if img in argv else []
        check(after[:1] == ["claude"] and "--plugin-dir" in after and "/workspace/.tf/plugin" in after
              and "/workspace/.tf/cache/session-settings.json" in after and after[-1:] == ["--continue"],
              f"IC-8: inside — claude with the factory plugin and the session settings, then your arguments: {after}")
        sess = json.loads((p / ".tf" / "cache" / "session-settings.json").read_text(encoding="utf-8"))
        check(sess.get("env") == {"A": "1"} and "sandbox" not in sess,
              f"IC-9: in the container the session settings carry no Bash sandbox (the container is the boundary): {sess}")
        check("TF_ISOLATION=container" in env and "CLAUDE_CONFIG_DIR=/home/node/.claude" in env,
              f"IC-10: TF_ISOLATION=container and Claude's config dir in the volume: {env}")

        q = project(base, "level", "isolation: container\n")
        r, argv = tf(q, bindir(base, "podman"), "code")
        check(r.returncode == 0 and argv[:1] == ["run"] and any(a.startswith("tf-sandbox:") for a in argv),
              f"IC-11: level container → tf code starts the container; Podman when only Podman is there: {argv[:4]} "
              f"{r.stdout[-300:]}{r.stderr[-300:]}")
        r, argv = tf(q, bindir(base, "docker", "podman"), "code", TF_CONTAINER_ENGINE="podman")
        check(r.returncode == 0 and argv[:1] == ["run"], f"IC-12: TF_CONTAINER_ENGINE chooses the engine: {argv[:3]}")
        r, argv = tf(q, bindir(base), "code")
        check(r.returncode == 2 and not argv and "Docker" in r.stdout + r.stderr and "Podman" in r.stdout + r.stderr,
              f"IC-13: no engine → a refusal naming Docker and Podman, nothing starts: {r.returncode} {r.stdout}{r.stderr}")
        r, argv = tf(q, bindir(base, "docker"), "code", TF_CONTAINER="1")
        check(r.returncode == 2 and not argv and "container" in r.stdout + r.stderr,
              f"IC-14: inside the container tf code does not start another container: {r.returncode} {r.stdout}{r.stderr}")

        # I5: after the session — the commits made in the container that wait for a push from this terminal
        remote = base / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        g = project(base, "gitproj", "isolation: container\n")
        gitenv = {**CLEAN, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                  "GIT_COMMITTER_EMAIL": "t@t"}
        for args in (["init", "-q", "-b", "main"], ["remote", "add", "origin", str(remote)],
                     ["commit", "-q", "--allow-empty", "-m", "a"], ["push", "-q", "-u", "origin", "main"],
                     ["commit", "-q", "--allow-empty", "-m", "b"], ["commit", "-q", "--allow-empty", "-m", "c"]):
            subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=g, check=True, env=gitenv, capture_output=True)
        gitbin = bindir(base, "docker")
        (gitbin / "git").write_text(f"#!/bin/sh\nexec {shutil.which('git')} \"$@\"\n", encoding="utf-8")
        (gitbin / "git").chmod(0o755)
        r, argv = tf(g, gitbin, "code")
        check(r.returncode == 0 and "2 commit" in r.stdout + r.stderr and "git push" in r.stdout + r.stderr,
              f"IC-17: after the session — how many commits wait for a push, and the command: {r.stdout}{r.stderr}")

    # the addresses: resolved once on the host and handed to the engine (--add-host), so /etc/hosts in the container,
    # the firewall and every program see the same address — round-robin DNS gave the firewall one and curl another
    import importlib.util
    import socket
    spec = importlib.util.spec_from_file_location("tf_container_t", ROOT / ".tf" / "factory" / "container.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    real = socket.getaddrinfo

    def fake(host, *a, **k):
        if host == "api.github.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("140.82.114.6", 443))]
        raise socket.gaierror("no such host in the test")
    socket.getaddrinfo = fake
    try:
        with tempfile.TemporaryDirectory() as t:
            args = mod.run_args(project(Path(t), "hosts"), [])
    finally:
        socket.getaddrinfo = real
    hosts = [args[i + 1] for i, a in enumerate(args[:-1]) if a == "--add-host"]
    check(hosts == ["api.github.com:140.82.114.6"],
          f"IC-18: the allowed domains' addresses resolved on the host go in as --add-host (unresolvable ones left out): {hosts}")

    df = (ROOT / ".tf" / "factory" / "container" / "Dockerfile").read_text(encoding="utf-8")
    check("@sha256:" in df and "claude-code@" in df and "TF_CONTAINER=1" in df,
          "IC-15: the Dockerfile pins the base image by digest and Claude Code by version, and sets TF_CONTAINER=1")
    fw = (ROOT / ".tf" / "factory" / "container" / "init_firewall.sh").read_text(encoding="utf-8")
    check("OUTPUT DROP" in fw and "TF_ALLOW_DOMAINS" in fw, "IC-16: the firewall drops outgoing traffic by default")
    check("/etc/hosts" not in fw.split("set -eu", 1)[-1] or ">> /etc/hosts" not in fw,
          "IC-16b: the firewall does not write /etc/hosts (read-only in the container; the engine writes it from --add-host)")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} container tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
