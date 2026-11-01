---
name: ai-agents
description: Użyj przy projekcie agenta LLM lub przepływu agentowego — workflow czy agent, narzędzia, MCP, kontekst, multi-agent, guardrails, limity, tracing, dobór frameworka.
metadata:
  przeglad: "2027-04-17"
  katalog: "Użyj, gdy projektujesz agenta LLM albo przepływ agentowy w kodzie — czy w ogóle potrzebny agent, wzorce workflow (prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer), projekt narzędzi (nazwy, opisy, parametry, błędy, idempotencja) i serwerów MCP, inżynieria kontekstu (co trafia do kontekstu, kompaktowanie, pamięć), kompromisy multi-agent, guardrails i uprawnienia, zatwierdzanie przez człowieka akcji nieodwracalnych, tracing i obserwowalność, warunki stopu i budżety, typowe porażki, wybór frameworka (Claude Agent SDK, LangGraph) wg kryteriów. Nie do wywołań SDK, kontraktu wyjścia i pętli narzędzi w kodzie (eng-llm-features), uruchamiania Claude Code bez nadzoru (core-async-delegation), doboru modelu i kosztu pracy z agentem (core-cost-control), bezpieczeństwa agenta-programisty (core-agent-security) ani RAG (ai-rag)."
  slowa: "agent llm, projekt agenta, agentic workflow, workflow czy agent, autonomiczny agent, multi-agent, wieloagentowy, orchestrator, subagent, narzędzia agenta, tool design, mcp server, serwer mcp, kontekst agenta, context engineering, kompaktowanie, pamięć agenta, guardrails, human in the loop, zatwierdzanie, tracing agenta, zapętlenie agenta, warunek stopu, langgraph, claude agent sdk, framework agentowy, pamięć agenta, pamięć asystenta, typy pamięci, pamięć długotrwała, asystent przywołuje nieaktualne fakty, trwałe wykonanie, Temporal, Inngest, DBOS, restart serwera agenta, kilku agentów-wykonawców, wykonawca znika w połowie, spóźniony wykonawca nadpisuje wynik, kolejka zadań agentów, dzierżawa zadania, reguła w prompcie agenta, agent sprzedażowy, zatwierdzenie kierownika przed akcją agenta, reguła naprawdę działała, agent wywołuje narzędzie, a potem pisze odpowiedź klientowi, inny limit niż zwróciło narzędzie, liczby z wyników narzędzi, rozbieżność odpowiedzi z narzędziem, wyłapać przed wysłaniem"
---

# Projekt agenta LLM — od „czy agent” do granic i obserwowalności

Agent to model, który sam wybiera kolejne kroki i narzędzia; workflow to kod, który te kroki ustala z góry.
Anthropic radzi zaczynać od najprostszego rozwiązania i dodawać złożoność tylko wtedy, gdy mierzalnie poprawia wynik.
Ten skill dotyczy **projektu**; wywołania SDK, schemat wyjścia i pętlę narzędzi w kodzie opisuje **eng-llm-features**.

## Procedura
1. **Zadanie i miara sukcesu.** Zapisz wejście, wynik, kto i kiedy go sprawdza oraz 10–20 realnych przypadków
   z oczekiwanym efektem. Bez nich nie wiesz, czy złożoność cokolwiek daje (metoda ewaluacji: **ai-evals**).
2. **Drabina złożoności.** Idź w górę dopiero po porażce niższego szczebla na przypadkach z kroku 1:
   - jedno wywołanie modelu z dobrym promptem i przykładami (lub z wyszukiwaniem: **ai-rag**);
   - **workflow** — kroki znane z góry: *prompt chaining* (kolejne kroki z bramką kodu między nimi), *routing*
     (klasyfikacja i wybór ścieżki), *parallelization* (podzadania niezależne albo głosowanie tego samego zadania),
     *orchestrator-workers* (model dzieli zadanie dynamicznie), *evaluator-optimizer* (jeden generuje, drugi krytykuje
     wg jasnego kryterium);
   - **autonomiczny agent** — liczby kroków nie da się przewidzieć, a zaufanie do decyzji modelu jest uzasadnione.
   Agent kupuje elastyczność za opóźnienie, koszt i narastanie błędów. Zadanie o stałych krokach (zgłoszenie →
   klasyfikacja → dane → szkic → kontrola) to workflow, nie agent.
