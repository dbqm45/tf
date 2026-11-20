# Observations and measurements — recorded facts about a subject, with method, time and certainty

## When it applies
- Signal: the system records what someone or something *found out* about a subject — a reading, a test result, an
  inspection finding, a classification — and later decisions depend on how, when and how surely it was found.
- Typical requirements: lab and field tests, sensor readings, quality inspections, condition surveys, audit findings,
  grading, KPIs derived from other figures, "flag it when the value is out of range".
- Not this: a static attribute that never needs a method, a time or a correction (a product's colour in the catalogue)
  → a plain field or product definitions.

## Core shape
- **Property kind** (catalogue, configuration): *what* can be observed — "free chlorine", "turbidity", "corrosion
  grade", "bacteria present". It lists the allowed units or the allowed **category values**, and the methods.
  Thousands of kinds are rows, not columns.
- **Observation** (operational, appended daily): subject, property kind, result, method, performer, two times, status.
  - **Measurement**: the result is a quantity (amount + unit, see quantities and money) — store the unit given at capture,
    convert on read.
  - **Category observation**: the result is a category value owned by one property kind ("grade C" of *corrosion grade* is
    not "grade C" of *paint finish*), plus a **present / absent** flag — absence is a finding too.
- **Method**: how the result was obtained (field kit, accredited lab, inline sensor model X), with its accuracy and
  detection limit. Odd values are explained by the method, so it is always recorded.
- **Two times**: *applies at / during* (when the fact held — the sampling time) and *recorded at* (when it entered the
  system). A result typed in three days after sampling keeps the sampling time.
- **Status**: *accepted* (a basis for action), *tentative* (prompts a re-check, triggers nothing), *forecast* (about a
  future state). A forecast that comes true is recorded again as an accepted observation.
- **Rejection**: a wrong observation is never deleted; it is marked rejected with a link to the observation that rejects
  it. *Rejected* (it was never true) differs from *ended* (it was true until a date).
- **Derived observation**: a result computed from other observations by a named **rule or formula** (a band, an index,
  a ratio, a roll-up). It keeps links to its inputs and to the rule version.

## Rules
- Bands map a number to a category with explicit interval bounds (inclusive / exclusive stated per band, no overlap, no
  gap unless intended), e.g. *0.2 ≤ chlorine < 0.5 mg/L → "low"*. Bands are data on the property kind, or a rule when the
  thresholds depend on context (another observation, a season, a site class).
- A category hierarchy has one-way inference: a specific finding implies its broader category; the absence of a broad
  category implies the absence of every narrower one; nothing else follows.
- Only accepted observations and forecasts start work (an alarm, a work request); tentative ones start a re-check.
- When an accepted observation is rejected, every derived observation and decision that used it is re-evaluated —
  keep the input links so they can be found.
- Several methods may give the same property kind; order them by preference so a derived figure picks one deterministically.
- A comparison (actual vs plan, this year vs last) is a derived observation over two results of the same kind that differ
  only in their variant (actual, plan version, forecast).
- Roll-ups (site → region → network) need an aggregation rule per property kind — sum for volumes, mean or max for
  concentrations; a cumulative figure (year to date) does not roll up by period.

## Decisions to settle
- Which property kinds and category lists does the business own, and who may change them (they are configuration that
  needs tests)?
- Correction policy: reject-and-replace only, or may a draft result be edited before acceptance?
- Which statuses exist in this business (accepted / tentative / forecast, or more)? Who promotes tentative to accepted?
- Band thresholds and their source (a regulation, a contract, an internal target), with validity dates.
- How long raw readings are kept vs only derived figures (volume and retention).

## Belongs elsewhere
- Amount and unit arithmetic → quantities and money.
- The work that produced or reacts to an observation (sampling round, repair) → work execution.
- Signed test certificates and reports as evidence → evidence documents.
- Dashboards and multidimensional analysis on top of derived figures → the data skills (data-*).
- Time-series storage and sensor ingestion → technology choice (be-database), not the model.

## Traps
- One column per measurable property (`ph`, `chlorine`, `turbidity`, … forty nullable columns) — every new test is a
  migration.
- The unit in the column name (`weight_kg`) and bare numbers; input in another unit is converted by hand and wrongly.
- A single timestamp — a late-entered result looks like a fresh one and triggers a false alarm.
- `UPDATE readings SET value = …` to fix a sensor fault — the alarm that fired on the old value cannot be explained.
- Categories as free strings shared across kinds; "absent" not recordable, so "not tested" and "tested negative" look the same.
- A derived index stored without its inputs and formula version — it cannot be recomputed after a correction.

## Worked example
Requirement: a water utility samples taps across 40 districts; field staff use a test kit, the accredited lab confirms;
inline sensors report turbidity every 5 minutes; a district is "non-compliant" when free chlorine is below 0.2 mg/L or
E. coli is present; sensor glitches happen; regulators ask what was known when.
- Property kinds: *free chlorine* (mg/L; bands: < 0.2 "non-compliant", 0.2–0.5 "low", > 0.5 "ok"), *E. coli*
  (category: present / absent), *turbidity* (NTU). Methods: *field kit DPD* (accuracy ±0.05 mg/L), *lab ISO-accredited*.
- Sample `S-2207` in district D12, sampled 2026-03-04 09:10, field kit 0.15 mg/L → measurement, status **tentative**
  (field kit policy) → a re-check request, no alarm.
- Lab result recorded 2026-03-06 for the same sampling time: 0.17 mg/L, **accepted** → derived *compliance = non-compliant*
  for D12 with inputs [lab result], rule *chlorine-bands v3* → a work request (flushing) — the alarm references the input.
- Sensor T-55 reports 48 NTU spikes at 02:00; maintenance finds a fouled lens: each spike observation is **rejected** by the
  maintenance finding, the derived hourly mean is recomputed, the original rows stay.
- Regulator's question "what did you know on 5 March?": accepted observations with `recorded_at ≤ 2026-03-05` → only the
  tentative field result; the non-compliance was established on 6 March.
