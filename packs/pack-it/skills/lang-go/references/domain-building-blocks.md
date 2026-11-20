# Domain building blocks in Go — a tested example

> **Contents:** go.mod · money/money.go · money/money_test.go · lending/lending.go · lending/lending_test.go

The domain is a **neighbourhood tool library** (the same one as in the Java and TypeScript skills): members borrow
tools, a tool can be on the shelf, lent or withdrawn. Checked 2026-11-20 with **go1.22.0 and go1.27.3**: `gofmt -l`
empty, `go vet ./...` clean, `go test ./...` passes. The code uses nothing newer than the `go 1.22` directive allows.

Files:
- go.mod — the module, `go 1.22`
- money/money.go — amount as a value object (minor units, parsing without `float64`, exact split)
- money/money_test.go — table-driven tests
- lending/lending.go — typed identifiers, rejection errors (sentinels and a typed error), state variants, events,
  the `Tool` aggregate, the repository port
- lending/lending_test.go — the lending sequence as a table, `errors.Is` / `errors.As`

Design choices:
- A business rejection is an `error` value returned from the method: a sentinel (`ErrWithdrawn`) when the caller only
  needs the kind, a typed error (`*OnLoanError` with `Unwrap`) when it also needs data. `panic` only for programmer
  errors (an unknown state, `Split(0)`).
- The state is an interface with an unexported marker method, so variants cannot be added outside the package; a type
  `switch` handles them. The compiler does not check exhaustiveness: the `default` branch panics, and the tests
  catch a missed variant.
- `PullEvents` hands over the slice and resets the buffer; `version` grows with every recorded event, and the SQL
  adapter uses it in `UPDATE … WHERE version = $n`.

## go.mod
```text
module example.com/toollibrary

go 1.22
```

## money/money.go
```go
// Package money: an amount as a value object — minor units in int64, the currency next to it.
package money

import (
	"errors"
	"fmt"
	"regexp"
	"strconv"
)

// Currency is an ISO 4217 code; the known ones are constants.
type Currency string

const (
	PLN Currency = "PLN"
	EUR Currency = "EUR"
)

var (
	ErrCurrencyMismatch = errors.New("money: currency mismatch")
	ErrInvalidAmount    = errors.New("money: invalid amount")
)

// Money is immutable (unexported fields, methods on a value) and comparable with ==.
type Money struct {
	minor    int64
	currency Currency
}

var amountPattern = regexp.MustCompile(`^(-)?(\d+)(?:[.,](\d{1,2}))?$`)

// Parse reads "12", "12.5" or "12,50" without passing through float64.
func Parse(text string, c Currency) (Money, error) {
	m := amountPattern.FindStringSubmatch(text)
	if m == nil || c == "" {
		return Money{}, fmt.Errorf("%w: %q %s", ErrInvalidAmount, text, c)
	}
	frac := m[3]
	for len(frac) < 2 {
		frac += "0"
	}
	minor, err := strconv.ParseInt(m[2]+frac, 10, 64)
	if err != nil {
		return Money{}, fmt.Errorf("%w: %q: %v", ErrInvalidAmount, text, err)
	}
	if m[1] == "-" {
		minor = -minor
	}
	return Money{minor: minor, currency: c}, nil
}

// FromMinor builds an amount from minor units (grosze, cents).
func FromMinor(minor int64, c Currency) Money { return Money{minor: minor, currency: c} }

func (m Money) Minor() int64       { return m.minor }
func (m Money) Currency() Currency { return m.currency }

func (m Money) String() string {
	sign, units := "", m.minor
	if units < 0 {
		sign, units = "-", -units
	}
	return fmt.Sprintf("%s%d.%02d %s", sign, units/100, units%100, m.currency)
}

// Add returns a new amount; different currencies are an error, never a silent conversion.
func (m Money) Add(o Money) (Money, error) {
	if m.currency != o.currency {
		return Money{}, fmt.Errorf("%w: %s + %s", ErrCurrencyMismatch, m.currency, o.currency)
	}
	return Money{minor: m.minor + o.minor, currency: m.currency}, nil
}

// Split divides the amount into n shares that add up exactly; leftover minor
// units go to the first shares, with the sign of the amount.
func (m Money) Split(n int) []Money {
	if n < 1 {
		panic("money: Split needs n >= 1") // a programmer error, not a business case
	}
	base, rest := m.minor/int64(n), m.minor%int64(n) // Go truncates toward zero
	step := int64(1)
	if rest < 0 {
		step, rest = -1, -rest
	}
	shares := make([]Money, n)
	for i := range shares {
		units := base
		if int64(i) < rest {
			units += step
		}
		shares[i] = Money{minor: units, currency: m.currency}
	}
	return shares
}
```

