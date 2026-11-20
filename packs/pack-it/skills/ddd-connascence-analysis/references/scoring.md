# Degree and cost

## What we count as a place (degree)
- one place = one line of production code that **would change** if the contract changed;
- we do not count: imports, unused declarations, comments; tests — a separate column (for information);
- a helper function that encloses the contract in one place counts as **one** place (it is good practice — this is meant to be visible);
- one line can count in several rows if it binds several contracts.

| Kind | We count |
|---|---|
| name | calls/references on the other side |
| type | places that construct or unpack the type on the other side |
| meaning | places that interpret the value (comparisons, mappings) on both sides |
| position | calls with a positional argument list |
| algorithm | copies of the algorithm |
| execution order | steps that must keep the order |
| timing | places with a timing assumption (timeout, retry, sleep) |
| value | writes to each of the stores that must agree |
| identity | components that receive the same instance |

## Row cost
`cost = rank × log2(1 + degree)`, rounded to 0.01. A degree given as a range → count with the **upper** bound.
The logarithm: the tenth place hurts less than the second, but the kind (rank) dominates.

## Sorting (deterministic)
cost descending → the first source path → line → row id.

## Bands
static weak (1–2) · static semantic (3–5) · dynamic (6–9). A row with > 8 sources: the full list in an appendix.
