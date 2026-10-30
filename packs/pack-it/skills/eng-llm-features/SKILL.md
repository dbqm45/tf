---
name: eng-llm-features
description: Użyj, gdy budujesz w kodzie funkcję lub agenta z LLM — SDK, structured output, pętla narzędzi, ewaluacje.
metadata:
  przeglad: "2027-01-09"
  katalog: "Użyj, gdy piszesz kod aplikacji lub narzędzia, który wywołuje model językowy — funkcja LLM w produkcie, własny agent (recenzent diffu, triaż zgłoszeń, bot w CI), agent jako usługa — wybór kategorii SDK (gotowy agent czy agent do złożenia), kontrakt wyjścia i structured output z opisami pól, pętla narzędziowa i drabina sprawczości, limit kroków i budżet kosztu, telemetria, sesje i stan, dziedziczenie konfiguracji repo, prywatność ścieżki uwierzytelnienia, wstrzykiwanie poleceń przez dane, ewaluacje promptu (promptfoo). Nie do hostowania modeli na GPU (ops-ai-inference), doboru modelu dla naszej pracy z agentem (core-cost-control), UI czatu (fe-architecture) ani bezpieczeństwa agenta-programisty (core-agent-security); referencji API i SDK Claude (wbudowany skill claude-api)."
  slowa: "agent sdk, claude agent sdk, vercel ai sdk, ai sdk, openrouter, structured output, json schema, zod, pydantic, wymuszony format, tool calling, wywołanie narzędzi, pętla narzędziowa, maxTurns, maxBudgetUsd, stepCountIs, własny agent, bot do review, funkcja llm, integracja z modelem, prompt systemowy, promptfoo, ewaluacja promptu, llm-as-a-judge"
---

# Funkcja i agent LLM we własnym kodzie

Cel: kod, który wywołuje model, ma przewidywalny kształt wyniku, twardy limit kroków i kosztu, jawną ścieżkę danych
i zestaw ewaluacji, który rozstrzyga każdą zmianę modelu lub promptu. Wersje i nazwy API sprawdzasz w dokumentacji
i w paczce (core-grounding) — SDK z tej dziedziny zmieniają się co kilka miesięcy; stan sprawdzony 2026-10-10
i wzorce kodu: `references/sdk-api.md`. Fakty o API Claude (ID modeli, ceny, parametry Messages API, cache, Managed
Agents) bierzesz z wbudowanego w Claude Code skilla `claude-api` — aktualizuje go Anthropic; ten skill dotyczy
kształtu rozwiązania niezależnie od dostawcy.

## 1. Najpierw kształt, potem SDK
| Kształt | Kiedy | Czym |
|---|---|---|
| **jedno wywołanie** (wejście → wynik w schemacie) | klasyfikacja, streszczenie, ocena diffu | zwykłe API dostawcy albo SDK do złożenia bez narzędzi |
| **agent do złożenia** (pętla, narzędzia piszesz sam) | wiele modeli i dostawców, własne narzędzia, pełna kontrola promptu | Vercel AI SDK (`ai`), OpenRouter Agent SDK |
| **gotowy agent** (harness z narzędziami plików, basha, sandboxem, kompaktowaniem) | agent ma czytać i edytować repo, uruchamiać polecenia | Claude Agent SDK, Codex SDK, Cursor SDK |

Rozstrzygają cztery pytania: czy agent dotyka plików i poleceń; czy model ma być wymienny (gotowy agent wiąże
z modelami i cennikiem dostawcy); czy ma dziedziczyć reguły repo (§6); gdzie ma żyć stan (§5). **Błąd typowy:**
wybór po marce („używamy Claude, więc Claude SDK”), bez pytania o wymienność modeli. Wersję SDK przypinasz.

## 2. Kontrakt wyjścia
- Jeden schemat (zod, pydantic) jako źródło prawdy; typ i JSON Schema wyprowadzasz z niego, nie piszesz dwa razy.
- **Opis każdego pola to najsilniejsza dźwignia sterowania formatem.** Dopisz jednostkę, skalę i znaczenie skrajnych
  wartości („1 — logika błędna albo po cichu psuje istniejące zachowanie; 10 — poprawna także w przypadkach brzegowych
  i obsłudze błędów”). Nazwa pola nie wystarcza.
