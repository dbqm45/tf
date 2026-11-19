# Examples: Scrum and Kanban in practice

## 1. A Monte Carlo forecast instead of a promise from estimates
**Situation:** A team works in Kanban. The product owner asks: "How many items from the release backlog will you finish
in 6 weeks? And when will you finish the 30 items that are on the list?".

**How:**
1. You collect throughput from the last 10 weeks (items finished per week): 4, 6, 3, 5, 7, 2, 5, 6, 4, 5.
2. You do not multiply the average (4.7 × 6) — that gives a forecast with about a 50% chance, which is a coin toss.
3. You simulate 10,000 futures: each week is drawn from the history (script below).
4. You give a forecast with a probability, not a promise date; point estimates are not needed.

**Result:**

| Confidence | Items in 6 weeks (at least) | 30 items done within |
|---|---|---|
| 50% | 28 | 7 weeks |
| 70% | 26 | 7 weeks |
| 85% | 25 | 8 weeks |
| 95% | 22 | 8 weeks |

Answer: "With an 85% chance we will finish at least 25 items in 6 weeks. All 30 — with an 85% chance within
8 weeks. We refresh the forecast every week with new data".

The script (verified, `python3 mc.py`, the output matches the table):
```python
import random
random.seed(42)
tp = [4, 6, 3, 5, 7, 2, 5, 6, 4, 5]  # items finished in the last 10 weeks
N = 10000
sums = sorted(sum(random.choice(tp) for _ in range(6)) for _ in range(N))
for p in (50, 70, 85, 95):
    print(f"{p}%: >= {sums[int(N * (100 - p) / 100)]}")

def weeks(target):
    done = w = 0
    while done < target:
        done += random.choice(tp)
        w += 1
    return w

ws = sorted(weeks(30) for _ in range(N))
for p in (50, 70, 85, 95):
    print(f"{p}%: <= {ws[int(N * p / 100) - 1]} wk.")
```

## 2. A vertical slice of a story
**Situation:** The backlog holds an item "Payment module: database tables, API, screen — 3 sprints". The team wants to
split it into "backend" and "frontend".

**How:**
1. A split by layers breaks INVEST: no part is valuable or testable for the user on its own.
2. You cut vertically along process paths and data variants — every piece goes through the UI, the logic and the data.
3. Each story gets acceptance criteria in Given/When/Then.

**Result:**

| Story | Value for the user |
|---|---|
| As a customer I want to pay for an order by card in PLN so that I can complete it | the happy path, one currency |
| As a customer I want to see the reason a payment was declined so that I can try again | the error path |
| As a customer I want to pay with BLIK so that I do not have to enter card details | a second method variant |
| As an accountant I want to see refunds on an order so that I can reconcile the statement | a business rule |

Criteria for the first: *Given* an order for 120 PLN, *When* the customer pays with a valid card, *Then* the order has
the status "paid" and the customer receives a confirmation. The first story fits in one sprint and delivers a working
increment.

## 3. Work item age as an early signal
**Situation:** On a Kanban board the "In progress" column holds 9 items with a WIP limit of 6. The team says that "everything
is going fine", but nothing has reached "Done" for a week.

**How:**
1. You look at the age of the items, not only at their number.
2. You compare the age with the team's typical cycle time (here: 85% of items finish within 5 days).
3. You apply "finish before you start new work": new work is paused until WIP returns to the limit.

**Result:**

| Item | Age (days) | Assessment |
|---|---|---|
| Invoice import | 11 | over 2× the typical cycle time — split it or clarify the blocker at the Daily |
| VAT report | 8 | waiting for review — a review pair today |
| Customer filter | 6 | borderline — check tomorrow |
| the other 6 | 1–4 | normal |

Decision: until it drops to 6 items nobody takes new work; the Daily starts from the oldest item,
not from a round of "what I did yesterday".
