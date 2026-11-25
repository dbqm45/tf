#!/usr/bin/env python3
"""Edge cases of add-ons (core/factory/addons.py): a broken addon.yaml (plain text, a list of `provides`, not UTF-8),
a wrong contract and a name that differs from the directory never stop `tf addon list`, `sync`, `check` or `tf learn`;
`tf learn` without network (an add-on declared with `install: true` cannot be fetched) still runs the other add-ons'
`learn`; `sync` keeps the line ending of the instructions file; a declared add-on with an invalid name is ignored.
python3 tests/test_addon_edges.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
ADDONS_PY = ROOT / "core" / "factory" / "addons.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def project(base: Path, name: str, mode: str = "private", source: str | None = None) -> Path:
    p = base / name
    p.mkdir()
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    man = {"mode": mode, **({"source": source} if source else {})}
    write(p / ".claude" / "factory-manifest.json", json.dumps(man))
    shutil.copytree(ROOT / "core" / "factory" / "_vendor", p / ".tf" / "factory" / "_vendor")
    return p


def put_addon(p: Path, name: str, yaml_bytes: bytes, extra: dict | None = None) -> Path:
    d = p / ".tf" / "addons" / name
    d.mkdir(parents=True)
    (d / "addon.yaml").write_bytes(yaml_bytes)
    for rel, text in (extra or {}).items():
        write(d / rel, text)
    return d


def addons(p: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DNA_OFFLINE": "1", "STANDARDS_OFFLINE": "1", "GIT_TERMINAL_PROMPT": "0"}
    return subprocess.run([sys.executable, str(ADDONS_PY), *args], cwd=p, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, timeout=300)


def out(r: subprocess.CompletedProcess) -> str:
    return r.stdout + r.stderr


GOOD = (b'{"name": "good", "version": "1.0.0", "contract": 1, '
        b'"provides": {"learn": "learn.py", "context": "out/GUIDE.md", "check": "check.py"}}')
LEARN = "import pathlib\np = pathlib.Path(__file__).parent / 'out'\np.mkdir(exist_ok=True)\n" \
        "(p / 'GUIDE.md').write_text('# guide\\n', encoding='utf-8')\nprint('learned')\n"


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)

        # AE-1..AE-4: broken add-ons next to a good one — every command goes on, each broken one is reported with
        # what to do; before, plain text and a non-UTF-8 file crashed `tf addon list` (and tf doctor, tf learn)
        p = project(base, "broken")
        put_addon(p, "good", GOOD, {"learn.py": LEARN, "check.py": "print('{}')\n"})
        put_addon(p, "text", b"just some text\n")                                       # AE-1: not a mapping
        put_addon(p, "listy", b"name: listy\ncontract: 1\nprovides: [learn, check]\n")  # AE-2: provides as a list
        put_addon(p, "latin", "name: latin\ncontract: 1\n# zażółć\n".encode("cp1250"))   # AE-3: not UTF-8
        put_addon(p, "future", b"name: future\ncontract: 2\nprovides: {learn: x.py}\n")   # AE-4: another contract
        put_addon(p, "other", b"name: renamed\ncontract: 1\nprovides: {}\n")             # AE-4b: name mismatch
        r = addons(p, "list")
        o = out(r)
        check(r.returncode == 0 and "Traceback" not in o and "✓ good" in o,
              f"AE-1..4: tf addon list with broken add-ons: {r.returncode} {o[-900:]}")
        check("text" in o and "not a mapping" in o and "tf addon add" in o, f"AE-1: plain-text addon.yaml: {o[-900:]}")
        check("listy" in o and o.count("not a mapping") >= 2, f"AE-2: provides as a list: {o[-900:]}")
        check("latin" in o and "unreadable" in o, f"AE-3: a non-UTF-8 addon.yaml: {o[-900:]}")
        check("contract 2" in o and "differs from the directory" in o, f"AE-4: contract and name: {o[-900:]}")
        r = addons(p, "list", "--json")
        try:
            rows = {x["name"]: x for x in json.loads(r.stdout)}
        except ValueError:
            rows = {}
        check(rows.get("good", {}).get("ok") is True and all(rows.get(n, {}).get("ok") is False and rows[n]["problem"]
                                                             for n in ("text", "listy", "latin", "future", "other")),
              f"AE-1..4: --json marks each broken one with its problem: {r.stdout[-600:]}")
        r = addons(p, "learn")
        o = out(r)
        check(r.returncode == 0 and "Traceback" not in o and "learned" in o
              and (p / ".tf" / "addons" / "good" / "out" / "GUIDE.md").is_file(),
              f"AE-1..4: tf learn runs the good add-on: {r.returncode} {o[-600:]}")
        r = addons(p, "sync")
        local = (p / "CLAUDE.local.md").read_text(encoding="utf-8") if (p / "CLAUDE.local.md").is_file() else ""
        check(r.returncode == 0 and "@.tf/addons/good/out/GUIDE.md" in local and "text" in out(r) and "skipped" in out(r),
              f"AE-1..4: sync wires the good one and says which are skipped: {out(r)[-500:]} {local[-300:]}")
        r = addons(p, "check")
        check(r.returncode == 0 and "Traceback" not in out(r) and "good" in out(r),
              f"AE-1..4: tf addon check: {r.returncode} {out(r)[-400:]}")
        st = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import addons; "
                             "from pathlib import Path; print(len(addons.status(Path(sys.argv[2]))))",
                             str(ROOT / "core" / "factory"), str(p)], capture_output=True, text=True)
        check(st.stdout.strip() == "5", f"AE-1..4: status() (tf doctor) lists the 5 broken ones: {st.stdout}{st.stderr}")
        r = addons(p, "remove", "text")
        check(r.returncode == 0 and not (p / ".tf" / "addons" / "text").exists(),
              f"AE-1: a broken add-on can be removed: {out(r)[-300:]}")

        # AE-5: adding from a directory with a broken addon.yaml: refused with the reason, nothing copied
        src = base / "src-broken" / "brk"
        write(src / "addon.yaml", "- a\n- b\n")
        r = addons(p, "add", str(src))
        check(r.returncode == 2 and "Traceback" not in out(r) and "not a mapping" in out(r)
              and not (p / ".tf" / "addons" / "brk").exists(),
              f"AE-5: add of a broken add-on refused: {r.returncode} {out(r)[-400:]}")

        # AE-6: tf learn without network: an add-on declared with `install: true` cannot be fetched from the factory's
        # git source — a warning with what to do, and the installed add-ons still learn (before: learn stopped there)
        q = project(base, "offline", source="https://127.0.0.1:9/tf.git")
        put_addon(q, "good", GOOD, {"learn.py": LEARN, "check.py": "print('{}')\n"})
        write(q / ".tf" / "config" / "config.yaml", "addons:\n  dna:\n    install: true\n")
        shutil.copytree(ROOT / "core" / "factory", q / ".tf" / "engine", ignore=shutil.ignore_patterns("__pycache__"))
        env = {**os.environ, "DNA_OFFLINE": "1", "GIT_TERMINAL_PROMPT": "0"}
        r = subprocess.run([sys.executable, str(q / ".tf" / "engine" / "addons.py"), "learn"], cwd=q,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
        o = out(r)
        check("Traceback" not in o and "dna" in o and "could not be installed" in o and "tf learn again" in o
              and "learned" in o and (q / ".tf" / "addons" / "good" / "out" / "GUIDE.md").is_file(),
              f"AE-6: learn without network still runs the other add-ons: {r.returncode} {o[-900:]}")

        # AE-7: sync keeps the line ending of the instructions file — a committed CRLF CLAUDE.md stays CRLF (before:
        # every line became LF), an LF one stays LF
        for name, eol in (("crlf", b"\r\n"), ("lf", b"\n")):
            c = project(base, f"eol-{name}", mode="shared")
            (c / "CLAUDE.md").write_bytes(b"# Team rules" + eol + b"- one" + eol)
            put_addon(c, "good", GOOD, {"out/GUIDE.md": "# g\n"})
            r = addons(c, "sync")
            data = (c / "CLAUDE.md").read_bytes()
            lone_lf = data.replace(b"\r\n", b"").count(b"\n")
            check(r.returncode == 0 and b"tf-addons:begin" in data and data.startswith(b"# Team rules" + eol)
                  and (lone_lf == 0 if name == "crlf" else b"\r\n" not in data),
                  f"AE-7: sync keeps {name}: {data[:120]!r}")
            r = addons(c, "remove", "good")
            data = (c / "CLAUDE.md").read_bytes()
            check(r.returncode == 0 and data == b"# Team rules" + eol + b"- one" + eol,
                  f"AE-7: remove unwires and keeps {name}: {data!r}")

        # AE-8: a declared add-on whose name is not a valid add-on name is ignored (no clone, no path tricks)
        d = project(base, "declared-bad", source=str(base / "no-such-factory"))
        write(d / ".tf" / "config" / "config.yaml", "addons:\n  \"../evil\":\n    install: true\n  Bad_Name:\n"
                                                     "    install: true\n")
        shutil.copytree(ROOT / "core" / "factory", d / ".tf" / "engine", ignore=shutil.ignore_patterns("__pycache__"))
        r = subprocess.run([sys.executable, str(d / ".tf" / "engine" / "addons.py"), "learn"], cwd=d,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        check(r.returncode == 0 and "evil" not in out(r) and "Bad_Name" not in out(r) and "No installed add-on" in out(r),
              f"AE-8: invalid declared names ignored: {r.returncode} {out(r)[-400:]}")

        # AE-9: removing an add-on that is not there: refused with the list command
        r = addons(d, "remove", "nothing-here")
        check(r.returncode == 2 and "No add-on" in out(r) and "tf addon list" in out(r), f"AE-9: remove of a missing add-on: {out(r)[-300:]}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} add-on edge cases")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
