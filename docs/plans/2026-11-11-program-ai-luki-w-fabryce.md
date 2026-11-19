# Plan: zadania fabryki z planu programu AI (T1–T14) wobec stanu 9.17

Stan: 2026-11-11. Źródło: pdi `docs/plan-program-ai-wg-aplikacji.md` §2.1 (zadania T1–T14 dla fabryki, plan z 2026-11-10
pisany wobec tf 9.15 i oceny z 2026-11-08). Decyzja człowieka 2026-11-11: „działaj ze zmianami z planu, zacznij od
fabryki”. Pokrycie sprawdzone 2026-11-11 w `core/`, `packs/`, `modes/` na `main` (9.17.0): pliki, nie wyszukiwanie
zgrubne.

Zasady kroków jak w `2026-11-09-luki-katalogu-i-autonomia.md`: kod metodą TDD (test czerwony, potem kod), skill wg
`core-skill-authoring` (scenariusze przed treścią, bramka), ewaluacja płatna tylko za zgodą, nic „dla kompletności”.

## 1. Co z T1–T14 już jest, a co jest luką

| # | Zadanie z planu programu | Stan w 9.17 | Wniosek |
|---|---|---|---|
| T1 | `pack-data`: model card, data contract, eval dataset, regresja promptów, metryki modelu, ocena ludzka | `pack-it`: `ai-evals` (zbiory, graderzy, sędzia z kalibracją na ocenach ludzi, pass@k, bramka w CI, online), `ai-mlops` (rejestr, karta modelu, drift, prompty jako artefakt), `data-engineering` (kontrakty), `data-analysis`, `ai-prompt-engineering`; persona danych `zofia` | **treść jest**. Osobna nakładka to kwestia pakowania, nie luki. Zostaje do sprawdzenia: rola „ML engineer” i metodyka z aiux (α Krippendorffa, A/B z bootstrapem) wobec `ai-evals` — porównanie treści, osobny krok |
| T2 | `repo-standard-check` w `tf doctor` i CI | `eng-repo-readiness/scripts/readiness_check.py` (lockfile, testy, CI, konfiguracja, pliki instrukcji, DX), `core-agent-instructions/scripts/instructions_lint.py` (karta kontroli CLAUDE.md), `build.py check` (instalacja) | **luka wąska**: brak jednego polecenia, które sprawdza standard dziennika (`docs/project/`: TL;DR, Przekazanie, `lessons.md`, decyzje) i zbiera trzy istniejące kontrole w jeden wynik dla CI. Krok 2 |
| T3 | jeden język instrukcji | `tf language`, `tf commit-language`, `default_language`, `languages` | **mechanizm jest**; brakuje decyzji D-P6, nie kodu |
| T4 | `eval-gate` dla modeli i promptów | wiedza w `ai-evals` (`references/ci-i-ruch.md`), `skill_gate.py` i `flow-evals` dla samej fabryki | **luka**: brak gotowego narzędzia dla produktu (zestaw + próg wobec linii bazowej + budżet → wynik dla CI i bramki pdi). Krok 3 |
| T5 | przegląd AI jako required check | `core-git-workflow/scripts/ai_review.py install` → `ai-review.yml`, status `ai-review/verdict`, `--all-prs`, obejście etykietą; drugi przegląd (N1); panel recenzentów specyfikacji (A9); moduły `tf analyze` z bramką (`security`, `accessibility`, `authz`…) | **zrobione**; „required” to ustawienie ochrony gałęzi w repo produktu (poza fabryką). Do rozważenia: przebiegi przeglądu jako osobne soczewki z budżetem |
| T6 | lista zatwierdzonych modeli | brak (tiery i profile wybierają po koszcie; `build.py check` sprawdza tylko, czy nazwa modelu jest znana) | **luka**. Krok 1 (niżej) |
| T7 | eksport dziennika agentów | lokalne `.tf/logs/usage.jsonl`, `delegation.jsonl`, `jev.jsonl`, `hook-errors.jsonl`; eksport przebiegów do pdi (`test_export_pdi_runs.py`) | **luka zależna**: schemat `agent-audit-event` musi najpierw wejść do kontraktu pdi (P5). Po kontrakcie |
| T8 | macierz uprawnień agent → system → operacja | polityka autonomii B1a (`autonomy.operations`: confirm / deny per typ operacji, projekt może tylko zaostrzać), `tf risk`, `cleanroom.json` | **wersja per repo jest**; poziom organizacji (źródło w rejestrze AI) czeka na rejestr |
| T9 | cykl życia funkcji AI (shadow → asystent → ograniczona autonomia → wycofanie) | `ai-mlops` (shadow, canary, A/B, wycofanie), `ai-evals` (offline → online), `ai-agents` | **częściowo**: brak powiązania etapów z poziomami autonomii decyzji i bramką operacyjną. Treść, po decyzji D-P4 |
| T10 | role ludzi (AI Champion, Data Owner, PO AI) i RACI | `core-delivery-lifecycle`: jeden człowiek jako właściciel i zatwierdzający; `ai-governance-compliance`: role wg AI Act | **luka treści**, zależna od operating modelu (pdi P1) |
| T11 | `pack-retail` | — | poza zakresem do czasu linii retail |
| T12 | sandbox dla agentów operacyjnych | `templates/sandbox.settings.json`, `tools/` test `test_sandbox_check.py`, kontener fazy w pdi | **luka zależna** od bramki modeli |
| T13 | packi spoza repo fabryki | `tf --repo <url>#ref` dla całej fabryki; nakładki tylko z `packs/` źródła | **luka**. Krok 4 |
| T14 | wersje technologii per aplikacja | `detect_stack.py`, `skill.meta.json`, `core-stack-sync` | do przemyślenia z człowiekiem (pdi plan §10); bez kodu teraz |

