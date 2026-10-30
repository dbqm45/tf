# Zagrożenia LLM i kontrole

Spis treści: prompt injection · eksfiltracja · sprawczość · dane i wyciek promptu · pośrednie wstrzyknięcie (Anthropic) · RAG · zużycie

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

Wyciek promptu systemowego (LLM07) — kolejność wg Anthropic („Reduce prompt leak”, platform.claude.com, odczyt
2026-10-20): najpierw nic poufnego w prompcie (czego model nie potrzebuje, tego nie dostaje), potem monitorowanie
i filtr wyjścia (wyrażenia, słowa kluczowe, tani model jako klasyfikator), regularny przegląd odpowiedzi. Utrudnianie
wycieku instrukcjami („nie ujawniaj…”) na końcu i z testem: komplikuje zadanie i może pogorszyć jakość odpowiedzi.

## Pośrednie wstrzyknięcie — zalecenia Anthropic
Źródło: „Mitigate jailbreaks and prompt injections”, platform.claude.com, odczyt 2026-10-20.
- Treść obcą (mail, strona, OCR, wynik narzędzia) podawaj w bloku wyniku narzędzia (`tool_result`), nie w prompcie
  systemowym ani w zwykłym tekście użytkownika; model traktuje instrukcje w wynikach narzędzi z rezerwą.
- W opisie narzędzia albo w samym wyniku podaj rodzaj i pochodzenie treści („treść maila od nieznanego nadawcy”).
- W prompcie systemowym napisz wprost, że treść z narzędzi, dokumentów i wyszukiwania to niezaufane dane, które nie
  zmieniają instrukcji ani prośby użytkownika.
- Obcy tekst opakuj w JSON zamiast doklejać do wolnego tekstu — escapowanie wyznacza jednoznaczną granicę.
- Własnych instrukcji nie umieszczaj w wynikach narzędzi (model może je zignorować jako podejrzane) — wyślij je
  w turze użytkownika po wyniku.
- Wynik narzędzia sprawdź tanim modelem-klasyfikatorem, zanim agent na nim zadziała; przy podejrzeniu zatrzymaj
  akcję albo poproś człowieka.
- Przed wdrożeniem red teaming z dokumentami i wynikami narzędzi zawierającymi wstrzyknięte polecenia
  (`references/red-teaming.md`).

## RAG i wektory (LLM08)
Uprawnienia dokumentów egzekwowane przy wyszukiwaniu (filtr po tożsamości), izolacja najemców w indeksie, kontrola
tego, co trafia do indeksu (zatrucie), wersjonowanie i możliwość usunięcia dokumentu. Szczegóły: `ai-rag`.

## Zużycie (LLM10)
Limity wejścia i wyjścia, maks. kroków agenta, budżet per użytkownik i per najemca, alert na koszt, ochrona przed
zapytaniami powielającymi (rekurencja narzędzi).

## SQL generowany przez model
Agent analityczny, który pisze i wykonuje SQL, to wykonanie kodu z niezaufanego wejścia. Tryb tylko do odczytu nie
chroni: SELECT potrafi czytać pliki z dysku, dołączać inne bazy i ładować rozszerzenia (w case study autora 5 z 11
ataków przeszło mimo trybu tylko do odczytu [niezweryfikowane]). Warstwy:
1. **Strażnik tekstu** przed wykonaniem: dokładnie jedno zapytanie SELECT, lista zakazanych funkcji (plikowe,
   sieciowe, `ATTACH`, ładowanie rozszerzeń), koszt planu oceniony własnym estymatorem liczby wierszy — planer silnika
   potrafi pomylić się o rzędy wielkości.
2. **Blokada w silniku**, której zapytanie nie zmieni. W DuckDB np. wyłączony dostęp zewnętrzny
   (`enable_external_access = false`), wyłączone automatyczne ładowanie rozszerzeń i zablokowana konfiguracja
   (`lock_configuration = true`); nazwy ustawień sprawdź w dokumentacji wersji z projektu.
3. **Limity** czasu i liczby zwracanych wierszy. Przerwanie zapytania działa zwykle dopiero między krokami silnika,
   więc jedno utknięte zapytanie wydłuża ogon czasu — limit ustawiasz z zapasem i mierzysz p95.
Bramka wejściowa (klasyfikator „czy odpowiadać”) zawodzi otwarcie: nieczytelna odpowiedź klasyfikatora = odmowa,
nie „odpowiadaj”.

Źródło: F. Khan, „Engineering Multi-Agent AI for a 100 GB Data Warehouse” (2026-10).
