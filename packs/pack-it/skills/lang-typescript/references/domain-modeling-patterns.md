# Domain modelling patterns in TypeScript (a supplement to `domain-building-blocks.md`)

> **Contents:** Type + companion object with the same name; required and… · Events: metadata, internal vs published, an exhaustive… · Decider and a shell with an explicit unit of work (no… · Module aliases without `baseUrl` · Pitfalls (checked by a test) · Tests

Checked: TypeScript 6.0.3 and 7.0.2 (`strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `erasableSyntaxOnly`,
`verbatimModuleSyntax`), run without compilation by Node 22 (`node --test`, type stripping). The conclusions come partly from an analysis
of the SmartSchedule example system (the Domain Drivers course) — the code is written from scratch.

## Type + companion object with the same name; required and optional brand
```ts
declare const brand: unique symbol;
/** Required brand: a raw string cannot be assigned without the factory. */
export type Brand<T, B extends string> = T & { readonly [brand]: B };
/** Optional brand: accepts the raw type (convenient for durations, counters). */
export type Flavour<T, F extends string> = T & { readonly [brand]?: F };
```
```ts
import { randomUUID } from 'node:crypto';
import type { Brand } from '#shared/brand';

// A type and a companion object with the same name: `ResourceId` as a type and as a factory.
export type ResourceId = Brand<string, 'ResourceId'>;
export const ResourceId = {
  newOne: (): ResourceId => randomUUID() as ResourceId,
  from: (raw: string): ResourceId => {
    if (!/^[0-9a-f-]{36}$/.test(raw)) throw new RangeError(`invalid ResourceId: ${raw}`);
    return raw as ResourceId;
  },
};

// An "enum" as a literal union + a companion with the list of values and a type guard.
export type Seniority = 'JUNIOR' | 'MID' | 'SENIOR' | 'LEAD';
export const Seniority = {
  values: ['JUNIOR', 'MID', 'SENIOR', 'LEAD'] as const satisfies readonly Seniority[],
  is: (x: string): x is Seniority => (Seniority.values as readonly string[]).includes(x),
};
```
Instead of an `enum` — a literal union with a companion (`values`, the `is` guard); it works with type stripping, unlike an `enum`.

## Events: metadata, internal vs published, an exhaustive `switch`
```ts
import type { ResourceId } from '#shared/ids';

type Meta = { readonly eventId: string; readonly occurredAt: Date };
export type DomainEvent<T extends string, D> = Readonly<{ type: T; data: Readonly<D> & Meta }>;
declare const published: unique symbol;
/** An event published outside the module (Published Language) — a marker only in the type, so that an internal one is not sent. */
export type PublishedEvent<T extends string, D> = DomainEvent<T, D> & { readonly [published]: true };
export type Publisher = (e: PublishedEvent<string, unknown>) => void;   // accepts only published events

export type ResourceBlocked = DomainEvent<'ResourceBlocked', { resourceId: ResourceId; owner: string }>;
export type ResourceTakenOver = PublishedEvent<'ResourceTakenOver', { resourceId: ResourceId; previousOwners: readonly string[] }>;
export type AvailabilityEvent = ResourceBlocked | ResourceTakenOver;

export const event = <E extends DomainEvent<string, unknown>>(
  type: E['type'], data: Omit<E['data'], keyof Meta>, clock: () => Date, id: () => string,
): E => ({ type, data: { ...data, eventId: id(), occurredAt: clock() } }) as unknown as E;

export function assertNever(x: never): never { throw new Error(`unhandled: ${JSON.stringify(x)}`); }

export function describe(e: AvailabilityEvent): string {
  switch (e.type) {
    case 'ResourceBlocked': return `blocked by ${e.data.owner}`;
    case 'ResourceTakenOver': return `taken over from ${e.data.previousOwners.join(', ')}`;
    default: return assertNever(e);   // a new event type = a compile error here
  }
}
```
The `published` marker exists only in the type (a symbol), and `Publisher` accepts only published events — an attempt to send
an internal event is a compile error (checked with `@ts-expect-error`).

## Decider and a shell with an explicit unit of work (no decorators)
```ts
// Decider: immutable state, commands as a union, a pure decide() function. No classes with parameter properties
// (not allowed with erasableSyntaxOnly / running by type stripping).
export type Slot = Readonly<{ state: 'free' } | { state: 'blocked'; by: string } | { state: 'disabled'; by: string }>;
export type SlotState = Readonly<{ slot: Slot; version: number }>;

export type Command =
  | { readonly kind: 'block'; readonly owner: string }
  | { readonly kind: 'release'; readonly owner: string }
  | { readonly kind: 'disable'; readonly owner: string };

export type Rejection = 'NOT_FREE' | 'NOT_OWNER' | 'DISABLED';
export type Decision =
  | { readonly ok: true; readonly state: SlotState; readonly previousOwner?: string }
  | { readonly ok: false; readonly reason: Rejection };

export function decide(s: SlotState, c: Command): Decision {
  const next = (slot: Slot): SlotState => ({ slot, version: s.version + 1 });
  switch (c.kind) {
    case 'block':
      if (s.slot.state === 'disabled') return { ok: false, reason: 'DISABLED' };
      if (s.slot.state === 'blocked') return { ok: false, reason: 'NOT_FREE' };
      return { ok: true, state: next({ state: 'blocked', by: c.owner }) };
    case 'release':
      if (s.slot.state !== 'blocked' || s.slot.by !== c.owner) return { ok: false, reason: 'NOT_OWNER' };
      return { ok: true, state: next({ state: 'free' }) };
    case 'disable': {
      const previousOwner = s.slot.state === 'blocked' ? s.slot.by : undefined;
      return { ok: true, state: next({ state: 'disabled', by: c.owner }), ...(previousOwner ? { previousOwner } : {}) };
    }
  }
}

// Shell: load → decide → save (explicitly) → publish; the transaction as an explicit unit of work, no decorators.
export interface SlotRepository { load(id: string): Promise<SlotState>; save(id: string, s: SlotState, expectedVersion: number): Promise<void>; }
export type UnitOfWork = <T>(work: (repo: SlotRepository) => Promise<T>) => Promise<T>;

export async function handle(uow: UnitOfWork, id: string, c: Command, publish: (msg: string) => void): Promise<Decision> {
  const d = await uow(async (repo) => {
    const s = await repo.load(id);
    const r = decide(s, c);
    if (r.ok) await repo.save(id, r.state, s.version);   // explicit save — do not rely on "dirty checking"
    return r;
  });
  if (d.ok && d.previousOwner) publish(`taken over from ${d.previousOwner}`);   // after the commit; without an outbox it can be lost
  return d;
}
```
Pass the transaction explicitly (`uow(repo => …)`, e.g. `db.transaction(tx => useCase(deps(tx)))`) instead of decorators that
attach the connection to services through reflection: "legacy" decorators (`experimentalDecorators`) have a different signature from the standard ones,
and parameter properties and `enum` are not allowed with `erasableSyntaxOnly`.

## Module aliases without `baseUrl`
`package.json` → `"imports": { "#shared/*": "./src/shared/*.ts" }` — works in Node and in TS (`moduleResolution: nodenext`/`bundler`)
without `paths`/`baseUrl` (deprecated in TS 6). Guard module boundaries with an import rule in ESLint (flat config) or an architecture test.

## Pitfalls (checked by a test)
```ts
// Pitfalls checked by running them (see the test).
export const monthIsZeroBased = new Date(Date.UTC(2021, 1, 1)).toISOString().slice(0, 10); // '2021-02-01' — February!
export const sameInstance = (): boolean => { const t = new Array(3).fill([]); t[0]!.push(1); return t[1]!.length === 1; };
export const freshInstances = (): boolean => { const t = Array.from({ length: 3 }, () => [] as number[]); t[0]!.push(1); return t[1]!.length === 0; };
// Comparing objects with the > operator uses valueOf(); an object whose valueOf returns a string compares lexicographically.
export const lexicographic = (): boolean => { const a = { valueOf: () => '9' }; const b = { valueOf: () => '10' }; return (a as unknown as number) > (b as unknown as number); };
```
- The `<`, `>` operators on objects (e.g. big decimal numbers from a library) call `valueOf()` — when it returns a string,
  the comparison is **lexicographic**. Use the library's methods (`a.gt(b)`) or a `bigint` in the smallest unit.
- A class that extends `Array` needs care (`Symbol.species`, the prototype) — composition is better: a class with a private array.
- A method that mutates the object **and** returns a new instance confuses callers — pick one.

## Tests
```ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ResourceId, Seniority } from '#shared/ids';
import { decide, handle, type SlotState, type SlotRepository } from './decider.ts';
import { describe as describeEvent, event, type ResourceTakenOver } from './events.ts';
import { monthIsZeroBased, sameInstance, freshInstances, lexicographic } from './pitfalls.ts';

test('id and literal union', () => {
  const id = ResourceId.newOne();
  assert.equal(ResourceId.from(id), id);
  assert.throws(() => ResourceId.from('x'));
  assert.ok(Seniority.is('MID')); assert.ok(!Seniority.is('GURU'));
});

test('decider: block, conflict, takeover', () => {
  const free: SlotState = { slot: { state: 'free' }, version: 0 };
  const b = decide(free, { kind: 'block', owner: 'A' });
  assert.ok(b.ok);
  assert.deepEqual(decide(b.state, { kind: 'block', owner: 'B' }), { ok: false, reason: 'NOT_FREE' });
  const d = decide(b.state, { kind: 'disable', owner: 'S' });
  assert.ok(d.ok && d.previousOwner === 'A' && d.state.version === 2);
});

test('shell saves explicitly and publishes after the save', async () => {
  const db = new Map<string, SlotState>([['r1', { slot: { state: 'blocked', by: 'A' }, version: 3 }]]);
  const repo: SlotRepository = {
    load: async (id) => db.get(id)!,
    save: async (id, s, expected) => { if (db.get(id)!.version !== expected) throw new Error('conflict'); db.set(id, s); },
  };
  const published: string[] = [];
  const r = await handle(async (w) => w(repo), 'r1', { kind: 'disable', owner: 'S' }, (m) => published.push(m));
  assert.ok(r.ok); assert.equal(db.get('r1')!.version, 4); assert.deepEqual(published, ['taken over from A']);
});

test('event with metadata and exhaustive switch', () => {
  const e = event<ResourceTakenOver>('ResourceTakenOver', { resourceId: ResourceId.newOne(), previousOwners: ['A'] }, () => new Date(0), () => 'e1');
  assert.equal(e.data.eventId, 'e1');
  assert.equal(describeEvent(e), 'taken over from A');
});

test('pitfalls', () => {
  assert.equal(monthIsZeroBased, '2021-02-01');
  assert.ok(sameInstance()); assert.ok(freshInstances()); assert.ok(lexicographic());
});

test('an internal event cannot be published (the compiler checks)', () => {
  const sent: string[] = [];
  const publisher: import('./events.ts').Publisher = (e) => { sent.push(e.type); };
  const internal = event<import('./events.ts').ResourceBlocked>('ResourceBlocked', { resourceId: ResourceId.newOne(), owner: 'A' }, () => new Date(0), () => 'e2');
  // @ts-expect-error — ResourceBlocked is not a published event
  publisher(internal);
  const pub = event<ResourceTakenOver>('ResourceTakenOver', { resourceId: ResourceId.newOne(), previousOwners: [] }, () => new Date(0), () => 'e3');
  publisher(pub);
  assert.equal(sent.length, 2);
});
```
`node:test` is enough for libraries and a pure domain (zero dependencies); for applications with Vite/a browser — tool-vitest.

