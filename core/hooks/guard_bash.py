#!/usr/bin/env python3
"""
PreToolUse (Bash): hard gate for shell commands — works independently of the model's decision,
also in subagents. DENY = block, ASK = human approval required.
Complements (does not replace) the permissions rules in settings.json.
"""
import importlib.util
import json
import os
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hook_errors import record as record_error  # hook error to .tf/logs/hook-errors.jsonl (tf doctor)
except ImportError:  # older install without the log module — the hook works as before
    def record_error(hook: str, exc: BaseException) -> None:
        return None
try:
    from hook_errors import record_block  # block to .tf/logs/hook-blocks.jsonl (warning after an update)
except ImportError:
    def record_block(hook: str, decision: str) -> None:
        return None

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DENY = [
    (r"\brm\s+-[a-zA-Z]*(rf|fr)[a-zA-Z]*\s+(/|/\*|~/?|\$HOME/?|\.\.?/?|\*)(\s|$)", "rm -rf on the root/home/current directory"),
    (r"--no-preserve-root", "rm --no-preserve-root"),
    (r"\bgit\s+push\b.*(\s--force(?!-with-lease)|\s-f\b|\s\+\S+)", "git push --force (use --force-with-lease after a human's consent)"),
    (r"\b(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?|py|node)\b", "pobieranie i wykonywanie skryptu z sieci (curl | sh)"),
    (r"(^|[;&|]\s*)(printenv|env)\s*($|[;&|>])", "printing all environment variables (they may contain secrets)"),
    (r"\b(cat|less|more|head|tail|bat|strings|xxd|base64|cp|scp|rsync|source|\.)\s+[^;&|]*"
     r"(\.env(?!\.(example|sample|template))\b|id_rsa|id_ed25519|\.pem\b|\.p12\b|\.aws/credentials|/secrets?/|"
     r"\.ssh/|\.git-credentials|\.kube/config|\.docker/config\.json|\.config/gh/hosts)",
     "reading a file with secrets"),
    # Patterns from attack analyses (Huntress: ClickFix, fake AI instructions, React2Shell, axios) — core-agent-security
    (r"\bbase64\s+(-d|-D|--decode)\b[^;&]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?|py|node|perl)\b",
     "decoding base64 and running it in a shell (typical of ClickFix)"),
    (r"\b(sh|bash|zsh)\s+(-c\s+)?[\"']?\$\(\s*(curl|wget)\b|<\(\s*(curl|wget)\b",
     "downloading and running a script from the network (sh -c \"$(curl …)\")"),
    (r"\b(iwr|irm|invoke-webrequest|invoke-restmethod)\b[^;&]*\|\s*(iex|invoke-expression)\b|"
     r"\b(iex|invoke-expression)\s*\(?\s*\(?\s*(iwr|irm|new-object\s+net\.webclient)",
     "downloading and running a PowerShell script from the network (irm | iex)"),
    (r"\bmshta(\.exe)?\s+\S", "mshta (running HTA — typical of ClickFix)"),
    (r"169\.254\.169\.254|metadata\.google\.internal|100\.100\.100\.200",
     "access to the cloud metadata service (instance credentials)"),
    (r"\bhistory\s+-c\b|\bunset\s+HISTFILE\b|HISTFILE=/dev/null", "clearing the shell history (covering tracks)"),
    (r"\bchattr\s+(-R\s+)?\+[a-zA-Z]*i", "chattr +i (locking files against deletion — a persistence technique)"),
    (r"\bterraform\s+(destroy|apply\b.*-auto-approve)", "terraform destroy / apply -auto-approve"),
    (r"\bmkfs(\.\w+)?\b|\bdd\s+[^;&|]*of=/dev/", "operations on block devices"),
    (r"\bchmod\s+(-R\s+)?0?777\b", "chmod 777"),
    (r":\(\)\s*\{\s*:\|:&\s*\};:", "fork bomb"),
    # git options that run an arbitrary program: git_exec_option() (by tokens, ignoring commit messages)
]

