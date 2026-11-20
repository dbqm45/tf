#!/usr/bin/env python3
"""Standards skills from a git repository by URL (`dna.py standards add`, cloned in cache/standards/).
python3 addons/dna/tests/test_standards_git.py — the repository is a local one (file://), no network."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

from lib import verify  # noqa: E402
from test_dna import repo  # noqa: E402


def standards_repo() -> Path:
    r = repo({"skills/acme-fe-standards/SKILL.md": "# FE\n- FE-001: Forms must use react-hook-form.\n",
              "skills/acme-be-standards/SKILL.md": "# BE\n- Services must log with the request id.\n",
              "README.md": "# Standards repo\n"})
    for args in (["init", "-q"], ["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "s"],
                 ["tag", "v1.0.0"]):
        subprocess.run(["git", *args], cwd=r, check=True, capture_output=True)
    return r


def run(root: Path, cfg: Path, *args) -> subprocess.CompletedProcess:
    env = {**os.environ, "DNA_CONFIG": str(cfg), "DNA_OFFLINE": "0"}
    return subprocess.run([sys.executable, str(ADDON / "dna.py"), *args, "--root", str(root), "--out",
                           str(root / ".tf/addons/dna/out"), "--cache", str(root / ".tf/addons/dna/cache")],
                          capture_output=True, text=True, env=env)


def test_add_by_url_learn_and_evidence():
    std = standards_repo()
    root = repo({"package.json": '{"name": "app"}'})
    cfg = Path(tempfile.mkdtemp()) / "dna.yaml"
    url = std.as_uri()
    r = run(root, cfg, "standards", "add", url, "--ref", "v1.0.0", "--dir", "skills")
    assert r.returncode == 0, r.stderr
    assert "v1.0.0" in run(root, cfg, "standards", "list").stdout
    r = run(root, cfg, "learn")
    assert r.returncode == 0, r.stdout + r.stderr
    out = root / ".tf/addons/dna/out"
    assert verify.check_out(out, root) == []
    k = json.loads((out / "knowledge.json").read_text(encoding="utf-8"))
    d = {i["title"]: i for i in k["items"] if i["kind"] == "decision"}
    fe = d["Forms must use react-hook-form"]
    assert fe["status"] == "auto-accepted" and fe["data"]["rule_id"] == "FE-001"
    assert fe["evidence"][0].startswith(f"{url}#v1.0.0:skills/acme-fe-standards/SKILL.md:L2 (fetched ")
    assert "**/*.tsx" in fe["scope"]["paths"]                                 # fe from the skill's name
    assert "**/*.py" in d["Services must log with the request id"]["scope"]["paths"]
    assert "Forms must use react-hook-form" in (out / "rules" / "standards-fe.md").read_text(encoding="utf-8")
    # offline later: the cached clone is used
    env = {**os.environ, "DNA_CONFIG": str(cfg), "DNA_OFFLINE": "1"}
    r2 = subprocess.run([sys.executable, str(ADDON / "dna.py"), "learn", "--root", str(root), "--out", str(out),
                         "--cache", str(root / ".tf/addons/dna/cache")], capture_output=True, text=True, env=env)
    assert r2.returncode == 0 and "Forms must use" in (out / "decisions.md").read_text(encoding="utf-8")
    assert run(root, cfg, "standards", "remove", url).returncode == 0
    assert "no standards configured" in run(root, cfg, "standards", "list").stdout


def test_bad_url_is_reported_not_fatal():
    root = repo({"package.json": '{"name": "app"}'})
    cfg = Path(tempfile.mkdtemp()) / "dna.yaml"
    run(root, cfg, "standards", "add", "file:///nonexistent/repo.git")
    r = run(root, cfg, "learn")
    assert r.returncode == 0, r.stderr
    cov = (root / ".tf/addons/dna/out/coverage.md").read_text(encoding="utf-8")
    assert "file:///nonexistent/repo.git: git clone failed" in cov


def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ {name}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"✗ {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
