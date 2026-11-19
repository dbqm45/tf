# Single Responsibility

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/single-responsibility.

Note: the general definition is already in `../principles.md`. This file adds what
the frontendpatterns.dev page specifically contributes: a full "before/after" example of splitting a component into units
with a single responsibility.

## Metadata

- **Category:** Fundamentals
- **Level:** Beginner
- **Examples:** React
- **Last updated:** September 22, 2025
- **Author:** Den Odell

## TLDR

"Give each function, component, and module one job describable in a single sentence without using 'and'."

## Notes (state in 2026, corrections to the source)

- The "one sentence without 'and'" test is agnostic; general SRP — eng-design-principles, naming — eng-clean-code.
- Copying server data into a form's local state through `useEffect` (the "After" example) is a known React anti-pattern
  — it is better to initialize the form with a key (`key={user.id}`) or a separate form component.

## Problem

"Kitchen sink components" — components that combine data fetching, validation, date formatting, authorization logic and rendering of many UI sections all at once. This hinders testing, teamwork and debugging — changing one responsibility requires wading through all the others.

## Solution

Every element of code (function, component, module) should have one responsibility, describable in one sentence without the word "and". Separate data fetching from validation, formatting and access logic — each of these changes for a different reason and at a different time.

## Code examples

### Before: many responsibilities at once

```javascript
// ❌ Everything crammed into one component
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});

  // Data fetching
  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(r => r.json())
      .then(data => { setUser(data); setLoading(false); });
  }, [userId]);

  // Validation
  const validateForm = (data) => {
    const errs = {};
    if (!data.email.includes('@')) errs.email = 'Invalid email';
    if (data.age < 18) errs.age = 'Must be 18+';
    return errs;
  };

  // Formatting
  const formatDate = (date) => new Date(date).toLocaleDateString('en-US');

  // Auth logic
  const canEdit = () => user.role === 'admin' || user.id === currentUserId;

  // Submit handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateForm(user);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    await fetch(`/api/users/${userId}`, { method: 'PUT', body: JSON.stringify(user) });
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="profile">
      <h1>{user.name}</h1>
      <p>Joined: {formatDate(user.createdAt)}</p>
      {canEdit() && (
        <form onSubmit={handleSubmit}>
          <input value={user.email} onChange={e => setUser({...user, email: e.target.value})} />
          {errors.email && <span>{errors.email}</span>}
          <button>Save</button>
        </form>
      )}
    </div>
  );
}
```

### After: one responsibility per unit of code

```javascript
// ✅ Hook: data fetching only
function useUser(userId) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(r => r.json())
      .then(data => { setUser(data); setLoading(false); });
  }, [userId]);

  return { user, loading };
}

// ✅ Pure functions: one job each
const validateUserForm = (data) => {
  const errors = {};
  if (!data.email?.includes('@')) errors.email = 'Invalid email';
  if (data.age < 18) errors.age = 'Must be 18+';
  return errors;
};

const formatDate = (date) => new Date(date).toLocaleDateString('en-US');
const canEditProfile = (user, currentUserId) => user.role === 'admin' || user.id === currentUserId;
const updateUser = (userId, data) => fetch(`/api/users/${userId}`, { method: 'PUT', body: JSON.stringify(data) });

// ✅ Component: display only
function UserInfo({ user }) {
  return (
    <div>
      <h1>{user.name}</h1>
      <p>Joined: {formatDate(user.createdAt)}</p>
    </div>
  );
}

// ✅ Component: form only
function UserEditForm({ user, errors, onSubmit, onChange }) {
  return (
    <form onSubmit={onSubmit}>
      <input value={user.email} onChange={e => onChange('email', e.target.value)} />
      {errors.email && <span>{errors.email}</span>}
      <button type="submit">Save</button>
    </form>
  );
}

// ✅ Container: coordinates the pieces
function UserProfile({ userId, currentUserId }) {
  const { user, loading } = useUser(userId);
  const [editedUser, setEditedUser] = useState(null);
  const [errors, setErrors] = useState({});

  useEffect(() => { if (user) setEditedUser(user); }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateUserForm(editedUser);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    await updateUser(userId, editedUser);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="profile">
      <UserInfo user={user} />
      {canEditProfile(user, currentUserId) && (
        <UserEditForm
          user={editedUser}
          errors={errors}
          onSubmit={handleSubmit}
          onChange={(field, val) => setEditedUser(prev => ({ ...prev, [field]: val }))}
        />
      )}
    </div>
  );
}
```

### At the function level

```javascript
// ❌ Fetching AND transforming
async function getUserData(userId) {
  const response = await fetch(`/api/users/${userId}`);
  const data = await response.json();
  return {
    ...data,
    fullName: `${data.firstName} ${data.lastName}`,
    age: new Date().getFullYear() - new Date(data.birthDate).getFullYear()
  };
}

// ✅ Separate concerns
async function fetchUser(userId) {
  const response = await fetch(`/api/users/${userId}`);
  return response.json();
}

function transformUser(userData) {
  return {
    ...userData,
    fullName: `${userData.firstName} ${userData.lastName}`,
    age: new Date().getFullYear() - new Date(userData.birthDate).getFullYear()
  };
}

// Usage
const rawUser = await fetchUser(userId);
const user = transformUser(rawUser);
```

## Advantages

- Immediate clarity — understanding the purpose of each file takes seconds.
- Simple testing — a single responsibility, without a complex mock setup.
- Contained (non-spreading) changes — modifying the validation does not affect the rest of the code.
- Actual reuse — a date formatting function works everywhere, regardless of context.
- Faster debugging — a date formatting bug means checking one specific file.
- Parallel work — teams can work on different responsibilities without conflicts in the same files.

## Disadvantages / tradeoffs

- More files — more navigation and more imports to manage.
- A flow that is harder to follow — understanding "what is going on" requires going through more places.
- Subjective boundaries — what exactly "one responsibility" means can be debatable in practice.
- Easy to overdo — the risk of "a three-line function in a separate file" (excessive fragmentation without real gain).
- Onboarding cost — new people on the team must learn the splitting convention before they find their way in it.
- Requires team alignment — without agreed, written-down boundaries, the split will be inconsistent between different people.

## Related patterns

- [Separation of Concerns](separation-of-concerns.md) — Fundamentals.
- [Presentational vs. Container](../components/presentational-vs-container.md) — Components.
- Single Responsibility Principle — Wikipedia.
- SOLID Principles — Wikipedia.
- Clean Code Principles — freeCodeCamp.

## When to use / when NOT to use

Apply this test directly: if the description of a function/component needs the word "and" ("fetches the data **and** formats it **and** validates it"), that is a signal to split it — exactly as the TLDR of this page puts it.

Do not take it to the point of absurdity — a three-line function does not need its own file/module if it is not reused anywhere else and has no separate reason to change. Split where responsibilities really change at different times/for different reasons, not mechanically at every opportunity (see also the critique of overusing fragmentation in eng-design-principles).
