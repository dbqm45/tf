# Plan: schemat rekomendacji triażu z kontraktu pdi 0.6.0 (F3, domknięcie)

Data: 2026-10-26 · Status: zrobione (kroki 1–5), commit i PR na prośbę człowieka · Gałąź: `claude/great-hypatia-angvam`
Źródło: tf `docs/plans/2026-10-26-f3-triaz-prb.md` (schemat zdefiniowany w tf jako propozycja do kontraktu); pdi
`docs/plan-f3-rekomendacja-triazu.md` (kontrakt 0.6.0: `triage-recommendation.schema.json`, osobny PR w pdi).

## TL;DR
Schemat rekomendacji triażu jest od 0.6.0 w kontrakcie pdi. tf przestaje go definiować: obok `triage_pdi.py` leży
kopia z kontraktu (jak `problem.schema.json` i `release-plan.schema.json`), a kopia w `tests/fixtures/pdi-contract/`
z testem zgodności pilnuje, że obie są te same. Rekomendacja ma `contract_version` 0.6.0. Wyjście skryptu się nie
zmienia — pola są te same; kontrakt dodaje warunek, który skrypt już spełnia (`executor` → `tf_state`).

## Decyzje
- **Kopie kontraktu w fixtures → 0.6.0** (`VERSION`, schematy zgłoszenia i planu wydania, przykłady): w 0.5.0 i 0.6.0
  zmieniły się w nich tylko tytuły. Nowe: `triage-recommendation.schema.json` i przykład `triage-recommendation.json`.
- **Jedna wersja kontraktu w tf — 0.6.0, także w zdarzeniach** (`phase_run.py`, `metric_watch.py`): testy
  wiążą wersję wysłanego zdarzenia z przykładem z kontraktu (M-3), a treść `gate.requested` i `metric.breached`
  w 0.5.0 i 0.6.0 się nie zmieniła; pdi sprawdza wersję wzorcem, więc przyjmuje każdą. (Zmiana planu w trakcie:
  pierwotnie zdarzenia miały zostać przy 0.4.0.)
- **Walidator tf** (`decision_record.validate`) musi obsłużyć schemat z kontraktu (`enum` w `then.properties`
  bez `type`, `required` w `if`): dziś sprawdza `enum` tylko przy `type: string` — poprawka z testem.

## Kolejność i testy
1. Kopie kontraktu 0.6.0 w `modes/mode-pdi/tests/fixtures/pdi-contract/` (bez zmian względem pdi).
2. Czerwone testy `test_triage_pdi.py`: schemat rekomendacji obok skryptu = kopia z kontraktu; przykład z kontraktu
   przechodzi walidator tf; `executor human` z `tf_state ready-for-agent` → błąd; `contract_version` 0.6.0.
   `test_decision_record.py`: wersja kopii 0.6.0.
3. Kod: kopie schematów obok skryptów, `CONTRACT = "0.6.0"` w `triage_pdi.py` i `CONTRACT_VERSION` w
   `phase_run.py` (G-2 w `test_phase_run.py` → 0.6.0), `enum` bez `type` w walidatorze.
4. Treść: `pdi-decisions` (schemat z kontraktu, nie propozycja; scenariusz ewaluacji najpierw), plan F3 (odnośnik).
5. Bramki: `workspace.py check --packs mode-pdi` i `all`; `refs`; testy repo; `skill_gate.py pdi-decisions`,
   `sync-gate`; tytuł przez `check_commit_message.py`.
