---
name: eng-code-audit
description: Użyj przy pełnym audycie kodu (architektura, bezpieczeństwo, jakość, dostępność, prawo) — zakres i budżet, tani skan, przeglądy równoległe, wspólny ranking.
metadata:
  katalog: "Użyj przy pełnym audycie kodu w kilku wymiarach naraz (architektura, bezpieczeństwo, jakość i dług, testy, dostępność, użyteczność, zgodność z prawem UE) — zakres i budżet zatwierdzone z góry, tani skan na najtańszym modelu, przeglądy równoległe po jednym wykonawcy na wymiar, scalenie duplikatów, ranking ryzyko × zasięg ÷ koszt naprawy, raport z dowodami i listą tego, czego nie sprawdzono. Nie do audytu samego długu technicznego (eng-tech-debt-audit) ani przeglądu jednego PR (qa-change-review)."
  przeglad: 2027-10-18
  slowa: "pełny audyt kodu, audyt aplikacji, przegląd całego kodu, audyt wielowymiarowy, audyt przed wdrożeniem, due diligence kodu, przejęcie projektu, audyt przed inwestycją, przeanalizuj cały kod, ocena jakości aplikacji, audyt bezpieczeństwa i dostępności"
---

# Pełny audyt kodu

Audyt w wielu wymiarach naraz, prowadzony jak projekt: zakres i budżet zatwierdza człowiek, tanie narzędzia robią
inwentarz, specjaliści oceniają równolegle, a główna sesja scala wyniki w jeden ranking z dowodami. Audyt niczego nie
naprawia — ustala, szereguje i przekazuje dalej.

## 1. Zakres i budżet (przed jakimkolwiek skanem)
Pokaż człowiekowi propozycję i poczekaj na zgodę:
- **Wymiary** (wybierz potrzebne, nie wszystkie z rozpędu):

| Wymiar | Wykonawca | Skille w briefie |
|---|---|---|
| architektura | `architect` (analiza) albo `tomasz-solution-architect` | arch-quality-attributes, eng-module-depth, ddd-connascence-analysis |
| bezpieczeństwo | `security-reviewer` | sec-appsec-devsecops, be-auth-security, arch-threat-modeling |
| jakość i dług | `specialist` | eng-tech-debt-audit, eng-clean-code |
| testy | `kasia-qa-analyst` | qa-test-design, qa-regression |
| dostępność | `natalia-accessibility-specialist` | ux-accessibility |
| użyteczność | `natalia-product-designer` | ux-feature-design |
| wydajność front i przeglądarki | `specialist` | fe-web-platform, fe-architecture |
| zgodność z prawem UE | `maja-product-compliance` | arch-eu-product-law, arch-privacy-compliance, sec-eu-regulations, ai-governance-compliance (gdy jest AI) |

- **Głębokość:**
  - *szybki* — etap 0 i 2–3 wymiary o największym ryzyku, wykonawcy na `sonnet`;
  - *standard* — wszystkie wybrane wymiary na `sonnet`, ranking, top 10 z propozycjami;
  - *pełny* — jak standard, a architektura i bezpieczeństwo na `opus`, duże repo dzielone na moduły.
- **Limit kosztu:** kwota albo liczba wywołań wykonawców, ustalona przez człowieka. Liczysz ją w pasku stanu lub
  `python3 factory/cost_report.py --days 1`; przy 80% limitu zatrzymujesz się i pytasz, co pominąć.
- **Granice:** czego nie ruszasz (np. `vendor/`, kod generowany), czy wolno uruchamiać narzędzia projektu, czy jest
  środowisko testowe. Skanów aktywnych (DAST, skaner portów) wobec działających systemów nie uruchamiasz bez pisemnej
  zgody (core-agent-security §5b).

**Uruchomienie po zgodzie:** workflow `/code-audit` (`.claude/workflows/code-audit.js`) przeprowadza etapy 0–2
i raport. Argumenty to zatwierdzony zakres: `{"date": "RRRR-MM-DD", "dimensions": ["architektura", "bezpieczenstwo",
"jakosc", "testy", "dostepnosc", "uzytecznosc", "wydajnosc", "prawo"], "depth": "standard", "limit": 8,
"modules": [], "exclude": ["vendor/"]}` (opcjonalnie `executors`: wymiar → agent, np. persona z tabeli).
- Ranking, duplikaty, blokery i hipotezy liczy skrypt, bez modelu.
- Wymiar bez zainstalowanych skilli i wymiar ponad limit trafiają do „Czego nie sprawdzono”.
- Wykonawcy pytają o zgodę na narzędzia jak zwykle; dłuższy przebieg bez pytań wymaga reguł `allow`.

