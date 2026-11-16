# Macierz kontroli i plan gotowości do audytu

Spis treści: 1. Macierz kontroli · 2. Plan gotowości · 3. Przebieg audytów · 4. Rejestr dowodów

## 1. Macierz kontroli (jeden rejestr na organizację)
| ID | Kontrola (jak działa) | Właściciel | System | Częstotliwość | Dowód (źródło, ścieżka) | ISO 27001 | SOC 2 | CSF 2.0 | PCI DSS | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| K-014 | Przegląd dostępów do AWS co kwartał, usunięcie nadmiarowych | CTO | AWS IAM | kwartał | eksport IAM + zgłoszenie | A.5.18 | CC6.2 | PR.AA | 7.2.4 | działa, dowód |
[przykład: numeracja kontroli i mapowania ilustracyjne; zweryfikuj w tekstach ram przed użyciem]

Zasady: kontrola opisana czasownikiem i częstotliwością („co kwartał”), nie hasłem („zarządzanie dostępem”); jeden
właściciel; dowód wskazuje źródło, z którego pobierasz go bez prośby do człowieka; mapowanie do wymagań ram dopiero po
sformułowaniu kontroli. Brak kontroli dla wymagania = luka; kontrola bez wymagania = kandydat do usunięcia.

## 2. Plan gotowości do audytu
| Etap | Wynik | Właściciel | Bramka |
|---|---|---|---|
| Zakres i motyw | zatwierdzony zakres, wyłączenia | CISO/zarząd | podpis kierownictwa |
| Ryzyka | rejestr ryzyk, plan postępowania (sec-risk-management) | CISO | akceptacje ryzyk |
| Polityki i standardy | komplet, zatwierdzone, znane zespołom | CISO | potwierdzenia zapoznania |
| Luki | zadania z terminami | właściciele kontroli | brak luk krytycznych |
| Dowody | automatyczny zbiór, kalendarz kontroli okresowych | właściciele | próbka dowodów z 3 miesięcy |
| Audyt wewnętrzny | raport, niezgodności, działania | niezależny audytor | zamknięte niezgodności większe |
| Przegląd zarządzania | protokół (wejścia i decyzje) | zarząd | protokół podpisany |
| Audyt zewnętrzny | próba generalna z dostawcą, rezerwacja terminu | CISO | brak otwartych blokad |

Rezerwa terminu: wybór jednostki certyfikującej lub firmy audytorskiej z wyprzedzeniem; czas zależy od zakresu.

## 3. Przebieg audytów
- **ISO 27001**: etap 1 — przegląd dokumentacji i gotowości (zakres, polityki, SoA, ocena ryzyka, audyt wewnętrzny,
  przegląd zarządzania); etap 2 — sprawdzenie wdrożenia próbkami i rozmowami; niezgodności większe blokują certyfikat
  do zamknięcia; potem audyty nadzoru i ponowna certyfikacja [niezweryfikowane: częstość wg jednostki].
- **SOC 2**: wybór kategorii, ocena gotowości (readiness), okres obserwacji dla typu II, próbkowanie dowodów z okresu,
  raport z opinią i listą wyjątków.
- **PCI DSS**: wyznaczenie poziomu i formy walidacji z acquirerem, dowody per wymaganie, AOC.
- **Zachowanie podczas audytu**: jedna osoba koordynuje, odpowiedzi wynikają z dowodów, „nie wiem, sprawdzę” zamiast
  zgadywania; nie poprawiasz dowodów wstecz.

## 4. Rejestr dowodów
| Dowód | Kontrola | Źródło | Zbiór | Data | Retencja |
|---|---|---|---|---|---|
| Eksport użytkowników IAM | K-014 | AWS CLI/API | automatyczny, kwartalnie | 2026-10-01 | 3 lata |
[przykład]. Dowód zawiera dane osobowe? Retencja i dostęp wg arch-privacy-compliance.
