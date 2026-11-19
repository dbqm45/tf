# Plan: bramka ewaluacji w CI i lista zatwierdzonych modeli — przeniesienie na fabrykę 20.1

Stan: 2026-11-19. Źródło: pdi `docs/plan-program-ai-wg-aplikacji.md` §2.1 (zadania fabryki T4 i T6). Trzy kroki
zbudowane 2026-11-11 na 9.17 (gałąź `claude/funny-hopper-8zsl07`: lista modeli, `tf standard`, `eval_gate.py`) nie
weszły na `main`; przez ten czas fabryka doszła do 20.1.0 (199 commitów: treść po angielsku, `model_check.py`,
warstwy firmy i zespołu, zadania ze stanem, `tf status`). Decyzja człowieka 2026-11-19: przenieść tylko to, co
**rozszerza obecną fabrykę i niczego w niej nie psuje**.

## Co przenosimy, a co nie

| Krok z 9.17 | Stan w 20.1 | Decyzja |
|---|---|---|
| `eval_gate.py` w `ai-evals` (T4) | nic podobnego; skill przetłumaczony, `references/ci-and-traffic.md` opisuje bramkę bez narzędzia | **przenosimy** po angielsku, werdykty jak w skillu: release / investigate / hold |
| lista zatwierdzonych modeli (T6) | `model_check.py` sprawdza, czy nazwy modeli istnieją i są aktualne (`models_current`, `models_legacy`); nie sprawdza, czy model jest **dozwolony** | **przerabiamy** na rozszerzenie `model_check.py`, bez osobnego silnika i bez zmian w `build.py` |
| `tf standard` (T2) | doszły `tf status`, `tf task check`, standardy firmowe bez modelu (`tf analyze`, `rules.yaml`) | **odkładamy** do porównania z nowymi poleceniami; nie wchodzi |

Zasada bezpieczeństwa zmiany: gałąź zaczyna od drzewa identycznego z `main` (merge 20.1.0), bramki
`tools/workspace.py check --packs all` i `--packs none` uruchomione **przed** zmianami (stan bazowy) i **po**; nowe
zachowanie jest wyłączone, dopóki nikt nie ustawi listy; istniejące testy zostają bez zmian (nowe testy w nowych plikach).

## Krok A — `eval_gate.py` (pack-it, skill `ai-evals`)

- `packs/pack-it/skills/ai-evals/scripts/eval_gate.py`: `baseline` (rozrzut i próg z 3–5 przebiegów obecnej wersji,
  `--margin`), `check` (release / investigate / hold; kod 1 przy hold, `--strict` także przy investigate; kod 2 przy
  błędzie danych — pusty plik to nie „0 porażek”), `--budget-usd`, `--json`, `--report`. Czyta JSON Lines
  (`id`, `passed`, opcjonalnie `layer`, `cost_usd`, `trial`), liczy sukces, pass^k, pass@k, koszt, regresje zadań
  stabilnych. Modelu nie uruchamia, sieci nie używa.
- Scenariusz ewaluacji `bramka-ci-narzedzie-prog-z-bazy` dodany **przed** treścią; SKILL.md pkt 9 i
  `references/ci-and-traffic.md` wskazują narzędzie.
- Testy `packs/pack-it/tests/test_eval_gate.py` (EG-1…EG-12, wartości policzone ręcznie) i porównanie z wzorcem
  policzonym niezależnie (30 zadań × 3 próby).

## Krok B — lista zatwierdzonych modeli jako rozszerzenie `model_check.py`

**Po co.** `model_check.py` odpowiada na pytanie „czy taki model istnieje”. Organizacja potrzebuje też odpowiedzi „czy
wolno go używać” (dane, region, umowa) — tej samej, którą później będzie egzekwować bramka modeli.

