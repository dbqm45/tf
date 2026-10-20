export type Money = number; // grosze

export function discountRate(quantity: number): number {
  if (quantity >= 50) return 0.10;
  if (quantity > 10) return 0.05;
  return 0;
}

export function orderTotal(unitPrice: Money, quantity: number): Money {
  if (quantity < 1) throw new RangeError('Quantity must be at least 1');
  const gross = unitPrice * quantity;
  return Math.round(gross * (1 - discountRate(quantity)));
}