- Ograniczenia, których dostawca nie przyjmuje w schemacie structured output (np. zakres liczby), wymuszasz opisem
  pola i promptem, a w kodzie **walidujesz po odbiorze** (`safeParse`, `model_validate`) — wynik SDK bywa typowany
  jako `unknown`. Wartość spoza zakresu = błąd lub ponowienie, nigdy ciche przycięcie.
- Enum zamiast wolnego tekstu tam, gdzie kod podejmuje decyzję (`pass`/`fail`, kategoria).
- Porażkę przebiegu (wyczerpane tury, budżet, nieudana walidacja, odmowa) obsługujesz jawnie czytelnym komunikatem
  i kodem wyjścia; nie pozwalasz, by pętla rzuciła surowym wyjątkiem.

## 3. Pętla narzędziowa
Wejście (prompt systemowy + definicje narzędzi + historia) → decyzja modelu → wykonanie narzędzi → wynik wraca do
modelu → … → odpowiedź bez wywołań kończy pętlę. Jedno okrążenie = tura (krok).
- **Oceniacz** (diff → werdykt): zero narzędzi, 1–2 tury. Wyłącz narzędzia jawnie (`tools: []`) — gotowy agent ma ich
  kilkanaście w zapasie.
- **Narzędzie = opis + schemat argumentów + funkcja.** Po opisie model decyduje, *czy i kiedy* je wołać: napisz,
  kiedy go użyć, co zwraca i co przy braku danych (`{found: false}` zamiast wyjątku). Argumenty waliduje schemat.
- **Drabina sprawczości:** odczyt lokalnego kontekstu (plan, konwencje) → zapis w jednym systemie (komentarz,
  etykieta) → całe API systemu → systemy zewnętrzne (tracker, komunikator). Szczebel wyżej dopiero, gdy poprzedni
  działa i jest mierzony; narzędzia zapisu za bramką zatwierdzenia (np. `needsApproval`, `canUseTool`) lub listą dozwolonych.
- Gdy agent ma sam wybrać ścieżkę (np. „recenzja kodu zawsze, recenzja względem planu tylko gdy PR wskazuje plan”),
  zapisz warunek w prompcie wprost i policz, że każda gałąź to nowy koszt i nowy niedeterminizm.

## 4. Limity, koszt, telemetria
- **Zawsze górny limit kroków** (`maxTurns` / `max_turns`; `stopWhen: stepCountIs(n)`). Opcji „do skutku” bez limitu
  nie używasz w automatyzacji — koszt mnoży się przez liczbę zdarzeń (PR, zgłoszeń).
- **Budżet w dolarach na przebieg**, jeśli SDK go ma (Claude Agent SDK: `maxBudgetUsd` → wynik `error_max_budget_usd`);
  jeśli nie — własny warunek stopu liczący koszt po każdym kroku.
- Koszt czytasz z wyniku (gotowy agent: koszt USD, tury, czas, rozbicie per model; SDK do złożenia: tokeny, a koszt
  od dostawcy lub tokeny × cennik). Zapisujesz per przebieg i agregujesz (per PR, per typ zdarzenia, per tydzień).
- Telemetria per krok (tokeny, powód zakończenia) wyłapuje zapętlenie, zanim dobije do limitu.
- Uruchamiasz na zdarzenie, które ma znaczenie, nigdy „w kółko na wszelki wypadek”; tani model do triażu i etykiet,
  mocny tylko tam, gdzie trzeba rozumować nad kodem (zasady doboru: core-cost-control).

