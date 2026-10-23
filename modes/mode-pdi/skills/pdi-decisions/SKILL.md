---
name: pdi-decisions
description: Użyj przy decyzji o zmianie (CHG) w projekcie z rejestrem pdi — dziennik zmiany, wpis w decisions.md, record_decision przez MCP.
metadata:
  przeglad: 2027-04-23
  katalog: "Użyj w projekcie z trybem mode-pdi, gdy zapada decyzja o konkretnej zmianie (CHG-n: bramka, odpowiedź właściciela, wybór wariantu) albo trzeba założyć dziennik zmiany ze zgłoszenia (PRB-n) — `decision_record.py change new` tworzy docs/project/changes/CHG-n/ (intent, plan, decisions) zgodnie z kontraktem pdi 0.3.0, decyzja trafia do decisions.md i do rejestru pdi przez MCP record_decision (numer DEC-n nadaje rejestr), bez serwera pdi wpis czeka jako niewysłany. Nie do dziennika faz projektu bez pdi (core-project-record) ani formatu commitów (core-conventional-commits)."
  slowa: "pdi, rejestr decyzji, record_decision, zapisz decyzję, decyzja o zmianie, ustaliliśmy, zdecydowaliśmy, decisions.md, CHG, PRB, DEC, dziennik zmiany, docs/project/changes, zgłoszenie przyjęte, jedno źródło decyzji, bramka B1, bramka B2, kontrakt pdi"
---

# Decyzje w jednym źródle (pdi)

Tryb `mode-pdi` łączy dziennik w repozytorium z rejestrem decyzji pdi. Źródło prawdy o decyzji dotyczącej zmiany
to `docs/project/changes/CHG-n/decisions.md` w repo; pdi ją indeksuje i nadaje numer `DEC-n`. Decyzje bez zmiany
(triaż, odrzucenie zgłoszenia) zapisuje sam pdi. Skrypt: `python3 .claude/skills/pdi-decisions/scripts/decision_record.py`
(dalej `decision_record.py`).

## Dziennik zmiany
Gdy pdi przyjmie zgłoszenie jako zmianę (albo człowiek poda klucz zmiany):
1. `decision_record.py change new CHG-12 --source PRB-34` → `docs/project/changes/CHG-12/` z `intent.md`, `plan.md`,
   `decisions.md` (status `draft`, nagłówek zgodny z `contract/change.schema.json`). Istniejący katalog → błąd,
   nic nie jest nadpisywane. Klucze tylko w kształcie `[A-Z][A-Z0-9]+-[0-9]+`; numerów nie wymyślasz — podaje je pdi
   albo człowiek.
2. Wypełniasz `intent.md` (problem, warianty, wybrany wariant, metryki, poza zakresem), potem `plan.md` (cięcia TSK
   z wartością, plikami i weryfikacją; klucze cięć w `tasks` nagłówka — tylko w `plan.md`).
3. Po każdej zmianie nagłówka: `decision_record.py check` — wykrywa brak `change`, niezgodność z katalogiem,
   nieznane pola i wartości, `tasks` poza planem, złe klucze i daty.

Dziennik faz całego projektu (`docs/project/0N-*`) prowadzisz jak dotąd (core-project-record); dziennik zmiany go
nie zastępuje.

## Decyzja
Decyzja to rozstrzygnięcie człowieka lub bramki (B1–B6): wybór wariantu, zgoda, odrzucenie, wyjątek. Nie zostawiasz
jej tylko w treści odpowiedzi.
1. **Wpis lokalny** w `decisions.md` zmiany, według wzoru w pliku: co (jedno zdanie), kiedy, kto, rodzaj
   (`product`, `technical`, `process`, `triage`, `intent`, `gate`, `other`), dlaczego (1–5 zdań), źródło
   (`claude-cli`, `claude-ai`, `slack`, `jira`, …). Pola `id` puste, `wyslano: nie`.
2. **Rejestr pdi:** jeśli narzędzie MCP `record_decision` jest dostępne w sesji, wywołaj je z tymi samymi polami
   i powiązaniem ze zmianą (`links.chg`), a zwrócony numer wpisz w `id` i ustaw `wyslano: tak`.
3. **Bez serwera pdi** (narzędzia nie ma albo nie odpowiada): nie wypychasz, nie nadajesz numeru, nie zgadujesz.
   Wpis zostaje z pustym `id` i `wyslano: nie`; mówisz człowiekowi, że decyzja czeka na wysłanie.
4. Decyzja zmienia inną → stara dostaje `superseded` (w nagłówku pliku albo we wpisie), nowa wskazuje starą.

## Przykład
Właściciel: „W CHG-12 eksport do CSV zamiast XLSX, klienci i tak otwierają go w arkuszu”. Dopisujesz w
`docs/project/changes/CHG-12/decisions.md` wpis „Eksport do CSV zamiast XLSX” (kto: właściciel produktu, rodzaj
`product`, dlaczego: …, źródło `claude-cli`), wołasz `record_decision`, dostajesz `DEC-41` → `id: DEC-41`,
`wyslano: tak`. Bez serwera: `id:` puste, `wyslano: nie` i informacja dla człowieka.
