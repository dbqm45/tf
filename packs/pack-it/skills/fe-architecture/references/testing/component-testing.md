# Component Testing

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/component-testing.

## Metadata

- **Category:** Testing
- **Level:** Intermediate
- **Framework examples:** React, Vue, Svelte, Native web
- **Last updated:** 29 November 2025
- **Author:** Den Odell

## TLDR

"Test components by rendering them, simulating user interactions, and asserting on the resulting
output rather than implementation details."

## Notes (state in 2026, corrections to the source)

- Strategy (the testing trophy, what to test, test doubles) — eng-testing; choosing cases — qa-test-design; tools —
  tool-vitest (also browser mode), tool-jest, tool-playwright (e2e, accessibility snapshots).
- The examples use `jest.fn()`; in Vitest it is `vi.fn()` / `vi.spyOn()` — a compatible API.
- Prefer `userEvent` over `fireEvent` (a realistic sequence of events) and queries by roles/labels
  (`getByRole`, `getByLabelText`) over `getByText`/CSS selectors.
- A `fetch` mock must have `ok: true` (and `status`) if the component checks `response.ok` — corrected. It is better
  to mock the network at the HTTP level (MSW) than `global.fetch`.
- Svelte 5: `component.$set` does not exist — use `rerender({ … })` from `@testing-library/svelte`. Corrected.
- Angular: `TestBed` + Angular Testing Library (`render(Component, { inputs })`), `provideHttpClientTesting()`;
  in zoneless — `await fixture.whenStable()` (fw-angular).
- Snapshots of whole trees are brittle — if at all, then small, targeted ones (`toMatchInlineSnapshot`) or ARIA snapshots
  (Playwright `toMatchAriaSnapshot`).

## Problem

Developers test components manually, which leads to missing error states, empty states and
edge cases. The lack of automated tests makes every refactor risky — a change in
a shared component can break many pages without the team knowing.

## Solution

Tests render the component, simulate user interaction and check the result — the happy path,
errors, loading states, edge cases. The key idea of Testing Library: test the component the way
the user actually uses it — find elements by accessible names (role/label), simulate
clicks and typing, check the visible content, not implementation details. Mocking the API
keeps tests fast and deterministic.

## Code examples

### Basic Component Testing — React

```javascript
import { render, fireEvent, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('button calls onClick when clicked', () => {
  const handleClick = jest.fn();
  render(<Button onClick={handleClick}>Click me</Button>);
  fireEvent.click(screen.getByText('Click me'));
  expect(handleClick).toHaveBeenCalledTimes(1);
});

test('form submission with user input', async () => {
  const handleSubmit = jest.fn();
  const user = userEvent.setup();
  render(<LoginForm onSubmit={handleSubmit} />);

  await user.type(screen.getByLabelText('Email'), 'user@example.com');
  await user.type(screen.getByLabelText('Password'), 'password123');
  await user.click(screen.getByRole('button', { name: /log in/i }));

  expect(handleSubmit).toHaveBeenCalledWith({
    email: 'user@example.com',
    password: 'password123'
  });
});
```

### Basic Component Testing — Vue

```javascript
import { mount } from '@vue/test-utils';
import Button from './Button.vue';

test('button calls onClick when clicked', async () => {
  const handleClick = jest.fn();
  const wrapper = mount(Button, {
    props: { onClick: handleClick },
    slots: { default: 'Click me' }
  });

  await wrapper.find('button').trigger('click');
  expect(handleClick).toHaveBeenCalledTimes(1);
});

test('form emits submit event with input data', async () => {
  const wrapper = mount(LoginForm);

  await wrapper.find('input[type="email"]').setValue('user@example.com');
  await wrapper.find('input[type="password"]').setValue('password123');
  await wrapper.find('form').trigger('submit.prevent');

  expect(wrapper.emitted('submit')[0]).toEqual([{
    email: 'user@example.com',
    password: 'password123'
  }]);
});
```

### Basic Component Testing — Svelte

```javascript
import { render, fireEvent, screen } from '@testing-library/svelte';
import Button from './Button.svelte';

test('button calls onClick when clicked', async () => {
  const handleClick = jest.fn();
  render(Button, { props: { onClick: handleClick } });

  await fireEvent.click(screen.getByRole('button'));
  expect(handleClick).toHaveBeenCalledTimes(1);
});

test('reactive statement updates display', async () => {
  const { rerender } = render(Counter, { props: { count: 0 } });
  expect(screen.getByText('Count: 0')).toBeInTheDocument();

  await rerender({ count: 5 }); // Svelte 5: no component.$set
  expect(screen.getByText('Count: 5')).toBeInTheDocument();
});
```

### Basic Component Testing — Web Components

