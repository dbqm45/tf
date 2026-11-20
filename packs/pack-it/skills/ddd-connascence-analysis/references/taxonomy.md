# Kinds and the rules for breaking into rows

| Rank | Kind | Contract | Example across the boundary |
|---|---|---|---|
| 1 | name | both sides use the same name | a call to `availability.block(...)` |
| 2 | type | both sides agree on the type | a DTO/event passed across the boundary |
| 3 | meaning | a shared interpretation of a value | `status == 3` means "cancelled" on both sides |
| 4 | position | the order of elements matters | `(from, to)` — two dates of the same type next to each other |
| 5 | algorithm | the same algorithm on both sides | the same way of rounding amounts / hash / normalization |
| 6 | execution order | calls must go in a specific order | first `reserve`, then `confirm` in the other module |
| 7 | timing | the result depends on the execution time | a timeout, a retry window, "within 5 s" |
| 8 | value | values in two places must agree | the number of seats in A and the sum of reservations in B |
| 9 | identity | both sides must have **the same instance** | a shared object/cache/connection through DI |

## Rules for breaking into rows
- A transaction covering both sides → **two rows**: execution order + value (for the stores that must agree).
- A type crossing the boundary → **one** "type" row per seam (not per use); the uses raise the degree.
- A "meaning" row requires **two** pieces of evidence: where the meaning arises and where the other side relies on it.
- A "position" row only for adjacent parameters of the same type (otherwise the compiler guards the type).
- Two equal copies of a value are "meaning" (or "value", when they must be synchronized at runtime), not "identity".
- Types from a **shared kernel** approved by the human give no rows — record that in the frame.

## Network seams (HTTP, events, files)
Name = path/topic/field name; type = schema; meaning = codes/enums in fields; position = CSV columns without a header;
execution order = the required sequence of calls/events; timing = timeouts, TTL, retry windows; value = data duplicated in both systems.