Bez workflow (inne narzędzie, wyłączone `disableWorkflows`, sprzeczności do rozstrzygnięcia w trakcie) prowadzisz
etapy ręcznie, jak niżej.

## 2. Etap 0 — tani inwentarz (jeden wykonawca `scout` na `haiku` albo sama sesja)
Cel: jeden plik z faktami, który dostaną wszyscy przeglądający, żeby każdy nie czytał repozytorium od nowa.
1. `python3 .claude/hooks/detect_stack.py` — stack i wersje.
2. `python3 .claude/skills/eng-codebase-mapping/scripts/git_territory.py --hotspots --cochange` — gorące punkty.
3. `python3 .claude/skills/eng-codebase-mapping/scripts/code_graph.py` (Python, TS/JS) — cykle i zależności.
4. Narzędzia, które projekt **już ma** (testy, lint, typy, `npm audit`, skanery z CI) — wynik do pliku. Bez globalnych
   instalacji; brakujące narzędzie zapisujesz jako „nie sprawdzono”, a nie instalujesz po cichu.
5. Mapa modułów i punktów wejścia (eng-codebase-mapping).
Wynik: `docs/project/07-review/<data>-audyt-inwentarz.md` — stack, moduły, hotspoty, wyniki narzędzi, czego brakuje.

## 3. Etap 1 — przeglądy równoległe
- Wszyscy wykonawcy w **jednej wiadomości** (osobne konteksty, cache 5-minutowy).
- Każdy brief zawiera: zakres i moduły, ścieżkę inwentarza, skille do wczytania, jedno pytanie, format ustalenia
  i limit (np. 10 najważniejszych). Wzór briefu: `references/szablon-raportu.md`.
- Format ustalenia: ID · wymiar · plik:linia · ryzyko · zasięg · koszt naprawy · dowód · propozycja.
- „Nic istotnego w tym wymiarze” to poprawny wynik; ustaleń nie dopisuje się dla objętości.
- Wykonawca, który przekroczył zakres lub nie podał dowodów, dostaje jedno dopytanie, nie nowy przebieg od zera.

## 4. Etap 2 — scalenie i ranking (główna sesja)
1. **Duplikaty:** ustalenia o tej samej przyczynie łączysz w jedno i zostawiasz wszystkie wymiary jako etykiety
   (np. brak walidacji wejścia to bezpieczeństwo i jakość). Liczba wymiarów, które je zgłosiły, to sygnał, nie mnożnik.
2. **Dowód:** każde ustalenie ma plik:linia, wynik polecenia albo cytat z dokumentu. Bez dowodu ustalenie przenosisz
   do sekcji „Hipotezy do sprawdzenia”, poza ranking.
3. **Ranking:** priorytet = ryzyko (4 krytyczne / 3 wysokie / 2 średnie / 1 niskie) × zasięg (3 cały system lub
   wszyscy użytkownicy / 2 moduł lub grupa / 1 jedno miejsce) ÷ koszt naprawy (1 = S godziny / 2 = M dni / 4 = L tygodnie).
   Wewnątrz wymiaru „jakość i dług” kolejność ustala już formuła eng-tech-debt-audit (z częstością zmian).
4. **Blokery poza rankingiem:** wyciek danych lub sekretu, obejście autoryzacji, obowiązek prawny z terminem —
   idą na górę niezależnie od wyniku i od razu do człowieka.
5. **Sprzeczności między wykonawcami** (np. architekt chce rozdzielić moduł, a bezpieczeństwo woli jedną granicę
   zaufania) pokazujesz wprost; rozstrzyga człowiek, a decyzję trudną do odwrócenia zapisujesz jako ADR.
6. **Przekazanie:** architektura → ADR (arch-architect-practice); refaktoryzacja → eng-refactor-planning; brakujące
   testy → qa-test-design; poprawki bezpieczeństwa → sec-appsec-devsecops; prawo → arch-eu-product-law (mapa obowiązków),
   arch-privacy-compliance (RODO).
