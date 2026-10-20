#!/usr/bin/env python3
"""
Bramka TDD: kod produkcyjny dopiero po czerwonym teście. Tylko biblioteka standardowa; błąd hooka nigdy nie blokuje.

Śledzi osobno każdy kontekst (sesja główna i każdy subagent) w `.claude/logs/tdd-state.json`:
  - PostToolUse Edit|Write   — edycja pliku testów;
  - PostToolUse / PostToolUseFailure Bash — uruchomienie testów i jego wynik (czerwony / zielony);
  - PreToolUse Edit|Write    — edycja pliku produkcyjnego: sprawdza regułę.

Reguły:
  A. Pierwsza edycja kodu produkcyjnego w danym kontekście wymaga: edycji testu, a PO NIEJ uruchomienia testów, które
     NIE przeszły (czerwony test — dowód, że test sprawdza brakujące zachowanie). Test, który od razu przeszedł,
     niczego nie dowodzi — wyjątek: test charakteryzujący przed refaktoryzacją, oznaczony w pliku testu słowem
     „charakteryz…”/„characteriz…” (qa-spec-first-testing).
  B. Później: po CLAUDE_TDD_MAX_EDITS (domyślnie 12) edycjach kodu produkcyjnego bez nowej edycji testu — następne
     zachowanie wymaga następnego testu.
  C. Osłabienie testu: edycja pliku testów, która zmniejsza liczbę asercji lub testów albo dopisuje pominięcie
     (skip, xfail, @Disabled, xit…). Tryb CLAUDE_TDD_WEAKEN: warn (domyślnie: ostrzeżenie dla człowieka i kontekst dla modelu, bez blokady),
     ask (decyduje człowiek), deny (blokada), off. Przenoszenie asercji przy refaktoryzacji testów też wywoła regułę —
     dlatego domyślnie tylko ostrzega.
  D. Zapis przez powłokę: guard_bash przed wykonaniem stosuje regułę A/B do celów zapisu (`>`, tee, sed -i, cp/mv…);
     po wykonaniu Bash migawka `git status` (timeout 1,5 s, po przekroczeniu wyłączona do końca sesji; tylko ścieżki,
     mtime i rozmiar, bez treści) zgłasza plik produkcyjny zmieniony bez czerwonego testu (np. skrypt z pliku).
     CLAUDE_TDD_BASH=off wyłącza obie kontrole.
  E. Pętla: ta sama porażka testów (skrót sha1 identyfikatorów testów i typu wyjątku) LOOP_AT razy z rzędu → kontekst
     „zmień podejście albo eskaluj model”, bez blokady; zielony wynik albo inna porażka zeruje licznik.
  F. Pliki chronione: po każdym Bash migawka (ścieżka, mtime, rozmiar — bez treści) `.claude/settings*.json`,
     `.claude/cleanroom.json`, `.claude/hooks/`, `.git/hooks/`, `.git/config` i plików z sekretami w katalogu głównym
     (wzorce guard_paths) → zmiana = kontekst „zatrzymaj się i powiedz człowiekowi” + komunikat dla człowieka. Działa
     także przy CLAUDE_TDD=off; wyłącza CLAUDE_GUARD_CHANGES=off. Wykrywa po fakcie, nie zapobiega (to robi piaskownica
     Bash); zmiana narzędziem Edit/Write (przeszła guard_paths) i pojedyncze `git …` na `.git/config` nie alarmują.

Tryb (zmienna środowiskowa CLAUDE_TDD): strict (domyślnie: blokada z wyjaśnieniem dla agenta), ask (decyduje człowiek),
off (wyłączone — np. spike, prototyp). Pliki nieobjęte: testy, konfiguracja, style i szablony, dokumentacja, `.claude/`,
`factory/`, wygenerowane katalogi; dodatkowe wzorce w CLAUDE_TDD_EXEMPT (oddzielone przecinkami, np. "src/migrations/*").
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".java", ".kt", ".go", ".rs", ".cs", ".rb", ".php",
              ".swift", ".scala"}
TEST_RE = re.compile(
    r"(\.(test|spec)\.[cm]?[jt]sx?$)|(/__tests__/)|(/(tests?|e2e|spec)/)|((^|/)test_[^/]+\.py$)|(_test\.(py|go)$)"
    r"|(/src/test/)|((Test|Tests|IT|Spec)\.(java|kt|cs|scala)$)|(_spec\.rb$)|(\.feature$)|(Test\.php$)", re.I)
EXEMPT_RE = re.compile(
    r"(^|/)(\.claude|factory|docs|node_modules|dist|build|out|coverage|target|vendor|\.git|generated|__generated__)/"
    r"|\.d\.ts$|(^|/)[^/]*\.config\.[cm]?[jt]s$|(^|/)(setup|conftest|manage)\.py$|(^|/)__init__\.py$", re.I)
TEST_CMD_RE = re.compile(
    r"\b((npm|pnpm|yarn|bun)( run)? (test|test:\S+)|npx (vitest|jest|playwright test|mocha)|vitest|jest|mocha"
    r"|pytest|python3? -m (pytest|unittest)|mvnw? (\S+ )*(test|verify)|gradlew? (\S+ )*test|go test|cargo test"
    r"|dotnet test|nx (test|run-many|affected)\b[^\n]*test|ng test|deno test|rspec|phpunit|tox)\b"
    # Testy jako samodzielne skrypty: python3 tests/test_x.py, py -3 .claude\tests\test_x.py, pętla po tests/test_*.py.
    r"|\b(python3?|py)(\s+-\S+)*\s+[\"']?([^\s\"';|&]*[/\\])?(test_[^\s/\\\"';|&]*|[^\s/\\\"';|&]+_test)\.py\b"
    r"|\bfor\s+\w+\s+in\s+[^;\n]*\btest_\*[^;\n]*\.py\b")
FAIL_RE = re.compile(r"\b(FAIL(ED)?|failing|failures?: [1-9]|[1-9]\d* (failed|failing)|AssertionError|"
                     r"Tests?:\s+[1-9]\d* failed|BUILD FAILURE)\b|[✗×] ", re.I)
MARK_RE = re.compile(r"charakteryz|characteriz", re.I)
ASSERT_RE = re.compile(r"\bassert\w*\b|\bexpect\s*\(|\bshould\b|\bverify\s*\(|\bpytest\.raises\b|\bassertThat\b")
TESTDEF_RE = re.compile(r"^\s*(async\s+)?def\s+test\w*|\b(it|test)\s*\(|@(Test|ParameterizedTest)\b|^\s*func\s+Test\w+",
                        re.M)
SKIP_RE = re.compile(r"\.(skip|todo)\s*\(|\b(xit|xdescribe|xtest)\s*\(|@pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\s*\("
                     r"|@(Disabled|Ignore)\b|\bt\.Skip\s*\(|@unittest\.skip", re.M)


def root_of(data: dict) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".")


def rel(path: str, root: Path) -> str:
    p = path.replace("\\", "/")
    r = str(root).replace("\\", "/").rstrip("/") + "/"
    return p[len(r):] if p.startswith(r) else p


def is_test(path: str) -> bool:
    return bool(TEST_RE.search("/" + path))


def is_production(path: str) -> bool:
    if Path(path).suffix.lower() not in SOURCE_EXT or is_test(path) or EXEMPT_RE.search("/" + path):
        return False
    extra = [g.strip() for g in os.environ.get("CLAUDE_TDD_EXEMPT", "").split(",") if g.strip()]
    return not any(fnmatch.fnmatch(path, g) for g in extra)


def load(root: Path) -> dict:
    try:
        return json.loads((root / ".claude" / "logs" / "tdd-state.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save(root: Path, state: dict) -> None:
    p = root / ".claude" / "logs" / "tdd-state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(list(state.items())[-100:]), ensure_ascii=False), encoding="utf-8")


def ctx_key(data: dict) -> str:
    return f"{data.get('session_id') or '?'}:{data.get('agent_id') or 'main'}"


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
# „Czerwony”, który nie wykonał żadnej asercji (brak plików testów, błąd składni w teście, zła konfiguracja runnera).
INVALID_RED_RE = re.compile(
    r"No test files found|No tests found|no tests ran|collected 0 items|\b0 tests? (?:passed|ran|run)\b|"
    r"No tests were executed|Transform failed with \d+ error|\[PARSE_ERROR\]|Your test suite must contain at least one test|"
    r"^(?:E\s+)?\s*(?:SyntaxError|ParseError|IndentationError)\b|"
    r"\.(?:test|spec)\.[cm]?[jt]sx?\(\d+,\d+\): error TS\d+|"
    r"Cannot find module '[^']*\.(?:test|spec)(?:\.[cm]?[jt]sx?)?'", re.I | re.M)
# Brak testowanego modułu lub funkcji to poprawny czerwony („jeszcze tego nie ma”).
VALID_MISSING_RE = re.compile(
    r"Cannot find module '(?![^']*\.(?:test|spec)\b)[^']+'|"
    r"Failed to (?:load|resolve) (?:url|import) [\"']?(?![^\s\"']*\.(?:test|spec)\.)[^\s\"']+|"
    r"No module named '(?![^']*test)[^']+'|cannot import name '[^']+'", re.I)


def response_text(data: dict) -> str:
    resp = data.get("tool_response")
    if isinstance(resp, dict):
        text = f"{resp.get('stdout', '')}\n{resp.get('stderr', '')}\n{resp.get('output', '')}"
    else:
        text = str(resp or "")
    return ANSI_RE.sub("", text[-20000:])


def red_without_assertion(data: dict) -> bool:
    text = response_text(data)
    return bool(INVALID_RED_RE.search(text)) and not VALID_MISSING_RE.search(text)


def bash_failed(data: dict) -> bool:
    if data.get("hook_event_name") == "PostToolUseFailure":
        return True
    resp = data.get("tool_response")
    if isinstance(resp, dict):
        code = resp.get("exit_code", resp.get("exitCode", resp.get("returncode")))
        if isinstance(code, int) and code != 0:
            return True
        text = f"{resp.get('stdout', '')}\n{resp.get('stderr', '')}\n{resp.get('output', '')}"
    else:
        text = str(resp or "")
    return bool(FAIL_RE.search(text[-20000:]))


def deny(reason: str) -> None:
    mode = os.environ.get("CLAUDE_TDD", "strict").lower()
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "ask" if mode == "ask" else "deny",
                                             "permissionDecisionReason": reason}}, ensure_ascii=False))


def weakening(tool: str, inp: dict, root: Path, path: str) -> list[str]:
    """Co osłabia test w tej edycji: mniej asercji, mniej testów, nowe pominięcie."""
    pairs: list[tuple[str, str]] = []
    if tool == "Edit":
        pairs = [(str(inp.get("old_string") or ""), str(inp.get("new_string") or ""))]
    elif tool == "MultiEdit":
        pairs = [(str(e.get("old_string") or ""), str(e.get("new_string") or "")) for e in inp.get("edits") or []]
    elif tool == "Write":
        try:
            pairs = [((root / path).read_text(encoding="utf-8", errors="ignore"), str(inp.get("content") or ""))]
        except OSError:
            return []
    old = "\n".join(a for a, _ in pairs)
    new = "\n".join(b for _, b in pairs)
    found = []
    if len(ASSERT_RE.findall(new)) < len(ASSERT_RE.findall(old)):
        found.append(f"mniej asercji ({len(ASSERT_RE.findall(old))} → {len(ASSERT_RE.findall(new))})")
    if len(TESTDEF_RE.findall(new)) < len(TESTDEF_RE.findall(old)):
        found.append("usunięty test")
    if len(SKIP_RE.findall(new)) > len(SKIP_RE.findall(old)):
        found.append("dopisane pominięcie testu (skip/xfail/disabled)")
    return found


def weaken_check(tool: str, inp: dict, root: Path, path: str) -> None:
    mode = os.environ.get("CLAUDE_TDD_WEAKEN", "warn").lower()
    if mode == "off":
        return
    found = weakening(tool, inp, root, path)
    if not found:
        return
    reason = (f"TDD: ta edycja może osłabić test {path}: {', '.join(found)}. Testów nie osłabiasz, żeby przeszły — "
              "popraw kod albo uzasadnij zmianę testu (zmienione wymaganie, refaktoryzacja testu bez utraty sprawdzeń).")
    if mode in ("ask", "deny"):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": mode,
                                                 "permissionDecisionReason": reason}}, ensure_ascii=False))
    else:   # warn: ostrzeżenie dla człowieka i kontekst dla modelu, bez decyzji o uprawnieniach
        print(json.dumps({"systemMessage": reason,
                          "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": reason}},
                         ensure_ascii=False))


def ctx_state(state: dict, key: str) -> dict:
    s = state.setdefault(key, {"seq": 0, "test_edit": -1, "red": -1, "green": -1, "prod_since_test": 0,
                               "started": False, "marked": False, "green_warned": False})
    s["seq"] += 1
    return s


def may_start(s: dict) -> bool:
    """Reguła A spełniona: czerwony po edycji testu albo zielony oznaczonego testu charakteryzującego."""
    red_after_test = s["test_edit"] >= 0 and s["red"] > s["test_edit"]
    green_after_test = s["test_edit"] >= 0 and s["green"] > s["test_edit"] and s["red"] < s["test_edit"]
    return red_after_test or (green_after_test and s["marked"])


def gate(s: dict, path: str) -> str | None:
    """Reguły A i B dla zmiany pliku produkcyjnego (Edit albo zapis przez Bash); None = dozwolone."""
    if not s["started"]:
        if may_start(s):
            s["started"] = True
            return None
        green_after_test = s["test_edit"] >= 0 and s["green"] > s["test_edit"] and s["red"] < s["test_edit"]
        if green_after_test and not s["green_warned"]:
            s["green_warned"] = True
            return ("TDD: nowy test od razu PRZESZEDŁ, więc niczego nie dowodzi. Popraw test tak, żeby sprawdzał "
                    "brakujące zachowanie i nie przechodził (czerwony z właściwego powodu), uruchom go i dopiero "
                    "wtedy pisz kod. Jeśli to test charakteryzujący przed refaktoryzacją, oznacz go w pliku testu "
                    "jako [charakteryzujący] (qa-spec-first-testing).")
        return (f"TDD: zanim zmienisz kod produkcyjny ({path}), napisz test opisujący oczekiwane zachowanie "
                "(przy błędzie: test odtwarzający błąd), uruchom testy i pokaż, że ten test NIE przechodzi "
                "z właściwego powodu. Potem minimalny kod → zielony → refaktoryzacja (eng-testing). Wyjątki: "
                "konfiguracja, style, dokumentacja; spike — człowiek ustawia CLAUDE_TDD=off.")
    limit = int(os.environ.get("CLAUDE_TDD_MAX_EDITS", "12") or 12)
    if s["prod_since_test"] >= limit:
        return (f"TDD: {s['prod_since_test']} zmian kodu produkcyjnego bez nowego testu. Następne zachowanie = "
                "następny test: dopisz test (czerwony), potem kod. Jeśli to tylko refaktoryzacja przy zielonych "
                "testach, uruchom testy i dopisz/zaktualizuj test, który ją zabezpiecza.")
    return None


def bash_pre(data: dict, paths: list[str]) -> str | None:
    """Dla guard_bash: zapis plików produkcyjnych przez polecenie powłoki podlega tym samym regułom co Edit."""
    if os.environ.get("CLAUDE_TDD", "strict").lower() == "off" or not paths:
        return None
    root = root_of(data)
    state = load(root)
    s = ctx_state(state, ctx_key(data))
    reason = gate(s, paths[0])
    s["ts"] = int(time.time())
    save(root, state)
    return reason


SNAP_MAX = 300   # tyle plików produkcyjnych naraz zmienionych w drzewie roboczym śledzimy; więcej → kontrola wyłączona


def bash_changes(root: Path, state: dict, data: dict) -> list[str]:
    """Pliki produkcyjne zmienione od poprzedniego polecenia (git status + mtime i rozmiar, bez treści).
    Pierwsze wywołanie w sesji tylko zapisuje stan wyjściowy. Timeout albo brak gita → wyłączone do końca sesji."""
    if not (root / ".git").exists():
        return []
    snap = state.setdefault("snap:" + str(data.get("session_id") or "?"), {})
    if snap.get("off"):
        return []
    try:
        out = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "-z"],
                             capture_output=True, timeout=1.5).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        snap["off"] = True
        return []
    entries, cur = out.split("\0"), {}
    skip = False
    for e in entries:
        if skip:
            skip = False
            continue
        if len(e) < 4:
            continue
        skip = e[0] in "RC"   # przy zmianie nazwy następny wpis to stara ścieżka
        path = e[3:]
        if is_production(path):
            try:
                st = (root / path).stat()
                cur[path] = [st.st_mtime_ns, st.st_size]
            except OSError:
                pass
    if len(cur) > SNAP_MAX:
        snap.clear()
        snap["off"] = True
        return []
    prev = snap.get("files")
    snap["files"] = cur
    if not isinstance(prev, dict):
        return []
    return sorted(p for p, v in cur.items() if prev.get(p) != v)


GUARD_FILES = (".claude/settings.json", ".claude/settings.local.json", ".claude/cleanroom.json", ".git/config")
GUARD_DIRS = (".claude/hooks", ".git/hooks")
GUARD_MAX = 200   # tyle plików chronionych najwyżej śledzimy (stat, bez treści)
GIT_ONLY_RE = re.compile(r"^\s*git\s[^;&|`$()<>\n]*$")


def _secret_res():
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_guard_paths", Path(__file__).with_name("guard_paths.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.SECRET_PATHS, mod.SAFE_ENV
    except Exception:
        return (re.compile(r"(^|/)\.env(\.[\w-]+)?$|\.(pem|key)$", re.I),
                re.compile(r"\.env\.(example|sample|template|dist)$", re.I))


def guarded_snapshot(root: Path) -> dict:
    """Ścieżka → [mtime_ns, rozmiar] plików chronionych i plików z sekretami w katalogu głównym; treści nie czyta."""
    paths = [root / f for f in GUARD_FILES]
    for d in GUARD_DIRS:
        try:
            for dirpath, dirs, files in os.walk(root / d):
                dirs[:] = [x for x in dirs if x != "__pycache__"]
                paths += [Path(dirpath) / f for f in files if not f.endswith(".sample")]
        except OSError:
            pass
    secret, safe = _secret_res()
    try:
        paths += [e for e in root.iterdir() if secret.search(e.name) and not safe.search(e.name)]
    except OSError:
        pass
    cur = {}
    for p in paths[:GUARD_MAX]:
        try:
            st = p.stat()
            if p.is_file():
                cur[p.relative_to(root).as_posix()] = [st.st_mtime_ns, st.st_size]
        except (OSError, ValueError):
            pass
    return cur


def guard_changes(root: Path, state: dict, data: dict) -> list[str]:
    """Reguła F: pliki chronione i z sekretami zmienione od poprzedniego polecenia. Pierwsze wywołanie w sesji tylko
    zapisuje stan wyjściowy; pojedyncze polecenie `git …` może zmienić `.git/config` (push -u, branch)."""
    key = "guard:" + str(data.get("session_id") or "?")
    prev, cur = state.get(key), guarded_snapshot(root)
    state[key] = cur
    if not isinstance(prev, dict):
        return []
    changed = []
    for p in sorted(set(prev) | set(cur)):
        if prev.get(p) == cur.get(p):
            continue
        if p == ".git/config" and GIT_ONLY_RE.match(str((data.get("tool_input") or {}).get("command") or "")):
            continue
        changed.append(f"{p} ({'nowy' if p not in prev else 'usunięty' if p not in cur else 'zmieniony'})")
    return changed


def guard_note(root: Path, state: dict, data: dict) -> dict:
    """Wyjście reguły F (kontekst dla modelu i komunikat dla człowieka) albo {}; tylko ścieżki, bez treści."""
    if os.environ.get("CLAUDE_GUARD_CHANGES", "on").lower() == "off":
        return {}
    event, tool = data.get("hook_event_name"), data.get("tool_name") or ""
    if event == "PostToolUse" and tool in ("Edit", "Write", "MultiEdit"):
        key = "guard:" + str(data.get("session_id") or "?")
        if isinstance(state.get(key), dict):   # zmiana narzędziem przeszła guard_paths — nowy stan wyjściowy
            state[key] = guarded_snapshot(root)
        return {}
    if not (event in ("PostToolUse", "PostToolUseFailure") and tool == "Bash"):
        return {}
    changed = guard_changes(root, state, data)
    if not changed:
        return {}
    names = ", ".join(changed[:8])
    return {"context": (f"[tdd_guard] Polecenie zmieniło pliki chronione lub z sekretami: {names}. Zatrzymaj się i "
                        "powiedz człowiekowi, co je zmieniło i dlaczego; nie czytaj ich treści i nie cofaj zmian "
                        "człowieka (core-agent-security)."),
            "human": f"⚠ tdd_guard: polecenie Bash zmieniło pliki chronione: {names} — sprawdź, czy to zamierzone."}


FAIL_ID_RES = [
    re.compile(r"^FAILED (\S+::\S+)", re.M),                                                    # pytest
    re.compile(r"^\s*(?:FAIL|×|✗)\s+(\S+\.(?:test|spec)\.\S+(?:\s+>\s+.+?)?)\s*$", re.M),       # vitest
    re.compile(r"^\s*● (.+?)\s*$", re.M),                                                         # jest
    re.compile(r"--- FAIL: (\S+)"),                                                              # go
]
EXC_RE = re.compile(r"\b([A-Z]\w*(?:Error|Exception|Failure))\b")
LOOP_AT = 3


def same_failure(s: dict, text: str) -> str:
    """Odcisk porażki = skrót (id padających testów + typy wyjątków); w stanie tylko skrót. Co LOOP_AT powtórzeń
    tego samego odcisku z rzędu → podpowiedź zmiany podejścia (bez blokady)."""
    ids = sorted({m for r in FAIL_ID_RES for m in r.findall(text)})
    exc = sorted(set(EXC_RE.findall(text)))
    if not ids and not exc:
        s["fail_fp"], s["fail_n"] = None, 0
        return ""
    fp = hashlib.sha1("\n".join(ids + ["--"] + exc).encode("utf-8")).hexdigest()[:12]
    s["fail_n"] = s.get("fail_n", 0) + 1 if s.get("fail_fp") == fp else 1
    s["fail_fp"] = fp
    if s["fail_n"] % LOOP_AT:
        return ""
    return (f"[tdd_guard] Ta sama porażka {s['fail_n']}. raz z rzędu (ten sam test i typ błędu) — zmień podejście "
            "albo eskaluj model (core-cost-control): nazwij, co nie zadziałało, sprawdź założenie o przyczynie, "
            "zamiast kolejnej podobnej poprawki.")


def emit(event: str, notes: list[str], guard: dict) -> None:
    notes = [n for n in notes + [guard.get("context", "")] if n]
    if notes:
        out = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": "\n".join(notes)}}
        if guard.get("human"):
            out["systemMessage"] = guard["human"]
        print(json.dumps(out, ensure_ascii=False))


def main() -> int:
    try:
        data = json.load(sys.stdin)
        root = root_of(data)
        event = data.get("hook_event_name")
        state = load(root)
        guard = guard_note(root, state, data)   # reguła F działa też przy CLAUDE_TDD=off
    except Exception:
        return 0
    if os.environ.get("CLAUDE_TDD", "strict").lower() == "off":
        try:
            if str(event).startswith("PostToolUse"):
                emit(event, [], guard)
                save(root, state)
        except Exception:
            pass
        return 0
    try:
        tool = data.get("tool_name") or ""
        inp = data.get("tool_input") or {}
        key = ctx_key(data)
        s = ctx_state(state, key)
        path = rel(str(inp.get("file_path") or inp.get("notebook_path") or ""), root)

        if event in ("PostToolUse", "PostToolUseFailure") and tool == "Bash":
            notes = []
            if TEST_CMD_RE.search(str(inp.get("command") or "")):
                if bash_failed(data):
                    s["red"] = s["seq"]
                    if red_without_assertion(data):
                        notes.append("[tdd_guard] To uruchomienie nie wykonało asercji (brak plików testów, błąd "
                                     "składni albo konfiguracji runnera) — to nie jest czerwony test. Napraw "
                                     "uruchomienie i zobacz test padający na brakującym zachowaniu, zanim napiszesz "
                                     "kod produkcyjny.")
                    notes.append(same_failure(s, response_text(data)))
                else:
                    s["green"] = s["seq"]
                    s["fail_fp"], s["fail_n"] = None, 0
            if os.environ.get("CLAUDE_TDD_BASH", "on").lower() != "off":
                changed = bash_changes(root, state, data)
                if changed and not (s["started"] or may_start(s)):
                    notes.append(f"[tdd_guard] TDD: polecenie zmieniło kod produkcyjny bez czerwonego testu: "
                                 f"{', '.join(changed[:5])}. Jeśli to zmiana z tego polecenia, cofnij ją albo najpierw "
                                 "napisz test i pokaż, że nie przechodzi. Zmian człowieka nie cofaj.")
            emit(event, notes, guard)
        elif event == "PostToolUse" and tool in ("Edit", "Write", "MultiEdit") and path:
            if is_test(path):
                s["test_edit"], s["prod_since_test"] = s["seq"], 0
                try:
                    s["marked"] = s["marked"] or bool(MARK_RE.search((root / path).read_text(encoding="utf-8",
                                                                                                errors="ignore")))
                except OSError:
                    pass
            elif is_production(path):
                s["prod_since_test"] += 1
                snap = state.get("snap:" + str(data.get("session_id") or "?"))
                if isinstance(snap, dict) and isinstance(snap.get("files"), dict):   # zmiana przez Edit przeszła bramkę
                    try:
                        st = (root / path).stat()
                        snap["files"][path] = [st.st_mtime_ns, st.st_size]
                    except OSError:
                        snap["files"].pop(path, None)
        elif event == "PreToolUse" and tool in ("Edit", "Write", "MultiEdit") and path and is_test(path):
            weaken_check(tool, inp, root, path)
            return 0
        elif event == "PreToolUse" and tool in ("Edit", "Write", "MultiEdit") and path and is_production(path):
            reason = gate(s, path)
            if reason:
                deny(reason)
                save(root, state)
                return 0
        s["ts"] = int(time.time())
        save(root, state)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
