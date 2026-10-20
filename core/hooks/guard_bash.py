#!/usr/bin/env python3
"""
PreToolUse (Bash): twarda bramka dla poleceń powłoki — działa niezależnie od decyzji modelu,
również w subagentach. DENY = blokada, ASK = wymagana zgoda człowieka.
Uzupełnia (nie zastępuje) reguły permissions w settings.json.
"""
import importlib.util
import json
import os
import re
import shlex
import sys
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DENY = [
    (r"\brm\s+-[a-zA-Z]*(rf|fr)[a-zA-Z]*\s+(/|/\*|~/?|\$HOME/?|\.\.?/?|\*)(\s|$)", "rm -rf na katalogu głównym/domowym/bieżącym"),
    (r"--no-preserve-root", "rm --no-preserve-root"),
    (r"\bgit\s+push\b.*(\s--force(?!-with-lease)|\s-f\b|\s\+\S+)", "git push --force (użyj --force-with-lease po zgodzie człowieka)"),
    (r"\b(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?|py|node)\b", "pobieranie i wykonywanie skryptu z sieci (curl | sh)"),
    (r"(^|[;&|]\s*)(printenv|env)\s*($|[;&|>])", "wypisywanie wszystkich zmiennych środowiskowych (mogą zawierać sekrety)"),
    (r"\b(cat|less|more|head|tail|bat|strings|xxd|base64|cp|scp|rsync|source|\.)\s+[^;&|]*"
     r"(\.env(?!\.(example|sample|template))\b|id_rsa|id_ed25519|\.pem\b|\.p12\b|\.aws/credentials|/secrets?/|"
     r"\.ssh/|\.git-credentials|\.kube/config|\.docker/config\.json|\.config/gh/hosts)",
     "odczyt pliku z sekretami"),
    # Wzorce z analiz ataków (Huntress: ClickFix, fałszywe instrukcje AI, React2Shell, axios) — core-agent-security
    (r"\bbase64\s+(-d|-D|--decode)\b[^;&]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?|py|node|perl)\b",
     "dekodowanie base64 i wykonanie w powłoce (typowe dla ClickFix)"),
    (r"\b(sh|bash|zsh)\s+(-c\s+)?[\"']?\$\(\s*(curl|wget)\b|<\(\s*(curl|wget)\b",
     "pobieranie i wykonywanie skryptu z sieci (sh -c \"$(curl …)\")"),
    (r"\b(iwr|irm|invoke-webrequest|invoke-restmethod)\b[^;&]*\|\s*(iex|invoke-expression)\b|"
     r"\b(iex|invoke-expression)\s*\(?\s*\(?\s*(iwr|irm|new-object\s+net\.webclient)",
     "pobieranie i wykonywanie skryptu PowerShell z sieci (irm | iex)"),
    (r"\bmshta(\.exe)?\s+\S", "mshta (uruchamianie HTA — typowe dla ClickFix)"),
    (r"169\.254\.169\.254|metadata\.google\.internal|100\.100\.100\.200",
     "dostęp do usługi metadanych chmury (poświadczenia instancji)"),
    (r"\bhistory\s+-c\b|\bunset\s+HISTFILE\b|HISTFILE=/dev/null", "kasowanie historii powłoki (zacieranie śladów)"),
    (r"\bchattr\s+(-R\s+)?\+[a-zA-Z]*i", "chattr +i (blokowanie plików przed usunięciem — technika trwałości)"),
    (r"\bterraform\s+(destroy|apply\b.*-auto-approve)", "terraform destroy / apply -auto-approve"),
    (r"\bmkfs(\.\w+)?\b|\bdd\s+[^;&|]*of=/dev/", "operacje na urządzeniach blokowych"),
    (r"\bchmod\s+(-R\s+)?0?777\b", "chmod 777"),
    (r":\(\)\s*\{\s*:\|:&\s*\};:", "fork bomb"),
    # opcje gita uruchamiające dowolny program: git_exec_option() (po tokenach, bez komunikatów commita)
]

ASK = [
    (r"\bsudo\b", "sudo"),
    (r"\bgit\s+(reset\s+--hard|clean\s+-[a-zA-Z]*f|push\b)", "git reset --hard / clean -f / push"),
    (r"\bterraform\s+(apply|import|state\s+(rm|mv))\b", "zmiana stanu infrastruktury"),
    (r"\b(kubectl\s+(delete|apply|scale|rollout)|helm\s+(install|upgrade|uninstall|rollback))\b", "zmiana w klastrze Kubernetes"),
    (r"\b(npm|pnpm|yarn)\s+publish\b|\bdocker\s+push\b", "publikacja paczki/obrazu"),
    (r"\b(DROP\s+(DATABASE|TABLE|SCHEMA)|TRUNCATE\s+TABLE?)\b", "destrukcyjne SQL"),
    (r"\b(curl|wget)\b.*(\s-d\s*@|--data(-binary)?\s*@|\s-T\s|--upload-file|-F\s+\S+=@|--post-file)", "wysyłanie pliku na zewnątrz"),
    (r"\bcrontab\b(?!\s+-l\b)|\bsystemctl\s+(--user\s+)?(enable|link)\b|\blaunchctl\s+(load|bootstrap)\b|"
     r"(LaunchAgents|LaunchDaemons|/etc/cron\.|/etc/systemd/|\.config/systemd/)",
     "trwałość: cron, usługa systemd lub LaunchAgent"),
    (r"\b(npm\s+(i|install|add)|pnpm\s+(add|i|install)|yarn\s+add|bun\s+add)\b(\s+-{1,2}[\w-]+(=\S+)?)*\s+[@\w][^\s;&|]*",
     "dodanie lub zmiana zależności (łańcuch dostaw)"),
    (r"\b(kubectl|helm|terraform|aws|gcloud|az)\b.*\b(prod|production|prd)\b", "polecenie dotyczące PRODUKCJI"),
]


