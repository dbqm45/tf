# Domain building blocks in TypeScript — a tested example

> **Contents:** 1. Money (`bigint` minor units) · 2. Measure with a unit · 3. Branded identifiers · 4. Member variants · 5. Loan period, read model, UI request state · 6. Data-driven field validation · 7. Accessory compatibility rules · 8. Result · 9. Aggregate with a state machine and events · 10. Repository port · 11. Barrel and compiler settings · 12. Tests: edge cases

One domain runs through every section: a **neighbourhood tool library** that lends drills, ladders and welders to its
members. `lang-java/references/domain-building-blocks.md` models the same domain, so Money, identifiers, variants,
Result, the loan period, the aggregate and the tests map one to one; sections 2, 5 (read model, UI state), 6 and 7 are
extra here because forms and views usually live in TypeScript.

Checked 2026-11-20: `tsc -p .` with `strict`, `noUncheckedIndexedAccess`, `erasableSyntaxOnly` and
`verbatimModuleSyntax` passes on TypeScript **5.9.3, 6.0.3 and 7.0.2**, and `node dist/lending.test.js` (Node 22)
prints the OK line. From 6.0 on set `rootDir` and `types` explicitly (section 11). No `any`, no non-null `!`, no
framework. Each `// ===== path =====` comment starts a separate file of a `lending/` domain folder; in a project
keep one exported concept per file, as here.

Only erasable syntax is used (no `enum`, `namespace` or constructor parameter properties), so deleting the types gives
working JavaScript — see `lang-javascript`.

## 1. Money (`bigint` minor units)
Amounts never pass through `number`: parsing goes from text straight to minor units, and `toDecimalString()` is what
you send to an API.

```ts
// ===== lending/money.ts =====
export type Currency = 'PLN' | 'EUR' | 'JPY';

const FRACTION_DIGITS = { PLN: 2, EUR: 2, JPY: 0 } as const satisfies Record<Currency, number>;

const AMOUNT = /^(-)?(\d+)(?:[.,](\d+))?$/;

export class Money {
  readonly minor: bigint;
  readonly currency: Currency;

  private constructor(minor: bigint, currency: Currency) {
    this.minor = minor;
    this.currency = currency;
  }

  /** Accepts "12", "12.5", "12,50", "-3.10". More decimals than the currency has is an error, not a rounding. */
  static of(text: string, currency: Currency): Money {
    const match = AMOUNT.exec(text.trim());
    const whole = match?.[2];
    const fraction = match?.[3] ?? '';
    const digits = FRACTION_DIGITS[currency];
    if (match === null || whole === undefined || fraction.length > digits) {
      throw new Error(`Not a ${currency} amount: "${text}"`);
    }
    const minor = BigInt(whole + fraction.padEnd(digits, '0'));
    return new Money(match[1] === '-' ? -minor : minor, currency);
  }

  static fromMinor(minor: bigint, currency: Currency): Money {
    return new Money(minor, currency);
  }

  static zero(currency: Currency): Money {
    return new Money(0n, currency);
  }

  add(other: Money): Money {
    this.#sameCurrency(other);
    return new Money(this.minor + other.minor, this.currency);
  }

  subtract(other: Money): Money {
    this.#sameCurrency(other);
    return new Money(this.minor - other.minor, this.currency);
  }

  negate(): Money {
    return new Money(-this.minor, this.currency);
  }

  equals(other: Money): boolean {
    return this.currency === other.currency && this.minor === other.minor;
  }

  /** Shares that add up exactly; leftover minor units go to the first shares (with the amount's sign). */
  split(parts: number): Money[] {
    if (!Number.isInteger(parts) || parts < 1) {
      throw new RangeError(`parts must be a positive integer, was ${parts}`);
    }
    const n = BigInt(parts);
    const base = this.minor / n; // bigint division truncates toward zero
    const rest = this.minor % n; // same sign as the amount
    const step = rest < 0n ? -1n : 1n;
    const extra = rest < 0n ? -rest : rest;
    return Array.from({ length: parts }, (_, i) =>
      new Money(BigInt(i) < extra ? base + step : base, this.currency),
    );
  }

  toDecimalString(): string {
    const digits = FRACTION_DIGITS[this.currency];
    const negative = this.minor < 0n;
    const units = (negative ? -this.minor : this.minor).toString().padStart(digits + 1, '0');
    const plain = digits === 0 ? units : `${units.slice(0, -digits)}.${units.slice(-digits)}`;
    return negative ? `-${plain}` : plain;
  }

  toString(): string {
    return `${this.toDecimalString()} ${this.currency}`;
  }

  #sameCurrency(other: Money): void {
    if (other.currency !== this.currency) {
      throw new Error(`Currency mismatch: ${this.currency} vs ${other.currency}`);
    }
  }
}
```

