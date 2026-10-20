# Ładowanie domowe pracownika — zamówienie, zwrot, RODO

Spis: 1. Zamówienie ładowarki · 2. Pomiar i stawka · 3. Wzór zwrotu · 4. Sesje służbowe i prywatne · 5. Dane (RODO) · 6. Płace · 7. Przykład

## 1. Zamówienie ładowarki — etapy i bramki
| Etap | Co sprawdzasz / robisz | Wynik |
|---|---|---|
| Kwalifikacja | pracownik uprawniony, auto służbowe, miejsce postojowe z tytułem prawnym; zgoda wspólnoty/właściciela, gdy wymagana | zgoda lub odmowa |
| Audyt instalacji | zabezpieczenie przedlicznikowe i moc umowna, liczba faz, rozdzielnica, trasa i długość kabla, uziemienie, łączność (Wi-Fi/LTE) | protokół i dobór mocy (zwykle jedno- lub trójfazowa; moc ≤ dostępnej po odjęciu obciążenia domu) |
| Zgłoszenia | zgłoszenie do OSD lub zmiana mocy, jeśli kraj tego wymaga | potwierdzenie [do weryfikacji w kraju] |
| Montaż | uprawniony elektryk, wyłącznik różnicowo-prądowy i zabezpieczenia wg projektu, pomiary odbiorcze | protokół odbioru |
| Uruchomienie | konfiguracja OCPP (adres CSMS, profil bezpieczeństwa, ID stacji), `BootNotification` → `Accepted`, test sesji z tokenem pracownika | test zaliczony |
| Podłączenie do CSMS | rejestr assetu, przypisanie do pracownika i centrum kosztów, wersja stacji (dom-ev-charger-onboarding) | stacja aktywna |
| Przekazanie | instrukcja, numer awarii, umowa użyczenia, zgoda na dane | zamknięcie zlecenia |

Kolejność wymusza bramki: bez protokołu pomiarów nie uruchamiaj, bez przypisania do pracownika nie licz zwrotu.
Wymogi krajowe (zgłoszenia, dopłaty, wymagania dla liczników): Dania jest przykładem kraju z rozwiniętym rynkiem
ładowarek domowych, ale konkretne reguły duńskie [do weryfikacji] — nie przenoś ich do innego kraju bez sprawdzenia.
Stację domową w małej mocy (AC, 3,7–11 kW) cechuje sterowanie przez CSMS: smart charging i okna cen
— dom-ev-smart-charging; przyłącze i limit domu — dom-ev-energy-management.

## 2. Pomiar i stawka
- **Pomiar:** licznik energii w ładowarce (MID) jest dowodem kWh; zapisz numer seryjny w rejestrze i sprawdź
  termin legalizacji (dom-ev-metering-calibration). `MeterValues` bez licznika legalnego traktuj jako szacunek.
- **Stawka zwrotu** (wybór polityki firmy, skutki podatkowe [do weryfikacji w kraju]):
| Stawka | Opis | Ryzyko |
|---|---|---|
| Taryfa domowa pracownika | rzeczywista cena z faktury za prąd | wymaga dokumentu od pracownika; zmienna |
| Stała średnia firmowa | jedna stawka dla wszystkich, aktualizowana kwartalnie | prosta; zawyża/zaniża koszt |
| Ryczałt | stała kwota miesięczna lub na km | nie odzwierciedla zużycia |
| Cena dynamiczna | cena godzinowa rynku w oknie sesji | najdokładniejsza; wymaga integracji z źródłem cen |
Każda stawka ma **datę obowiązywania** i wersję; zmiana nie przelicza historii. Stawek podatkowych i zwolnień nie podaję —
zależą od kraju i formy rozliczenia [do weryfikacji u doradcy podatkowego].

## 3. Wzór zwrotu
`zwrot = Σ (kWh sesji służbowych) × stawka_obowiązująca_w_dniu_sesji` (netto lub brutto wg polityki).
Wejście: licznik ładowarki, sesje z przypisanym tokenem auta służbowego. Straty między licznikiem a akumulatorem są po
stronie pracownika (kWh z licznika, nie kWh w baterii) — zapisz to w regulaminie.

## 4. Sesje służbowe a prywatne
Ładowarka domowa widzi token (lub nic, gdy ładowanie otwarte). Metody, od najpewniejszej:
1. **Token auta służbowego** jedyną drogą startu sesji; ładowanie bez tokenu zablokowane lub oznaczone prywatne.
2. **Identyfikacja auta** przez EMAID w Plug & Charge (dom-ev-iso15118) — tam, gdzie auto i stacja to wspierają.
3. **Potwierdzenie w aplikacji** po sesji, z kolejką „do potwierdzenia”; wymaga audytu losowego.
4. **Telematyka** (przebieg, SoC, położenie) jako dowód pomocniczy — z zachowaniem minimalizacji danych.
Sesje auta prywatnego (żona, gość) nie podlegają zwrotowi; nie są też ukrywane, jeśli ładowarka jest własnością firmy —
polityka musi wprost mówić, czy firma widzi ich energię i czy wolno ją naliczać prywatnie.

## 5. Dane domowe i RODO (w skrócie)
| Zasada | Skutek dla skilla |
|---|---|
| Cel | zwrot kosztów i obsługa serwisowa; nie kontrola prywatnego życia |
| Minimalizacja | do zwrotu wystarczy suma kWh i daty; godziny i wzorce dnia tylko, gdy potrzebne (np. smart charging) |
| Podstawa | umowa/obowiązek pracodawcy; zgoda na dane lokalizacyjne i telematykę osobno i odwoływalna |
| Retencja | surowe sesje krótko, agregaty do końca okresu rozliczeniowego i wymaganych terminów [do ustalenia] |
| Dostęp | księgowość widzi sumy, administrator floty — sesje służbowe; serwis — stan stacji, nie życie domowe |
Szczegóły (DPIA, procesory, retencja) — obszar ogólny ochrony danych; tu tylko decyzje projektowe.

## 6. Lista płac
Eksport miesięczny: `employee_id`, okres, kWh służbowe, stawka (wersja), kwota, liczba sesji „do potwierdzenia”
(nierozliczone). Lista płac dostaje kwotę, nie sesje. Korekty to osobne wiersze w kolejnym okresie.

## 7. Przykład
Pracownik P, okres 2026-09: 14 sesji tokenem auta służbowego = 312,4 kWh z licznika; 3 sesje bez tokenu = 41,0 kWh
(prywatne, poza zwrotem). Stawka firmowa 0,95 [ilustracja, nie dane rynkowe] za kWh od 2026-07-01 → zwrot 312,4 × 0,95 =
296,78. Do płac idzie jedna kwota; 41,0 kWh nie jest zwracane i nie jest naliczane pracownikowi, chyba że polityka stanowi inaczej.
