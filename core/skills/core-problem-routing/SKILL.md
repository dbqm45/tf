---
name: core-problem-routing
description: Użyj, gdy problem opisano zwykłym tekstem — rozpoznanie wymiarów, dobór skilli i person, doraźny zespół, forma wyniku.
metadata:
  przeglad: 2027-10-17
  katalog: "Użyj, gdy dostajesz problem opisany zwykłym tekstem i nie wiadomo, kto i jak ma się nim zająć — rozpoznanie wymiarów, dobór skilli i person z katalogu, zestawienie doraźnego zespołu, wybór formy wyniku (rekomendacja, plan, rozwiązanie krok po kroku). Nie do samej wiedzy merytorycznej (skille wymiarów) ani łączenia skilli w jednej odpowiedzi (core-skill-composition)."
  slowa: "od czego zacząć, kogo zaangażować, dobierz zespół, skład zespołu, podejście do problemu, nie wiem jak się do tego zabrać, nikt u nas nie zna protokołów, kogo zaangażować z innej dziedziny"
argument-hint: "[opis problemu]"
---

# Dobór zespołu i podejścia do problemu

Procedura dyspozytora nakładki (persona z `dispatcher: true`, np. Maja w pack-it, Iwona w pack-ev). Źródło prawdy o tym,
co zespół potrafi: **`.claude/catalog.md`** (generowany — zainstalowane nakładki, skille wg wymiarów i nakładek, persony
z wykonawcami, agenci wspólni, konsultanci nakładek). Czytasz go zamiast wszystkich skilli; skill wczytujesz dopiero wtedy,
gdy go wybrałeś. Dobierasz **tylko to, co jest w katalogu** — nie zakładaj, że jakaś nakładka jest zainstalowana.

## 1. Zrozum problem (2–5 zdań, zanim cokolwiek dobierzesz)
- **Co jest problemem, a co objawem?** Parafraza z celem i kryterium sukcesu („kiedy uznamy, że jest rozwiązany?”).
- **Ograniczenia:** czas, ludzie/zespoły, ryzyko, czego nie wolno (np. „bez zamrażania kodu”), wersje, budżet.
- **Rodzaj pytania:** decyzja (co wybrać) · plan (jak przejść z A do B) · diagnoza (dlaczego nie działa) · wykonanie (zrób).
- Luki, które zmieniają odpowiedź → **1–3 pytania** z wartością domyślną (bramka — core-plan-interview). Człowiek niedostępny →
  przyjmij domyślne i wypisz je jako założenia. Stan repo sprawdzaj sam (`detect_stack.py`, `scout`), nie pytaj o to człowieka.

