# Estimating cost and schedule — an example

The numbers in the example were computed with a script (2026-10-03). The project: a room booking system, the estimate in person-days.

## 1. The outside view (the reference class)
1. Collect at least a few completed projects of a similar class (the same type of system, a similar team and stack):
   plan and reality (cost, time).
2. Compute the distribution of the reality / plan ratio, e.g. a median of 1.3, the 80th percentile 1.8.
3. You multiply your "inside" estimate by the percentile that matches the accepted risk (P50 for a portfolio
   of many projects, P80 for a single important project).

Without your own historical data: say so plainly, give a wide range and plan a discovery stage that
will provide data (the first milestone as a measurement).

## 2. The inside view (a three-point estimate)
| Part | O | M | P | E = (O+4M+P)/6 | σ = (P−O)/6 |
|---|---|---|---|---|---|
| End-to-end skeleton and CI | 5 | 8 | 15 | 8.7 | 1.7 |
| Room bookings | 10 | 15 | 30 | 16.7 | 3.3 |
| Notifications | 4 | 6 | 12 | 6.7 | 1.3 |
| Admin panel | 6 | 10 | 20 | 11.0 | 2.3 |
| Calendar integration | 5 | 10 | 30 | 12.5 | 4.2 |
| **Sum** | 30 | **49** | 107 | **55.5** | √Σσ² = **6.2** |

Conclusions:
- the sum of the "most likely" values (49) is lower than the sum of the expected values (55.5) — whoever reports the sum of M
  understates the estimate;
- the range from independent parts (P80 ≈ 55.5 + 0.84 × 6.2 ≈ 60.7) is too narrow, because the parts are not independent
  (common causes: unclear requirements, new technology, people's availability), and overruns in IT have a fat tail;
- so you take the final range from the reference class: e.g. with percentiles 1.3 (P50) and 1.5 (P80) —
  P50 ≈ 72 person-days, P80 ≈ 83 person-days;
- the widest range is in the calendar integration (P − O = 25) — a candidate for a spike in the first milestone.

## 3. From person-days to schedule and cost
- Schedule: person-days ÷ (number of people × real availability) + external dependencies (approvals, vendors, tests with users).
  You establish availability with the people, you do not assume 100%.
- Cost: person-days × rate + environments + licences + AI models + maintenance. State the source of the rate.
- Reserves: for identified risks (Σ probability × cost of impact from the register) and a management reserve for the unknown.

## 4. Updating
After each milestone compare reality with the plan for the completed parts and recompute the forecast. When the team
has a throughput history, the schedule forecast comes from a Monte Carlo simulation (proc-agile).