## 2. Measure with a unit
Cable length, paint volume, filament weight: a scaled integer (thousandths), a units table checked with
`satisfies` while keeping the literal keys, and adding only within one unit.

```ts
// ===== lending/measure.ts =====
export interface Unit {
  readonly symbol: string;
  readonly name: string;
}

export const UNITS = {
  m: { symbol: 'm', name: 'metre' },
  kg: { symbol: 'kg', name: 'kilogram' },
  l: { symbol: 'l', name: 'litre' },
} as const satisfies Record<string, Unit>;

export type UnitCode = keyof typeof UNITS;

const SCALE = 1000n;
const DECIMAL = /^(\d+)(?:[.,](\d{1,3}))?$/;

export class Measure {
  readonly thousandths: bigint;
  readonly unit: UnitCode;

  private constructor(thousandths: bigint, unit: UnitCode) {
    this.thousandths = thousandths;
    this.unit = unit;
  }

  static of(text: string, unit: UnitCode): Measure {
    const match = DECIMAL.exec(text.trim());
    const whole = match?.[1];
    if (whole === undefined) {
      throw new Error(`Not a measure in ${unit}: "${text}"`);
    }
    const fraction = (match?.[2] ?? '').padEnd(3, '0');
    return new Measure(BigInt(whole) * SCALE + BigInt(fraction), unit);
  }

  add(other: Measure): Measure {
    if (other.unit !== this.unit) {
      throw new Error(`Unit mismatch: ${this.unit} vs ${other.unit}`);
    }
    return new Measure(this.thousandths + other.thousandths, this.unit);
  }

  /** "12,5 m": decimal comma, trailing zeros trimmed. */
  toString(): string {
    const whole = this.thousandths / SCALE;
    const fraction = (this.thousandths % SCALE).toString().padStart(3, '0').replace(/0+$/, '');
    return `${whole}${fraction === '' ? '' : `,${fraction}`} ${UNITS[this.unit].symbol}`;
  }
}
```

## 3. Branded identifiers
Both ids are strings at runtime; the brand makes the compiler refuse a `MemberId` where a `ToolId` is expected. Build
them only at a validated boundary (API mapper, route param parser); tests may cast.

```ts
// ===== lending/ids.ts =====
export type ToolId = string & { readonly __brand: 'ToolId' };
export type MemberId = string & { readonly __brand: 'MemberId' };

export function parseToolId(raw: string): ToolId {
  if (!/^T-\d{3,}$/.test(raw)) throw new Error(`Invalid tool id: "${raw}"`);
  return raw as ToolId;
}

export function parseMemberId(raw: string): MemberId {
  if (!/^[msc]-\d{4}$/.test(raw)) throw new Error(`Invalid member id: "${raw}"`);
  return raw as MemberId;
}
```

## 4. Member variants
A discriminated union on `kind` with a shared base. `assertNever` turns a forgotten variant into a compile error in
every `switch` that uses it.

```ts
// ===== lending/assert-never.ts =====
export function assertNever(value: never): never {
  throw new Error(`Unhandled variant: ${JSON.stringify(value)}`);
}
```

