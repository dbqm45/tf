export function Card({ id, title, open }) {
  return (
    <div
      className="card"
      role="button"
      tabIndex={0}
      onClick={() => open(id)}
      onKeyDown={(e) => e.key === "Enter" && open(id)}
    >
      <h3>{title}</h3>
      <button onClick={() => open(id)}>Otwórz</button>
    </div>
  );
}
