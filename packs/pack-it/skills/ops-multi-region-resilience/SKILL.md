---
name: ops-multi-region-resilience
description: Użyj przy projekcie HA i DR na strefy i regiony — RTO/RPO per tier, strategie DR, replikacja, failover, testy DR.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj przy projektowaniu odporności na awarię strefy lub regionu — wpływ biznesowy i RTO/RPO per tier usług, wybór strategii DR (backup and restore, pilot light, warm standby, multi-site active-active) z kosztem, replikacja danych (synchroniczna i asynchroniczna, spójność, konflikty, split-brain), kierowanie ruchu i failover (DNS, globalne load balancery, ponowienia klientów), zależność od płaszczyzny sterowania regionu i static stability, runbooki failover i failback, testy DR i game days, eksperymenty chaos z limitem zasięgu, dowody dla audytora. Wynik to projekt odporności z tabelą tierów i planem testów DR. Nie do SLO, budżetu błędów, incydentów i podstaw kopii zapasowych (ops-sre-incidents), scenariuszy dostępności jako atrybutu jakości (arch-quality-attributes), replikacji w samej bazie (be-database) ani strategii wydań (ops-release-engineering)."
  slowa: "awaria całego regionu, region chmury padł, strategia DR, jaką strategię DR wybrać, ile może stać system, disaster recovery, DR, awaria regionu, awaria strefy, multi-region, wieloregionowy, failover, failback, RTO, RPO, pilot light, warm standby, active-active, active-passive, split-brain, replikacja między regionami, plan ciągłości działania, BCP, game day, test DR, chaos engineering, static stability, Route 53 health check, globalny load balancer, drugi region, ćwiczenie awarii"
  widocznosc: nazwa
---

# Odporność wielostrefowa i wieloregionowa (HA/DR)

**Granica.** SLO, budżet błędów, incydenty i podstawy kopii (RPO/RTO, test odtworzenia) — **ops-sre-incidents**.
Scenariusz dostępności jako czynnik architektury — **arch-quality-attributes**. Replikacja w silniku bazy — **be-database**.
Ten skill zaczyna tam, gdzie pada pytanie „co, gdy padnie cała strefa albo region, i jak to udowodnimy?”.
Zmiany w prawdziwej infrastrukturze (przełączenie ruchu, test na produkcji) proponujesz jako plan z oknem zmian
i wykonujesz tylko po zatwierdzeniu przez człowieka.

## Procedura
1. **Wpływ biznesowy → tiery.** Dla każdej usługi (ścieżki użytkownika): koszt godziny przestoju, dopuszczalna utrata danych,
   wymogi prawne (np. DORA/NIS2 — sec-eu-regulations), zależności (w górę i w dół). Z tego **RTO** (czas do przywrócenia)
   i **RPO** (okno utraconych danych). Usługi grupuj w 3–4 tiery; cel dotyczy tieru, nie pojedynczego zespołu.
   Zależność nie może mieć słabszego tieru niż usługa, która od niej zależy — inaczej cel jest fikcją.
2. **Zakres awarii.** Rozdziel: awaria instancji, strefy (AZ), regionu, dostawcy, błąd ludzki lub złośliwa zmiana
   (replikacja powiela też usunięcie i uszkodzenie — potrzebna jest kopia niezmienialna, ops-sre-incidents).
   Wielostrefowość (HA) chroni przed strefą; region wymaga DR. Region to nie zawsze cel: jeśli SLO i prawo go nie wymagają, zatrzymaj się na strefach.
3. **Strategia DR per tier** (cztery strategie z whitepaperu AWS „Disaster Recovery of Workloads on AWS”; nazwy używane też poza AWS):

