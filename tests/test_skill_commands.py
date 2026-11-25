#!/usr/bin/env python3
"""Consistency of what the model is told to run with what the factory scripts accept.

The texts the model reads (skills with their references and hint.pl.txt, core/CLAUDE.md, core/guide/, the agent prompts
in config.yaml and the packs' and modes' pack.yaml, personas and roles) name factory scripts with subcommands and flags
(`python3 .claude/skills/tf/scripts/run_state.py stage <dir> intake --auto`, `tf task flag <KEY> set <key>`, …), agents
(`mcp-runner`, `scope-reviewer`) and tools (AskUserQuestion, ToolSearch, the Agent tool with `run_in_background`).
An instruction that no longer matches the code sends the model down a path it cannot take, so this test checks:

  C-1  every referenced script exists in the assembled workspace (default layout) and in the plugin layout;
  C-2  every subcommand exists and every flag is accepted (argparse introspection where the script has a parser,
       otherwise the exact string literals the script compares its arguments with); `tf <sub>` goes through the
       dispatcher table below, which must match tf.py's own dispatch;
  C-3  (report only) argparse subcommands and `tf` commands no text documents — dead or internal; listed, never failed;
  C-0  the extraction finds references, and the checker rejects known-broken ones (so it cannot pass vacuously).
  C-4  agents named in a skill (shared agents in backticks) are in the `Agent(...)` allowlist of every main-session
       agent that runs it (each persona; tf-task for its own skill), an `only_for` agent in at least one; an agent's
       own prompt names only agents it can start; every `Agent(...)` entry exists; both layouts build the same agents;
  C-5  tools a skill tells the model to use (AskUserQuestion, ToolSearch, Agent) are in the `tools:` of those agents
       (`claude --agent <name>` gets only the listed tools);
  C-6  the script commands of the loop skills (tf, tf-task, tf-design) are covered by `permissions.allow` in both
       layouts, so an unattended run does not stop at a permission prompt.

Placeholders (`<KEY>`, `<dir>`, `…`, `[--flag]`, `a|b`) are tolerated: a placeholder is never a subcommand, a flag in
square brackets is still checked.

  python3 tests/test_skill_commands.py [--verbose]
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ["TF_NO_PLUGIN_REGISTER"] = "1"   # installs here never call the real Claude Code CLI (plugin_register.py)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
VERBOSE = "--verbose" in sys.argv

# ───────────────────────── the texts the model reads ─────────────────────────


def text_sources() -> list[Path]:
    out: list[Path] = []
    bases = [ROOT / "core"] + sorted((ROOT / "packs").glob("*/")) + sorted((ROOT / "modes").glob("*/"))
    for base in bases:
        skills = base / "skills"
        out += sorted(skills.glob("*/SKILL.md")) + sorted(skills.glob("*/references/**/*.md")) \
            + sorted(skills.glob("*/hint.pl.txt"))
        out += sorted(base.glob("pack.yaml")) + sorted(base.glob("personas/*.yaml")) + sorted(base.glob("roles/*.yaml"))
    out += [ROOT / "core" / "CLAUDE.md", ROOT / "core" / "factory" / "config.yaml"]
    out += sorted((ROOT / "core" / "guide").glob("*.md"))
    return [p for p in out if p.is_file()]


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


SPAN = re.compile(r"`((?:[^`\n]|\n(?![ \t]*\n))+?)`")       # an inline code span, also across one line break
FENCE = re.compile(r"^[ \t]*(```|~~~)[^\n]*\n(.*?)^[ \t]*\1[ \t]*$", re.S | re.M)


def code_fragments(text: str) -> list[tuple[int, str]]:
    """Inline code spans (a span broken over two lines joined into one) and the lines of fenced blocks (also indented
    ones, in a list item), with their line numbers."""
    frags: list[tuple[int, str]] = []
    rest = text
    for m in FENCE.finditer(text):
        start = text.count("\n", 0, m.start(2)) + 1
        for i, line in enumerate(m.group(2).splitlines()):
            frags.append((start + i, line))
        rest = rest[:m.start()] + re.sub(r"[^\n]", " ", m.group(0)) + rest[m.end():]   # keep offsets and line numbers
    for m in SPAN.finditer(rest):
        frags.append((rest.count("\n", 0, m.start()) + 1, re.sub(r"\s*\n\s*", " ", m.group(1))))
    return frags


# ───────────────────────── command references ─────────────────────────

SCRIPT_PATH = re.compile(r"(?:^|[\s(\"'])(?:python3?|py|\$PY|\{py\})\s+((?:\./)?(?:\.claude|\.tf)/[\w./-]+\.py)\b(.*)$")
BARE = re.compile(r"^([a-z_]+\.py)\b(.*)$")
TF_CMD = re.compile(r"^tf ([a-z][\w-]*)\b(.*)$")
STOP_AT = re.compile(r"\s(?:\|\||&&|;|>>?|2>|#|→|->|—|–)\s|\s\|\s")
PLACEHOLDER = re.compile(r"[<>{}…*$\"'`]|\.\.\.")
FLAG = re.compile(r"^--?[a-zA-Z][\w-]*$")


class Ref:
    def __init__(self, src: str, line: int, script: str, args: list[str], frag: str, via: str = ""):
        self.src, self.line, self.script, self.args, self.frag, self.via = src, line, script, args, frag, via

    def where(self) -> str:
        return f"{self.src}:{self.line} `{self.frag.strip()[:110]}`"


def split_args(tail: str) -> list[str]:
    """The arguments of one command: up to a pipe, chain, comment or prose arrow; quoted text collapses to one token."""
    tail = STOP_AT.split(" " + tail + " ", maxsplit=1)[0]
    tail = re.sub(r'"[^"]*"|\'[^\']*\'', '"…"', tail)
    return tail.split()


def find_refs(sources: list[Path], bare_names: dict[str, str]) -> tuple[list[Ref], list[Ref]]:
    """References to scripts (`python3 <path>.py …` and bare `<name>.py <sub>` in code) and `tf <sub> …` commands."""
    scripts: list[Ref] = []
    tf_refs: list[Ref] = []
    for src in sources:
        text = src.read_text(encoding="utf-8")
        frags = code_fragments(text)
        if src.suffix == ".yaml":     # a YAML value can be a command itself (`verify: python3 …`), outside backticks
            frags += [(n, re.split(r"\s#\s", line)[0]) for n, line in enumerate(text.splitlines(), 1)
                      if "`" not in line and not line.lstrip().startswith("#")]
        for line, frag in frags:
            frag = frag.strip()
            for m in SCRIPT_PATH.finditer(" " + frag):
                path = m.group(1).removeprefix("./")
                scripts.append(Ref(rel(src), line, path, split_args(m.group(2)), frag))
            m = BARE.match(frag)
            if m and m.group(1) in bare_names:
                scripts.append(Ref(rel(src), line, bare_names[m.group(1)], split_args(m.group(2)), frag, via="bare"))
            m = TF_CMD.match(frag)
            if m:
                tf_refs.append(Ref(rel(src), line, "tf", [m.group(1)] + split_args(m.group(2)), frag))
    return scripts, tf_refs


# ───────────────────────── what the scripts accept ─────────────────────────

INTROSPECT = r"""
import argparse, json, runpy, sys
class _Stop(BaseException):
    pass
