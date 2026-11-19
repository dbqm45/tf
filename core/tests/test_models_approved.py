#!/usr/bin/env python3
"""Approved models (`models_approved`): an optional list of the models an organization allows, checked by
`.tf/factory/model_check.py`, by `profile.py` when switching profiles and by the `model_guard` hook on delegation.

python3 .claude/tests/test_models_approved.py

Without the list nothing changes. With it: a tier model (after the active profile) or a session setting of the active
profile that is not approved is an error; other profiles and `inherit` are warnings; a lower layer (team, project) can
only narrow the company's list; `until` in the past ends an approval. An alias and an identifier are linked through
`models_current`. Plan: docs/plans/2026-11-19-bramka-ewaluacji-i-zatwierdzone-modele.md (factory repository).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".tf" / "factory" / "tf.py").is_file())
HOOK = ROOT / ".claude" / "hooks" / "model_guard.py"
TODAY = "2026-11-19"


def call(project: Path, script: str, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(project / ".tf" / "factory" / script), *args], cwd=project, input=stdin,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                          env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)})


def check_json(project: Path) -> tuple[int, dict, str]:
    r = call(project, "model_check.py", "--json", "--today", TODAY)
    try:
        return r.returncode, json.loads(r.stdout), r.stdout + r.stderr
    except ValueError:
        return r.returncode, {}, r.stdout + r.stderr


def project(base: Path, name: str, override: str | None = None, company: str | None = None) -> Path:
    """A copy of the factory engine with an optional project configuration and an optional company pack."""
    p = base / name
    shutil.copytree(ROOT / ".tf" / "factory", p / ".tf" / "factory", ignore=shutil.ignore_patterns("__pycache__", "packs"))
    if override is not None:
        (p / ".tf" / "config").mkdir(parents=True)
        (p / ".tf" / "config" / "config.yaml").write_text(override, encoding="utf-8")
    if company is not None:
        d = p / ".tf" / "factory" / "packs" / "pack-acme"
        d.mkdir(parents=True)
        (d / "pack.yaml").write_text("id: pack-acme\nversion: 1.0.0\ntitle: Acme\norg_defaults:\n  config:\n" + company,
                                     encoding="utf-8")
    return p


def hook(project_dir: Path, tool_input) -> tuple[str, str]:
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"tool_name": "Agent", "tool_input": tool_input}),
                       cwd=project_dir, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir)})
    if r.returncode != 0:
        return f"exit {r.returncode}", r.stderr[-300:]
    if not r.stdout.strip():
        return "none", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out["permissionDecisionReason"]


def models(*names: str, indent: str = "") -> str:
    body = "".join(f"{indent}    {n}: {{}}\n" for n in names)
    return f"{indent}models_approved:\n{indent}  models:\n{body}"


def main() -> int:
    fails, total = [], 0

    def check(cond, msg):
        nonlocal total
        total += 1
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as t:
        base = Path(t)

        # MA-1: no list — the result is as before, with empty approval fields
        p = project(base, "clean")
        rc, data, out = check_json(p)
        current = data.get("current") or {}
        check(rc == 0 and data.get("errors") == [] and data.get("approved") is None and "usage" in data,
              f"MA-1: without the list no errors and `approved` is null: {rc} {out[:400]}")
        r = call(p, "model_check.py", "--today", TODAY)
        check(r.returncode == 0 and "approved" not in r.stdout.lower(),
              f"MA-1b: without the list the text output does not mention approvals: {r.stdout}")

        # MA-2: a tier of the active profile outside the list → error naming the tier, the model and the key
        p = project(base, "no-opus", models("haiku", "sonnet"))
        rc, data, out = check_json(p)
        errs = data.get("errors") or []
        check(rc == 1 and any("tiers.deep" in e and "opus" in e and "models_approved" in e for e in errs),
              f"MA-2: deep tier with opus outside the list → error: {rc} {errs}")
        check(sorted(data.get("approved") or []) == ["haiku", "sonnet"], f"MA-2b: JSON lists the approved models: {data.get('approved')}")
        check(any(u.get("where") == "tiers.deep" and u.get("model") == "opus" and u.get("active") for u in data.get("usage") or []),
              f"MA-2c: JSON lists where models are used: {data.get('usage')}")

        # MA-3: approving an identifier covers the alias that points to it in models_current
        ids = [current.get(a) for a in ("haiku", "sonnet", "opus")]
        if all(ids):
            p = project(base, "by-id", models(*ids))
            rc, data, out = check_json(p)
            check(rc == 0 and not data.get("errors"), f"MA-3: identifiers on the list approve their aliases: {rc} {data.get('errors')}")
            # MA-4: approving an alias covers the identifier it points to
            p = project(base, "by-alias", models("haiku", "sonnet", "opus") + f"tiers:\n  deep: {{model: {current['opus']}, effort: high}}\n")
            rc, data, out = check_json(p)
            check(rc == 0 and not data.get("errors"), f"MA-4: an alias on the list approves the identifier it points to: {rc} {data.get('errors')}")
        else:
            check(False, f"MA-3: models_current lacks haiku/sonnet/opus: {current}")

        # MA-5: `until` ends an approval
        p = project(base, "expired", "models_approved:\n  models:\n    haiku: {}\n    sonnet: {}\n    opus: {until: \"2026-11-18\"}\n")
        rc, data, out = check_json(p)
        check(rc == 1 and any("tiers.deep" in e and "2026-11-18" in e for e in data.get("errors") or [])
              and (data.get("approved_expired") or {}).get("opus") == "2026-11-18",
              f"MA-5: an approval past its `until` date → error with the date: {rc} {data.get('errors')} {data.get('approved_expired')}")
        p = project(base, "valid-today", "models_approved:\n  models:\n    haiku: {}\n    sonnet: {}\n    opus: {until: \"2026-11-19\"}\n")
        rc, data, out = check_json(p)
        check(rc == 0, f"MA-5b: `until` equal to today still holds: {rc} {data.get('errors')}")
        p = project(base, "bad-date", "models_approved:\n  models:\n    haiku: {}\n    sonnet: {}\n    opus: {until: June}\n")
        rc, data, out = check_json(p)
        check(rc == 1 and any("until" in e and "YYYY-MM-DD" in e for e in data.get("errors") or []) and "Traceback" not in out,
              f"MA-5c: a bad `until` date → configuration error: {rc} {data.get('errors')}")

        p = project(base, "date-time", "models_approved:\n  models:\n    haiku: {}\n    sonnet: {}\n    opus: {until: 2026-11-18 10:00:00}\n")
        rc, data, out = check_json(p)
        check(rc == 1 and (data.get("approved_expired") or {}).get("opus") == "2026-11-18" and "Traceback" not in out,
              f"MA-5d: `until` written with a time counts by its date: {rc} {out[:300]}")

        # MA-6: other profiles only warn; the active one decides
        p = project(base, "economy", models("haiku", "sonnet") + "default_profile: economy\n")
        rc, data, out = check_json(p)
        warns = data.get("warnings") or []
        check(rc == 0 and not data.get("errors") and any("profiles.balanced" in w and "opus" in w for w in warns)
              and any("profiles.quality" in w for w in warns),
              f"MA-6: active profile without opus passes, other profiles warn: {rc} {data.get('errors')} {warns}")

        # MA-7: session settings of the active profile (advisorModel)
        p = project(base, "advisor", models("haiku", "sonnet") + "default_profile: quality\ntiers:\n  deep: {model: sonnet, effort: high}\n")
        rc, data, out = check_json(p)
        check(rc == 1 and any("advisorModel" in e and "quality" in e for e in data.get("errors") or []),
              f"MA-7: advisorModel of the active profile outside the list → error: {rc} {data.get('errors')}")

        # MA-8: inherit is outside the list's control → warning
        p = project(base, "inherit", models("haiku", "sonnet", "opus") + "tiers:\n  std: {model: inherit, effort: medium}\n")
        rc, data, out = check_json(p)
        check(rc == 0 and any("inherit" in w and "tiers.std" in w for w in data.get("warnings") or []),
              f"MA-8: inherit → warning, not an error: {rc} {data.get('errors')} {data.get('warnings')}")

        # MA-9: layers — the project can narrow the company's list, not widen it
        p = project(base, "narrow", models("haiku", "sonnet"), company=models("haiku", "sonnet", "opus", indent="    "))
        rc, data, out = check_json(p)
        check(rc == 1 and sorted(data.get("approved") or []) == ["haiku", "sonnet"]
              and any("tiers.deep" in e for e in data.get("errors") or []),
              f"MA-9: the project narrows the company's list (no opus) → error on the deep tier: {rc} {data.get('approved')} {data.get('errors')}")
        p = project(base, "widen", models("haiku", "sonnet", "opus", "fable"), company=models("haiku", "sonnet", "opus", indent="    "))
        rc, data, out = check_json(p)
        check(rc == 0 and sorted(data.get("approved") or []) == ["haiku", "opus", "sonnet"]
              and any("fable" in w and "models_approved" in w for w in data.get("warnings") or []),
              f"MA-9b: a model added below the company layer is ignored with a warning: {rc} {data.get('approved')} {data.get('warnings')}")
        p = project(base, "company-only", None, company=models("haiku", "sonnet", indent="    "))
        rc, data, out = check_json(p)
        check(rc == 1 and any("tiers.deep" in e for e in data.get("errors") or []),
              f"MA-9c: the company's list applies without any project configuration: {rc} {data.get('errors')}")

        # MA-10: a bad shape is a configuration error, never an exception
        for i, bad in enumerate(("models_approved:\n  models: [sonnet]\n", "models_approved:\n  models:\n    sonnet: yes\n",
                                 "models_approved: sonnet\n")):
            p = project(base, f"bad{i}", bad)
            rc, data, out = check_json(p)
            check(rc == 1 and any("models_approved" in e for e in data.get("errors") or []) and "Traceback" not in out,
                  f"MA-10: bad shape {i} → configuration error: {rc} {out[:300]}")

        # MA-11: text output with a list
        p = project(base, "text", models("haiku", "sonnet", "opus", "fable"))
        r = call(p, "model_check.py", "--today", TODAY)
        check(r.returncode == 0 and "approved" in r.stdout.lower() and "✓" in r.stdout,
              f"MA-11: with a list that covers everything the text output confirms it: {r.returncode} {r.stdout}")

        # MA-12: profile.py refuses a profile with an unapproved model and leaves the state untouched
        p = project(base, "profile", models("haiku", "sonnet"))
        r = call(p, "profile.py", "quality")
        check(r.returncode == 1 and "models_approved" in r.stdout and "opus" in r.stdout
              and not (p / ".claude" / "factory-profile.json").exists(),
              f"MA-12: profile.py quality with a list without opus → exit 1, nothing saved: {r.returncode} {r.stdout[-300:]} {r.stderr[-200:]}")
        r = call(p, "profile.py", "economy", "--dry-run")
        check(r.returncode == 0, f"MA-12b: a profile inside the list passes (--dry-run): {r.returncode} {r.stdout[-300:]} {r.stderr[-200:]}")
        p = project(base, "profile-free")
        r = call(p, "profile.py", "quality", "--dry-run")
        check(r.returncode == 0, f"MA-12c: without the list profile switching is unchanged: {r.returncode} {r.stdout[-300:]} {r.stderr[-200:]}")

        # MA-13: with the managed-agents target the identifier a tier alias maps to must be approved too
        remap = models("haiku", "sonnet", "opus") + f"managed_agents:\n  models: {{sonnet: {current.get('fable')}}}\n"
        p = project(base, "managed", remap)
        (p / ".claude").mkdir()
        (p / ".claude" / "factory-settings.json").write_text('{"targets": ["claude", "managed-agents"]}', encoding="utf-8")
        rc, data, out = check_json(p)
        check(rc == 1 and any("managed_agents.models.sonnet" in e and str(current.get("fable")) in e for e in data.get("errors") or []),
              f"MA-13: managed-agents maps sonnet to an unapproved identifier → error: {rc} {data.get('errors')}")
        p = project(base, "managed-off", remap)
        rc, data, out = check_json(p)
        check(rc == 0, f"MA-13b: without the managed-agents target that mapping is not checked: {rc} {data.get('errors')}")

        # MG: the model_guard hook (PreToolUse Agent|Task)
        check(HOOK.is_file(), "MG-0: the hook .claude/hooks/model_guard.py is installed")
        if HOOK.is_file():
            free = project(base, "hook-free")
            limited = project(base, "hook-limited", models("haiku", "sonnet"))
            broken = project(base, "hook-broken", "models_approved: [this is not a mapping\n")
            for proj, ti, want, why in (
                    (free, {"model": "opus", "prompt": "x"}, "none", "MG-1: without the list the hook does not decide"),
                    (limited, {"model": "sonnet", "prompt": "x"}, "none", "MG-2: a model on the list passes"),
                    (limited, {"model": "opus", "prompt": "x"}, "deny", "MG-3: a model outside the list → deny"),
                    (limited, {"prompt": "x"}, "none", "MG-4: a delegation without the model parameter passes"),
                    (broken, {"model": "opus", "prompt": "x"}, "none", "MG-5: a broken configuration does not block"),
                    (limited, "not a mapping", "none", "MG-6: input outside the format does not crash")):
                got, _ = hook(proj, ti)
                check(got == want, f"{why}: {got}")
            got, reason = hook(limited, {"model": "opus"})
            check("haiku" in reason and "sonnet" in reason and "models_approved" in reason,
                  f"MG-3b: the denial names the approved models and the configuration key: {reason}")
            blocks = limited / ".tf" / "logs" / "hook-blocks.jsonl"
            check(blocks.is_file() and "model_guard" in blocks.read_text(encoding="utf-8"),
                  "MG-3c: a denial is recorded in .tf/logs/hook-blocks.jsonl")
            if current.get("sonnet"):
                by_id = project(base, "hook-by-id", models("haiku", current["sonnet"]))
                got, _ = hook(by_id, {"model": "sonnet"})
                check(got == "none", f"MG-7: an approved identifier covers the alias in a delegation: {got}")

    for f in fails:
        print(f"✗ {f}")
    print(f"{'✓' if not fails else '✗'} {total - len(fails)}/{total} approved models tests")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
