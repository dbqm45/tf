# GDPR in the team's practice — procedures and code

## 1. Retention table (an example for a room booking system)
| Data | Purpose | Basis (to be confirmed by the DPO) | Period | Deletion mechanism |
|---|---|---|---|---|
| account (name, email) | account handling | contract | until the account is deleted + the complaint period | account deletion → a deletion job |
| phone | booking reminders | contract / consent — a decision | until the account is deleted | as above |
| booking history | settlements | legal obligation (accounting) | per tax rules | a retention job |
| analytics events | product improvement | legitimate interest or consent — a decision | 13 months, a pseudonym instead of the ID | a retention job |
| application logs | security and diagnosis | legitimate interest | 30 days, without the content of requests with data | log rotation |
| backups | business continuity | legitimate interest | 35 days | expiry in the backup store |

The periods in the table are an example for a decision, not a legal recommendation.

## 2. Pseudonymization and a retention job (Python)
Checked 2026-10-03 on CPython 3.14.8: pytest 9.1.1 (2 tests), `mypy --strict`, ruff with the `S` security rules.
```python
import hashlib
import hmac
import sqlite3
from datetime import datetime, timedelta


def pseudonym(value: str, key: bytes) -> str:
    """A stable pseudonym with an HMAC key — without the key it cannot be reversed with a dictionary."""
    normalized = value.strip().lower().encode("utf-8")
    return hmac.new(key, normalized, hashlib.sha256).hexdigest()[:32]


def purge_expired(db: sqlite3.Connection, now: datetime, keep_days: int) -> int:
    """A retention job: deletes reservations older than the retention period; returns the number deleted."""
    cutoff = (now - timedelta(days=keep_days)).isoformat()
    cur = db.execute("DELETE FROM reservations WHERE ended_at < ?", (cutoff,))
    db.commit()
    return cur.rowcount

```
```python
import sqlite3
from datetime import UTC, datetime, timedelta

from privacy_tools import pseudonym, purge_expired

KEY = b"klucz-testowy"


def test_pseudonym_is_stable_after_normalization_and_depends_on_key() -> None:
    a = pseudonym("Jan.Kowalski@example.com ", KEY)
    assert a == pseudonym("jan.kowalski@example.com", KEY)
    assert a != pseudonym("jan.kowalski@example.com", b"inny-klucz")


def test_purge_removes_only_rows_past_retention() -> None:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE reservations (id INTEGER PRIMARY KEY, phone TEXT, ended_at TEXT)")
    now = datetime(2026, 10, 3, tzinfo=UTC)
    db.executemany("INSERT INTO reservations (phone, ended_at) VALUES (?, ?)", [
        ("500100200", (now - timedelta(days=400)).isoformat()),
        ("500100201", (now - timedelta(days=10)).isoformat()),
    ])
    assert purge_expired(db, now, keep_days=365) == 1
    assert db.execute("SELECT phone FROM reservations").fetchall() == [("500100201",)]
```
You keep the pseudonymization key in the secrets manager (ops-secrets-identities), separately from the data — with the key
the pseudonym can be linked to the person, so it is still personal data. A plain SHA-256 hash of an email without a key is easy
to reverse with a dictionary of addresses.

## 3. A data erasure request — the flow
1. Intake: the channel, the date (you count the month from it), identity verification.
2. Checking exceptions: whether a rule requires keeping part of the data (e.g. invoices) — then you restrict
   the processing of that part, the rest you erase.
3. Erasure in the system: the account, related records, files, search indexes, cache.
4. Processors: an erasure instruction (mailing, analytics, customer service), with confirmation.
5. Logs and backups: they expire with the cycle; the identifier goes on the list of erased ones, which you apply after every
   backup restore.
6. An answer to the person and an entry in the request register (date, scope, result).
An automated test: after the account is deleted, queries to all tables with this person's data return nothing.

## 4. Personal data breach — the timeline
| Time since becoming aware | Action | Who |
|---|---|---|
| immediately | stopping the leak (closing access, rotating keys), securing the evidence | the team + ops-security-operations |
| within a few hours | establishing: what data, how many people, since when, who had access, whether the data was encrypted | the team, the agent gathers facts |
| before 72 h pass | a risk assessment and the decision on notifying UODO (the supervisory authority); the notification (information can be supplemented in stages) | the controller with the DPO |
| without undue delay | notifying the persons, if the risk is high: what happened, the consequences, what we are doing, what they can do | the controller |
| always | an entry in the internal breach register, also for unreported ones; a process fix and a lesson | the team |

A processor (e.g. the company maintaining the system) notifies the controller without undue delay — the 72-hour deadline runs
at the controller.

## 5. When to consider a DPIA — control questions
- Does the system assess or profile people in a way that has significant effects for them (credit, work, access to services)?
- Does it process special categories of data or data on convictions on a large scale?
- Does it monitor people systematically (location, behaviour, public places)?
- Does it use biometric data, combine data sets from different sources, apply a new technology (e.g. an AI model making
  decisions)?
- Does it concern particularly vulnerable people (children, patients, employees)?
Two "yes" answers are a strong signal to ask the DPO about a DPIA; the UODO list (M.P. 2019 item 666) settles the cases on the list.
