---
name: ux-service-design
description: Użyj, gdy problem to usługa w wielu kanałach z zapleczem, nie ekran — service blueprint, mapa podróży, punkty styku, prototyp usługi.
metadata:
  przeglad: 2027-10-17
  katalog: "Użyj, gdy problem klienta rozciąga się na wiele kanałów, ludzi i zaplecze (sklep, urząd, bank, serwis, onboarding), a nie na pojedynczy ekran — service blueprint (działania klienta, frontstage, backstage, procesy wspierające, dowody, linie interakcji i widoczności), mapa podróży klienta obecna i docelowa, mapa interesariuszy, inwentarz punktów styku, spójność między kanałami, warsztat współprojektowania, prototyp usługi (odgrywanie ról, concierge, Wizard of Oz), metryki usługi i standard usług publicznych (GOV.UK Service Standard); artefakt service-blueprint.md. Nie do modelowania procesu domenowego zdarzeniami (ddd-event-storming), mapy strumienia wartości i marnotrawstwa (proc-lean), wyboru, co budować, i testów założeń (proc-product-discovery) ani przepływów ekranów i stanów (ux-feature-design)."
  slowa: "usługa, service design, projektowanie usług, service blueprint, blueprint usługi, plan usługi, frontstage, backstage, zaplecze, mapa podróży klienta, customer journey, journey map, punkty styku, touchpoint, omnichannel, wielokanałowość, spójność kanałów, interesariusze, mapa interesariuszy, współprojektowanie, co-design, warsztat z klientami, prototyp usługi, Wizard of Oz, concierge, odgrywanie ról, bodystorming, standard usług, GOV.UK Service Standard, usługa publiczna, urząd, obsługa klienta, zwroty, reklamacje od strony klienta, nikt nie widzi całości"
---

# Projektowanie usługi — od całości doświadczenia do planu zaplecza

Usługa to nie ekran: klient przechodzi przez kanały (www, aplikacja, telefon, okienko, paczka), ludzi i systemy,
z których część widzi, a część nie. Problem jest „usługowy”, gdy skargi dotyczą **styków** (zmiana kanału, przekazanie
między działami, czekanie na zaplecze), a nie jednego ekranu. Efekt: wspólny obraz całości i lista zmian w
zapleczu, nie tylko w interfejsie.

## Kiedy ten skill
- Skargi, powtórzenia danych, „odbijanie” klienta między działami, różne odpowiedzi w różnych kanałach → tak.
- Pytanie o jeden ekran lub przepływ w aplikacji → **ux-feature-design**.
- Model zdarzeń i reguł domenowych dla systemu → **ddd-event-storming**; czas i kolejki w procesie → **proc-lean**.
- Wybór, które szanse realizować, i testy założeń → **proc-product-discovery**.

## Procedura
1. **Zakres i wejście.** Wybierz jedną usługę od zdarzenia otwierającego do zamykającego („klient chce zwrócić
   towar” → „pieniądze wróciły”). Zbierz dowody z badań (wywiady, zgłoszenia do obsługi, dane); brakuje — zaplanuj
   badania (ux-research-methods). Nie rysuj z głowy zespołu.
2. **Mapa interesariuszy.** Klienci (segmenty), pracownicy frontstage i backstage, partnerzy (kurier, płatności),
   regulator. Dla każdego: czego potrzebuje, na co wpływa, kto go słucha. Zapis jako tabela; diagram tylko przy
   >10 stronach.
3. **Mapa podróży — obecna.** Etapy, działania klienta, kanały, myśli i emocje, momenty prawdy i bolączki, każde
   z dowodem (cytat, liczba). Osobna mapa na segment, jeśli ścieżki się różnią. Mapa pokazuje **perspektywę
   klienta**; zaplecze dodaje blueprint.
4. **Inwentarz punktów styku.** Tabela: punkt styku, kanał, właściciel, system, cel, spójność z innymi kanałami
   (te same dane, ten sam język, ta sama obietnica). Luki spójności to kandydaci do zmian (`references/szablony.md`).
5. **Service blueprint** (obecny stan, potem docelowy). Poziome pasy od góry:
   dowody fizyczne i cyfrowe → **działania klienta** → *linia interakcji* → **frontstage** (widoczne czynności
   pracowników i interfejsów) → *linia widoczności* → **backstage** (niewidoczne czynności pracowników) →
   *linia interakcji wewnętrznej* → **procesy wspierające** (systemy, inne jednostki, partnerzy).
   Każdy krok: czas, kto, jakim narzędziem, jakie dane. Zaznacz punkty awarii, czekanie i przekazania.
   Mermaid i szablon tabeli: `references/szablony.md`.
6. **Diagnoza.** Na blueprincie zaznacz: przekazania bez danych, miejsca, gdzie klient robi pracę zaplecza,
   rozjazdy między kanałami, kroki bez właściciela. Rangę nadaj wpływem na klienta i kosztem obsługi.
   Najpierw rozwiąż **cały problem** (nie fragment) i spójność między kanałami.
7. **Współprojektowanie.** Warsztat z klientami i pracownikami obu stron linii widoczności: 6–10 osób, 2–3 godziny,
   blueprint na ścianie, uczestnicy dopisują brakujące kroki i proponują zmiany. Pracownicy zaplecza znają
   obejścia, których nie ma w dokumentach. Prowadzenie: ddd-facilitation.
