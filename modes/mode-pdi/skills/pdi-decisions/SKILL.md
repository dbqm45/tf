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
   `decisions.md` (status `draft`, nagłówek zgodny z `contract/change.schema.json`) i planem wydania `release.yaml`
   (kontrakt 0.4.0, `contract/release-plan.schema.json`). Istniejący katalog → błąd,
   nic nie jest nadpisywane. Klucze tylko w kształcie `[A-Z][A-Z0-9]+-[0-9]+`; numerów nie wymyślasz — podaje je pdi
   albo człowiek.
2. Wypełniasz `intent.md` (problem, warianty, wybrany wariant, metryki, poza zakresem), potem `plan.md` (cięcia TSK
   z linią wydania, flagą, wartością, plikami i weryfikacją; klucze cięć w `tasks` nagłówka — tylko w `plan.md`)
   i `release.yaml`: `mvp` (linia R1, wynik i metryka z `intent.md`), linie R1…Rn z TSK, flagi z właścicielem,
   `remove_by` i etapami `rollout` (kryterium wyjścia, minimalny czas) — według planu cięć (core-delivery-lifecycle,
   `.claude/skills/core-delivery-lifecycle/references/plan-ciec.md`).
3. Po każdej zmianie nagłówka albo planu wydania: `decision_record.py check` — wykrywa brak `change`, niezgodność
   z katalogiem, nieznane pola i wartości, `tasks` poza planem, złe klucze i daty; w `release.yaml` błędy schematu
   kontraktu, `mvp.release` spoza linii, TSK w dwóch liniach albo różne od `plan.md` (także kolumny „Wydanie”
   i „Flaga”), flagę bez etapów lub `remove_by`. Zmiana założona bez `release.yaml` nie jest błędem.

Dziennik faz całego projektu (`docs/project/0N-*`) prowadzisz jak dotąd (core-project-record); dziennik zmiany go
nie zastępuje.

## Decyzja
Decyzja to rozstrzygnięcie człowieka lub bramki (B1–B6): wybór wariantu, zgoda, odrzucenie, wyjątek. Nie zostawiasz
jej tylko w treści odpowiedzi — ale też nie decydujesz sam, co jest decyzją (tak wymaga rejestr pdi).
1. **Szkic do zatwierdzenia:** pokaż człowiekowi: co (jedno zdanie), dlaczego (1–5 zdań, tylko z rozmowy — czego
   brakuje, o to zapytaj), kto zdecydował, rodzaj (`product`, `technical`, `process`, `triage`, `intent`, `gate`,
   `other`). Zapisujesz dopiero po jego „tak”.
2. **Wpis lokalny:** `decision_record.py decision add CHG-12 --statement "…" --why "…" --kind product --by "…"`
   (opcjonalnie `--source-kind slack|jira|…`, `--drafted-by human`, `--date`) → `CHG-12/Dn` w `decisions.md`,
   `id` puste, `wyslano: nie`.
3. **Rejestr pdi:** jeśli w sesji jest narzędzie MCP `record_decision` serwera pdi, `decision_record.py decision pending
   --change CHG-12` daje gotowe argumenty; wywołaj je, a zwrócony numer zapisz: `decision mark CHG-12/Dn --id DEC-41`.
   Zanim zaproponujesz rozwiązanie w obszarze już rozstrzyganym, sprawdź `find_decisions`.
4. **Bez serwera pdi** (narzędzia nie ma albo nie odpowiada): nie wypychasz, nie nadajesz numeru, nie zgadujesz. Wpis
   zostaje niewysłany; mówisz człowiekowi, że czeka. Gdy serwer wróci: `decision pending`, `record_decision`, `mark`
   (ponowienie identycznego zapisu rejestr zwraca jako istniejący wpis — bez duplikatów).
5. Decyzja zmienia wcześniejszą → w rejestrze `supersede_decision` (nie nowa, sprzeczna decyzja), w repo stary
   artefakt dostaje `superseded`.

Eksport wszystkich decyzji projektu (z numerem i stanem wysłania): `decision_record.py decision export`.
`decision_record.py check` sprawdza też wpisy decyzji (ref, numer, rodzaj, źródło, daty, `wyslano: tak` bez numeru).

## Przykład
Właściciel: „W CHG-12 eksport do CSV zamiast XLSX, klienci i tak otwierają go w arkuszu”. Pokazujesz szkic
(co, dlaczego, kto, rodzaj `product`), po zgodzie: `decision add CHG-12 …` → `CHG-12/D1`; `decision pending`,
`record_decision` → `DEC-41`; `decision mark CHG-12/D1 --id DEC-41`. Bez serwera: wpis `CHG-12/D1` z pustym `id`,
`wyslano: nie` i informacja dla człowieka.
