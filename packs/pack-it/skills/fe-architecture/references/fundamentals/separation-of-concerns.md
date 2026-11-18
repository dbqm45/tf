# Separation of Concerns

> **Contents:** Metadata · TLDR · Notes (state in 2026, corrections to the source) · Problem · Solution · Code examples · Advantages · Disadvantages / tradeoffs · Related patterns · When to use / when NOT to use

Source: frontendpatterns.dev/separation-of-concerns.

Note: the general definition of this concept is already in `../principles.md` (the "Logical
Separation of Concerns" foundation + the SoC principle from Hrynkevych's article). This file adds what
the frontendpatterns.dev page specifically contributes: the split into layers (data/logic/presentation/styles) with full
before/after examples.

## Metadata

- **Category:** Fundamentals
- **Level:** Beginner
- **Examples:** Native web
- **Last updated:** September 22, 2025
- **Author:** Den Odell

## TLDR

"Organize code into layers (data, logic, presentation, styling) so changes in one area don't ripple through unrelated code."

## Notes (state in 2026, corrections to the source)

- The principle is agnostic (eng-design-principles); in Angular the layers are naturally a service (data) + pure functions
  (rules) + a component (presentation) — fw-angular.
- The data layer examples lack a `response.ok` check (fe-web-platform) — add it in real code.
- Domain logic as an immutable class (`Cart`) or pure functions — both forms are good; what matters is that it does not
  depend on the framework.

## Problem

Components containing "500 lines of tangled spaghetti where API calls sit next to inline styles, business logic weaves through JSX, and validation rules hide between event handlers." The effect: difficulties with code reuse, testing, teamwork and maintenance.

## Solution

Split the code into layers: API services returning plain data, pure functions for business rules, components focused solely on rendering, and separate style files/modules.

## Code examples

### A basic split into layers

**❌ Mixed:**

```javascript
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(r => r.json())
      .then(data => {
        if (data.age >= 18) setUser(data);
      });
  }, [userId]);

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc' }}>
      {user && <h1>{user.name}</h1>}
    </div>
  );
}
```

**✅ Separated:**

```javascript
const userApi = {
  fetchUser: (id) => fetch(`/api/users/${id}`).then(r => r.json())
};

const userValidation = {
  canViewProfile: (user) => user.isActive && user.age >= 18
};

function UserProfile({ user }) {
  return (
    <div className="user-profile">
      <h1>{user.name}</h1>
    </div>
  );
}

function UserProfileContainer({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    userApi.fetchUser(userId).then(data => {
      if (userValidation.canViewProfile(data)) setUser(data);
    });
  }, [userId]);

  if (!user) return <div>Loading...</div>;
  return <UserProfile user={user} />;
}
```

### Separating data from presentation (a full example with a form)

```javascript
// Data layer
class UserService {
  async getUser(id) {
    const response = await fetch(`/api/users/${id}`);
    const data = await response.json();
    return { id: data.user_id, name: data.full_name, email: data.email_address };
  }

  async updateUser(id, updates) {
    return fetch(`/api/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
  }
}

// Business logic
class UserValidator {
  static validate(user) {
    const errors = {};
    if (!user.name || user.name.length < 2) errors.name = 'Name must be at least 2 characters';
    if (!user.email?.includes('@')) errors.email = 'Valid email required';
    return { isValid: Object.keys(errors).length === 0, errors };
  }
}

// Presentation
function UserForm({ user, errors, onSubmit, onChange }) {
  return (
    <form onSubmit={onSubmit}>
      <input value={user.name} onChange={e => onChange('name', e.target.value)} />
      {errors.name && <span className="error">{errors.name}</span>}
      <input value={user.email} onChange={e => onChange('email', e.target.value)} />
      {errors.email && <span className="error">{errors.email}</span>}
      <button type="submit">Save</button>
    </form>
  );
}

