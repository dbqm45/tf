---
artifact: adr
phase: architecture
status: accepted
version: 1
author: tomasz-solution-architect
created: 2026-09-27
updated: 2026-09-27
inputs: [docs/project/03-requirements/requirements.md, docs/project/04-architecture/stack-decision.md]
---
# 0001. Styl architektury: modularny monolit (Spring Modulith)

## Kontekst
Jeden zespół (2 × TS/Angular, 1 × Java), MVP w 3 miesiące, niski budżet utrzymania. Scenariusze (H,H)/(H,M):
spójność rezerwacji (50 równoczesnych prób → 1 sukces), modyfikowalność (nowy typ zasobu ≤ 2 dni), dostępność 99,5% w godz. 7–19.
Żaden scenariusz nie wymaga niezależnego skalowania ani wdrażania części systemu.

## Decyzja
Jedna aplikacja Spring Boot (jedna jednostka wdrożenia, jedna baza) podzielona na moduły z małym interfejsem na krawędzi:
`identity` (Entra ID, role), `resources` (katalog zasobów i typów, polityki), `booking` (archetyp Availability: rezerwacje,
blokady serwisowe, zwalnianie no-show), `calendarsync` (ACL do Microsoft Graph). Moduły komunikują się przez publiczne API
modułu i zdarzenia aplikacyjne; granice sprawdza `ApplicationModules.verify()` w CI. Front Angular budowany osobno,
serwowany przez tę samą aplikację **[propozycja]**.

## Rozważane opcje
- Modularny monolit — zalety: najprostsze wdrożenie i obserwowalność, transakcja ACID obejmuje rezerwację i outbox, zespół zna Spring; wady: wspólne wdrożenie frontu i backendu, dyscyplina granic wymaga testów.
- Mikroserwisy (np. booking / resources / calendarsync) — zalety: niezależne wdrożenia; wady: spójność ostateczna między usługami utrudnia gwarancję „0 podwójnych”, sieć, platforma i monitoring ponad możliwości 1 programisty backendu w 3 miesiące.
- Serverless (Azure Functions) — zalety: koszt przy małym ruchu; wady: transakcje i ograniczenia bazy te same co w monolicie, ale więcej elementów, zimne starty w szczycie 9:00, słabsze wsparcie Spring.

## Konsekwencje
- Zyskujemy: jedną transakcję dla rezerwacji + zdarzenia (outbox), jeden pipeline, niski koszt.
- Tracimy: niezależne skalowanie modułów (nie jest potrzebne przy 300 użytkownikach).
- Modyfikowalność: nowy typ zasobu dotyka tylko modułu `resources` (dane + polityka); `booking` operuje na (zasób, przedział).
- Wydzielenie usługi (np. `calendarsync`) możliwe później po granicy modułu, gdy konkretny scenariusz tego zażąda — decyzja odwracalna.
- Do zrobienia: szkielet modułów + test `verify()` w pierwszej iteracji.
