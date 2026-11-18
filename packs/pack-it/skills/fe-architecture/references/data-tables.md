# Data tables

A table in a business application is usually the most used screen: a list of orders, customers, tickets. Typical
problems come from treating it like an ordinary component rather than a view onto a server-side
data set.

## 1. State in the URL
- Filters, sorting, the page (or cursor) and the page size are kept in the URL parameters, e.g.
  `?status=new&sort=-created_at&cursor=…`. After a refresh, going back and sending a link, the view is the same.
- Values in the URL are user input: you validate them with a schema (an unknown sort field → the default),
  you do not insert them directly into the query.
- A filter change replaces the history entry (`replace`), it does not add a new one on every keystroke; the search field
  with a delay (`performance/debounce.md`).
- Row selection and expanded details are local state. You do not keep them in the URL.

## 2. Server-side data
- Filtering, sorting and pagination are server-side when the set is not small and fixed. Pulling 100 thousand
  records into the browser means a slow start and stale data. The API contract (cursor, the list of allowed fields):
  be-api-design (pack-it), `.claude/skills/be-api-design/references/http-in-practice.md` §4.
- You keep server data in a layer with a query cache (e.g. TanStack Query, SWR, RTK Query). The query key is
  the parameters from the URL, so going back to the previous filter is instant.
- Every view state: loading (without layout jumps), an error with a retry, empty after a filter ("no results for…
  — clear the filters") and empty in general (`resilience/loading-state.md`).

## 3. Performance with many rows
- Pagination or "load more" is the first choice. Virtualization (rendering only the visible rows,
  e.g. TanStack Virtual, react-window) is for lists that must be long: logs, an import preview.
- With virtualization: a fixed or measured row height, and scrolling and keyboard focus work on
  the whole list. The browser's find-in-page (Ctrl+F) does not see rows that are not in the DOM, so provide
  your own search.
- Heavy cells (charts, images) are rendered lazily (`performance/lazy-loading.md`).

## 4. Selection and bulk operations
- "Select all" has two levels: the rows on this page and **all matching the filter**, with a count
  ("50 selected on this page — select all 12,413 matching").
- An operation on "all matching" sends the **filter** to the server, not a list of IDs from the browser. The server computes
  the set, checks the permissions for every record and performs the operation in the background. Pattern: be-business-app-patterns
  (pack-it), `.claude/skills/be-business-app-patterns/references/bulk-operations.md`.
- After a filter change, the "all matching" selection is cleared: a different filter is a different set.

## 5. Command palette and shortcuts
- With many actions and screens: a command palette (Ctrl/Cmd+K) with a search of actions and records. Destructive actions
  require confirmation here too.
- Keyboard shortcuts in the table (arrows, space to select) must be possible to turn off and must not collide
  with a screen reader (WCAG 2.2 SC 2.1.4).

## 6. Accessibility
- A real table (`<table>`, `<thead>`, `<th scope="col">`) instead of a grid of `div`s. You build a grid with the `grid` role
  and arrow-key navigation only when the cells are editable and it is well thought out.
- A sortable column: a button in the header and `aria-sort="ascending" | "descending"` on the `<th>` of the currently
  sorted column (the others without the attribute or `none`).
- A change of results after filtering announced through an `aria-live="polite"` region ("12,413 results"), without moving
  focus.
- A row selection checkbox has a label with the record's name ("Select order 1042"), not an empty one.
- On a narrow screen: horizontal scrolling with the first column visible, or a card view. You do not hide columns without
  telling the user.

## Notes (state in 2026)
- The libraries in the examples are a typical choice in React. In another framework the rules are the same, only the
  tool changes (Angular CDK Table and Virtual Scroll, TanStack Table for Vue and Solid). You check versions in the project
  (core-grounding).
- `aria-sort` and table roles: WAI-ARIA 1.2 and the APG patterns (Table, Sortable Table) [unverified in the source 2026-11-10].
