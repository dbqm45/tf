"""Shared parts of tf stress: the library loader, project preparation, the factory install and fault injection."""
from __future__ import annotations

import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # the factory repository
STRESS = ROOT / "tools" / "stress"
LIBRARY = STRESS / "library"
CORPUS = STRESS / "corpus"
FIXTURES = STRESS / "fixtures"
CHECKS = STRESS / "checks"
sys.path.insert(0, str(ROOT / "core" / "factory" / "_vendor"))
import yaml  # noqa: E402  (the factory's vendored PyYAML)

SESSION_VARS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT", "CLAUDE_PID", "CLAUDE_CODE_CHILD_SESSION")
GIT_ID = ["-c", "user.name=tf-stress", "-c", "user.email=tf-stress@example.invalid"]

CATEGORIES = ("Intake", "Weight & mode", "Loop speed", "Safety stops", "Environment", "Edge input", "Concurrency",
              "Hooks", "Gates", "Scale", "Install")
SCENARIO_KEYS = {"id", "name", "category", "engine", "tags", "description", "fixture", "probe", "corpus", "params",
                 "input", "mode", "setup", "budget", "model", "expect", "timeout", "layout", "check", "sizes"}
EXPECT_KEYS = {"outcome", "weight", "check", "max_wall", "max_cost", "max_turns", "max_files", "forbid", "stop",
               "min_accuracy", "max_p95_ms", "max_p50_ms", "max_under", "max_false_deny", "max_errors", "max_ms",
               "no_code", "commits_min", "max_tool_errors", "max_denials"}
FAULTS = {"dirty_tree", "no_scanner", "slow_tests", "red_main", "flaky_test", "no_gate", "big_repo", "feature_branch",
          "story_file", "env", "remote", "tdd_off", "detached_head", "readonly_file", "huge_file", "unicode_paths",
          "no_lockfile_dep", "deep_tree"}


# Secret-shaped test values, assembled at run time so that the repository holds no literal a secret scanner (or
# GitHub push protection) would flag. `{fake:<kind>}` in a corpus or a scenario input becomes one of these.
FAKE_SECRETS = {
    "aws": "AK" + "IA" + "Q3EGRT7LMN2PXZ4K",
    "github": "gh" + "p_" + "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
    "stripe": "sk" + "_live_" + "51HxYzAbCdEfGhIjKlMnOpQr",
    "anthropic": "sk" + "-ant-" + "api03-AbCdEfGhIjKlMnOpQrStUvWxYz",
    "npm": "np" + "m_" + "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789",
    "private_key": "-----BEGIN OPENSSH " + "PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAA\n-----END OPENSSH " + "PRIVATE KEY-----\n",
}


def fake(text):
    if isinstance(text, str):
        return re.sub(r"\{fake:(\w+)\}", lambda m: FAKE_SECRETS[m.group(1)], text)
    if isinstance(text, dict):
        return {k: fake(v) for k, v in text.items()}
    if isinstance(text, list):
        return [fake(v) for v in text]
    return text


