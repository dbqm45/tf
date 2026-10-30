---
name: dom-ev-regulations-eu
description: Użyj przy wymogach UE dla ładowania EV — AFIR (płatność ad hoc, cena, NAP, smart charging), NIS2, CRA, Data Act, EPBD, RED III; mapa obowiązków dla CPO, eMSP, producenta.
metadata:
  przeglad: "2027-04-20"
  katalog: "Użyj, gdy oprogramowanie lub ładowarka ma spełnić przepisy UE — AFIR (UE) 2023/1804 (płatność ad hoc i terminal, cena kWh i opłata za minutę przed sesją, ceny eMSP i roaming, dane statyczne i dynamiczne do NAP i API, IDRO, smart charging, ISO 15118, terminy), NIS2 (czy CPO jest podmiotem, zgłaszanie incydentów 24 h i 72 h), CRA (firmware i aplikacja, zgłaszanie podatności, terminy 2026 i 2027), Data Act (dane z ładowarki i pojazdu, zmiana dostawcy chmury), EPBD (pre-okablowanie w budynkach), RED III (smart i dwukierunkowe ładowanie, dane baterii), plus mapa akt, artykuł, kogo dotyczy, od kiedy, skutek dla CPMS. To nie porada prawna. Nie do przepisów polskich (ustawa o elektromobilności, UDT, EIPA, URE — osobny skill dom-ev-regulations-pl), USA (dom-ev-regulations-us), technicznej płatności kartą i PCI (dom-ev-payments) ani liczenia ceny z taryfy OCPI (dom-ev-tariffs-pricing)."
  slowa: "MID MI-011, dyrektywa 2026/706, wynik pomiaru w aplikacji, AFIR, rozporządzenie 2023/1804, płatność ad hoc, terminal kartowy, czytnik kart, bezstykowa, kod QR, cena przed sesją, cena za kWh, opłata za zajęcie, occupancy fee, cena za minutę, NAP, krajowy punkt dostępu, API danych, dane statyczne, dane dynamiczne, IDRO, identyfikator operatora, smart charging, inteligentne ładowanie, cyfrowo połączony punkt, stały kabel DC, ISO 15118-20, Plug & Charge, NIS2, 2022/2555, podmiot ważny, podmiot kluczowy, zgłoszenie incydentu, 24 godziny, CRA, Cyber Resilience Act, 2024/2847, SBOM, podatność aktywnie wykorzystywana, okres wsparcia, Data Act, 2023/2854, dane z urządzenia, zmiana dostawcy chmury, EPBD, pre-okablowanie, RED III, V2G, dwukierunkowe ładowanie, dane baterii, RED delegated act, EN 18031, MID, przepisy UE, EU regulations, ad hoc payment, price transparency, national access point, cybersecurity ładowarka, firmware compliance, konsument UE"
---

# Przepisy UE dla ładowania EV — mapa obowiązków

**To nie jest porada prawna.** Skill pomaga ustalić, który akt i artykuł wpływa na CPMS, aplikację albo firmware.
Decyzję prawną podejmuje prawnik. Teksty aktów są w bazie wiedzy fabryki (pliki od człowieka, wczytane 2026-10-20);
cytuj je jako `eu-afir Art. 5(4)`. Zmiany po tej dacie i przepisy krajowe wdrażające dyrektywy nie są sprawdzone.

## Procedura
1. **Ustal rolę.** CPO (operator punktu), eMSP (dostawca usługi mobilności), producent ładowarki, właściciel punktu,
   flota, dostawca CPMS (SaaS). Jedna firma ma często kilka ról. Role: dom-ev-market-roles.
2. **Ustal akt i datę.** Znajdź wiersz w tabeli niżej, sprawdź „od kiedy” względem dziś (2026-10-20) i daty
   uruchomienia punktu (AFIR i CRA rozróżniają punkty nowe i starsze).
3. **Przeczytaj artykuł w bazie** (numery linii w `references/`), nie polegaj na pamięci. Cytuj artykuł i wersję.
4. **Dla dyrektyw** (NIS2, EPBD, RED III) obowiązek firmy wynika z **prawa krajowego**: sprawdź je w skillu
   dom-ev-regulations-pl (dla Polski) i oznacz **[do weryfikacji]**. Rozporządzenia (AFIR, CRA, Data Act) działają bezpośrednio.
5. **Przełóż na zmianę w systemie** (kolumna „Dla CPMS/aplikacji/firmware”) i wskaż, kto dowodzi zgodności.

