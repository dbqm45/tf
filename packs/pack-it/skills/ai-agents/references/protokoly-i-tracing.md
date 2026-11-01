# Protokoły agentów i tracing w standardzie

Spis treści: 1. Mapa protokołów · 2. Bezpieczeństwo na styku protokołów · 3. Tracing wg konwencji GenAI OpenTelemetry

## 1. Mapa protokołów
| Protokół | Kto z kim | Co niesie | Kiedy |
|---|---|---|---|
| **MCP** (Model Context Protocol) | agent ↔ narzędzia i dane | narzędzia, zasoby, prompty serwera | agent ma korzystać z systemów firmy; wielu klientów tych samych narzędzi (ai-mcp-server) |
| **A2A** (Agent2Agent) | agent ↔ agent, także między dostawcami i frameworkami | **Agent Card** (nazwa, opis, wersja, interfejsy, możliwości, schematy bezpieczeństwa, umiejętności, opcjonalne podpisy; pod `/.well-known/agent-card.json`), zadania z cyklem życia | delegujesz zadanie agentowi, którego nie kontrolujesz (partner, inny zespół), a nie tylko wywołujesz funkcję |
| **ACP** (Agent Client Protocol) | edytor ↔ agent kodujący (wzorowany na LSP) | JSON-RPC 2.0; lokalnie stdio (agent jako podproces edytora), zdalnie HTTP/WebSocket — wsparcie w toku; typy JSON z MCP tam, gdzie się da, plus własne (np. diff), tekst w Markdown; agent prosi o zgodę przez `session/request_permission` | wbudowujesz własnego agenta kodującego w edytor albo edytor w agenta |

- Protokoły się **uzupełniają**: ten sam agent może być klientem MCP (narzędzia), serwerem A2A (dla innych agentów)
  i agentem ACP (w edytorze).
- **Stany zadania A2A** (`TASK_STATE_…`): `SUBMITTED`, `WORKING`; przerwane: `INPUT_REQUIRED`, `AUTH_REQUIRED`;
  końcowe: `COMPLETED`, `FAILED`, `CANCELED`, `REJECTED`. Stany przerwane projektujesz jak punkt zatwierdzenia,
  nie jak błąd. Zadanie w stanie końcowym nie przyjmuje kolejnych wiadomości.
- **Odbiór aktualizacji:** odpytywanie (`GetTask`), strumień SSE (`SendStreamingMessage`, `SubscribeToTask`; wymaga
  `capabilities.streaming`) albo webhook push (wymaga `capabilities.pushNotifications`). `SendMessage` domyślnie
  czeka do stanu końcowego lub przerwanego; `returnImmediately: true` zwraca od razu.
- **Wyniki w artefaktach, nie w wiadomościach:** wiadomości służą do rozmowy i statusu i nie są gwarantowanym kanałem
  dostarczenia; wynik zadania to `Artifact`.
- **Wersja:** klient wysyła `A2A-Version` (Major.Minor, np. `1.0`) w każdym żądaniu; brak nagłówka serwer traktuje
  jako `0.3`. Wersja 1.0 usunęła pole `kind` (typ wynika z nazwy pola, np. `{"text": …}`, `{"statusUpdate": …}`)
  i przeniosła `extendedAgentCard` do `capabilities` — klient 0.3 i serwer 1.0 bez obsługi obu formatów się nie
  dogadają.
- Zanim dodasz A2A między własnymi agentami w jednym procesie, sprawdź, czy nie wystarczy zwykłe wywołanie
  podagenta. Protokół opłaca się na granicy własności (inny zespół, inny dostawca).

## 2. Bezpieczeństwo na styku protokołów
- **Agent Card i wynik innego agenta to niezaufane wejście:** opis umiejętności może zawierać instrukcje, a wynik
  zadania — wstrzyknięcie. Traktujesz je jak wynik narzędzia: schemat, limity, bez wykonywania poleceń z treści
  (sec-llm-security, `references/wzorce-projektowe-agentow.md` §6). Podpisy kart sprawdzasz, gdy partner je
  publikuje.
- Uwierzytelnianie i uprawnienia ustawiasz osobno dla każdego styku. Token z jednego protokołu nie przechodzi do
  drugiego (agent nie przekazuje tokenu MCP agentowi A2A).
