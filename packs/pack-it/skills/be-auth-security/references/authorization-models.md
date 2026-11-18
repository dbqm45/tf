# Authorization models — which one to choose

| Model | The decision based on | Good for | Limitations |
|---|---|---|---|
| **RBAC** (roles) | the user's role → permissions | most business applications, few roles | role explosion ("Kraków branch manager"); it does not express "only your own documents" |
| **ABAC** (attributes) | attributes of the user, resource, action and context (department, region, confidentiality level, hour) | rules like "a doctor sees the patients of their own ward" | rules hard to review and test without a tool |
| **ReBAC** (relations) | a relation graph: owner, team member, shared by | document sharing, organizations and teams, folder hierarchies | a relation store needed (e.g. in the Google Zanzibar style: OpenFGA, SpiceDB) |
| **PBAC** (policies) | policies written as code outside the application, evaluated by an engine | many services with one set of rules, audit | an extra component (e.g. OPA/Rego, Cedar), decision latency |
| **DAC** (discretionary) | the resource owner decides whom to share it with | file sharing between users | hard to get central control and to revoke access |
| **MAC** (mandatory) | confidentiality labels assigned centrally, the user does not change them | government and military systems, strictly classified data | rigid; rare in business applications |

## Rules independent of the model
- Start with RBAC with a resource ownership check in the code; add attributes or relations when a specific case appears.
- The decision in one module or service (a decision point), called on **every** access to an object — BOLA
  and IDOR are the most common API bugs (be-api-design, `lifecycle-and-security.md`).
- **OAuth scopes** limit what *the application* can do on the user's behalf; they do not replace checking
  what *the user* can do with a specific object.
- Authorization tests as a matrix: roles or relations × actions × "own / someone else's object"; a permission change = a PR with tests.
- Denial decisions logged (an attack signal), without revealing in the response whether the object exists (404 instead of 403, when it
  matters).

## Sources
- [roadmap.sh — API Design](https://roadmap.sh/api-design) (RBAC, ABAC, ReBAC, PBAC, DAC, MAC, scopes)
- [AWS IAM: ABAC](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html),
  [Auth0: permissions, privileges and scopes](https://auth0.com/blog/permissions-privileges-and-scopes/)
Described in our own words.