```javascript
describe('Button component', () => {
  let button;

  beforeEach(() => {
    button = document.createElement('custom-button');
    document.body.appendChild(button);
  });

  afterEach(() => {
    document.body.removeChild(button);
  });

  test('button calls onClick when clicked', () => {
    const handleClick = jest.fn();
    button.addEventListener('click', handleClick);
    button.click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('button updates text when attribute changes', () => {
    button.setAttribute('label', 'New Label');
    expect(button.shadowRoot.querySelector('button').textContent).toBe('New Label');
  });
});
```

### Testing Async Behavior

```javascript
test('displays user data after loading', async () => {
  jest.spyOn(global, 'fetch').mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ id: 1, name: 'John Doe' })
  });

  render(<UserProfile userId={1} />);
  expect(screen.getByText('Loading...')).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
  global.fetch.mockRestore();
});

test('displays error message on failure', async () => {
  jest.spyOn(global, 'fetch').mockRejectedValue(new Error('Failed to fetch'));
  render(<UserProfile userId={1} />);

  await waitFor(() => {
    expect(screen.getByText('Failed to load user')).toBeInTheDocument();
  });
  global.fetch.mockRestore();
});
```

### Testing Component State Changes

```javascript
test('counter increments when button is clicked', () => {
  render(<Counter initialCount={0} />);
  const button = screen.getByRole('button', { name: /increment/i });

  fireEvent.click(button);
  expect(screen.getByText('Count: 1')).toBeInTheDocument();

  fireEvent.click(button);
  expect(screen.getByText('Count: 2')).toBeInTheDocument();
});
```

### Testing with Mock Providers

```javascript
test('component uses context value', () => {
  const mockContext = { user: { name: 'John' } };

  render(
    <UserContext.Provider value={mockContext}>
      <UserGreeting />
    </UserContext.Provider>
  );

  expect(screen.getByText('Hello, John')).toBeInTheDocument();
});
```

### Testing Error Boundaries

```javascript
test('error boundary catches component errors', () => {
  const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
  const ThrowError = () => { throw new Error('Test error'); };

  render(
    <ErrorBoundary fallback={<div>Error occurred</div>}>
      <ThrowError />
    </ErrorBoundary>
  );

  expect(screen.getByText('Error occurred')).toBeInTheDocument();
  consoleSpy.mockRestore();
});
```

### Accessibility Testing

```javascript
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

test('button has no accessibility violations', async () => {
  const { container } = render(<Button>Click me</Button>);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});

test('form labels are associated with inputs', () => {
  render(<LoginForm />);
  expect(screen.getByLabelText('Email')).toBeInTheDocument();
  expect(screen.getByLabelText('Password')).toBeInTheDocument();
});
```

### Snapshot Testing

```javascript
test('component renders correctly', () => {
  const { container } = render(<Card title="Test" content="Content" />);
  expect(container.firstChild).toMatchSnapshot();
});
```

### Testing Custom Hooks (React)

```javascript
import { renderHook, act } from '@testing-library/react';

test('useCounter increments count', () => {
  const { result } = renderHook(() => useCounter(0));
  expect(result.current.count).toBe(0);

  act(() => result.current.increment());
  expect(result.current.count).toBe(1);
});
```

## Advantages

- Regressions caught before production — bugs found earlier cost less.
- Refactoring becomes safe, because the tests back it up.
- Tests act as documentation for new people on the team.
- The time of manual quality checks shrinks.
- Writing tests forces you to think about edge cases upfront.
- Components become better designed — the ones that are hard to test usually have a design
  problem, not just a testing one.

## Disadvantages / tradeoffs

- Writing thorough tests can double the initial development time.
- Testing implementation details (not behaviour) creates brittle tests that break on
  every refactor.
- Green tests do not mean the code works — unrealistic mocks give false confidence.
- Mocking adds complexity and can mask integration problems.
- Slow test suites kill the team's productivity.
- Snapshot tests break on harmless formatting changes.
- Testing asynchrony is genuinely hard — `waitFor`/`act` have subtle timing
  behaviour.
- Deciding what to test requires judgement — too many unit tests give brittleness, too few
  miss important cases.
- Outdated, unmaintained tests are worse than no tests — they give a false sense
  of safety.

## Related patterns

- Testing Library Documentation (React).
- Vue Test Utils.
- Svelte Testing Library.
- Component Testing — Cypress.

## When to use / when NOT to use

Test behaviour from the user's perspective (what they see, what they can click/type) by default for every
component with real logic (conditions, states, interactions) — this is the boundary where manual
testing systematically misses edge cases. Do **not** test implementation details
(internal state, variable names, internal structure) — that is exactly the type of test that
breaks on every harmless refactor and as a result discourages the team from testing, instead of
building trust in it.
