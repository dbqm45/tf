# Work execution — the prescribed procedure vs the work actually done

## When it applies
- Signal: the difference between how work should be done and what really happened (who, when, with what result) matters —
  inspections, repairs, clinical procedures, audits, field service.
- Not this: pure timing of stages → stage scheduling.

## Core shape
- **Procedure (template)**: ordered steps, possibly nested; a result type per step (measurement with unit, pass/fail,
  remark, photo); a version.
- **Execution**: references the procedure version it followed (or a snapshot of its steps). Editing a procedure in place
  would break old executions — version it.
- **Work chain**:
  - **work request** — what is needed (from a customer, a sensor alarm, a schedule);
  - **work order / effort** — what was done; request ↔ order is many-to-many (one order covers three requests, one
    request needs two orders);
  - **party assignments** — who, in which role, for which period;
  - **time entries** — who, from–to, against which work item. Never a single `hours` field; summing and costing
    belong to the value ledger and price calculation.
- **Intended vs performed work**: two records, not one with two dates. The intended work item lives in plans; its time,
  performers and place can be set in any order. The performed record is created when work starts. The link is optional
  both ways — plans are dropped, and unplanned work happens. Rebooking a missed intention creates a new intended item.
- **Plan**: references to intended work items with dependencies between the references. One item may appear in several
  plans (a maintenance plan and a shutdown plan); a plan may replace others (split, merge, supersede).
- **Resource claim**: intended work *reserves*, performed work *consumes*. A **general** claim names a kind ("one
  certified welder, 4 h"); it is later resolved into a **specific** claim (Nowak, Tuesday 8–12). Durable resources are
  claimed for time, consumables by quantity (drawn from a stock holding, see value ledger).
- **Execution states**: proposed, started, suspended ↔ resumed, completed, abandoned. Each transition is an event with
  time, actor and justification.
- **Step result**: execution data typed by the step definition.

## Rules
- **Completed ≠ successful**: completion says the work was carried out as intended; whether it achieved its aim is a
  separate outcome, recorded as an observation linked to the work (observations and measurements).
- **Abandoned** is final; a temporary stop is a **suspension** record with a period (it stays as history after resuming).
  Holding an intended item postpones its start.
- Procedures (templates) generate plans or child work items; skilled work may deviate from the template's order —
  record the deviation, do not forbid it.
- Checks that need information not yet known (which specific technician) are lazy: accept the record, show an open
  consistency issue, resolve later; checks that are easy at capture time are enforced at once.
- Plan and execution are separate: moving a planned date does not change when work actually happened.
- Choose a notation by the nature of the work (OMG specifications, omg.org, accessed 2026-11-20):
  - predictable flow → **BPMN 2.0**;
  - case work driven by human judgement → **CMMN 1.1** (do not force a fixed order);
  - decision tables → **DMN**; decision logic is a separate module.
  A workflow engine is a technology choice, not the domain model; step names come from the experts' language.
- Checklist from the classic control-flow patterns: parallel split, synchronisation, exclusive choice, cancellation.
  Also check: rework, repeated steps, reopening after completion, partial completion of composite work, negative results,
  a procedure changing mid-execution, attachments and evidence, deadlines and escalation (parameters).
- Responsibility of a performer is a party relationship, not a text field. Approval rights are authorisation.

## Decisions to settle
- Snapshot steps onto each execution, or reference an immutable procedure version?
- What happens to running executions when a procedure gets a new version?
- Can a completed execution be reopened, and by whom (authorisation)?
- Which step results are mandatory before completion?
- Deadlines and escalation rules (parameters from a policy).

## Belongs elsewhere
- Costing of time → price calculation and value ledger; who is free → resource holds; evidence of results →
  evidence documents.

## Traps
- A `status` column plus `hours_spent` on the work order.
- Editing the checklist template and silently changing last year's inspection records.
- Planned and actual dates in the same field.
- Unplanned work forced to get a fake plan entry; a suspension recorded as abandon-and-recreate.
- "Completed" read as "fixed" — no outcome recorded, so repeated failures stay invisible.
- A BPMN engine's process model treated as the domain model.

## Worked example
Requirement: a lift-maintenance firm runs a monthly 14-point inspection; technicians sometimes stop when a part is
missing and come back; auditors need what was measured and by whom.
- Procedure `LIFT-MONTHLY v5`: 14 steps; step 6 "brake gap" result type = measurement in mm (range 0.2–0.6), step 9
  "door sensor" = pass/fail.
- Work request `WR-901` (schedule) → work order `WO-4412`; party assignment: technician Lis, role *inspector*.
- Execution of `WO-4412` follows v5: started 08:10 → suspended 08:55 (reason: missing sensor) → resumed next day
  10:00 → completed 10:40. Time entries: 08:10–08:55 and 10:00–10:40.
- Step 6 result: 0.71 mm → negative result triggers a follow-up work request (rework), escalation deadline a parameter.
- Procedure v6 published later; `WO-4412` still shows v5 steps.