## Mapa obowiązków (stan tekstów: AFIR 08.01.2026, EPBD 24.05.2026, reszta oryginał OJ)
| Akt · artykuł | Kogo dotyczy | Obowiązek (własnymi słowami) | Od kiedy | Dla CPMS / aplikacji / firmware |
|---|---|---|---|---|
| AFIR Art. 5(1) | CPO, punkty publiczne | ad hoc bez umowy; od nowych punktów (po 13.04.2024) płatność kartą: czytnik kart lub urządzenie bezstykowe; QR tylko do 50 kW | 13.04.2024 | ścieżka sesji bez konta; zob. dom-ev-payments |
| AFIR Art. 5(1) akapit 3 | CPO, punkty ≥ 50 kW na TEN-T lub parkingu bezpiecznym, także starsze | czytnik kart lub bezstykowy | 01.01.2027 | zdalna aktywacja sesji po płatności na terminalu; QR nie wystarczy |
| AFIR Art. 5(2) | CPO z automatyczną autoryzacją | prawo odmowy (ad hoc lub inna umowa) widoczne na punkcie | 13.04.2024 | tryb „bez Plug & Charge” zawsze dostępny |
| AFIR Art. 5(3), 5(4) | CPO | cena rozsądna, przejrzysta, niedyskryminująca; ≥ 50 kW cena ad hoc oparta na kWh plus opcjonalnie opłata za minutę; cena widoczna przed startem | punkty po 13.04.2024 | taryfa ad hoc z ENERGY jako podstawą; wyświetlacz i aplikacja |
| AFIR Art. 5(5) | eMSP | cena sesji przed startem, składniki rozdzielone, koszty roamingu jawne, brak dopłaty za roaming transgraniczny | 13.04.2024 | ekran ceny w aplikacji eMSP; zob. dom-ev-tariffs-pricing |
| AFIR Art. 5(7), 5(8), 5(10) | CPO | punkty cyfrowo połączone; smart charging dla nowych i odnowionych; stały kabel na DC | 5(7): 14.10.2024; 5(8): nowe po 13.04.2024, odnowione po 14.10.2024; 5(10): 14.04.2025 | OCPP z sterowaniem mocą; zob. dom-ev-ocpp-16 i dom-ev-ocpp-2x |
| AFIR Art. 20(1)-(5) | CPO lub właściciel | dane statyczne i dynamiczne bezpłatnie, API, zgłoszenie API do NAP; kod IDRO | 14.04.2025 | eksport do NAP; wspólny punkt europejski do 31.12.2026 |
| AFIR Aneks II pkt 2.1 | CPO, producent | ISO 15118-1 do -5 (od 08.01.2026), ISO 15118-20 (od 01.01.2027) dla punktów nowych lub odnowionych | 08.01.2026 / 01.01.2027 | SECC z -20; P&C wymaga -2 i -20 |
| NIS2 Art. 2, 3, Aneks I pkt 1(a) | CPO średni i większy | środki zarządzania ryzykiem (Art. 21), zgłoszenia (Art. 23) | prawo krajowe od 18.10.2024 | proces incydentów, łańcuch dostaw CPMS |
| CRA Art. 13, Aneks I | producent ładowarki, aplikacji | cyberbezpieczeństwo w projekcie, wsparcie ≥ 5 lat, SBOM | 11.12.2027 | bezpieczne aktualizacje firmware, bezpieczna konfiguracja domyślna |
| RED rozp. del. 2022/30 (EN 18031) | producent ładowarki z Wi-Fi, LTE, BT | cyberbezpieczeństwo radiowe | od 01.08.2025 do 10.12.2027, potem wymogi przejmuje CRA (rozp. 2026/339) | ładowarka sprzedawana dziś spełnia EN 18031, nie czeka na CRA |
| CRA Art. 14, 69(3) | producent, także produkty starsze | zgłoszenie podatności i incydentów: 24 h, 72 h, raport końcowy | 11.09.2026 (już) | kontakt do podatności, kanał zgłoszeń |
| Data Act Art. 3, 4, 5 | producent, dostawca usługi, posiadacz danych | dostęp użytkownika do danych produktu bezpłatnie; udostępnienie stronie trzeciej | 12.09.2025; Art. 3(1) dla produktów po 12.09.2026 | API danych ładowarki i sesji dla użytkownika |
| Data Act Art. 23-31 | dostawca chmury, klient | zmiana dostawcy: wypowiedzenie do 2 mies., 30 dni przejścia, od 12.01.2027 bez opłat | 12.09.2025; 12.01.2027 | eksport danych CPMS, wyjście z chmury |
| EPBD Art. 14 | państwa, właściciele budynków | punkty i pre-okablowanie na parkingach; smart i otwarte protokoły | prawo krajowe od 29.05.2026 | wymagania do instalacji w budynkach |
| RED III Art. 20a ust. 3-4 | producenci pojazdów, państwa | dane baterii pojazdu w czasie rzeczywistym dla użytkownika i eMSP; smart i bi-directional dla punktów niepublicznych | prawo krajowe od 21.05.2025 | integracja danych SoC i SoH w smart charging |

