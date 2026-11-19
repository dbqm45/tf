# Domain adapters in Angular — tested

The version for **Angular 22**: compiled with `ngc` 22.2 (TypeScript 6.0, `strictTemplates`). The `../domain/archetypes` import
is the code from `lang-typescript/references/domain-building-blocks.md` (the domain layer without a dependency on Angular).

```ts
import { Component, LOCALE_ID, Pipe, PipeTransform, Service, computed, inject, input, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, httpResource } from '@angular/common/http';
import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { FormField, form, validate } from '@angular/forms/signals';
import { firstValueFrom } from 'rxjs';
import {
  BlockRequestState, CalendarView, FeatureType, Money, Party, TimeSlot, displayName, validateFeature,
} from '../domain/archetypes';

// ── Pipe: formatting Money in one place (standalone by default since v19) ─────
@Pipe({ name: 'money' })
export class MoneyPipe implements PipeTransform {
  private readonly locale = inject(LOCALE_ID);

  transform(value: Money | null | undefined): string {
    if (!value) return '';
    // Number() is enough for DISPLAY; calculations always on Money (bigint).
    return new Intl.NumberFormat(this.locale, { style: 'currency', currency: value.currency })
      .format(Number(value.minor) / 100);
  }
}

// ── Signal Forms (stable since v22): validation from product feature constraints (data from the API) ─
@Component({
  selector: 'app-feature-field',
  imports: [FormField],
  template: `
    <label>
      {{ feature().name }}
      <input [formField]="field.value" [attr.aria-invalid]="field.value().invalid()" />
    </label>
    @for (error of field.value().errors(); track error.kind) {
      <small role="alert">{{ error.message }}</small>
    }
  `,
})
export class FeatureFieldComponent {
  readonly feature = input.required<FeatureType>();
  protected readonly model = signal({ value: '' });
  protected readonly field = form(this.model, (path) => {
    validate(path.value, ({ value }) => {
      const message = validateFeature(this.feature(), value());
      return message ? { kind: 'feature', message } : null;
    });
  });
}

// ── Reactive Forms (v14+): the same domain rule as a ValidatorFn — for existing forms ─
export function featureValidator(feature: FeatureType): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const error = validateFeature(feature, String(control.value ?? ''));
    return error ? { feature: error } : null;
  };
}

// ── Edge: DTO from the API → domain read model ───────────────────────────────
interface CalendarDto {
  resourceId: string;
  free: { from: string; to: string }[];
  taken: Record<string, { from: string; to: string }[]>;
}

const toSlot = (s: { from: string; to: string }): TimeSlot => ({ from: new Date(s.from), to: new Date(s.to) });

export function toCalendarView(dto: CalendarDto): CalendarView {
  return {
    resourceId: dto.resourceId,
    free: dto.free.map(toSlot),
    taken: new Map(Object.entries(dto.taken).map(([owner, slots]) => [owner, slots.map(toSlot)])),
  };
}

// ── Availability store (v22: @Service + httpResource) ────────────────────────
@Service()
export class ResourceAvailabilityStore {
  private readonly http = inject(HttpClient);
  private readonly resourceId = signal<string | undefined>(undefined);
  private readonly _request = signal<BlockRequestState>({ kind: 'idle' });

  /** Read model: reloads itself when resourceId changes; status: idle/loading/resolved/error. */
  readonly calendar = httpResource<CalendarView>(
    () => {
      const id = this.resourceId();
      return id ? `/api/availability/${id}/calendar` : undefined;
    },
    { parse: (raw) => toCalendarView(raw as CalendarDto) },
  );
  readonly request = this._request.asReadonly();
  readonly isPending = computed(() => this._request().kind === 'pending');

  select(resourceId: string): void {
    this.resourceId.set(resourceId);
  }

  /** Command: no optimistic update — this is a contended resource; 409 is a normal result. */
  async block(resourceId: string, slot: TimeSlot): Promise<void> {
    this._request.set({ kind: 'pending', slot });
    try {
      await firstValueFrom(this.http.post(`/api/availability/${resourceId}/blocks`, {
        from: slot.from.toISOString(),
        to: slot.to.toISOString(),
      }));
      this._request.set({ kind: 'blocked', slot });
    } catch (err) {
      const reason = err instanceof HttpErrorResponse && err.status === 409
        ? 'The slot has just been taken'
        : 'Could not block the slot';
      this._request.set({ kind: 'rejected', slot, reason });
    } finally {
      this.calendar.reload();
    }
  }
}

// ── Party variant component (OnPush by default since v22) ────────────────────
@Component({
  selector: 'app-party-card',
  template: `
    <h3>{{ name() }}</h3>
    @switch (party().kind) {
      @case ('person') { <span class="badge">Person</span> }
      @case ('organization') { <span class="badge">Organization</span> }
    }
    <ul>
      @for (role of party().roles; track role) { <li>{{ role }}</li> }
    </ul>
  `,
})
export class PartyCardComponent {
  readonly party = input.required<Party>();
  readonly name = computed(() => displayName(this.party()));
}
```

## Older versions (check the project's version)
| In v22 code | Angular 19–21 | Angular 17–18 |
|---|---|---|
| `@Service()` | `@Injectable({ providedIn: 'root' })` | same as the column to the left |
| `httpResource(..., { parse })` | experimental in 19–21 — in production code rather a service with `HttpClient` + `signal`/`toSignal` | a service with `HttpClient` + `toSignal` |
| Signal Forms (`form`, `validate`, `[formField]`) | 21: experimental; ≤20: absent → `featureValidator` (Reactive Forms) | `featureValidator` |
| no `standalone: true` | ≥19 same as the column to the left | **add** `standalone: true` |
| OnPush by default | add `changeDetection: ChangeDetectionStrategy.OnPush` | same as the column to the left |

The pre-v22 variant (Reactive Forms, `@Injectable`, `HttpClient` + signals) was compiled with `ngc` 19 with `strictTemplates`.

## How to use it
- **A product features form** (the Product archetype): for each feature from the product type API `<app-feature-field [feature]="f" />`
  (Signal Forms) or `new FormControl('', { nonNullable: true, validators: featureValidator(f) })` (Reactive Forms).
  A new feature in the backend = zero changes in the form code.
- **An amount in a form** (Money): in the control the string typed by the user, conversion `Money.of(...)` on submit;
  with many forms with an amount — a custom control (`FormValueControl` / `ControlValueAccessor`).
- **A reservation** (Availability): `store.select(id)` loads the calendar (`store.calendar.value()`, `.isLoading()`, `.error()`);
  the button disabled while `store.isPending()`; `request().kind === 'rejected'` → a message in an `aria-live` region.
  No optimistic "reserved"; after the command `calendar.reload()`.
- **A configurator**: `computed(() => optionStates(all, picked(), rules))` — options with `disabledBecause` greyed out with a hint.
- **NgRx / SignalStore**: the same domain functions in reducers/`computed` — the domain does not depend on the state library.