def dump(p):
    out = {"flags": [], "subs": {}, "pos": [], "choices": {}}
    for a in p._actions:
        out["flags"] += list(a.option_strings)
        ch = [str(c) for c in a.choices] if a.choices is not None and not isinstance(a.choices, dict) else None
        if isinstance(a, argparse._SubParsersAction):
            for name, sp in a.choices.items():
                out["subs"][name] = dump(sp)
        elif not a.option_strings:
            out["pos"].append([a.dest, ch, a.nargs if isinstance(a.nargs, (int, type(None))) else str(a.nargs)])
        elif ch:
            for o in a.option_strings:
                out["choices"][o] = ch
    return out
def fake(self, *a, **k):
    print("@@ARGPARSE@@" + json.dumps(dump(self)))
    raise _Stop
argparse.ArgumentParser.parse_args = fake
argparse.ArgumentParser.parse_known_args = fake
argparse.ArgumentParser.parse_intermixed_args = fake
sys.argv = [sys.argv[1]]
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except _Stop:
    pass
except BaseException as e:
    print("@@NOPARSE@@" + type(e).__name__)
"""


def docstring_nodes(tree: ast.AST) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                ids.add(id(first.value))
    return ids


def literals(path: Path) -> set[str]:
    """Every string literal of the script except docstrings, and each piece of a literal tuple/list of words."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return set()
    docs = docstring_nodes(tree)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            v = node.value
            out.add(v)
            if v.startswith("-") and "=" in v:
                out.add(v.split("=", 1)[0])
            if re.fullmatch(r"(--?[\w-]+)( --?[\w-]+)*", v):     # "--a --b" written as one string
                out.update(v.split())
    return out