Szczegóły AFIR (jednostki, kolejność składników ceny, dane do NAP, wyjątki): `references/afir.md`.
Pozostałe akty z numerami linii: `references/akty-nis2-cra-data-act-epbd-red.md`.

## AFIR — co trzeba zbudować (skrót)
- **Płatność ad hoc (Art. 5(1)).** Definicja (Art. 2 pkt 47): bez rejestracji i bez umowy. Terminal obsługuje
  jeden punkt albo całą pulę. Punkty bez płatności są poza obowiązkiem.
- **Cena przed sesją (Art. 5(4)).** ≥ 50 kW: cena za kWh i, jeśli jest, opłata za minutę, widoczne na stacji przed startem.
  < 50 kW: wszystkie składniki w kolejności: za kWh, za minutę, za sesję, inne. Ostatni akapit Art. 5(4) wymienia akapity
  pierwszy i drugi; zakres dla punktów starszych i < 50 kW oceń z prawnikiem **[do weryfikacji]**.
- **Dane (Art. 20).** Lista 24 pozycji statycznych stacji plus pozycje punktu (EVSE, złącze, moc, P&C, smart charging,
  100 % OZE), dynamiczne: operational status, availability, ad hoc price. Dostęp bez opłat przez API zgłoszone do NAP.
- **Smart charging (Art. 5(8), Art. 2 pkt 65).** Natężenie prądu zmieniane w czasie rzeczywistym wg informacji
  z komunikacji elektronicznej. Cyfrowo połączony punkt (pkt 17): dwukierunkowa komunikacja z siecią i pojazdem, zdalny start i stop.
- **Komunikacja backend i roaming.** Aneks II pkt 2.2-2.4 w tekście z 08.01.2026 nie zawierają norm: OCPP i OCPI nie są
  wskazane przez AFIR. Nie pisz „AFIR wymaga OCPP”.

## Przykład
Pytanie: „CPO, 150 kW DC przy autostradzie TEN-T, uruchomione w 2023, płatność tylko aplikacją i QR. Co z AFIR?”
Odpowiedź: Art. 5(1) akapit 3 obejmuje starsze punkty ≥ 50 kW na TEN-T. Od 01.01.2027 potrzebny czytnik kart lub urządzenie
bezstykowe (QR dla ≥ 50 kW nie wystarcza). Cena ad hoc ma mieć kWh i ewentualnie opłatę za minutę (Art. 5(4), dla punktów
po 13.04.2024; dla starszych **[do weryfikacji]**). Dane do NAP: Art. 20(2)-(3). Przepisy krajowe i kary: dom-ev-regulations-pl.
Zastrzeżenie: to nie porada prawna.

## Poza bazą wiedzy [do weryfikacji]
| Id rejestru | Akt | Czego dotyczy | Status |
|---|---|---|---|
| `eu-red-da`, `eu-red-da-uchylenie` | Rozporządzenie delegowane (UE) 2022/30 do dyrektywy RED 2014/53/UE (EN 18031); uchylające rozp. delegowane (UE) 2026/339 | cyberbezpieczeństwo urządzeń radiowych (Wi-Fi, LTE, Bluetooth w ładowarce): zabezpieczenie sieci, danych osobowych, ochrona przed oszustwem | 2022/30 stosuje się od 01.08.2025; **uchylone z dniem 11.12.2027** (rozp. 2026/339 art. 1), bo od tej daty te wymogi obejmuje CRA (motyw 3–4); urządzenia wprowadzone na rynek 01.08.2025–10.12.2027 nadal podlegają nadzorowi wg RED (motyw 5). Treść 2022/30 i EN 18031 **[do weryfikacji]** |
| `eu-mid`, `eu-mid-2026-706` | MID 2014/32/UE i dyrektywa zmieniająca (UE) 2026/706 | nowa kategoria **MI-011 — systemy pomiarowe EVSE** (AC i DC, klasy A/B/C: 2 %/1 %/0,5 %; MMQ ≤ 0,1 kWh AC, ≤ 1 kWh DC; kWh na wskazaniu; przerwana transakcja kończy się albo jest kontynuowana po zakłóceniu — zał. Va); wynik dostępny bez narzędzi na wyświetlaczu lokalnym, zdalnym **albo na urządzeniu konsumenta (aplikacja)**, powiązany z przyrządem, z dowodem manipulacji, podstawą ceny (zał. I pkt 10.6) | 2026/706 w bazie: transpozycja do 10.04.2028, stosowanie od 10.10.2028 (art. 3); przyrządy zgodne z MID z 08.04.2026 i wprowadzone przed 10.10.2028 dalej dopuszczone, zgodne z prawem krajowym — do 10.04.2030, stare certyfikaty najdłużej do 10.04.2038 (art. 2). Z tekstu bazowego (zał. I): oprogramowanie metrologiczne identyfikowalne i odporne na wpływ innego oprogramowania (7.6), dane pomiarowe przechowywane i przesyłane zabezpieczone przed zafałszowaniem, dowód ingerencji (8.1–8.4), przyrząd używany pod nieobecność strony zapisuje trwale wyniki z identyfikacją transakcji i wydaje trwały dowód na życzenie (11.1–11.2). Zał. V (MI-003) **[do weryfikacji]** |

