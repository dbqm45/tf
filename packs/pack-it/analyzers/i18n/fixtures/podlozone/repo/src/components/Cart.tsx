export function Cart({ total, order }: { total: number; order: { date: Date } }) {
  return (
    <section>
      <h2>Koszyk</h2>
      <input placeholder="Kod rabatowy" />
      <p>{total.toFixed(2)} zł</p>
      <p>{order.date.toLocaleDateString()}</p>
    </section>
  );
}
