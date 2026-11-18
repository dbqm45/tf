import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { orderTotal } from './pricing';

// Oracle: docs/project/05-plan/test-plan.md — table TC-001..TC-014 (values computed by hand,
// independently of the implementation). The tests do not copy the formula from pricing.ts.

describe('H1: order line pricing — quantity discount', () => {
  it.each([
    { id: 'TC-001', qty: 1, price: 1999, expected: 1999 },
    { id: 'TC-002', qty: 9, price: 1999, expected: 17991 },
    { id: 'TC-004', qty: 11, price: 1999, expected: 20890 },
    { id: 'TC-005', qty: 49, price: 1999, expected: 93053 },
    { id: 'TC-006', qty: 50, price: 1999, expected: 89955 },
    { id: 'TC-007', qty: 51, price: 1999, expected: 91754 },
    { id: 'TC-009', qty: 51, price: 15, expected: 689 },
    { id: 'TC-014', qty: 100, price: 1999, expected: 179910 },
  ])('$id: qty=$qty, price=$price gr -> $expected gr', ({ qty, price, expected }) => {
    expect(orderTotal(price, qty)).toBe(expected);
  });

  // DEFECT (docs/project/07-review/defects.md): discountRate() uses the threshold `quantity > 10` instead of
  // `quantity >= 10` (H1-AC2/AC3 say "from 10 units inclusive"). For qty=10 the code applies no discount.
  // it.fails documents the expected (correct) result from the specification, leaving a trace of the defect without turning the wrong value green.
  it.fails('TC-003 (DEFECT-01): qty=10, price=1999 gr -> 18991 gr (5% discount from 10 units inclusive)', () => {
    expect(orderTotal(1999, 10)).toBe(18991);
  });

  it.fails('TC-008 (DEFECT-01): qty=10, price=11 gr -> 105 gr (5% discount from 10 units inclusive)', () => {
    expect(orderTotal(11, 10)).toBe(105);
  });

  describe('H1-AC4: quantity validation (integer, >=1)', () => {
    it.each([
      { id: 'TC-010', qty: 0 },
      { id: 'TC-011', qty: -1 },
    ])('$id: qty=$qty -> pricing rejected (validation error)', ({ qty }) => {
      expect(() => orderTotal(1999, qty)).toThrow();
    });

    // DEFECT (docs/project/07-review/defects.md): orderTotal() does not check that the quantity is an integer —
    // it rejects only qty<1. Non-integer quantities pass without an error, contrary to AC4.
    it.fails('TC-012 (DEFECT-02): qty=2.5, price=1999 gr -> pricing rejected (validation error)', () => {
      expect(() => orderTotal(1999, 2.5)).toThrow();
    });

    it.fails('TC-013 (DEFECT-02): qty=9.999999, price=1999 gr -> pricing rejected, NOT treated as qty=10', () => {
      expect(() => orderTotal(1999, 9.999999)).toThrow();
    });
  });

  // Addition: invariant properties (fast-check) for money calculations — the oracle is
  // a business property ("a discount cannot increase the price", "the price is non-negative"), not the production code.
  describe('properties (addition to the plan)', () => {
    it('the result never exceeds the base value (without a discount)', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 1, max: 100000 }),
          fc.integer({ min: 1, max: 1000 }),
          (price, qty) => {
            expect(orderTotal(price, qty)).toBeLessThanOrEqual(price * qty);
          },
        ),
      );
    });

    it('the result is always non-negative', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 100000 }),
          fc.integer({ min: 1, max: 1000 }),
          (price, qty) => {
            expect(orderTotal(price, qty)).toBeGreaterThanOrEqual(0);
          },
        ),
      );
    });
  });
});