# Typy operacji polityki autonomii (B1a, `autonomy.operations` w .tf/factory/config.yaml i .tf/config/config.yaml):
# default "confirm" (human approval); a project may only tighten to "deny" (human decision 2026-11-10, D1).
ASK = [
    (r"\bsudo\b", "sudo", "sudo"),
    (r"\bgit\s+(reset\s+--hard|clean\s+-[a-zA-Z]*f|push\b)", "git reset --hard / clean -f / push", "git_push"),
    (r"\bterraform\s+(apply|import|state\s+(rm|mv))\b", "a change to the infrastructure state", "infra_change"),
    (r"\b(kubectl\s+(delete|apply|scale|rollout)|helm\s+(install|upgrade|uninstall|rollback))\b", "a change in a Kubernetes cluster",
     "infra_change"),
    (r"\b(npm|pnpm|yarn)\s+publish\b|\bdocker\s+push\b", "publishing a package/image", "publish"),
    (r"\b(DROP\s+(DATABASE|TABLE|SCHEMA)|TRUNCATE\s+TABLE?)\b", "destructive SQL", "destructive_sql"),
    (r"\b(curl|wget)\b.*(\s-d\s*@|--data(-binary)?\s*@|\s-T\s|--upload-file|-F\s+\S+=@|--post-file)", "sending a file outside",
     "data_upload"),
    (r"\bcrontab\b(?!\s+-l\b)|\bsystemctl\s+(--user\s+)?(enable|link)\b|\blaunchctl\s+(load|bootstrap)\b|"
     r"(LaunchAgents|LaunchDaemons|/etc/cron\.|/etc/systemd/|\.config/systemd/)",
     "persistence: cron, a systemd service or a LaunchAgent", "persistence"),
    (r"\b(npm\s+(i|install|add)|pnpm\s+(add|i|install)|yarn\s+add|bun\s+add)\b(\s+-{1,2}[\w-]+(=\S+)?)*\s+[@\w][^\s;&|]*",
     "adding or changing a dependency (supply chain)", "dependency_add"),
    (r"\b(kubectl|helm|terraform|aws|gcloud|az)\b.*\b(prod|production|prd)\b", "a command touching PRODUCTION", "prod_command"),
]
OPERATIONS = sorted({op for _, _, op in ASK})
LEVELS = {"confirm": 1, "deny": 2}


def _project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def load_policy(root: Path | None = None) -> tuple[dict, list[str]]:
    """Level of each operation type, and warnings. Engine and project configuration may only tighten: a value
    weaker than "confirm" (e.g. full, allow) or an unknown type is ignored and reported in the warnings."""
    root = root or _project_root()
    levels, warns = {op: "confirm" for op in OPERATIONS}, []
    packs_py = next((c for c in (root / ".tf" / "factory" / "packs.py", Path(__file__).resolve().parents[2] / ".tf" / "factory"
                                 / "packs.py") if c.is_file()), None)
    if not packs_py:
        return levels, warns
    try:
        spec = importlib.util.spec_from_file_location("tf_packs_guard", packs_py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "config_layers"):     # engine ← company ← team ← project ← person
            layers = mod.config_layers(root)
        else:
            layers = [(str(s), mod.load_yaml(s)) for s in (root / ".tf" / "factory" / "config.yaml",
                                                           root / ".tf" / "config" / "config.yaml") if s.is_file()]
        for src, data in layers:
            ops = ((data or {}).get("autonomy") or {}).get("operations") or {}
            for op, val in ops.items():
                val = str(val).strip().lower()
                if op not in levels:
                    warns.append(f"{src}: unknown operation type `{op}` (known: {', '.join(OPERATIONS)})")
                elif val not in LEVELS:
                    warns.append(f"{src}: `{op}: {val}` ignored — a policy can only tighten (confirm or deny)")
                elif LEVELS[val] > LEVELS[levels[op]]:
                    levels[op] = val
    except Exception as e:   # a configuration error never loosens — defaults remain
        warns.append(f"could not load the autonomy policy: {e}")
    return levels, warns


GIT_GLOBAL_OPTS = re.compile(
    r"\bgit((?:\s+(?:-C\s+\S+|-c\s+\S+|--(?:git-dir|work-tree|namespace|exec-path|config-env)(?:=\S+|\s+\S+)|"
    r"--no-pager|--paginate|-p|-P|--bare|--no-replace-objects|--literal-pathspecs|--no-optional-locks))+)(?=\s)")


def normalize(cmd: str) -> str:
    """`git -C dir push -f` and `git -c a=b reset --hard` are the same operations as without global options — the patterns see
    the subcommand right after `git`."""
    return GIT_GLOBAL_OPTS.sub("git", cmd)


# File writes through the shell (D-012): the same rules as Edit/Write — guard_paths (secrets, security configuration)
# and tdd_guard (production code after a red test). Recognizes redirections, tee, sed/perl -i, cp/mv/install and
# open(…,'w') / Path(…).write_text / writeFileSync in code given in the command. A script run from a file is not
# checked before execution — after execution tdd_guard reports the code change (git status).
REDIRECT = re.compile(r"[();|]*(&?>>?\|?)")
NO_TARGET = re.compile(r"^(/dev/(null|std(out|err)|tty|fd/\d+)|&?\d*)$")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1")
PREFIX = {"sudo", "env", "nohup", "time", "command", "exec", "nice", "doas", "!"}
INLINE_WRITES = [
    re.compile(r"\bopen\(\s*[rfbu]?['\"]([^'\"]+)['\"]\s*,\s*['\"][rbt]*[wax+]"),
    re.compile(r"Path\(\s*[rf]?['\"]([^'\"]+)['\"]\s*\)\s*\.\s*write_(?:text|bytes)\b"),
    re.compile(r"\b(?:writeFileSync|appendFileSync|writeFile|appendFile)\(\s*['\"`]([^'\"`]+)['\"`]"),
]


