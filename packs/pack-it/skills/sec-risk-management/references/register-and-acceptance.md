# The risk register and risk acceptance

Contents: 1. Register fields · 2. A row template · 3. The acceptance record · 4. Authority levels · 5. Expiry and review

## 1. Register fields
ID · title · description (cause → event → consequence) · asset/process · category (data, availability, vendor, people,
compliance) · source (threat model, audit, incident, vendor) · risk owner · likelihood and impact
(inherent) · inherent score · existing controls · treatment option · plan (tasks, owners, deadlines) ·
residual likelihood and impact · residual score · status (open, in treatment, retained, closed) ·
the date of the last and the next review · links (the control ID in the matrix, ADR, ticket).

## 2. A row template [example]
| ID | Description | Owner | Inh. | Option | Plan | Res. | Status | Next review |
|---|---|---|---|---|---|---|---|---|
| R-017 | Takeover of a partner account in a portal without MFA → a leak of orders | sales director | 16 | modification + temporary retention | MFA by 2027-03-31 (Z-212) | 9 | in treatment | 2027-01-15 |

Rules: one owner (a person, not a team); a risk without a plan and a deadline is not "in treatment"; closing a risk
requires evidence (a test, a scan, a contract), not a declaration.

## 3. The risk acceptance record
Header: `Risk acceptance R-017` · version · date.
- The risk (description and inherent/residual score, FAIR: the annual loss range, if calculated).
- Why we are not treating it fully now (cost, deadline, dependency) and **the alternatives considered**.
- Compensating controls and their evidence.
- Revocation conditions (an incident, a change of scope, a new vulnerability, a change of appetite).
- The accepting risk owner (name, role, authority), the decision date, **valid until** (a date), the reviewer.
- Consulted and informed (CISO, lawyer, DPO, finance).
- The signature of the acceptor. Recording and identifying the signature per the company's procedures; the agent prepares a draft, it does not sign.

## 4. Authority to accept [example, set by the board in the criteria]
| Residual score | Who accepts | Max. period |
|---|---|---|
| low | team manager | 24 months |
| medium | area director | 12 months |
| high | board member + CISO informed | 6 months |
| critical | we do not accept; treatment or avoidance, exceptionally the board | — |
Separation rule: the person who manages the control or requests the exception is not the only acceptor.

## 5. Expiry and review
A calendar of expiring acceptances (an alert 30 days before). After expiry the risk returns to treatment; an extension
is a new decision with current data, not an automatic entry. The KRI "overdue acceptances" reported quarterly.
Accepting an exception to the security policy is the same record (sec-governance-compliance: exceptions in the matrix).
