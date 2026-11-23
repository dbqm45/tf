# D3 — publikacja decyzji fabryki do indeksu suity (mode-pdi)

**Data:** 2026-11-23 · **Źródło:** pdi `docs/plan-budowy-suity.md` §3a (krok D3), kontrakt di-contract 0.17.0
(`decision.recorded` z `origin`, `decision-record.md` §8) · **Decyzja właściciela (2026-11-23):** warstwa publikacji —
pliki w repo bez zmian; Decision Record jest formatem w zdarzeniu i w indeksie pdi, nie w repo.

## Cel
Decyzje z codziennej pracy fabryki (rejestr `docs/project/decisions.md`, ADR) trafiają do indeksu suity w pdi,
z linkiem do oryginału, bez zmiany sposobu pisania decyzji w projektach i bez migracji.

## Ustalenia
1. **Hook `decision_publish.py` w mode-pdi** (SessionStart `startup|resume` i SessionEnd) oraz to samo jako polecenie
   (`--dry-run` wypisuje zdarzenia bez wysyłania). Włączony tylko z `PDI_EVENTS_URL` i `PDI_TF_SIGNING_SECRET`
   (jak `run_report.py`); `TF_DECISION_PUBLISH=0` wyłącza. Nigdy nie blokuje sesji: krótki limit czasu, błędy do
   `.tf/logs/hook-errors.jsonl`, kod 0.
2. **Co publikuje:**
   - wiersze rejestru `| D-NNN | data | decyzja | uzasadnienie | status | autor | szczegóły |` — poza statusami
     propozycji, odrzucenia i zastąpienia (`proposed`, `draft`, `rejected`, `superseded` i polskie odpowiedniki);
     `decision_type: project.decision`, `kind: other`;
   - ADR `docs/project/04-architecture/adr/NNNN-*.md` ze statusem `accepted`: tytuł z nagłówka `# NNNN. …` jako
     ustalenie, pierwszy akapit sekcji `## Decision` jako uzasadnienie; `local_id: ADR-NNNN`,
     `decision_type: architecture.decision`, `kind: technical`.
   - Wpisy decyzji zmian (`changes/CHG-n/decisions.md`) zostają przy dotychczasowej ścieżce (`decision pending`,
     MCP), żeby nie trafiały do indeksu dwa razy; ujednolicenie później.
3. **Pochodzenie:** `origin.app: tf`, `scope` = repo `owner/name` z `git remote get-url origin` (inaczej nazwa
   katalogu), `local_id` (`D-012`, `ADR-0003`), `path`, `commit` (ostatni commit pliku), `url` (link do pliku na
   GitHubie, gdy repo jest na GitHubie). `drafted_by: human` (rejestr zawiera decyzje, nie propozycje).
   `occurred_at` = dzień decyzji, bo z niego pdi bierze `decided_at`.
4. **Idempotencja i dosyłanie:** id zdarzenia z `scope`, `local_id` i treści (bez `path`, `commit`, `url` — jak
   §8 kontraktu), więc ponowne wysłanie tej samej decyzji daje ten sam `DEC`, a zmiana treści — nowe zdarzenie
   i nową wersję w pdi. Stan wysłanych poza gitem: `.tf/cache/decision-publish/sent.json` (id zdarzenia, `DEC`
   z odpowiedzi). Błąd sieci albo 5xx — bez zapisu, zdarzenie idzie przy następnej sesji. 4xx — zapis z powodem,
   bez ponawiania, dopóki treść się nie zmieni. Limit czasu na jedno uruchomienie; reszta przy następnym.
5. **Kontrakt:** przypięcie fabryki 0.15.1 → 0.17.0 (`tools/sync_contract.py`), `run_report.py` niesie 0.17.0.

## Poza zakresem
Zastąpienie decyzji w rejestrze (`superseded`) nie trafia jeszcze do pdi jako zastąpienie — wymaga pola w kontrakcie
albo powiązania z poprzednim `DEC`; pamięć podręczna decyzji suity (D8); pliki Decision Record w repo.

## Pliki
| Plik | Zmiana |
|---|---|
| `modes/mode-pdi/hooks/decision_publish.py` (nowy) | zbieranie, zdarzenia, wysyłka, stan |
| `modes/mode-pdi/settings.json` | hook na SessionStart i SessionEnd, zgoda na polecenie |
| `modes/mode-pdi/tests/test_decision_publish.py` (nowy) | |
| `modes/mode-pdi/hooks/run_report.py` | `CONTRACT_VERSION` 0.17.0 |
| `tools/pdi-contract.json` i kopie kontraktu | 0.17.0 |
| `modes/mode-pdi/GUIDE.md` | opis |

## Kolejność (TDD)
1. Test (czerwony): wyłączony bez zmiennych; co publikuje i czego nie; pola i pochodzenie; podpis i ścieżka; klucze
   jak w przykładzie kontraktu; druga sesja nic nie wysyła; zmiana treści = nowe zdarzenie; 5xx = ponowienie przy
   następnej sesji; 4xx = bez ponawiania; `--dry-run`.
2. Kod, przypięcie kontraktu, opis.

Bramki: `python3 tools/workspace.py check --packs mode-pdi` i `--packs all`, `python3 tools/workspace.py refs`,
`for t in tests/test_*.py`, `python3 scripts/check_commit_message.py "<tytuł>"`.
