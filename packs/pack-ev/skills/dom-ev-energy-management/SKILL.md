---
name: dom-ev-energy-management
description: Użyj przy mocy lokacji i floty EV — limit przyłącza, DLM, podział mocy między ładowarki, zajezdnia, PV i magazyn, ceny energii, sygnały OSD, odporność offline.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy trzeba rozdzielić ograniczoną moc między ładowarki lokacji albo floty — limit przyłącza i moc umowna, dynamiczne zarządzanie obciążeniem (DLM) statyczne i z pomiarem budynku, algorytmy podziału (równy, EDF, priorytety, minimum 6 A), fazy, nierównowaga i pojazdy 1-fazowe, zajezdnia z harmonogramem odjazdów i SoC docelowym, PV i magazyn energii za licznikiem, ceny energii i taryfy dynamiczne operatora, sygnały OSD (OpenADR, IEEE 2030.5, EEBUS), RED III art. 20a, AFIR, EPBD i przyłączenie w Polsce, gdzie liczyć (CSMS, lokalny kontroler, ładowarka), praca offline i limit fail-safe, testy na scenariuszach z liczbami. Nie do budowy profili OCPP, stackLevel i GetCompositeSchedule (dom-ev-smart-charging), ceny dla kierowcy i taryf OCPI (dom-ev-tariffs-pricing), V2G i ISO 15118 (dom-ev-charging)."
  slowa: "zarządzanie energią, energy management, EMS, DLM, dynamic load management, load balancing, równoważenie obciążenia, limit przyłącza, moc umowna, moc przyłączeniowa, zabezpieczenie przedlicznikowe, przekroczenie mocy, peak shaving, ścinanie szczytów, pomiar budynku, licznik budynku, podział mocy, równy podział, EDF, termin odjazdu, priorytet pojazdu, minimum 6 A, nierównowaga faz, pojazd jednofazowy, zajezdnia, depot, flota, harmonogram odjazdów, SoC docelowy, ponowne planowanie, PV, fotowoltaika, nadwyżka PV, magazyn energii, BESS, taryfa dynamiczna, ceny dzień-przód, koszt energii, OSD, OpenADR, IEEE 2030.5, EEBUS, demand response, elastyczność, RED III art. 20a, AFIR smart charging, EPBD art. 14, lokalny kontroler, offline, fail-safe, zanik łącza, bezpieczny limit, ile ładowarek na przyłącze"
---

# Zarządzanie energią lokacji i floty

Skill odpowiada na pytanie „**ile mocy przypada na pojazd i kiedy**, żeby nie przekroczyć przyłącza i dotrzymać terminów”.
Wynik to plan w amperach na fazę. Zamianę planu na komunikaty OCPP (`SetChargingProfile`, `stackLevel`, composite schedule)
opisuje **dom-ev-smart-charging**. Ceny dla kierowcy: **dom-ev-tariffs-pricing**. Sprzęt (PWM, 6 A): **dom-ev-charger-hardware**.

## Procedura
1. **Ustal limity** (references/przepisy-przylacze.md, sekcja 3): zabezpieczenie przedlicznikowe na fazę, moc umowna, moc
   przyłączeniowa. Limit DLM to najmniejszy z nich minus rezerwa. Rób to na fazę, w amperach.
2. **Zdecyduj o pomiarze.** Budynek zmienny i dostępny licznik → DLM dynamiczny. Brak pomiaru → statyczny z limitem na najgorszy przypadek.
3. **Zbierz dane o pojazdach:** obecność, termin odjazdu, energia do dostarczenia, maks. prąd i fazy (tabela „Dane do planu”).
4. **Sprawdź wykonalność fizyczną** (max_a × 0,23 × fazy × czas postoju ≥ potrzeba), zanim uruchomisz algorytm. Niewykonalne zgłoś człowiekowi.
5. **Wybierz algorytm** (tabela poniżej) i policz przydział na fazę z regułami: minimum 6 A albo 0, maksimum pojazdu, rozdzielczość 0,1 A w dół.
6. **Dodaj PV, magazyn, ceny i sygnały OSD** jako kolejne ograniczenia lub preferencje (references/pv-bess-taryfy-sygnaly.md).
7. **Przełóż plan na profile** (dom-ev-smart-charging) i dodaj bezpiecznik w stacji (`ChargePointMaxProfile`/`TxDefaultProfile`).
8. **Zaprojektuj awarie:** limit fail-safe w stacji, krótka ważność profili dynamicznych (references/architektura-odpornosc.md).
9. **Przetestuj na scenariuszach z liczbami** i niezmienniku „suma na fazie ≤ limit w każdej chwili” (references/scenariusze-testowe.md).

