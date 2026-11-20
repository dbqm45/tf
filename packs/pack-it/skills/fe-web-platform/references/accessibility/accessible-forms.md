# Accessible Forms

> **Contents:** Metadata · TLDR · Notes (state as of 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / trade-offs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/accessible-forms (Den Odell, updated 17 October 2025).

## Metadata

- **Category:** Accessibility
- **Level:** Beginner
- **Format:** Native web examples

## TLDR

"Connect inputs to labels, use ARIA for dynamic validation, and ensure keyboard operability to
create forms that work for everyone."

## Notes (state as of 2026, corrections to the source)

- Use the native `required` instead of (or instead of duplicating it with) `aria-required`; the native attribute also gives browser
  validation. Mark the asterisk with `aria-hidden="true"` — an `aria-label` on a plain `<span>` is not read
  (the generic role does not take a name in ARIA 1.2). The example was corrected.
- Set `aria-invalid` only after an interaction/a submit attempt (not on a fresh form). After a failed submit
  move focus to the first invalid field or to the error summary (focus-management.md).
- For labels in components generate stable IDs (React `useId`, Angular — a field with `inject(…)`/a counter, Vue 3.5 `useId`)
  — consistent between SSR and the client.
- Validating the e-mail format with a regex is only UX; `type="email"` + server validation. Forms in Angular:
  Signal Forms / reactive forms — fw-angular.

## Problem

Three main accessibility problems of forms:

1. **Unlabelled input fields** — screen reader users do not know what to enter when the fields
   have no labels.
2. **Invisible validation errors** — errors shown as red text next to a field are completely
   invisible to screen readers.
3. **Keyboard navigation problems** — an inconsistent Tab order, invisible focus indicators,
   buttons inaccessible to keyboard users.

## Solution

- **Labels** — a `<label for="...">` associated with the `id` of the input field.
- **Announcing errors** — `role="alert"` on the error message, `aria-invalid="true"` on the field,
  linked through `aria-describedby`.
- **Grouping** — `<fieldset>` + `<legend>` for related fields (e.g. a radio group).
- **DOM order** — the order in the DOM must match the visual order (Tab follows the DOM, not
  the CSS).

## Code examples

### A basic form with labels and errors

```html
<form>
  <label for="email">Email address</label>
  <input
    id="email"
    type="email"
    aria-describedby="email-error email-hint"
    aria-invalid="true"
    required
  />
  <div id="email-hint">We'll never share your email</div>
  <div id="email-error" role="alert">Please enter a valid email address</div>

  <label for="username">
    Username <span aria-hidden="true">*</span>
  </label>
  <input id="username" type="text" required />

  <fieldset>
    <legend>Newsletter frequency</legend>
    <label><input type="radio" name="frequency" value="daily" /> Daily</label>
    <label><input type="radio" name="frequency" value="weekly" checked /> Weekly</label>
    <label><input type="radio" name="frequency" value="monthly" /> Monthly</label>
  </fieldset>

  <label>
    <input type="checkbox" aria-describedby="terms-error" />
    I agree to the terms and conditions
  </label>
  <div id="terms-error" role="alert"></div>

  <button type="submit">Create account</button>
</form>
```

### Dynamic announcement of validation errors

```javascript
function validateEmail(input) {
  const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value);
  const errorEl = document.getElementById(`${input.id}-error`);

  input.setAttribute('aria-invalid', !isValid);
  errorEl.textContent = isValid ? '' : 'Please enter a valid email address';
}

document.getElementById('email').addEventListener('blur', function() {
  validateEmail(this);
});
```

### A form-level success message

```html
<div role="status" aria-live="polite" aria-atomic="true" id="form-status"></div>

<script>
function handleFormSubmit(event) {
  event.preventDefault();
  document.getElementById('form-status').textContent =
    'Account created successfully. Redirecting...';
  setTimeout(() => { window.location.href = '/dashboard'; }, 2000);
}
</script>
```

### Multiple description references (`aria-describedby` with several IDs)

```html
<label for="password">Password</label>
<input
  id="password"
  type="password"
  aria-describedby="password-hint password-requirements password-error"
/>
<div id="password-hint">Choose a strong password</div>
<div id="password-requirements">At least 8 characters, one uppercase, one number</div>
<div id="password-error" role="alert"></div>
```

## Advantages

- Screen reader users know exactly what to enter in each field.
- Errors are announced, not only displayed visually.
- Higher form completion rates.
- WCAG conformance becomes realistically achievable.
- Correct labels and immediate feedback improve the experience of all users,
  not only those using assistive technologies.

## Disadvantages / trade-offs

- The HTML becomes more verbose — labels, IDs, multiple `aria-describedby` references.
- "Wrong ARIA is worse than no ARIA" — wrongly chosen attributes can mislead a screen reader
  more than their absence.
- Automated tools (linters/auditors) detect only obvious problems — tests with
  a real screen reader (NVDA, JAWS, VoiceOver) are required.
- CSS frameworks may clash with the required HTML structure, expecting different markup patterns.
- Too many announcements through a live region overwhelm the user.
- Some JS frameworks break `label`/`input` associations by generating dynamic IDs without synchronization.

## Related patterns

- [ARIA Roles and Attributes](aria-roles-and-attributes.md) — Accessibility
- [Semantic HTML](semantic-html.md) — Fundamentals
- [Focus Management](focus-management.md) — Accessibility
- [Creating Accessible Forms — W3C](https://www.w3.org/WAI/tutorials/forms/)
- [Form Validation — MDN](https://developer.mozilla.org/en-US/docs/Learn/Forms/Form_validation)
- [ARIA Form Properties — MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Attributes)

## When to use / when NOT to use

Apply these practices **by default, in every production form** — this is not an optional pattern
"for large projects", it is the accessibility minimum required by WCAG and it really affects the
completion rate. The only justified reduction of scope: a prototype/an internal tool without real
users with disabilities — even then a basic `<label>`+`for`/`id` costs as much
as its absence, so there is no reason to give it up (the KISS principle works here in favour of
accessibility, not against it — semantic HTML is *simpler* than recreating labelling in JS).
Just beware of overdoing ARIA (see "Wrong ARIA is worse than no ARIA" above) — add
ARIA attributes where native HTML really is not enough, not mechanically to everything.
