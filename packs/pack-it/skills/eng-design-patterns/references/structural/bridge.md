# Bridge

> **Contents:** Problem · Solution and participants · When to use · Costs · Relations · Idiomatic form in TS · Example (TS) · When NOT to use / pitfalls

Category: structural. The essence: separate two **independent dimensions of variation** into two hierarchies connected by composition,
instead of multiplying subclasses for every combination.

## Problem
Reports (occupancy, revenue, complaints) have to be generated in several formats (CSV, Markdown, PDF). Inheritance gives
`OccupancyCsvReport`, `OccupancyPdfReport`, `RevenueCsvReport`… — the number of classes is the product of reports and formats, and changing
the CSV format requires edits in many classes.

## Solution and participants
- **Abstraction** — the high-level logic (`Report`), holds a reference to the implementation.
- **Refined abstractions** — variants of the logic (`OccupancyReport`, `RevenueReport`).
- **Implementation interface** — simple, primitive operations (`heading()`, `row()`).
- **Concrete implementations** — the details of the technology/platform (`CsvWriter`, `MarkdownWriter`).
- **Client** — connects an abstraction + implementation pair (usually in the constructor or through DI).

## When to use
- A class grows in two (or more) directions independently: logic × platform, data × format, UI × system.
- A monolithic class supporting many technology variants (e.g. several databases) has to be split.
- The implementation has to be swapped at runtime.

## Costs
More types and indirection; with a cohesive, rarely changing class it only obscures the code.

## Relations
- **Adapter** — a similar structure, but reactive (patches an incompatibility); a Bridge is a design decision made up front.
- **Strategy** / **State** — also composition + delegation, but one interchangeable algorithm/state, not two hierarchies.
- **Abstract Factory** can create matching abstraction–implementation pairs.
- Ports and adapters in hexagonal architecture are in practice a bridge between the domain and the infrastructure.

## Idiomatic form in TS
The implementation as an `interface` (or a function type), the abstraction as a class or a function taking the implementation.
Often **higher-order functions** are enough: `renderOccupancy(writer, data)`.

## Example (TS)
```ts
/** Implementation: the output format. */
interface ReportWriter {
  heading(text: string): void;
  row(cells: readonly string[]): void;
  result(): string;
}

class CsvWriter implements ReportWriter {
  #lines: string[] = [];
  heading(text: string): void {
    this.#lines.push(`# ${text}`);
  }
  row(cells: readonly string[]): void {
    this.#lines.push(cells.map((c) => `"${c.replaceAll('"', '""')}"`).join(','));
  }
  result(): string {
    return this.#lines.join('\n');
  }
}

class MarkdownWriter implements ReportWriter {
  #lines: string[] = [];
  heading(text: string): void {
    this.#lines.push(`## ${text}`, '');
  }
  row(cells: readonly string[]): void {
    this.#lines.push(`| ${cells.join(' | ')} |`);
  }
  result(): string {
    return this.#lines.join('\n');
  }
}

/** Abstraction: what we report. */
abstract class Report {
  protected readonly writer: ReportWriter;
  constructor(writer: ReportWriter) {
    this.writer = writer;
  }
  abstract render(): string;
}

class OccupancyReport extends Report {
  readonly #occupancy: ReadonlyMap<string, number>;
  constructor(writer: ReportWriter, occupancy: ReadonlyMap<string, number>) {
    super(writer);
    this.#occupancy = occupancy;
  }
  render(): string {
    this.writer.heading('Room occupancy');
    for (const [room, ratio] of this.#occupancy) this.writer.row([room, `${Math.round(ratio * 100)}%`]);
    return this.writer.result();
  }
}

class RevenueReport extends Report {
  readonly #revenueCents: number;
  constructor(writer: ReportWriter, revenueCents: number) {
    super(writer);
    this.#revenueCents = revenueCents;
  }
  render(): string {
    this.writer.heading('Revenue');
    this.writer.row(['total', (this.#revenueCents / 100).toFixed(2)]);
    return this.writer.result();
  }
}

const occupancy = new Map([['A1', 0.82], ['B2', 0.4]]);
console.log(new OccupancyReport(new MarkdownWriter(), occupancy).render());
console.log(new RevenueReport(new CsvWriter(), 1_250_000).render());
```

## When NOT to use / pitfalls
- **Only one dimension grows** — ordinary composition or one hierarchy is enough; do not build a bridge "in case a second
  dimension appears one day" (YAGNI — eng-design-principles).
- The signal to apply it: class names that are the product of two traits (`CsvOccupancy`, `PdfOccupancy`, `CsvRevenue`…)
  and a really growing number of combinations on both sides.
- The implementation interface is to be **low-level** and stable; if it grows by methods for a specific abstraction, the boundary is drawn
  badly.