def sibling_modules(path: Path) -> list[Path]:
    """Modules of the same directory the script imports or loads by file name (their literals are its vocabulary)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    names = set(re.findall(r"^\s*(?:from|import)\s+(\w+)", text, re.M)) | set(re.findall(r"[\"'](\w+)\.py[\"']", text))
    return [path.parent / f"{n}.py" for n in sorted(names) if (path.parent / f"{n}.py").is_file()
            and path.parent / f"{n}.py" != path]


def uses_argparse(path: Path) -> bool:
    """Only a script that builds an argparse parser is run (stopped at parse_args); a hand-parsed one is never run —
    without arguments it would do its default work (tf.py and update.py update, build.py builds)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return False
    return any(isinstance(n, ast.Import) and any(a.name == "argparse" for a in n.names) for n in ast.walk(tree))


def introspect(path: Path, ws: Path) -> dict | None:
    """The parser tree of an argparse script: run it with parse_args replaced by a dump (cwd: the workspace,
    HOME: an empty directory, so nothing outside the temporary tree is touched)."""
    home = ws.parent / "home"
    home.mkdir(exist_ok=True)
    r = subprocess.run([sys.executable, "-c", INTROSPECT, str(path)], cwd=ws, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60, stdin=subprocess.DEVNULL,
                       env={**os.environ, "HOME": str(home), "USERPROFILE": str(home), "TF_NO_PLUGIN_REGISTER": "1",
                            "PYTHONDONTWRITEBYTECODE": "1"})
    m = re.search(r"@@ARGPARSE@@(.*)", r.stdout)
    return json.loads(m.group(1)) if m else None


# Words a hand-parsed script accepts without comparing them with a literal (checked by reading the code):
# decision_cache.py runs a refresh for any command that is not `search` or `status` (its docstring: `refresh|status`).
IMPLICIT_WORDS = {"decision_cache.py": {"refresh"}}


class Cli:
    def __init__(self, path: Path, ws: Path):
        self.path = path
        self.words = literals(path)
        for m in sibling_modules(path):
            self.words |= literals(m)
        self.parser = introspect(path, ws) if uses_argparse(path) else None
        self.implicit = IMPLICIT_WORDS.get(path.name, set())

    def check(self, args: list[str]) -> list[str]:
        """Problems with one argument list ([] when it is accepted)."""
        problems: list[str] = []
        flags = [f for a in args for f in flag_tokens(a)]
        node = self.parser
        if node is not None:
            accepted = set(node["flags"])
            rest = list(args)
            while node["subs"]:
                first = rest[0] if rest else ""
                # `[x]` (not a flag in brackets) is an optional placeholder, never a subcommand
                word = "" if first.startswith("[") and not flag_tokens(first) else first.strip("[]")
                if not is_word(word):
                    accepted |= {f for s in node["subs"].values() for f in s["flags"]}   # which subcommand is unknown
                    break
                if word not in node["subs"]:
                    return [f"subcommand '{word}' does not exist (has: {', '.join(sorted(node['subs']))})"]
                node, rest = node["subs"][word], rest[1:]
                accepted |= set(node["flags"])
            for f in flags:
                if f not in accepted:
                    problems.append(f"flag {f} is not accepted")
            return problems + choice_problems(node, rest, self.words)
        first = args[0] if args and not args[0].startswith("[") else ""
        if is_word(first) and first not in self.words | self.implicit:   # no parser: a subcommand is a literal
            problems.append(f"subcommand '{first}' is not a literal the script handles")
        for f in flags:               # no parser: the flag must be a literal the script compares with
            if f not in self.words:
                problems.append(f"flag {f} is not a literal the script handles")
        return problems