def strip_heredocs(cmd: str) -> str:
    out, end = [], None
    for line in cmd.split("\n"):
        if end is not None:
            if line.strip() == end:
                end = None
            continue
        out.append(line)
        m = HEREDOC.search(line)
        if m:
            end = m.group(2)
    return "\n".join(out)


# git push/fetch/pull run outside the Bash sandbox (sandbox.excludedCommands) — these options run an arbitrary program.
# Checked by tokens, not by text: an option name in a commit message (-m '…', heredoc) is data.
GIT_EXEC_OPT = re.compile(r"--(upload-pack|receive-pack|exec)\b")
GIT_EXEC_RAW = re.compile(r"\bgit\b[^;&|]*\s--(upload-pack|receive-pack|exec)\b")
CODE_RUNNERS = re.compile(r"\b(sh|bash|zsh|dash|ksh|fish|eval|source|python3?|py|perl|ruby|node)\b")


def git_exec_option(cmd: str) -> bool:
    lines, end, keep = [], None, False
    for line in cmd.replace("\\\n", " ").split("\n"):
        if end is not None:
            if line.strip() == end:
                end = None
            elif keep:
                lines.append(line)   # a heredoc for a shell or interpreter is code, not data
            continue
        lines.append(line)
        m = HEREDOC.search(line)
        if m:
            end, keep = m.group(2), bool(CODE_RUNNERS.search(line[:m.start()]))
    text = " ; ".join(lines)
    lex = shlex.shlex(text, posix=True, punctuation_chars=True)
    lex.whitespace_split, lex.commenters = True, ""
    try:
        toks = list(lex)
    except ValueError:
        return bool(GIT_EXEC_RAW.search(text))
    runner, seen_git = False, False
    for t in toks:
        if t and all(c in ";&|()" for c in t):
            runner, seen_git = False, False
            continue
        name = os.path.basename(t.lstrip("`"))
        if not seen_git and not runner and CODE_RUNNERS.fullmatch(name):
            runner = True
        if seen_git and GIT_EXEC_OPT.match(t):
            return True
        # code in an argument: sh -c "git …", a $(…) or `…` substitution in quotes
        if (runner or "$(" in t or "`" in t) and GIT_EXEC_RAW.search(t):
            return True
        seen_git = seen_git or name == "git"
    return False


def tokens(cmd: str) -> list[str]:
    text = strip_heredocs(cmd.replace("\\\n", " ")).replace("\n", " ; ")
    lex = shlex.shlex(text, posix=True, punctuation_chars=True)
    lex.whitespace_split, lex.commenters = True, ""
    try:
        return list(lex)
    except ValueError:
        return text.split()


def write_targets(cmd: str) -> list[str]:
    """Paths the command may write (without executing and without reading files)."""
    found = [m for r in INLINE_WRITES for m in r.findall(cmd)]
    segments, cur, redirect_next = [], [], False
    for t in tokens(cmd):
        if redirect_next:
            redirect_next = False
            if not NO_TARGET.match(t):
                found.append(t)
            continue
        m = REDIRECT.fullmatch(t)
        if m:
            redirect_next = True
            continue
        if t in ("<", "<<", "<<<", "<<-", ">&", "<&") or re.fullmatch(r"\d*[<>]&?\d*-?", t):
            redirect_next = t.startswith(">")   # an input operand or a descriptor — not a write target
            if not redirect_next:
                cur.append("\0")               # the next token is an operand, skip it
            continue
        if t and all(c in ";&|()" for c in t):
            segments.append(cur)
            cur = []
            continue
        if cur and cur[-1] == "\0":
            cur.pop()
            continue
        cur.append(t)
    segments.append(cur)
    for seg in segments:
        while seg and (seg[0] in PREFIX or re.fullmatch(r"[A-Za-z_]\w*=.*", seg[0])):
            seg = seg[1:]
        if not seg:
            continue
        name, args = os.path.basename(seg[0]), seg[1:]
        if name == "tee":
            found += [a for a in args if not a.startswith("-")]
        elif name in ("sed", "gsed", "perl"):
            if not any(a.startswith("--in-place") or re.match(r"-[a-zA-Z]*i", a) for a in args):
                continue
            script, skip, files = False, False, []
            for a in args:
                if skip:
                    skip = False
                elif a in ("-e", "-f", "--expression", "--file") or (name == "perl" and a in ("-E", "-M")):
                    script = skip = True
                elif a.startswith("-") and len(a) > 1:
                    script = script or (name == "perl" and "e" in a.lstrip("-").split(".")[0])
                elif not script:
                    script = True
                else:
                    files.append(a)
            found += files
        elif name in ("cp", "mv", "install"):
            plain, skip, target_dir = [], False, None
            for i, a in enumerate(args):
                if skip:
                    skip = False
                elif a in ("-t", "--target-directory"):
                    target_dir = args[i + 1] if i + 1 < len(args) else None
                    skip = True
                elif a.startswith("--target-directory="):
                    target_dir = a.split("=", 1)[1]
                elif a in ("-S", "--suffix", "-m", "-o", "-g", "--mode", "--owner", "--group"):
                    skip = True
                elif not a.startswith("-") or a == "-":
                    plain.append(a)
            if target_dir:
                found += [os.path.join(target_dir, os.path.basename(a.rstrip("/"))) for a in plain]
            elif len(plain) >= 2:
                dest = plain[-1]
                if dest.endswith("/") or os.path.isdir(dest) or len(plain) > 2:
                    found += [os.path.join(dest, os.path.basename(a.rstrip("/"))) for a in plain[:-1]]
                else:
                    found.append(dest)
    return [f.rstrip("\\") for f in found if f]


