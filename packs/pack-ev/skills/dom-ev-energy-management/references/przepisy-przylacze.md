# Przepisy i przyłączenie

Pełna mapa obowiązków i terminów: dom-ev-regulations-eu i dom-ev-regulations-pl. Tu tylko to, co dotyczy zarządzania energią.

## 1. UE
| Akt i artykuł | Co mówi (własnymi słowami) | Znaczenie dla energii |
|---|---|---|
| RED III (dyrektywa 2023/2413) art. 20a ust. 1–2 | OSP i OSD (gdy dane mają) udostępniają udział OZE i emisyjność energii w strefie, w odstępach ≤ 1 h, cyfrowo i w ujednoliconym formacie | wejście planisty: kiedy energia jest czystsza |
| RED III art. 20a ust. 3 | producenci pojazdów dają w czasie rzeczywistym SoC, SoH, power set point, pojemność i lokalizację właścicielowi i stronom trzecim (m.in. eMSP), bez opłat | źródło SoC do planu; wdrożenie przez prawo krajowe |
| RED III art. 20a ust. 4 | nowe i wymieniane **niepubliczne** normalne punkty ładowania mają obsługiwać smart recharging i, gdzie stosowne, interfejs z licznikiem inteligentnym oraz dwukierunkowe | garaż firmowy i domowy muszą mieć sterowanie mocą; transpozycja do 21.05.2025 |
| RED III art. 20a ust. 5 | prawo krajowe pozwala małym i mobilnym zasobom (baterie, EV) uczestniczyć w rynkach, w tym zarządzanie ograniczeniami i bilansowanie, przez agregację | elastyczność floty jako usługa |
| AFIR (rozp. 2023/1804) art. 5 ust. 8, art. 2 pkt 65 | publiczne punkty zbudowane po 13.04.2024 lub odnowione po 14.10.2024 mają być zdolne do smart recharging | funkcja musi działać w stacji i CSMS |
| EPBD (dyrektywa 2024/1275) art. 14 ust. 6 | punkty w budynkach z ust. 1, 2, 4 zdolne do smart charging, sterowane niezastrzeżonymi i niedyskryminującymi protokołami | DLM w budynkach na otwartych protokołach |
| EPBD art. 14 ust. 4 | w budynkach mieszkalnych > 3 miejsc wymiarowanie pod jednoczesne użycie wszystkich miejsc | projekt przyłącza, nie algorytm |

Odesłanie w RED III art. 20a ust. 4 do „art. 15 ust. 3–4” AFIR nie pasuje do tekstu AFIR z 08.01.2026 (art. 15 ust. 3 to ocena
państw o elastyczności pojazdów) — nie wyprowadzaj z niego dodatkowych obowiązków [do weryfikacji].

## 2. Polska (ustawa o elektromobilności i paliwach alternatywnych, tekst jedn. Dz.U. 2026 poz. 1243)
| Przepis | Treść |
|---|---|
| art. 12 ust. 1 | budynki użyteczności publicznej i wielorodzinne w gminach z art. 60 ust. 1 projektuje się z mocą przyłączeniową pozwalającą wyposażyć stanowiska w punkty ≥ 3,7 kW |
| art. 12a ust. 1 | budynki niemieszkalne z > 10 stanowiskami: co najmniej jeden punkt i kanały na przewody |
| art. 12b ust. 9–10 | gdy ekspertyza wymaga zmiany umowy o przyłączenie lub instalacji, wnioskodawca pokrywa koszty; OSD instaluje układ pomiarowo-rozliczeniowy dla punktu na miejscu z wyłącznym prawem użytku |
| art. 11 | budowa infrastruktury ładowania transportu publicznego i przyłączenia jej do sieci to cel publiczny |

Warunki przyłączenia, moc przyłączeniowa i umowna, taryfy OSD: Prawo energetyczne i rozporządzenia [do weryfikacji — poza bazą].
Rozróżnij: **moc przyłączeniowa** (techniczna zdolność przyłącza), **moc umowna/zamówiona** (kW w umowie, może być niższa) i **zabezpieczenie
przedlicznikowe** (A na fazę). Do DLM bierz najmniejszy z tych limitów; przekroczenie mocy umownej może mieć skutki finansowe [do weryfikacji].

## 3. Limit przyłącza i moc umowna — jak ustalić limit DLM
1. Odczytaj z umowy lub warunków przyłączenia moc przyłączeniową i umowną oraz z rozdzielnicy zabezpieczenie przedlicznikowe.
2. `limit_A = min(zabezpieczenie_A, moc_umowna_W / (3 × 230))` na fazę. Przykład: umowna 40 kW → 40 000 / 690 = 57,97 A, w dół do 0,1 A: 57,9 A (58 A przekroczyłoby moc umowną); zabezpieczenie 63 A → limit 57,9 A.
3. Odejmij rezerwę (np. 5–10 % lub kilka amperów) na błąd pomiaru i opóźnienie regulacji [założenie].
4. Moc umowna bywa rozliczana średnią z okna czasowego [do weryfikacji], a zabezpieczenie reaguje w sekundach — chroń **oba**.

## 4. Czego nie ma w bazie
Szczegóły OpenADR, IEEE 2030.5, EEBUS, warunków przyłączenia OSD, rozliczania mocy umownej, taryf stref, limitów asymetrii oraz specyfikacji
OCPP od OCA. Oznaczone [do weryfikacji]; sprawdź przez researcher, zanim trafią do decyzji.
