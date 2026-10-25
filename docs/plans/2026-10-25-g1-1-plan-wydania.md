# Plan: G1.1 — plan wydania (MVP z metryką, linie wydań, flagi z etapami)

Data: 2026-10-25 · Status: zrobione (kroki 1–6), commit i PR na prośbę człowieka · Gałąź: `claude/great-hypatia-angvam`
Źródło: pdi `docs/plan-g1-g2.md` §5.2 (model), §5.4 (zmiany w tf), §5.8 (G1.1); kontrakt pdi 0.4.0
(`contract/release-plan.schema.json`, `examples/release-plan.json`, `task.schema.json`: pola `release`, `flag`;
README „Konwencje”: plan wydania w repo = `changes/CHG-n/release.yaml`, DG6). Poza zakresem: reguły REL w ci_for_sdlc
(G1.2, G1.4), ShipScope (G1.3), zdarzenia pdi (G1.5), dopisek `Change:` i hook commit-msg (F1 — w tf jeszcze go nie ma).

## TL;DR
Każda zmiana robiona z tf ma sprawdzalny plan wydania: `release.yaml` z MVP (wynik, metryka z progiem i horyzontem),
liniami R1…Rn i flagami z etapami udostępniania i datą usunięcia. `decision_record.py change new` zakłada
`release.yaml`, `check` waliduje go schematem z kontraktu i sprawdza spójność z `plan.md`. Skille: plan cięć z liniami
i flagami, fazy 5 i 8 cyklu dostarczania, MVP w fazie 3 kształtowania wymagań, etapy flag w ciągłym dostarczaniu
i inżynierii wydań, kawałek z flagą w Talosie.

## Decyzje
- **Schemat:** kopia `release-plan.schema.json` obok skryptu (zainstalowany skill nie widzi `tests/`); test pilnuje
  zgodności z kopią w `modes/mode-pdi/tests/fixtures/pdi-contract/` (schemat, przykład z kontraktu, `VERSION` 0.4.0).
- **YAML:** PyYAML z dołączoną kopią `factory/_vendor`, jak `run_report.py` Talosa. Daty z YAML (`2026-12-31`)
  zamieniane na tekst przed walidacją.
- **Walidator:** mały, na podzbiorze JSON Schema użytym w kontrakcie (type, required, additionalProperties, properties,
  items, pattern, minLength, minItems, minimum, enum). Bez nowej zależności.
- **Spójność w `check`** (README kontraktu): `mvp.release` jest wśród linii; identyfikatory linii unikalne; TSK
  w najwyżej jednej linii; zbiór TSK w liniach = `tasks` w nagłówku `plan.md`; TSK flagi należą do linii; każda flaga
  ma etapy (`rollout`) i `remove_by`; kolumny „Wydanie” i „Flaga” w tabeli `plan.md` zgodne z `release.yaml`.
- **Zgodność wstecz:** zmiana bez `release.yaml` (założona przed G1.1) nie jest błędem.
- **Rdzeń bez pdi:** plan wydania żyje obok planu cięć (`05-plan/release.yaml`, ten sam kształt); walidacja skryptem
  tylko w trybie mode-pdi. Rdzeń nie nazywa skilli nakładek (bramka `refs`).
- **Talos:** `Flag: <klucz>` w treści commita kawałka za flagą; `Change: TSK-n` tylko gdy projekt już go używa (F1).

## Kolejność i testy
1. Kopie kontraktu (schemat obok skryptu, fixtures) — bez kodu.
2. Czerwone testy w `modes/mode-pdi/tests/test_decision_record.py`:
   - `change new` tworzy `release.yaml` zgodny ze schematem, świeży dziennik przechodzi `check`;
   - przykład z kontraktu + `plan.md` z tymi samymi TSK przechodzi;
   - `check` wykrywa: błąd schematu (zły klucz TSK, linia `X1`, nieznane pole), `mvp.release` spoza linii, TSK różne
     od `plan.md`, TSK w dwóch liniach, flaga bez etapów, flaga bez `remove_by`, TSK flagi spoza linii, kolumna
     „Wydanie” lub „Flaga” w `plan.md` niezgodna, niepoprawny YAML;
   - zmiana bez `release.yaml` przechodzi; schemat obok skryptu = kopia kontraktu.
   - `test_mode_talos.py`: T-8 (kawałek z flagą, `Flag:` w commicie).
3. Kod `decision_record.py`, szablony `release.yaml` i `plan.md`.
4. Scenariusze ewaluacji (przed treścią): core-delivery-lifecycle, pdi-decisions, proc-requirements-shaping,
   eng-continuous-delivery, ops-release-engineering.
5. Treść skilli i `plan-ciec.md`.
6. Bramki: `workspace.py check --packs all`, `matrix` dla mode-pdi i mode-talos osobno, `refs`, `tests/test_*.py`,
   `skill_gate` zmienionych skilli, `sync-gate`, tytuł przez `check_commit_message.py`.