## Statyczny kontra dynamiczny DLM
| | Statyczny | Dynamiczny z pomiarem budynku |
|---|---|---|
| Limit dla EV | stały: limit przyłącza − szczyt budynku − rezerwa, dzielony na stacje | zmienny: limit − bieżący pobór budynku (na fazę) − rezerwa |
| Wymaga | tylko konfiguracji | licznika lub przekładników, odczytu co kilka sekund, łączności |
| Zaleta | prostota, odporność | większa moc EV poza szczytem budynku |
| Wada | zostawia moc niewykorzystaną | pomiar to nowy punkt awarii → fail-safe obowiązkowy |
| Błąd typowy | limit z mocy sumarycznej zamiast z fazy | licznik tylko na jednej fazie albo bez kierunku |

Wzór dynamiczny, dla każdej fazy x: `EV_max(x) = limit(x) − budynek(x) − rezerwa`. Stacja 3-fazowa dostaje **minimum z faz**.

## Dane do planu (na pojazd)
| Pole | Skąd | Uwaga |
|---|---|---|
| obecność, EVSE | StatusNotification, TransactionEvent | po utracie łączności: nieznana |
| odjazd | harmonogram floty, aplikacja kierowcy | brak = zakładaj najgorszy (wczesny) |
| kWh do dostarczenia | SoC docelowy − SoC teraz, pojemność, sprawność | SoC z telematyki lub MeterValues; sprawność ~0,90 [założenie] |
| maks. prąd | min(stacja, kabel PP, ładowarka pokładowa) | zmierz, nie zakładaj nastawy |
| fazy | typ pojazdu i stacji | 1-fazowy obciąża jedną fazę |

## Algorytmy podziału (szczegóły: references/algorytmy-podzialu.md)
| Algorytm | Użyj, gdy | Uwaga |
|---|---|---|
| równy podział | publiczny parking, brak terminów | oddaje prąd pojazdom, które go nie wezmą; odzyskuj niewykorzystany prąd z pomiaru |
| EDF (najwcześniejszy odjazd) | flota z harmonogramem | remis rozstrzygaj priorytetem lub luzem, nie nazwą EVSE |
| najmniejszy luz (LLF) | terminy ścisłe, znane moce pojazdów | częste zmiany kolejności |
| priorytety + EDF | SLA, flota mieszana | pilnuj głodzenia niskiego priorytetu |
| z ceną | taryfy dynamiczne | najpierw wykonalność terminu, potem tańsze sloty |

Zasady wspólne: poniżej 6 A pojazd nie ładuje, więc przydział < 6 A to 0; przy 63 A i pojazdach 3-fazowych ładuje naraz najwyżej 10;
pojazdy 1-fazowe przypisuj rotacyjnie do faz; mierz rzeczywisty pobór i oddawaj nieużyty prąd.

## Przykład: zajezdnia z przykładu depot-smart-charging
Wejście: przyłącze 3×63 A, 230 V, cztery pojazdy trójfazowe (przyjazd 18:00 oprócz EVSE-3 o 20:00):
| EVSE | Okno | Potrzeba | Maks. |
|---|---|---|---|
| EVSE-1 | 18:00–22:00 | 30 kWh | 32 A |
| EVSE-2 | 18:00–04:00 | 40 kWh | 16 A |
| EVSE-3 | 20:00–06:00 | 50 kWh | 32 A |
| EVSE-4 | 18:00–20:00 | 60 kWh | 16 A |

Skrypt `depot.py` z katalogu `examples/depot-smart-charging/` fabryki, uruchomiony na scenariuszu `depot` (EDF, sloty 15 min), daje:
EVSE-1 30,0, EVSE-2 40,0, EVSE-3 50,0, **EVSE-4 22,08 kWh z 60**; kod wyjścia 1.
Wnioski:
- EVSE-4 nie uda się przy żadnym limicie: 16 A × 0,23 × 3 × 2 h = 22,08 kWh. To granica fizyczna, nie wina przyłącza.
  Zgłoś dyspozytorowi przed ładowaniem (niższy SoC docelowy, dłuższy postój, inna stacja).
- Przyłącze 63 A jest wykorzystane w pełni tylko do 19:15, a trzy wykonalne pojazdy dostają energię już przy limicie 22 A.
  (przy 21 A EVSE-1 ma 28,98 kWh). Z tego wynika, że da się obniżyć moc umowną albo dostawić stacje; wniosek z heurystyki, nie z optimum.
