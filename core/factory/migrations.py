#!/usr/bin/env python3
"""
Core migrations — auto-correction of project files after changes in the factory's public API (.tf/factory/PUBLIC_API.md).

  python3 .tf/factory/migrations.py            # show what needs fixing (changes nothing)
  python3 .tf/factory/migrations.py --apply    # fix it

They are run by the installer (after every update) and `tf doctor --fix`. Only project files the factory did not install are fixed:
own personas and roles (`.tf/config/personas/`, `.tf/config/roles/`), own overlays
(`.tf/factory/packs/<id>/` outside the manifest) and own skills (`.claude/skills/<skill>/SKILL.md` outside the manifest).
The installer updates factory files. Standard library + PyYAML (via packs.py) to read pack.yaml.

Value migrations (`migrate_values`: 11.0.0, 12.0.0, 13.0.0, 14.0.0, 19.0.0) rewrite old identifiers, headings and labels
in the project data the factory's scripts read (tasks, runs, configuration, journals, checkpoints, caches); 19.0.0 covers
the Polish forms from before 14.x that the readers no longer accept.

A new rename in the core = a new entry in RENAMES (with the core version from which it applies). A rename in an overlay =
an entry `renames: {"<version>": {old: new}}` in its pack.yaml (also works for overlays outside the factory repository).
"""
from __future__ import annotations

import json
import re
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: the cp1250 code page lacks “✓”, “⚠” — always UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # child processes (build.py, tests, hooks) also write and read UTF-8

sys.dont_write_bytecode = True   # engine in .tf/factory/ without __pycache__ (like node_modules — code only)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# core version → old name → new name (skills, traits, roles)
RENAMES: dict[str, dict[str, str]] = {
    "3.0.0": {
        "core-tech-docs": "docs-tech-writing",          # pack-docs
        "fe-ux-design": "ux-feature-design",            # pack-ux
    },
    "5.0.0": {
        "core-story-run": "tf",                         # the “task → PR” loop (until 9.33 the talos-story-run skill of the mode-talos mode)
    },
    "10.0.0": {
        "talos-story-run": "tf",                        # loop moved from the mode-talos mode to the core
    },
}


def factory_files(root: Path) -> set[str]:
    try:
        return set(json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get("files") or {})
    except (OSError, ValueError):
        return set()


def own_files(root: Path) -> list[Path]:
    """Project files that may refer to factory names and that the factory does not install."""
    installed = factory_files(root)
    cands = [*(root / ".tf" / "config" / "personas").glob("*.yaml"), *(root / ".tf" / "config" / "roles").glob("*.yaml"),
             *(root / ".tf" / "factory" / "packs").glob("*/**/*.yaml"), *(root / ".claude" / "skills").glob("*/SKILL.md")]
    return [p for p in cands if p.is_file() and p.relative_to(root).as_posix() not in installed]


def pack_renames(root: Path) -> dict[str, str]:
    """Renames declared by installed overlays (`renames` w .tf/factory/packs/<id>/pack.yaml)."""
    base = root / ".tf" / "factory" / "packs"
    files = sorted(base.glob("*/pack.yaml")) if base.is_dir() else []
    if not files:
        return {}
    import importlib.util
    spec = importlib.util.spec_from_file_location("tf_packs_mig", Path(__file__).resolve().parent / "packs.py")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    out: dict[str, str] = {}
    for f in files:
        for table in (pm.load_yaml(f).get("renames") or {}).values():
            out.update({str(k): str(v) for k, v in (table or {}).items()})
    return out


def apply(root: Path = ROOT, dry: bool = True) -> list[str]:
    """Renames in project files. Returns a description of the changes (with dry=True — changes to be made)."""
    mapping = {old: new for table in RENAMES.values() for old, new in table.items()}
    mapping.update(pack_renames(root))
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, mapping)) + r")\b")
    out = []
    for p in own_files(root):
        text = p.read_text(encoding="utf-8")
        hits = sorted(set(pattern.findall(text)))
        if not hits:
            continue
        out.append(f"{p.relative_to(root).as_posix()}: " + ", ".join(f"{h} → {mapping[h]}" for h in hits))
        if not dry:
            p.write_text(pattern.sub(lambda m: mapping[m.group(1)], text), encoding="utf-8")
    return out


