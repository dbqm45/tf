# Bramka przed modelami, zarządzany runtime i niezawodność

Spis treści: 1. Bramka (gateway) · 2. Ponowienia i strumień · 3. Cache wyników i wycofanie · 4. Zarządzany runtime agenta

## 1. Bramka (gateway) przed modelami
- **Trasy jawne per funkcja** (`funkcja → model, zapasowy`) z wyłącznikiem, zamiast „sprytnego” automatycznego
  routingu, którego decyzji nikt nie przewidzi.
- **Fallback tylko do modeli spełniających te same ograniczenia.** Dane przeznaczone dla modelu własnego nie mogą po
  cichu pójść do zewnętrznego dostawcy (rezydencja, umowa), a słabszy model to cicha utrata jakości. Jest też
  fallback produktowy: „pokaż dane bez streszczenia AI”.
- **Limity w tokenach, nie tylko w żądaniach:** rezerwacja `max_tokens` z góry i zwrot różnicy po odpowiedzi.
- **Budżet osobno od limitu:** przy 80% alert, przy 100% polityka wybrana z góry przez właściciela (blokada /
  tańsza trasa / zgoda z alertem).
- Logowanie treści promptów tylko po włączeniu dla trasy, z retencją. Miara „odsetek fallbacków” to wczesne
  ostrzeżenie o awarii lub degradacji.

## 2. Ponowienia i strumień
- **Ponowienia w jednej warstwie,** ze wspólnym budżetem czasu i prób na całe żądanie. Gdy każda warstwa (klient,
  bramka, orkiestrator, SDK) ponawia osobno, jedno żądanie mnoży wywołania dostawcy i pogłębia awarię.
- **Strumień:** po rozłączeniu albo anulowaniu przez klienta przerywasz generowanie u dostawcy, bo tokeny nadal
  kosztują; rozliczenie po końcu strumienia. Strumień przerwany błędem dostawcy kończy się jawnym zdarzeniem błędu
  i jest oznaczony jako częściowy — bez cichego zszywania dwóch odpowiedzi.
- Komentarz „sprawdzam zgłoszenie” to nie wynik; wynik pokazujesz po odpowiedzi usługi.

## 3. Cache wyników i wycofanie
- **Unieważnianie cache wyników:** klucz albo metadane zawierają wersję dokumentów źródłowych. Zmiana lub usunięcie
  dokumentu unieważnia odpowiedzi z cache, które na nim powstały, tak jak fragmenty w indeksie (ai-rag).
- Miary cache: odsetek trafień, zaoszczędzony koszt i opóźnienie, incydenty nieaktualnej odpowiedzi.
- **Wycofanie zmiany AI obejmuje całą konfigurację:** prompt, model, definicje narzędzi, ustawienia wyszukiwania
  i rankingu oraz **wersję indeksu** i cache wyników. Bez migawki indeksu powrót do poprzedniego promptu nie
  przywraca poprzedniego zachowania (ai-mlops). Warunki wycofania ustalasz przed wydaniem: błędy, wynik ewaluacji,
  koszt, błędne akcje narzędzi.

## 4. Zarządzany runtime agenta
Zarządzane środowiska agentów (np. Claude Managed Agents, OpenAI Agents API, Bedrock AgentCore — ceny i daty
z artykułu [niezweryfikowane]) dają pętlę „za darmo”, ale lock-in schodzi niżej:
- dialekt schematu narzędzi (zmiana nazw przez bramkę);
- format piaskownicy i płaszczyzna sterowania: obraz kontenera jest przenośny, identyfikatory środowiska i sesji nie;
- okablowanie MCP (uwierzytelnienie, mapowanie nazw);
- semantyka stanu i sesji (wygaszenie po bezczynności kasuje pamięć procesu).
Koszt migracji to rachunek za ewaluacje: regresja kontraktu narzędzi, trajektorii, stanu, polityki i środowiska
oraz ponowne policzenie jakości i kosztu. Do ADR: stan biznesowy trzymasz w systemie, który kontrolujesz, a własny
zestaw ewaluacji (przenośna definicja sukcesu) masz, zanim zaufasz śladom konkretnego runtime'u.

Źródła: A. Kumar, „Design an LLM Gateway…” (2026-10-22); J. Wąsowski, „Managed Agent Runtime Lock-In” (2026-10-07);
P. Kashyap, „AI System Design…” (2026-10-17); M. Ranjan, „Harness Engineering vs. Loop Engineering…” (2026-10).