```ts
// ===== lending/members.ts =====
import { assertNever } from './assert-never.js';
import type { MemberId } from './ids.js';

export type Licence = 'power-tools' | 'ladders' | 'welding';

interface MemberBase {
  readonly id: MemberId;
  readonly licences: readonly Licence[];
}

export interface Adult extends MemberBase {
  readonly kind: 'adult';
  readonly fullName: string;
}

export interface Junior extends MemberBase {
  readonly kind: 'junior';
  readonly fullName: string;
  readonly guardian: MemberId;
}

export interface Company extends MemberBase {
  readonly kind: 'company';
  readonly legalName: string;
  readonly parent?: MemberId;
}

export type Member = Adult | Junior | Company;

export function displayName(member: Member): string {
  switch (member.kind) {
    case 'adult':
      return member.fullName;
    case 'junior':
      return `${member.fullName} (junior)`;
    case 'company':
      return member.legalName;
    default:
      return assertNever(member);
  }
}

/** Juniors never use licensed tools on their own, whatever the data says. */
export function mayUse(member: Member, licence: Licence): boolean {
  return member.kind !== 'junior' && member.licences.includes(licence);
}
```

## 5. Loan period, read model, UI request state
The write model (the aggregate, section 9) protects rules; the read model is a flat, readonly projection made for one
screen. A check against the read model is only a hint for the UI.

```ts
// ===== lending/loan-period.ts =====
/** Half-open [from, to): a loan ending at 10:00 and one starting at 10:00 do not overlap. */
export interface LoanPeriod {
  readonly from: Date;
  readonly to: Date;
}

export function loanPeriod(from: Date, to: Date): LoanPeriod {
  if (!(from.getTime() < to.getTime())) {
    throw new RangeError(`A loan must end after it starts: ${from.toISOString()} / ${to.toISOString()}`);
  }
  return { from, to };
}

export function overlaps(a: LoanPeriod, b: LoanPeriod): boolean {
  return a.from.getTime() < b.to.getTime() && b.from.getTime() < a.to.getTime();
}
```

```ts
// ===== lending/shelf-view.ts =====
import type { ToolId } from './ids.js';
import { overlaps, type LoanPeriod } from './loan-period.js';
import type { LoanRefusal } from './lendable-tool.js';

/** Read model: what the booking screen shows, built by a query, never by loading aggregates. */
export interface ShelfView {
  readonly asOf: Date;
  readonly loans: ReadonlyMap<ToolId, readonly LoanPeriod[]>;
}

/**
 * A HINT for the UI (grey out a day, show "probably free"), not a decision:
 * the view may be stale, and only the backend's answer to the loan request counts.
 */
export function looksFree(view: ShelfView, tool: ToolId, wanted: LoanPeriod): boolean {
  return !(view.loans.get(tool) ?? []).some((booked) => overlaps(booked, wanted));
}

/**
 * State of one loan request in the UI; each state carries only the data it needs.
 * 'refused' is a business answer (show the reason), 'failed' is a technical one (offer a retry).
 */
export type LoanRequestState =
  | { readonly kind: 'idle' }
  | { readonly kind: 'sending'; readonly tool: ToolId }
  | { readonly kind: 'lent'; readonly tool: ToolId; readonly period: LoanPeriod }
  | { readonly kind: 'refused'; readonly tool: ToolId; readonly reason: LoanRefusal }
  | { readonly kind: 'failed'; readonly tool: ToolId; readonly message: string };
```

## 6. Data-driven field validation
The checkout form is described by data (often delivered by the API). Each constraint kind is one variant; `checkField`
returns a message for the user or `null`.

