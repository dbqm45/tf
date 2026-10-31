# Pamięć agenta i trwałe wykonanie

## 1. Pięć pytań zamiast jednego indeksu wektorowego
| Pamięć | Pytanie | Kontrakt |
|---|---|---|
| robocza | co jest w bieżącym kontekście | składana z pozostałych; budżet tokenów i kolejność |
| semantyczna | co jest prawdą | źródło, data weryfikacji; konsolidacja zastępuje stary fakt, nie dokłada drugiego |
| epizodyczna | co się stało | czas, kontekst, wynik; traci przydatność, nie prawdziwość |
| proceduralna | jak to robić | wersja, przegląd, wycofanie; zapis jak merge request, bo zły wpis zmienia zachowanie w wielu zadaniach |
| profil | kim jest użytkownik | krótki dokument zawsze w promptcie, łatka w miejscu |

Fizyczny podział na osobne magazyny dopiero po objawie (przeterminowany fakt wraca jako bieżący, wpis tymczasowy
konkuruje ze stałym). Często wystarcza pole typu i daty wygaśnięcia w jednym magazynie. Odpowiedniki w fabryce:
`docs/project/lessons.md` (semantyczna), dziennik i punkty kontrolne (epizodyczna), skille zmieniane przez PR
(proceduralna). Zapis do pamięci to wejście niezaufane (sec-llm-security, `references/wzorce-projektowe-agentow.md` §7).
Źródło: J. Wąsowski, „AI Agent Memory Types…” (2026-10-08); wyniki porównań z artykułu [niezweryfikowane].

## 2. Trwałe wykonanie
Zysk zależy od **granic kroków**, nie od narzędzia:
- jeden krok na każde kosztowne wywołanie modelu lub narzędzia; jeden krok na całą pętlę to tylko kolejka z dodatkami;
- wszystko poza krokiem wykonuje się ponownie przy wznowieniu. Inngest zapisuje wynik kroku i przy kolejnym
  wywołaniu szuka go po skrócie nazwy kroku; w Temporal kod workflow musi być deterministyczny (zegar, losowość,
  HTTP tylko w aktywnościach); DBOS zapisuje punkty kontrolne kroków w Postgresie;
- **trwałość to nie idempotencja**: krok, który obciążył kartę i nie zdążył zgłosić sukcesu, wykona się drugi raz
  bez klucza idempotencji u dostawcy płatności (be-messaging-outbox).

Pułapki ustawień:
- zapis punktu kontrolnego w tle może zgubić ostatni krok;
- wznowienie z tym samym wejściem nadpisuje stan;
- brak stałego id workflow oznacza, że drugi przebieg startuje obok pierwszego;
- zmiana nazwy kroku osieroca przebiegi w toku, więc kroki wersjonujesz.

Wybór:
- agent już jest grafem → graf z checkpointerem w Postgresie;
- stan ma być w tej samej transakcji co dane → DBOS;
- dane kroków nie mogą opuścić sieci → bez usług hostowanych;
- brak zespołu platformowego → bez własnego klastra.

**Test odzyskiwania przed produkcją:** `SIGKILL` w środku przebiegu i policzenie, co wykonało się ponownie.

Źródła: P. Perrone, „Inngest vs Temporal vs DBOS vs LangGraph” (2026-09-22, artykuł sponsorowany przez Inngest);
dokumentacja Inngest (repozytorium `inngest/website`, how-functions-are-executed) i DBOS (`dbos-inc/dbos-docs`,
architecture), odczyt 2026-10-29. Szczegóły Temporal i domyślny tryb LangGraph [niezweryfikowane].