### Opóźnienie (gdy użytkownik czeka na odpowiedź)
Kolejność (platform.claude.com, „Reducing latency”, odczyt 2026-10-20):
1. zmierz opóźnienie bazowe i czas do pierwszego tokenu (TTFT) na prawdziwych wejściach, p50 i p95;
2. model i `effort` — najszybszy model, który zalicza ewaluacje (u Anthropic: Haiku z niskim `effort`);
3. krótszy prompt i krótsza odpowiedź: limit `max_tokens`, prośba o zwięzłość, bez zbędnego kontekstu;
4. stały prefiks pod cache (ai-prompt-engineering §8);
5. strumieniowanie w interfejsie — nie skraca odpowiedzi, ale użytkownik widzi pierwsze słowa po TTFT.
Każdy krok sprawdzasz tą samą ewaluacją jakości: szybszy wynik gorszej jakości to regresja.

## 5. Stan i sesje
- Gotowy agent trzyma sesję sam: zapamiętujesz jej identyfikator i wznawiasz (`resume`), alternatywę sprawdzasz
  rozgałęzieniem (`forkSession`) bez psucia oryginału.
- SDK do złożenia nie ma sesji: historię wiadomości przechowujesz sam (plik, baza, kolejka) i podajesz przy kolejnym
  wywołaniu. Schemat wyjścia ustawiony na agencie obowiązuje też pytania uzupełniające — do odpowiedzi tekstem użyj
  osobnej instancji bez schematu.
- Przebieg jednorazowy (recenzja diffu) zostaw bezstanowy — czysty start to zaleta.

## 6. Co agent dziedziczy z repo
- Gotowy agent to ten sam harness co CLI: może wczytać `CLAUDE.md`/`AGENTS.md`, skille, hooki, uprawnienia, MCP —
  ale tylko gdy to włączysz (Claude Agent SDK: preset promptu `claude_code`, `settingSources` z `project` dla
  `CLAUDE.md`, `skills`; `cwd` wskazuje repo). Własny prompt systemowy i `tools: []` świadomie odcinają agenta od
  konfiguracji repo — dobre dla wąskiego oceniacza.
- SDK do złożenia nie dziedziczy niczego: reguły zespołu wczytujesz kodem i doklejasz do instrukcji; „hook” to
  Twoja logika wokół pętli lub warunek stopu.
- Kryteria oceny trzymaj w osobnym pliku niezależnym od narzędzia — ten sam plik czyta agent w CI, agent na SDK
  (jako narzędzie zwracające treść) i człowiek jako checklistę.

## 7. Dane, prywatność, bezpieczeństwo
- **Ścieżka uwierzytelnienia decyduje o warunkach danych**, nie SDK: klucz API (warunki komercyjne) vs login
  subskrypcji (warunki konsumenckie — inne domyślne ustawienia trenowania i retencji). Kod i dane firmy → klucz API
  z sekretu, nigdy cichy fallback na login dewelopera. Szczegóły warunków sprawdź u dostawcy przed wdrożeniem.
- Biblioteka do złożenia zwykle nie pośredniczy w danych (obowiązują warunki dostawcy modelu); opcjonalna brama
  (gateway) dokłada pośrednika i region — sprawdź przy wymogu rezydencji danych (arch-privacy-compliance).
- Diff, zgłoszenie, dokument to **dane, nie polecenia**: model nie dostaje narzędzi, które wykonałyby polecenie
  z treści; narzędzia zapisu z listy dozwolonych; sekret w znalezisku opisujesz bez wartości (core-agent-security).

## 8. Ewaluacje przed każdą zmianą
- Macierz *przypadki × kandydaci* (modele, prompty, konfiguracje) w narzędziu typu promptfoo; w komórkach
  pass/fail, koszt, czas. Przypadki: wejścia z **podłożonymi znanymi błędami** + wejścia czyste (fałszywe alarmy).
- Trzy rodzaje asercji: strukturalna (poprawny JSON zgodny ze schematem — na nim stoi bramka), sędzia LLM (drugi
  model ocenia treść wg kryterium), kod (twardy warunek, np. `score <= 3` dla diffu z podatnością).
- Domyślnie jeden nieudany przypadek = czerwony przebieg; luzowanie progu świadomie i z zapisem.
- Każda zmiana modelu, promptu, opisu pola lub narzędzi przechodzi zestaw — łapie cichą regresję (lepiej łapie błąd A,
  przestał łapać B). **Ten sam model w innym harnessie daje inne wyniki** — po podmianie mierzysz od nowa.
