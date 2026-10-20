# CAPEX, OPEX, dotacje i obniżanie kosztów

## Spis treści
1. Przyłącze
2. Opłaty za moc
3. Dotacje
4. BESS i smart charging
5. Rozbudowa etapami
6. Przychody dodatkowe

## 1. Przyłącze
- Często największa i najbardziej niepewna pozycja CAPEX: zależy od odległości do sieci, wymaganej mocy, stanu sieci
  OSD i konieczności budowy stacji transformatorowej.
- Niepewna jest też kolejność w czasie: warunki przyłączenia, umowa i budowa mogą trwać dłużej niż montaż ładowarek.
  Opóźnienie przesuwa przychody, a nie koszty stałe dzierżawy i projektu.
- Przed liczeniem NPV zbierz od OSD warunki przyłączenia i kosztorys; do tego czasu licz trzy warianty (niski,
  bazowy, wysoki) zamiast jednej liczby. Procedura w Polsce: dom-ev-regulations-pl. Wybór lokalizacji z mocą: dom-ev-site-development.

## 2. Opłaty za moc
- Dwa typowe mechanizmy [założenie, zależą od taryfy OSD i kraju]: opłata za moc umowną (stała, miesięczna) i opłata za
  szczyt zmierzony w okresie rozliczeniowym. Sprawdź w taryfie sprzedawcy i OSD, który z nich masz.
- Skrypt modeluje je jednym wzorem: stawka za kW na miesiąc × moc umowna × 12. Dla szczytu zmierzonego wstaw szczyt jako
  `contracted_kw` albo policz kilka wariantów.
- Opłata za moc nie zależy od sprzedanych kWh, więc przy niskim utilization jest największym składnikiem pełnego kosztu kWh.

## 3. Dotacje
- Dotacja obniża CAPEX netto (`grants`). Nie wpisuj jej do modelu bez potwierdzonego naboru, intensywności i warunków
  [do weryfikacji w aktualnym ogłoszeniu].
- Warunki często wymuszają konfigurację (moc, liczba portów, uptime, dane dla stron trzecich) i raportowanie, a więc koszt.
  Przykład faktu: NEVI w USA finansuje projekty, które muszą spełniać 23 CFR 680 (dom-ev-regulations-us).
- Dotacja bywa wypłacana po budowie: finansowanie przejściowe nie mieści się w skrypcie.

## 4. BESS i smart charging
- Smart charging ogranicza moc w szczycie i pozwala zakontraktować mniej (dom-ev-smart-charging, dom-ev-energy-management);
  koszt: dłuższe ładowanie, ryzyko dla doświadczenia kierowcy.
- BESS ścina szczyt, zbiera tańszą energię i może obejść drogie przyłącze. Ma własny CAPEX, straty, degradację i wymianę.
  Policz: różnica `contracted_kw` oraz dodatkowa pozycja w `capex`; skrypt nie modeluje arbitrażu cen energii ani degradacji.

## 5. Rozbudowa etapami
- Etap 1: przyłącze i infrastruktura zgodnie z przewidywanym końcowym stanem, mniej ładowarek. Etap 2: kolejne punkty,
  gdy rzeczywiste utilization przekroczy próg uruchomienia rozbudowy.
- Zaleta: mniejsze ryzyko popytu. Wada: koszt dwukrotnej budowy, jeśli zabraknie rezerwy w przyłączu.
- Modeluj jako dwa pliki wejściowe albo listę `utilization`, a drugi etap jako osobną decyzję.

## 6. Przychody dodatkowe
- Sklep, gastronomia, reklama, usługi dla floty. Pole `other_revenue_per_year` jest stałą roczną; nie zależy od ruchu.
- Zapisz, kto jest stroną umowy (najemca, właściciel terenu), i przyjmij wartość ostrożną.