```ts
// ===== lending/field-rules.ts =====
import { assertNever } from './assert-never.js';

export type FieldRule =
  | { readonly kind: 'oneOf'; readonly values: readonly string[] }
  | { readonly kind: 'between'; readonly min: number; readonly max: number }
  | { readonly kind: 'dateWindow'; readonly earliest: string; readonly latest: string } // ISO yyyy-mm-dd
  | { readonly kind: 'pattern'; readonly source: string; readonly hint: string }
  | { readonly kind: 'free' };

export interface FieldSpec {
  readonly label: string;
  readonly required: boolean;
  readonly rule: FieldRule;
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

/** Empty input: a message if the field is required, otherwise valid. */
export function checkField(spec: FieldSpec, raw: string): string | null {
  const value = raw.trim();
  if (value === '') return spec.required ? `${spec.label} is required` : null;
  const rule = spec.rule;
  switch (rule.kind) {
    case 'oneOf':
      return rule.values.includes(value) ? null : `${spec.label}: choose one of ${rule.values.join(', ')}`;
    case 'between': {
      const n = Number(value.replace(',', '.'));
      return Number.isFinite(n) && n >= rule.min && n <= rule.max
        ? null
        : `${spec.label}: enter a number from ${rule.min} to ${rule.max}`;
    }
    case 'dateWindow':
      // ISO dates of equal length compare correctly as strings
      return ISO_DATE.test(value) && value >= rule.earliest && value <= rule.latest
        ? null
        : `${spec.label}: pick a date from ${rule.earliest} to ${rule.latest}`;
    case 'pattern':
      // anchored here, so a pattern from the API cannot match just a fragment
      return new RegExp(`^(?:${rule.source})$`).test(value) ? null : `${spec.label}: ${rule.hint}`;
    case 'free':
      return null;
    default:
      return assertNever(rule);
  }
}
```

## 7. Accessory compatibility rules
A drill can go out with accessories. Rules are data; the UI disables options and explains why, and lists unmet needs
before submit. The backend repeats the check and has the final word.

```ts
// ===== lending/accessory-rules.ts =====
import { assertNever } from './assert-never.js';

export type AccessoryRule =
  | { readonly kind: 'pickOne'; readonly options: readonly string[] }
  | { readonly kind: 'needsAnyOf'; readonly option: string; readonly anyOf: readonly string[] }
  | { readonly kind: 'clashesWith'; readonly option: string; readonly other: string };

export interface OptionState {
  readonly option: string;
  readonly disabled: boolean;
  readonly why: readonly string[];
}

/** UI hint: which unselected options to disable, with a reason for each. */
export function optionStates(
  rules: readonly AccessoryRule[],
  options: readonly string[],
  chosen: ReadonlySet<string>,
): OptionState[] {
  return options.map((option) => {
    const why: string[] = [];
    if (!chosen.has(option)) {
      for (const rule of rules) {
        switch (rule.kind) {
          case 'pickOne': {
            const other = rule.options.find((o) => o !== option && chosen.has(o));
            if (rule.options.includes(option) && other !== undefined) {
              why.push(`only one of ${rule.options.join(' / ')}: ${other} is selected`);
            }
            break;
          }
          case 'needsAnyOf':
            break; // a need never disables anything; see unmetNeeds
          case 'clashesWith':
            if (rule.option === option && chosen.has(rule.other)) why.push(`does not work with ${rule.other}`);
            if (rule.other === option && chosen.has(rule.option)) why.push(`does not work with ${rule.option}`);
            break;
          default:
            assertNever(rule);
        }
      }
    }
    return { option, disabled: why.length > 0, why };
  });
}

type NeedsAnyOf = Extract<AccessoryRule, { kind: 'needsAnyOf' }>;

export function unmetNeeds(rules: readonly AccessoryRule[], chosen: ReadonlySet<string>): string[] {
  return rules
    .filter((rule): rule is NeedsAnyOf => rule.kind === 'needsAnyOf')
    .filter((rule) => chosen.has(rule.option) && !rule.anyOf.some((o) => chosen.has(o)))
    .map((rule) => `${rule.option} needs one of: ${rule.anyOf.join(', ')}`);
}
```

## 8. Result
A business refusal is a value. `never` on the unused side lets `success(x)` and `failure(e)` fit any `Result`.

```ts
// ===== lending/result.ts =====
export type Result<E, T> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export const success = <T>(value: T): Result<never, T> => ({ ok: true, value });
export const failure = <E>(error: E): Result<E, never> => ({ ok: false, error });
```

## 9. Aggregate with a state machine and events
The state is a union keyed by `state`, so "on the shelf with a borrower" cannot be written down. Fields are `#private`;
`pullEvents()` drains the buffer with `splice(0)`. Timestamps in events are ISO strings, ready to serialise.