| Strategia | Co działa w drugim regionie | Odtwarzanie | Koszt i złożoność |
|---|---|---|---|
| backup and restore | tylko kopie (poza regionem) | odbudowa infrastruktury i danych z kopii | najniższe |
| pilot light | dane replikowane, rdzeń gotowy, obliczenia wyłączone | uruchomienie i skalowanie przy awarii | niskie |
| warm standby | pomniejszona, w pełni działająca kopia | skalowanie w górę przy awarii | średnie |
| multi-site active-active | pełna obsługa ruchu w obu regionach | brak „przełączenia” — wypada jeden region | najwyższe, w tym spójność danych |

   Orientacyjnie: im niższe RTO/RPO, tym drożej, a progi między strategiami zależą od systemu — własne RTO/RPO mierz testem,
   nie czytaj z tabeli. Warm standby i active-active mają sens tylko dla tieru 0–1; reszta zwykle backup lub pilot light.
4. **Dane.** Dla każdego magazynu wybierz replikację:
   - **synchroniczna** — RPO≈0, ale opóźnienie zapisu rośnie z odległością i awaria łącza blokuje zapisy;
   - **asynchroniczna** — niski koszt opóźnienia, RPO>0 (zmierz lag i alarmuj), przy failover możliwa utrata ostatnich zapisów;
   - **multi-writer** — wymaga reguły konfliktów (last-writer-wins gubi zapisy; CRDT, scalanie domenowe, albo przypisanie
     właściciela rekordu do regionu); bez reguły nie włączaj zapisu w dwóch miejscach.
   - **split-brain**: jeden lider z dowodem (kworum, lease, fencing token), automatyczne promowanie tylko z trzecim świadkiem poza obu regionami.
   Szczegóły silnika bazy — be-database; sesje, kolejki, cache, obiekty i sekrety też mają replikację (i własny lag).
5. **Ruch i failover.** DNS z health checkami (TTL niski, ale klienci i resolwery go przeciągają — realny czas ≥ TTL),
   globalny load balancer/anycast, ponowienia klientów z jitterem i limitem (burza ponowień po przełączeniu). Health check
   musi sprawdzać głęboko zależności krytyczne, ale bez kaskady (płytki = przełączenie zdrowego regionu; zbyt głęboki = wyłączenie obu).
   Decyzja o failover: automatyczna tylko dla jasno zdefiniowanych sygnałów; reszta ręcznie, z zapisanym właścicielem decyzji.
6. **Static stability i płaszczyzna sterowania.** Podczas awarii regionu **nie polegaj na tym, co awaria dotyka**: API
   tworzenia zasobów, konsola, autoskalowanie, IAM/SSO, rejestr obrazów, CI, narzędzie do runbooka. Zasady:
   - przełączaj ruch przez **data plane** (np. routing controls w Route 53 ARC z kluczami/endpointami zapisanymi w runbooku), nie przez konsolę;
   - pojemność w drugim regionie/strefie **wstępnie przygotowana** (w AWS: static stability — nadmiar w każdej strefie, 3+ strefy),
     a nie dokupowana w trakcie awarii (limity i brak mocy w regionie docelowym, gdy wszyscy robią to samo);
   - poświadczenia awaryjne i dostęp działają bez zależności od regionu głównego;
   - zasoby globalne dostawcy często mają region-matkę dla płaszczyzny sterowania — sprawdź w dokumentacji dostawcy [niezweryfikowane dla Twojego dostawcy].
7. **Runbooki failover i failback.** Wykonywalne polecenia, kolejność (dane → aplikacja → ruch), kryteria go/no-go, czas
   decyzji, komunikacja. **Failback** to osobny, planowany ruch: resynchronizacja danych, zatrzymanie zapisów, weryfikacja, okno zmian.
   Najpierw odtwórz redundancję po awarii, dopiero potem ogłoś koniec. Runbook z ops-sre-incidents / docs-tech-writing.
8. **Testy DR i chaos.** Plan testów rośnie stopniowo:

