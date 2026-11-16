export function Card({ id, title, open }) {
  return (
    <div className="card" onClick={() => open(id)}>
      <h3>{title}</h3>
    </div>
  );
}