```ts
// ===== lending/lendable-tool.ts =====
import { assertNever } from './assert-never.js';
import type { MemberId, ToolId } from './ids.js';
import { failure, success, type Result } from './result.js';

export const LOAN_REFUSALS = ['on-loan', 'not-the-borrower', 'not-lent', 'withdrawn'] as const;
export type LoanRefusal = (typeof LOAN_REFUSALS)[number];

/** For data from outside (an API error body): narrows unknown to a known refusal. */
export function isLoanRefusal(value: unknown): value is LoanRefusal {
  return LOAN_REFUSALS.some((r) => r === value);
}

export type ShelfState =
  | { readonly state: 'on-shelf' }
  | { readonly state: 'lent'; readonly borrower: MemberId; readonly since: string }
  | { readonly state: 'withdrawn'; readonly by: MemberId; readonly reason: string };

export type ToolEvent =
  | { readonly type: 'ToolLent'; readonly tool: ToolId; readonly borrower: MemberId; readonly at: string }
  | { readonly type: 'ToolReturned'; readonly tool: ToolId; readonly borrower: MemberId; readonly at: string }
  | {
      readonly type: 'ToolWithdrawn';
      readonly tool: ToolId;
      readonly by: MemberId;
      readonly reason: string;
      readonly at: string;
    };

export class LendableTool {
  readonly id: ToolId;
  #state: ShelfState = { state: 'on-shelf' };
  #version = 0;
  #pending: ToolEvent[] = [];

  constructor(id: ToolId) {
    this.id = id;
  }

  get state(): ShelfState {
    return this.#state;
  }

  get version(): number {
    return this.#version;
  }

  lend(member: MemberId, at: Date): Result<LoanRefusal, ToolEvent> {
    const current = this.#state;
    switch (current.state) {
      case 'on-shelf':
        this.#state = { state: 'lent', borrower: member, since: at.toISOString() };
        return success(this.#record({ type: 'ToolLent', tool: this.id, borrower: member, at: at.toISOString() }));
      case 'lent':
        return failure('on-loan');
      case 'withdrawn':
        return failure('withdrawn');
      default:
        return assertNever(current);
    }
  }

  giveBack(member: MemberId, at: Date): Result<LoanRefusal, ToolEvent> {
    const current = this.#state;
    switch (current.state) {
      case 'lent':
        if (current.borrower !== member) return failure('not-the-borrower');
        this.#state = { state: 'on-shelf' };
        return success(this.#record({ type: 'ToolReturned', tool: this.id, borrower: member, at: at.toISOString() }));
      case 'on-shelf':
        return failure('not-lent');
      case 'withdrawn':
        return failure('withdrawn');
      default:
        return assertNever(current);
    }
  }

  /** A staff decision (broken, lost, sold): it cannot be refused. */
  withdraw(by: MemberId, reason: string, at: Date): Result<never, ToolEvent> {
    this.#state = { state: 'withdrawn', by, reason };
    return success(this.#record({ type: 'ToolWithdrawn', tool: this.id, by, reason, at: at.toISOString() }));
  }

  /** Events recorded since the last call; the buffer is empty afterwards. */
  pullEvents(): ToolEvent[] {
    return this.#pending.splice(0);
  }

  #record(event: ToolEvent): ToolEvent {
    this.#pending.push(event);
    this.#version += 1;
    return event;
  }
}
```

## 10. Repository port
The domain declares what it needs; HTTP, IndexedDB or in-memory implementations live outside `lending/` and are
injected.

```ts
// ===== lending/lendable-tools.ts =====
import type { ToolId } from './ids.js';
import type { LendableTool } from './lendable-tool.js';

export interface LendableTools {
  load(id: ToolId): Promise<LendableTool | undefined>;
  /** Rejects when the stored version differs from expectedVersion (optimistic locking). */
  save(tool: LendableTool, expectedVersion: number): Promise<void>;
}
```

## 11. Barrel and compiler settings
The barrel is the module's public API; code outside imports `…/lending` (bundler resolution) or
`./lending/index.js` (Node resolution).

```ts
// ===== lending/index.ts =====
export * from './accessory-rules.js';
export * from './assert-never.js';
export * from './field-rules.js';
export * from './ids.js';
export * from './lendable-tool.js';
export * from './lendable-tools.js';
export * from './loan-period.js';
export * from './measure.js';
export * from './members.js';
export * from './money.js';
export * from './result.js';
export * from './shelf-view.js';
```