Wniosek dla planu programu: sekcja §2.1 w pdi zakładała więcej braków, niż jest. Realne kroki w fabryce to cztery
(T6, T2, T4, T13); reszta jest zrobiona, zależy od innych aplikacji albo od decyzji.

## 2. Krok 1 — lista zatwierdzonych modeli (T6)

**Po co.** Organizacja ma listę modeli, których wolno używać (dane, region, umowa). Dziś fabryka dobiera model po
koszcie i nic nie stoi na przeszkodzie, żeby tier, profil albo agent delegujący wskazał model spoza listy. Ta sama
lista ma być czytana przez bramkę modeli (ai-gateway), gdy powstanie.

**Zakres.**
1. Klucz konfiguracji `approved_models` (`.tf/factory/config.yaml`, nadpisanie w `.tf/config/config.yaml`). Pusty albo
   bez `models` = bez ograniczeń (zachowanie jak dotąd). Kształt:
   ```yaml
   approved_models:
     source: "Polityka AI 2026-11"         # skąd lista (dokument, decyzja) — opcjonalne
     models:
       haiku:  {provider: anthropic, regions: [eu], data: [public, internal], contract: "DPA 2026-03"}
       sonnet: {provider: anthropic, regions: [eu], data: [public, internal, personal], until: "2027-06-30"}
   ```
   Kluczem jest nazwa użyta w konfiguracji: alias (`haiku`, `sonnet`, `opus`, `fable`) albo pełny identyfikator
   `claude-…`. Dopasowanie dokładne: alias zatwierdza alias, identyfikator zatwierdza identyfikator. `until` po
   terminie = model niezatwierdzony. Pola opisu (`provider`, `regions`, `data`, `contract`, `note`) są dla ludzi
   i dla bramki; fabryka ich nie interpretuje.
2. Silnik `models_policy.py` (`.tf/factory/`): `check(cfg, active_profile)` → błędy i ostrzeżenia;
   `python3 .tf/factory/models_policy.py [--json]` wypisuje listę i miejsca użycia modeli (dla człowieka i dla bramki).
3. `build.py check` (więc także `tf doctor`): **błąd**, gdy model tieru po nałożeniu aktywnego profilu albo ustawienie
   sesji aktywnego profilu (`model`, `advisorModel`) jest spoza listy; **ostrzeżenie** dla pozostałych profili
   (nieużywany profil nie blokuje pracy) i dla `inherit` (model sesji jest poza kontrolą listy). Target
   `managed-agents`: sprawdzany identyfikator, na który tłumaczy `managed_agents.models`, chyba że zatwierdzony jest
   alias.
