# Codebase mapping — worked cases

## 1. An unfamiliar Nx + TypeScript repo, one day
- `nx graph --file=graph.json` for project-level edges; `madge --circular --extensions ts apps/ libs/` for file-level cycles.
- `git_territory.py --repo . --all`: the stable centre is `libs/booking-core` (top in 4/4 quarters); `apps/admin` was a Q3 campaign.
- Entry points scored: `apps/web/src/main.ts`, `apps/api/src/main.ts`, two Nest cron controllers found in the module registry.
- Map written with the date and HEAD commit; 3 cycles listed (1 runtime, 2 type-only via `import type`).

## 2. Reading co-change pairs
`git_territory.py --cochange` reports:
| Pair | Share | Reading |
|---|---|---|
| `api/schema.graphql` ↔ `web/src/gql/generated.ts` | 0.95 | regeneration — cheap, the generator keeps them in step |
| `billing/rates.py` ↔ `web/src/pricing/rates.ts` | 0.83 | hand-maintained copy of the same table — hidden agreement, a connascence candidate |
| `config/settings.py` (hub) | with 9 areas | wide reach; not a pair problem |
A 140-file commit "format with black" was skipped by `--max-files 30`; without the limit it would have paired everything with everything.

## 3. Diff impact in a monorepo
Input: 12 changed files, map from commit `4b1d0aa`.
1. `git diff --name-only 4b1d0aa HEAD -- libs/payments` → 7 files changed since the map, 2 of them new → the map of `libs/payments` is
   stale; `libs/catalog` unchanged → its map still holds. `nx show projects --affected` lists 4 projects.
2. Per changed file `code_graph.py . --impact <file>`: `libs/payments/src/refund.ts` is used by 3 files in 2 layers (EXTRACTED) and by a
   queue handler wired in DI (INFERRED).
3. Risk: medium (cross-layer edge into `apps/api`, one INFERRED edge). What to test: refund API contract, the queue handler.

## 4. A repository without history
A zip export with no `.git`: `git_territory.py` exits with code 2. Territory, hotspots, contributors and bus factor are skipped;
Limitations says "no git history — change frequency and owners unknown". The map relies on the import graph and the inventory only.

## 5. Whom to ask
`git_territory.py --authors billing/ --bus-factor`: two people active in `billing/` in the last 90 days, bus factor 1 for
`billing/tax/` (high), `legacy/fax/` nobody active (critical). The map lists initials and areas — not "owners" and no judgement of people.
