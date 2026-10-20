---
name: ops-cloud-migration
description: Użyj przy migracji obciążeń do chmury lub między środowiskami — portfel, strategie 7R, fale, dane, cutover, rollback.
metadata:
  przeglad: 2027-04-17
  widocznosc: nazwa
  katalog: "Użyj, gdy planujesz przeniesienie aplikacji, baz lub całego centrum danych do chmury albo między chmurami i środowiskami — discovery i ocena portfela (zależności, grawitacja danych, licencje), strategie 7R (retire, retain, rehost, relocate, replatform, repurchase, refactor), fale i grupy przenoszenia, pilot, migracja danych (transfer offline, replikacja, podwójny zapis, cutover z budżetem przestoju), runbook przełączenia i plan wycofania, łączność hybrydowa, kryteria sukcesu, optymalizacja po migracji, typowe błędy. Wynik to plan migracji z falami i runbookiem cutover. Nie do strategii wydań (ops-release-engineering), migracji schematu bazy (be-database), wzorca Strangler w kodzie (eng-refactor-planning) ani budowy fundamentu chmury (ops-cloud-landing-zones)."
  slowa: "migracja do chmury, cloud migration, lift and shift, 7R, rehost, replatform, refactor, repurchase, retire, retain, relocate, fale migracji, wave planning, discovery, portfel aplikacji, przeniesienie serwerowni, cutover, rollback, przełączenie, okno przestoju, replikacja danych, DMS, migracja bazy do chmury, połączenie hybrydowe, Direct Connect, ExpressRoute, migracja między chmurami"
---

# Migracja do chmury: portfel, fale, cutover

Cel: przenieść obciążenia przewidywalnie, z odwracalnym przełączeniem i dowodem, że po migracji jest nie gorzej.
Wynik: `docs/project/05-delivery/migration-plan.md` (core-project-record): portfel ze strategią, fale, plan danych,
runbook cutover, kryteria sukcesu. Fundament docelowy (konta, sieć, tożsamość) to ops-cloud-landing-zones i musi
istnieć przed pierwszą falą. Skill niczego nie przełącza: zmiany na produkcji idą z planem, oknem zmian i zgodą
człowieka; każdy krok ma właściciela.

## Procedura
1. **Cel i ograniczenia.** Po co migrujemy (wyjście z centrum danych z datą kontraktu, koszt, skalowanie, regulacje)
   i co jest nieprzekraczalne (data, budżet przestoju, rezydencja danych). Cel „bo chmura” nie pozwala wybrać strategii.
2. **Discovery.** Inwentarz: serwery, aplikacje, bazy, **zależności** (ruch sieciowy, kto z kim rozmawia — z
   obserwacji przez co najmniej pełny cykl biznesowy, np. koniec miesiąca, a nie z dokumentacji), właściciele,
   system operacyjny i wsparcie producenta, **licencje** (czy wolno uruchomić w chmurze, model per rdzeń/socket),
   **grawitacja danych** (rozmiar, tempo zmian, kto je czyta), wymagania: RPO/RTO, opóźnienie, zgodność.
   Narzędzia dostawców (AWS Application Discovery Service / Migration Hub, Azure Migrate, Google Migration Center)
   [niezweryfikowane: bieżące nazwy i funkcje]. Luki w danych oznacz jawnie.
3. **Strategia per aplikacja (7R)**, wg AWS Prescriptive Guidance:
   | Strategia | Sens |
   |---|---|
   | retire | wyłącz, bo nikt nie używa (często kilka–kilkanaście % portfela [przykład]) |
   | retain | zostaw tam, gdzie jest (powód i data ponownej oceny) |
   | rehost | „lift and shift”, bez zmian aplikacji |
   | relocate | przeniesienie na poziomie hipernadzorcy lub kontenerów bez zakupu sprzętu i zmian aplikacji |
   | replatform | drobna optymalizacja (np. zarządzana baza) bez zmiany architektury |
   | repurchase | zamiana na inny produkt, zwykle SaaS |
   | refactor | zmiana architektury pod chmurę (kod: Strangler Fig w eng-refactor-planning) |
   Domyślnie najtańsza strategia, która spełnia cel (z kroku 1); refactor tylko gdy uzasadnia go wartość biznesowa,
   nie w ramach migracji pod presją daty. Definicje retire, retain i repurchase streszczone [niezweryfikowane: dosłowny tekst AWS];
   źródła wymieniają siedem kategorii, ale nie w każdym przewodniku identycznie (pochodzenie od Gartnera: 2011 lub 2019).
