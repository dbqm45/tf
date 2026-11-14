# Mapa artefaktów

> **Spis treści:** Pliki stałe (cały projekt) · 0. Rekonstrukcja istniejącego kodu (przed zmianami w… · 1. Przyjęcie, plan faz i odkrywanie produktu —… · 2. Domena — `02-domain/` · 3. Wymagania — `03-requirements/` · 4. Architektura — `04-architecture/` · 5. Plan — `05-plan/` · 6–7. Realizacja i przygotowanie do wydania — `06-delivery/` · 7–8. Przeglądy, wydanie, obserwacja — `07-review/` · 9. Utrzymanie — `08-operations/` · Poza `docs/project/` · Jak używać

Gdzie leży wynik każdej fazy, kto go pisze, który skill prowadzi pracę i kto go potem czyta. Ścieżki są względem
`docs/project/` (dziennik projektu, core-project-record), chyba że podano inaczej. Skill z nakładką działa tylko
wtedy, gdy nakładka jest zainstalowana (`.claude/catalog.md`). Kolumna „Mały projekt” mówi, kiedy artefakt można
pominąć na ścieżce skróconej. Pominięcie zapisujesz jednym zdaniem w Przekazaniu fazy, żeby następna persona nie
szukała pliku, którego nie ma.

Zasada nadrzędna: artefakt powstaje, gdy ktoś go przeczyta i podejmie na jego podstawie decyzję. Pusty szablon nie
jest artefaktem.

## Pliki stałe (cały projekt)
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `journal.md` | każda persona (dopisuje) | core-project-record | następna sesja: co się stało | zawsze |
| `decisions.md` | persona przy decyzji człowieka | core-project-record | wszyscy: rejestr decyzji D-NNN | zawsze |
| `lessons.md` | persona po powtarzającej się pułapce | core-agent-retro, core-project-record | każda sesja na starcie | gdy jest lekcja |
| `questions.md` | dyspozytor, persony | core-problem-routing | człowiek: otwarte pytania | gdy są pytania |
| `wip/<nazwa>.md` | persona przy zadaniu dłuższym niż kilka kroków | core-project-record | ta sama persona po przerwie | zawsze przy długim zadaniu |
| `archive/research/<RRRRMMDD>-<temat>.md` | persona badająca fakty | core-source-research, core-knowledge | autor decyzji, która na nich stoi | gdy badano źródła |
| `archive/retro/<RRRRMMDD>-retro.md` | persona po etapie | core-agent-retro | następny etap | po każdym etapie |
| `exports/report-<data>.md`, `exports/handoff-<data>-<temat>.md` | generowane | core-project-record | ludzie poza repo, inny agent | na żądanie |

## 0. Rekonstrukcja istniejącego kodu (przed zmianami w nieznanym repo)
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `00-reconstruction/report.md`, `00-reconstruction/plan.md`, `00-reconstruction/manifest.json` | architekt / analityk | eng-project-reconstruction (pack-it) | każda persona przed zmianą | pomiń w nowym projekcie |
| `00-reconstruction/domain.md`, `00-reconstruction/standards/INDEX.md` | jak wyżej | eng-project-reconstruction (pack-it) | pętla `/tf` przed historyjką (skill tf) | pomiń w nowym projekcie |

## 1. Przyjęcie, plan faz i odkrywanie produktu — `01-discovery/`
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `01-discovery/brief.md` | dyspozytor | core-plan-interview, core-problem-routing; proc-requirements-shaping (pack-it) | wszystkie fazy: problem, cel, zakres, plan faz | zawsze (może być krótki) |
| `01-discovery/project-plan.md` | dyspozytor / architekt | proc-project-planning (pack-it) | człowiek: koszt i termin P50/P80, ryzyka | pomiń bez budżetu i terminu |
| `01-discovery/pre-flight.md` | analityk domeny | ddd-discovery-intake (pack-it) | decyzja „czy modularyzować” | pomiń przy jednym module |
| `01-discovery/research-plan.md`, `01-discovery/research-report.md` | badacz UX | ux-research-methods (pack-ux) | projektant produktu: co wiemy o użytkownikach | pomiń bez badań |
| `01-discovery/service-blueprint.md` | projektant usług | ux-service-design (pack-ux) | produkt i operacje: zaplecze usługi | pomiń bez usługi wielokanałowej |
| `01-discovery/ux-maturity.md` | lider designu | ux-design-leadership (pack-ux) | kierownictwo: dojrzałość UX | rzadko potrzebne |

## 2. Domena — `02-domain/`
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `02-domain/glossary.md` | analityk domeny | ddd-event-storming, ddd-facilitation (pack-it); korekta txt-polish-correctness (pack-editorial-pl) | wszyscy: język wszechobecny | zawsze, choćby 10 pojęć |
| `02-domain/corpus.md`, `02-domain/contradictions.md`, `02-domain/strategic-gaps.md` | analityk domeny | ddd-discovery-intake (pack-it) | analityk: bank dowodów i sprzeczności | gdy są surowe materiały |
| `02-domain/strategic.md`, `02-domain/context-map.md` | analityk domeny | ddd-strategic-analysis, ddd-context-mapping (pack-it) | architekt: granice kontekstów | pomiń przy jednym kontekście |
| `02-domain/event-storming/<id>/` | facylitator | ddd-event-storming (pack-it) | analityk: zdarzenia i procesy | pomiń, gdy proces jest prosty |
| `02-domain/concepts/<pojecie>.md` | analityk domeny | ddd-deep-modeling (pack-it) | implementer: trudne pojęcie | tylko trudne pojęcia |
| `02-domain/archetypes/<archetyp>-<obszar>.md` | analityk domeny | ddd-archetypes (pack-it) | architekt, implementer | gdy pasuje archetyp |
| `02-domain/algorithms.md` | analityk domeny | ddd-algorithm-recognition (pack-it) | implementer: ukryty problem algorytmiczny | gdy jest |
| `02-domain/connascence/<a>-<b>.md`, `02-domain/connascence/<a>-<b>.frame.md` | analityk domeny | ddd-connascence-analysis (pack-it) | architekt: koszt sprzężenia | przy sporze o granice |
| `02-domain/stress/<metryka>.md`, `02-domain/_blind/brief.md`, `02-domain/_blind/competitors.md` | analityk + ślepy analityk | ddd-model-stress-test (pack-it) | architekt: czy model wytrzyma wymagania | pomiń |
| `02-domain/acl-<pakiet>.md`, `02-domain/distillation.md`, `02-domain/invariant-<nazwa>.md` | analityk domeny | ddd-legacy-modernization (pack-it) | implementer przy modernizacji | tylko legacy |
| `02-domain/experiment-<nazwa>.md` | badacz AI | ai-research-methods (pack-it) | decyzja o podejściu ML | tylko badania ML |

## 3. Wymagania — `03-requirements/`
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `03-requirements/requirements.md` | analityk + projektant produktu | proc-requirements-shaping, qa-test-design, ai-product-management (pack-it) | projektant testów (testy z kryteriów), architekt, implementer | zawsze |
| `03-requirements/spec-review.md` | panel recenzentów | core-delivery-lifecycle (`references/przeglad-specyfikacji.md`) | człowiek na bramce przed planem | pomiń na ścieżce skróconej |
| `03-requirements/ia-documentation.md` | architekt informacji | ux-information-architecture (pack-ux) | projektant UI, implementer frontu | pomiń przy kilku ekranach |

## 4. Architektura — `04-architecture/`
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `04-architecture/stack-decision.md` | architekt rozwiązania | arch-tech-selection (pack-it) | generator szkieletu (eng-repo-readiness, pack-it), implementer | zawsze, krótko |
| `04-architecture/architecture.md` | architekt rozwiązania | core-project-record (szablon); arch-system-design (pack-it) | wszyscy: C4, strategia danych i wdrożeń | jeden akapit + diagram |
| `04-architecture/adr/NNNN-krotki-tytul.md` | architekt | core-project-record (szablon `adr`); docs-tech-writing (pack-docs) | przyszli autorzy zmian: dlaczego tak | gdy decyzja jest kosztowna w odwróceniu |
| `04-architecture/erd.md` | architekt / implementer backendu | be-database (pack-it) | implementer, analityk danych, przegląd migracji | gdy jest relacyjna baza |
| `04-architecture/threat-model.md` | architekt + security | arch-threat-modeling (pack-it) | security-reviewer, implementer | gdy dane wrażliwe lub dostęp z internetu |
| `04-architecture/privacy.md`, `04-architecture/data-inventory.md` | architekt | arch-privacy-compliance (pack-it) | człowiek z IOD, implementer: klasy pól, retencja | zawsze przy danych osobowych |
| `04-architecture/<data>-mapa-prawna.md` | architekt | arch-eu-product-law (pack-it) | człowiek z prawnikiem | gdy produkt podlega prawu UE |
| `04-architecture/compliance.md`, `04-architecture/risk-register.md`, `04-architecture/eu-cyber-regulations.md` | architekt bezpieczeństwa | sec-governance-compliance, sec-risk-management, sec-eu-regulations (pack-it) | kierownictwo, audytor | gdy są wymogi formalne |
| `04-architecture/zero-trust.md`, `04-architecture/cloud-security-baseline.md`, `04-architecture/landing-zone.md` | architekt bezpieczeństwa / chmury | sec-zero-trust-identity, sec-cloud-security, ops-cloud-landing-zones (pack-it) | DevOps, security | pomiń poza chmurą firmową |
| `04-architecture/ai-architecture.md`, `04-architecture/ai-compliance.md` | architekt AI | arch-ai-solutions, ai-governance-compliance (pack-it) | implementer funkcji AI, człowiek | tylko z komponentem AI |
| `04-architecture/codebase-map.md`, `04-architecture/legacy-dossier/README.md` | architekt | eng-codebase-mapping, eng-legacy-dossier (pack-it) | implementer w nieznanym kodzie | tylko istniejący kod |
| `04-architecture/context-architecture.md` | autor instrukcji agenta | core-agent-instructions | autor CLAUDE.md / AGENTS.md | przy dużych instrukcjach |
| kontrakt API (OpenAPI) — **w repozytorium kodu**, obok serwisu, nie w dzienniku | architekt + implementer | be-api-design (pack-it) | klienci API, test kontraktu w CI | gdy jest API dla innych |

## 5. Plan — `05-plan/`
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `05-plan/plan.md` | architekt + projektant testów | core-delivery-lifecycle (`references/plan-ciec.md`) | wykonawcy: cięcia w kolejności | zawsze |
| `05-plan/release.yaml` | architekt | core-delivery-lifecycle (`references/plan-ciec.md`) | DevOps przy wydaniu, bramki B5 | pomiń przy jednym wydaniu bez flag |
| `05-plan/test-plan.md`, `05-plan/test-strategy.md` | projektant testów | qa-test-design, eng-local-quality-gates (pack-it) | implementer, przegląd zmian | test-plan zawsze; strategia przy wielu warstwach |
| `05-plan/migration-plan.md` | architekt chmury | ops-cloud-migration (pack-it) | DevOps, człowiek: fale i cutover | tylko migracja |

## 6–7. Realizacja i przygotowanie do wydania — `06-delivery/`
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `06-delivery/NNN-<slug>.md` | wykonawca kroku | core-project-record (szablon `delivery`) | przegląd, następny krok | zawsze (raport kroku) |
| `06-delivery/NNN-behavior-contract.md` | wykonawca refaktoryzacji | eng-behavior-preserving-refactoring (pack-it) | przegląd: zachowanie bez zmian | tylko refaktoryzacja |
| `06-delivery/bootstrap-verification.md` | wykonawca szkieletu | eng-repo-readiness (pack-it) | człowiek: czy szkielet działa | nowy projekt |
| `06-delivery/deploy-plan.md` | DevOps | ops-release-engineering (pack-it) | człowiek wdrażający | proste wdrożenie bez etapów |
| `README.md`, `CHANGELOG.md` — **w korzeniu repozytorium** | implementer / tech writer | core-semver; docs-tech-writing (pack-docs) | użytkownicy i nowe osoby | zawsze |
| runbook — **przy usłudze lub w dokumentacji operacyjnej** | DevOps/SRE | ops-sre-incidents (pack-it); docs-tech-writing (pack-docs) | dyżurny | gdy usługa ma dyżur |
| sekcja „Ryzyko zmiany” w opisie PR | generowana (`tf risk --md`) | core-git-workflow | recenzent: co musi zobaczyć człowiek | każdy PR |

## 7–8. Przeglądy, wydanie, obserwacja — `07-review/`
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `07-review/<data>-gotowosc.md` | DevOps + security + projektant testów | core-delivery-lifecycle (`references/gotowosc-produkcyjna.md`) | człowiek na bramce wydania | zawsze przed produkcją |
| `07-review/<data>-przebieg-probny.md` | dyspozytor | core-delivery-lifecycle (`references/przebieg-probny.md`) | człowiek: czy fabryka dowozi | jednorazowo |
| `07-review/<data>-<rodzaj>.md` (bezpieczeństwo, architektura, retro, testy) | recenzent danego rodzaju | security-reviewer; core-agent-retro | człowiek, następna faza | wg ryzyka |
| `07-review/<data>-gotowosc-repo.md` | audytor repo | eng-repo-readiness (pack-it) | człowiek, autor CLAUDE.md: poprawki dla agentów | przy przejęciu repo |
| `07-review/<data>-audyt-kodu.md`, `07-review/<data>-audyt-inwentarz.md` | zespół audytu | eng-code-audit (pack-it) | człowiek: ranking problemów | na żądanie |
| `07-review/<data>-dlug-techniczny.md` | audytor | eng-tech-debt-audit (pack-it) | człowiek: priorytety długu | na żądanie |
| `07-review/<data>-poglebienia.md` | architekt | eng-module-depth (pack-it) | implementer: płytkie moduły | na żądanie |
| `07-review/<data>-przeglad-planu-<krok>.md` | recenzent zmian | qa-change-review (pack-it) | wykonawca przed realizacją | przy ryzykownym kroku |
| `07-review/<data>-facilitation.md` | coach facylitacji | ddd-facilitation (pack-it) | facylitator | po warsztacie |
| `07-review/<data>-jezyk-<dokument>.md` | redaktor | txt-polish-correctness (pack-editorial-pl) | autor dokumentu | dokumenty dla ludzi |

## 9. Utrzymanie — `08-operations/`
| Artefakt | Pisze | Skill | Czyta / po co | Mały projekt |
|---|---|---|---|---|
| `08-operations/<data>-<rodzaj>.md` (przegląd okresowy z szablonu `operations-review`, łatki, aktualizacje, wycofania) | DevOps/SRE + implementer | core-delivery-lifecycle (`references/utrzymanie.md`) | człowiek: co wymaga decyzji | przegląd co kwartał |

## Poza `docs/project/`
| Artefakt | Pisze | Czyta / po co |
|---|---|---|
| `.tf/reports/<moduł>.md` i `.tf/register/items.jsonl` | `tf analyze` (skrypty) | persona przy przeglądzie i planie poprawek; odhaczenia zostają przy ponownej analizie |
| `.tf/reports/metrics.md` | `tf metrics` | człowiek: skuteczność fabryki (reverty, koszt na przyjętą zmianę, przyczyny poprawek) |
| `.tf/logs/` (`usage.jsonl`, `hook-errors.jsonl`) | hooki | `cost_report.py`, `tf doctor` |
| `docs/project/changes/CHG-n/` | tryby z cyklem zmiany (np. mode-pdi) | persony trybu: plan i decyzje jednej zmiany |
| `docs/project/vendors/` | persony sprzętowe (np. pack-ev) | onboarding modelu urządzenia |
| `CLAUDE.md` / `AGENTS.md` | autor instrukcji (core-agent-instructions) | każdy agent w każdej sesji |

## Jak używać
- **Persona na starcie fazy** czyta wiersze swojej fazy i Przekazanie poprzedniej. Brak wymaganego pliku z
  poprzedniej fazy to pytanie do człowieka, a nie powód, żeby go zgadywać.
- **Persona na końcu fazy** sprawdza swoje wiersze: każdy artefakt jest zapisany albo opisany w Przekazaniu jako
  pominięty, z powodem.
- **Nowy skill** zapisuje wynik w istniejącym katalogu fazy i dopisuje wiersz do tej mapy. Test repozytorium
  fabryki (`tests/test_artifact_map.py`) pilnuje, że katalog istnieje, a artefakt jest w mapie.