**Konfiguracja.** Nowy opcjonalny klucz `models_approved` (pusty = bez ograniczeń, zachowanie jak dotąd):
```yaml
models_approved:
  source: "AI policy 2026-11"            # skąd lista — opcjonalne
  models:
    haiku:  {provider: anthropic, regions: [eu], data: [public, internal], contract: "DPA 2026-03"}
    claude-sonnet-5-5: {until: "2027-06-30"}
```
- Kluczem jest alias (`haiku`, `sonnet`, `opus`, `fable`) albo pełny identyfikator. Alias i identyfikator łączy
  `models_current`: zatwierdzenie identyfikatora obejmuje alias, **dopóki** alias na niego wskazuje (gdy fabryka
  przestawi alias na nowszy model, zatwierdzenie przestaje obowiązywać i kontrola to zgłosi); zatwierdzenie aliasu
  obejmuje model, na który alias wskazuje.
- `until` po terminie = model niezatwierdzony. Pola opisu (`provider`, `regions`, `data`, `contract`, `note`) są dla
  ludzi i dla bramki; fabryka ich nie interpretuje.
- **Warstwy:** klucz dochodzi do `ORG_CONFIG_KEYS`, więc firma ustawia go w `org_defaults.config`, zespół
  w `team_defaults.config`, projekt w `.tf/config/config.yaml`. Niższa warstwa może listę tylko **zawęzić** (część
  wspólna, jak `task.allowed_modes`); model dopisany niżej, którego wyższa warstwa nie ma, jest ignorowany z ostrzeżeniem.

**Kontrola (`model_check.py`, więc także `tf doctor` i CI).** Gdy lista jest ustawiona: model tieru po nałożeniu
aktywnego profilu i ustawienia sesji aktywnego profilu (`model`, `advisorModel`) spoza listy → **błąd**; pozostałe
profile → ostrzeżenie; `inherit` → ostrzeżenie (model sesji jest poza kontrolą); przy targecie `managed-agents`
identyfikator z `managed_agents.models` musi być zatwierdzony. Wynik JSON zyskuje pola `approved`, `approved_expired`
i `usage`. Bez listy wynik i wydruk są takie jak dziś.

**Egzekwowanie w chwili użycia.**
- `profile.py <profil>` odmawia przełączenia na profil z modelem spoza listy (kod 1, bez zapisu).
- Nowy hook `model_guard.py` (PreToolUse `Agent|Task`): parametr `model` delegacji spoza listy → `deny` z listą
  zatwierdzonych, zapis w `hook-blocks.jsonl`. Bez listy hook kończy od razu. Błąd odczytu konfiguracji nie blokuje
  (zapis w `hook-errors.jsonl`), dlatego hook nie ma `onFailure: block`.

**Poza zakresem.** Model sesji wybrany ręcznie (`/model`) — to rola bramki modeli. `build.py` bez zmian.

**Zgodność wstecz.** Nowy klucz, nowa blokada wyłączona domyślnie, nowe pola w JSON → MINOR (`feat`).

**Testy (najpierw czerwone)** `core/tests/test_models_approved.py`: bez listy wynik `model_check.py` jak dotąd;
tier spoza listy → błąd; alias zatwierdzony przez identyfikator z `models_current`; identyfikator zatwierdzony przez
alias; `until` po terminie; profil nieaktywny → ostrzeżenie; `advisorModel`; `inherit`; zawężanie warstw (firma →
projekt) i próba rozszerzenia; zły kształt bez wyjątku; `profile.py` odmawia; hook: bez listy brak decyzji, model
z listy brak decyzji, spoza listy `deny` z zapisem bloku, brak parametru brak decyzji, uszkodzona konfiguracja nie
blokuje. Istniejący `test_model_check.py` pozostaje bez zmian i ma przechodzić.

**Dokumentacja.** `PUBLIC_API.md`, `core/guide/GUIDE.md` i `FAQ.md`, komentarz przy kluczu w `config.yaml`,
`org/README.md` (wiersz o warstwie firmy), `docs/todo.md`.

## Bramki
`tools/workspace.py refs`; testy repozytorium (`tests/test_*.py`); `tools/workspace.py check --packs none`,
`--packs pack-it` i `--packs all` — porównane ze stanem bazowym z `main`.