def choice_problems(node: dict, rest: list[str], words: set[str]) -> list[str]:
    """A literal word given for a positional argument or a flag value that has `choices` must be one of them; a word
    for a positional without `choices` (a stage, a mode) must be a literal the script knows. Alternatives `a|b` are
    checked one by one, placeholders are skipped."""
    problems = []
    values = []                      # (what, token, choices)
    pos = list(node.get("pos") or [])
    i = 0
    while i < len(rest):
        tok = rest[i]
        flag = flag_tokens(tok)
        if flag:
            ch = node["choices"].get(flag[0])
            if ch and "=" not in tok and i + 1 < len(rest):
                values.append((flag[0], rest[i + 1], ch))
                i += 1
            elif ch and "=" in tok:
                values.append((flag[0], tok.split("=", 1)[1], ch))
            i += 1
            continue
        if tok.startswith("-"):
            i += 1
            continue
        if pos and not tok.startswith("["):
            dest, ch, nargs = pos[0]
            if ch:
                values.append((dest, tok, ch))
            elif nargs in (None, "?") and re.fullmatch(r"[a-z][\w-]*", tok) and tok not in words:   # not a list of names
                problems.append(f"'{tok}' (for {dest}) is not a value the script knows")
            if nargs not in ("*", "+", "...", "A...") and not str(nargs).startswith("A"):
                pos.pop(0)
        i += 1
    for what, tok, ch in values:
        for alt in tok.strip("[]()").split("|"):
            if re.fullmatch(r"[a-z][\w-]*", alt) and alt not in ch:
                problems.append(f"'{alt}' is not a choice of {what} ({', '.join(ch)})")
    return problems


