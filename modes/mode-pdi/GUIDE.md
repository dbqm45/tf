# pdi — decyzje w jednym źródle

Tryb `mode-pdi` dokłada do fabryki zapis decyzji zgodny z rejestrem pdi. Bez niego fabryka działa jak dotąd.
Instalacja: `tf add mode-pdi`, usunięcie: `tf remove mode-pdi`.

## Co daje
- **Dziennik zmiany:** `python3 .claude/skills/pdi-decisions/scripts/decision_record.py change new CHG-12 --source PRB-34`
  tworzy `docs/project/changes/CHG-12/` z `intent.md`, `plan.md` i `decisions.md`; nagłówki są zgodne z kontraktem
  pdi 0.3.0 (`contract/change.schema.json`). `decision_record.py check` sprawdza nagłówki.
- **Decyzje:** skill `pdi-decisions` (wspólny dla wszystkich person) po zatwierdzeniu szkicu przez człowieka zapisuje
  decyzję o zmianie w `decisions.md` (`decision add`) i — gdy serwer MCP pdi jest podłączony — w rejestrze pdi
  (`record_decision`), który nadaje numer `DEC-n` (`decision mark`). Niewysłane: `decision pending`; wszystkie
  w JSON: `decision export`.

- **Fazy uruchamiane przez pdi (F4):** po decyzji na bramce skrzynka pdi wywołuje w repo workflow `sdlc-phase.yml`
  (`python3 .claude/skills/pdi-decisions/scripts/phase_run.py workflow install`). Workflow zapisuje decyzję w
  `decisions.md` (`decision_record.py decision gate`), uruchamia personę fazy bez interakcji (`phase_run.py run`:
  `intent` — maja, `requirements` — ewa, `architecture` — tomasz, `design` — natalia, `delivery` — talos; inna
  persona w `.claude/pdi-phases.json`), otwiera PR fazy na gałęzi `pdi/CHG-n-<faza>` i wysyła do pdi prośbę o
  następną bramkę (`phase_run.py gate request`, podpisane `gate.requested` na `PDI_EVENTS_URL/events/tf`).
  Potrzebne: sekrety `ANTHROPIC_API_KEY` i `PDI_TF_SIGNING_SECRET` (ten sam w odbiorniku pdi), zmienna
  `PDI_EVENTS_URL`; w pdi `PDI_DISPATCH_REPO` wskazuje to repo. Zatwierdzając bramkę, scal też PR fazy — następna
  faza zaczyna od gałęzi domyślnej. Każde uruchomienie kosztuje (model); limit fazy daje `PDI_PHASE_BUDGET_USD` w pdi.
  Przyjęcie zgłoszenia w pdi (F3) uruchamia fazę `intent` z wejściami `source` (PRB) i `problem` (treść zgłoszenia):
  workflow zakłada `docs/project/changes/CHG-n/` ze źródłem i dniem zgłoszenia (`source_reported_at`, od niego
  ShipScope liczy lead time od zgłoszenia), a persona pisze `intent.md` z problemu zgłaszającego.

