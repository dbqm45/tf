# The recipe for collecting evidence (for the `scout` subagent)

Input: the frame (`*.frame.md`) — the membership of A and B, the local rules of the stack. Output: raw hits, **without naming kinds or assessments**.

1. **The public surface** of A and B: exported types, functions, endpoints, event topics; also ports implemented
   on the other side and fields injected under a name different from the type.
2. **A symbol search** for each item of A's surface in B's code and the other way round — as a whole word, within the other side's scope,
   skipping import lines. Record the **exact patterns** of the search (the next run is to give the same result).
3. **A dynamic search** (separately, structurally): transaction markers that cover calls to the other side; writes to the stores
   of both sides in one flow; shared instances (DI registrations, singletons, static fields); timeouts, retries,
   schedules; a call order required by the other side.
4. Reject hits that do not cross the boundary (internal uses).
5. Return: the list of searches performed; `code:path:line` rows + a fragment of ≤ 1 line; separately the number of hits in tests;
   unused public surface.
Read only the minimum around a hit (a few lines), not whole files.