## money/money_test.go
```go
package money

import (
	"errors"
	"slices"
	"testing"
)

func mustParse(t *testing.T, s string, c Currency) Money {
	t.Helper()
	m, err := Parse(s, c)
	if err != nil {
		t.Fatalf("Parse(%q): %v", s, err)
	}
	return m
}

func TestParse(t *testing.T) {
	tests := []struct {
		in      string
		minor   int64
		wantErr bool
	}{
		{"12", 1200, false},
		{"12,5", 1250, false},
		{"0.07", 7, false},
		{"-3.10", -310, false},
		{"1.234", 0, true},
		{"12.", 0, true},
		{"", 0, true},
	}
	for _, tt := range tests {
		t.Run(tt.in, func(t *testing.T) {
			got, err := Parse(tt.in, PLN)
			if tt.wantErr {
				if !errors.Is(err, ErrInvalidAmount) {
					t.Fatalf("Parse(%q) error = %v, want ErrInvalidAmount", tt.in, err)
				}
				return
			}
			if err != nil || got.Minor() != tt.minor {
				t.Fatalf("Parse(%q) = %d, %v; want %d", tt.in, got.Minor(), err, tt.minor)
			}
		})
	}
}

func TestAddIsExact(t *testing.T) {
	sum, err := mustParse(t, "0.10", EUR).Add(mustParse(t, "0.20", EUR))
	if err != nil || sum != mustParse(t, "0.30", EUR) {
		t.Fatalf("0.10 + 0.20 = %v, %v", sum, err)
	}
}

func TestAddRejectsOtherCurrency(t *testing.T) {
	_, err := FromMinor(100, PLN).Add(FromMinor(100, EUR))
	if !errors.Is(err, ErrCurrencyMismatch) {
		t.Fatalf("error = %v, want ErrCurrencyMismatch", err)
	}
}

func TestSplit(t *testing.T) {
	tests := []struct {
		name  string
		minor int64
		n     int
		want  []int64
	}{
		{"100 into 3", 10000, 3, []int64{3334, 3333, 3333}},
		{"negative", -100, 3, []int64{-34, -33, -33}},
		{"exact", 900, 3, []int64{300, 300, 300}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var got []int64
			for _, s := range FromMinor(tt.minor, PLN).Split(tt.n) {
				got = append(got, s.Minor())
			}
			if !slices.Equal(got, tt.want) {
				t.Fatalf("Split = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestString(t *testing.T) {
	if got := FromMinor(-1205, PLN).String(); got != "-12.05 PLN" {
		t.Fatalf("String = %q", got)
	}
}
```

## lending/lending.go
```go
// Package lending: a lendable tool as an aggregate with a state machine,
// rejection errors, events and a repository port.
package lending

import (
	"context"
	"errors"
	"fmt"
	"time"
)

// Typed identifiers: a MemberID cannot be passed where a ToolID is expected.
type (
	ToolID   string
	MemberID string
)

// Sentinel errors for business rejections; callers use errors.Is.
var (
	ErrOnLoan       = errors.New("lending: tool is on loan")
	ErrNotBorrower  = errors.New("lending: member is not the borrower")
	ErrNotLent      = errors.New("lending: tool is not lent")
	ErrWithdrawn    = errors.New("lending: tool is withdrawn")
	ErrToolNotFound = errors.New("lending: tool not found")
)

// OnLoanError carries who holds the tool; errors.Is(err, ErrOnLoan) still works through Unwrap.
type OnLoanError struct {
	Borrower MemberID
}

func (e *OnLoanError) Error() string {
	return fmt.Sprintf("lending: tool is on loan to %s", e.Borrower)
}
func (e *OnLoanError) Unwrap() error { return ErrOnLoan }

// State variants. The unexported marker method closes the set to this package.
type state interface{ isState() }

type (
	OnShelf struct{}
	Lent    struct {
		Borrower MemberID
		Since    time.Time
	}
	Withdrawn struct {
		By     MemberID
		Reason string
	}
)

func (OnShelf) isState()   {}
func (Lent) isState()      {}
func (Withdrawn) isState() {}

// Events, named in the past tense.
type Event interface{ isEvent() }

type (
	ToolLent struct {
		Tool     ToolID
		Borrower MemberID
		At       time.Time
	}
	ToolReturned struct {
		Tool     ToolID
		Borrower MemberID
		At       time.Time
	}
	ToolWithdrawn struct {
		Tool   ToolID
		By     MemberID
		Reason string
		At     time.Time
	}
)

func (ToolLent) isEvent()      {}
func (ToolReturned) isEvent()  {}
func (ToolWithdrawn) isEvent() {}

// Tool is the aggregate: state changes only through business methods.
type Tool struct {
	id      ToolID
	state   state
	version int
	pending []Event
}

func NewTool(id ToolID) *Tool { return &Tool{id: id, state: OnShelf{}} }

func (t *Tool) ID() ToolID   { return t.id }
func (t *Tool) Version() int { return t.version }

// Lend returns nil on success, ErrWithdrawn, or *OnLoanError.
func (t *Tool) Lend(member MemberID, at time.Time) error {
	switch s := t.state.(type) {
	case OnShelf:
		t.state = Lent{Borrower: member, Since: at}
		t.record(ToolLent{Tool: t.id, Borrower: member, At: at})
		return nil
	case Lent:
		return &OnLoanError{Borrower: s.Borrower}
	case Withdrawn:
		return ErrWithdrawn
	default:
		panic(fmt.Sprintf("lending: unknown state %T", s))
	}
}

// GiveBack returns nil, ErrNotBorrower, ErrNotLent or ErrWithdrawn.
func (t *Tool) GiveBack(member MemberID, at time.Time) error {
	switch s := t.state.(type) {
	case Lent:
		if s.Borrower != member {
			return ErrNotBorrower
		}
		t.state = OnShelf{}
		t.record(ToolReturned{Tool: t.id, Borrower: member, At: at})
		return nil
	case OnShelf:
		return ErrNotLent
	case Withdrawn:
		return ErrWithdrawn
	default:
		panic(fmt.Sprintf("lending: unknown state %T", s))
	}
}

// Withdraw is a staff decision and cannot be refused.
func (t *Tool) Withdraw(by MemberID, reason string, at time.Time) {
	t.state = Withdrawn{By: by, Reason: reason}
	t.record(ToolWithdrawn{Tool: t.id, By: by, Reason: reason, At: at})
}

// PullEvents hands over the recorded events and empties the buffer.
func (t *Tool) PullEvents() []Event {
	out := t.pending
	t.pending = nil
	return out
}

func (t *Tool) record(e Event) {
	t.pending = append(t.pending, e)
	t.version++
}

// Repository is the port; the SQL adapter lives in an infrastructure package
// and checks expectedVersion in its UPDATE (optimistic locking).
type Repository interface {
	Get(ctx context.Context, id ToolID) (*Tool, error) // ErrToolNotFound when missing
	Save(ctx context.Context, t *Tool, expectedVersion int) error
}
```