3. **Narzędzia** (agent-computer interface; większość błędów agentów to błędy narzędzi):
   - mało narzędzi o wysokim poziomie (`znajdz_zamowienia_klienta`), nie lustro każdego endpointu REST; jeśli człowiek
     nie wskaże jednoznacznie, które narzędzie wybrać, model też nie wybierze;
   - nazwy z przestrzenią (`crm_zamowienia_szukaj`), parametry jednoznaczne (`customer_id`, nie `id`), opis jak dla
     nowego współpracownika: kiedy użyć, formaty, granice względem podobnych narzędzi, przykład;
   - *poka-yoke*: taki kształt argumentów, w którym trudno się pomylić (ścieżki bezwzględne, enum zamiast tekstu);
   - wynik z czytelnymi nazwami zamiast surowych UUID, ze stronicowaniem, filtrem i limitem długości; opcjonalnie
     `response_format: concise|detailed`;
   - błąd **podpowiada naprawę** („brak pola `data_od` w formacie RRRR-MM-DD”), a nie zwraca stos wywołań;
   - narzędzia zapisu **idempotentne** (klucz idempotencji z wywołania), bo po timeoucie agent ponowi akcję;
   - narzędzia sprawdzasz zadaniami wieloetapowymi z weryfikowalnym wynikiem; liczysz wywołania, błędy i tokeny,
     czytasz transkrypty i poprawiasz opisy (drobna zmiana opisu potrafi dużo zmienić).
   Wystawiasz narzędzia przez **serwer MCP**, gdy korzysta z nich wielu klientów; ta sama zasada: narzędzia
   zorientowane na zadanie, nie na endpointy. Zaufanie do cudzych serwerów MCP: **core-agent-security**; budowa,
   bezpieczeństwo, testy i wersje własnego serwera: **ai-mcp-server**.
4. **Kontekst** (okno jest zasobem skończonym, jakość spada, gdy się zapełnia): do kontekstu trafia minimum, które
   pozwala na kolejny krok. Techniki: ładowanie na żądanie (agent trzyma ścieżki i zapytania, a treść pobiera
   narzędziem), usuwanie starych wyników narzędzi, **kompaktowanie** (streszczenie rozmowy w nowym oknie), notatki
   poza oknem (plik postępu, lista zadań), subagenci z czystym kontekstem zwracający krótkie streszczenie. Stan,
   który ma przetrwać sesję, zapisujesz poza kontekstem.
5. **Multi-agent — tylko z uzasadnieniem.** Anthropic (czerwiec 2025): agent zużywa ok. 4×, a system wieloagentowy
   ok. 15× więcej tokenów niż czat; opłaca się przy zadaniach szerokich i równoległych o wysokiej wartości
   (badanie wielu źródeł). Kodowanie ma mniej naprawdę równoległych części, a koordynacja i delegowanie przez modele
   bywają słabe. Test: czy podzadania są niezależne, czy wynik uzasadnia wielokrotny koszt, czy jeden agent
   z lepszymi narzędziami nie wystarczy. Subagent dostaje cel, format wyniku, granice i narzędzia — nie „zbadaj to”.
6. **Guardrails i uprawnienia.** Zasada najmniejszych uprawnień per narzędzie; narzędzia tylko do odczytu domyślnie.
   Akcje **nieodwracalne lub kosztowne** (przelew, usunięcie, wysyłka na zewnątrz, deploy) wymagają zatwierdzenia
   człowieka z pokazaniem dokładnego skutku, albo są wykonywane dopiero po twardej walidacji w kodzie (limit kwoty,
   lista dozwolonych odbiorców). Treść z maili, stron i dokumentów to dane, nie polecenia — agent nie dostaje
   narzędzia, które by je wykonało, razem z dostępem do danych poufnych i kanałem wyjścia na zewnątrz jednocześnie.
7. **Stop i budżet.** Zawsze: maksymalna liczba kroków, budżet kosztu i czasu na przebieg, wykrywanie powtarzanych
   tych samych wywołań, wyraźny stan końcowy (zrobione / nie da się / potrzebny człowiek). Po osiągnięciu limitu
   agent oddaje stan i powód, a nie urywa się po cichu. Szczegóły liczenia w kodzie: **eng-llm-features**, dobór
   modeli: **core-cost-control**.
8. **Tracing.** Każdy przebieg ma identyfikator; zapisujesz kroki: wejście, wywołanie narzędzia z argumentami
   i wynikiem, tokeny, czas, powód zakończenia. Bez tego nie zdiagnozujesz zapętlenia ani złej decyzji (ogólnie:
   **ops-observability**; dane osobowe w śladach maskuj). Pamięć długotrwała to kilka kontraktów (semantyczna,
   epizodyczna, proceduralna, profil, robocza), a nie jeden indeks wektorowy; trwałe wykonanie zależy od granic
   kroków — `references/pamiec-i-trwale-wykonanie.md`. Błędy stanu się kumulują, więc projektuj wznawianie
   od punktu kontrolnego zamiast restartu od zera.