- **A2A wprost:**
  - serwer uwierzytelnia każde żądanie i zawęża `ListTasks`/`GetTask` do zadań widocznych dla wywołującego; nie
    zdradza istnienia cudzych zadań (404 zamiast 403);
  - `AUTH_REQUIRED` samo w sobie **nie jest autoryzacją** żadnej operacji; poświadczenie najlepiej poza pasmem.
    Jeśli przechodzi w pasmie przez łańcuch agentów, wiąże się je z agentem, który o nie prosił (a2a §7.6);
  - webhook push: agent waliduje URL (odrzuca adresy prywatne, localhost, link-local — ochrona przed SSRF), a klient
    sprawdza uwierzytelnienie powiadomienia, oczekiwany `taskId` i przetwarza powtórzenia idempotentnie;
  - **podpis Agent Card:** JWS (RFC 7515) na karcie skanonizowanej wg JCS (RFC 8785), klucz przez `kid`/`jku`
    z HTTPS; klient powinien sprawdzić co najmniej jeden podpis, zanim zaufa karcie;
  - rozszerzona karta (`GetExtendedAgentCard`) tylko po uwierzytelnieniu i bez wewnętrznych adresów czy sekretów.
- W ACP zgoda na zapis i polecenie terminala jest w edytorze, ale granicą nadal jest środowisko (core-agent-security).

## 3. Tracing wg konwencji GenAI OpenTelemetry
- **Jeden ślad na zadanie** (`trace_id` jako identyfikator korelacji między systemami). Wywołania modelu
  (`chat`, `generate_content`), narzędzia (`execute_tool`) i agenta (`invoke_agent`, `invoke_workflow`) to span-y
  potomne. Ponowienie to nowy span w tym samym śladzie, a rozgałęzienie lub praca w tle — `links`.
- **Atrybuty:**
  - `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`;
  - `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.usage.cache_read.input_tokens`;
  - `gen_ai.conversation.id`, `gen_ai.agent.name`, `gen_ai.tool.name`, `gen_ai.tool.call.id`.

  Konwencja nie definiuje atrybutu kosztu. Koszt liczysz z tokenów i cennika w potoku, a własne atrybuty (wynik
  guardrails, koszt) dajesz we własnej przestrzeni nazw, nie w `gen_ai.*`.
- **Treść promptów i odpowiedzi** domyślnie nie trafia do śladów; konwencja przewiduje jawne włączenie. Włączasz ją
  tylko z maskowaniem danych osobowych i z retencją ustaloną dla danych wrażliwych.
- Są też osobne konwencje dla MCP i A2A. Dzięki nim ślad przechodzi przez granicę protokołu.
- **Stan:** konwencje mają status *Development*, więc nazwy i typy atrybutów mogą się zmienić. Wersję przypinasz
  w instrumentacji, a SLO i raporty liczysz z własnego rekordu końca zadania (ops-observability, „Agent AI
  i dochodzenie po incydencie”), nie z nazw spanów.
- Ze śladów robisz ewaluację offline (ai-evals, `references/pulapki-pomiaru.md` §7) i analizę kosztu
  (core-cost-control, ops-finops).

Źródła (sprawdzone 2026-11-01 w repozytoriach na GitHubie; strony a2a-protocol.org, agentclientprotocol.com
i opentelemetry.io niedostępne z sieci sesji):
- A2A: github.com/a2aproject/A2A — wydanie 1.0.1 (2026-05-26, wersja protokołu 1.0), projekt Linux Foundation,
  `specification/a2a.proto`; treść specyfikacji z a2a-protocol.org/latest/specification przekazana przez człowieka
  2026-11-01 (§3, §7.6, §8.4, §13, załącznik A–B);
- ACP: github.com/agentclientprotocol/agent-client-protocol — stabilna wersja protokołu 1, wydanie schematu 1.14.0
  (2026-10-30), `docs/protocol/v1/transports.mdx` (stdio, Streamable HTTP w przygotowaniu), `tool-calls.mdx`; wprowadzenie z agentclientprotocol.com przekazane przez człowieka 2026-11-01;
- OpenTelemetry: github.com/open-telemetry/semantic-conventions-genai (commit 2026-10-31), `docs/gen-ai/gen-ai-spans.md`,
  `gen-ai-agent-spans.md`, `mcp.md`, `a2a.md` — status Development;
- artykuły: „Agentic Communication Protocols” (0s & 1s, 2026-05-28), D. Biswas, „Observability for the Agentic
  Harness” (2026-08-04).
