# Klocki domenowe w Go — przetestowane przykłady

Moduł sprawdzony 2026-10-23: `gofmt -l` (bez uwag), `go vet ./...` i `go test ./...` na go1.22.0 i go1.27.3
(dyrektywa `go 1.22` — przykłady działają w całym zakresie skilla). Pliki skopiowane bez zmian.

## Spis treści
- go.mod
- money/money.go — obiekt wartości (kwota)
- money/money_test.go
- availability/availability.go — identyfikator, błędy odrzucenia, warianty stanu, zdarzenia, agregat, port repozytorium
- availability/availability_test.go — test tabelaryczny, errors.Is / errors.As

## go.mod
```go
module example.com/blocks

go 1.22
```

## money/money.go
```go
// Package money: kwota jako obiekt wartości — jednostki minimalne (grosze) w int64, waluta w typie.
package money

import (
	"errors"
	"fmt"
)

var ErrCurrencyMismatch = errors.New("money: różne waluty")

type Currency string

const PLN Currency = "PLN"

// Money jest porównywalne (==) i niezmienne: pola nieeksportowane, operacje zwracają nową wartość.
type Money struct {
	minor    int64 // grosze, centy
	currency Currency
}

func New(minor int64, c Currency) (Money, error) {
	if c == "" {
		return Money{}, errors.New("money: brak waluty")
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
		t.Fatalf("chcę ErrCurrencyMismatch, mam %v", err)
	}
	if x, _ := New(500, PLN); x != (Money{minor: 500, currency: PLN}) {
		t.Fatal("Money ma być porównywalne ==")
	}
}
```

## availability/availability.go
```go
// Package availability: agregat dostępności zasobu z maszyną stanów, wynikiem operacji i zdarzeniami.
package availability

import (
	"errors"
	"fmt"
	"time"
)

// ResourceID — identyfikator jako typ nazwany, nie goły string.
type ResourceID string

// Odrzucenia biznesowe — błędy wartownicze; wywołujący sprawdza errors.Is.
var (
	ErrSlotTaken = errors.New("availability: termin zajęty")
	ErrDisabled  = errors.New("availability: zasób wyłączony")
)

// ConflictError niesie szczegóły odrzucenia; Unwrap pozwala na errors.Is(err, ErrSlotTaken).
type ConflictError struct {
	Resource  ResourceID
	BlockedBy string
}

func (e *ConflictError) Error() string {
	return fmt.Sprintf("zasób %s zajęty przez %s", e.Resource, e.BlockedBy)
}
func (e *ConflictError) Unwrap() error { return ErrSlotTaken }

// state — warianty jako interfejs z metodą nieeksportowaną (zamknięty zbiór w pakiecie).
type state interface{ isState() }

type Free struct{}
type Blocked struct{ By string }
type Disabled struct{}

func (Free) isState()     {}
func (Blocked) isState()  {}
func (Disabled) isState() {}

// Event — zdarzenia w czasie przeszłym.
type Event interface{ isEvent() }

type ResourceBlocked struct {
	Resource ResourceID
	By       string
	At       time.Time
}

func (ResourceBlocked) isEvent() {}

// ResourceAvailability — agregat: stan prywatny, zmiana tylko metodami biznesowymi.
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
			return nil // idempotentnie
		}
		return &ConflictError{Resource: r.id, BlockedBy: s.By}
	case Disabled:
		return ErrDisabled
	default:
		panic(fmt.Sprintf("nieobsłużony stan %T", s)) // błąd programisty, nie odrzucenie biznesowe
	}
}

// PullEvents oddaje zdarzenia do publikacji (np. przez outbox) i czyści listę.
func (r *ResourceAvailability) PullEvents() []Event {
	ev := r.events
	r.events = nil
	return ev
}

func (r *ResourceAvailability) Version() int { return r.version }

// Repository — port w pakiecie domeny; adapter (SQL) w infrastrukturze.
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
		{"wolny → zablokowany", func(*ResourceAvailability) {}, "anna", nil},
		{"zajęty przez kogoś innego", func(r *ResourceAvailability) { _ = r.Block("jan", now) }, "anna", ErrSlotTaken},
		{"ponownie przez tę samą osobę", func(r *ResourceAvailability) { _ = r.Block("anna", now) }, "anna", nil},
		{"wyłączony", func(r *ResourceAvailability) { r.state = Disabled{} }, "anna", ErrDisabled},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			r := New("sala-1")
			tc.setup(r)
			err := r.Block(tc.by, now)
			if !errors.Is(err, tc.wantErr) {
				t.Fatalf("Block() = %v, chcę %v", err, tc.wantErr)
			}
		})
	}
}

func TestConflictDetails(t *testing.T) {
	r := New("sala-1")
	_ = r.Block("jan", time.Now())
	err := r.Block("anna", time.Now())
	var ce *ConflictError
	if !errors.As(err, &ce) || ce.BlockedBy != "jan" {
		t.Fatalf("chcę ConflictError z BlockedBy=jan, mam %v", err)
	}
	if got := len(r.PullEvents()); got != 1 {
		t.Fatalf("zdarzeń: %d, chcę 1", got)
	}
}
```
