# Wzorce projektowe bezpiecznych agentów

Spis treści: 1. Reguła dwóch · 2. Wzorce izolacji (Beurer-Kellner i in.) · 3. Kontrola przepływu informacji (CaMeL) ·
4. Zgoda związana z argumentami · 5. Poświadczenia i manifest narzędzi · 6. Przekazania między agentami ·
7. Pamięć i RAG jako niezaufane

Wspólna idea: gdy niezaufana treść weszła do agenta, system ma być tak zbudowany, żeby nie mogła ona wywołać
działania o skutkach. Wymusza to kod i architektura, nie prompt.

## 1. Reguła dwóch
Meta, „Agents Rule of Two” (2025-10-31): dopóki wstrzyknięć nie da się wiarygodnie wykrywać, jedna sesja agenta ma
najwyżej **dwie z trzech** cech:
| Cecha | Przykład |
|---|---|
| A. przetwarza niezaufane wejście | e-maile, strony, dokumenty od klientów, wyniki wyszukiwania |
| B. ma dostęp do danych wrażliwych lub systemów | dysk firmowy, baza klientów, sekrety |
| C. zmienia stan albo komunikuje się na zewnątrz | wysyłka e-maila, zapis, płatność, żądanie HTTP |

Sesja z wszystkimi trzema → rozdziel na dwie sesje albo dodaj zatwierdzenie człowieka przed C. Reguła uzupełnia
„potrójną kombinację” (SKILL.md krok 2) o zmianę stanu i nie zastępuje najmniejszych uprawnień — Meta zaznacza, że
nie pokrywa nadmiernych uprawnień ani halucynacji.

## 2. Wzorce izolacji
Beurer-Kellner i in., „Design Patterns for Securing LLM Agents against Prompt Injections” (arXiv 2506.08837,
2025-06, v3 2025-06-27). Nazwy i liczbę wzorców podaję za streszczeniami pracy; przed cytowaniem sprawdź PDF.
| Wzorzec | Jak działa | Kiedy | Koszt |
|---|---|---|---|
| **action-selector** | model wybiera jedną akcję z zamkniętej listy, wynik narzędzia nie wraca do modelu | bot z menu operacji | brak elastyczności |
| **plan-then-execute** | plan (lista wywołań i adresatów) zamrożony przed odczytem obcych treści; dane z treści wypełniają argumenty, ale nie wybierają akcji ani adresata | asystent e-maila, kalendarza | plan nie reaguje na treść |
| **map-reduce** | każdy dokument przetwarza osobny izolowany przebieg z ustrukturyzowanym wynikiem; agregacja nie widzi surowych treści | przegląd wielu dokumentów | więcej wywołań |
| **podwójny LLM** | model *uprzywilejowany* (z narzędziami) nie widzi obcej treści; model *w kwarantannie* (bez narzędzi) ją czyta i oddaje tylko pola schematu — symbole, nie prozę | streszczenia, ekstrakcja | dwa wywołania, kod pośredniczący |
| **code-then-execute** | model pisze program (np. w ograniczonym języku), który wykonuje się bez dalszego udziału modelu w decyzjach | stałe przepływy danych | trudniejsze debugowanie |
| **minimalizacja kontekstu** | po ustaleniu intencji usuwasz z kontekstu treść, która mogła ją zmienić | rozmowa wieloetapowa | utrata kontekstu |

Przykład w kodzie (podwójny LLM, szkic):
```python
summary = quarantined_llm(email_body, schema={"type": "object", "additionalProperties": False,
    "properties": {"topic": {"enum": ["faktura", "reklamacja", "inne"]},
                   "invoice_id": {"type": "string", "pattern": "^FV/[0-9]{4}/[0-9]+$"}}})
validate(summary)                     # w kodzie; niezgodność = odrzucenie
recipient = customer_db.owner_of(summary["invoice_id"])   # adresat z naszych danych, nigdy z treści e-maila
privileged_llm.draft_reply(topic=summary["topic"], to=recipient)
```

## 3. Kontrola przepływu informacji (CaMeL)
Debenedetti i in., „Defeating Prompt Injections by Design” (arXiv 2503.18813, 2025-03, v2 2025-06). Wartości niosą
**etykietę pochodzenia i dozwolonych odbiorców**; interpreter sprawdza politykę przed każdym wywołaniem narzędzia
(np. dokument z dysku można streścić użytkownikowi, ale nie wysłać na adres znaleziony w tym dokumencie). Koszt
użyteczności według autorów: na AgentDojo 77% zadań z gwarancją bezpieczeństwa wobec 84% bez obrony.

## 4. Zgoda związana z argumentami
Zgoda człowieka obejmuje **skrót kanonicznych argumentów** (np. SHA-256 posortowanego JSON-a z kwotą, kontem,
walutą), aktora, narzędzie, termin ważności i jednorazowy nonce. Wykonanie sprawdza skrót; inne argumenty = nowa
zgoda. Brak polityki dla narzędzia albo nieudany zapis audytu = brak wywołania (zamknięcie bezpieczne). Narzędzia mają
klasy ryzyka (niskie, średnie, wysokie, krytyczne) z domyślną odmową dla nieznanego narzędzia. Człowiek widzi surowe
argumenty, nie opis wygenerowany przez model.

## 5. Poświadczenia i manifest narzędzi
- **Krótkotrwałe poświadczenia na jedno wywołanie:** broker poza procesem agenta wydaje token związany z narzędziem
  i argumentami; agent nie trzyma długich kluczy.
- **Przypięty skrót manifestu narzędzia MCP** (opis i schemat): zmiana opisu lub schematu = nowa instalacja do
  przeglądu, nie cicha aktualizacja (core-agent-security §4).

## 6. Przekazania między agentami
Agent czytający obce dokumenty ma tylko odczyt, bez MCP i narzędzi zapisu, i zwraca JSON ze schematem
(`additionalProperties: false`, `maxItems`, `maxLength`, `pattern` na każdym polu), sprawdzany w kodzie przed
orkiestratorem. Prośba o przekazanie zadania (`handoff_request`) przechodzi tylko wtedy, gdy cel jest na liście
dozwolonych, a ładunek zgadza się ze schematem — dokument może zawierać podrobione bloki przekazania. Wzorzec opisany
w omówieniu repozytorium `anthropics/financial-services` (M. Craddock, 2026-05-06) [niezweryfikowane w repozytorium].

## 7. Pamięć i RAG jako niezaufane
- Zapis do pamięci długotrwałej i bazy wektorowej przechodzi przegląd (człowiek albo reguła) i dostaje etykietę
  pochodzenia; odczyt z pamięci traktujesz jak treść obcą.
- Log wywołań narzędzi zapisuje pochodzenie każdego argumentu (użytkownik, narzędzie, dokument).
- Agent ma wyłącznik awaryjny po stronie platformy (core-async-delegation §6).

Źródła (dostęp 2026-10-31, przez wyszukiwarkę; strony arXiv niedostępne z sieci sesji): arXiv 2506.08837,
arXiv 2503.18813, ai.meta.com/blog/practical-ai-agent-security (2025-10-31); artykuły wtórne: A. Dighe, „Top 4
Security design patterns for AI agents” (2026-10-08), C. Kalhara, „Building Secure AI Agents”.
