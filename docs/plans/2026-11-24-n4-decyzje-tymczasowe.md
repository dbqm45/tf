# N4 — wisząca decyzja nie blokuje całej fazy (mode-pdi)

**Data:** 2026-11-24 · **Źródło:** pdi `docs/plan-budowy-suity.md` §3b (zasady 6 i 9, krok N4) · **Zależy od:** N2
(di-contract #8: kontrakt 0.19.0 — `reversibility`, `provisional`, w pytaniach `closes_at`, `default_option`, `asked`)

## Cel
Faza delivery nie stoi przez pytanie z `## Gate questions` w `plan.md`, na które decydent jeszcze nie odpowiedział,
jeśli decyzja jest łatwa do cofnięcia i ma opcję domyślną: pętla cięć idzie dalej z tą opcją jako tymczasową.
Pytanie trudne do cofnięcia zatrzymuje tylko cięcia, które od niego zależą. Dziś każde otwarte pytanie blokuje
cały delivery (Z1, PRB-3).

## Ustalenia
1. **Znaczniki pytania** — opcjonalny nawias kwadratowy na końcu wiersza pytania, elementy rozdzielone `;`:
   `local` | `broad` | `one_way` (odwracalność, wartości kontraktu 0.19.0), `default: <opcja>` (rekomendowana opcja),
   `blocks: TSK-2, TSK-3` (cięcia zależne). Przykład:
   `- Czy limit eksportu to 1000 wierszy? (PO) [local; default: 1000 wierszy]`.
   Pytanie bez znaczników zachowuje się jak dziś. Znaczniki nie zmieniają dopasowania odpowiedzi do pytania
   (`normalized` je pomija).
2. **Przed delivery**, dla pytań bez odpowiedzi w `decisions.md`:
   - `local` albo `broad` z `default` → **tymczasowa**: delivery rusza, prompt podaje opcję jako dane i każe oznaczyć ją
     w opisie PR („Tymczasowo: …”) i trzymać tak, żeby dało się ją zmienić; pytanie zostaje otwarte w pdi;
   - z `blocks` (i nie tymczasowe) → wskazane cięcia **pominięte** w tej fazie, reszta rusza;
   - inne (bez znaczników, łatwe bez opcji domyślnej, `one_way` bez `blocks`) → odmowa jak dziś.
   Wynik fazy (JSON) dostaje `provisional` (pytanie, opcja) i `skipped_tasks` (cięcie → pytania).
3. **Bramka:** `gate.requested` niesie `reversibility` najostrzejszą z pytań (`one_way` > `broad` > `local`), tylko
   gdy wszystkie pytania mają znacznik odwracalności; pytania wysyłane jak dotąd (tekst wiersza).
4. **Prompt faz z artefaktem:** persona dopisuje znaczniki, gdy je zna (odwracalność zawsze, opcja rekomendowana,
   zależne cięcia w `plan.md`).
5. **Kontrakt:** przypięcie tf na 0.19.0 (`tools/pdi-contract.json`, `sync_contract.py sync`, stałe wersji).

## Pliki
| Plik | Zmiana |
|---|---|
| `tools/pdi-contract.json` i kopie kontraktu | 0.19.0 |
| `modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py` | znaczniki, decyzja przed delivery, prompt, `reversibility` bramki |
| `modes/mode-pdi/hooks/{decision_publish,run_report}.py`, `triage_pdi.py` | stała wersji kontraktu |
| `modes/mode-pdi/tests/test_phase_run.py` | przypadki N4 (najpierw, czerwone) |
| `modes/mode-pdi/skills/pdi-decisions/SKILL.md`, `modes/mode-pdi/GUIDE.md` | jak oznaczać pytania |

## Kolejność (TDD)
1. Testy (czerwone): znaczniki nie psują dopasowania odpowiedzi; delivery z pytaniem tymczasowym rusza i prompt
   podaje opcję; z `blocks` — rusza bez tych cięć; bez znaczników — odmowa jak dziś; `reversibility` w bramce.
2. Kod, opis; bramka skilla `pdi-decisions` (scenariusz ewaluacji najpierw, jeśli zmienia się SKILL.md).

Bramki: `python3 tools/workspace.py check --packs mode-pdi` i `--packs all`, `refs`, `for t in tests/test_*.py`,
`scripts/check_commit_message.py`.