8. **Prototyp usługi** najtańszą metodą, która odpowie na pytanie: odgrywanie ról i bodystorming (układ
   okienka, rozmowa), **concierge** (człowiek ręcznie robi to, co potem zrobi system), **Wizard of Oz**
   (klient sądzi, że system działa, a robi to człowiek), makieta pomieszczenia lub formularza papierowego.
   Zapisz hipotezę, kryterium sukcesu i co zmierzysz; kod dopiero po potwierdzeniu.
9. **Docelowy blueprint i mapa docelowa.** Zmiany ułożone w fale; dla każdej: wpływ na klienta, praca zaplecza,
   zmiany w systemach, zmiana organizacyjna (kto traci, kto zyskuje zadania). Zamień na szanse do
   proc-product-discovery, a zmiany w zapleczu na backlog.
10. **Metryki i standard.** Metryki usługi z klientem w środku: wskaźnik ukończenia całego zadania (w każdym kanale),
    czas od zgłoszenia do wyniku, kontakty ponowne w tej sprawie, koszt obsługi jednego przypadku, satysfakcja. Dla
    usług publicznych odnieś ocenę do GOV.UK Service Standard (14 punktów, m.in. „Solve a whole problem for users”,
    „Provide a joined up experience across channels”, „Define what success looks like and publish performance
    data”) — pełna lista i uwagi: `references/standard-uslug.md`.

Wynik: `docs/project/01-discovery/service-blueprint.md` (+ mapy w tym samym katalogu); TL;DR i Przekazanie wg
core-project-record. Pierwsza linia pliku: `Service blueprint: <usługa> — stan obecny|docelowy`.

## Przykład
Wejście: „Zwroty w sklepie internetowym: 31% klientów kontaktuje się z obsługą po wysłaniu formularza zwrotu.”
Wynik (fragment `service-blueprint.md`, stan obecny):

```markdown
Service blueprint: zwrot towaru — stan obecny
| Warstwa | Krok 1 | Krok 2 | Krok 3 |
|---|---|---|---|
| Dowody | formularz www, e-mail „przyjęto” | etykieta PDF | SMS kuriera |
| Działania klienta | wypełnia formularz (6 pól) | drukuje etykietę, pakuje | czeka na zwrot pieniędzy |
| — linia interakcji — | | | |
| Frontstage | — | infolinia: „kurier w 3 dni” | czat: „sprawdzę” |
| — linia widoczności — | | | |
| Backstage | ręczne przepisanie do ERP (~4 h) | magazyn skanuje paczkę | księgowość czeka na zgodę |
| — linia int. interakcji — | | | |
| Procesy wspierające | ERP, e-mail | system kuriera | bank (przelew raz dziennie) |
Punkty awarii: P1 przepisywanie (opóźnienie 4 h, 9% błędów); P2 brak statusu dla klienta →
31% kontaktów. Spójność: infolinia i czat podają inny czas zwrotu pieniędzy (3 vs 7 dni).
```

Zmiana docelowa: formularz zapisuje się wprost w ERP, klient widzi status w e-mailu; wstępny test przez concierge
(pracownik ręcznie wysyła statusy 50 klientom), mierzymy spadek kontaktów z 31% w tym samym okresie.

## Checklista
- [ ] jedna usługa, zdarzenie otwierające i zamykające; dowody z badań, nie z głowy zespołu
- [ ] interesariusze, mapa podróży (obecna), inwentarz punktów styku z oceną spójności kanałów
- [ ] blueprint ze wszystkimi pasami, trzema liniami i punktami awarii; stan obecny osobno od docelowego
- [ ] warsztat z pracownikami frontstage i backstage; prototyp usługi z hipotezą i kryterium
- [ ] metryki usługi obejmują całe zadanie we wszystkich kanałach; (usługa publiczna) odniesienie do Service Standard
- [ ] [niezweryfikowane] i założenia oznaczone; wynik w `docs/project/01-discovery/`

## Materiały dodatkowe
- `references/szablony.md` — szablony blueprintu (tabela i Mermaid), mapy podróży, interesariuszy i inwentarza; czytaj przy pisaniu artefaktu.
- `references/standard-uslug.md` — GOV.UK Service Standard, metody prototypowania usługi i jak ich użyć.

## Źródła
- NN/g, *Service Blueprints: Definition* (nngroup.com/articles/service-blueprints-definition/) — elementy blueprintu;
  w tej sesji potwierdzone tylko wyszukiwaniem (dostęp 2026-10-17), brzmienie linii z źródeł wtórnych [niezweryfikowane].
- GOV.UK Service Manual, *Service Standard* (gov.uk/service-manual/service-standard), punkty 2, 3, 4 i 10 potwierdzone
  w wynikach wyszukiwania (dostęp 2026-10-17); pełna lista 14 punktów w references.
- Shostack, *How to Design Services* (1984) i Bitner, Ostrom, Morgan, *Service Blueprinting* (2008) — źródło
  metody blueprintu [niezweryfikowane w tej sesji].
Opisane własnymi słowami.
