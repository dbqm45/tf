---
artifact: decisions
phase: plan
status: draft
version: 1
author: pdi
inputs: []
change: CHG-3
---
# Decyzje zmiany CHG-3

## Przyjmujemy PRB-27 do pracy jako zmianę: licznik „Wdrożenia w ostatnich 7 dniach: N" na stronie głównej, za flagą deploy_counter (off na prod na start).
- ref: CHG-3/D1
- id: DEC-0012
- wyslano: tak
- kiedy: 2026-11-03
- kto: dbqm45 (z góry, przebieg testowy A6, zatwierdził właściciel 2026-11-03)
- rodzaj: triage
- dlaczego: Zgłoszenie opisuje realny brak miary wprost na stronie; proponowane rozwiązanie mieści się w aktualnej architekturze sdlc-proba (strona + istniejący odczyt /deployments). Ryzyko regresji ograniczone nową flagą deploy_counter, domyślnie off na prod. Przebieg testowy A6 — triaż accepted z góry zatwierdzony przez właściciela 2026-11-03.
- zrodlo: manual
- szkic: ai

## Zatwierdzamy intent CHG-3: wariant A — licznik „Wdrożenia w ostatnich 7 dniach: N" renderowany po stronie serwera, nowa funkcja `countDeployments` w `src/deployments.js`, za flagą `deploy_counter` (off na prod na start).
- ref: CHG-3/D2
- id: DEC-0013
- wyslano: tak
- kiedy: 2026-11-03
- kto: dbqm45 (z góry, przebieg testowy A6, zatwierdził właściciel 2026-11-03)
- rodzaj: gate
- dlaczego: Intent zgadza się z PRB-27 i decyzją triażu CHG-3/D1 (DEC-0012). Wariant A mieści się w decyzji DL4 (Node bez zależności, node:sqlite) i obecnej architekturze (strona + odczyt z tabeli deployments), nie powiększa API (wariant C out), a daje dokładną liczbę przy >100 wdrożeniach (czego wariant B nie gwarantuje). Trzy pytania do bramki rozstrzygamy rekomendowanymi odpowiedziami. Przebieg testowy A6, B1 approved z góry zatwierdzony przez właściciela 2026-11-03.
- zrodlo: manual
- szkic: ai
- pytanie: Właściciel aplikacji sdlc-proba: co oznacza „ostatnie 7 dni" — 7 × 24 h wstecz od chwili wyświetlenia strony (UTC) czy 7 dni kalendarzowych, i czy liczą się wszystkie wdrożenia ze środowiska, czy tylko udane?
- odpowiedz: 7 × 24 h wstecz od chwili renderowania strony w UTC (rolling window, nie dni kalendarzowe). Liczymy wszystkie wdrożenia dla danego środowiska — udane i nieudane — bo zgłoszenie mówi o tempie wdrożeń, nie o skuteczności; rozróżnienie udane/nieudane jest poza zakresem MVP.
- pytanie: Właściciel aplikacji sdlc-proba: kiedy ta zmiana jest porażką, nawet jeśli licznik działa (np. strona wolniejsza niż próg, liczba rozbieżna z /deployments, widoczna publicznie na prod)?
- odpowiedz: Porażka, gdy zachodzi którekolwiek: (a) licznik pokazuje liczbę różną od wyniku zapytania do tabeli deployments dla tego samego środowiska i okna 7×24h (test pokrywa też przypadek >100 wdrożeń); (b) flaga `deploy_counter` jest po wdrożeniu na prod `enabled: true` zamiast `false` (widoczność publiczna bez intencji); (c) istniejące testy strony z wyłączoną flagą przestają przechodzić bez zmian — strona ma wyglądać bajt w bajt jak dziś, gdy flaga off.
- pytanie: Właściciel aplikacji sdlc-proba: czy licznik ma być widoczny każdemu odwiedzającemu, czy wystarczy, że widzi go właściciel (np. tylko na test, na prod po włączeniu flagi)?
- odpowiedz: Widoczny każdemu, kto odwiedzi stronę w środowisku, w którym flaga `deploy_counter` jest włączona. Na start: włączona na test, wyłączona na prod (zgodnie z PRB-27). Prawdziwa kontrola widoczności idzie przez etapy rolloutu flagi w fazie plan — żadnej dodatkowej autoryzacji w aplikacji nie dodajemy (poza zakresem MVP).