| Poziom | Co | Częstotliwość [przykład] |
|---|---|---|
| stół | przejście runbooka bez zmian | kwartalnie |
| odtworzenie | restore kopii do izolowanego środowiska z pomiarem RTO/RPO | kwartalnie, tier 0 częściej |
| failover w staging | pełne przełączenie w środowisku zbliżonym do produkcji | półrocznie |
| game day na produkcji | przełączenie lub awaria strefy w oknie, z obserwatorami | rocznie / po dużej zmianie |
   Eksperyment chaos: hipoteza stanu ustalonego, **limit zasięgu** (jedna strefa, % ruchu, wybrany tenant), warunki zatrzymania
   (SLO spada poniżej progu), wyłącznik awaryjny, zgoda właściciela i okno zmian. Wynik: zmierzone RTO/RPO kontra cel, luki, zadania z terminem.
9. **Dowody dla audytora** (ISO 27001/22301, DORA — sec-governance-compliance, sec-eu-regulations): tabela tierów z zatwierdzeniem biznesu,
   plan i protokoły testów z datą, zmierzone RTO/RPO, otwarte luki z właścicielem, wersjonowane runbooki. Nieprzetestowane = niezadeklarowane.
10. **Wynik** w `docs/project/`: sekcje „Tiery”, „Strategia i dane”, „Ruch i zależności”, „Plan testów DR”, „Ryzyka i koszt”.

## Przykład
Wejście: „Sklep: płatności (RTO 15 min, RPO 1 min), katalog (RTO 4 h, RPO 15 min), raporty (RTO 24 h, RPO 24 h). Jeden region.”

Wynik (fragment) [przykład, liczby ilustracyjne]:

| Tier | Usługi | RTO / RPO | Strategia | Dane | Ruch |
|---|---|---|---|---|---|
| 1 | płatności | 15 min / 1 min | warm standby w drugim regionie | asynchroniczna replika, lag < 30 s z alarmem; ręczne promowanie po kworum | DNS z niskim TTL + przełącznik data plane |
| 2 | katalog | 4 h / 15 min | pilot light | replikacja asynchroniczna + obiekty między regionami | skrypt w runbooku |
| 3 | raporty | 24 h / 24 h | backup and restore | kopia nocna poza regionem, test odtworzenia | bez zmian |
Test: odtworzenie raportów kwartalnie; failover płatności na stagingu półrocznie; game day płatności z limitem 5% ruchu i zatrzymaniem przy
spadku SLO. Luka do zamknięcia: rejestr obrazów tylko w regionie głównym (zależność w trakcie awarii).

## Checklista
- [ ] tiery z RTO/RPO zatwierdzone przez biznes; zależności nie słabsze niż usługa
- [ ] zakres awarii rozdzielony (instancja, strefa, region, błąd ludzki)
- [ ] strategia DR i koszt per tier; lag replikacji zmierzony i alarmowany
- [ ] reguła konfliktów i ochrona przed split-brain dla zapisu w wielu miejscach
- [ ] failover przez data plane, pojemność wstępnie przygotowana, dostęp awaryjny bez regionu głównego
- [ ] runbooki failover i failback wykonywalne i przetestowane
- [ ] plan testów DR z limitem zasięgu i warunkami zatrzymania; wyniki z datą
- [ ] zmiany na produkcji tylko za zgodą człowieka w oknie zmian

## Źródła
- AWS, „Disaster Recovery of Workloads on AWS: Recovery in the Cloud” (AWS Well-Architected) — cztery strategie; wyszukiwanie 2026-10-17, strona niedostępna do pobrania w sesji, opis z wyników wyszukiwania [niezweryfikowane u źródła].
- AWS Builders' Library, „Static stability using Availability Zones” (Weiss, Furr) — płaszczyzna sterowania i danych, nadmiar pojemności w 3+ strefach; 2026-10-17.
- AWS Application Recovery Controller, „Data and control planes for routing control” oraz „Best practices for routing control” — przełączanie przez data plane, TTL 60–120 s; 2026-10-17.
- AWS Well-Architected, REL11-BP05 (static stability) i REL13-BP02 (strategie odzyskiwania) — 2026-10-17.
Terminologia stosowana też u innych dostawców; progi RTO/RPO per strategia pochodzą od dostawców i różnią się — nie podano ich jako faktów.
