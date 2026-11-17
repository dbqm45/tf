#!/usr/bin/env python3
"""`profile.py` bez argumentów: lista profili z opisem z `config.yaml` (klucz `description`), a `--team-only`
przełącza tylko zespół (bez `.claude/settings.local.json`). Uruchamia `--dry-run`, niczego nie zapisuje.
python3 .claude/tests/test_profile_show.py"""
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "profile.py").is_file())


def main() -> int:
    import importlib.util   # nie `import profile` — nazwa zderza się z modułem biblioteki standardowej
    spec = importlib.util.spec_from_file_location("tf_profile", ROOT / ".tf" / "factory" / "profile.py")
    prof_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prof_mod)
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    cfg = prof_mod.load_cfg()
    profiles = cfg.get("profiles") or {}
    r = subprocess.run([sys.executable, str(ROOT / ".tf/factory/profile.py")], capture_output=True, text=True,
                       encoding="utf-8", cwd=ROOT)
    for name, p in profiles.items():
        desc = p.get("description", "")
        check(desc and any(name in line and desc in line for line in r.stdout.splitlines()),
              f"PS-1: profil {name} wyświetlony z opisem „{desc}”: {r.stdout}")
    name = next(iter(profiles))
    r = subprocess.run([sys.executable, str(ROOT / ".tf/factory/profile.py"), name, "--dry-run", "--team-only"],
                       capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    check(r.returncode == 0 and profiles[name].get("description", "") in r.stdout and "effortLevel" not in r.stdout,
          f"PS-2: --team-only --dry-run: nagłówek z opisem profilu, bez zmian sesji: {r.returncode} {r.stdout}{r.stderr}")
    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów listy profili")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
