import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { orderTotal } from './pricing';

// Wyrocznia: docs/project/05-plan/test-plan.md — tabela TC-001..TC-014 (wartości policzone ręcznie,
// niezależnie od implementacji). Testy nie powielają formuły z pricing.ts.

describe('H1: wycena pozycji zamówienia — rabat ilościowy', () => {
  it.each([
    { id: 'TC-001', qty: 1, price: 1999, expected: 1999 },
    { id: 'TC-002', qty: 9, price: 1999, expected: 17991 },
    { id: 'TC-004', qty: 11, price: 1999, expected: 20890 },
    { id: 'TC-005', qty: 49, price: 1999, expected: 93053 },
    { id: 'TC-006', qty: 50, price: 1999, expected: 89955 },
    { id: 'TC-007', qty: 51, price: 1999, expected: 91754 },
    { id: 'TC-009', qty: 51, price: 15, expected: 689 },
    { id: 'TC-014', qty: 100, price: 1999, expected: 179910 },
  ])('$id: qty=$qty, cena=$price gr -> $expected gr', ({ qty, price, expected }) => {
    expect(orderTotal(price, qty)).toBe(expected);
  });

  // DEFEKT (docs/project/07-review/defekty.md): discountRate() progiem `quantity > 10` zamiast
  // `quantity >= 10` (H1-AC2/AC3 mówią "od 10 sztuk włącznie"). Dla qty=10 kod nie nalicza rabatu.
  // it.fails dokumentuje oczekiwany (poprawny) wynik ze specyfikacji, zostawiając ślad defektu bez zazieleniania błędnej wartości.
  it.fails('TC-003 (DEFEKT-01): qty=10, cena=1999 gr -> 18991 gr (5% rabatu od 10 szt. włącznie)', () => {
    expect(orderTotal(1999, 10)).toBe(18991);
  });

  it.fails('TC-008 (DEFEKT-01): qty=10, cena=11 gr -> 105 gr (5% rabatu od 10 szt. włącznie)', () => {
    expect(orderTotal(11, 10)).toBe(105);
  });

  describe('H1-AC4: walidacja ilości (całkowita, >=1)', () => {
    it.each([
      { id: 'TC-010', qty: 0 },
      { id: 'TC-011', qty: -1 },
    ])('$id: qty=$qty -> wycena odrzucona (błąd walidacji)', ({ qty }) => {
      expect(() => orderTotal(1999, qty)).toThrow();
    });

    // DEFEKT (docs/project/07-review/defekty.md): orderTotal() nie waliduje całkowitości ilości —
    // odrzuca tylko qty<1. Ilości niecałkowite przechodzą bez błędu, wbrew AC4.
    it.fails('TC-012 (DEFEKT-02): qty=2.5, cena=1999 gr -> wycena odrzucona (błąd walidacji)', () => {
      expect(() => orderTotal(1999, 2.5)).toThrow();
    });

    it.fails('TC-013 (DEFEKT-02): qty=9.999999, cena=1999 gr -> wycena odrzucona, NIE traktowane jak qty=10', () => {
      expect(() => orderTotal(1999, 9.999999)).toThrow();
    });
  });

  // Uzupełnienie: właściwości niezmienne (fast-check) dla obliczeń pieniężnych — wyrocznią jest
  // właściwość biznesowa ("rabat nie może zwiększyć ceny", "wycena nieujemna"), nie kod produkcyjny.
  describe('właściwości (uzupełnienie planu)', () => {
    it('wynik nigdy nie przekracza wartości bazowej (bez rabatu)', () => {
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

    it('wynik jest zawsze nieujemny', () => {
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
