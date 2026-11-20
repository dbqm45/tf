#!/usr/bin/env python3
"""
tf addon — add-ons: independent packages of the project in one directory each (`.tf/addons/<name>/`), which the
factory uses through a fixed contract (`addon.yaml`, contract 1). The core does not know any add-on by name.

  tf addon list [--json]                 # installed add-ons, contract compatibility, output state
  tf addon add <path | git URL | name>   # copy an add-on into .tf/addons/<name>/ (a bare name: from the factory source)
  tf addon remove <name>                 # remove the directory and everything sync wired in
  tf addon sync                          # wire the output into the project (also run by build.py)
  tf addon check [--base <ref>] [--json] # each add-on's `check` on the current change; exit 1 when one blocks
  tf addon run <name> <provides-key> [args…]
  tf learn [<name>]                      # each add-on's `learn`, then sync
  tf addon refresh                       # each add-on's `refresh` (cheap when nothing changed), then sync;
                                         # the SessionStart hook addons_refresh.py runs it in the background

Contract 1 (`provides` in addon.yaml; every key optional):
  context  — a file read in every session: sync puts one import line `@<path>` in the factory's add-on block of the
             instructions file (CLAUDE.md in a team install, CLAUDE.local.md in a private one);
  context_extra — more such files;
  rules    — a directory of rule files with `paths`: sync copies them to .claude/rules/addon-<name>-<file>.md;
  skill_overrides — a JSON file {skill: "name-only" | "off" | …}: merged into .claude/settings.local.json
             `skillOverrides`; removed again on `remove` when the value is still the one the add-on set;
  plan     — a file the task's scout and plan read (listed by `tf addon list --json`);
  decisions — a JSON file {"contract": 1, "decisions": [...]} of agreed rules; an add-on that lists
             `consumes: [decisions]` gets the paths of the other add-ons' files in TF_ADDON_DECISIONS (os.pathsep);
  pending  — a JSON file {"instructions": "...", "items": [{"tool", "save_to", "reason", …}]}: work only the
             session can do — `tool` names a tool connected through MCP (e.g. confluence: `url`) or `model` (the
             cheapest model as a subagent: `prompt` and `input` files, tier `fast`); listed by `tf addon list`,
             announced at session start;
  learn, check, refresh, … — commands: the first word is a script in the add-on directory, run with the current
             Python from the project root; `{base}` is replaced by the base ref.
Settings from the factory's configuration layers (engine ← company pack `org_defaults.config` ← team pack
`team_defaults.config` ← project `.tf/config/config.yaml` ← person), key `addons.<name>`: the core merges them and
passes the result to the add-on in TF_ADDON_SETTINGS (JSON). Dictionaries merge across layers (keyed entries add
up; a lower layer overrides a key), lists are replaced. `addons.<name>.install: true` makes `tf learn` install the
add-on from the factory source when it is missing — a company pack can roll an add-on out to all its projects.
`keep` (list) in addon.yaml: paths in the add-on directory that `add` over an existing copy keeps (default: out,
cache). An add-on with another contract, a broken addon.yaml or a failing command never stops the factory: it is
reported (`tf addon list`, `tf doctor`) and skipped. Standard library + PyYAML.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

os.environ.setdefault("PYTHONUTF8", "1")  # child processes read and write UTF-8 too
sys.dont_write_bytecode = True
_HERE = Path(__file__).resolve().parent
if str(_HERE / "_vendor") not in sys.path and (_HERE / "_vendor").is_dir():
    sys.path.append(str(_HERE / "_vendor"))
import yaml  # noqa: E402

CONTRACT = 1
ADDONS = Path(".tf") / "addons"
STATE = ADDONS / ".applied.json"
BEGIN, END = "<!-- tf-addons:begin (tf addon sync — do not edit by hand) -->", "<!-- tf-addons:end -->"
NAME = re.compile(r"^[a-z][a-z0-9-]{1,40}$")
DEFAULT_KEEP = ("out", "cache")
SKIP_COPY = {"__pycache__", ".git", "out", "cache", "tests", "fixtures"}
TIMEOUT = int(os.environ.get("TF_ADDON_TIMEOUT", "900"))


# ---------------------------------------------------------------- discovery

def load(d: Path) -> dict:
    """{name, dir, meta, ok, problem}. Never raises."""
    info = {"name": d.name, "dir": d, "meta": {}, "ok": False, "problem": None}
    try:
        meta = yaml.safe_load((d / "addon.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        info["problem"] = f"addon.yaml unreadable: {e}"
        return info
    info["meta"] = meta
    if meta.get("contract") != CONTRACT:
        info["problem"] = f"contract {meta.get('contract')!r}, this factory supports {CONTRACT}"
    elif meta.get("name") != d.name:
        info["problem"] = f"name {meta.get('name')!r} differs from the directory {d.name!r}"
    else:
        info["ok"] = True
    return info


def installed(root: Path) -> list[dict]:
    base = root / ADDONS
    if not base.is_dir():
        return []
    return [load(d) for d in sorted(base.iterdir()) if d.is_dir() and (d / "addon.yaml").is_file()]


def _provides(a: dict) -> dict:
    return a["meta"].get("provides") or {}


# ---------------------------------------------------------------- state and git

def _state(root: Path) -> dict:
    try:
        return json.loads((root / STATE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(root: Path, state: dict):
    path = root / STATE
    if not state:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _mode(root: Path) -> str:
    try:
        return json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get("mode") \
            or "private"
    except (OSError, ValueError):
        return "private"


def _instructions(root: Path) -> Path:
    return root / ("CLAUDE.md" if _mode(root) == "shared" else "CLAUDE.local.md")


def _ignore(root: Path, lines: list[str]):
    """Private install: .git/info/exclude (nothing visible in the repo); team install: .gitignore."""
    if _mode(root) == "shared":
        target = root / ".gitignore"
    else:
        try:
            r = subprocess.run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=root, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=10)
        except (OSError, subprocess.SubprocessError):
            return
        if r.returncode != 0:
            return
        target = (root / r.stdout.strip()).resolve()
    have = set(target.read_text(encoding="utf-8").splitlines()) if target.exists() else set()
    new = [ln for ln in lines if ln not in have]
    if new:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as f:
            f.write(("" if not have or target.read_text(encoding="utf-8").endswith("\n") else "\n")
                    + "\n".join(new) + "\n")


# ---------------------------------------------------------------- sync

def _block(text: str, body: str) -> str:
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)
    if not body:   # remove the block and the blank line sync put before it
        new = re.sub(r"\n*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "\n", text, flags=re.S)
        return new.rstrip("\n") + "\n" if new.strip() else ""
    block = f"{BEGIN}\n{body}\n{END}\n"
    if pattern.search(text):
        return pattern.sub(lambda m: block, text)
    return text + ("" if not text or text.endswith("\n") else "\n") + ("\n" if text else "") + block


def sync(root: Path, quiet: bool = False) -> list[str]:
    """Wire every compatible add-on's output into the project; remove what an add-on no longer provides.
    With no add-ons and nothing wired before, nothing is written. Returns notes for the human."""
    notes = []
    addons = [a for a in installed(root) if a["ok"]]
    state = _state(root)
    # 1. instructions file: one import line per context file that exists
    lines = []
    for a in addons:
        p = _provides(a)
        for rel in [p.get("context"), *(p.get("context_extra") or [])]:
            if rel and (a["dir"] / rel).is_file():
                lines.append(f"@{(ADDONS / a['name'] / rel).as_posix()}")
    instr = _instructions(root)
    if lines or (instr.exists() and BEGIN in instr.read_text(encoding="utf-8")):
        body = ("Add-on guidelines (generated from the project; follow them when writing code):\n" + "\n".join(lines)) \
            if lines else ""
        old = instr.read_text(encoding="utf-8") if instr.exists() else ""
        new = _block(old, body)
        if new != old:
            instr.write_text(new, encoding="utf-8")
    # 2. rules: copies, not links (Windows)
    rules_dir = root / ".claude" / "rules"
    wanted = {}
    for a in addons:
        src = _provides(a).get("rules")
        if src and (a["dir"] / src).is_dir():
            for f in sorted((a["dir"] / src).glob("*.md")):
                wanted[f"addon-{a['name']}-{f.name}"] = f.read_text(encoding="utf-8")
    existing = sorted(rules_dir.glob("addon-*.md")) if rules_dir.is_dir() else []
    for f in existing:
        if f.name not in wanted:
            f.unlink()
    if wanted:
        rules_dir.mkdir(parents=True, exist_ok=True)
        for name, text in wanted.items():
            target = rules_dir / name
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                target.write_text(text, encoding="utf-8")
    # 3. skill overrides in the personal settings
    desired: dict[str, str] = {}
    for a in addons:
        src = _provides(a).get("skill_overrides")
        if src and (a["dir"] / src).is_file():
            try:
                for skill, value in (json.loads((a["dir"] / src).read_text(encoding="utf-8")) or {}).items():
                    desired.setdefault(skill, value)
            except ValueError:
                notes.append(f"{a['name']}: {src} is not valid JSON — skipped")
    applied = state.get("skillOverrides") or {}
    if desired or applied:
        sp = root / ".claude" / "settings.local.json"
        try:
            settings = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
        except ValueError:
            settings = None
            notes.append(".claude/settings.local.json is not valid JSON — skill overrides not applied")
        if settings is not None:
            so = dict(settings.get("skillOverrides") or {})
            for skill, value in applied.items():
                if skill not in desired and so.get(skill) == value:
                    so.pop(skill)
            for skill, value in desired.items():
                if skill not in so or so[skill] == applied.get(skill):
                    so[skill] = value
                elif so[skill] != value:
                    notes.append(f"skillOverrides.{skill}: your value {so[skill]!r} kept (add-on wants {value!r})")
            if so:
                settings["skillOverrides"] = so
            else:
                settings.pop("skillOverrides", None)
            sp.parent.mkdir(parents=True, exist_ok=True)
            sp.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            state["skillOverrides"] = {k: v for k, v in desired.items() if so.get(k) == v}
            if not state["skillOverrides"]:
                state.pop("skillOverrides")
    _save_state(root, state)
    if addons:
        ignore = [f"{ADDONS.as_posix()}/*/cache/"]
        if _mode(root) != "shared":
            ignore += [f"{ADDONS.as_posix()}/", ".claude/rules/addon-*.md"]
        _ignore(root, ignore)
    for a in installed(root):
        if not a["ok"]:
            notes.append(f"{a['name']}: skipped — {a['problem']}")
    if not quiet:
        for n in notes:
            print(f"⚠ {n}")
    return notes


# ---------------------------------------------------------------- commands

def _command(a: dict, key: str, base: str | None = None) -> list[str] | None:
    spec = _provides(a).get(key)
    if not spec:
        return None
    parts = shlex.split(str(spec).replace("{base}", base or "HEAD"))
    script = a["dir"] / parts[0]
    if parts[0].endswith(".py"):
        return [sys.executable, str(script), *parts[1:]]
    return [str(script), *parts[1:]]


def settings(root: Path, name: str) -> dict:
    """`addons.<name>` merged across the factory's configuration layers ({} without a factory engine)."""
    try:
        import importlib.util
        here = Path(__file__).resolve().parent
        spec = importlib.util.spec_from_file_location("tf_packs_for_addons", here / "packs.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return ((mod.load_config(root).get("addons") or {}).get(name)) or {}
    except Exception:  # noqa: BLE001 — settings are optional; an add-on works without them
        return {}


def declared(root: Path) -> list[str]:
    """Add-ons the configuration asks for (`addons.<name>.install: true`)."""
    try:
        import importlib.util
        here = Path(__file__).resolve().parent
        spec = importlib.util.spec_from_file_location("tf_packs_for_addons", here / "packs.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return sorted(n for n, v in (mod.load_config(root).get("addons") or {}).items()
                      if isinstance(v, dict) and v.get("install") is True and NAME.match(n))
    except Exception:  # noqa: BLE001
        return []


def _env_for(root: Path, a: dict) -> dict:
    env = dict(os.environ)
    env["TF_ADDON_SETTINGS"] = json.dumps(settings(root, a["name"]), ensure_ascii=False)
    if "decisions" in (a["meta"].get("consumes") or []):
        files = [str(o["dir"] / _provides(o)["decisions"]) for o in installed(root)
                 if o["ok"] and o["name"] != a["name"] and _provides(o).get("decisions")
                 and (o["dir"] / _provides(o)["decisions"]).is_file()]
        env["TF_ADDON_DECISIONS"] = os.pathsep.join(files)
    return env


def pending(root: Path) -> list[dict]:
    """Reads the add-ons wait for (MCP tools of the session): [{addon, instructions, items}]."""
    out = []
    for a in installed(root):
        rel = _provides(a).get("pending") if a["ok"] else None
        if not rel or not (a["dir"] / rel).is_file():
            continue
        try:
            data = json.loads((a["dir"] / rel).read_text(encoding="utf-8"))
        except ValueError:
            continue
        if data.get("items"):
            out.append({"addon": a["name"], "file": (ADDONS / a["name"] / rel).as_posix(),
                        "instructions": data.get("instructions", ""), "items": data["items"]})
    return out


def run(root: Path, a: dict, key: str, extra: list[str] | None = None, base: str | None = None,
        capture: bool = False) -> subprocess.CompletedProcess | None:
    cmd = _command(a, key, base)
    if cmd is None:
        return None
    if key == "learn" and "--root" not in cmd:
        cmd += ["--root", str(root)]
    try:
        return subprocess.run(cmd + list(extra or []), cwd=root, capture_output=capture, text=True,
                              encoding="utf-8", errors="replace", timeout=TIMEOUT, env=_env_for(root, a))
    except (OSError, subprocess.TimeoutExpired) as e:
        return subprocess.CompletedProcess(cmd, 124, "", str(e))


def _resolve_source(root: Path, spec: str) -> tuple[Path, Path | None]:
    """(directory with addon.yaml, temporary directory to delete or None)."""
    p = Path(spec).expanduser()
    if p.is_dir():
        return p.resolve(), None
    if re.match(r"^(https://|git@|ssh://)", spec):
        tmp = Path(tempfile.mkdtemp(prefix="tf-addon-"))
        r = subprocess.run(["git", "clone", "--depth", "1", spec, str(tmp / "src")], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            shutil.rmtree(tmp, ignore_errors=True)
            raise SystemExit(f"✗ git clone failed: {r.stderr.strip()[-300:]}")
        src = tmp / "src"
        return (src if (src / "addon.yaml").is_file() else src / "addons" / Path(spec).stem), tmp
    if NAME.match(spec):
        try:
            source = json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get(
                "source") or ""
        except (OSError, ValueError):
            source = ""
        if source and Path(source).is_dir():
            return (Path(source) / "addons" / spec).resolve(), None
        if source:
            tmp = Path(tempfile.mkdtemp(prefix="tf-addon-"))
            r = subprocess.run(["git", "clone", "--depth", "1", source, str(tmp / "src")], capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            if r.returncode != 0:
                shutil.rmtree(tmp, ignore_errors=True)
                raise SystemExit(f"✗ git clone of the factory source failed: {r.stderr.strip()[-300:]}")
            return tmp / "src" / "addons" / spec, tmp
    raise SystemExit(f"✗ Not an add-on directory, git URL or add-on name: {spec}")


def add(root: Path, spec: str) -> int:
    src, tmp = _resolve_source(root, spec)
    try:
        info = load(src) if (src / "addon.yaml").is_file() else None
        if info is None:
            print(f"✗ No addon.yaml in {src}")
            return 2
        name = info["meta"].get("name") or src.name
        if not NAME.match(str(name)):
            print(f"✗ Bad add-on name {name!r}")
            return 2
        if info["meta"].get("contract") != CONTRACT:
            print(f"✗ {name}: contract {info['meta'].get('contract')!r}, this factory supports {CONTRACT}")
            return 2
        dst = root / ADDONS / name
        keep = list(info["meta"].get("keep") or []) + list(DEFAULT_KEEP)
        saved = Path(tempfile.mkdtemp(prefix="tf-addon-keep-"))
        try:
            for k in keep:
                if (dst / k).exists():
                    shutil.move(str(dst / k), str(saved / k))
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if n in SKIP_COPY])
            for k in keep:
                if (saved / k).exists():
                    if (dst / k).exists():
                        shutil.rmtree(dst / k) if (dst / k).is_dir() else (dst / k).unlink()
                    shutil.move(str(saved / k), str(dst / k))
        finally:
            shutil.rmtree(saved, ignore_errors=True)
        print(f"✓ Add-on {name} {info['meta'].get('version', '?')} in {dst.relative_to(root)}")
        sync(root)
        if _provides(info).get("learn"):
            print("  Next: tf learn   (builds the add-on's guidelines from this repository)")
        return 0
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def remove(root: Path, name: str) -> int:
    dst = root / ADDONS / name
    if not NAME.match(name) or not dst.is_dir():
        print(f"✗ No add-on {name!r} in {ADDONS}")
        return 2
    shutil.rmtree(dst)
    sync(root)
    print(f"✓ Removed add-on {name} and its wiring")
    return 0


def _order(addons: list[dict]) -> list[dict]:
    """Producers of decisions before their consumers."""
    return sorted(addons, key=lambda a: "decisions" in (a["meta"].get("consumes") or []))


def learn(root: Path, only: str | None) -> int:
    have = {a["name"] for a in installed(root)}
    for name in declared(root):   # rolled out by the company/team/project configuration
        if name not in have and (not only or name == only):
            print(f"→ {name}: install (addons.{name}.install in the configuration)")
            if add(root, name) != 0:
                print(f"⚠ {name}: could not be installed from the factory source")
    targets = _order([a for a in installed(root) if a["ok"] and _provides(a).get("learn")
                      and (not only or a["name"] == only)])
    if not targets:
        print("ℹ No installed add-on provides `learn`" + (f" named {only}" if only else "") + " — tf addon list")
        return 2 if only else 0
    rc = 0
    for a in targets:
        print(f"→ {a['name']}: learn")
        r = run(root, a, "learn")
        if r is None or r.returncode != 0:
            rc = 1
            print(f"⚠ {a['name']}: learn failed (exit {getattr(r, 'returncode', '?')})")
    sync(root)
    return rc


def refresh(root: Path) -> int:
    rc = 0
    for a in _order(installed(root)):
        if not a["ok"] or not _provides(a).get("refresh"):
            continue
        r = run(root, a, "refresh", capture=True)
        if r is None or r.returncode not in (0,):
            rc = 1
            print(f"⚠ {a['name']}: refresh failed (exit {getattr(r, 'returncode', '?')}): "
                  f"{(getattr(r, 'stderr', '') or '').strip()[-300:]}")
    sync(root, quiet=True)
    return rc


def check(root: Path, base: str | None, as_json: bool) -> int:
    results = []
    for a in installed(root):
        if not a["ok"] or not _provides(a).get("check"):
            continue
        r = run(root, a, "check", base=base, capture=True)
        entry = {"addon": a["name"], "exit": r.returncode, "blocking": r.returncode == 1}
        try:
            entry["report"] = json.loads(r.stdout) if r.stdout.strip() else None
        except ValueError:
            entry["report"] = r.stdout[-4000:]
        if r.returncode not in (0, 1):
            entry["error"] = (r.stderr or "")[-1000:]
        results.append(entry)
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for e in results:
            mark = "✗" if e["blocking"] else ("⚠" if e.get("error") else "✓")
            print(f"{mark} {e['addon']}: check exit {e['exit']}" + (f" — {e['error'].strip()}" if e.get("error") else ""))
        if not results:
            print("ℹ No installed add-on provides `check`")
    return 1 if any(e["blocking"] for e in results) else 0


def status(root: Path) -> list[str]:
    """Problems for tf doctor (empty: all fine or no add-ons)."""
    return [f"add-on {a['name']}: {a['problem']}" for a in installed(root) if not a["ok"]]


def cmd_list(root: Path, as_json: bool) -> int:
    rows = []
    for a in installed(root):
        p = _provides(a)
        plan = p.get("plan")
        waiting = next((len(x["items"]) for x in pending(root) if x["addon"] == a["name"]), 0)
        rows.append({"name": a["name"], "version": a["meta"].get("version"), "ok": a["ok"], "problem": a["problem"],
                     "dir": (ADDONS / a["name"]).as_posix(), "provides": sorted(p),
                     "plan": (ADDONS / a["name"] / plan).as_posix() if plan and (a["dir"] / plan).exists() else None,
                     "pending": waiting,
                     "pending_file": (ADDONS / a["name"] / p["pending"]).as_posix() if waiting else None})
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print("ℹ No add-ons. Add one: tf addon add <name | path | git URL>")
    for r in rows:
        state = "✓" if r["ok"] else f"⚠ {r['problem']}"
        print(f"{state} {r['name']} {r['version'] or '?'} — provides: {', '.join(r['provides']) or 'nothing'}"
              + ("" if r["plan"] or not r["ok"] else "  (no output yet: tf learn)")
              + (f"  — {r['pending']} items wait for the session (MCP tool or cheap model): {r['pending_file']}"
                 if r["pending"] else ""))
    return 0


def main(argv: list[str]) -> int:
    root = Path.cwd()
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "list":
        return cmd_list(root, "--json" in rest)
    if cmd == "add" and len(rest) == 1:
        return add(root, rest[0])
    if cmd == "remove" and len(rest) == 1:
        return remove(root, rest[0])
    if cmd == "sync":
        sync(root)
        return 0
    if cmd == "learn":
        return learn(root, rest[0] if rest else None)
    if cmd == "refresh":
        return refresh(root)
    if cmd == "check":
        base = rest[rest.index("--base") + 1] if "--base" in rest and rest.index("--base") + 1 < len(rest) else None
        return check(root, base, "--json" in rest)
    if cmd == "run" and len(rest) >= 2:
        a = next((x for x in installed(root) if x["name"] == rest[0]), None)
        if not a or not a["ok"]:
            print(f"✗ No usable add-on {rest[0]!r}")
            return 2
        r = run(root, a, rest[1], rest[2:])
        if r is None:
            print(f"✗ {rest[0]} does not provide {rest[1]!r}")
            return 2
        return r.returncode
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