`tsconfig.json` used for the check (next to a `package.json` with `"type": "module"`, and `@types/node`
installed for `console` in the test). In 6.0+ `rootDir` no longer
defaults to the common folder of the inputs and `types` defaults to none, so both are written out:

```json
{
  "compilerOptions": {
    "target": "es2022",
    "module": "nodenext",
    "rootDir": ".",
    "outDir": "dist",
    "types": ["node"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "erasableSyntaxOnly": true,
    "verbatimModuleSyntax": true
  },
  "include": ["lending", "lending.test.ts"]
}
```

## 12. Tests: edge cases
No framework: `eq` compares JSON, so only plain data is compared (Money through `toDecimalString()`, since `bigint`
does not serialise). Run with `tsc -p . && node dist/lending.test.js`.

```ts
// ===== lending.test.ts =====
import {
  LendableTool, Measure, Money, checkField, displayName, isLoanRefusal, loanPeriod, looksFree, mayUse, optionStates,
  overlaps, unmetNeeds,
  type AccessoryRule, type Member, type MemberId, type ShelfView, type ToolId,
} from './lending/index.js';

function eq(actual: unknown, expected: unknown, what: string): void {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) throw new Error(`${what}: expected ${e} but was ${a}`);
}

function throws(action: () => unknown, what: string): void {
  try {
    action();
  } catch {
    return;
  }
  throw new Error(`${what}: expected an error`);
}

const amounts = (xs: readonly Money[]): string[] => xs.map((m) => m.toDecimalString());

// Money
eq(Money.of('12,50', 'PLN').add(Money.of('0.75', 'PLN')).toDecimalString(), '13.25', 'comma and point');
eq(Money.of('-3.1', 'EUR').toDecimalString(), '-3.10', 'negative parse');
eq(Money.of('0.10', 'EUR').add(Money.of('0.20', 'EUR')).equals(Money.of('0.30', 'EUR')), true, 'no float error');
eq(amounts(Money.of('100', 'PLN').split(3)), ['33.34', '33.33', '33.33'], 'split 100 into 3');
eq(amounts(Money.of('-1', 'PLN').split(3)), ['-0.34', '-0.33', '-0.33'], 'split a negative amount');
eq(Money.of('1500', 'JPY').toString(), '1500 JPY', 'zero-decimal currency');
throws(() => Money.of('1.5', 'JPY'), 'too many decimals for JPY');
throws(() => Money.of('12.5.0', 'PLN'), 'not an amount');
throws(() => Money.of('1', 'PLN').add(Money.of('1', 'EUR')), 'currency mismatch');

// Measure
eq(Measure.of('10', 'm').add(Measure.of('2,5', 'm')).toString(), '12,5 m', 'measure addition');
throws(() => Measure.of('1', 'kg').add(Measure.of('1', 'l')), 'unit mismatch');

// Variants
const ola = 'm-0042' as MemberId;
const kuba = 'm-0107' as MemberId;
const staff = 's-0001' as MemberId;
const members: Member[] = [
  { kind: 'adult', id: ola, fullName: 'Ola Wrona', licences: ['power-tools'] },
  { kind: 'junior', id: 'm-0108' as MemberId, fullName: 'Tymek Wrona', guardian: ola, licences: ['power-tools'] },
  { kind: 'company', id: 'c-0007' as MemberId, legalName: 'Dach-Serwis sp. z o.o.', licences: ['ladders'] },
];
eq(members.map(displayName), ['Ola Wrona', 'Tymek Wrona (junior)', 'Dach-Serwis sp. z o.o.'], 'display names');
eq(members.map((m) => mayUse(m, 'power-tools')), [true, false, false], 'licence check');

// Loan period and read model
const at = (hhmm: string): Date => new Date(`2026-11-20T${hhmm}:00Z`);
eq(overlaps(loanPeriod(at('09:00'), at('11:00')), loanPeriod(at('10:00'), at('12:00'))), true, 'overlap');
eq(overlaps(loanPeriod(at('09:00'), at('10:00')), loanPeriod(at('10:00'), at('11:00'))), false, 'touching');
throws(() => loanPeriod(at('10:00'), at('10:00')), 'empty period');
const drillId = 'T-217' as ToolId;
const view: ShelfView = { asOf: at('08:00'), loans: new Map([[drillId, [loanPeriod(at('09:00'), at('10:00'))]]]) };
eq(looksFree(view, drillId, loanPeriod(at('10:00'), at('12:00'))), true, 'hint: free after the loan');
eq(looksFree(view, drillId, loanPeriod(at('09:30'), at('12:00'))), false, 'hint: clashes with the loan');

// Field validation
const voltage = { label: 'Battery', required: true, rule: { kind: 'oneOf', values: ['12V', '18V'] } } as const;
eq(checkField(voltage, '24V'), 'Battery: choose one of 12V, 18V', 'value outside the list');
eq(checkField({ label: 'Days', required: true, rule: { kind: 'between', min: 1, max: 14 } }, '7'), null, 'range ok');
eq(checkField({ label: 'Notes', required: false, rule: { kind: 'free' } }, '  '), null, 'optional and empty');
eq(checkField(voltage, ''), 'Battery is required', 'required and empty');
const postcode = { label: 'Postcode', required: true, rule: { kind: 'pattern', source: '\\d{2}-\\d{3}', hint: 'use 00-000' } } as const;
eq(checkField(postcode, '31-1234'), 'Postcode: use 00-000', 'pattern is anchored');

// Accessory rules
const rules: AccessoryRule[] = [
  { kind: 'pickOne', options: ['battery-2Ah', 'battery-5Ah'] },
  { kind: 'needsAnyOf', option: 'charger-fast', anyOf: ['battery-2Ah', 'battery-5Ah'] },
  { kind: 'clashesWith', option: 'masonry-bits', other: 'wood-bits' },
];
const options = ['battery-2Ah', 'battery-5Ah', 'charger-fast', 'masonry-bits', 'wood-bits'];
eq(
  optionStates(rules, options, new Set(['battery-5Ah', 'wood-bits'])).filter((s) => s.disabled),
  [
    { option: 'battery-2Ah', disabled: true, why: ['only one of battery-2Ah / battery-5Ah: battery-5Ah is selected'] },
    { option: 'masonry-bits', disabled: true, why: ['does not work with wood-bits'] },
  ],
  'disabled options with reasons',
);
eq(unmetNeeds(rules, new Set(['charger-fast'])), ['charger-fast needs one of: battery-2Ah, battery-5Ah'], 'unmet need');

// Aggregate: the full lending sequence
const drill = new LendableTool(drillId);
eq(drill.lend(ola, at('09:00')), { ok: true, value: { type: 'ToolLent', tool: drillId, borrower: ola, at: '2026-11-20T09:00:00.000Z' } }, 'first loan');
eq(drill.lend(kuba, at('10:00')), { ok: false, error: 'on-loan' }, 'rival refused');
eq(drill.giveBack(kuba, at('10:00')), { ok: false, error: 'not-the-borrower' }, 'stranger cannot return');
eq(drill.giveBack(ola, at('10:00')).ok, true, 'return');
eq(drill.giveBack(ola, at('10:00')), { ok: false, error: 'not-lent' }, 'return twice');
eq(drill.withdraw(staff, 'worn chuck', at('11:00')).ok, true, 'withdraw');
eq(drill.lend(kuba, at('11:00')), { ok: false, error: 'withdrawn' }, 'lend after withdrawal');
eq(drill.lend(staff, at('11:00')), { ok: false, error: 'withdrawn' }, 'even staff cannot lend it');
eq(drill.version, 3, 'version counts recorded events');
eq(drill.pullEvents().map((e) => e.type), ['ToolLent', 'ToolReturned', 'ToolWithdrawn'], 'events in order');
eq(drill.pullEvents(), [], 'second pull is empty');
eq([isLoanRefusal('on-loan'), isLoanRefusal('lost'), isLoanRefusal(409)], [true, false, false], 'refusal guard');

console.log('OK: tool-lending domain tests passed (TypeScript)');
```