4. **Fale i grupy przenoszenia.** Grupa = aplikacje, które muszą przejść razem (silne zależności, wspólna baza,
   opóźnienie). Fala = grupy przenoszone w jednym oknie czasu. Kolejność:
   - **pilot**: 1–3 aplikacje o niskim ryzyku, ale reprezentatywne (sprawdzają proces, narzędzia, sieć i zespół);
   - potem od najprostszych i najmniej połączonych do najtrudniejszych; krytyczne i silnie powiązane na końcu;
   - limit przepustowości zespołu (ilu cutover naraz) i kalendarz biznesowy (nie w szczycie sezonu).
   Zależność między falami = wspólny wąski punkt: zapisz ją i sprawdź (np. współdzielona baza dzieli grupę).
5. **Łączność hybrydowa.** Na czas migracji obie strony widzą się: VPN lub łącze dedykowane (Direct Connect,
   ExpressRoute, Cloud Interconnect), spójna adresacja bez nakładania CIDR (rejestr z ops-cloud-landing-zones),
   DNS rozstrzygający obie strony, tożsamość dostępna po obu. Policz przepustowość i opóźnienie: aplikacja
   rozmawiająca z bazą „po drugiej stronie” często staje się wolna (wiele małych zapytań przez WAN). Łącze
   zaplanuj z zapasem i zdecyduj, kiedy jest wyłączane.
6. **Dane.** Wybór po rozmiarze, tempie zmian i budżecie przestoju (czas przełączenia):
   | Podejście | Kiedy | Uwaga |
   |---|---|---|
   | transfer offline (urządzenie fizyczne, kopia) | duże, rzadko zmieniane dane, wolne łącze | policz czas dostawy i dosyłkę różnicy |
   | jednorazowa kopia w oknie | małe dane, długie okno | prosty rollback = stare źródło |
   | replikacja ciągła (CDC, replikacja natywna, DMS) | duże i żywe dane, krótki przestój | monitoruj opóźnienie replikacji; przełączasz przy opóźnieniu ≈ 0 |
   | podwójny zapis (dual-write) | gdy nie ma replikacji; bardzo ostrożnie | ryzyko rozjazdu, wymaga rekoncyliacji; ostatnia opcja |
   Weryfikacja: liczby wierszy, sumy kontrolne, próbka biznesowa. Schemat i migracje wersji: be-database.
   Rezydencja danych i dane osobowe: arch-privacy-compliance.
7. **Cutover i runbook.** Per grupa osobny dokument: numerowane kroki z właścicielem, czasem i poleceniem;
   **freeze** zmian; ostatnia synchronizacja; test dymny; przełączenie ruchu (DNS z obniżonym wcześniej TTL, load
   balancer; wzorce wydań: ops-release-engineering); decyzja **go/no-go** z kryteriami zapisanymi z góry. Zapisz
   **punkt bez powrotu** (po nim rollback to restore, nie przełączenie) i budżet przestoju z podziałem na kroki.
   Próba generalna na kopii z zegarem; po niej poprawiony runbook.
8. **Rollback.** Plan wycofania gotowy przed cutover: warunki uruchomienia (metryki, czas), kroki, kto decyduje,
   co z danymi zapisanymi po stronie nowej (replikacja zwrotna albo utrata uzgodniona z biznesem). Źródło
   zostaje działające i niezmienne do końca okresu stabilizacji (np. 2–4 tygodnie [przykład]); wyłączane dopiero
   po akceptacji.
