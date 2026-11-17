#!/usr/bin/env python3
"""
Migracje rdzenia — autokorekta plików projektu po zmianach w publicznym API fabryki (.tf/factory/PUBLIC_API.md).

  python3 .tf/factory/migrations.py            # pokaż, co trzeba poprawić (nic nie zmienia)
  python3 .tf/factory/migrations.py --apply    # popraw

Uruchamiają je instalator (po każdej aktualizacji) i `tf doctor --fix`. Poprawiane są tylko pliki projektu, których
fabryka nie instalowała: własne persony i role (`.tf/config/personas/`, `.tf/config/roles/`), własne nakładki
(`.tf/factory/packs/<id>/` spoza manifestu) i własne skille (`.claude/skills/<skill>/SKILL.md` spoza manifestu).
Pliki fabryki aktualizuje instalator. Biblioteka standardowa + PyYAML (przez packs.py) do czytania pack.yaml.

Nowa zmiana nazwy w rdzeniu = nowy wpis w RENAMES (z wersją rdzenia, od której obowiązuje). Zmiana nazwy w nakładce =
wpis `renames: {"<wersja>": {stara: nowa}}` w jej pack.yaml (działa też dla nakładek spoza repozytorium fabryki).
"""
from __future__ import annotations

import json
import re
import sys

import os
for _stream in (sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) nie zna „✓”, „⚠” — zawsze UTF-8
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
os.environ.setdefault("PYTHONUTF8", "1")  # procesy potomne (build.py, testy, hooki) też piszą i czytają UTF-8

sys.dont_write_bytecode = True   # silnik w .tf/factory/ bez __pycache__ (jak node_modules — tylko kod)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# wersja rdzenia → stara nazwa → nowa nazwa (skille, cechy, role)
RENAMES: dict[str, dict[str, str]] = {
    "3.0.0": {
        "core-tech-docs": "docs-tech-writing",          # pack-docs
        "fe-ux-design": "ux-feature-design",            # pack-ux
    },
    "5.0.0": {
        "core-story-run": "tf",                         # pętla „zadanie → PR” (do 9.33 skill talos-story-run trybu mode-talos)
    },
    "10.0.0": {
        "talos-story-run": "tf",                        # pętla przeniesiona z trybu mode-talos do rdzenia
    },
}


def factory_files(root: Path) -> set[str]:
    try:
        return set(json.loads((root / ".claude" / "factory-manifest.json").read_text(encoding="utf-8")).get("files") or {})
    except (OSError, ValueError):
        return set()


def own_files(root: Path) -> list[Path]:
    """Pliki projektu, które mogą odwoływać się do nazw fabryki, a których fabryka nie instaluje."""
    installed = factory_files(root)
    cands = [*(root / ".tf" / "config" / "personas").glob("*.yaml"), *(root / ".tf" / "config" / "roles").glob("*.yaml"),
             *(root / ".tf" / "factory" / "packs").glob("*/**/*.yaml"), *(root / ".claude" / "skills").glob("*/SKILL.md")]
    return [p for p in cands if p.is_file() and p.relative_to(root).as_posix() not in installed]


def pack_renames(root: Path) -> dict[str, str]:
    """Zmiany nazw zadeklarowane przez zainstalowane nakładki (`renames` w .tf/factory/packs/<id>/pack.yaml)."""
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
    """Zmiany nazw w plikach projektu. Zwraca opis zmian (przy dry=True — zmian do zrobienia)."""
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


# 11.0.0: identyfikatory stanu zadania, pętli i konfiguracji po angielsku (opisy zostają po polsku)
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


# 12.0.0: pola wpisu dziennika decyzji pdi (`docs/project/changes/*/decisions.md`, wiersze `- pole: wartość`)
DECISION_KEYS = {"wyslano": "sent", "kiedy": "date", "kto": "by", "rodzaj": "kind", "dlaczego": "why", "zrodlo": "source",
                 "szkic": "drafted_by", "ustalenie": "finding", "skutek": "effect", "pochodzenie": "origin",
                 "pytanie": "question", "odpowiedz": "answer"}
DECISION_RX = re.compile(r"(?m)^- (" + "|".join(DECISION_KEYS) + r"):")
SENT_RX = re.compile(r"(?m)^- sent: (tak|nie)[ \t]*$")


REGISTER_STATUS = {"otwarte": "open", "rozstrzygnięte": "resolved"}
ART_STATUS = {"szkic": "draft", "zatwierdzony": "approved"}   # 14.0.0: status pliku zadania w task.json

# 14.0.0: składnia specyfikacji i planu otwartych zadań (zamknięte zostają jako historia)
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
    """Migracje danych projektu z nakładek: `.tf/factory/packs/<id>/migrations.py` z funkcją
    `migrate_values(root, dry) -> list[str]` (rdzeń nie zna skilli nakładek — każda migruje swoje pliki)."""
    import importlib.util
    out = []
    for f in sorted((root / ".tf" / "factory" / "packs").glob("*/migrations.py")):
        spec = importlib.util.spec_from_file_location(f"tf_pack_migrations_{f.parent.name}", f)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            out += list(mod.migrate_values(root, dry) or [])
        except Exception as e:   # noqa: BLE001 — błąd migracji nakładki nie zatrzymuje aktualizacji
            print(f"⚠ pack migration {f.parent.name}: {e}")
    return out


def _sha(data: bytes, plan: bool = False) -> str:
    import hashlib
    return hashlib.sha256(TICKED.sub(rb"\1[ ]\2", data) if plan else data).hexdigest()


def _task_docs(root: Path, tj: Path, dry: bool) -> list[str]:
    """spec.md i plan.md otwartego zadania w składni 14.0.0; skróty w task.json przeliczone tylko tam, gdzie zgadzały
    się z plikiem przed migracją — zgoda człowieka zostaje ważna, a zmiana bez zgody nadal jest widoczna."""
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


def migrate_values(root: Path = ROOT, dry: bool = True) -> list[str]:
    """Dane projektu sprzed 11.0.0: zadania, przebiegi, konfiguracja projektu i osoby, profil kosztów."""
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
    key_rx = re.compile(r"(?m)^(\s+)(" + "|".join(map(re.escape, keys)) + r"):")          # kroki, profile, opis
    val_rx = re.compile(r"(?m)^(\s*(?:default_profile|default_mode|profile):\s*)([\w-]+)")  # pojedyncze wartości
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
