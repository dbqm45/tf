# Examples of continuous delivery

## 1. A three-week feature branch → a series of small steps
**Situation:** "The branch `feature/new-checkout` has lived for 3 weeks, has 74 changed files and conflicts on every rebase.
How do we deliver it and not repeat this?"

**How:**
1. **Trunk-based development:** branches ≤ 1–2 days, integration at least daily — the current branch is a hidden integration
   risk.
2. **Small batches:** a large change → a series of PRs, each deployable on its own.
3. **A feature flag** separates deployment from release; the flag has an owner and a removal date.
4. **Branch by abstraction** for replacing the old cart: an interface, the new implementation next to it, switching with the flag.
5. **Main always deployable:** every PR goes through the full pipeline, and you fix a red build before new work.

**Result** — the plan for splitting the branch into steps and the flag definition:

| Step | PR | Deployable without release? |
|---|---|---|
| 1 | the interface `CheckoutFlow` + the old cart behind it (no behaviour change) | yes |
| 2 | the new `CheckoutFlowV2` behind the flag `checkout-v2`, off by default | yes |
| 3 | the *expand* data migration: new columns next to the old ones (be-database) | yes |
| 4 | turning the flag on for the internal team | yes |
| 5 | turning it on for everyone, then *contract*: removing the old cart and the flag | yes |

```ts
type FeatureFlag = { key: string; owner: string; removeBy: string; defaultOn: boolean };

export const flags: FeatureFlag[] = [
  { key: "checkout-v2", owner: "payments-team", removeBy: "2026-12-15", defaultOn: false },
];
```

## 2. DORA metrics as a target for teams
**Situation:** "I want to give the teams a target: at least 20 deployments a week, and a ranking of the teams every month."

**How:**
1. DORA metrics are for learning, **they are not targets** (Goodhart's law) — a numeric target encourages splitting deployments
   into artificial pieces.
2. **Compare the system with itself over time**, not teams with each other (different services, different risk).
3. Measure throughput and instability together — speed and stability go together.
4. The level of measurement: the application/service, not a person.

**Result** — the recommendation: instead of a target and a ranking, a quarterly review of the trend of the service `orders-api`:

| Metric | Q2 | Q3 | Conclusion |
|---|---|---|---|
| change lead time | 6 days | 2 days | smaller PRs work |
| deployment frequency | 3 / week | 9 / week | — |
| failed deployment recovery time | 5 h | 1.5 h | — |
| change failure rate | 18% | 9% | faster does not mean worse |
| deployment rework rate | 7% | 6% | unchanged — a task: review the hotfixes |

## 3. Configuration in code and Twelve-Factor
**Situation:** "A service review: the database address is written in `settings.py`, the logs go to the file `app.log`, and we build the image
separately for test and production."

**How:**
1. **Configuration in the environment**, not in the code — one image for all environments.
2. **Separated build/release/run:** build once, release = the image + the environment configuration.
3. **Logs as an event stream:** `stdout`, the platform takes care of collecting them.
4. **Shift left:** a secret scan in the pipeline would have caught the password in `settings.py` before the merge.

**Result:**
```python
import logging
import os
import sys

DATABASE_URL = os.environ["DATABASE_URL"]  # a missing variable = an error at startup, not a silent default value
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig(stream=sys.stdout, level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")
```
Notes from the review: remove the password from the history and change it (ops-secrets-identities), one image promoted test → production.