9. **Kryteria sukcesu i po migracji.** Przed startem zmierz bazę: opóźnienie p95, błędy, koszt, dostępność
   (ops-observability; SLO: ops-sre-incidents). Sukces = progi w tych samych miarach plus zamknięcie źródła.
   Potem optymalizacja: dopasowanie rozmiaru, rezerwacje po 1–3 miesiącach danych, tagi i budżety (ops-finops),
   wyłączenie łączy i licencji, retrospektywa fali.
10. **Zapis.** Portfel (tabela: aplikacja, strategia, grupa, fala, właściciel, ryzyko), harmonogram fal, plan danych,
    runbook i rollback per grupa, ryzyka. Status `proposed`; wykonanie po zgodzie człowieka.

## Typowe porażki
- Ukryte zależności (zadanie wsadowe raz w miesiącu, hardkodowane IP, wspólny dysk sieciowy).
- Nieobliczone opóźnienie WAN i koszt transferu danych wychodzących.
- Licencja nie przenosi się na chmurę, a wychodzi to po cutover.
- Brak próby generalnej i brak punktu bez powrotu w runbooku.
- Lift and shift bez późniejszej optymalizacji: rachunek wyższy niż w centrum danych.
- Wyłączenie źródła w dniu cutover.

## Przykład
**Sytuacja:** „Wychodzimy z serwerowni do końca marca. 120 aplikacji, baza zamówień 2 TB (zmienia się cały dzień), okno przestoju 30 minut.”
**Wynik** (fragment, liczby [przykład]):

| Aplikacja | Strategia | Grupa | Fala |
|---|---|---|---|
| intranet-stary | retire | — | 0 |
| raporty-wsadowe | rehost | G2 | 1 (pilot) |
| zamowienia + baza | replatform (baza zarządzana) | G5 | 3 |
| stary-ERP (licencja per socket) | retain do renegocjacji, ocena 2027-Q2 | — | — |

Baza zamówień: replikacja ciągła od T-14 dni; cutover w nocy: freeze → opóźnienie replikacji < 5 s → odcięcie
zapisów → synchronizacja → test dymny → DNS (TTL obniżony do 60 s dzień wcześniej). Budżet 30 min: freeze+sync 10, test 10,
DNS 5, zapas 5. Punkt bez powrotu: po pierwszym zapisie do nowej bazy; rollback do tego momentu = powrót DNS.

## Checklista
- [ ] cel i nieprzekraczalne ograniczenia; fundament docelowy gotowy
- [ ] zależności z obserwacji pełnego cyklu, licencje i grawitacja danych w inwentarzu
- [ ] strategia 7R z uzasadnieniem dla każdej aplikacji (w tym retire i retain)
- [ ] pilot reprezentatywny; grupy zależności; fale z kalendarzem biznesowym
- [ ] łączność hybrydowa: CIDR bez kolizji, DNS, przepustowość, opóźnienie
- [ ] metoda danych dobrana do budżetu przestoju; weryfikacja zgodności danych
- [ ] runbook z go/no-go, punktem bez powrotu i próbą generalną; rollback z warunkami
- [ ] baza pomiarowa przed migracją, źródło utrzymane do końca stabilizacji
- [ ] optymalizacja i retrospektywa po fali

## Źródła
- AWS Prescriptive Guidance: strategie migracji (7R), glosariusz, szczegółowe discovery portfela — wyszukiwanie 2026-10-17,
  strony dokumentacji niedostępne bezpośrednio; definicje relocate, rehost i replatform potwierdzone, retire/retain/repurchase [niezweryfikowane]
- Microsoft Learn: Cloud Adoption Framework (Migrate); Google Cloud: Migration Center i przewodniki migracji — nie sprawdzano szczegółowo
  [niezweryfikowane]