4. `profile.py <profil>` odmawia przełączenia na profil z modelem spoza listy (kod 1, bez zapisu).
5. Hook `model_guard.py` (PreToolUse `Agent|Task`): parametr `model` delegacji spoza listy → `deny` z listą
   zatwierdzonych. Bez listy hook nic nie robi. Błąd odczytu konfiguracji nie blokuje (zapis w `hook-errors.jsonl`).

**Poza zakresem.** Model sesji wybrany ręcznie (`/model`) — fabryka go nie kontroluje, to rola bramki modeli.
Synchronizacja listy z bramki — gdy bramka powstanie.

**Zgodność wstecz.** Nowy klucz, nowe polecenie, nowa blokada wyłączona domyślnie → MINOR (`feat`).

**Testy (najpierw czerwone)** `core/tests/test_models_policy.py`:
- MP-1 brak listy → brak błędów i ostrzeżeń; MP-2 tier spoza listy → błąd z nazwą tieru i modelu;
- MP-3 profil aktywny nadpisuje tier na model spoza listy → błąd; inny profil → tylko ostrzeżenie;
- MP-4 `advisorModel`/`model` aktywnego profilu spoza listy → błąd;
- MP-5 `until` po terminie → niezatwierdzony; w terminie → zatwierdzony; zły format daty → błąd konfiguracji;
- MP-6 `inherit` → ostrzeżenie; MP-7 target `managed-agents`: identyfikator z mapy spoza listy → błąd, zatwierdzony
  alias wystarcza;
- MP-8 zły kształt (`models` nie jest słownikiem, wpis nie jest słownikiem) → błąd konfiguracji, nie wyjątek;
- MP-9 CLI `--json`: lista i użycia; MP-10 `build.py check` w projekcie z listą bez `opus` → kod 1 i komunikat;
- MP-11 `profile.py jakosc` przy liście bez `opus` → kod 1, plik profilu bez zmian;
- MG-1…MG-5 hook: bez listy brak decyzji; model z listy brak decyzji; model spoza listy `deny`; brak parametru `model`
  brak decyzji; uszkodzona konfiguracja nie blokuje.

**Dokumentacja.** `PUBLIC_API.md` (klucz, polecenie, hook w regułach blokujących), `core/guide/PRZEWODNIK.md` i `FAQ.md`
(hooki-strażnicy), komentarz przy kluczu w `config.yaml`, `docs/todo.md`.

**Bramki.** `tools/workspace.py check --packs none`, `--packs all`, `refs`; testy repo (`tests/test_*.py`).

## 3. Kolejne kroki (osobno, po akceptacji kroku 1)

- **Krok 2 (T2) — zrobiony 2026-11-11:** `tf standard` (`.tf/factory/standard.py`) — jeden wynik z pięciu
  istniejących kontroli: `install` (`build.py check`), `journal` (`project_record.py`: kontrola dziennika
  `docs/project/` już była, więc nic nowego nie powstało), `instructions` (`instructions_lint.py`), `readiness`
  (`readiness_check.py` z pack-it; bez nakładki `skip`), `hooks` (`hooks_status.py`). Statusy ok / warn / fail / skip,
  werdykt = najgorszy, kod 1 przy `fail` (`--strict`: także `warn`), `--json`, `--only`. Kontrole tylko czytają pliki
  (dziennik sprawdzany funkcją `check`, bez przebudowy indeksu). Krok w `team-factory.yml` jest informacyjny
  (`continue-on-error`), żeby aktualizacja nie zaczęła blokować CI istniejących projektów. Testy:
  `core/tests/test_standard.py` (ST-1…ST-8).
- **Krok 3 (T4):** `eval_gate.py` dla produktu: zestaw (JSONL), grader z kodu, próg wobec linii bazowej z rozrzutem,
  budżet USD, wynik JSON; szablon `eval-gate.yml`; w trybie pdi wynik jako warunek bramki (cele zmiany `targets`).
- **Krok 4 (T13):** nakładka z innego repozytorium (`tf add <repo>#tag:pack-x`), z `skill_audit.py` i przypięciem
  wersji; warunek wydzielenia `pack-ev` do linii EV.
- **Treść po decyzjach:** T9 i T10 po operating modelu (pdi P1); T7 po schemacie w kontrakcie; T14 po rozmowie.
