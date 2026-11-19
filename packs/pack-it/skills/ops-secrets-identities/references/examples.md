# Examples: secrets and machine identities

> **Contents:** 1. A cloud key pushed to a public repository · 2. OIDC instead of static keys in CI · 3. Reviewing the token inventory

Names, accounts and numbers are illustrative.

## 1. A cloud key pushed to a public repository
**Situation:** "Someone pushed `deploy.env` with an AWS access key to the public repository `acme/shop-sdk`.
I removed the file in the next commit, is that enough?"

**How:**
1. It is not enough: the key is in the history and could have been used within minutes (the skill's introduction). Rotation first (section 4).
2. Establish from the inventory the owner, the scope and the dependent services, so that the rotation does not silently switch anything off (section 1).
3. Check the cloud logs for use of the key since the push.
4. Revoke everything that was reachable with this key (e.g. secrets read from the secrets manager).
5. Only then the history clean-up and the security gap: why neither the hook nor push protection stopped it.

**Result:** a rotation runbook.

| # | Step | Who | Time target | Evidence |
|---|---|---|---|---|
| 1 | deactivate the key `AKIA…7Q2X` of the `svc-shop-deploy` account | on-call | 15 min from the report | "Inactive" status in the console |
| 2 | issue a new credential or move straight to OIDC (example 2) | owner of `svc-shop-deploy` | 1 h | a successful test deployment |
| 3 | review the cloud audit logs from the window between the push and the deactivation | security | 4 h | a list of API calls with this key |
| 4 | rotate the secrets reachable from the role (the `shop-prod` database password, the payment token) | service owners | 24 h | new versions in the secrets manager |
| 5 | remove the key from the history, turn on push protection in the repository, add a `--staged` scan in the hook | repository owner | 2 days | a blocked push with a test secret |
| 6 | delete the old key permanently, an entry in the incident log | on-call | after step 4 | an entry with a date |

## 2. OIDC instead of static keys in CI
**Situation:** "We have `AWS_ACCESS_KEY_ID` with administrator permissions in the repository secrets, used by the build
and by the deployment. Let's do it properly."

**How:**
1. Separate the identities: the build gets no cloud role, the deployment — a separate role (section 2).
2. The deployment role assumed through OIDC, valid for minutes, not a static key.
3. The trust policy pinned to the repository **and** the protected `production` environment — not to every branch.
4. The role's permissions narrowed to what the deployment uses; after a month a review of unused actions.
5. The old key deactivated and deleted, the secret removed from the repository; an entry in the inventory.

**Result:** the trust policy of the `shop-deploy-prod` role and a workflow fragment.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:acme/shop:environment:production"
        }
      }
    }
  ]
}
```

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read          # no id-token: the build will not assume any role
    steps:
      - uses: actions/checkout@<SHA>
      - run: make build
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production   # human approval required
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: aws-actions/configure-aws-credentials@<SHA>
        with:
          role-to-assume: arn:aws:iam::123456789012:role/shop-deploy-prod
          aws-region: eu-central-1
          role-duration-seconds: 900
      - run: make deploy
```

## 3. Reviewing the token inventory
**Situation:** the first daily export of the organization's credential inventory (CSV) has 412 rows. The team asks
where to start.

**How:**
1. The alerts from section 1: no expiry date, too broad a scope, no use for 90 days.
2. AI agent tokens to the front of the queue — broad permissions, work without supervision.
3. Every item gets an owner; no owner → revocation after a deadline is announced.
4. The inventory only reports — the PAT lifetime limit you configure separately as a policy.

**Result:** a report with decisions.

| Credential | Owner | Problem | Decision | Deadline |
|---|---|---|---|---|
| classic PAT `ci-release` (scope `repo`, `admin:org`) | none | no expiry, too broad | replace with a GitHub App with access to 2 repositories | 7 days |
| agent token `review-bot` | platform team | write access to all repositories | fine-grained, read-only code access and PR comments, expiry 30 days | 3 days |
| SSH key `deploy@old-jenkins` | none | unused for 214 days | revoke | immediately |
| 37 fine-grained PATs unused for 90 days | various | unused | an e-mail to the owners, then revocation | 14 days |
| — | — | no policy | a maximum PAT lifetime in the organization settings | 14 days |