- Algorytm jest chciwy (ASAP): nie szuka tanich godzin ani nie wygładza szczytu. Do kosztu dodaj cenę (references/pv-bess-taryfy-sygnaly.md).
Kontrola profili: `composite_schedule.py <profile>.json --start 2026-10-20T18:00:00Z --duration 43200` (dom-ev-smart-charging).
Więcej: references/zajezdnia-floty.md.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| references/algorytmy-podzialu.md | liczysz przydział, fazy, nierównowagę, odzyskiwanie prądu; chcesz porównać algorytmy |
| references/zajezdnia-floty.md | przeliczasz SoC na kWh, sprawdzasz wykonalność, planujesz ponownie, czytasz wynik scenariusza `depot` |
| references/pv-bess-taryfy-sygnaly.md | masz PV, magazyn, ceny dzień-przód albo sygnały OSD (OpenADR, IEEE 2030.5, EEBUS) |
| references/architektura-odpornosc.md | decydujesz, gdzie liczyć (CSMS, kontroler, ładowarka), i co robić offline; `NotifyChargingLimit` |
| references/przepisy-przylacze.md | pytanie o RED III art. 20a, AFIR, EPBD, ustawę o elektromobilności, moc umowną i przyłączenie |
| references/scenariusze-testowe.md | piszesz testy DLM i zajezdni z liczbami |

## Pułapki
- Limit z sumy mocy zamiast z fazy: stacja 3-fazowa jest ograniczona najsłabszą fazą.
- Przydział 1–5 A: pojazd i tak nie ładuje, a plan liczy energię, której nie będzie.
- PV odjęte od limitu bezpieczeństwa: chmura zabiera produkcję w sekundy; PV to bonus, nie zapas.
- „Ostatni znany limit” po utracie łączności lub pomiaru: budynek się zmienił; użyj limitu fail-safe zapisanego w stacji.
- Plan liczony z limitów, nie z poboru: pojazd bierze mniej, a reszta stoi niewykorzystana.
- Remis terminów rozstrzygany nazwą EVSE (jak w `depot.py`): pojazd, któremu nic nie pomoże, może zabrać energię innemu.
- Niewykonalny termin odkryty w nocy: sprawdź wykonalność przy przyjeździe i zgłoś od razu.
- Szybkie przełączanie profili (flapping): obcinaj szybko, podnoś wolno, nie zmieniaj profilu aktywnej sesji bez potrzeby.
- Mieszanie ceny operatora z ceną dla kierowcy: tu koszt energii operatora, taryfa OCPI to dom-ev-tariffs-pricing.
- Szczegóły OpenADR, IEEE 2030.5, EEBUS i warunków OSD podane jako pewne: [do weryfikacji], nie ma ich w bazie.

## Checklista
- [ ] Limit na fazę z zabezpieczenia i mocy umownej, minus rezerwa.
- [ ] Pomiar budynku na wszystkich fazach, z kierunkiem, z kontrolą nieaktualności.
- [ ] Wykonalność fizyczna sprawdzona przed planem; niewykonalne zgłoszone.
- [ ] Minimum 6 A albo 0; rozdzielczość 0,1 A w dół; stacja 3-fazowa liczona minimum z faz.
- [ ] Pojazdy 1-fazowe rozłożone na fazy.
- [ ] PV i magazyn nie obniżają limitu bezpieczeństwa.
- [ ] Limit fail-safe w stacji i krótka ważność profili dynamicznych; test zaniku łącza i pomiaru.
- [ ] Testy na scenariuszach z liczbami i niezmiennik sumy na fazie.
- [ ] Fakty oznaczone [do weryfikacji] nie trafiają do decyzji bez sprawdzenia.

## Źródła
- Baza wiedzy fabryki, pobrane 2026-10-20: `eu-red-iii` (dyrektywa 2023/2413, art. 20a, eur-lex.europa.eu/eli/dir/2023/2413/oj, doc.txt L2924–2985),
  `eu-afir` (rozp. 2023/1804, art. 2 pkt 65 i art. 5 ust. 8, wersja 08.01.2026), `eu-epbd` (dyrektywa 2024/1275, art. 14),
  `pl-elektromobilnosc` (isap.sejm.gov.pl, WDU20180000317, doc.txt L349–365, L428–437),
  `ocpp-json-schemas` (NotifyChargingLimitRequest 2.0.1: `chargingLimitSource`, `isGridCritical`),
  `everest-libocpp-smart-charging` (K01, K08, ranga W — implementacja, nie specyfikacja).
- Skille fabryki: dom-ev-regulations-eu (references o AFIR, EPBD i RED III), dom-ev-regulations-pl, dom-ev-charger-hardware.
- Przykład zajezdni (katalog `examples/depot-smart-charging/`: algorytm, README, scenariusz), uruchomiony 2026-10-20.
- Nie ma w bazie: OpenADR, IEEE 2030.5, EEBUS, Prawo energetyczne, specyfikacja OCPP od OCA — oznaczone [do weryfikacji].
