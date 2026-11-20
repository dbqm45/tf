# Stage scheduling — dependent stages, parallelism, critical path

## When it applies
- Signal: some work items need the output of others, and their order or parallelism must be decided.
- Not this: a linear status flow of one document (a state machine), or pure shift staffing (task selection + resource holds).
- Who performs a stage → task selection; whether a resource is free → resource holds.

## Core shape
- **Stage**: duration (fixed or a range), dependencies, required resources; any domain payload.
- **Explicit dependencies** come from the work ("ceilings after electrics").
- **Implicit dependencies**: two stages that need the same unique resource cannot overlap. Leaving them out yields plans
  that look parallel on paper and cannot be carried out.
- **Topological sort** → levels of mutually independent stages. Rough duration = sum of each level's longest stage; the
  exact figure and the stages without slack come from the **critical path** method.
- **Calendar placement** — a separate calculation anchored on a kickoff date, on a mandatory window of a key stage, or on
  when resources become free. Changing the start date must not recompute parallelism.
- The generic graph and its algorithms are separate from the domain; nodes carry any payload.

## Rules
- A cycle is a business result — "no feasible plan" — with a suggested minimal set of dependencies to drop, for a human to
  decide. Never a technical exception.
- A delay on a critical stage delays the whole project; penalties for that are computed by price calculation and posted by
  the value ledger.
- Unmet resource needs emit an event for other processes (e.g. risk tracking).
- Tests are business scenarios with assertions in domain language ("flooring is on level 4", "HVAC is critical").

## Decisions to settle
- Which dependencies are real and which are habit?
- Start-before-finish (partial) dependencies?
- Uncertain durations: ranges, simulation?
- Working calendars, holidays, shifts?
- Re-planning after a delay — automatic or approved?
- Is the plan binding (it places resource holds) or a simulation? Who approves it?

## Belongs elsewhere
- Who → task selection; when a resource is free → resource holds; penalties → price calculation and value ledger.

## Traps
- Parallel stages that share the single crane or scissor lift.
- A cycle that crashes the planner with a stack trace.
- Calendar dates baked into the dependency graph, so moving the kickoff reshuffles levels.

## Worked example
Requirement: fitting out a retail store — demolition, then electrics and HVAC, then ceilings after both, then flooring,
then shelving. Electrics (4 days) and HVAC (3 days) both need the single scissor lift. The landlord fines per day late.
The drawn plan also has flooring before ceilings and ceilings before flooring.
- Cycle detected: ceilings ↔ flooring. Reported as "no feasible plan"; suggested drop: *flooring before ceilings* (it
  contradicts the stated order) — a human confirms.
- Implicit dependency from the lift: electrics and HVAC cannot overlap → order them (electrics first, decision A).
- Levels after the fix: L1 demolition (2 d), L2 electrics (4 d), L3 HVAC (3 d), L4 ceilings (3 d), L5 flooring (2 d),
  L6 shelving (1 d) → 15 days, every stage critical. Without the lift constraint the plan would wrongly show 12 days.
- Calendar: kickoff 2026-03-02, working days only → handover 2026-03-20; moving the kickoff shifts dates, not levels.
- Fines: a per-day penalty calculator (price calculation) on days beyond the agreed handover.
