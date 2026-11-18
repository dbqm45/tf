# Examples: SAFe

## 1. The order of features in an ART backlog by WSJF
**Situation:** Product Management of the "Online Sales" ART has five features for the next PI and a dispute over what goes first:
"BLIK brings the most money, so it goes to the top".

**How:**
1. You rate each component of the cost of delay relatively, comparing the features with each other (here a conventional scale of 1–10).
2. Cost of delay = business value + time criticality + risk reduction/opportunity enablement.
3. You divide by size (also relative) and sort in descending order.
4. The result is the basis for a conversation at PI Planning, not a verdict — the ratings are set together by Product Management and Business Owners.

**Result:**

| Feature | Value | Time | Risk/opportunities | Cost of delay | Size | WSJF |
|---|---|---|---|---|---|---|
| Feature flags | 1 | 2 | 8 | 11 | 2 | **5.5** |
| Replacing the encryption library (end of support) | 2 | 8 | 7 | 17 | 5 | **3.4** |
| BLIK payment | 9 | 7 | 2 | 18 | 6 | **3.0** |
| Sales report | 6 | 2 | 1 | 9 | 4 | **2.25** |
| Warehouse integration | 7 | 3 | 4 | 14 | 10 | **1.4** |

Conclusion: BLIK has the highest cost of delay, but two smaller features give more value per unit of work
and open up opportunities (the flags will let BLIK be released gradually). The warehouse integration is worth cutting — at size
10 it may not fit in the PI.

## 2. Does SAFe fit?
**Situation:** "We have three teams of 6 people: a mobile app, a partner panel, a company blog. The board wants to
introduce SAFe because 'that is what the big ones do'".

**How:**
1. You check the conditions: a shared solution? real dependencies? a need for synchronization?
2. You count the scale: 18 people is below the typical size of an ART (~50–125 people).
3. You look for the "SAFe-washing" risk: new names on an old process.
4. Before you add coordination — you check whether the dependencies can be reduced.

**Result (a recommendation):**

| Criterion | State | Assessment |
|---|---|---|
| A shared solution | three independent products | no |
| Dependencies between teams | sporadic (shared login) | weak |
| Scale | 18 people | below an ART |
| Readiness to change funding | no signals | no |

Recommendation: **do not introduce SAFe**. Each team works per proc-agile; move the shared login to a single
owner with a clear interface (proc-team-topologies). Come back to the topic when a shared solution
with many teams and real dependencies appears.

## 3. The PI Planning outcome as a shared plan
**Situation:** The "Online Sales" ART (4 teams, PI = 4 iterations + an IP iteration) finishes PI Planning. The RTE asks
for a summary for the Business Owners.

**How:**
1. You collect each team's PI objectives and the dependencies from the program board.
2. Dependencies with no owner or with a date after the receiving iteration you mark as a risk.
3. You describe the plan as a shared prediction that Inspect & Adapt will verify, not as a scope contract.

**Result:**

| Team | PI objective | Dependency | Risk |
|---|---|---|---|
| Payments | BLIK behind a flag for 10% of customers | feature flags from the Platform team (iteration 1) | low |
| Platform | feature flags, a new encryption library | — | medium: the encryption migration is uncertain |
| Cart | a sales report for the sales department | data from Payments (iteration 3) | low |
| Warehouse | the first piece of the integration: stock levels | the warehouse vendor's API (iteration 2) | **high**: no confirmation from the vendor |

The Business Owners accept the objectives and their value; the "Warehouse" risk has an owner (the RTE) and a deadline for clarification before
the end of iteration 1. The System Demo after each iteration shows the integrated increment.