// Container
function UserFormContainer({ userId }) {
  const [user, setUser] = useState({ name: '', email: '' });
  const [errors, setErrors] = useState({});

  useEffect(() => { new UserService().getUser(userId).then(setUser); }, [userId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validation = UserValidator.validate(user);
    if (!validation.isValid) { setErrors(validation.errors); return; }
    await new UserService().updateUser(userId, user);
  };

  return <UserForm user={user} errors={errors} onSubmit={handleSubmit}
    onChange={(field, value) => setUser(prev => ({ ...prev, [field]: value }))} />;
}
```

### Separating business logic from framework code

**❌ Mixed:**

```javascript
function useShoppingCart() {
  const [items, setItems] = useState([]);

  const addItem = (product) => {
    setItems(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item => item.id === product.id
          ? { ...item, quantity: item.quantity + 1 } : item);
      }
      return [...prev, { ...product, quantity: 1 }];
    });
  };

  return { items, addItem };
}
```

**✅ Separated — the cart logic as a React-independent class:**

```javascript
class Cart {
  constructor(items = []) { this.items = items; }

  addItem(product) {
    const existing = this.items.find(item => item.id === product.id);
    if (existing) {
      return new Cart(this.items.map(item => item.id === product.id
        ? { ...item, quantity: item.quantity + 1 } : item));
    }
    return new Cart([...this.items, { ...product, quantity: 1 }]);
  }

  getTotal() {
    return this.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  }
}

function useShoppingCart() {
  const [cart, setCart] = useState(() => new Cart());
  return {
    items: cart.items,
    total: cart.getTotal(),
    addItem: (product) => setCart(prev => prev.addItem(product))
  };
}
```

### Separating styles from component logic

**❌ Mixed:**

```javascript
function Button({ onClick, children }) {
  return (
    <button onClick={onClick}
      style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white' }}>
      {children}
    </button>
  );
}
```

**✅ Separated (CSS Modules):**

```javascript
import styles from './Button.module.css';

function Button({ onClick, children }) {
  return <button onClick={onClick} className={styles.button}>{children}</button>;
}

/* Button.module.css */
.button { padding: 10px 20px; background-color: #007bff; color: white; }
.button:hover { background-color: #0056b3; }
```

## Advantages

- "When I open a file, I know exactly what I'm looking at—it's handling data, managing business rules, or rendering UI, not all three."
- Testing becomes simpler — each layer testable independently.
- The code is actually reusable (a pure validation function works in any context).
- "Changes stop cascading. Update how data is fetched without touching components" — a change in the data layer does not require touching UI components.
- Teams can work in parallel on different layers without getting in each other's way.

## Disadvantages / tradeoffs

- "More files means more cognitive overhead navigating between layers" — more files to open to understand one feature.
- The team must agree together where the layer boundaries lie — otherwise the split will be inconsistent.
- A conflict between layer separation and code colocation (keeping related things close together) — these are opposing forces, you cannot maximize both at once.
- "Debugging gets trickier when bugs span multiple layers" — a bug passing through three layers requires tracing it through three files.
- Perfect separation is impossible/not worth it in practice — there is always some compromise.
- A coordinating component (container) can over time become a mini God Object if it coordinates too many layers at once.

## Related patterns

- [Single Responsibility](single-responsibility.md) — Fundamentals.
- [Presentational vs. Container](../components/presentational-vs-container.md) — Components.
- Separation of Concerns — Wikipedia.
- MVC Pattern — Wikipedia.
- SOLID — Wikipedia.

## When to use / when NOT to use

Layer the code (data/logic/presentation/styles) when these layers really change **at different frequencies and for different reasons** — that is the core of SoC, not a split "for tidiness". If the validation logic changes independently of what the form looks like, separating them pays off.

For a very small, one-off component (one file, a dozen or so lines, no plans for development) a full split into 4 layers is overkill — the cost of indirection (more files, more imports) exceeds the gain. Find the level of separation proportional to the real complexity and the expected volatility of the code, not the maximum theoretically possible.