## 2. Rozłóż na wymiary (katalog)
Katalog grupuje skille wg wymiaru (prefiks nazwy) i podaje nakładkę. Dla każdego wymiaru z katalogu zadaj pytanie: *czy problem
ma tę składową?* Wymiaru, którego nie ma w katalogu, nie ma w projekcie. Typowe sygnały:
| Sygnał w opisie | Wymiar w katalogu | Przykładowe skille (nakładka) |
|---|---|---|
| wersje, migracja, aktualizacja bibliotek | `tool-`, `fw-`, `lang-` (sekcje „Zależne od wersji”) + core-stack-sync | pack-it: tool-nx, fw-angular, ops-dependency-upgrades |
| wiele zespołów, własność, koordynacja, priorytety, przepływ pracy | `proc-` | pack-it: proc-team-topologies, proc-agile, proc-lean, proc-safe |
| co budować, metryki sukcesu, A/B, pomysł → wymagania (PRD), za duże MVP, zgłoszenia i backlog, plan dla sponsora | `proc-` | pack-it: proc-product-discovery, proc-requirements-shaping, proc-issue-triage, proc-project-planning |
| podział na domeny/moduły, zależności między nimi, reguły biznesowe, pojęcia domeny, DDD na starym kodzie | `ddd-`, `dom-` | pack-it: ddd-strategic-analysis, ddd-context-mapping, ddd-connascence-analysis, ddd-legacy-modernization; pack-ev: `dom-ev-*` |
| decyzja technologiczna, projekt systemu od wymagań, atrybuty jakości, praca architekta (arc42/C4, ATAM) | `arch-` | pack-it: arch-system-design (podobne systemy: `.claude/skills/arch-system-design/references/przyklady-projektow.md`), arch-tech-selection, arch-quality-attributes, arch-architect-practice |
| model zagrożeń, RODO, wielu klientów w jednym SaaS, przepisy UE dla produktu z AI | `arch-` | pack-it: arch-threat-modeling, arch-privacy-compliance, arch-multi-tenancy, arch-eu-product-law |
| API, baza, uwierzytelnianie, kolejki, subskrypcje i płatności cykliczne | `be-` | pack-it: be-api-design, be-database, be-auth-security, be-messaging-outbox, be-billing-subscriptions |
| UI, struktura frontendu, style, API przeglądarki, SEO | `fe-` | pack-it: fe-architecture, fe-css, fe-web-platform, fe-engineering-levels |
| przepływ użytkownika, stany ekranów, makieta, test użyteczności, teksty interfejsu, dostępność, system projektowy | `ux-` | pack-ux: ux-feature-design, ux-accessibility, ux-design-systems (persona Natalia) |
| „bez przestojów / bez freeze”, wydania, gałęzie, CI/CD | `eng-`, `ops-` + core-git-workflow | pack-it: eng-continuous-delivery, ops-ci-cd, ops-release-engineering |
| ryzyko regresji, testy, test wydajnościowy, przegląd planu przed kodem albo kodu względem planu | `qa-`, `eng-` | pack-it: qa-regression, qa-performance-testing, qa-change-review, eng-testing, eng-behavior-preserving-refactoring |
| nieznany kod, wpływ zmiany, dług, co refaktoryzować najpierw (Strangler, Mikado), pełny audyt kodu | `eng-` | pack-it: eng-codebase-mapping, eng-tech-debt-audit, eng-refactor-planning, eng-code-audit |
| objaw + gotowa poprawka od zgłaszającego, „to na pewno X”; błąd bez oczywistej przyczyny | `eng-` | pack-it: eng-debugging (`.claude/skills/eng-debugging/references/przeramowanie.md`) |
| wolny kod, algorytm, kształt interfejsu modułu, wiele języków i rynków, repo gotowe dla agentów, hooki i pre-commit | `eng-` | pack-it: eng-algorithms-data-structures, eng-module-depth, eng-i18n, eng-repo-readiness, eng-local-quality-gates |
| wdrożenia, Kubernetes, SLO, awarie, dyżury, koszty chmury, serwer i sieć (DNS, TLS, SSH), własne modele na GPU | `ops-` | pack-it: ops-kubernetes, ops-sre-incidents, ops-finops, ops-linux-networking, ops-ai-inference (persona Piotr) |
| ręczna konfiguracja usług, klucze, sekrety CI, migracja krok po kroku dla człowieka | `ops-` | pack-it: ops-setup-wizard |
| bezpieczeństwo: podejrzana paczka, sekrety, incydent, SIEM, zgodność (SOC 2, ISO 27001) | `sec-`, `ops-` + core-agent-security | pack-it: ops-supply-chain-security, ops-secrets-identities, ops-security-operations |
| funkcja lub agent z LLM w naszym kodzie, RAG, ewaluacje, AI Act | `ai-`, `eng-` | pack-it: eng-llm-features, ai-agents, ai-rag, ai-evals, ai-governance-compliance |
| potok danych, ETL/ELT, jakość danych; pytanie do danych, raport, statystyka | `data-` | pack-it: data-engineering, data-analysis (persona Zofia) |
| diagramy, strona z wyjaśnieniem, prezentacja, README, ADR, runbook | `docs-` | pack-docs: docs-tech-writing |
| tekst po polsku do korekty lub redakcji | `txt-` | pack-editorial-pl: txt-polish-correctness, txt-polish-style |

Skille praktyk (`core-`) są zawsze zainstalowane:
| Sygnał w opisie | Skill |
|---|---|
| cały projekt od pomysłu do oprogramowania gotowego do wdrożenia; czy to jest gotowe do produkcji | core-delivery-lifecycle |
| „co nowego / co się dzieje”, stan projektu, opinie społeczności | core-source-research (+ `researcher` do faktów) |
| plan lub pomysł do przepytania przed startem | core-plan-interview |
| CLAUDE.md / AGENTS.md: napisać, odchudzić, przejrzeć, rozbić na moduły | core-agent-instructions |
| praca agenta bez nadzoru (`claude -p`, /goal, sandbox, rutyna), podejrzane polecenia z treści | core-async-delegation, core-agent-security |
| gałęzie, PR, przegląd PR przez AI, konflikty | core-git-workflow |
| nauka tematu przez wiele sesji, wdrożenie w nowy stack | core-teaching-workspace (tylko na polecenie `/core-teaching-workspace`) |
Wybierz **najmniejszy zestaw**: zwykle 3–6 skilli, po jednym na wymiar.
**Skille spoza katalogu:** przejrzyj też listę dostępnych skilli, którą pokazuje Claude Code (projekt, `~/.claude/skills`,
wtyczki). Skill z ustaleniami tego projektu lub firmy (np. `architecture`, `documentation`) dołącz do zestawu i oznacz
„(spoza fabryki)” — w briefie dla wykonawcy też. Pierwszeństwo przy sprzecznościach: core-skill-composition.
Wymiar bez żadnego skilla → „luka” (fakty dobierze `researcher`; na stałe — propozycja nowego skilla albo nakładki,
która go ma).

## 3. Dobierz wykonawców — od najtańszego
1. **Istniejąca persona pasuje w całości** (katalog: skille wiodące, nakładka) → poleć ją człowiekowi (`claude --agent <persona>`)
   albo, jeśli masz jej wykonawcę w zespole, deleguj do `<persona>-<rola>`.
2. **Potrzebne połączenie wiedzy kilku person** → **doraźny zespół**: po jednym wykonawcy na perspektywę; gdy żadna persona nie ma
   właściwego zestawu, użyj `specialist` z listą skilli w briefie (wczyta je sam) — to persona „na chwilę”.