def is_word(tok: str) -> bool:
    return bool(re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", tok))


def flag_tokens(tok: str) -> list[str]:
    """Flags in one token: `--a`, `[--a]`, `--a=1`, `--a|--b`, `(--a)`; never in a placeholder like `<--x>`."""
    out = []
    for part in tok.strip("[](),.;:").split("|"):
        part = part.strip("[](),.;:")
        part = part.split("=", 1)[0]
        if part.startswith("--") and FLAG.match(part) and not PLACEHOLDER.search(part):
            out.append(part)
    return out


def config_keys(config: Path, section: str) -> set[str]:
    """The keys of one top-level mapping of config.yaml (no YAML parser: two-space indented `key:` lines)."""
    m = re.search(rf"^{section}:\n((?:(?:  .*|\s*)\n)+)", config.read_text(encoding="utf-8"), re.M)
    return set(re.findall(r"^  ([\w-]+):", m.group(1), re.M)) if m else set()


def copied_template(ref: Ref, ws: Path) -> Path | None:
    """A script the same text says to copy from a skill's templates/ to this path (it exists only after that step)."""
    text = (ROOT / ref.src).read_text(encoding="utf-8")
    if not re.search(rf"\bto `{re.escape(ref.script)}`", text):
        return None
    name = Path(ref.script).name
    return next(iter(sorted((ws / ".claude" / "skills").glob(f"*/templates/{name}"))), None)


# ───────────────────────── the tf dispatcher ─────────────────────────

# `tf <sub>` → (the script in .tf/factory/ or the skill path it runs, the arguments it puts first). Checked against
# tf.py's own dispatch below, so a new or removed `tf` command fails here until this table follows.
TF_ROUTES: dict[str, tuple[str | None, list[str]]] = {
    "install": ("core/factory/install.py", []),
    "update": (".tf/factory/update.py", []),
    "add": (None, []), "remove": (None, []), "list": (None, []),
    "language": (None, []), "commit-language": (None, []),
    "doctor": (".tf/factory/tf.py", []),
    "init": (".tf/factory/analyze.py", ["init"]),
    "analyze": (".tf/factory/analyze.py", ["run"]),
    "risk": (".tf/factory/risk_triage.py", []),
    "diff": (".tf/factory/system_diff.py", []),
    "new": (".tf/factory/build.py", []),
    "skill": (None, []),
    "config": (".tf/factory/tf.py", []),
    "uninstall": (".tf/factory/uninstall.py", []),
    "style": (".tf/factory/tf.py", []),
    "isolation": (".tf/factory/isolation.py", []),
    "task": (".tf/factory/task_state.py", []),
    "proposals": (".tf/factory/proposals.py", []),
    "status": (".tf/factory/task_state.py", ["list"]),
    "spec": (".tf/factory/spec_check.py", []),
    "trace": (".tf/factory/trace_check.py", []),
    "flag": (".tf/factory/flag_check.py", []),
    "onboard": (".tf/factory/onboard.py", []),
    "code": (".tf/factory/tf.py", []),
    "cloud-setup": (".tf/factory/tf.py", []),
    "work": (".tf/factory/work.py", []),
    "cooldown": (".claude/skills/tf/scripts/security_scan.py", ["cooldown"]),
    "addon": (".tf/factory/addons.py", []),
    "learn": (".tf/factory/addons.py", ["learn"]),
    "metrics": (".tf/factory/metrics.py", []),
}
TF_SKILL = {"check": ".tf/factory/skill_gate.py", "audit": ".tf/factory/skill_audit.py"}
TF_OWN_FLAGS = {"--repo", "--bin", "--install-launcher", "-h", "--help"}   # tf.py's own, before the command
TF_SUB_FLAGS = {"status": {"--open"}, "analyze": {"--list"}}           # handled by tf.py itself, the rest goes on
TF_PASSTHROUGH = {"code"}   # `tf code [--container] [claude arguments]`: the rest goes to claude


def tf_dispatch(tf_py: Path) -> set[str]:
    """The commands tf.py's main() compares `cmd` with."""
    tree = ast.parse(tf_py.read_text(encoding="utf-8"))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    cmds: set[str] = set()
    for node in ast.walk(main):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == "cmd":
            for comp in node.comparators:
                for c in ast.walk(comp):
                    if isinstance(c, ast.Constant) and isinstance(c.value, str):
                        cmds.add(c.value)
    return cmds


def check_tf(args: list[str], clis: dict[str, Cli], ws: Path, styles: set[str]) -> list[str]:
    """Problems with one `tf <sub> …` command: the command exists, then its arguments as the engine script sees them."""
    sub, rest = args[0], args[1:]
    if sub not in TF_ROUTES:
        return [f"`tf {sub}` is not a tf command"]
    target, lead = TF_ROUTES[sub]
    if sub == "skill":
        if not rest or not is_word(rest[0]):
            return []
        if rest[0] not in TF_SKILL:
            return [f"`tf skill {rest[0]}` is not a tf command"]
        target, rest = TF_SKILL[rest[0]], rest[1:]
    if target is None or sub in TF_PASSTHROUGH:
        return []
    problems = []
    if sub == "style":        # `tf style <name>`: a work style from config.yaml `styles`
        word = rest[0] if rest and is_word(rest[0]) else None
        if word and word not in styles:
            problems.append(f"`tf style {word}` is not a style ({', '.join(sorted(styles))})")
        rest = rest[1:] if word else rest
    if sub == "analyze":
        lead = ["list"] if "--list" in rest else lead
    if sub == "flag":         # `tf flag check <KEY>`: tf.py accepts only `check`, flag_check.py drops it
        if rest and is_word(rest[0]) and rest[0] != "check":
            return [f"`tf flag {rest[0]}` is not a tf command (only `tf flag check`)"]
        rest = rest[1:] if rest and rest[0] == "check" else rest
    if sub == "isolation":
        lead = ["set"] if rest and is_word(rest[0].strip("[]")) else ["show"]
    path = ROOT / target if target.startswith("core/") else ws / target
    cli = clis.get(target) or Cli(path, ws)
    clis[target] = cli
    own = TF_OWN_FLAGS | TF_SUB_FLAGS.get(sub, set())
    for p in cli.check(lead + rest):
        if not (p.startswith("flag ") and p.split()[1] in own):
            problems.append(f"tf {sub} → {Path(target).name}: {p}")
    return problems


# References that must fail: a renamed subcommand, an unknown flag, an unknown tf command (C-0).
BROKEN = [
    (["stagee", "<dir>", "intake"], ".claude/skills/tf/scripts/run_state.py"),              # argparse, subcommand
    (["stage", "<dir>", "intake", "--no-such-flag"], ".claude/skills/tf/scripts/run_state.py"),   # argparse, flag
    (["flag", "<dir>", "toggle"], ".claude/skills/tf/scripts/run_state.py"),               # argparse, positional choice
    (["stage", "<dir>", "intake", "--effort", "huge"], ".claude/skills/tf/scripts/run_state.py"),  # argparse, flag choice
    (["stage", "<dir>", "intakee"], ".claude/skills/tf/scripts/run_state.py"),             # argparse, positional word
    (["resolvee", "x"], ".claude/skills/tf/scripts/intake.py"),                             # hand-parsed, subcommand
    (["--no-such-flag"], ".tf/factory/update.py"),                                         # hand-parsed, flag
    (["no-such-command"], "tf"),
    (["task", "no-such-sub", "<KEY>"], "tf"),
    (["status", "--no-such-flag"], "tf"),
    (["style", "no-such-style"], "tf"),
    (["skill", "no-such-sub", "x"], "tf"),
    (["flag", "set", "<KEY>"], "tf"),
]


# ───────────────────────── agents, tools, settings ─────────────────────────


def agent_files(base: Path) -> dict[str, dict]:
    """name → {tools: [...], agents: [...]} from the generated agent files' frontmatter."""
    out = {}
    for f in sorted(base.rglob("*.md")):
        text = f.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        head = text.split("---", 2)[1]
        name = re.search(r"^name:\s*(\S+)", head, re.M)
        tools = re.search(r"^tools:\s*(.*)$", head, re.M)
        if not name:
            continue
        line = tools.group(1) if tools else ""
        agents = re.search(r"Agent\(([^)]*)\)", line)
        out[name.group(1)] = {
            "tools": [t.strip() for t in re.sub(r"Agent\([^)]*\)", "Agent", line).split(",") if t.strip()],
            "agents": [a.strip() for a in agents.group(1).split(",")] if agents else None,
            "all_tools": tools is None,
            "persona": f.parent.name == f.stem,
            "shared": f.parent.name == "shared",
            "body": text.split("---", 2)[2],
        }
    return out


def only_for_agents(ws: Path) -> set[str]:
    """Shared agents limited to some personas (`only_for` in config.yaml or a pack.yaml), read with the factory's PyYAML."""
    sys.path.insert(0, str(ws / ".tf" / "factory" / "_vendor"))
    import yaml  # noqa: PLC0415 — the factory's bundled copy (no PyPI dependency)
    files = [ws / ".tf" / "factory" / "config.yaml"] + sorted((ws / ".tf" / "factory" / "packs").glob("*/pack.yaml"))
    out = set()
    for f in files:
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for name, spec in (data.get("shared_agents") or {}).items():
            if isinstance(spec, dict) and spec.get("only_for"):
                out.add(name)
    return out


def bash_allow(settings: Path) -> list[re.Pattern]:
    data = json.loads(settings.read_text(encoding="utf-8"))
    pats = []
    for r in (data.get("permissions") or {}).get("allow") or []:
        m = re.fullmatch(r"Bash\((.*)\)", r)
        if not m:
            continue
        p = m.group(1)
        if p.endswith(":*"):
            p = p[:-2] + " *"
        if p.endswith(" *"):
            pats.append(re.compile(rf"^{re.escape(p[:-2])}(?:\s.*)?$"))
        else:
            pats.append(re.compile(rf"^{re.escape(p)}$"))
    return pats


# The tool a skill tells the main session to use → the phrase that means it (the Agent tool: a background subagent).
TOOL_PHRASES = {
    "AskUserQuestion": re.compile(r"\bAskUserQuestion\b"),
    "ToolSearch": re.compile(r"\bToolSearch\b"),
    "Agent": re.compile(r"\brun_in_background\b|\bthe Agent tool\b"),
}
# The loop skills: they run unattended (`claude -p`, tf work), so their script commands need allow rules (C-6).
LOOP_SKILLS = ("tf", "tf-task", "tf-design")
# A command that records a human's decision (`--by human:<id>`): the model runs it after the human answered, and the
# permission prompt is a second confirmation by design, so it needs no allow rule.
HUMAN_DECISION = re.compile(r"--by human:")


def skill_text(skill_dir: Path) -> str:
    parts = [skill_dir / "SKILL.md"] + sorted((skill_dir / "references").glob("**/*.md"))
    return "\n".join(p.read_text(encoding="utf-8") for p in parts if p.is_file())


# ───────────────────────── the test ─────────────────────────


def assemble(tmp: Path) -> tuple[Path, Path]:
    ws = tmp / "all"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "workspace.py"), "assemble", "--packs", "all", "--out", str(ws)],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise SystemExit(f"✗ workspace assemble failed: {r.stdout[-800:]}{r.stderr[-800:]}")
    plg = tmp / "plugin"
    plg.mkdir()
    subprocess.run(["git", "init", "-q", str(plg)], check=False)
    r = subprocess.run([sys.executable, str(ROOT / "core" / "factory" / "install.py"), str(plg), "--yes", "--layout", "plugin",
                        "--packs", "all"], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise SystemExit(f"✗ plugin install failed: {r.stdout[-800:]}{r.stderr[-800:]}")
    return ws, plg


def main() -> int:
    fails: list[str] = []
    notes: list[str] = []
    total = 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory(prefix="tf-cmds-") as t:
        ws, plg = assemble(Path(t))
        sources = text_sources()
        known = sorted(p for p in (ws / ".claude").rglob("*.py") if "/tests/" not in p.as_posix()) \
            + sorted((ws / ".tf" / "factory").glob("*.py"))
        by_name: dict[str, list[str]] = {}
        for p in known:
            by_name.setdefault(p.name, []).append(p.relative_to(ws).as_posix())
        bare = {n: ps[0] for n, ps in by_name.items() if len(ps) == 1}
        scripts, tf_refs = find_refs(sources, bare)
        check(len(scripts) > 200 and len(tf_refs) > 50, f"C-0: too few references found ({len(scripts)} scripts, "
                                                         f"{len(tf_refs)} tf) — the extraction is broken")

        # C-1: the script exists in both layouts
        paths = sorted({r.script for r in scripts if not PLACEHOLDER.search(r.script) and (ws / r.script).is_file()}
                       | {tgt for tgt, _ in TF_ROUTES.values() if tgt and not tgt.startswith("core/")} | set(TF_SKILL.values()))
        with ThreadPoolExecutor(max_workers=8) as pool:     # each argparse script is one short subprocess
            clis: dict[str, Cli] = dict(zip(paths, pool.map(lambda s: Cli(ws / s, ws), paths)))
        for ref in scripts:
            if PLACEHOLDER.search(ref.script):
                continue
            in_ws, in_plg = (ws / ref.script).is_file(), (plg / ref.script).is_file()
            if not in_ws and (tpl := copied_template(ref, ws)):      # the skill tells the human to copy it there first
                if ref.script not in clis:
                    clis[ref.script] = Cli(tpl, ws)
                continue
            check(in_ws, f"C-1 {ref.where()}: {ref.script} does not exist in the assembled workspace")
            check(in_plg or not in_ws, f"C-1 {ref.where()}: {ref.script} does not exist in the plugin layout")
            if in_ws and ref.script not in clis:
                clis[ref.script] = Cli(ws / ref.script, ws)

        # C-2: subcommands and flags
        for ref in scripts:
            cli = clis.get(ref.script)
            if cli is None:
                continue
            for p in cli.check(ref.args):
                check(False, f"C-2 {ref.where()}: {Path(ref.script).name}: {p}")

        # C-2 (tf): the dispatcher table matches tf.py, then each `tf <sub> …`
        tf_py = ws / ".tf" / "factory" / "tf.py"
        dispatched = tf_dispatch(tf_py)
        check(set(TF_ROUTES) == dispatched, f"C-2 tf.py dispatch changed: not in TF_ROUTES "
                                            f"{sorted(dispatched - set(TF_ROUTES))}, gone {sorted(set(TF_ROUTES) - dispatched)}")
        styles = config_keys(ws / ".tf" / "factory" / "config.yaml", "styles")
        check(len(styles) >= 2, f"C-2: no work styles found in config.yaml: {styles}")
        for ref in tf_refs:
            for p in check_tf(ref.args, clis, ws, styles):
                check(False, f"C-2 {ref.where()}: {p}")

        # C-0: the checker itself catches broken references (a checker that accepts everything passes vacuously)
        for args, script in BROKEN:
            if script == "tf":
                found = check_tf(args, clis, ws, styles)
            else:
                cli = clis.get(script) or Cli(ws / script, ws)
                found = cli.check(args)
            check(found, f"C-0: the checker accepts a broken reference: {script} {' '.join(args)}")

        # C-3 (report): argparse subcommands no text mentions
        corpus = "\n".join(s.read_text(encoding="utf-8") for s in sources)
        for script, cli in sorted(clis.items()):
            if not cli.parser or not cli.parser["subs"]:
                continue
            name = Path(script).name
            tf_names = [s for s, (tgt, lead) in TF_ROUTES.items() if tgt == script and not lead]
            tf_lead = {lead[0]: s for s, (tgt, lead) in TF_ROUTES.items() if tgt == script and lead}
            tf_lead.update({"list": "analyze --list"} if name == "analyze.py" else {})
            for sub in sorted(cli.parser["subs"]):
                pats = [rf"{re.escape(name)} {re.escape(sub)}\b"] + [rf"\btf {re.escape(s)} (?:\S+ )?{re.escape(sub)}\b"
                                                                    for s in tf_names]
                pats += [rf"\btf {re.escape(tf_lead[sub])}\b"] if sub in tf_lead else []
                if not any(re.search(p, corpus) for p in pats):
                    notes.append(f"C-3 {script}: subcommand '{sub}' is not documented in any skill, guide or prompt")

        used = {r.args[0] for r in tf_refs}
        for sub in sorted(set(TF_ROUTES) - used - {"language", "commit-language"}):   # (the two print "no longer needed")
            notes.append(f"C-3 tf.py: `tf {sub}` is not documented in any skill, guide or prompt")

        # C-4/C-5: agents and tools of the main-session agents that run the skills
        agents = agent_files(ws / ".claude" / "agents" / "_generated")
        plg_agents = agent_files(plg / ".tf" / "plugin" / "agents")
        check(set(agents) == set(plg_agents), "C-4: the plugin layout builds other agents than the default layout")
        all_agents = set(agents) | {"Explore", "general-purpose", "Plan"}
        mains = {n: a for n, a in agents.items() if a["persona"] or n == "tf-task"}
        check("tf-task" in mains and len(mains) > 5, f"C-4: main-session agents not found: {sorted(mains)}")
        restricted = only_for_agents(ws)
        check("specialist" in restricted, f"C-4: the only_for agents were not read: {sorted(restricted)}")
        named_re = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+|scout|architect|researcher|specialist)`")
        for skill_dir in sorted((ws / ".claude" / "skills").glob("*/")):
            if not (skill_dir / "SKILL.md").is_file():
                continue
            text = skill_text(skill_dir)
            named = {m for m in named_re.findall(text) if m in agents and agents[m]["shared"]
                     and not re.search(rf"claude --agent {re.escape(m)}\b", text)}
            callers = {"tf-task": mains["tf-task"]} if skill_dir.name == "tf-task" else {}
            callers.update({n: a for n, a in mains.items() if a["persona"]})
            for n in sorted(named & restricted):      # `only_for`: some persona must reach it, not every one
                check(any(n in (a["agents"] or []) for a in mains.values()),
                      f"C-4 {skill_dir.name}: names the agent `{n}`, which no main-session agent can start")
            for caller, a in sorted(callers.items()):
                if a["agents"] is None:
                    continue
                for n in sorted(named - restricted):
                    check(n in a["agents"] or n == caller,
                          f"C-4 {skill_dir.name}: names the agent `{n}`, which is not in {caller}'s Agent(...) list")
                for tool, rx in TOOL_PHRASES.items():
                    if rx.search(text) and not a["all_tools"]:
                        check(tool in a["tools"],
                              f"C-5 {skill_dir.name}: tells the model to use {tool}, which {caller}'s tools lack")
        for caller, a in sorted(agents.items()):   # an agent's own prompt names only agents it can start
            body = a["body"]
            own = {m for m in named_re.findall(body) if m in agents and agents[m]["shared"]} - restricted - {caller}
            for n in sorted(own):
                if re.search(rf"claude --agent {re.escape(n)}\b", body):
                    continue
                unlimited = a["all_tools"] or (a["agents"] is None and "Agent" in a["tools"])   # plain `Agent`: any agent
                check(unlimited or n in (a["agents"] or []),
                      f"C-4 agent {caller}: its prompt names `{n}`, which is not in its Agent(...) list")
        for a in agents.values():       # every Agent(...) entry is a real agent
            for n in a["agents"] or []:
                check(n in all_agents, f"C-4: Agent({n}) names an agent that does not exist")

        # C-6: permissions for the loop skills' script commands, both layouts
        rules = {"default": bash_allow(ws / ".claude" / "settings.local.json"),
                 "plugin": bash_allow(plg / ".tf" / "plugin" / "session-settings.json")}
        loop_srcs = {f"core/skills/{s}/" for s in LOOP_SKILLS}
        for ref in scripts:
            if not any(ref.src.startswith(s) for s in loop_srcs) or PLACEHOLDER.search(ref.script) \
                    or HUMAN_DECISION.search(ref.frag):
                continue
            cmd = " ".join(["python3", ref.script, *ref.args]).strip()
            for layout, pats in rules.items():
                check(any(p.match(cmd) for p in pats),
                      f"C-6 {ref.where()}: `{cmd[:90]}` has no permissions.allow rule ({layout} layout)")

    for n in sorted(set(notes)):
        print(f"ℹ {n}")
    seen = set()
    for f in fails:
        if f not in seen:
            print(f"✗ {f}")
            seen.add(f)
    if VERBOSE:
        print(f"ℹ {len(scripts)} script references, {len(tf_refs)} tf references, {len(clis)} scripts inspected "
              f"({sum(1 for c in clis.values() if c.parser)} with an argparse parser)")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} skill command consistency checks")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