# 11.0.0: task state, loop and configuration identifiers in English (descriptions stay in Polish)
VALUES = {
    "przyjecie": "intake", "specyfikacja": "spec", "realizacja": "implementation", "przeglad": "review",
    "wdrozenie": "deploy", "zamkniecie": "closed", "lekka": "light", "zwykla": "normal", "pelna": "full",
    "zwykly": "normal", "czerwone": "red", "wycofane": "rolled-back", "oszczedny": "economy",
    "zrownowazony": "balanced", "jakosc": "quality", "pytanie": "question", "podzial": "split", "zrodlo": "source",
    "zgoda-na-plan": "plan-approval", "testy": "tests", "skan": "scan", "budzet": "budget", "srodowisko": "environment",
    "zaleznosc": "dependency", "kontrakt": "contract", "uprawnienia": "permissions",
}
VALUE_KEYS = {"stage", "weight", "mode", "state", "from", "to", "stop_code", "code", "profile", "task_stage"}
ROUND_KEYS = {"kod": "code", "weryf": "verify", "skan": "scan", "zakres": "scope"}
STEP_KEYS = {"fakty": "facts", "wersje": "versions", "realizacja": "implementation", "mechanika": "mechanical",
             "przeglad": "review", "decyzja": "decision", "bezpieczenstwo": "security", "opis": "description"}


# 12.0.0: fields of a pdi decision journal entry (`docs/project/changes/*/decisions.md`, rows `- pole: wartość`)
DECISION_KEYS = {"wyslano": "sent", "kiedy": "date", "kto": "by", "rodzaj": "kind", "dlaczego": "why", "zrodlo": "source",
                 "szkic": "drafted_by", "ustalenie": "finding", "skutek": "effect", "pochodzenie": "origin",
                 "pytanie": "question", "odpowiedz": "answer"}
DECISION_RX = re.compile(r"(?m)^- (" + "|".join(DECISION_KEYS) + r"):")
SENT_RX = re.compile(r"(?m)^- sent: (tak|nie)[ \t]*$")


REGISTER_STATUS = {"otwarte": "open", "rozstrzygnięte": "resolved"}
ART_STATUS = {"szkic": "draft", "zatwierdzony": "approved"}   # 14.0.0: task file status in task.json

# 14.0.0: syntax of the specification and plan of open tasks (closed ones stay as history)
SPEC_HEADINGS = [(re.compile(r"(?m)^# Specyfikacja:"), "# Spec:"),
                 (re.compile(r"(?mi)^## Kryteria(?: akceptacji)?\s*$"), "## Acceptance criteria"),
                 (re.compile(r"(?mi)^## Bez zmian\s*$"), "## Unchanged"),
                 (re.compile(r"(?mi)^## Poza zakresem\s*$"), "## Out of scope"),
                 (re.compile(r"(?mi)^## Otwarte pytania\s*$"), "## Open questions"),
                 (re.compile(r"\[blokuje\]", re.I), "[blocking]")]
AC_LINE = re.compile(r"(?m)^(\s*(?:[-*]\s+|#{3,6}\s+)?\**AC-\d+\**\s*[:—–-]?\s*)(.*)$")
GWT = [(re.compile(r"^(Zakładając|Zakladajac|Mając|Majac)\b"), "Given"), (re.compile(r",\s+(gdy|kiedy)\b"), ", when"),
       (re.compile(r",\s+wtedy\b"), ", then")]
PLAN_FIELDS = {"pliki": "files", "kryteria": "criteria", "weryfikacja": "verify", "po": "after"}
PLAN_SLICE = re.compile(r"(?m)^(\s*-\s*\[[ xX]\]\s*[KS]\d+\b)(.*)$")
TICKED = re.compile(rb"(?m)^(\s*-\s*)\[[xX]\](\s*[KS]\d+\b)")


def _spec(text: str) -> str:
    for rx, new in SPEC_HEADINGS:
        text = rx.sub(new, text)

    def ac(m):
        body = m.group(2)
        for rx, new in GWT:
            body = rx.sub(new, body, count=1)
        return m.group(1) + body
    return AC_LINE.sub(ac, text)


def _plan(text: str) -> str:
    def fields(m):
        parts = m.group(2).split("·")
        for i, part in enumerate(parts[1:], 1):
            k, sep, v = part.partition(":")
            name = k.strip().lower()
            if sep and name in PLAN_FIELDS:
                v = " none" if name == "po" and v.strip().lower() in ("brak", "nic") else v
                parts[i] = k.replace(k.strip(), PLAN_FIELDS[name]) + ":" + v
        return m.group(1) + "·".join(parts)
    return PLAN_SLICE.sub(fields, text)