7. `python3 .claude/skills/core-grounding/scripts/grounding_check.py <raport.md>` — ścieżki i odwołania istnieją.

## 5. Raport
Plik `docs/project/07-review/<data>-audyt-kodu.md` (core-project-record), szablon w `references/szablon-raportu.md`:
1. TL;DR (≤ 7 punktów) i blokery.
2. Ranking (tabela) i top 10 z propozycją zmiany (bez wykonywania).
3. Szybkie wygrane: koszt S przy ryzyku co najmniej średnim.
4. **Czego nie sprawdzono** — wymiary pominięte, brakujące narzędzia, moduły poza zakresem. Obowiązkowo.
5. Sprzeczności i decyzje dla człowieka.
6. Koszt audytu względem budżetu (wywołania, modele, kwota z `cost_report.py`).
Ponowny audyt porównuje z poprzednim raportem: ROZWIĄZANE, NOWE, ZMIENIONE.

## Zasady
- Jedno spójne pytanie na wykonawcę; nie dzielisz jednego wymiaru między kilku bez podziału na moduły.
- Duże repo (ponad ~50 tys. linii lub więcej niż 5 modułów) w trybie pełnym: podział na moduły tylko w wymiarach,
  które tego wymagają (jakość, bezpieczeństwo); architektura zawsze patrzy na całość.
- Kodu nie wysyłasz do zewnętrznych serwisów analizy; fakty o wersjach i przepisach sprawdza `researcher`.
- Kod się nie zmienia w trakcie audytu; poprawki to osobne zadania po akceptacji rankingu.

## Przykład
**Sytuacja:** „Przejmujemy aplikację SaaS (Next.js + Python, ok. 40 tys. linii). Pełny audyt przed umową, budżet 15 USD.”
**Wynik:**
- Zakres zatwierdzony: *standard*, 6 wymiarów (bez użyteczności i wydajności), limit 8 wywołań wykonawców.
- Etap 0 na `haiku`: inwentarz z 3 hotspotami, brak skanera sekretów w CI („nie sprawdzono historii gita pod kątem
  sekretów”).
- Etap 1: 6 wykonawców w jednej wiadomości, 41 ustaleń; po scaleniu 29 (12 duplikatów, m.in. ten sam brak
  walidacji api/orders.py:88 zgłoszony przez bezpieczeństwo i jakość).
- Bloker: brak sprawdzenia właściciela zasobu w api/invoices.py:41 (ryzyko 4, zasięg 3, koszt S → 12, ale i tak bloker).
- Ranking: #2 brak etykiet w formularzu płatności (app/checkout/form.tsx:23, 3 × 3 ÷ 1 = 9); #3 cykl między
  modułami `billing` i `accounts` (3 × 2 ÷ 2 = 3).
- Czego nie sprawdzono: wydajność, użyteczność, testy obciążeniowe. Koszt: 7 wywołań, 11,40 USD z 15.

## Checklista
- [ ] zakres, głębokość i limit kosztu zatwierdzone przez człowieka przed skanem
- [ ] etap 0 na najtańszym modelu; jeden plik inwentarza dla wszystkich wykonawców
- [ ] przeglądy w jednej wiadomości; każdy brief z pytaniem, skillami, formatem i limitem ustaleń
- [ ] duplikaty scalone; każde ustalenie z dowodem, reszta w „Hipotezach”
- [ ] ranking ryzyko × zasięg ÷ koszt; blokery osobno i od razu do człowieka
- [ ] sekcja „Czego nie sprawdzono” i koszt względem budżetu w raporcie
- [ ] `grounding_check.py` bez błędów; przekazania do ADR, refaktoryzacji i testów nazwane

## Źródła
- Anthropic, „How we built our multi-agent research system” (anthropic.com/engineering, 13.06.2025) — równoległe
  podzadania z osobnymi kontekstami, koszt tokenów systemów wieloagentowych.
- Skille fabryki: eng-tech-debt-audit (format ustaleń, ponowny audyt), core-cost-control (kaskada modeli),
  core-problem-routing (doraźny zespół). Opisane własnymi słowami.
