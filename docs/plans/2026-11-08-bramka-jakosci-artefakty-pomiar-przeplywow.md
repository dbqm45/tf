# Plan: bramka jakości, budżet artefaktów, pomiar przepływów (wnioski z porównania z dev-kitem)

Decyzja człowieka 2026-11-08: zrobić wszystkie trzy. Każdy punkt to osobny PR.

## 1. Bramka jakości przy zakończeniu pracy + blokada testów
**Problem:** `tdd_guard` pilnuje kolejności (najpierw czerwony test), ale nic nie blokuje zakończenia tury
z czerwonym buildem — wychodzi to dopiero w CI. Równoległe uruchomienia testów (agent i bramka) psują wspólny
katalog build (Gradle, Maven) i wyglądają jak regresja.

**Zmiana:**
- `core/hooks/quality_gate.py` na `Stop` i `SubagentStop`:
  - działa tylko z konfiguracją projektu `.claude/quality-gate.json` (`command`, `watch`, `timeout`, `max_blocks`) —
    fabryka nie zna poleceń projektu, więc bez pliku nic nie robi;
  - uruchamia polecenie tylko, gdy zmienił się obserwowany kod (odcisk diffu względem HEAD i nowych plików
    w `watch`); ten sam odcisk po zielonym przebiegu → bez ponownego uruchomienia;
  - czerwony wynik → `{"decision": "block"}` z końcem wyjścia testów; po `max_blocks` (domyślnie 3) blokadach tego
    samego odcisku przepuszcza z komunikatem dla człowieka (ochrona przed pętlą);
  - świadomie czerwona partia: plik `.claude/quality-gate.expected-red` z powodem → przepuszcza;
  - `QG_GATE_DISABLE=1` wyłącza; przekroczenie `timeout` to wynik czerwony z opisem.
- `core/hooks/test_lock.py`: blokada na poziomie maszyny dla repozytorium (`flock`), re-entrant
  (`TF_TEST_LOCK_HELD`), zajęta dłużej niż `QG_LOCK_WAIT` → kod 75 bez uruchamiania; CLI
  `python3 .claude/hooks/test_lock.py -- <polecenie>`; bramka używa tej samej blokady.
- `core/settings.json` (Stop, SubagentStop), opis w `core/CLAUDE.md` i przewodniku.

**Testy (czerwone przed kodem):** `core/tests/test_quality_gate.py` — Q-1…Q-10 (brak konfiguracji, brak zmian,
czerwone → blokada, zielone → zapamiętany odcisk, zmiana poza `watch`, expected-red, ochrona przed pętlą,
wyłączenie, SubagentStop, limit czasu), L-1…L-2 (blokada zajęta → 75, re-entrant).

## 2. Budżet artefaktów w PR
**Problem:** w PR z kodem artefakty przebiegu (plany, raporty, dowody) potrafią być większością diffu (u nich 391
z 486 dodanych linii) — szum w przeglądzie.

**Zmiana:** `core/skills/core-delivery-lifecycle/scripts/pr_budget.py --base main`: dodane linie kodu i artefaktów
(`docs/project/**`, `docs/test/**`, `.claude/runs/**` i wzorce z konfiguracji), werdykt w pierwszej linii; błąd, gdy
pojedynczy artefakt > 600 linii (plan > 300) albo artefakty > 50% dodanych linii przy zmianie kodu. Wpięcie: talos
(krok 4, przed PR) i opis w core-delivery-lifecycle. Testy czerwone przed kodem.

## 3. Pomiar przepływów na tych samych zgłoszeniach
**Problem:** nie mamy danych, czy `mode-pdi` (pełny przepływ) i `talos` (krótki) są lepsze od samego trybu planu
przy rozsądnym koszcie — dev-kit pokazał 7–12× wyższy koszt pełnego przepływu przy porównywalnej jakości.

**Zmiana (bez płatnych przebiegów w tym PR):** protokół i narzędzie: `tools/flow_compare.py` zbiera z gałęzi
przebiegów te same miary (koszt, czas, linie kodu i artefaktów z `pr_budget`, testy, liczba commitów) do tabeli,
a ślepa ocena wg kryteriów z protokołu daje werdykt; raport w `docs/evals/`. Uruchomienie na zgłoszeniach — za zgodą
człowieka z budżetem.