- **Skan bezpieczeństwa na każdym PR (Z8c-2):** `phase_run.py workflow install --workflow change-check` instaluje
  `change-check.yml`: ten sam skan co w pętli kawałka Talosa (`security_scan.py scan` z trybu mode-talos — semgrep
  z regułami OWASP Top 10 i `.semgrep.yml` produktu na plikach zmienionych od bazy PR, `npm audit` / `pip-audit` przy
  zmianie manifestu lub lockfile'a), a SARIF z `reports/security` sprawdza ci_for_sdlc (`--sarif`, SEC-001…003) razem
  z definicją zmian. Błąd skanu (brak skanera, audyt, który się nie wykonał) czerwieni PR. W fazie `delivery`
  `sdlc-phase.yml` instaluje semgrep i pip-audit przed personą, żeby Talos mógł skanować kawałki. Reguły
  `p/owasp-top-ten` pobiera się z `semgrep.dev` — w sandboxie persony host jest na liście dozwolonych (Z8a,
  `sandbox_settings.py`) i działa bez logowania (zestaw węższy niż po `semgrep login` — własne wzorce produktu
  w `.semgrep.yml`); w CI bez sieci ustaw zmienną repozytorium `TALOS_SEMGREP_CONFIG` na plik reguł w repo.
  Wymaga trybu mode-talos.

- **Drugi przegląd przed bramkami B2 i B3 (N1, DZ12):** `second_review.py artifact --change CHG-n --phase P`
  po fazie `requirements`/`architecture`, a przed prośbą o bramkę, czyta artefakt razem z decyzjami zmiany i
  (dla architecture) `requirements.md` i podaje luki (brakujące stany błędu, kryteria bez przykładu, sprzeczności
  z decyzją, cięcia bez dowodu sprawdzalności) jako JSON ze schematem i sekcję „Przegląd drugim modelem"
  w artefakcie. Dostawca: `PDI_SECOND_MODEL` (`openai:<model>` → `OPENAI_API_KEY`, `claude:<model>` →
  `ANTHROPIC_API_KEY`); bez `PDI_SECOND_MODEL` albo bez klucza dostawcy — zapasowy
  `claude:claude-sonnet-5-5` oznaczony jako przegląd tego samego dostawcy (`same_vendor: true`).
  Blokujące ustalenia (`blocker` i `major`) dopisuje `phase_run.py gate request` do pytań bramki z prefiksem
  `[drugi przegląd]`, a sprzeczności z decyzjami wymienia z odwołaniem `[sprzeczne z <ref>]`. Niedostępność
  drugiego modelu jest w prośbie o bramkę jako `second_review: {status: unavailable, reason: …}`. W Actions
  `OPENAI_API_KEY` dostaje tylko ten krok (klucz nie trafia do kontenera persony — Z8g). Koszt zapisany
  w sidecarze (`docs/project/changes/CHG-n/.review/<phase>.json`) wchodzi w budżet fazy (`PDI_PHASE_BUDGET_USD`)
  obok kosztu persony. Druga podkomenda `comments` sprawdza uwagi recenzenta z PR (N2, A5).

- **Pętla PR talosa (N2):** po fazie `delivery` w trybie lokalnym pdi prowadzi każdy PR cięcia przez rundy:
  przegląd AI według `REVIEW.md` produktu (`pr_loop.py review`, w kontenerze fazy; bez pliku — szablon tf, a
  `pr_loop.py scaffold` dodaje go do produktu) → walidacja uwag drugim modelem (`second_review.py comments`, N1) →
  talos poprawia tylko potwierdzone uwagi `critical`/`important` i czerwone checki (`pr_loop.py fix`, log CI jako
  dane cytowane) → ponowny przegląd; najwyżej 2 rundy (jak DZ6). Uwagi niepotwierdzone, przy niedostępnym drugim
  modelu i sprzeczne z decyzją zmiany idą do człowieka jako pytania; drobne (`minor`) — jako lista w PR. **Zielone**
  = co najmniej jeden check CI na głowie PR i wszystkie `pass`/`skipping`; dlatego `change-check.yml` ma obowiązkowy
  krok „Weryfikacja produktu (N3)” (`./verify.sh`). PR bez checków nie jest zielony: pdi uruchamia wtedy
  `pr_loop.py verify` w kontenerze i kończy z powodem `no_ci_checks`. Opis PR dostaje sekcję „Przewodnik
  dokończenia” (co zrobione, co zostaje, decyzje poza planem, ryzyka), aktualizowaną po każdej rundzie. W Actions
  (`sdlc-phase.yml`) pętli nie ma: push tokenem `github.token` nie uruchamia CI na gałęziach cięć.

- **Pasma kontrolne z ShipScope (F5):** `metric_watch.py check` czyta dzienny szereg PROD z API usług ShipScope
  (rollbacki, wdrożenia nieudane, lead time, liczba wdrożeń), liczy pasma `control_band.py` i przy punkcie poza 3σ
  z ostatnich dni wysyła do pdi `metric.breached` (`--send`). Codziennie: `metric_watch.py workflow install`
  (`metric-watch.yml`). Potrzebne: sekrety `SHIPSCOPE_TOKEN` (token usługi z ShipScope) i `PDI_TF_SIGNING_SECRET`,
  zmienne `SHIPSCOPE_URL` i `PDI_EVENTS_URL`; metryki i linia bazowa w `.claude/pdi-metrics.json`. Bez modelu, bez
  kosztu. pdi musi przyjmować `metric.breached` od tf (zgłoszenia, F3) — wcześniej odpowie 400.

## Warunek: serwer MCP pdi
Zapis do rejestru działa tylko wtedy, gdy w sesji jest serwer MCP `pdi` (narzędzia `record_decision`,
`find_decisions`, `get_decision`, `supersede_decision`). Instalację opisuje repo pdi
(`integrations/claude-code/README.md`; rejestracja `claude mcp add --scope user pdi …`). Bez niego decyzje zostają w `decisions.md` z pustym `id` i `wyslano: nie` — nic nie ginie.

## Czego nie zmienia
Rdzeń fabryki, dziennik faz projektu (`docs/project/0N-*`), inne nakładki i ustawienia — bez zmian. Projekt bez
katalogu `docs/project/changes/` nie widzi różnicy.

## Polecenia
`decision_record.py change new|check`, `decision add|pending|mark|export|gate`, `phase_run.py prompt|run|gate
request|workflow install`, `metric_watch.py check|workflow install` — pełny opis: `--help` skryptów.
