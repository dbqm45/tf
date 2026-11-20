# Control mapping: service equivalents and the table template

Contents: 1. Template · 2. Service equivalents · 3. Configuration pitfalls

## 1. The table template in `cloud-security-baseline.md`
Columns: ID · control (goal) · AWS · Azure · GCP · enforcement (preventive) · detection · verification · owner ·
deviations (until when). A control is written as a goal ("no public storage"), not as a service name.

## 2. Service equivalents
| Goal | AWS | Azure | GCP |
|---|---|---|---|
| Hierarchy | Organizations, OUs, accounts | management groups, subscriptions | organization, folders, projects |
| Preventive guardrail | SCP (RCP for resources) | Azure Policy (Deny) | Organization Policy |
| Audit log | CloudTrail | Activity Log | Cloud Audit Logs |
| Workload identity | IAM roles, IRSA, Pod Identity | managed identity, Workload Identity | a service account with attachment, Workload Identity |
| Federation with CI | OIDC provider in IAM | Entra credential federation | Workload Identity Federation |
| Private access to PaaS | PrivateLink, VPC endpoints | Private Endpoint | Private Service Connect |
| Customer keys | KMS | Key Vault | Cloud KMS |
| Posture | Security Hub | Defender for Cloud | Security Command Center |
| Access analysis | IAM Access Analyzer | Entra Permissions Management [unverified: product status] | IAM Recommender |

## 3. Configuration pitfalls
- An SCP without an exception for the emergency role also blocks the fix; test in a trial OU.
- Azure Policy with the Deny effect does not fix existing resources (a remediation task is needed).
- A trail in only one region misses activity in the others; use a multi-region trail.
- Logs in the same account as the workloads: an attacker with permissions deletes them; a separate log account.
- "Encrypted" does not mean "customer key": check who owns the key and the policies.
