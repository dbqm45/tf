#!/usr/bin/env python3
"""The factory's session image (plan docs/plans/2026-11-20-poziomy-izolacji.md, slice I4), built and run with the
arguments `tf code --container` uses: the session runs as `node`, cannot write outside /workspace (and its tmpfs home),
cannot change the firewall, reaches an allowed domain and not one outside the list; Claude Code starts.
Needs Docker (or Podman via TF_CONTAINER_ENGINE) and the network, and takes minutes, so it runs only with
TF_CONTAINER_TEST=1 (the CI job `container` sets it); without a working engine it then fails.
TF_CONTAINER_TEST=1 python3 tests/test_container_image.py"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
PROBE = r"""
echo "user=$(id -un)"
touch /etc/tf-probe 2>/dev/null && echo "write_etc=OK" || echo "write_etc=DENIED"
touch /workspace/tf-probe 2>/dev/null && echo "write_workspace=OK" || echo "write_workspace=DENIED"
touch "$HOME/tf-probe" 2>/dev/null && echo "write_home=OK" || echo "write_home=DENIED"
iptables -P OUTPUT ACCEPT 2>/dev/null && echo "firewall_change=OK" || echo "firewall_change=DENIED"
curl -s -o /dev/null -m 10 https://api.github.com && echo "allowed_domain=OK" || echo "allowed_domain=DENIED"
curl -s -o /dev/null -m 10 https://example.com && echo "other_domain=OK" || echo "other_domain=DENIED"
claude --version >/dev/null 2>&1 && echo "claude=OK" || echo "claude=MISSING"
echo "tf_container=$TF_CONTAINER"
"""
WANT = {"user": "node", "write_etc": "DENIED", "write_workspace": "OK", "write_home": "OK", "firewall_change": "DENIED",
        "allowed_domain": "OK", "other_domain": "DENIED", "claude": "OK", "tf_container": "1"}


def main() -> int:
    if os.environ.get("TF_CONTAINER_TEST") != "1":
        print("ℹ the image test runs with TF_CONTAINER_TEST=1 (CI job `container`) — skipped")
        return 0
    eng = shutil.which(os.environ.get("TF_CONTAINER_ENGINE") or "docker") or shutil.which("podman")
    if not eng or subprocess.run([eng, "info"], capture_output=True).returncode != 0:
        print("✗ no working container engine (Docker or Podman)")
        return 1
    spec = importlib.util.spec_from_file_location("tf_container_image", ROOT / "core" / "factory" / "container.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as t:
        proj = Path(t) / "proj"
        (proj / ".tf" / "factory").mkdir(parents=True)
        shutil.copy(ROOT / "core" / "factory" / "VERSION", proj / ".tf" / "factory" / "VERSION")
        os.chmod(proj, 0o777)                                  # the container's `node` user writes in /workspace
        tag = mod.image(proj)
        b = subprocess.run([eng, "build", "-t", tag, str(ROOT / "core" / "factory" / "container")],
                           capture_output=True, text=True, timeout=1800)
        if b.returncode != 0:
            print(f"✗ CI-0: the image builds: {b.stdout[-1500:]}{b.stderr[-1500:]}")
            return 1
        args = mod.run_args(proj, [])
        args = args[:args.index(tag) + 1] + ["sh", "-c", PROBE]
        r = subprocess.run([eng, *args], capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
        got = dict(line.split("=", 1) for line in r.stdout.splitlines() if "=" in line)
        print(json.dumps(got))
        fails = [f"{k}: want {v}, got {got.get(k)}" for k, v in WANT.items() if got.get(k) != v]
        if not (proj / "tf-probe").is_file():
            fails.append("the file written in /workspace is not in the project on the host")
    for f in fails:
        print(f"✗ {f}")
    if r.returncode != 0 and not fails:
        fails.append(f"exit {r.returncode}: {r.stderr[-800:]}")
        print(f"✗ {fails[-1]}")
    print(f"{'✓' if not fails else '✗'} {len(WANT) + 1 - len(fails)}/{len(WANT) + 1} container image checks")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
