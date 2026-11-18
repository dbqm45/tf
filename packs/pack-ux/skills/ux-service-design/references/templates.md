# Service artifact templates

## Blueprint — table
As in the SKILL.md example: the columns are steps in time, the rows are lanes. Every failure point has an ID (P1…), evidence
(a number, a quote) and an owner. The current and the target state in separate sections.

## Blueprint — Mermaid
```mermaid
flowchart TB
  subgraph Customer
    K1[Fills in the return form] --> K2[Packs and sends the parcel] --> K3[Waits for the refund]
  end
  subgraph Frontstage
    F1[Hotline and chat]
  end
  subgraph Backstage
    B1[Re-entry into the ERP] --> B2[The warehouse scans the parcel] --> B3[Accounting approval]
  end
  subgraph Support
    S1[ERP] ; S2[Courier system] ; S3[Bank]
  end
  K1 -.-> B1
  K3 -.-> F1
  B3 --> S3
```
Describe the lines of interaction, visibility and internal interaction in footnotes or as separate separator nodes; Mermaid has no
native lanes, so keep the order of the subgraphs.

## Journey map
| Stage | Customer actions | Channel | Thoughts | Emotion (−2…+2) | Pain point and evidence |
|---|---|---|---|---|---|
The target map has the same stages, so that they can be compared.

## Stakeholder map
| Party | Role in the service | Need | Influence (H/M/L) | Who listens to them |
|---|---|---|---|---|

## Touchpoint inventory
| Touchpoint | Channel | Owner | System | Data shared with | Consistency (the same promise, language, data) | Gap |
|---|---|---|---|---|---|---|

## Omnichannel — consistency test
For one customer case go through all channels: does a channel change require repeating data, is the
answer about the state of the matter the same, does the employee see the history from other channels.
