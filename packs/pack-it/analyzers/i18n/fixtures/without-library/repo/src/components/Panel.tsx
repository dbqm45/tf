export function Panel({ at }: { at: Date }) {
  return (
    <section>
      <h2>Panel administracyjny</h2>
      <time>{at.toLocaleDateString()}</time>
    </section>
  );
}
