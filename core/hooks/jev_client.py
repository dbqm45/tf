#!/usr/bin/env python3
"""
Client for the Jev decision model (TypeSafe, System One API) — optional, DISABLED by default. Standard library only.

Jev does not write text. For a state (text or JSON) and questions of type noul (yes/no), choice (a pick, ≤255 options) and score
(a scale of 2–10 levels) it returns probabilities and confidence — in ~0.1–0.5 s, $0.042 per 1M input tokens.
The factory uses it as a fast, cheap decision layer with a fallback to a regular model (patterns from the TypeSafe documentation):
  - two-stage skill hint (cookbook "skill suggestion")               → skill_hint.py,  CLAUDE_SKILL_HINT_JEV=1
  - content grading in skill evaluations (Jev → haiku cascade)       → run_skill_evals.py --judge jev
  - checking `file:line` references against content (cookbook "citation check") → grounding_check.py --jev
  - protection against commands hidden in web content (cookbook "guardrails") → jev_guard.py, CLAUDE_JEV_GUARD=1
  - checking executor reports (a "verify → escalate" cascade)        → jev_guard.py, CLAUDE_JEV_REPORT_CHECK=1
  - model tier suggestion for a task (assessments built from noul questions) → jev_client.py --tier "<task description>"

Configuration (environment variables, as in the official SDK; NEVER in repository files):
  TYPESAFE_API_KEY (required), TYPESAFE_BASE_URL (default https://api.typesafe.ai), TYPESAFE_DEFAULT_MODEL (jev-latest).
Rules from the documentation: instructions in English (best accuracy; the state may be in Polish), one condition per
question, a high value = "yes", a state with only the fields needed for the decision, arithmetic and dates in code, the
state content may contain hostile commands. Noul confidence = |2p − 1|; uncertainty band 0.30–0.70 → fallback.
NOTE: the state goes to an external service. The client strips known secret patterns and truncates the state.
The domain jevtypesafeai.com does NOT belong to TypeSafe; the official skill: `claude plugin marketplace add typesafe-ai/skills`.

  python3 .claude/hooks/jev_client.py --check
  python3 .claude/hooks/jev_client.py --tier "Zmień nazwę pola w 3 plikach, testy są"
  echo '{"state": ..., "questions": {...}}' | python3 .claude/hooks/jev_client.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):  # Windows: strona kodowa (cp1250) ≠ UTF-8 Claude Code
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DEFAULT_BASE = "https://api.typesafe.ai"
ENDPOINT = "/v1/systemone"
MAX_STATE_CHARS = 60_000          # service limit: 64k tokens per request, 32k for the state + the longest question
PRICE_PER_MTOK_INPUT = 0.042      # USD (docs.typesafe.ai/models, 2026-10); output tokens are free
LOW, HIGH = 0.30, 0.70            # noul uncertainty band (cookbook "self-consistency: nouls")
SECRET_RULES = [
    r"\b(AKIA|ASIA)[0-9A-Z]{16}\b",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b",
    r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
    r"\bsk-ant-[A-Za-z0-9_-]{20,}\b",
    r"\bsk-(proj-)?[A-Za-z0-9]{32,}\b",
    r"\bAIza[0-9A-Za-z_-]{35}\b",
    r"\b(sk|rk)_live_[0-9a-zA-Z]{20,}\b",
    r"\b(jv|ts)_live_[A-Za-z0-9_-]{8,}\b",
    r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
    r"(?i:\b(password|passwd|secret|api[_-]?key|access[_-]?token|client[_-]?secret)\b\s*[:=]\s*\S{8,})",
]
SECRET_RE = re.compile("|".join(f"(?:{r})" for r in SECRET_RULES))


def api_key() -> str:
    return os.environ.get("TYPESAFE_API_KEY") or os.environ.get("JEV_API_KEY") or ""   # JEV_API_KEY: compatibility with 1.33


def enabled() -> bool:
    return bool(api_key())


def redact(value):
    """Strips secrets from all strings (recursively) and truncates long texts."""
    if isinstance(value, str):
        v = SECRET_RE.sub("[UKRYTO]", value)
        return v if len(v) <= MAX_STATE_CHARS else v[:MAX_STATE_CHARS] + " …[truncated]"
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def decide(state, questions: dict, timeout: float = 10.0, retries: int = 2) -> dict | None:
    """A System One request. Returns `answers` with `_usage` added, or None (no key, error, timeout,
    invalid response) — the caller then uses the fallback. 429/529 → retry with exponential backoff."""
    key = api_key()
    if not key or not questions:
        return None
    base = (os.environ.get("TYPESAFE_BASE_URL") or DEFAULT_BASE).rstrip("/")
    url = base if base.endswith(ENDPOINT) else base + ENDPOINT
    body = json.dumps({"model": os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest"), "state": redact(state),
                       "questions": redact(questions)}, ensure_ascii=False).encode("utf-8")
    t0 = time.time()
    data = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 529) and attempt < retries and time.time() - t0 + 0.5 * 2 ** attempt < timeout:
                time.sleep(0.5 * 2 ** attempt)
                continue
            return None
        except (urllib.error.URLError, OSError, ValueError, TimeoutError):
            return None
    answers = data.get("answers") if isinstance(data, dict) else None
    if not isinstance(answers, dict) or not all(q in answers for q in questions):
        return None
    usage = data.get("usage") or {}
    answers["_usage"] = {"input_tokens": usage.get("input_tokens") or 0, "seconds": round(time.time() - t0, 3),
                         "cost": (usage.get("input_tokens") or 0) * PRICE_PER_MTOK_INPUT / 1e6,
                         "model": data.get("model"), "questions": len(questions)}
    log(answers["_usage"])
    return answers


def log(usage: dict) -> None:
    """Usage to .tf/logs/jev.jsonl (without request content)."""
    try:
        root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
        p = root / ".tf" / "logs" / "jev.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **usage}) + "\n")
    except OSError:
        pass


def p_yes(answer: dict | None, default: float = 0.5) -> float:
    try:
        return float((answer or {}).get("noul", default))
    except (TypeError, ValueError):
        return default


def noul_confidence(p: float) -> float:
    """Noul confidence per the TypeSafe documentation: |2p − 1| (0 at p = 0.5; 1 at p ∈ {0, 1})."""
    return abs(2 * p - 1)


def noul_verdict(p: float, low: float = LOW, high: float = HIGH) -> bool | None:
    """Uncertainty band: p > high → True, p < low → False, in between → None (escalate to a model or a human)."""
    if p > high:
        return True
    if p < low:
        return False
    return None


# ───────────── tier suggestion (assessments built from noul questions) ─────────────

TIER_QUESTIONS = {
    "verifiable": {"type": "noul", "instructions": "Can the result of `task` be checked by running a command "
                   "(tests, linter, type check or build) rather than by human judgement?"},
    "reversible": {"type": "noul", "instructions": "Is `task` easy to undo, for example a code change kept in git "
                   "that touches no production data, money, credentials or external systems?"},
    "decision": {"type": "noul", "instructions": "Does `task` require choosing between approaches or making a design "
                 "trade-off, rather than only carrying out an already decided change?"},
    "risky": {"type": "noul", "instructions": "Does `task` involve security, authentication, permissions, personal "
              "data, payments, data migration or system architecture?"},
    "broad": {"type": "noul", "instructions": "Does `task` span more than one area (for example UI and API and "
              "deployment) or many files without an obvious pattern?"},
}


def suggest_tier(task: str) -> dict | None:
    """The core-cost-control rubric as 5 noul questions; the code assembles the decision. None → grade with the rubric yourself."""
    a = decide({"task": task[:4000]}, TIER_QUESTIONS, timeout=8)
    if not a:
        return None
    p = {k: p_yes(a[k]) for k in TIER_QUESTIONS}
    conf = min(noul_confidence(v) for v in p.values())
    if p["risky"] > HIGH:
        tier, why = "deep", "risk (security, data, money, architecture)"
    elif p["broad"] > HIGH:
        tier, why = "std", "a scope of many areas — split it into steps"
    elif p["decision"] > HIGH and p["verifiable"] < LOW:
        tier, why = "deep", "a decision without objective verification"
    elif p["verifiable"] > HIGH and p["reversible"] > HIGH and p["decision"] < LOW:
        tier, why = "fast", "checkable by a command, reversible, no decision"
    else:
        tier, why = "std", "typical work"
    return {"tier": tier, "why": why, "confidence": round(conf, 2), "p": {k: round(v, 2) for k, v in p.items()},
            "uncertain": conf < 0.4}


def main(argv: list[str]) -> int:
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    if not enabled():
        print("Jev off: set TYPESAFE_API_KEY (a key from console.typesafe.ai; do not write it in the repository).")
        return 2
    if "--check" in argv:
        a = decide({"text": "Ala ma kota."}, {"animal": {"type": "noul", "instructions": "Does `text` mention an animal?"}})
        if not a:
            print("✗ No valid answer — check the key, TYPESAFE_BASE_URL and network access.")
            return 1
        print(f"✓ Jev works: p(yes)={p_yes(a['animal'])}, {a['_usage']['seconds']} s, model {a['_usage']['model']}")
        return 0
    if "--tier" in argv:
        task = " ".join(a for a in argv[1:] if a != "--tier")
        s = suggest_tier(task)
        if not s:
            print("No answer from Jev — assess the task with the core-cost-control rubric.")
            return 1
        tail = " — UNCERTAIN: assess it with the rubric yourself" if s["uncertain"] else ""
        print(f"tier: {s['tier']} ({s['why']}); confidence {s['confidence']}{tail}\n{json.dumps(s['p'])}")
        return 0
    req = json.load(sys.stdin)
    print(json.dumps(decide(req.get("state") or {}, req.get("questions") or {}), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
