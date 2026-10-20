# Analiza ryzyka, FAIR, ubezpieczenie i KRI

Spis treści: 1. Skale jakościowe · 2. FAIR krok po kroku · 3. Ubezpieczenie cyber · 4. KRI · 5. Granica z modelem zagrożeń

## 1. Skale jakościowe
Skala 1–5 działa tylko z **definicjami**: wpływ 1 = strata <10 tys. zł, 3 = 100–500 tys. zł, 5 = >5 mln zł lub
utrata licencji [przykład; progi ustala zarząd]; prawdopodobieństwo 1 = rzadziej niż raz na 10 lat, 3 = raz na 1–3
lata, 5 = więcej niż raz w roku. Ocena = P × W; progi: 1–6 niska, 7–14 średnia, 15–25 wysoka [przykład]. Wady macierzy:
kompresja ocen, brak dodawania ryzyk, subiektywność — dlatego dla decyzji o pieniądzach używasz FAIR.

## 2. FAIR krok po kroku
1. **Scenariusz**: aktywo, zagrożenie (kto/co), rodzaj straty (poufność, integralność, dostępność), zakres.
2. **Częstotliwość zdarzeń strat (LEF)** = częstotliwość prób × odsetek, który się udaje (podatność). Przedział,
   np. 0,05–0,5 rocznie, najbardziej prawdopodobna 0,15 [przykład]; dane: własne incydenty, branżowe raporty, ekspert.
3. **Wielkość straty (LM)**: straty pierwotne (reakcja, przestój, odtworzenie) i wtórne (kary, powiadomienia, utrata
   klientów, koszty prawne). Każda kategoria jako przedział (min, najbardziej prawdopodobna, max).
4. **Symulacja Monte Carlo**: tysiące losowań z przedziałów (np. rozkład trójkątny lub PERT) → rozkład rocznej straty;
   raportujesz medianę, średnią i P90, nie jedną liczbę. Narzędzia: arkusz, Python (np. biblioteka pyfair).
5. **Decyzja**: porównaj rozkład przed i po kontroli z kosztem kontroli i apetytem; różnica to wartość kontroli.
6. **Kalibracja**: ekspertów ćwicz w podawaniu 90% przedziałów; zapisz założenia, bo wynik jest tak dobry jak dane.
Nie liczysz FAIR dla każdego ryzyka — tylko dla najwyższych i spornych. Wynik wpisujesz do rejestru obok oceny macierzowej.

## 3. Ubezpieczenie cyber (podział ryzyka)
Przenosi część skutku finansowego (koszty reakcji, przestój, roszczenia stron trzecich — zależnie od polisy), nie usuwa
przyczyny. Sprawdź z brokerem i prawnikiem: sumy i podlimity, **wyłączenia** (np. wojna, brak spełnienia minimalnych
kontroli), franszyzę, wymagane kontrole (MFA, kopie offline, EDR) i ich zgodność z rzeczywistością przy wniosku
(nieprawdziwe odpowiedzi mogą unieważnić ochronę), okres wykrycia i zgłoszenia, wybór doradców przez ubezpieczyciela.
Wiersz rejestru ma opcję „podział” z numerem polisy i datą wygaśnięcia. Warunki rynku zmieniają się — [niezweryfikowane] w sesji.

## 4. KRI (wskaźniki ryzyka)
| KRI | Próg zielony / czerwony [przykład] | Właściciel |
|---|---|---|
| krytyczne podatności po terminie SLA | 0 / >3 | CISO |
| akceptacje ryzyka po terminie | 0 / >0 | CISO |
| dostawcy tier 1 bez oceny <12 mies. | 0 / >1 | zakupy |
| odsetek kont uprzywilejowanych z MFA | 100% / <98% | IT |
| udany test odtworzenia w ostatnich 6 mies. | tak / nie | SRE |
Zasady: KRI przewiduje (wskaźnik wyprzedzający), ma próg i akcję przy przekroczeniu; nie raportuj liczby bez trendu.

## 5. Granica z modelem zagrożeń
**arch-threat-modeling** ocenia konkretny projekt (DFD, STRIDE, kontrole w backlogu) i daje listę zagrożeń z oceną.
Ten skill bierze z niego ryzyka istotne dla organizacji, agreguje je w jednym rejestrze z jednymi kryteriami, ustala
właścicieli, apetyt i akceptacje oraz raportuje zarządowi. Niska ocena techniczna w modelu zagrożeń może być wysoka
organizacyjnie (aktywo krytyczne, wiele funkcji dotkniętych) — przelicz wg kryteriów organizacji.