## Pułapki
- „AFIR wymaga OCPI/OCPP/ISO 15118”: wymaga ISO 15118 (Aneks II 2.1), ale nie wskazuje protokołów backendu.
- QR jako płatność ad hoc: dla ≥ 50 kW nie wystarcza, obowiązek obejmuje starsze punkty TEN-T od 01.01.2027.
- Sama cena za minutę przy ≥ 50 kW: cena ad hoc ma być oparta na kWh; opłata za minutę jest dodatkiem (opłata za zajęcie).
- NIS2 dla eMSP: w Aneksie I wymieniony jest operator punktu, nie eMSP; eMSP może wpaść przez inny typ podmiotu (chmura,
  usługi zarządzane) **[do weryfikacji]**.
- Dyrektywy (NIS2, EPBD, RED III) to nie prawo bezpośrednio stosowane: sprawdź ustawę krajową.
- CRA: Art. 14 dotyczy też produktów już na rynku (Art. 69(3)); reszta CRA tylko produktów po 11.12.2027 lub istotnie zmodyfikowanych.
- CPMS jako SaaS nie jest „produktem z elementami cyfrowymi” sam z siebie; wchodzi, gdy jest zdalnym przetwarzaniem
  danych wymaganym do działania ładowarki producenta (CRA Art. 3 pkt 2, motyw 12). Chmura/SaaS: NIS2.
- Data Act: Art. 3(1) dotyczy produktów wprowadzonych po 12.09.2026; mikro i małe przedsiębiorstwa mają wyłączenie (Art. 7).

## Checklista
- [ ] Rola (CPO, eMSP, producent, flota) i data uruchomienia punktu ustalone; wersje: AFIR 08.01.2026, EPBD 24.05.2026.
- [ ] Każde twierdzenie ma akt, artykuł i datę; dyrektywy odesłane do prawa krajowego.
- [ ] Płatność ad hoc, cena przed sesją i dane NAP sprawdzone z Art. 5 i 20.
- [ ] Zgłaszanie incydentów (NIS2 Art. 23, CRA Art. 14) ma właściciela i kanał.
- [ ] Akty spoza bazy (treść RED DA 2022/30, zał. V MID) oznaczone **[do weryfikacji]**; zastrzeżenie „to nie porada prawna” podane.

## Czytaj references, gdy…
| Plik | Kiedy |
|---|---|
| `references/afir.md` | szczegóły AFIR: definicje, cena, płatności, dane do NAP, cele infrastruktury, Aneks II, terminy |
| `references/akty-nis2-cra-data-act-epbd-red.md` | NIS2, CRA, Data Act, EPBD, RED III: artykuły, linie `doc.txt`, ocena roli CPO i eMSP |

## Źródła
Wszystkie wczytane 2026-10-20 z plików od człowieka (`.claude/knowledge/<id>/doc.txt`):
- `eu-afir`: AFIR (UE) 2023/1804, wersja skonsolidowana EN 08.01.2026 (02023R1804-002.001), zmieniona rozp. (UE) 2025/656 i 2025/671.
- `eu-nis2`: NIS2 (UE) 2022/2555, EN, tekst OJ L 333 z 27.12.2022.
- `eu-cra`: CRA (UE) 2024/2847, PL, tekst OJ z 20.11.2024.
- `eu-data-act`: Data Act (UE) 2023/2854, EN, OJ L z 22.12.2023.
- `eu-epbd`: EPBD (UE) 2024/1275, wersja skonsolidowana EN 24.05.2026 (02024L1275-001.001).
- `eu-red-iii`: RED III (UE) 2023/2413, EN, OJ L z 31.10.2023.
- `eu-red-da-uchylenie`: rozp. delegowane (UE) 2026/339, EN, OJ L 29.4.2026 (wczytane 2026-10-20 z pliku od człowieka).
- `eu-mid-2026-706`: dyrektywa (UE) 2026/706 zmieniająca MID, EN, OJ L 20.3.2026 (wczytane 2026-10-20 z pliku od człowieka).
- `eu-mid`: MID 2014/32/UE, art. 1–4 i zał. I, PL, Dz.U. UE L 96 z 29.3.2014 (wklejone przez człowieka 2026-10-20; pkt 7.6, 8, 10, 11 dosłownie).
- `eu-red-da` (tekst 2022/30): w rejestrze, nie pobrane.
