# Ładowanie w pracy i B2B — grupy, taryfa zerowa, najemcy, przepisy o budynkach

Spis: 1. Ładowarki za szlabanem · 2. Taryfa zerowa vs wyłączenie · 3. Najemcy · 4. EPBD · 5. Polska · 6. Przykład

## 1. Ładowarki za szlabanem
Lokalizacja niepubliczna: w OCPI `Location.publish` = `false` z `publish_allowed_to` (tylko wskazane tokeny widzą
lokalizację), albo lokalizacja poza roamingiem i dostępna tylko w aplikacji firmy. Dostęp wymusza CSMS (grupy tokenów →
lokalizacje, `model-danych-i-uprawnienia.md`), a szlaban jest osobnym systemem — skorelowanie tablicy rejestracyjnej z
tokenem to dodatkowa dana osobowa. Godziny dostępu: `opening_times` w lokalizacji i reguły CSMS. Gdy szlaban zamyka
miejsce publiczne, pamiętaj o obowiązkach dla punktów dostępnych publicznie (dom-ev-regulations-eu).

## 2. Taryfa zerowa vs wyłączenie z rozliczenia
| Podejście | Co powstaje | Skutek |
|---|---|---|
| Taryfa zerowa (Free of Charge) | sesja, CDR z `total_cost` = 0, taryfa `FLAT` 0.00 w `tariffs` | pełne raporty kWh, koszt energii u hosta, audyt |
| Wyłączenie z rozliczenia | brak CDR lub brak sesji w raporcie | brak zużycia per klient, brak dowodu, rozjazd energii z licznikiem hosta |
Zasada: darmowe = **cena 0**, nie **brak danych**. W OCPI `total_cost` = 0 oznacza darmową sesję, a brak pola nie
oznacza darmowej (Session). Wartość biznesowa: „ile kosztuje nas darmowa oferta dla klienta B2B” = kWh × koszt energii
(dom-ev-business-economics). Koszt zerowy dla kierowcy może mieć niezerowy koszt wewnętrzny (energia kupiona) — raportuj
oba. Cenę w CPO buduje dom-ev-tariffs-pricing; korekty CDR dom-ev-cdr-settlement.

## 3. Podział kosztów między najemców
1. Źródło kWh: licznik ładowarki (MID) per sesja; licznik główny tylko do bilansu strat budynku.
2. Przypisz sesję do najemcy przez grupę tokenów lub centrum kosztów.
3. Koszty zmienne: kWh × cena energii hosta (wg umowy z najemcą, ewentualnie marża).
4. Koszty stałe (opłata za moc, serwis, CSMS): klucz — po równo, po liczbie miejsc, po kWh [wybiera umowa].
5. Faktura/nota zbiorcza per najemca; załącznik: lista sesji.
Kto kupuje energię i kto jest stroną faktury — model hosta w dom-ev-market-roles.

## 4. EPBD (dyrektywa (UE) 2024/1275)
| Art. | Wg tekstu (skrót własny) |
|---|---|
| 14 ust. 1 | budynki niemieszkalne nowe lub po gruntownej renowacji z > 5 miejscami: punkt ładowania na 5 miejsc, pre-okablowanie dla co najmniej 50 % miejsc, kanały dla reszty; biura: punkt na 2 miejsca |
| 14 ust. 2 | istniejące niemieszkalne z > 20 miejscami: do 01.01.2027 punkt na 10 miejsc albo kanały dla ≥ 50 % |
| 14 ust. 4 | mieszkalne z > 3 miejscami: pre-okablowanie 50 %, nowe — co najmniej jeden punkt |
| 14 ust. 6 | punkty zdolne do smart charging, sterowane niezastrzeżonymi i niedyskryminującymi protokołami |
| 14 ust. 7 | państwa zachęcają, by punkty niepubliczne stosowały zasady cenowe z AFIR art. 5 ust. 4 |
| 16 ust. 1 | właściciele, najemcy i zarządcy mają dostęp do danych systemów budynku (punkty ładowania) |
| 35 | termin transpozycji: 29.05.2026 |
Dla software: wspieraj smart charging na otwartych protokołach (OCPP), raport zużycia per najemca i dostęp do
danych za zgodą; dosłowna zgodność z art. 14 ust. 6 [do weryfikacji]. Tekst skonsolidowany: dom-ev-regulations-eu.

## 5. Polska (ustawa o elektromobilności i paliwach alternatywnych, Dz.U. 2026 poz. 1243)
| Art. | Treść |
|---|---|
| 12 ust. 1 | budynki użyteczności publicznej i wielorodzinne w wymienionych gminach: moc przyłączeniowa pozwalająca na punkty ≥ 3,7 kW |
| 12a ust. 1 | niemieszkalne z > 10 stanowiskami: co najmniej jeden punkt i kanały na punkt na każde pięć stanowisk |
| 12a ust. 2 | mieszkalne z > 10 stanowiskami: kanały na wszystkich stanowiskach |
| 12b ust. 1–2 | wielorodzinne (> 3 lokale): punkt wymaga zgody zarządu wspólnoty; dla punktu < 11 kW to zwykły zarząd |
| 12b ust. 3–4 | wniosek: oświadczenie o kosztach, tytuł prawny; ekspertyza w 30 dni |
Szczegóły i wyjątki (zabytki, koszty > 7 % przebudowy) — czytaj tekst w bazie `pl-elektromobilnosc`; przepisy OSD i
przyłączenia: dom-ev-energy-management, `.claude/skills/dom-ev-energy-management/references/przepisy-przylacze.md`.

## 6. Przykład
Biurowiec, 40 miejsc, 8 ładowarek AC. Grupy: „Pracownicy” (24/7, taryfa wewnętrzna), „Goście” (token z recepcji, 8 h
ważności, taryfa gościa), „B2B-Alfa” (taryfa zerowa). Po miesiącu: 1 820 kWh, z czego B2B-Alfa 410 kWh przy koszcie
energii hosta 0,60 [ilustracja]/kWh = 246 — kwota widoczna w raporcie dzięki CDR z kosztem 0.
