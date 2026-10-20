---
name: sec-detection-engineering
description: Użyj przy projektowaniu i testowaniu reguł wykrywania — Sigma jako kod, pokrycie ATT&CK, jakość alertów, purple team, polowanie na zagrożenia.
metadata:
  przeglad: 2027-04-17
  katalog: "Użyj, gdy trzeba zaprojektować, napisać, przetestować i utrzymać wykrywanie ataków — cykl życia reguły (hipoteza, źródło danych, reguła, test symulacją, wdrożenie, strojenie, wycofanie), detection-as-code (Sigma, repo, CI), mapa pokrycia MITRE ATT&CK i analiza luk, jakość alertu (trafność, budżet szumu, kontekst, runbook), ćwiczenia purple team (Atomic Red Team, Caldera), podstawy polowania na zagrożenia, metryki (czas do wykrycia, pokrycie, fałszywe alarmy). Nie do obsługi SIEM, EDR, SOAR i reagowania na incydent (ops-security-operations), ogólnych alertów aplikacji (ops-observability), modelu zagrożeń funkcji (arch-threat-modeling) ani analizy próbek malware (sec-malware-analysis)."
  slowa: "reguła wykrywania, detection engineering, detection as code, Sigma, pokrycie ATT&CK, MITRE ATT&CK, Navigator, luki w wykrywaniu, fałszywe alarmy, zmęczenie alertami, strojenie reguł, purple team, red team, emulacja przeciwnika, Atomic Red Team, Caldera, threat hunting, polowanie na zagrożenia, hipoteza, czas do wykrycia, MTTD, hunting, testy reguł, SIEM reguła"
---

# Inżynieria wykrywania (detection engineering, purple team)

Granica: **ops-security-operations** obsługuje SIEM, EDR, SOAR i incydenty (telemetria, triaż, reagowanie). Ten skill
dotyczy **projektowania i testowania wykrywania**: skąd wiadomo, że reguła łapie technikę i że da się ją utrzymać.
Ogólne alerty o awarii: ops-observability. Co może pójść źle w projekcie: arch-threat-modeling. Reguły z analizy
próbki: sec-malware-analysis. Szczegóły, szablon reguły i metryki: `references/reguly-i-metryki.md`.

## Procedura (cykl życia reguły)
1. **Hipoteza.** Skąd wiemy, że to ważne: raport o zagrożeniu, incydent własny, technika ATT&CK istotna dla naszej branży
   i stosu. Zapisz: „Jeśli napastnik zrobi [technika], zobaczymy [obserwowalny ślad] w [źródle]”.
2. **Źródło danych.** Czy telemetria istnieje, jest kompletna i parsowana (pola, opóźnienie, retencja)? Bez źródła
   reguła jest ozdobą; wynik tego kroku bywa zadaniem „włącz logowanie”, a nie regułą.
3. **Reguła.** Format Sigma (niżej), jedna reguła na jedno zachowanie; warunek na zachowaniu, nie na nazwie narzędzia.
   Zapisz znane fałszywe alarmy (`falsepositives`) i poziom (`level`).
4. **Test.** Pozytywny: symulacja techniki w laboratorium lub na stagingu (Atomic Red Team) albo nagrane zdarzenia —
   alert musi się pojawić. Negatywny: zdarzenia z normalnej pracy z ostatnich dni — alertów ma być mało.
5. **Wdrożenie** przez PR i CI; najpierw tryb obserwacji (bez wezwania dyżurnego), potem produkcyjny.
6. **Strojenie.** Wyjątki dla znanych dobrych zachowań dodajesz wąsko (konto, ścieżka, host), nie osłabiasz warunku.
7. **Wycofanie.** Reguła bez trafień i bez testu od kwartału, albo ciągle ignorowana → popraw, połącz lub usuń (`status: deprecated`).

## Detection-as-code (Sigma)
- Sigma to otwarty, niezależny od dostawcy format reguł w YAML. Wymagane pola: `title`, `logsource`, `detection`
  z `condition`. Zalecane: `id` (UUID), `status`, `description`, `references`, `author`, `date`, `tags`
  (np. `attack.t1059.001`), `falsepositives`, `level`. Wartości `status` i `level` — `references/reguly-i-metryki.md`.
- Repozytorium: reguły w katalogach wg źródła, przegląd w PR, właściciel, historia zmian jako dziennik decyzji.
- CI: (1) walidacja składni i schematu, (2) konwersja do zapytania docelowego SIEM-a (pySigma, `sigma convert`;
  pipeline mapujący pola), (3) test na zdarzeniach pozytywnych i negatywnych, (4) kontrola obowiązkowych pól
  (`id`, `level`, `falsepositives`, tag ATT&CK). Czerwony test blokuje scalenie.
- Reguły korelacyjne (wiele zdarzeń w czasie) opisuje osobna specyfikacja Sigma; zacznij od reguł pojedynczych.

