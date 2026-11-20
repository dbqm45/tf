# Forms in React: a schema shared with the server, errors, accessibility, wizards

API checked in the packages on 2026-11-10: `react-hook-form` 7.91.0 (React 16.8–19), `@hookform/resolvers` 7.0.5
(`zodResolver` accepts Zod 3 and Zod 4 schemas, `standardSchemaResolver` — Standard Schema), `zod` 4.6.7.
You check the versions in the project in `package.json` (core-grounding).

## 1. A native form or a library
- **Native** (`<form action={fn}>`, `useActionState`, `useFormStatus` — rule 6 in SKILL.md): a few fields,
  validation on submit, the result from the server. No library; with Server Actions it also works without JavaScript.
- **React Hook Form**: many fields with validation while typing, fields dependent on others, lists of fields added
  by the user, a wizard in several steps, controls from libraries (a date picker, a search box). The fields are
  uncontrolled (`register`), so the form does not re-render on every keystroke.

## 2. One schema for the client and the server
```ts
// shared/company-schema.ts — imported both in the browser and on the server
import { z } from "zod";
export const companySchema = z.object({
  name: z.string().trim().min(2, "Enter the company name"),
  nip: z.string().regex(/^\d{10}$/, "NIP is 10 digits"),
  contacts: z.array(z.object({ email: z.email("Invalid e-mail") })).min(1, "Add a contact person"),
});
export type CompanyInput = z.input<typeof companySchema>;
```
- Client: `useForm<CompanyInput>({ resolver: zodResolver(companySchema), mode: "onTouched" })`.
- Server: `companySchema.safeParse(body)`. **The server always validates**, because validation in the browser is a convenience,
  not a safeguard. Rules that require the database (NIP (the Polish tax identification number) already taken, a limit) are only on the server.
- Domain rules (e.g. "a NIP with a valid checksum") you write as pure functions in `domain/` and use them
  in the schema (`.refine`), rather than copying them into the component.
- A schema with transformations (`.transform`, `z.coerce`) has different input and output types: the form works on
  `z.input`, and the server and the domain on `z.output`.

## 3. Field errors and errors from the server
- Field errors are in `formState.errors.<field>.message`. The message says what to fix ("NIP is 10 digits"), not "invalid
  field".
- A 422 response with field errors (Problem Details with an `errors` list, be-api-design, pack-it) you map onto the fields:
  ```ts
  for (const e of problem.errors ?? []) setError(e.field as FieldPath<CompanyInput>, { type: "server", message: e.message });
  if (!problem.errors?.length) setError("root.serverError", { type: "server", message: problem.detail });
  ```
- A general error (no network, 500, a conflict) you show above the form from `errors.root.serverError`. The data stays
  in the fields; the user does not type it a second time.
- The `onTouched` or `onBlur` validation mode: the error appears after leaving the field, not from the first keystroke. After
  the first submit the correction is checked live (`reValidateMode`, `onChange` by default).

## 4. Accessibility
- Every field has a `<label htmlFor>`. A placeholder does not replace the label (the `accessibility` module in `tf analyze`
  detects a field without a label).
- A field with an error: `aria-invalid="true"` and `aria-describedby` pointing to the element with the message. The message
  as text, not by colour alone (WCAG 2.2 SC 3.3.1 and 1.4.1).
- After a failed submit the focus goes to the first field with an error (`shouldFocusError`, enabled by default). For
  a long form you add an error summary with links to the fields (`role="alert"`).
- The submit button is not disabled "because the form is invalid". The user clicks and gets the messages.
  You disable it only during submission.
- Required fields marked in the label (with text, e.g. "required"), not with an asterisk alone.

## 5. A wizard in several steps
- **One `useForm` for the whole wizard** and one schema. A step is a subset of the fields. Moving on:
  `if (await trigger(["name", "nip"])) next()` (`trigger` validates the given fields and returns `Promise<boolean>`).
- The step in the URL (`?step=2`), so that back in the browser goes back a step instead of closing the wizard. The data stays when
  going back.
- A draft for a long wizard: saved in `sessionStorage` or on the server (a working version), without sensitive
  data in the browser's storage. On return the question "continue the draft?".
- The last step shows a summary to review. The server validates everything once more.

## 6. Dynamic fields and controls from libraries
- A list of fields added by the user (contact persons, invoice lines): `useFieldArray`. The key in `map`
  is `field.id` from the hook, not the index, because otherwise the values jump after a row is removed.
- A control that does not accept the native field's `ref` (a date picker, a select from a library): `Controller` or
  `useController`. The control gets `value`/`onChange`/`onBlur` and a name accessible to the screen reader.
- A field dependent on another (e.g. "NIP" only for companies): `useWatch` in a small component, so as not to re-render the whole
  form.

## 7. Submission
- During submission (`formState.isSubmitting`) the button is disabled with the text "Saving…". A double
  click does not send two requests, and the server accepts an idempotency key for create operations anyway
  (be-api-design, pack-it).
- After success: a message and moving on, or `reset()` with the values from the server's response.
- Leaving the page with unsaved changes (`formState.isDirty`): a warning only in long forms.

## 8. Tests
- Testing Library from the user's perspective: type, submit, check the message at the field, `aria-invalid` and the focus
  on the first error (`references/patterns.md`; component tests: fe-architecture, pack-it).
- A separate schema test (pure functions, valid and invalid examples). The same schema protects the server, so
  the API test checks 422 with field errors.
- Wizard: a test of moving between steps with a block on an error, and of going back without losing data.