9. **Framework wg kryteriów.** Zacznij od surowego API i pętli, jeśli przypadek jest prosty. Kryteria: potrzebny
   trwały stan i wznawianie? sterowanie grafem i punkty zatwierdzenia? gotowe narzędzia plików i basha? wymienność
   modeli? obserwowalność? ile abstrakcji ukrywa prompty? Claude Agent SDK daje gotowy harness (narzędzia, sesje,
   kompaktowanie), LangGraph — jawny graf stanu z punktami kontrolnymi i przerwaniami dla człowieka. Wersje i API
   sprawdź w dokumentacji i w paczce (core-grounding).

Agent, który obsługuje program (desktop, przeglądarka): **najpierw podnieś interfejs**, zrzuty ekranu na końcu —
`references/porazki-i-wzorce.md` §„Agent obsługujący program”.

Kilku wykonawców nad wspólnym stanem (dzierżawa, wersja rekordu, ponowienie / wznowienie / kompensacja), „kto jest
świadkiem tego kroku” (reguła o stanie, akcji lub sekwencji poza modelem), długie przebiegi w wielu oknach kontekstu
i interfejs harnessu, kontrola liczb z narzędzi przed odpowiedzią, sonda end-to-end: `references/wykonawcy-i-bramki.md`.

Typowe porażki i środki: `references/porazki-i-wzorce.md`.

## Przykład
**Wejście:** „Agent do reklamacji: czyta maila, sprawdza zamówienie w CRM, pisze odpowiedź, w razie zwrotu >500 zł
zleca przelew.”
**Wynik:**
- kroki znane → workflow: routing (reklamacja/pytanie) → pobranie zamówienia → szkic → evaluator-optimizer (1 poprawka);
  agent nie jest potrzebny, multi-agent tym bardziej (koszt ok. 15×);
- narzędzia: `crm_zamowienie_pobierz`, `zwrot_przygotuj` (zapis, idempotentny po `reklamacja_id`); nie 40 endpointów;
- zwrot >500 zł: tylko po zatwierdzeniu człowieka z podsumowaniem skutku; limit kwoty egzekwuje kod;
- treść maila to dane; agent nie ma narzędzia „wyślij na dowolny adres”;
- limity: 6 kroków, budżet na przebieg, ślad każdego kroku; 15 przypadków testowych (w tym mail z podłożonym poleceniem).

## Checklista
- [ ] przypadki z oczekiwanym wynikiem; najprostszy szczebel, który je zalicza, wybrany świadomie
- [ ] narzędzia: mało, o wysokim poziomie, z opisem „kiedy”, czytelne błędy, zapisy idempotentne
- [ ] kontekst: minimum, ładowanie na żądanie, plan kompaktowania i notatek
- [ ] multi-agent tylko z uzasadnieniem kosztu (ok. 15×) i niezależnych podzadań
- [ ] akcje nieodwracalne za zatwierdzeniem człowieka lub twardą walidacją; treść = dane
- [ ] limit kroków, budżet, wykrywanie pętli, jawny stan końcowy
- [ ] tracing każdego kroku; wznawianie od punktu kontrolnego
- [ ] framework wybrany kryteriami, nie marką

## Źródła
- Anthropic, „Building effective agents” (19.12.2024, dostęp 2026-10-17): wzorce workflow, ACI, poka-yoke, ścieżki
  bezwzględne, limity iteracji, testy w sandboxie.
- Anthropic, „How we built our multi-agent research system” (13.06.2025, dostęp 2026-10-17): ok. 4× i ok. 15× tokenów,
  mniej równoległości w kodowaniu, tracing, wznawianie, rainbow deployments.
- Anthropic, „Writing effective tools for agents” (11.09.2025, dostęp 2026-10-17): konsolidacja narzędzi, przestrzenie
  nazw, czytelne identyfikatory, `response_format`, czytelne błędy, ewaluacja narzędzi.
- Anthropic, „Effective context engineering for AI agents” (29.09.2025, dostęp 2026-10-17): kompaktowanie, notatki,
  subagenci, ładowanie na żądanie.
- [niezweryfikowane] opis możliwości LangGraph i Claude Agent SDK w kroku 9 — z wiedzy ogólnej, sprawdź w dokumentacji.

Opisane własnymi słowami.
