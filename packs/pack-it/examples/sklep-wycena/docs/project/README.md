<!-- WYGENEROWANO przez .claude/hooks/project_record.py — nie edytuj ręcznie -->
# Dziennik projektu

**Bieżąca faza:** Przeglądy  ·  **Do akceptacji:** 0  ·  [Dziennik zdarzeń](journal.md)  ·  [Rejestr decyzji](decisions.md)

| Faza | Artefakt | Status | Wersja | Autor | Aktualizacja | TL;DR |
|---|---|---|---|---|---|---|
| Wymagania | [Wymagania: wycena zamówienia](03-requirements/requirements.md) | accepted | 1 | ewa | 2026-09-22 | Rabat ilościowy przy wycenie pozycji zamówienia: progi 10 i 50 sztuk, kwoty w groszach. |
| Plan | [Plan testów: wycena pozycji zamówienia — rabat ilościowy (H1)](05-plan/test-plan.md) | draft | 1 | kasia | 2026-09-27 | 14 przypadków testowych (clean-room, bez wglądu w src/pricing.ts) pokrywających H1-AC1..AC5: klasy równoważności i |
| Przeglądy | [Zgłoszenia defektów: wycena pozycji zamówienia — rabat ilościowy (H1)](07-review/defekty.md) | draft | 1 | kasia | 2026-09-27 | Automatyzacja planu TC-001..TC-014 (src/pricing.spec.ts) wykryła 2 defekty w src/pricing.ts: (1) próg rabatu 5%/10% |

## Ostatnie przekazanie — z [07-review/defekty.md](07-review/defekty.md)

Do decyzji: poprawka `discountRate` (`>=` zamiast `>`) oraz dodanie walidacji `Number.isInteger(quantity)` w
`orderTotal` (z jednoznacznym mechanizmem błędu — patrz otwarte pytanie niżej). Po poprawce zdjąć `it.fails` →
`it` w `src/pricing.spec.ts` (TC-003, TC-008, TC-012, TC-013).

## Ostatnie zdarzenia

| Kiedy | Kto | Faza | Zdarzenie |
|---|---|---|---|
| 2026-09-27 08:56 | system | meta | Utworzono dziennik projektu (docs/project/) |
| 2026-09-27 08:59 | kasia | plan | Zaprojektowano plan testów wyceny (rabat ilościowy) |
| 2026-09-27 09:01 | kasia | plan | Zautomatyzowano testy wyceny wg planu TC-001..TC-014 |
| 2026-09-27 09:01 | kasia | review | Zgłoszono 2 defekty (progi rabatu 10 szt., walidacja całkowitości qty) w docs/project/07-review/defekty.md |
