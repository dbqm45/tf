# Przykłady przeglądów

## 1. Przegląd planu z obietnicą bez fazy
**Plan kroku** „eksport zamówień do CSV”: stan końcowy „admin pobiera plik do 50 tys. wierszy w < 10 s, plik nie
zawiera danych osobowych”; fazy: 1) endpoint, 2) przycisk w panelu, 3) testy.
**Raport (fragment):**
```
Ugruntowanie: 4/5 ścieżek (brak src/admin/ExportButton.tsx — plan zakłada istniejący komponent), 2/2 symbole, TL;DR zgodne
| ID | Waga | Wpływ | Wymiar | Miejsce | Ustalenie | Poprawka |
| P1 | krytyczne | niski | spójność | Stan końcowy ↔ Faza 1 | „bez danych osobowych” — żadna faza nie usuwa pól email i telefon | dodaj w fazie 1 listę kolumn eksportu i test, że email nie występuje |
| P2 | ostrzeżenie | średni | ślepe plamy | Faza 1 | 50 tys. wierszy w pamięci — brak strumieniowania i limitu czasu | (A, rekomendowane) strumień CSV · (B) zadanie w tle z linkiem — większy zakres |
| P3 | ostrzeżenie | niski | wykonalność | Faza 2 | ścieżka komponentu nie istnieje | popraw ścieżkę albo dopisz utworzenie komponentu |
Werdykt: do poprawy
```

## 2. Dobry plan — krótki raport
```
Ugruntowanie: 5/5 ścieżek, 3/3 symbole, TL;DR zgodne z planem
Wymiary: zgodność ze stanem końcowym ✓ · oszczędność ✓ · architektura ✓ · ślepe plamy ✓ · wykonalność ✓
Ustalenia: brak. Werdykt: gotowy
```
Nie dopisuj obserwacji, żeby raport „wyglądał na pracę”.

## 3. Implementacja z dryfem i brakiem
Plan: 3 fazy, 7 plików. Diff: 9 plików.
```
Zbiory: w planie i w diffie 6 · NADMIAR: src/utils/date.ts, src/config/flags.ts · BRAK: db/migrations/0042_status.sql
| F1 | krytyczne | średni | zgodność z planem | db/migrations/ | brak zaplanowanej migracji statusu; kod czyta kolumnę, której nie ma | dopisz migrację z planu (expand) przed scaleniem |
| F2 | ostrzeżenie | niski | dyscyplina zakresu | src/config/flags.ts:3 | nowa flaga poza planem; plan wyklucza zmiany konfiguracji | usuń albo dopisz do planu jako odstępstwo |
| F3 | obserwacja | niski | spójność | src/utils/date.ts | helper dla zaplanowanego kodu — nieszkodliwy dodatek | — |
Kryteria: npm test → 61 passed; npm run typecheck → 2 errors (wynik dosłownie w raporcie)
Werdykt: odrzucone (F1 krytyczne + typecheck)
```

## 4. Triaż z lekcją
Ustalenie F3 (ostrzeżenie, wpływ niski): „ręczne sprawdzanie `userId` w akcji serwerowej zamiast wspólnego strażnika”.
Człowiek: „zapisz jako lekcję”. Agent proponuje wpis:
```
- 2026-10-10 **nowe akcje serwerowe używają wspólnego strażnika autoryzacji** — Kontekst: src/actions/** ·
  Zamiast tego: requireUser() z src/auth/guard.ts · Dotyczy: realizacja
```
i pyta: „Zastosować też poprawkę w `actions/deck.ts:12` teraz?” — dopiero odpowiedź człowieka zamyka ustalenie.
