---
name: ops-iac-terraform
description: Use for infrastructure as code (Terraform/OpenTofu) — modules, state, variables, network, IAM, databases, storage.
disable-model-invocation: true
metadata:
  status: "inactive"  # measured 2026-11-16: docs/inactive-skills.md
  review: "2027-04-17"
  catalog: "Use for infrastructure as code — Terraform/OpenTofu, modules, state, variables, cloud resources (network, IAM, databases, storage). Not for pipelines (ops-ci-cd) or containers (ops-docker)."
---

# Infrastructure as code (Terraform)

## The golden rule
**You never run `terraform apply` or `destroy` on your own.** You prepare the change, run
`terraform fmt`, `terraform validate` and `terraform plan`, and present the plan to a human for approval.

## Structure
```
infra/
  modules/<name>/      # main.tf, variables.tf, outputs.tf, README.md
  envs/staging/        # module calls + backend
  envs/production/
```
- Environments differ in variables, not in code.
- Modules have documented variables (`description`, `type`, validations) and outputs.

## State
- A remote backend with locking. On S3, native locking `use_lockfile = true` (Terraform ≥ 1.11, experimental in 1.10;
  OpenTofu ≥ 1.10) — locking through DynamoDB is deprecated; GCS and Terraform Cloud lock on their own. State encrypted, separate per environment. Never state in the repo.
- State contains secrets — treat access to it like access to secrets.

## Security
- IAM: least privilege, no `*` in actions and production resources.
- Storage private by default, encryption enabled, public access explicitly blocked.
- Databases and internal services without a public IP; security groups without `0.0.0.0/0` except for the load balancer on 80/443.
- Secrets from a secrets manager (data source), not in `.tfvars` in the repo.
- Management ports (SSH 22, RDP 3389, admin panels) never from `0.0.0.0/0` — access through a bastion, SSM or VPN.

## Test and temporary environments
Huntress described its own incident: a bug in automation left 37 test machines running with RDP and SSH open
and a weak password; one of them was taken over by guessing the password and used to scan other addresses.
Segmentation limited the damage.
- Test/QA in a separate cloud account or project, with separate secrets and synthetic or masked data.
- Credentials generated for every run (SSH keys per run), no shared passwords in images.
- Every temporary resource has `owner` and `expires` tags; automatic deletion after its lifetime and a periodic search for
  "orphans". An alert on unusual outbound traffic from test machines.
- Source: [Investigating Unauthorized Access: Huntress QA Environment Incident](https://www.huntress.com/blog/investigating-unauthorized-access-huntress-qa-environment-incident)

## Gates in the PR
In order from the cheapest: `terraform fmt -check` → `terraform validate` → Checkov or tfsec (Trivy config) → organization
policies in OPA/Conftest (tags, allowed sizes, forbidden constructs) → secret scan (TruffleHog, Gitleaks) →
the plan and the cost difference (Infracost, ops-finops). You enable new scanners first in warning mode, then in blocking mode.
AI-generated infrastructure is marked in the PR and passes the same gates plus a human review.

## Drift
- A scheduled job (e.g. daily) runs `terraform plan -detailed-exitcode` (code 2 = a difference) for every
  environment and reports drift as a task or an incident.
- Who changed it: correlation with the cloud audit log (CloudTrail, Activity Log); an alert on manual changes to IAM and network
  rules (e.g. an open port 22 added in the console).
- You fix drift through a PR (the code catches up with reality or the other way round), never through a manual `apply` outside the pipeline.

## Protection against disaster
- `lifecycle { prevent_destroy = true }` for databases, data buckets, KMS keys.
- In the plan, look for `must be replaced` / `destroy` — describe every such occurrence clearly in the report.
- Provider versions pinned (`required_providers` + `.terraform.lock.hcl` in the repo).

## Verification
`terraform fmt -check`, `terraform validate`, `terraform plan -out=tfplan`; optionally `tflint`, `checkov`/`tfsec`.

Sources (devops.com): [Common IaC Security Issues and How to Fix Them](https://devops.com/common-iac-security-issues-and-how-to-fix-them/),
[AI Can Generate Your Infrastructure. Can Your CI/CD Pipeline Trust It?](https://devops.com/ai-can-generate-your-infrastructure-can-your-ci-cd-pipeline-trust-it/),
[AI-Driven Drift Detection in AWS](https://devops.com/ai-driven-drift-detection-in-aws-terraform-meets-intelligence/);
S3 locking: [What's new in OpenTofu 1.10](https://opentofu.org/docs/v1.10/intro/whats-new/),
[Terraform S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3); drift:
[terraform plan](https://developer.hashicorp.com/terraform/cli/commands/plan) (`-detailed-exitcode`).