def _pack_migrations(root: Path, dry: bool) -> list[str]:
    """Project data migrations from overlays: `.tf/factory/packs/<id>/migrations.py` with the function
    `migrate_values(root, dry) -> list[str]` (the core does not know overlay skills — each migrates its own files)."""
    import importlib.util
    out = []
    for f in sorted((root / ".tf" / "factory" / "packs").glob("*/migrations.py")):
        spec = importlib.util.spec_from_file_location(f"tf_pack_migrations_{f.parent.name}", f)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            out += list(mod.migrate_values(root, dry) or [])
        except Exception as e:   # noqa: BLE001 — an overlay migration error does not stop the update
            print(f"⚠ pack migration {f.parent.name}: {e}")
    return out


def _sha(data: bytes, plan: bool = False) -> str:
    import hashlib
    return hashlib.sha256(TICKED.sub(rb"\1[ ]\2", data) if plan else data).hexdigest()


def _task_docs(root: Path, tj: Path, dry: bool) -> list[str]:
    """spec.md and plan.md of an open task in the 14.0.0 syntax; hashes in task.json recomputed only where they matched
    the file before the migration — human consent stays valid, and a change without consent is still visible."""
    try:
        task = json.loads(tj.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(task, dict) or task.get("stage") in ("closed", "zamkniecie"):
        return []
    out, folder = [], tj.parent
    for name, fn in (("spec.md", _spec), ("plan.md", _plan)):
        f = folder / name
        if not f.is_file():
            continue
        old = f.read_bytes()
        new = fn(old.decode("utf-8")).encode("utf-8")
        if new == old:
            continue
        out.append(f.relative_to(root).as_posix())
        if dry:
            continue
        f.write_bytes(new)
        for art_name, art in (task.get("artifacts") or {}).items():
            if not isinstance(art, dict):
                continue
            if art_name == name and art.get("approved_sha") == _sha(old, name == "plan.md"):
                art["approved_sha"] = _sha(new, name == "plan.md")
            inputs = art.get("inputs") or {}
            if inputs.get(name) == _sha(old):
                inputs[name] = _sha(new)
        rel = f.relative_to(root).as_posix()
        fr = (task.get("frozen") or {}).get(rel)
        if isinstance(fr, dict) and fr.get("sha") == _sha(old):
            fr["sha"] = _sha(new)
    if out and not dry:
        tj.write_text(json.dumps(task, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def _decisions(text: str) -> str:
    text = DECISION_RX.sub(lambda m: f"- {DECISION_KEYS[m.group(1)]}:", text)
    return SENT_RX.sub(lambda m: "- sent: " + ("yes" if m.group(1) == "tak" else "no"), text)


def _walk(o):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            k2 = ROUND_KEYS.get(k, k) if isinstance(v, str) and v in ("run", "pass", "fail", "todo") else k
            out[k2] = VALUES.get(v, v) if k in VALUE_KEYS and isinstance(v, str) else \
                ART_STATUS.get(v, v) if k == "status" and isinstance(v, str) else _walk(v)
        return out
    if isinstance(o, list):
        return [_walk(v) for v in o]
    return o


# 19.0.0: the readers no longer accept the Polish forms from before 14.x — the project files they read get the English form.
RETRO_DECISIONS = {"tak": "yes", "nie": "no", "później": "later"}
WIP_HEADINGS = [(re.compile(r"(?m)^## Pułapki i ślepe uliczki[ \t]*$"), "## Pitfalls and dead ends")]
CORPUS_ENTRY = re.compile(r"(?m)^(-\s+\*\*E\d+\*\*\s*>\s*[„\"“].+?[”\"“]\s*[—-]\s*[^\[\n]*?\s*)((?:\[[^\]]*\]\s*)+)$")
CORPUS_TAGS = {"wzmianka": "mention", "zastąpiony": "superseded", "niezweryfikowany": "unverified"}
CORPUS_TAG = re.compile(r"\[\s*(" + "|".join(CORPUS_TAGS) + r")\s*\]", re.I)
KB_FILE_MARK = re.compile(r"(?m)^<!-- plik: (\S+) -->$")
CLAUDE_MD_BLOCK = ("<!-- team-factory:begin -->", "<!-- team-factory:end -->")
CLAUDE_MD_SUBS = [("\n### Komendy\n", "\n### Commands\n"), ("\n### Język\n", "\n### Language\n"),
                  ("dostosuj do swojego projektu", "adapt to your project")]
OWN_SKILL_SUBS = [(re.compile(r"\[niezweryfikowane"), "[unverified"),
                  (re.compile(r"(?m)^## Pojęcia domenowe w "), "## Domain concepts in "),
                  (re.compile(r"(?m)^## Pojęcia domenowe"), "## Domain concepts"),
                  (re.compile(r"(?m)^## Zależne od wersji"), "## Version-dependent")]
SOURCES_PL = re.compile(r"(?m)^## Źródła[ \t]*$")
PERSONA_RUN = re.compile(r"Uruchom przez (`claude --agent )")
MANAGED_MARK = re.compile(r"WYGENEROWANO przez \.tf/factory/build\.py(?: — nie edytuj ręcznie\.)?")
MANAGED_README = ("# Managed Agents — wygenerowane przez fabrykę", "# Managed Agents — generated by the factory")
PDI_COLUMNS = {"wydanie": "Release", "flaga": "Flag", "rodzaj": "Kind", "wartość": "Value", "wymagania": "Requirements",
               "odblokowuje": "Unblocks", "weryfikacja": "Verification", "cięcie": "Slice", "pliki": "Files"}   # as the template
PDI_PLAN_HEADINGS = [(re.compile(r"(?mi)^(##+)\s+Rozwa[zż]one opcje\b"), r"\1 Options considered"),
                     (re.compile(r"(?m)^(###+)\s+Opcja\b"), r"\1 Option"),
                     (re.compile(r"(?mi)^(##+)\s+Cele zmiany\b"), r"\1 Change targets")]
PDI_ARTIFACT_HEADINGS = [(re.compile(r"(?m)^## Pytania do bramki[ \t]*$"), "## Gate questions"),
                         (re.compile(r"(?m)^## Przegląd drugim modelem[ \t]*$"), "## Second-model review")]
RECON = Path("docs") / "project" / "00-reconstruction"
RECON_STAMP = re.compile(r"(?m)^Odświeżenie przyrostowe:")
RECON_SUBS = [(re.compile(r"\[(założenie)", re.I), "[assumption"), (re.compile(r"\[(niezweryfikowane)", re.I), "[unverified"),
              (re.compile(r"\[(pytanie)", re.I), "[question"), (re.compile(r"\((\s*)pewność", re.I), r"(\1confidence"),
              (re.compile(r"\(szczegóły: modules/"), "(details: modules/")]
RECON_BATCH = re.compile(r"(\"name\":\s*\"[^\"\n]*) \(pliki\)\"")


def _hash(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def _rewrite(root: Path, p: Path, fn, dry: bool, out: list[str]) -> tuple[bytes, bytes] | None:
    """Rewrites a text file with `fn`; records it in `out` when it changes. Returns (old, new) bytes of a changed file."""
    if not p.is_file():
        return None
    try:
        old = p.read_bytes()
        text = old.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    new = fn(text).encode("utf-8")
    if new == old:
        return None
    out.append(p.relative_to(root).as_posix())
    if not dry:
        p.write_bytes(new)
    return old, new


def _subs(rules):
    def fn(text: str) -> str:
        for rx, new in rules:
            text = rx.sub(new, text)
        return text
    return fn


def claude_md_v19(text: str) -> str:
    """The factory block in CLAUDE.md / CLAUDE.local.md: Polish subsection names and the template note → English.
    The installer calls it before it rewrites the block (the project's commands in the subsection survive)."""
    begin, end = CLAUDE_MD_BLOCK
    a = text.find(begin)
    b = text.find(end, a + 1) if a >= 0 else -1
    if a < 0 or b < 0:
        return text
    block = text[a:b]
    for old, new in CLAUDE_MD_SUBS:
        block = block.replace(old, new)
    return text[:a] + block + text[b:]


def _own_skill(text: str) -> str:
    text = _subs(OWN_SKILL_SUBS)(text)
    out, inside = [], False
    for line in text.split("\n"):
        if line.startswith("## "):
            line = SOURCES_PL.sub("## Sources", line)
            inside = line.strip().startswith("## Sources")
        elif inside:
            line = re.sub(r"\bodczyt\b", "accessed", line)
        out.append(line)
    return "\n".join(out)


def _pdi_plan(text: str) -> str:
    """plan.md of a pdi change: the cut table header (a row followed by `|---`) and the architect's headings."""
    lines = text.split("\n")
    for i, line in enumerate(lines[:-1]):
        if not (line.strip().startswith("|") and re.match(r"^\s*\|\s*:?-{3,}", lines[i + 1])):
            continue
        cells = line.split("|")
        if {"wydanie", "flaga", "odblokowuje"} & {c.strip().lower() for c in cells}:
            lines[i] = "|".join(c.replace(c.strip(), PDI_COLUMNS[c.strip().lower()]) if c.strip().lower() in PDI_COLUMNS
                                else c for c in cells)
    return _subs(PDI_PLAN_HEADINGS)("\n".join(lines))


def _corpus(text: str) -> str:
    return CORPUS_ENTRY.sub(lambda m: m.group(1) + CORPUS_TAG.sub(lambda t: f"[{CORPUS_TAGS[t.group(1).lower()]}]",
                                                                   m.group(2)), text)


def migrate_v19(root: Path, dry: bool = True) -> list[str]:
    """19.0.0: project files read by the readers that accepted the Polish forms from before 14.x, in the English form.
    Only the files those readers read; the rest of each file byte-identical; factory-installed files are left to the
    installer (own skills and personas only)."""
    out: list[str] = []
    for p in sorted([*root.glob(".tf/wip/*.md"), *root.glob(".tf/wip/archive/*.md")]):       # retro_data traps
        _rewrite(root, p, _subs(WIP_HEADINGS), dry, out)
    for p in sorted(root.glob("docs/project/archive/retro/*-retro.json")):                    # retro decisions
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        dec = data.get("decisions") if isinstance(data, dict) else None
        if isinstance(dec, dict) and any(isinstance(v, str) and v in RETRO_DECISIONS for v in dec.values()):
            data["decisions"] = {k: RETRO_DECISIONS.get(v, v) if isinstance(v, str) else v for k, v in dec.items()}
            out.append(p.relative_to(root).as_posix())
            if not dry:
                p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for p in sorted(root.glob(".claude/knowledge/*/doc.txt")):                                # kb cache
        done = _rewrite(root, p, lambda t: KB_FILE_MARK.sub(r"<!-- file: \1 -->", t), dry, out)
        meta = p.parent / "meta.json"
        if done and meta.is_file():
            try:
                m = json.loads(meta.read_text(encoding="utf-8"))
            except ValueError:
                continue
            if isinstance(m, dict) and m.get("sha256") == _hash(done[0]):
                m["sha256"], m["bytes"] = _hash(done[1]), len(done[1])
                if not dry:
                    meta.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    _rewrite(root, root / "docs" / "project" / "02-domain" / "corpus.md", _corpus, dry, out)  # evidence tags
    for name in ("CLAUDE.md", "CLAUDE.local.md"):                                             # factory block
        _rewrite(root, root / name, claude_md_v19, dry, out)
    installed = factory_files(root)
    for skill_md in sorted((root / ".claude" / "skills").glob("*/SKILL.md")):                 # own skills
        if skill_md.relative_to(root).as_posix() in installed:
            continue
        for p in [skill_md, *sorted(skill_md.parent.glob("references/*.md"))]:
            if p.relative_to(root).as_posix() not in installed:
                _rewrite(root, p, _own_skill, dry, out)
    for p in sorted((root / ".tf" / "config" / "personas").glob("*.yaml")):                   # own personas
        if p.relative_to(root).as_posix() not in installed:
            _rewrite(root, p, lambda t: PERSONA_RUN.sub(r"Run with \1", t), dry, out)
    ma = root / "managed-agents"                                                              # managed-agents target
    for p in sorted(ma.rglob("*")) if ma.is_dir() else []:
        if p.suffix not in (".md", ".yaml"):
            continue
        def managed(t: str) -> str:
            if t.startswith(MANAGED_README[0]):
                return MANAGED_README[1] + t[len(MANAGED_README[0]):]
            head, sep, rest = t.partition("\n---\n")
            return MANAGED_MARK.sub("GENERATED by .tf/factory/build.py — do not edit by hand.", head, count=1) + sep + rest
        _rewrite(root, p, managed, dry, out)
    for d in sorted(x for x in root.glob("docs/project/changes/*") if x.is_dir()):                                    # pdi change artifacts
        _rewrite(root, d / "plan.md", _pdi_plan, dry, out)
        for p in sorted(d.glob("*.md")):
            _rewrite(root, p, _subs(PDI_ARTIFACT_HEADINGS), dry, out)
    rec = root / RECON                                                                        # pack-it reconstruction
    _rewrite(root, rec / "report.md", lambda t: RECON_STAMP.sub("Incremental refresh:", t), dry, out)
    for name in ("rules.md", "requirements.md", "domain.md"):
        _rewrite(root, rec / name, _subs(RECON_SUBS), dry, out)
    done = _rewrite(root, rec / "manifest.json", lambda t: RECON_BATCH.sub(r'\1 (files)"', t), dry, out)
    remap = rec / "raw" / "remap.json"
    if done and remap.is_file():   # the refresh mark: the same manifest → the line remapping is not done twice
        try:
            mark = json.loads(remap.read_text(encoding="utf-8"))
        except ValueError:
            mark = None
        if isinstance(mark, dict) and mark.get("manifest") == _hash(done[0]):
            mark["manifest"] = _hash(done[1])
            if not dry:
                remap.write_text(json.dumps(mark), encoding="utf-8")
    return list(dict.fromkeys(out))


def migrate_values(root: Path = ROOT, dry: bool = True) -> list[str]:
    """Project data from before 11.0.0: tasks, runs, project and people configuration, cost profile."""
    out = []
    jsons = [*root.glob("docs/project/changes/*/task.json"), *root.glob(".tf/runs/*/run.json"),
             root / ".claude" / "factory-profile.json"]
    for p in jsons:
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        new = _walk(data)
        if new != data:
            out.append(p.relative_to(root).as_posix())
            if not dry:
                p.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    keys = {**STEP_KEYS, "oszczedny": "economy", "zrownowazony": "balanced", "jakosc": "quality"}
    key_rx = re.compile(r"(?m)^(\s+)(" + "|".join(map(re.escape, keys)) + r"):")          # steps, profiles, description
    val_rx = re.compile(r"(?m)^(\s*(?:default_profile|default_mode|profile):\s*)([\w-]+)")  # single values
    list_rx = re.compile(r"(?m)^(\s*allowed_modes:\s*\[)([^\]]*)(\])")
    for p in [root / ".tf" / "config" / "config.yaml", root / ".tf" / "config" / "me.yaml"]:
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            new = key_rx.sub(lambda m: m.group(1) + keys[m.group(2)] + ":", text)
            new = val_rx.sub(lambda m: m.group(1) + VALUES.get(m.group(2), m.group(2)), new)
            new = list_rx.sub(lambda m: m.group(1) + ", ".join(VALUES.get(x.strip(), x.strip())
                                                               for x in m.group(2).split(",")) + m.group(3), new)
            new = re.sub(r"(\{\s*default_mode:\s*)([\w-]+)", lambda m: m.group(1) + VALUES.get(m.group(2), m.group(2)), new)
            if new != text:
                out.append(p.relative_to(root).as_posix())
                if not dry:
                    p.write_text(new, encoding="utf-8")
    for tj in sorted(root.glob("docs/project/changes/*/task.json")):
        out += _task_docs(root, tj, dry)
    out += _pack_migrations(root, dry)
    out += migrate_v19(root, dry)
    reg = root / ".tf" / "register" / "items.jsonl"   # 13.0.0: status pozycji rejestru tf analyze
    if reg.is_file():
        rows, changed = [], False
        for line in reg.read_text(encoding="utf-8").splitlines():
            try:
                x = json.loads(line)
            except ValueError:
                rows.append(line)
                continue
            if isinstance(x, dict) and x.get("status") in REGISTER_STATUS:
                x["status"], changed = REGISTER_STATUS[x["status"]], True
            rows.append(json.dumps(x, ensure_ascii=False, sort_keys=True) if isinstance(x, dict) else line)
        if changed:
            out.append(reg.relative_to(root).as_posix())
            if not dry:
                reg.write_text("".join(r + "\n" for r in rows), encoding="utf-8")
    for p in root.glob("docs/project/changes/*/decisions.md"):
        text = p.read_text(encoding="utf-8")
        new = _decisions(text)
        if new != text:
            out.append(p.relative_to(root).as_posix())
            if not dry:
                p.write_text(new, encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    changes = apply(ROOT, dry="--apply" not in argv) + [f"{c}: 11.0.0 values" for c in
                                                        migrate_values(ROOT, dry="--apply" not in argv)]
    for c in changes:
        print(("✓ " if "--apply" in argv else "⚠ ") + c)
    if not changes:
        print("✓ Nothing to migrate")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
