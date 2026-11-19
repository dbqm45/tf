# Domain building blocks in Go — tested examples

> **Contents:** go.mod · money/money.go · money/money_test.go · availability/availability.go · availability/availability_test.go

Module checked 2026-10-23: `gofmt -l` (no findings), `go vet ./...` and `go test ./...` on go1.22.0 and go1.27.3
(the `go 1.22` directive — the examples work across the whole range of the skill). Code from the tested project; only comments and message strings were translated to English (after translation: `gofmt -l` clean, `go vet` and `go test ./...` pass, go1.24.7).

## Contents
- go.mod
- money/money.go — value object (amount)
- money/money_test.go
- availability/availability.go — identifier, rejection errors, state variants, events, aggregate, repository port
- availability/availability_test.go — table-driven test, errors.Is / errors.As

## go.mod
```go
module example.com/blocks

go 1.22
```

## money/money.go
```go
// Package money: an amount as a value object — minor units (grosze) in int64, the currency in the type.
package money

import (
	"errors"
	"fmt"
)

var ErrCurrencyMismatch = errors.New("money: different currencies")

type Currency string

const PLN Currency = "PLN"

// Money is comparable (==) and immutable: unexported fields, operations return a new value.
type Money struct {
	minor    int64 // grosze, cents
	currency Currency
}

func New(minor int64, c Currency) (Money, error) {
	if c == "" {
		return Money{}, errors.New("money: missing currency")
	}
	return Money{minor: minor, currency: c}, nil
}

func (m Money) Minor() int64       { return m.minor }
func (m Money) Currency() Currency { return m.currency }
func (m Money) String() string {
	return fmt.Sprintf("%d.%02d %s", m.minor/100, abs(m.minor%100), m.currency)
}

func (m Money) Add(o Money) (Money, error) {
	if m.currency != o.currency {
		return Money{}, fmt.Errorf("%w: %s + %s", ErrCurrencyMismatch, m.currency, o.currency)
	}
	return Money{minor: m.minor + o.minor, currency: m.currency}, nil
}

func abs(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}
```

## money/money_test.go
```go
package money

import (
	"errors"
	"testing"
)

func TestAdd(t *testing.T) {
	a, _ := New(1999, PLN)
	b, _ := New(1, PLN)
	sum, err := a.Add(b)
	if err != nil || sum.String() != "20.00 PLN" {
		t.Fatalf("Add = %v, %v", sum, err)
	}
	eur, _ := New(100, "EUR")
	if _, err := a.Add(eur); !errors.Is(err, ErrCurrencyMismatch) {
		t.Fatalf("want ErrCurrencyMismatch, got %v", err)
	}
	if x, _ := New(500, PLN); x != (Money{minor: 500, currency: PLN}) {
		t.Fatal("Money must be comparable with ==")
	}
}
```

## availability/availability.go
```go
// Package availability: a resource availability aggregate with a state machine, an operation result and events.
package availability

import (
	"errors"
	"fmt"
	"time"
)

// ResourceID — an identifier as a named type, not a bare string.
type ResourceID string

// Business rejections — sentinel errors; the caller checks errors.Is.
var (
	ErrSlotTaken = errors.New("availability: slot taken")
	ErrDisabled  = errors.New("availability: resource disabled")
)

// ConflictError carries the rejection details; Unwrap allows errors.Is(err, ErrSlotTaken).
type ConflictError struct {
	Resource  ResourceID
	BlockedBy string
}

func (e *ConflictError) Error() string {
	return fmt.Sprintf("resource %s taken by %s", e.Resource, e.BlockedBy)
}
func (e *ConflictError) Unwrap() error { return ErrSlotTaken }

// state — variants as an interface with an unexported method (a set closed within the package).
type state interface{ isState() }

type Free struct{}
type Blocked struct{ By string }
type Disabled struct{}

func (Free) isState()     {}
func (Blocked) isState()  {}
func (Disabled) isState() {}

// Event — events in the past tense.
type Event interface{ isEvent() }

type ResourceBlocked struct {
	Resource ResourceID
	By       string
	At       time.Time
}

func (ResourceBlocked) isEvent() {}

// ResourceAvailability — the aggregate: private state, changed only through business methods.
type ResourceAvailability struct {
	id      ResourceID
	state   state
	version int
	events  []Event
}

func New(id ResourceID) *ResourceAvailability {
	return &ResourceAvailability{id: id, state: Free{}}
}

func (r *ResourceAvailability) Block(by string, at time.Time) error {
	switch s := r.state.(type) {
	case Free:
		r.state = Blocked{By: by}
		r.version++
		r.events = append(r.events, ResourceBlocked{Resource: r.id, By: by, At: at})
		return nil
	case Blocked:
		if s.By == by {
			return nil // idempotent
		}
		return &ConflictError{Resource: r.id, BlockedBy: s.By}
	case Disabled:
		return ErrDisabled
	default:
		panic(fmt.Sprintf("unhandled state %T", s)) // a programmer error, not a business rejection
	}
}

// PullEvents hands out the events for publishing (e.g. through an outbox) and clears the list.
func (r *ResourceAvailability) PullEvents() []Event {
	ev := r.events
	r.events = nil
	return ev
}

func (r *ResourceAvailability) Version() int { return r.version }

// Repository — a port in the domain package; the adapter (SQL) in the infrastructure.
type Repository interface {
	Get(id ResourceID) (*ResourceAvailability, error)
	Save(r *ResourceAvailability, expectedVersion int) error
}
```

## availability/availability_test.go
```go
package availability

import (
	"errors"
	"testing"
	"time"
)

func TestBlock(t *testing.T) {
	now := time.Date(2026, 10, 23, 9, 0, 0, 0, time.UTC)
	cases := []struct {
		name    string
		setup   func(*ResourceAvailability)
		by      string
		wantErr error
	}{
		{"free → blocked", func(*ResourceAvailability) {}, "anna", nil},
		{"taken by someone else", func(r *ResourceAvailability) { _ = r.Block("jan", now) }, "anna", ErrSlotTaken},
		{"again by the same person", func(r *ResourceAvailability) { _ = r.Block("anna", now) }, "anna", nil},
		{"disabled", func(r *ResourceAvailability) { r.state = Disabled{} }, "anna", ErrDisabled},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			r := New("room-1")
			tc.setup(r)
			err := r.Block(tc.by, now)
			if !errors.Is(err, tc.wantErr) {
				t.Fatalf("Block() = %v, want %v", err, tc.wantErr)
			}
		})
	}
}

func TestConflictDetails(t *testing.T) {
	r := New("room-1")
	_ = r.Block("jan", time.Now())
	err := r.Block("anna", time.Now())
	var ce *ConflictError
	if !errors.As(err, &ce) || ce.BlockedBy != "jan" {
		t.Fatalf("want ConflictError with BlockedBy=jan, got %v", err)
	}
	if got := len(r.PullEvents()); got != 1 {
		t.Fatalf("events: %d, want 1", got)
	}
}
```
