# Data governance: owner, classes, inventory

Data governance answers three questions about every data set and field: **who is responsible for it**, **how sensitive it is**
and **where else it lives**. Without it, retention, data subjects' rights and the response to a breach are guesswork.

## 1. The data set's owner
- Every data set (a table, a topic in a queue, a log index, a set in the warehouse) has a **business owner**: a person or
  a team that decides on the purpose, access, retention and schema changes. The system administrator is not the owner.
- The owner approves the data set's class and every new field with personal data; the agent prepares the proposal.
- Copies (the warehouse, exports, test environments) inherit the class and owner of the source, unless the data has been
  effectively anonymized — then record it as a decision.

## 2. Data classes and requirements per class

| Class | Examples | Access | Encryption | Masking in logs and outside production | Retention |
|---|---|---|---|---|---|
| public | price list, product description | everyone | in transit | not needed | as needed |
| internal | configuration, metrics without people | employees by role | in transit and at rest | not needed | as needed |
| confidential | contracts, company financial data, keys | named, least privilege, access log | in transit and at rest | yes | defined, with deletion |
| personal data | email, phone, PESEL (national ID), address, IP, customer identifier | named by purpose, access log | in transit and at rest; high-risk fields (PESEL, IBAN, document) also at the field level | yes: a pseudonym (HMAC) or a mask | a period per purpose, automatic deletion |
| special categories (Art. 9) and children's data | health, biometrics for identification, opinions | narrowly, with a justification | as personal data, always at the field level | always; no copies in tests | the shortest possible; usually a DPIA |

- A data set has the class of the most sensitive field it contains.
- The class determines the technical requirements. The legal basis and the purpose are set separately (rule 2 in SKILL.md).

## 3. Data inventory
The file `docs/project/04-architecture/data-inventory.md`, one row per field with confidential or personal data:

| Data set | Field | Class | Purpose | Retention | Owner | Where else it lives |
|---|---|---|---|---|---|---|
| `customers` | `email` | personal data | account, notifications | 2 years after the account is closed | the Accounts team | application logs (masked), mailing (processor), warehouse |

- "Where else it lives" are the copies: logs, backups, analytics, the warehouse, queues, processors and test
  environments. Whether erasing data on request (rule 5) can be done at all depends on this column.
- The inventory is input to the record of processing activities (Art. 30), kept by the controller.

**An existing system without an inventory:**
1. Make a draft automatically: `tf analyze --only data-classification` lists fields with names typical for personal
   data in schemas, migrations and models, and also personal data in logs and in analytics calls.
2. Complete the draft with fields whose name says nothing. Review a sample of the data from text and JSON columns
   (`notes`, `metadata`, `payload`), doing it in the production environment and without copying the data.
3. The owners approve the classes, and then you add the purpose and retention.
4. You first fix personal data in logs and in analytics, because they have the widest audience.

## 4. The class next to the field in the code
Mark a field with a confidential or personal class at its definition, so that the change review and the analysis see it:
- SQL: `email varchar(255) NOT NULL, -- pii: personal data` or `COMMENT ON COLUMN customers.email IS 'pii'`;
- Prisma: a `/// pii` comment above the field;
- ORM: an annotation or comment next to the field (`# pii`, `// pii`, your own `@Pii` annotation).

A new field without a class and without an inventory entry is reported by `tf analyze` (the rule `pii-field-unclassified`).

## 5. Lineage and contracts
Data lineage and data contracts between teams in pipelines are described by `data-engineering`. A data set's contract
should carry the class of the fields, so that the consumer in the warehouse gets the same requirements as the source.
