#!/usr/bin/env python3
"""
tf init / tf analyze — katalog `.tf/` na wyniki pracy fabryki i modułowy przegląd projektu (piętro 0: skrypty).

  python3 factory/analyze.py init                      # szkielet .tf/ (idempotentnie) i mapa katalogu
  python3 factory/analyze.py list                      # dostępne moduły i czy stosują się do repo
  python3 factory/analyze.py run [--only a,b] [--since <commit>] [--top N]

Moduł to katalog z `analyzer.yaml` (name, prefix, title, description, version, applies_when.files_any,
tier0.script) w `factory/analyzers/`, `.tf/analyzers/` albo katalogach z `TF_ANALYZERS_PATH`. Skrypt piętra 0
dostaje `--root <repo> [--files a,b]` i wypisuje ustalenia jako JSON Lines (rule, title, file, line, snippet,
severity, confidence, evidence, basis, suggestion). Rdzeń nadaje stabilne `id` (`<prefix>-<6 hex>` z reguły, pliku
i treści, bez numeru linii), deduplikuje, szereguje, pisze `.tf/reports/<moduł>.md` (checkboxy scalane przy ponownej
analizie po `id`), `.tf/reports/<moduł>.json` (pełna lista), `.tf/reports/README.md` (przegląd) i rejestr
`.tf/register/items.jsonl`. Cache: `.tf/cache/analyze/<moduł>.json` po commicie (`TF_ANALYZE_NO_CACHE=1` wyłącza).
Piętra 1–3 (model, przeglądarka, weryfikacja) jeszcze nie istnieją — raport mówi to w zakresie.
Plan: docs/plans/2026-11-08-krok-1-tf-analyze-rdzen.md w repozytorium fabryki. Tylko biblioteka standardowa + PyYAML.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # dołączona kopia PyYAML (factory/_vendor)
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
    import yaml

TF = Path(".tf")
SEVERITY = ["krytyczna", "wysoka", "średnia", "niska"]
NOTE = "  ↳ "  # adnotacje rdzenia w liście działań (odtwarzane przy każdej analizie; notatki człowieka zostają)
DIRS = {
    "reports": ("Raporty `tf analyze`: przegląd (ten plik po pierwszej analizie), `<moduł>.md` z listą działań "
                "do odhaczania i `<moduł>.json` z pełną listą ustaleń.", True),
    "register": ("Rejestr pracy: `items.jsonl`, jedna pozycja na linię (ustalenia analizy; później zadania, pytania, "
                 "decyzje). Piszą `tf analyze` i persony; odhaczenie w raporcie zmienia status tutaj.", True),
    "cache": ("Wyniki pośrednie i odciski analiz (po commicie). Odtwarzalne — można usunąć.", False),
    "logs": ("Logi pracy fabryki (zużycie, podpowiedzi, bramka jakości). Można usunąć.", False),
    "runs": ("Przebiegi wykonawcze trybów. Można usunąć po zakończeniu pracy.", False),
    "backup": ("Kopie plików z aktualizacji i usuwania nakładek. Można usunąć, gdy niepotrzebne.", False),
}
SHORT = {"reports": "raporty analiz z listą działań", "register": "rejestr pracy (ustalenia, później zadania i decyzje)",
         "cache": "wyniki pośrednie, odtwarzalne", "logs": "logi pracy fabryki", "runs": "przebiegi wykonawcze",
         "backup": "kopie z aktualizacji"}
CONFIG = "analyze:\n  top: 10\n  modules: {}\nproject_record: docs/project\n"


# ───────────── narzędzia ─────────────

def git(root: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, errors="replace", timeout=120)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)}: kod {r.returncode}")
    return r.stdout if r.returncode == 0 else ""


def glob_re(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(f"^{out}$")


def load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}


def today() -> str:
    return dt.date.today().isoformat()


# ───────────── init ─────────────

def cmd_init(root: Path) -> int:
    base = root / TF
    for d, (text, in_git) in DIRS.items():
        (base / d).mkdir(parents=True, exist_ok=True)
        readme = base / d / "README.md"
        if not readme.exists():
            where = "w gicie (instalacja zespołowa)" if in_git else "poza gitem"
            readme.write_text(f"# .tf/{d}/\n\n{text}\n\nGit: {where}.\n", encoding="utf-8")
    cfg = base / "config.yaml"
    if not cfg.exists():
        cfg.write_text(CONFIG, encoding="utf-8")
    note = git_rules(root)
    print("✓ .tf/ — wyniki pracy fabryki:")
    print("  config.yaml   ustawienia (moduły analizy, top N, ścieżka dziennika projektu)")
    for d, (text, in_git) in DIRS.items():
        print(f"  {d + '/':<13} {'git (zespołowa)' if in_git else 'poza gitem':<16} {SHORT[d]}")
    if note:
        print(note)
    return 0


def git_rules(root: Path) -> str:
    if not (root / ".git").exists():
        return ""
    manifest = root / ".claude" / "factory-manifest.json"
    try:
        mode = json.loads(manifest.read_text(encoding="utf-8")).get("mode", "private")
    except (OSError, ValueError):
        mode = "private"
    if mode == "shared":
        target, lines = root / ".gitignore", [f".tf/{d}/" for d, (_t, g) in DIRS.items() if not g]
    else:
        target, lines = root / ".git" / "info" / "exclude", [".tf/"]
    old = target.read_text(encoding="utf-8") if target.exists() else ""
    missing = [ln for ln in lines if ln not in old.splitlines()]
    if missing:
        target.parent.mkdir(parents=True, exist_ok=True)
        sep = "" if not old or old.endswith("\n") else "\n"
        target.write_text(old + sep + "\n".join(missing) + "\n", encoding="utf-8")
    rel = target.relative_to(root)
    return f"  git: {', '.join(lines)} w {rel}" if mode == "shared" else f"  git: .tf/ w {rel} (instalacja prywatna)"


# ───────────── moduły ─────────────

def module_dirs(root: Path) -> list[Path]:
    dirs = [root / "factory" / "analyzers", root / TF / "analyzers"]
    dirs += [Path(p) for p in os.environ.get("TF_ANALYZERS_PATH", "").split(os.pathsep) if p]
    return dirs


def discover(root: Path) -> list[dict]:
    mods, seen = [], set()
    for d in module_dirs(root):
        for y in sorted(d.glob("*/analyzer.yaml")) if d.is_dir() else []:
            m = load_yaml(y)
            name = m.get("name") or y.parent.name
            if name in seen:
                continue
            seen.add(name)
            m.update(name=name, _dir=y.parent, prefix=str(m.get("prefix") or name[:3]).upper())
            mods.append(m)
    return mods


def applies(m: dict, files: list[str]) -> str | None:
    """None, gdy moduł się stosuje; inaczej powód pominięcia."""
    pats = ((m.get("applies_when") or {}).get("files_any")) or []
    if not pats:
        return None
    res = [glob_re(p) for p in pats]
    return None if any(r.match(f) for f in files for r in res) else f"brak plików pasujących do {', '.join(pats)}"


def repo_files(root: Path) -> list[str]:
    return [f for f in git(root, "ls-files", check=False).splitlines() if f]


def cmd_list(root: Path) -> int:
    mods = discover(root)
    if not mods:
        print("Brak modułów analizy. Moduły dokładają nakładki (krok 2 planu) albo katalog .tf/analyzers/; "
              "katalogi: " + ", ".join(str(d) for d in module_dirs(root)))
        return 0
    files = repo_files(root)
    for m in mods:
        why = applies(m, files)
        print(f"  {m['name']:<16} {m.get('version', '?'):<8} {m.get('description', '')}"
              f" — {'stosuje się' if why is None else 'pominięty: ' + why}")
    return 0


# ───────────── ustalenia ─────────────

def finding_id(prefix: str, f: dict) -> str:
    snippet = " ".join(str(f.get("snippet", "")).split())
    h = hashlib.sha1(f"{f.get('rule', '')}|{f.get('file', '')}|{snippet}".encode()).hexdigest()[:6]
    return f"{prefix}-{h}"


def rank(f: dict) -> tuple:
    sev = SEVERITY.index(f["severity"]) if f.get("severity") in SEVERITY else len(SEVERITY)
    return sev, -float(f.get("confidence") or 0), f.get("file", ""), int(f.get("line") or 0)


def run_script(m: dict, root: Path, files: list[str] | None) -> tuple[list[dict], str | None]:
    script = (m.get("tier0") or {}).get("script")
    if not script:
        return [], "brak tier0.script w analyzer.yaml"
    cmd = [sys.executable, str(m["_dir"] / script), "--root", str(root)]
    if files is not None:
        cmd += ["--files", ",".join(files)]
    try:
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, errors="replace", timeout=600)
    except subprocess.TimeoutExpired:
        return [], "przekroczony czas 600 s"
    if r.returncode != 0:
        return [], f"kod wyjścia {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}"
    out = []
    for i, line in enumerate(r.stdout.splitlines(), 1):
        if not line.strip():
            continue
        try:
            f = json.loads(line)
        except ValueError:
            return [], f"linia {i} wyjścia to nie JSON: {line[:120]}"
        if not isinstance(f, dict) or not f.get("rule") or not f.get("file"):
            return [], f"linia {i}: ustalenie bez pól rule i file"
        out.append(f)
    return out, None


def dedupe(m: dict, raw: list[dict], prev: dict[str, dict], commit: str) -> list[dict]:
    by_id: dict[str, dict] = {}
    for f in sorted(raw, key=lambda x: int(x.get("line") or 0)):
        fid = finding_id(m["prefix"], f)
        if fid in by_id:
            continue
        f = dict(f, id=fid, module=m["name"], kind="finding", commit=commit,
                 first_seen=(prev.get(fid) or {}).get("first_seen") or today())
        by_id[fid] = f
    return sorted(by_id.values(), key=rank)


def analyze_module(m: dict, root: Path, head: str, clean: bool, since: str | None) -> tuple[list[dict], str | None, str]:
    """(ustalenia, błąd, opis zakresu)."""
    reports = root / TF / "reports"
    cache = root / TF / "cache" / "analyze" / f"{m['name']}.json"
    prev_json = load_json(reports / f"{m['name']}.json")
    prev = {f["id"]: f for f in prev_json.get("findings", [])}
    version = str(m.get("version", ""))
    c = load_json(cache)
    if (not os.environ.get("TF_ANALYZE_NO_CACHE") and not since and clean and c.get("commit") == head
            and c.get("version") == version):
        return c.get("findings", []), None, "wynik z cache (ten sam commit i wersja modułu)"
    files, scope = None, "całe repozytorium"
    if since:
        files = [f for f in git(root, "diff", "--name-only", f"{since}..HEAD").splitlines() if f]
        scope = f"pliki zmienione od {since[:7]} ({len(files)}); ustalenia pozostałych plików z poprzedniej analizy"
    raw, err = run_script(m, root, files)
    if err:
        return [], err, scope
    found = dedupe(m, raw, prev, head)
    if since:
        changed = set(files or [])
        found = sorted(found + [f for f in prev.values() if f.get("file") not in changed
                                and f["id"] not in {x["id"] for x in found}], key=rank)
    if clean and not since:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"commit": head, "version": version, "findings": found}, ensure_ascii=False,
                                    indent=1) + "\n", encoding="utf-8")
    return found, None, scope


def load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# ───────────── raport i scalanie ─────────────

ITEM = re.compile(r"^- \[( |x|X)\] ([A-Z0-9]+-[0-9a-f]{6})\b")


def parse_actions(text: str) -> list[dict]:
    """Pozycje listy działań w kolejności: id, checked, header, notes (notatki człowieka)."""
    if "## Rekomendowane działania" not in text:
        return []
    body = text.split("## Rekomendowane działania", 1)[1].split("\n## ", 1)[0]
    items: list[dict] = []
    for line in body.splitlines():
        mt = ITEM.match(line)
        if mt:
            items.append({"id": mt.group(2), "checked": mt.group(1) != " ", "header": line, "notes": []})
        elif items and line.startswith("  ") and not line.startswith(NOTE):
            items[-1]["notes"].append(line)
    return items


def history(text: str) -> list[str]:
    if "## Historia analiz" not in text:
        return []
    return [ln for ln in text.split("## Historia analiz", 1)[1].splitlines() if ln.startswith("- ")]


def header(f: dict, checked: bool) -> str:
    return (f"- [{'x' if checked else ' '}] {f['id']} — {f.get('title') or f['rule']} "
            f"({f['file']}:{f.get('line', '?')}) — {f.get('severity', '?')}")


def write_report(m: dict, root: Path, found: list[dict], err: str | None, scope: str, head: str, top: int,
                 register: dict[str, dict]) -> tuple[str, int]:
    path = root / TF / "reports" / f"{m['name']}.md"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    prev_ids = {f["id"] for f in load_json(root / TF / "reports" / f"{m['name']}.json").get("findings", [])}
    now = {f["id"]: f for f in found}
    old_items = parse_actions(old)
    actions, open_n = [], 0
    for it in old_items:
        f = now.get(it["id"])
        lines = [header(f, it["checked"]) if f else it["header"]] + it["notes"]
        if f and it["checked"]:
            lines.append(NOTE + "analiza wciąż widzi problem — sprawdź, czy poprawka objęła ten przypadek")
        if not f and not it["checked"] and not err:
            lines.append(NOTE + "wygląda na naprawione — potwierdź (odhacz)")
        if f and not it["checked"]:
            open_n += 1
        reg = register.get(it["id"])
        if reg is not None:
            reg["status"] = "rozstrzygnięte" if it["checked"] else "otwarte"
            reg["note"] = lines[-1][len(NOTE):] if lines[-1].startswith(NOTE) else ""
        actions += lines
    listed = {it["id"] for it in old_items}
    for f in found[:top]:
        if f["id"] not in listed:
            actions.append(header(f, False))
            open_n += 1
    verdict = "BŁĄD" if err else ("DO POPRAWY" if open_n else "OK")
    tiers = "piętro 0 (skrypty); piętra 1–3 (model, przeglądarka, weryfikacja drugim agentem) jeszcze nie istnieją"
    lines = [f"# {m.get('title', m['name'])} — raport tf analyze",
             f"Werdykt: {verdict} · {today()} · commit {head[:7]} · moduł {m['name']} {m.get('version', '')} · "
             f"koszt: 0 USD (piętro 0)", "", "## Zakres", f"- Zbadano: {scope}.", f"- Piętra: {tiers}."]
    if err:
        lines.append(f"- Moduł nie powiódł się: {err}. Brak ustaleń nie jest tu wynikiem.")
    lines += ["", "## Ustalenia", ""]
    if found:
        lines += [f"- **{f['id']}** {f.get('severity', '?')} (pewność {f.get('confidence', '?')}) — "
                  f"{f.get('title') or f['rule']} — `{f['file']}:{f.get('line', '?')}`"
                  + (f"; dowód: {f['evidence']}" if f.get("evidence") else "")
                  + (f"; podstawa: {f['basis']}" if f.get("basis") else "")
                  + (f"; co zrobić: {f['suggestion']}" if f.get("suggestion") else "") for f in found[:top]]
        if len(found) > top:
            lines.append(f"- … i {len(found) - top} więcej w `{m['name']}.json`.")
    else:
        lines.append("- brak" if not err else "- brak (moduł nie powiódł się)")
    gone = len(prev_ids - set(now)) if not err else 0
    hist = history(old) + [f"- {today()} · {head[:7]} · ustaleń: {len(found)} (nowe: {len(set(now) - prev_ids)}, "
                           f"zniknęło: {gone}) · {verdict}"]
    lines += ["", "## Rekomendowane działania", "", *(actions or ["- brak"]), "", "## Historia analiz", "", *hist]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not err:
        (root / TF / "reports" / f"{m['name']}.json").write_text(json.dumps(
            {"module": m["name"], "version": m.get("version"), "commit": head, "date": today(), "findings": found},
            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return verdict, open_n


def update_register(root: Path, found_by_module: dict[str, list[dict]]) -> dict[str, dict]:
    path = root / TF / "register" / "items.jsonl"
    reg: dict[str, dict] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                x = json.loads(line)
                reg[x["id"]] = x
            except (ValueError, KeyError):
                continue
    for mod, found in found_by_module.items():
        for f in found:
            x = reg.get(f["id"])
            if x is None:
                reg[f["id"]] = {"id": f["id"], "kind": "finding", "module": mod, "title": f.get("title") or f["rule"],
                                "status": "otwarte", "source": "tf analyze", "refs": [f"{f['file']}:{f.get('line')}"],
                                "created": today(), "updated": today(), "note": ""}
            else:
                x.update(title=f.get("title") or f["rule"], refs=[f"{f['file']}:{f.get('line')}"], updated=today())
    return reg


def save_register(root: Path, reg: dict[str, dict]) -> None:
    path = root / TF / "register" / "items.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(reg[k], ensure_ascii=False, sort_keys=True) + "\n" for k in sorted(reg)),
                    encoding="utf-8")


def cmd_run(root: Path, only: list[str], since: str | None, top: int | None) -> int:
    if not (root / TF / "config.yaml").exists():
        cmd_init(root)
    cfg = load_yaml(root / TF / "config.yaml")
    top = top or int(((cfg.get("analyze") or {}).get("top")) or 10)
    mods = [m for m in discover(root) if not only or m["name"] in only]
    if not mods:
        print("Brak modułów analizy do uruchomienia (tf analyze --list).")
        return 0
    head = git(root, "rev-parse", "HEAD").strip()
    clean = not git(root, "status", "--porcelain", "--", ".", ":(exclude).tf").strip()
    files = repo_files(root)
    results, failed, skipped = {}, False, []
    for m in mods:
        why = applies(m, files)
        if why:
            skipped.append((m, why))
            continue
        results[m["name"]] = (m, *analyze_module(m, root, head, clean, since))
    reg = update_register(root, {n: r[1] for n, r in results.items() if not r[2]})
    rows = []
    for name, (m, found, err, scope) in results.items():
        verdict, open_n = write_report(m, root, found, err, scope, head, top, reg)
        failed |= bool(err)
        rows.append(f"| [{name}]({name}.md) | {verdict} | {open_n} | {len(found)} |")
        print(f"{'✗' if err else '✓'} {name}: {verdict} — ustaleń {len(found)}, do zrobienia {open_n}"
              + (f" ({err})" if err else ""))
    save_register(root, reg)
    for m, why in skipped:
        rows.append(f"| {m['name']} | pominięty: {why} | — | — |")
        print(f"- {m['name']}: pominięty ({why})")
    (root / TF / "reports" / "README.md").write_text("\n".join(
        ["# Raporty tf analyze", f"Stan: {today()} · commit {head[:7]}", "",
         "| Moduł | Werdykt | Do zrobienia | Ustaleń |", "|---|---|---|---|", *rows, "",
         "Lista działań w raporcie modułu jest widokiem rejestru `.tf/register/items.jsonl`: odhaczenie zmienia "
         "status pozycji przy następnej analizie."]) + "\n", encoding="utf-8")
    return 1 if failed else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("list")
    r = sub.add_parser("run")
    r.add_argument("--only", default="")
    r.add_argument("--since")
    r.add_argument("--top", type=int)
    a = ap.parse_args(argv)
    root = Path.cwd()
    try:
        if a.cmd == "init":
            return cmd_init(root)
        if a.cmd == "list":
            return cmd_list(root)
        return cmd_run(root, [x for x in a.only.split(",") if x], a.since, a.top)
    except RuntimeError as e:
        print(f"✗ {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
