# Upgrading Stripe versions: API, SDK, Stripe.js, webhooks

## 1. The target version
- You take a version given by a human as is. Otherwise you check the current one in the documentation (the "API
  versioning" page, the sentence "The current version is…"; in the Stripe CLI `stripe docs /api/versioning`).
- A snapshot from the source (2026-10-21): `2026-09-30.endive`. New stable versions come out monthly, so a snapshot older
  than a month is probably out of date. Without access to the documentation, say that the latest version is
  unverified; do not guess a newer number.
- Compare the target with every pin in the integration: client configuration, per-request overrides, webhook endpoints.
  Do not roll a pin back to an older version or change a stable one to a preview one without being asked; a pin that matches
  the target is reported as unchanged.

## 2. How Stripe versions
- Dated versions (`YYYY-MM-DD.name`, e.g. `2024-12-18.acacia`, `2025-08-27.basil`). Since `2024-09-30.acacia`, monthly
  a version without breaking changes, and twice a year a major release that starts with a version with breaking changes.
- **Backward compatible:** new resources, new optional parameters, new fields in responses, a change of identifier
  length, new event types. **Breaking:** renaming or removing a field, a change of behavior, removed
  endpoints and parameters.
- Store Stripe object identifiers in columns of up to 255 characters with case-sensitive comparison.

## 3. Server SDKs
- **Ruby, Python, PHP, Node.js:** you set the API version in the client configuration (Node: `apiVersion`) and can
  override it per request — this is how you test a new version in pieces.
- **Java, Go, .NET:** the API version is fixed for an SDK release (the response types match it). Do not override it —
  raise the SDK to the release that targets the target version.
- A preview version requires a `beta` SDK release in every language.
- Always an explicit version in code, not the account's default version.

## 4. Stripe.js and mobile SDKs
- Stripe.js: an "evergreen" model with major releases twice a year (Acacia, Basil, Clover, Dahlia, Endive). The Stripe.js
  version is paired with the API version and you cannot override that; you load it with a script path that names the release
  or with the `@stripe/stripe-js` package (the package's major version matches the release). v3 is supported indefinitely; before changing
  Stripe.js, raise the API version first.
- iOS and Android: SemVer, fixes only in the latest major version. React Native: the `0.x.y` scheme, where a change of `x`
  may break. Mobile SDKs work with any backend API version, unless the documentation says otherwise.

## 5. Webhooks and event destinations
- "Snapshot" events have an API version; "thin" events do not, so you do not change their destinations (calls
  that fetch the full event or resource are still versioned).
- A v2 destination (webhook, Amazon EventBridge, Azure Event Grid) has a `snapshot_api_version` that is immutable after
  creation: you create a new one, test it, during the switchover the handler accepts both signing secrets, then you disable the
  old one (otherwise events arrive twice).
- Webhook handling ignores unknown event types without an error.

## 6. Procedure
1. Review the API changelog between the current and the target version and the "API upgrades" guide.
2. Raise the SDK package (e.g. `npm update stripe`, `pip install --upgrade stripe`) in a separate PR (ops-dependency-upgrades).
3. Change the pinned version in the client configuration.
4. Test with the `Stripe-Version` header (curl) or a per-request override in a sandbox.
5. Event destinations per section 5.
6. Stripe.js and mobile SDKs, if needed.
7. Deploy. For 72 hours after raising the account's version you can go back to the previous one in Workbench.

## Sources
stripe/ai, file skills/upgrade-stripe/SKILL.md, commit 1bcd18a (2026-10-21), MIT. Described in our own words; names of
versions and releases copied from the source.
