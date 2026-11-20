# Domain adapters in Angular — tested

> **Contents:** Code: pipe, form validation, read model, store, variant… · Older versions (check the project's version) · How to use it

The version for **Angular 22**: compiled with `ngc` 22.2.0 (TypeScript 6.0.3, `strictTemplates`) on 2026-11-20. The
`../domain/lending` import is the tool-lending domain from `lang-typescript/references/domain-building-blocks.md`
(the domain layer without a dependency on Angular).

## Code: pipe, form validation, read model, store, variant component
```ts
import { Component, LOCALE_ID, Pipe, PipeTransform, Service, computed, inject, input, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, httpResource } from '@angular/common/http';
import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { FormField, form, validate } from '@angular/forms/signals';
import { firstValueFrom } from 'rxjs';
import {
  checkField, displayName, isLoanRefusal, parseToolId,
  type FieldSpec, type LoanPeriod, type LoanRequestState, type Member, type Money, type ShelfView, type ToolId,
} from '../domain/lending';

// ── Pipe: formatting Money in one place (standalone by default since v19) ─────
@Pipe({ name: 'money' })
export class MoneyPipe implements PipeTransform {
  private readonly locale = inject(LOCALE_ID);

  transform(value: Money | null | undefined): string {
    if (!value) return '';
    // Number() is enough for DISPLAY; calculations always on Money (bigint minor units).
    return new Intl.NumberFormat(this.locale, { style: 'currency', currency: value.currency })
      .format(Number(value.toDecimalString()));
  }
}

// ── Signal Forms (stable since v22): validation from field specs (data from the API) ─
@Component({
  selector: 'app-checkout-field',
  imports: [FormField],
  template: `
    <label>
      {{ spec().label }}
      <input [formField]="field.value" [attr.aria-invalid]="field.value().invalid()" />
    </label>
    @for (error of field.value().errors(); track error.kind) {
      <small role="alert">{{ error.message }}</small>
    }
  `,
})
export class CheckoutFieldComponent {
  readonly spec = input.required<FieldSpec>();
  protected readonly model = signal({ value: '' });
  protected readonly field = form(this.model, (path) => {
    validate(path.value, ({ value }) => {
      const message = checkField(this.spec(), value());
      return message ? { kind: 'field-rule', message } : null;
    });
  });
}

// ── Reactive Forms (v14+): the same domain rule as a ValidatorFn — for existing forms ─
export function fieldRuleValidator(spec: FieldSpec): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const message = checkField(spec, String(control.value ?? ''));
    return message ? { fieldRule: message } : null;
  };
}

// ── Edge: DTO from the API → domain read model ───────────────────────────────
interface ShelfDto {
  asOf: string;
  loans: Record<string, { from: string; to: string }[]>;
}

const toPeriod = (p: { from: string; to: string }): LoanPeriod => ({ from: new Date(p.from), to: new Date(p.to) });

export function toShelfView(dto: ShelfDto): ShelfView {
  return {
    asOf: new Date(dto.asOf),
    loans: new Map(Object.entries(dto.loans).map(([id, periods]) => [parseToolId(id), periods.map(toPeriod)])),
  };
}

// ── Loan store (v22: @Service + httpResource) ────────────────────────────────
@Service()
export class ToolLoanStore {
  private readonly http = inject(HttpClient);
  private readonly day = signal<string | undefined>(undefined);
  private readonly _request = signal<LoanRequestState>({ kind: 'idle' });

  /** Read model: reloads itself when the day changes; status: idle/loading/resolved/error. */
  readonly shelf = httpResource<ShelfView>(
    () => {
      const day = this.day();
      return day ? `/api/shelf?day=${day}` : undefined;
    },
    { parse: (raw) => toShelfView(raw as ShelfDto) },
  );
  readonly request = this._request.asReadonly();
  readonly isSending = computed(() => this._request().kind === 'sending');

  showDay(isoDay: string): void {
    this.day.set(isoDay);
  }

  /** Command: no optimistic "lent" — tools are contended; a 409 refusal is a normal answer. */
  async lend(tool: ToolId, period: LoanPeriod): Promise<void> {
    this._request.set({ kind: 'sending', tool });
    try {
      await firstValueFrom(this.http.post(`/api/tools/${tool}/loans`, {
        from: period.from.toISOString(),
        to: period.to.toISOString(),
      }));
      this._request.set({ kind: 'lent', tool, period });
    } catch (err) {
      const body: unknown = err instanceof HttpErrorResponse && err.status === 409 ? err.error : undefined;
      const code = typeof body === 'object' && body !== null && 'refusal' in body ? body.refusal : undefined;
      this._request.set(isLoanRefusal(code)
        ? { kind: 'refused', tool, reason: code }
        : { kind: 'failed', tool, message: 'Could not reach the library, try again' });
    } finally {
      this.shelf.reload();
    }
  }
}

// ── Member variant component (OnPush by default since v22) ───────────────────
@Component({
  selector: 'app-member-card',
  template: `
    <h3>{{ name() }}</h3>
    @switch (member().kind) {
      @case ('adult') { <span class="badge">Adult</span> }
      @case ('junior') { <span class="badge">Junior</span> }
      @case ('company') { <span class="badge">Company</span> }
    }
    <ul>
      @for (licence of member().licences; track licence) { <li>{{ licence }}</li> }
    </ul>
  `,
})
export class MemberCardComponent {
  readonly member = input.required<Member>();
  readonly name = computed(() => displayName(this.member()));
}
```

## Older versions (check the project's version)
| In v22 code | Angular 19–21 | Angular 17–18 |
|---|---|---|
| `@Service()` | `@Injectable({ providedIn: 'root' })` | same as the column to the left |
| `httpResource(..., { parse })` | experimental in 19–21 — in production code rather a service with `HttpClient` + `signal`/`toSignal` | a service with `HttpClient` + `toSignal` |
| Signal Forms (`form`, `validate`, `[formField]`) | 21: experimental; ≤20: absent → `fieldRuleValidator` (Reactive Forms) | `fieldRuleValidator` |
| no `standalone: true` | ≥19 same as the column to the left | **add** `standalone: true` |
| OnPush by default | add `changeDetection: ChangeDetectionStrategy.OnPush` | same as the column to the left |

The pre-v22 column was checked with `ngc` 19 (`strictTemplates`) on an earlier version of this example; the code above was
compiled with 22.2.0 only.

## How to use it
- **A checkout form**: for each field spec from the API `<app-checkout-field [spec]="s" />` (Signal Forms) or
  `new FormControl('', { nonNullable: true, validators: fieldRuleValidator(s) })` (Reactive Forms).
  A new field rule in the backend = zero changes in the form code.
- **An amount in a form** (Money): in the control the string typed by the user, conversion `Money.of(...)` on submit;
  with many forms with an amount — a custom control (`FormValueControl` / `ControlValueAccessor`).
- **A loan**: `store.showDay(day)` loads the shelf view (`store.shelf.value()`, `.isLoading()`, `.error()`);
  `looksFree(view, tool, period)` only greys out days (a hint); the button disabled while `store.isSending()`;
  `request().kind === 'refused'` → the reason in an `aria-live` region, `'failed'` → a retry button.
  No optimistic "lent"; after the command `shelf.reload()`.
- **Accessories**: `computed(() => optionStates(rules, options, chosen()))` — disabled options greyed out with `why`
  as the hint; `unmetNeeds(...)` listed before submit.
- **NgRx / SignalStore**: the same domain functions in reducers/`computed` — the domain does not depend on the state library.
