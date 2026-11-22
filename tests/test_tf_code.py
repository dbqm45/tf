#!/usr/bin/env python3
"""Tryb fabryki, krok T2 (docs/plans/2026-11-20-tryb-fabryki-plan.md): `tf code [argumenty claude]` uruchamia sesję
fabryki — `claude --plugin-dir .tf/plugin --settings .tf/plugin/session-settings.json …` — w projekcie z układem
wtyczki; w układzie domyślnym uruchamia `claude` bez zmian. `tf doctor` mówi, jak uruchomić fabrykę.
Zamiast prawdziwego `claude` test podstawia skrypt (TF_CLAUDE).
python3 tests/test_tf_code.py"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "core" / "factory").is_dir())
INSTALL = ROOT / "core" / "factory" / "install.py"
FAKE = "import json, sys, os\nopen(os.environ['TF_FAKE_OUT'], 'w').write(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), 'isolation': os.environ.get('TF_ISOLATION')}))\n" \
       "raise SystemExit(int(os.environ.get('TF_FAKE_EXIT', '0')))\n"


def env(base: Path, **extra: str) -> dict:
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(base), "TF_CLAUDE": f"{sys.executable} {base / 'fake.py'}",
            "TF_FAKE_OUT": str(base / "argv.json"), **extra}


def make(base: Path, name: str, *opts: str) -> Path:
    p = base / name
    p.mkdir()
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    r = subprocess.run([sys.executable, str(INSTALL), str(p), "--yes", "--packs", "none", *opts], capture_output=True,
                       text=True, timeout=600, env=env(base))
    assert r.returncode == 0, r.stdout[-500:] + r.stderr[-500:]
    return p


def tf(p: Path, base: Path, *args: str, **extra: str) -> subprocess.CompletedProcess:
    (base / "argv.json").unlink(missing_ok=True)
    return subprocess.run([sys.executable, str(p / ".tf" / "factory" / "tf.py"), *args], cwd=p, capture_output=True,
                          text=True, timeout=300, env=env(base, **extra))


def called(base: Path) -> dict:
    f = base / "argv.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        (base / "fake.py").write_text(FAKE, encoding="utf-8")
        p = make(base, "plugin", "--layout", "plugin")
        r = tf(p, base, "code", "--continue", "-p", "zrób coś")
        c = called(base)
        plug = (p / ".tf" / "plugin").resolve()
        launch = (p / ".tf" / "cache" / "session-settings.json").resolve()
        want = ["--plugin-dir", str(plug), "--settings", str(launch), "--continue", "-p", "zrób coś"]
        sess = json.loads(launch.read_text(encoding="utf-8")) if launch.is_file() else {}
        base_sess = json.loads((plug / "session-settings.json").read_text(encoding="utf-8"))
        check(r.returncode == 0 and c.get("argv") == want and Path(c.get("cwd", "")).resolve() == p.resolve()
              and all(sess.get(k) == v for k, v in base_sess.items() if k != "sandbox")
              and (sess.get("sandbox") or {}).get("enabled") is True and c.get("isolation") == "sandbox",
              f"TC-1: tf code uruchamia claude z wtyczką fabryki i ustawieniami sesji, potem argumenty: {r.returncode} "
              f"{c} {r.stdout[-300:]} {r.stderr[-300:]}")
        (p / ".tf" / "config" / "config.yaml").write_text("isolation: basic\n", encoding="utf-8")
        r = tf(p, base, "code")
        sess = json.loads(launch.read_text(encoding="utf-8")) if launch.is_file() else {"sandbox": "?"}
        check(r.returncode == 0 and "sandbox" not in sess and called(base).get("isolation") == "basic",
              f"TC-7: level basic → tf code starts the session without the sandbox: {sess} {called(base)}")
        r = tf(p, base, "code", TF_FAKE_EXIT="7")
        check(r.returncode == 7, f"TC-2: kod wyjścia claude przechodzi dalej: {r.returncode}")
        r = tf(p, base, "doctor")
        check("tf code" in r.stdout and "plugin" in r.stdout.lower(),
              f"TC-3: tf doctor mówi o układzie wtyczki i o tym, jak uruchomić fabrykę: {r.stdout[-600:]}")
        (p / ".tf" / "plugin" / "session-settings.json").unlink()
        r = tf(p, base, "code")
        check(r.returncode == 2 and not called(base) and "tf doctor" in r.stdout + r.stderr,
              f"TC-4: brak pliku wtyczki → odmowa z podpowiedzią, claude nie startuje: {r.returncode} {r.stdout}{r.stderr}")

        q = make(base, "default", "--layout", "default")
        r = tf(q, base, "code", "--continue")
        c = called(base)
        check(r.returncode == 0 and c.get("argv") == ["--continue"] and "layout" in (r.stdout + r.stderr).lower(),
              f"TC-5: w układzie domyślnym tf code uruchamia zwykły claude i mówi o układzie: {r.returncode} {c} {r.stdout}")
        r = tf(q, base, "--help")
        check("tf code" in r.stdout, "TC-6: tf code w opisie poleceń")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} testów tf code")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
