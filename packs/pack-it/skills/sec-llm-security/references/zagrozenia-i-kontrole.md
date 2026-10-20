# Zagrożenia LLM i kontrole

Spis treści: prompt injection · eksfiltracja · sprawczość · dane · RAG · zużycie

## Prompt injection (LLM01)
- **Bezpośredni**: użytkownik sam wpisuje instrukcje (jailbreak). Skutek ogranicza się zwykle do jego uprawnień, więc
  kluczowe są uprawnienia narzędzi, nie treść promptu.
- **Pośredni**: instrukcja siedzi w treści pobieranej przez system (mail, strona, PDF, komentarz w kodzie, opis
  narzędzia MCP, dokument w RAG). Napastnik nie jest użytkownikiem; to główny wektor dla agentów.
- Środek: architektura (potrójna kombinacja), nie lista zakazanych fraz.

## Eksfiltracja
Kanały: obraz markdown z adresem zawierającym dane w zapytaniu, link do kliknięcia, wywołanie narzędzia HTTP, mail,
zapis do współdzielonego dokumentu, wywołanie MCP do obcego serwera. Środki: CSP, brak zdalnych obrazów, proxy z
allow-listą, brak narzędzia z dowolnym URL, zatwierdzenie wysyłki.

## Nadmierna sprawczość (LLM06)
Trzy źródła: za dużo funkcji, za duże uprawnienia, za mało zatwierdzeń. Środek: narzędzia wąskie (zadanie, nie
„wykonaj SQL”), poświadczenia użytkownika, zatwierdzenia dla zapisu.

## Dane (LLM02, LLM07, LLM04)
Wyciek: dane treningowe lub dostrajania, kontekst z innych sesji, system prompt. Środki: separacja kontekstu per
użytkownik, brak sekretów w prompcie, minimalizacja i anonimizacja danych (`arch-privacy-compliance`), kontrola
pochodzenia danych dostrajania (`ai-fine-tuning`). Zatrucie: zapis do bazy wiedzy i pamięci agenta wymaga kontroli
źródła i przeglądu.

## RAG i wektory (LLM08)
Uprawnienia dokumentów egzekwowane przy wyszukiwaniu (filtr po tożsamości), izolacja najemców w indeksie, kontrola
tego, co trafia do indeksu (zatrucie), wersjonowanie i możliwość usunięcia dokumentu. Szczegóły: `ai-rag`.

## Zużycie (LLM10)
Limity wejścia i wyjścia, maks. kroków agenta, budżet per użytkownik i per najemca, alert na koszt, ochrona przed
zapytaniami powielającymi (rekurencja narzędzi).