def _module(name: str):
    spec = importlib.util.spec_from_file_location(f"_{name}", Path(__file__).with_name(f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_writes(data: dict, cmd: str) -> None:
    targets = write_targets(cmd)
    if not targets:
        return
    paths = _module("guard_paths")
    root = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")
    cwd = data.get("cwd") or root
    production = []
    for t in targets:
        full = os.path.normpath(os.path.join(cwd, os.path.expanduser(os.path.expandvars(t))))
        inside = full == root or full.startswith(root.rstrip(os.sep) + os.sep)
        norm = (os.path.relpath(full, root) if inside else full).replace("\\", "/")
        if paths.SECRET_PATHS.search(norm) and not paths.SAFE_ENV.search(norm):
            decide("deny", f"Blocked: writing to a file with secrets ({t}). Use environment variables and "
                           "*.example files; a human changes secrets.")
        if paths.GUARDRAILS.search(norm):
            decide("ask", f"Needs consent: a shell write to the safeguards' configuration or .git ({t}).")
        if inside and "$" not in norm:
            production.append(norm)
    mode = os.environ.get("CLAUDE_TDD", "strict").lower()
    if mode == "off" or os.environ.get("CLAUDE_TDD_BASH", "on").lower() == "off":
        return
    tdd = _module("tdd_guard")
    production = [p for p in production if tdd.is_production(p)]
    reason = tdd.bash_pre(data, production) if production else None
    if reason:
        decide("ask" if mode == "ask" else "deny", reason + " A shell write (sed -i, >, tee, cp…) goes through the "
                                                             "same gate as Edit.")


def decide(decision: str, reason: str) -> None:
    if decision in ("deny", "ask"):
        record_block("guard_bash", decision)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": f"[guard_bash] {reason}",
        }
    }, ensure_ascii=False))
    sys.exit(0)


def check_policy() -> int:
    levels, warns = load_policy()
    for w in warns:
        print(f"⚠ {w}")
    print("Polityka autonomii (guard_bash): " + ", ".join(f"{op}={lv}" for op, lv in sorted(levels.items())))
    return 1 if warns else 0


def main() -> None:
    if "--check-policy" in sys.argv[1:]:
        sys.exit(check_policy())
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    ti = data.get("tool_input") if isinstance(data, dict) else None
    cmd = ti.get("command") if isinstance(ti, dict) else None
    if not cmd or not isinstance(cmd, str):   # data outside the Claude Code format: a decision, not a failure (onFailure: block)
        sys.exit(0)
    cmd = normalize(cmd)
    for pattern, reason in DENY:
        if re.search(pattern, cmd, re.IGNORECASE):
            decide("deny", f"Blocked: {reason}. If it is necessary, ask a human to run it by hand.")
    if git_exec_option(cmd):
        decide("deny", "Blocked: a git option that runs any program (--upload-pack, --receive-pack, "
                       "--exec). If it is necessary, ask a human to run it by hand.")
    try:
        check_writes(data, cmd)
    except Exception as e:  # a write-detection error never blocks (decide ends the process via SystemExit — we do not catch it)
        record_error("guard_bash", e)
    hits = [(reason, op) for pattern, reason, op in ASK if re.search(pattern, cmd, re.IGNORECASE)]
    if hits:
        levels, _ = load_policy()
        for reason, op in hits:
            if levels.get(op) == "deny":
                decide("deny", f"Blocked by the project's autonomy policy ({op}: deny): {reason}. "
                               f"Ask a human to run it by hand.")
        reason, op = hits[0]
        decide("ask", f"Needs consent ({op}): {reason}.")
    sys.exit(0)  # no decision → normal permission flow


if __name__ == "__main__":
    main()
