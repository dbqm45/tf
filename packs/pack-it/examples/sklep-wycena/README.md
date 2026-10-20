# Przykład: testy od wymagań (persona Kasia)

Wejście: zaakceptowane wymagania `docs/project/03-requirements/requirements.md` i kod `src/pricing.ts` z **dwoma celowymi
błędami** (próg `> 10` zamiast „od 10 sztuk włącznie”, brak walidacji ilości niecałkowitej) oraz „lustrzany” test,
który przechodził mimo błędów.

Polecenie: `claude --agent kasia -p "Przygotuj testy dla wyceny zamówienia (src/pricing.ts) zgodnie z wymaganiami w docs/project."`
(bez żadnej wskazówki o błędach).

Co zrobili agenci (Sonnet, koszt $0,95, ~6 min):
1. `kasia-qa-analyst` (clean-room, bez dostępu do kodu) → `docs/project/05-plan/test-plan.md`: 14 przypadków z
   wartościami brzegowymi i oczekiwanym wynikiem policzonym ręcznie z wymagań.
2. `kasia-qa-automation` → `src/pricing.spec.ts` (Vitest + fast-check): 12 zielonych, 4 `it.fails` dokumentujące defekty.
3. `docs/project/07-review/defekty.md` — oba błędy znalezione i zgłoszone; **kod i oczekiwane wartości nietknięte**.

Uruchomienie: `npm i && npm test` (Vitest 5, Node ≥ 22.12).