## lending/lending_test.go
```go
package lending

import (
	"errors"
	"reflect"
	"testing"
	"time"
)

func TestLendingSequence(t *testing.T) {
	var (
		ola    = MemberID("m-0042")
		kuba   = MemberID("m-0107")
		staff  = MemberID("s-0001")
		nine   = time.Date(2026, 11, 20, 9, 0, 0, 0, time.UTC)
		ten    = nine.Add(time.Hour)
		eleven = ten.Add(time.Hour)
	)
	tool := NewTool("T-217")

	steps := []struct {
		name    string
		act     func() error
		wantErr error // nil means success
	}{
		{"first loan", func() error { return tool.Lend(ola, nine) }, nil},
		{"rival refused", func() error { return tool.Lend(kuba, ten) }, ErrOnLoan},
		{"stranger cannot return", func() error { return tool.GiveBack(kuba, ten) }, ErrNotBorrower},
		{"return", func() error { return tool.GiveBack(ola, ten) }, nil},
		{"return twice", func() error { return tool.GiveBack(ola, ten) }, ErrNotLent},
		{"withdraw", func() error { tool.Withdraw(staff, "worn chuck", eleven); return nil }, nil},
		{"lend after withdrawal", func() error { return tool.Lend(kuba, eleven) }, ErrWithdrawn},
		{"even staff cannot lend it", func() error { return tool.Lend(staff, eleven) }, ErrWithdrawn},
	}
	for _, s := range steps {
		err := s.act()
		if s.wantErr == nil && err != nil || s.wantErr != nil && !errors.Is(err, s.wantErr) {
			t.Fatalf("%s: error = %v, want %v", s.name, err, s.wantErr)
		}
	}

	if tool.Version() != 3 {
		t.Fatalf("version = %d, want 3", tool.Version())
	}
	want := []Event{
		ToolLent{Tool: "T-217", Borrower: ola, At: nine},
		ToolReturned{Tool: "T-217", Borrower: ola, At: ten},
		ToolWithdrawn{Tool: "T-217", By: staff, Reason: "worn chuck", At: eleven},
	}
	if got := tool.PullEvents(); !reflect.DeepEqual(got, want) {
		t.Fatalf("events = %#v", got)
	}
	if got := tool.PullEvents(); len(got) != 0 {
		t.Fatalf("second pull = %v, want empty", got)
	}
}

func TestOnLoanErrorCarriesBorrower(t *testing.T) {
	tool := NewTool("T-301")
	_ = tool.Lend("m-0042", time.Now())

	err := tool.Lend("m-0107", time.Now())
	var onLoan *OnLoanError
	if !errors.As(err, &onLoan) || onLoan.Borrower != "m-0042" {
		t.Fatalf("errors.As = %v, %+v", err, onLoan)
	}
	if !errors.Is(err, ErrOnLoan) {
		t.Fatal("errors.Is(err, ErrOnLoan) must hold through Unwrap")
	}
}
```

A caller in the HTTP layer maps the errors: `errors.As(err, &onLoan)` → 409 with `onLoan.Borrower` in the message,
`errors.Is(err, lending.ErrWithdrawn)` → 409, `errors.Is(err, lending.ErrToolNotFound)` → 404, anything else → 500.