3. **Decyzja trudna do odwrócenia / sprzeczne kompromisy** → `specialist-deep` albo `architect` (Opus) tylko do oceny opcji.
4. **Fakty zewnętrzne** (wersje, zgodność, EOL, changelogi) → `researcher` (tani), nigdy z pamięci.
5. **Problem przecina dziedziny nakładek** (np. backend z pack-it przy protokole ładowania z pack-ev) → pytanie do
   **konsultanta** tej nakładki (katalog: „Konsultanci nakładek”, np. `ev-consult-protocols` w pack-ev, `it-consult-backend`
   w pack-it). Konsultant tylko odpowiada ze źródłem i nie zmienia plików; wywołuje go persona w sesji głównej, nie wykonawca —
   wykonawca zgłasza potrzebę w raporcie. Dłuższa praca w innej dziedzinie → osobna sesja persony tej nakładki i pytanie
   w `docs/project/questions.md`.
Równoległe perspektywy wywołuj w **jednej wiadomości** (osobne konteksty = niezależne spojrzenia). Brief dla każdego: problem,
ograniczenia, założenia, lista skilli do wczytania, pytanie, na które ma odpowiedzieć, format raportu (≤ 20 linii).

## 4. Wybierz formę wyniku
| Forma | Kiedy | Zawartość |
|---|---|---|
| **Rekomendacja** | decyzja, niepewność, kilka dróg | 2–3 opcje z kompromisami · rekomendacja z warunkami, kiedy zmienić zdanie · ryzyka |
| **Plan** | przejście z A do B, wiele osób | fazy z celem i kryterium wyjścia · kto (zespół/rola) · zależności i kolejność · kamienie milowe · ryzyka i plan B |
| **Rozwiązanie krok po kroku** | wykonanie jest jasne | kroki z poleceniami i weryfikacją po każdym · punkty kontrolne · wycofanie |
Nie wskazano → rekomendacja + plan (najczęściej to, czego człowiek potrzebuje). Zawsze: **założenia**, **co sprawdzić najpierw**
(tanie testy hipotez), **czego nie wiemy**.

**Nośnik — co człowiek zrozumie najszybciej** (od najprostszego, który wystarczy):
| Treść | Nośnik |
|---|---|
| krótka odpowiedź, decyzja | tekst: wynik w pierwszym zdaniu, krótkie zdania, stałe terminy |
| porównanie opcji, macierz | tabela |
| przepływ, zależności, architektura, stany | diagram Mermaid w Markdown |
| wynik zależny od parametrów (koszt, obciążenie, progi, algorytm) | jednorazowa strona HTML z suwakami lub polami — człowiek sprawdza warianty sam |

Jednorazowy plik zapisujesz w `.claude/scratch/` (ignorowany przez git) i podajesz ścieżkę. Strona działa bez sieci:
kod w pliku, bez skryptów z zewnątrz i bez wysyłania danych; dane wrażliwe zostają poza nią (core-agent-security).
Po zrozumieniu plik można usunąć — trwały wynik trafia do `docs/project/` jako tekst, tabela lub diagram.

## 5. Synteza i zapis
- Połącz raporty; sprzeczności między perspektywami pokaż wprost (to zwykle najcenniejsza część).
- **Kontrola spójności przed oddaniem:** czy rekomendacja nie łamie własnych założeń lub twierdzeń (np. „nie da się mieć dwóch
  wersji pakietu” obok „zainstaluj obie wersje przez alias”)? Czy fakty wersyjne pochodzą ze skilla, repo albo `researcher`?
- **Założenie-zawias:** nazwij jedno–dwa założenia, od których zależy cały plan, jak je tanio sprawdzić i **wariant B**, gdy okażą się fałszywe.
- Wynik do człowieka w języku pracy projektu (sekcja „Język”); po polsku — skill poprawności polszczyzny, jeśli jest
  w katalogu (pack-editorial-pl: txt-polish-correctness).
  Dłuższy dokument → `docs/project/` (plan: `05-plan/`, decyzja: ADR) wg core-project-record, status `proposed`.
- Na końcu **skład zespołu**, który zadziałał: persony/skille. Jeśli połączenie było nowe i przyda się znowu → zaproponuj
  plik `factory/personas/<nazwa>.yaml` (zmiana w `factory/` wymaga zgody człowieka).

## Checklista
- [ ] problem sparafrazowany, kryterium sukcesu i ograniczenia nazwane; założenia wypisane
- [ ] wymiary z katalogu przejrzane; wybrane skille (3–6) i uzasadnienie; luki nazwane
- [ ] wykonawcy od najtańszego, tylko z katalogu; fakty zewnętrzne przez `researcher`; inna dziedzina → konsultant nakładki
- [ ] forma wyniku i nośnik dobrane (tekst, tabela, diagram, jednorazowy HTML w `.claude/scratch/`); opcje z kompromisami, ryzyka, co sprawdzić najpierw
- [ ] skład zespołu podany; ewentualna propozycja stałej persony