GIT_GLOBAL_OPTS = re.compile(
    r"\bgit((?:\s+(?:-C\s+\S+|-c\s+\S+|--(?:git-dir|work-tree|namespace|exec-path|config-env)(?:=\S+|\s+\S+)|"
    r"--no-pager|--paginate|-p|-P|--bare|--no-replace-objects|--literal-pathspecs|--no-optional-locks))+)(?=\s)")


def normalize(cmd: str) -> str:
    """`git -C dir push -f` i `git -c a=b reset --hard` to te same operacje co bez opcji globalnych — wzorce widzą
    podkomendę zaraz po `git`."""
    return GIT_GLOBAL_OPTS.sub("git", cmd)


# Zapis plików przez powłokę (D-012): te same reguły co Edit/Write — guard_paths (sekrety, konfiguracja zabezpieczeń)
# i tdd_guard (kod produkcyjny po czerwonym teście). Rozpoznaje przekierowania, tee, sed/perl -i, cp/mv/install oraz
# open(…,'w') / Path(…).write_text / writeFileSync w kodzie podanym w poleceniu. Skrypt uruchomiony z pliku nie jest
# sprawdzany przed wykonaniem — po wykonaniu zmianę kodu zgłasza tdd_guard (git status).
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


# git push/fetch/pull działają poza piaskownicą Bash (sandbox.excludedCommands) — te opcje uruchamiają dowolny program.
# Sprawdzane po tokenach, nie po tekście: nazwa opcji w komunikacie commita (-m '…', heredoc) to dane.
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
                lines.append(line)   # heredoc dla powłoki lub interpretera to kod, nie dane
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
        # kod w argumencie: sh -c "git …", podstawienie $(…) lub `…` w cudzysłowie
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
    """Ścieżki, które polecenie może zapisać (bez wykonywania i bez czytania plików)."""
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
            redirect_next = t.startswith(">")   # operand wejścia albo deskryptor — nie jest celem zapisu
            if not redirect_next:
                cur.append("\0")               # następny token to operand, pomiń
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
            decide("deny", f"Zablokowano: zapis do pliku z sekretami ({t}). Używaj zmiennych środowiskowych i plików "
                           "*.example; zmianę sekretów robi człowiek.")
        if paths.GUARDRAILS.search(norm):
            decide("ask", f"Wymaga zgody: zapis przez powłokę do konfiguracji zabezpieczeń lub .git ({t}).")
        if inside and "$" not in norm:
            production.append(norm)
    mode = os.environ.get("CLAUDE_TDD", "strict").lower()
    if mode == "off" or os.environ.get("CLAUDE_TDD_BASH", "on").lower() == "off":
        return
    tdd = _module("tdd_guard")
    production = [p for p in production if tdd.is_production(p)]
    reason = tdd.bash_pre(data, production) if production else None
    if reason:
        decide("ask" if mode == "ask" else "deny", reason + " Zapis przez powłokę (sed -i, >, tee, cp…) podlega tej "
                                                             "samej bramce co Edit.")


def decide(decision: str, reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": f"[guard_bash] {reason}",
        }
    }, ensure_ascii=False))
    sys.exit(0)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    ti = data.get("tool_input") if isinstance(data, dict) else None
    cmd = ti.get("command") if isinstance(ti, dict) else None
    if not cmd or not isinstance(cmd, str):   # dane spoza formatu Claude Code: decyzja, nie awaria (onFailure: block)
        sys.exit(0)
    cmd = normalize(cmd)
    for pattern, reason in DENY:
        if re.search(pattern, cmd, re.IGNORECASE):
            decide("deny", f"Zablokowano: {reason}. Jeśli to konieczne, poproś człowieka o wykonanie ręczne.")
    if git_exec_option(cmd):
        decide("deny", "Zablokowano: opcja gita uruchamiająca dowolny program (--upload-pack, --receive-pack, "
                       "--exec). Jeśli to konieczne, poproś człowieka o wykonanie ręczne.")
    try:
        check_writes(data, cmd)
    except Exception:
        pass   # błąd rozpoznawania zapisu nigdy nie blokuje (decide kończy proces przez SystemExit — nie łapiemy go)
    for pattern, reason in ASK:
        if re.search(pattern, cmd, re.IGNORECASE):
            decide("ask", f"Wymaga zgody: {reason}.")
    sys.exit(0)  # brak decyzji → normalny przepływ uprawnień


if __name__ == "__main__":
    main()