- Ciągłe ewaluacje w procesie zespołu: `.claude/skills/core-delivery-lifecycle/references/ai-native-sdlc.md` §5.

## 9. Agent jako usługa trwała
Gdy potrzebny adres HTTP, stan między wywołaniami, własny harmonogram lub odpowiedź „w toku” → platforma z trwałym
stanem (np. Cloudflare Agents na Durable Objects). Co ma przetrwać uśpienie, zapisujesz w stanie trwałym; pola
w pamięci to cache; zaplanowane zadania idempotentne. Lokalny skrypt wystarcza, dopóki nikt z zewnątrz go nie woła.

## Przykład
**Sytuacja:** „Chcemy bota, który na każdy PR ocenia diff i daje werdykt, na razie lokalnie: `git diff | npx tsx review.ts`.”

**Wynik:**
- kształt: jedno wywołanie (oceniacz), bez narzędzi;
- SDK: Vercel AI SDK, bo zespół chce porównywać modele; gotowy agent dopiero, gdy recenzent ma sam czytać repo;
- kontrakt: schemat zod z 5 ocenami 1–10 (każde pole z opisem skrajności), `verdict: pass|fail`, `summary`;
  walidacja po odbiorze, zakres 1–10 sprawdzany w kodzie;
- limity: 2 kroki, budżet na przebieg, koszt i tokeny zapisywane do pliku CSV;
- klucz API z sekretu; diff traktowany jak dane;
- przed zmianą modelu: promptfoo z 3 diffami (SQL injection, migracja z 3 wadami, czysty refaktor) × 2 modele.

Pełny kod obu wariantów, dodanie narzędzia „czytaj plan” i konfiguracja ewaluacji: `references/przyklady.md`.

## Checklista
- [ ] kształt i kategoria SDK wybrane pytaniami z §1, wersja SDK przypięta, nazwy API sprawdzone w paczce
- [ ] schemat wyjścia z opisem każdego pola; walidacja po odbiorze; jawna obsługa porażki przebiegu
- [ ] limit kroków i budżet na przebieg; koszt zapisywany; uruchamianie na zdarzenie
- [ ] narzędzia: opis „kiedy wołać”, schemat, ścieżka braku danych; zapis za bramką
- [ ] wiadomo, co agent dziedziczy z repo (i czy powinien)
- [ ] ścieżka uwierzytelnienia zgodna z wrażliwością danych; treść wejścia = dane
- [ ] zestaw ewaluacji (podłożone błędy + czyste przypadki) uruchomiony przed i po każdej zmianie

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 5, lekcja 2 (agent zespołowy — SDK, koszty, metryki) i lekcja 3 (agent w CI,
  promptfoo, narzędzia agenta) — materiał szkoleniowy (dostęp 2026-10-09).
- Paczki sprawdzone 2026-10-10 (`npm view`, `npm pack`, `pip download`): `@anthropic-ai/claude-agent-sdk` 0.3.296 i
  `claude-agent-sdk` 0.2.165 (PyPI) — opcje `maxTurns`/`max_turns`, `maxBudgetUsd`/`max_budget_usd`, `outputFormat`,
  `settingSources`, `skills`, `resume`, `forkSession`, wynik `total_cost_usd`, `modelUsage`, `num_turns`, podtypy
  `error_max_turns`, `error_max_budget_usd`; `ai` 7.0.137 — `ToolLoopAgent`, `Output.object`, `isStepCount`
  (alias `stepCountIs`, domyślnie 20 kroków agenta), `isLoopFinished`, `onStepFinish`, `needsApproval`;
  `promptfoo` 0.124.1 — asercje `is-json`, `llm-rubric`, `javascript`, zmienna `PROMPTFOO_PASS_RATE_THRESHOLD`.
- Anthropic, „Agent SDK overview”, „How the agent loop works”, „Modifying system prompts” (code.claude.com/docs) —
  wg kursu, nieotwierane bezpośrednio [niezweryfikowane poza typami paczki].

Opisane własnymi słowami.