def load_yaml(path: Path) -> dict:
    return fake(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def duration(v) -> float | None:
    """'90s', '2m', '1h', 30 → seconds."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.fullmatch(r"\s*([\d.]+)\s*(ms|s|m|h)?\s*", str(v))
    if not m:
        raise ValueError(f"bad duration {v!r}")
    n, unit = float(m.group(1)), m.group(2) or "s"
    return n * {"ms": 0.001, "s": 1, "m": 60, "h": 3600}[unit]


def load_library(errors: list[str] | None = None) -> list[dict]:
    """Every scenario in tools/stress/library/*.yaml; unknown keys, faults or duplicate ids are errors
    (a typo must not silently switch a check off)."""
    out, seen = [], set()
    errors = errors if errors is not None else []
    for f in sorted(LIBRARY.glob("*.yaml")):
        doc = load_yaml(f)
        for s in doc.get("scenarios", [doc] if "id" in doc else []):
            sid = s.get("id", f"?{f.name}")
            bad = set(s) - SCENARIO_KEYS
            if bad:
                errors.append(f"{sid}: unknown keys {sorted(bad)}")
            bad = set(s.get("expect") or {}) - EXPECT_KEYS
            if bad:
                errors.append(f"{sid}: unknown expect keys {sorted(bad)}")
            for st in s.get("setup") or []:
                if (st or {}).get("fault") not in FAULTS:
                    errors.append(f"{sid}: unknown fault {st!r}")
            if s.get("category") not in CATEGORIES:
                errors.append(f"{sid}: unknown category {s.get('category')!r}")
            if s.get("engine") not in ("mech", "model"):
                errors.append(f"{sid}: engine must be mech or model")
            if sid in seen:
                errors.append(f"{sid}: duplicate id")
            seen.add(sid)
            s.setdefault("tags", [])
            s["_file"] = f.name
            out.append(s)
    return out


def select(scenarios: list[dict], suite: str | None, ids: list[str] | None, engine: str | None) -> list[dict]:
    out = scenarios
    if ids:
        want = {i.upper() for i in ids}
        out = [s for s in out if s["id"].upper() in want or s.get("name") in ids]
    if suite and suite != "all":
        out = [s for s in out if suite in s["tags"] or s["category"].lower() == suite.lower()]
    if engine and engine != "all":
        out = [s for s in out if s["engine"] == engine]
    return out


def clean_env(extra: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in SESSION_VARS}
    env["TF_NO_PLUGIN_REGISTER"] = "1"
    env.update(extra or {})
    return env


def run(cmd, cwd, env=None, timeout=None, inp=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), env=env, timeout=timeout, capture_output=True, text=True, input=inp,
                          stdin=None if inp is not None else subprocess.DEVNULL)


def git(cwd, *args) -> subprocess.CompletedProcess:
    return run(["git", *GIT_ID, *args], cwd)


def pct(values: list[float], q: float) -> float | None:
    v = sorted(values)
    if not v:
        return None
    return v[min(len(v) - 1, int(round(q * (len(v) - 1))))]


def stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    return {"n": len(values), "p50": round(statistics.median(values), 1), "p95": round(pct(values, .95), 1),
            "max": round(max(values), 1), "sum": round(sum(values), 1)}


# --- projects -------------------------------------------------------------------------------------------------

_TEMPLATES: dict[tuple, Path] = {}


def template(fixture: str, work: Path, layout: str = "default", packs: str = "none") -> Path:
    """The fixture committed in a fresh git repository with the factory installed and onboarded, built once per
    (fixture, layout, packs) and copied for each scenario — the install is not what most scenarios measure."""
    key = (fixture, layout, packs)
    if key in _TEMPLATES:
        return _TEMPLATES[key]
    dest = work / "_templates" / f"{fixture}-{layout}-{packs}"
    if dest.exists():
        shutil.rmtree(dest)
    src = FIXTURES / fixture if (FIXTURES / fixture).is_dir() else ROOT / "tools" / "bench" / "fixture"
    shutil.copytree(src, dest)
    if (dest / "_quality-gate.json").exists():            # the bench fixture keeps its gate config aside
        (dest / ".claude").mkdir(exist_ok=True)
        (dest / "_quality-gate.json").rename(dest / ".claude" / "quality-gate.json")
    git(dest, "init", "-q", "-b", "main")
    git(dest, "add", "-A")
    git(dest, "commit", "-qm", "feat: initial fixture")
    t = time.time()
    p = run([sys.executable, str(ROOT / "core/factory/install.py"), "--yes", "--packs", packs, "--layout", layout],
            dest, env=clean_env(), timeout=600)
    if p.returncode:
        raise RuntimeError(f"install failed: {(p.stdout + p.stderr)[-800:]}")
    install_s = time.time() - t
    if not (dest / ".claude" / "quality-gate.json").exists():
        run([sys.executable, ".tf/factory/tf.py", "onboard", "--yes"], dest, env=clean_env(), timeout=300)
    (dest / ".stress-install.json").write_text(json.dumps({"install_s": round(install_s, 2)}))
    git(dest, "config", "user.name", "tf-stress")
    git(dest, "config", "user.email", "tf-stress@example.invalid")
    excl = dest / ".git" / "info" / "exclude"
    excl.write_text(excl.read_text() + "\n.stress-install.json\n.stress/\n")
    _TEMPLATES[key] = dest
    return dest


def copy_project(tpl: Path, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(tpl, dest, symlinks=True)
    return dest


# --- faults ---------------------------------------------------------------------------------------------------

def _write(proj: Path, rel: str, text: str) -> None:
    p = proj / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _commit(proj: Path, msg: str) -> None:
    git(proj, "add", "-A")
    git(proj, "commit", "-qm", msg)


def nosemgrep_path(work: Path, path: str) -> str:
    """PATH without the semgrep binary (a directory of symlinks to everything else in its directory)."""
    which = shutil.which("semgrep", path=path)
    if not which:
        return path
    src = Path(which).parent
    d = work / "_nosemgrep"
    if not d.exists():
        d.mkdir(parents=True)
        for p in src.iterdir():
            if not p.name.startswith(("semgrep", "pysemgrep", "osemgrep")):
                try:
                    (d / p.name).symlink_to(p)
                except OSError:
                    pass
    return ":".join(str(d) if x == str(src) else x for x in path.split(":"))


def apply_faults(proj: Path, setup: list[dict], env: dict, work: Path, fixture: str) -> list[str]:
    """Injects the scenario's faults into the project copy (and its environment); returns what was done."""
    node = fixture == "node-tasks"
    done = []
    for f in setup or []:
        kind = f["fault"]
        if kind == "dirty_tree":
            target = "src/store.js" if node else "app/pricing.py"
            with open(proj / target, "a", encoding="utf-8") as fh:
                fh.write("// uncommitted work of a human\n" if node else "# uncommitted work of a human\n")
        elif kind == "no_scanner":
            env["PATH"] = nosemgrep_path(work, env.get("PATH", ""))
        elif kind == "slow_tests":
            s = float(f.get("seconds", 15))
            if node:
                _write(proj, "test/slow.test.js", "import { test } from \"node:test\";\n\ntest(\"slow integration\", async () => {\n"
                       f"  await new Promise((r) => setTimeout(r, {int(s * 1000)}));\n}});\n")
            else:
                _write(proj, "tests/test_slow.py", f"import time\nimport unittest\n\n\nclass Slow(unittest.TestCase):\n"
                       f"    def test_slow(self):\n        time.sleep({s})\n")
            _commit(proj, "test: slow integration test")
        elif kind == "red_main":
            if node:
                _write(proj, "test/broken.test.js", "import { test } from \"node:test\";\nimport assert from \"node:assert/strict\";\n\n"
                       "test(\"legacy rounding\", () => {\n  assert.equal(0.1 + 0.2, 0.3);\n});\n")
            else:
                _write(proj, "tests/test_broken.py", "import unittest\n\n\nclass Broken(unittest.TestCase):\n"
                       "    def test_rounding(self):\n        self.assertEqual(0.1 + 0.2, 0.3)\n")
            _commit(proj, "test: legacy rounding test")
        elif kind == "flaky_test":
            p = float(f.get("fail_rate", 0.5))
            _write(proj, "test/flaky.test.js", "import { test } from \"node:test\";\nimport assert from \"node:assert/strict\";\n\n"
                   f"test(\"flaky network\", () => {{\n  assert.ok(Math.random() >= {p});\n}});\n")
            _commit(proj, "test: network check")
        elif kind == "no_gate":
            for g in (".claude/quality-gate.json",):
                (proj / g).unlink(missing_ok=True)
        elif kind == "big_repo":
            n = int(f.get("files", 1500))
            for i in range(n):
                ext = "js" if node else "py"
                body = (f"// legacy module {i}\nexport function legacy{i}(store) {{\n  return store.list().length + {i};\n}}\n"
                        if node else f"# legacy module {i}\ndef legacy_{i}(store):\n    return len(store) + {i}\n")
                _write(proj, f"{'src' if node else 'app'}/legacy/m{i // 100}/mod{i}.{ext}", body)
            _commit(proj, f"chore: {n} legacy modules")
        elif kind == "huge_file":
            lines = int(f.get("lines", 20000))
            target = "src/generated_table.js" if node else "app/generated_table.py"
            row = "export const ROW_{i} = {{ id: {i}, label: \"row {i}\" }};\n" if node else "ROW_{i} = {{'id': {i}}}\n"
            _write(proj, target, "".join(row.format(i=i) for i in range(lines)))
            _commit(proj, "chore: generated table")
        elif kind == "deep_tree":
            d = "src" if node else "app"
            _write(proj, f"{d}/" + "/".join(f"l{i}" for i in range(int(f.get("depth", 25)))) + ("/x.js" if node else "/x.py"),
                   "// deep\n")
            _commit(proj, "chore: deep tree")
        elif kind == "unicode_paths":
            _write(proj, "docs/zażółć gęślą/notatka ąę.md", "# Notatka\n")
            _commit(proj, "docs: unicode note")
        elif kind == "feature_branch":
            git(proj, "switch", "-q", "-c", f.get("name", "feature/wip"))
        elif kind == "detached_head":
            git(proj, "checkout", "-q", "--detach")
        elif kind == "story_file":
            _write(proj, f["path"], f["text"])
            _commit(proj, "docs: story")
        elif kind == "env":
            env.update({k: str(v) for k, v in (f.get("vars") or {}).items()})
        elif kind == "tdd_off":
            env["CLAUDE_TDD"] = "off"
        elif kind == "remote":
            bare = work / "_remotes" / proj.name
            if bare.exists():
                shutil.rmtree(bare)
            bare.parent.mkdir(parents=True, exist_ok=True)
            run(["git", "init", "-q", "--bare", str(bare)], work)
            git(proj, "remote", "add", "origin", str(bare))
            git(proj, "push", "-q", "-u", "origin", "main")
        elif kind == "readonly_file":
            p = proj / f["path"]
            p.chmod(0o444)
        elif kind == "no_lockfile_dep":
            pj = json.loads((proj / "package.json").read_text())
            pj.setdefault("dependencies", {})["left-pad"] = "^1.3.0"
            (proj / "package.json").write_text(json.dumps(pj, indent=2) + "\n")
            _commit(proj, "chore: add dependency")
        done.append(kind)
    return done
