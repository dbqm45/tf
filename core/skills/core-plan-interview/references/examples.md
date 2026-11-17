# Examples: plan interview

## 1. CSV export of orders
**Situation:** "I want to add a CSV export of orders in the admin panel. Grill me before you start".

**How:**
1. Tree: permissions, personal data and filters are independent of each other; the export register depends on
   personal data, the file size on the filters, and how the file is delivered on the size.
2. You check facts yourself: `scout` finds that the panel has the roles `admin` and `support`, and the orders table
   has about 2 million rows. You do not ask about that.
3. Frontier of the first round: only decisions without unsettled preconditions (permissions, personal data,
   filters). The question about how the file is delivered waits — it depends on the answer about filters (file size).

**Result (round 1):**
```
**Q1 — Who can export**: a) only admin, b) admin and support
→ Recommendation: a — the export holds customer data; support can get it later.

**Q2 — Personal data in the file**: a) full (name, e-mail, address), b) no personal data, c) selectable at export
→ Recommendation: b — enough for reports, and it creates no copy of personal data outside the system.

**Q3 — Filters**: a) date range, b) date range and status, c) all filters from the order list
→ Recommendation: b — covers the described case, and does not tie the export to every change in the list.
```
The human: `P1: a, P2: c, P3: b`. The answers unlock new questions for round 2: the export register (follows from
Q2: c) and how the file is delivered when the date filter covers all 2 million rows (follows from Q3).

## 2. Summary and confirmation
**Situation:** After three rounds (13 questions) the frontier is empty.

**How:**
1. Summary: decisions, assumptions, what is out of scope.
2. The question about shared understanding; without "yes" you do not implement.
3. Decisions recorded to `decisions.md`; the decision to deliver files in the background meets the ADR threshold →
   an ADR proposal.

**Result:**
```
Decisions: export only for admin; personal data selectable, every export with personal data in the register;
filters: dates and status; above 50 thousand rows the file is generated in the background, link by e-mail.
Assumptions: CSV format UTF-8 with the separator ";" [to be confirmed by the reporting team].
Out of scope: export to XLSX, a schedule of automatic exports.
Is that how we understand it?
```

## 3. The human is unavailable
**Situation:** The human leaves a note: "I'm away until Friday, prepare a plan for migrating login to OIDC".

**How:**
1. You gather facts from the repo as usual.
2. You do not settle decisions silently: you take the recommendations as explicit **assumptions**.
3. You do not implement — the plan waits for confirmation after they are back.

**Result:**
```
Assumptions (to confirm, nothing implemented):
A1 — identity provider: the company's current Keycloak [recommendation Q1]
A2 — old sessions: expire naturally, no forced logout [recommendation Q2]
A3 — accounts without an e-mail: manual linking by support [recommendation Q3]
After you are back: confirm or change A1–A3; A1 changes the shape of the further questions.
```