## Pokrycie ATT&CK i analiza luk
1. Zbierz tagi `attack.tNNNN` z reguł i wygeneruj warstwę ATT&CK Navigator.
2. Oddziel trzy stany techniki: **brak telemetrii**, **jest telemetria bez reguły**, **jest reguła przetestowana**.
   Sama obecność reguły z tagiem nie jest pokryciem; reguła nieprzetestowana liczy się jako „niepotwierdzona”.
3. Priorytet luk: techniki używane przez grupy atakujące naszą branżę (wywiad o zagrożeniach), nasz stos i aktywa,
   koszt wykrycia; nie dąż do 100% mapy (bez sensu i bez kosztu-efektu).
4. Wersję ATT&CK podaj w warstwie i w raporcie; matryca zmienia się dwa razy do roku, a identyfikatory bywają zastępowane.

## Jakość alertu
Alert ma: ważność, kontekst (host, konto, polecenie, proces nadrzędny), kroki triażu i **link do runbooka**, właściciela.
- **Trafność** = prawdziwe alarmy / wszystkie alarmy; mierz per reguła. **Budżet szumu**: ustal, ile alertów na analityka
  na zmianę jest znośne [przykład: 20], i nowa reguła musi się w nim mieścić albo zastąpić inną.
- Reguła z trafnością poniżej progu ustalonego z SOC trafia do strojenia lub zmienia się w polowanie (bez alertu).

## Purple team
Ćwiczenie wspólne ofensywy i obrony: wykonujemy technikę, sprawdzamy, czy alert się pojawił, i poprawiamy.
- **Tylko za pisemną zgodą właściciela systemów, w uzgodnionym zakresie** (cele, okno czasowe, kontakt awaryjny,
  zakaz szkód); najlepiej laboratorium lub staging. Zespół SOC wie o ćwiczeniu albo ma zasady rozpoznania symulacji.
- Plan emulacji: lista technik z ATT&CK dla wybranego przeciwnika, dla każdej: oczekiwany ślad, oczekiwany alert,
  sposób sprzątania. Narzędzia: Atomic Red Team (małe testy per technika, z krokiem sprzątania), MITRE Caldera (platforma
  emulacji; używaj wersji ≥ 5.1.0 po łatce CVE-2025-27364, nie wystawiaj do internetu).
- Wynik per technika: wykryto / zarejestrowano bez alertu / brak śladu → zadania: telemetria, reguła, strojenie.
  Powtórz test po poprawce (regresja).

## Polowanie na zagrożenia (podstawy)
Polowanie jest sterowane hipotezą, nie alertem: pytanie, zapytanie, analiza wyników (długi ogon, rzadkie wartości,
anomalie względem linii bazowej). Wynik: znalezisko (→ incydent, ops-security-operations), nowa reguła z kroku 3
procedury albo luka w telemetrii. Zapisz hipotezę, zapytanie, zakres czasu i wynik, także negatywny.

## Metryki
Czas do wykrycia (od wykonania techniki w teście do alertu), pokrycie przetestowane techniki / priorytetowe techniki,
odsetek fałszywych alarmów, odsetek reguł z testem i runbookiem, wiek reguł bez przeglądu. Metryki to kierunek, nie cel
sam w sobie (nie nagradzaj liczby reguł).

## Przykład
**Wejście:** „Raport o grupie atakującej naszą branżę opisuje uruchamianie PowerShella z zakodowanym poleceniem (T1059.001).”
**Wynik** (fragment karty reguły): hipoteza: `powershell.exe` z `-enc` uruchomiony przez proces Office; źródło: zdarzenia
tworzenia procesu z linią poleceń (sprawdzone: jest na stacjach, brak na serwerach → zadanie telemetrii); test
pozytywny: atomic T1059.001 na maszynie laboratoryjnej, alert po [przykład: 40 s]; test negatywny: 7 dni zdarzeń,
[przykład: 3 trafienia, wszystkie z narzędzia do inwentaryzacji → wyjątek po ścieżce]; `level: high`, `falsepositives`
uzupełnione, runbook podlinkowany, tag `attack.t1059.001`.

## Checklista
- [ ] hipoteza z technika ATT&CK i sprawdzone źródło danych
- [ ] reguła Sigma z `id`, `level`, `falsepositives`, tagiem; w repo, przez PR
- [ ] test pozytywny (symulacja) i negatywny (normalny ruch) w CI
- [ ] alert z kontekstem i runbookiem; trafność mierzona
- [ ] pokrycie z rozróżnieniem „jest reguła” i „przetestowana”; podana wersja ATT&CK
- [ ] purple team tylko za zgodą, w zakresie, ze sprzątaniem

## Źródła
- [Sigma Rules Specification 2.1.0](https://github.com/SigmaHQ/sigma-specification) (odczyt 2026-10-17); [pySigma i sigma-cli](https://github.com/SigmaHQ/pySigma)
- [MITRE ATT&CK, wydania danych STIX](https://github.com/mitre-attack/attack-stix-data/releases): v20.0 (odczyt 2026-10-17, rok wydania [niezweryfikowane])
- [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team) (MIT); [MITRE Caldera](https://github.com/mitre/caldera) (Apache-2.0; ≥ 5.1.0 po CVE-2025-27364), odczyt 2026-10-17
Opisane własnymi słowami.
