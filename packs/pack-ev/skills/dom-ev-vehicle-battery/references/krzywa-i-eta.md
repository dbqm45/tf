# Krzywa ładowania i ETA w aplikacji

## Spis treści
1. Skąd wziąć krzywą · 2. Model odcinkowy · 3. Przykład liczbowy (ilustracja) · 4. Przeliczanie w trakcie sesji ·
5. AC · 6. Co pokazać kierowcy

## 1. Skąd wziąć krzywą
| Źródło | Zaleta | Wada |
|---|---|---|
| dane producenta lub katalog modeli | dostępne przed sesją | liczby konkretnych aut [do weryfikacji]; w bazie fabryki ich nie ma |
| historia własnych sesji (`Power.Active.Import` i `SoC` w czasie) | dopasowana do floty i klimatu | potrzebuje SoC, więc działa tylko dla sesji DC z SoC |
| deklaracja z ISO 15118 (maks. moc, napięcie, prąd auta) | pewny sufit w sesji | nie daje kształtu krzywej, tylko limity (pola: SKILL.md) |
| dane z API producenta | SoC i czasem moc | opóźnienie, zgoda, format każdego producenta [do weryfikacji] |

Bez żadnego źródła stosuj profil zachowawczy: stała moc do 50–60 % SoC, malejąca do 80 %, bardzo niska powyżej. Oznacz go
jako przybliżenie.

## 2. Model odcinkowy
Dla odcinka `i` o granicach `s_i … s_{i+1}` (SoC w %):
- `E_i = (s_{i+1} − s_i) / 100 × C_użytkowa` (kWh),
- `P_i = min(P_ładowarki, P_krzywej(i), P_profilu)`; w DC pamiętaj o prądzie: `P ≤ U × I_max`, a przy 400 V prąd
  stacji może być limitem (SKILL.md, 400 V i 800 V),
- `t_i = E_i / P_i`; ETA = `Σ t_i`.

Straty ładowania (sprawność, ciepło) powodują, że energia z licznika jest większa niż energia w baterii; do ETA do
zadanego SoC użyj współczynnika [do weryfikacji] albo skalibruj z historii (licznik kWh vs różnica SoC × pojemność).

## 3. Przykład liczbowy (ilustracja, nie model auta)
Bateria użytkowa 77 kWh, 20 → 80 %, ładowarka 150 kW:

| Odcinek | E | P | t |
|---|---|---|---|
| 20–50 % | 23,1 kWh | 130 kW | 10,7 min |
| 50–70 % | 15,4 kWh | 100 kW | 9,2 min |
| 70–80 % | 7,7 kWh | 60 kW | 7,7 min |
| razem | 46,2 kWh | średnio ok. 100 kW | ok. 27,6 min |

Naiwnie 46,2 / 150 = 18,5 min — o ok. 9 minut za mało. Gdyby ładowarka miała tylko 50 kW, `min` obcina krzywą auta do
50 kW w każdym odcinku: 46,2 / 50 ≈ 55 min.

## 4. Przeliczanie w trakcie sesji
- Pierwsze minuty (rozgrzewanie, negocjacja) są nietypowe: ETA pokazuj z szerszym przedziałem.
- Co kilka minut weź ostatnie `Power.Active.Import` (wygładzone z kilku próbek) i `SoC`; przelicz pozostałe odcinki
  przez skalowanie krzywej: `współczynnik = moc_obserwowana / moc_krzywej_w_tym_punkcie`.
- Gdy SoC brak (AC), licz od energii: `E_pozostała = E_cel − (Energy.Active.Import.Register − meterStart)`, tylko jeśli
  znasz energię cel, np. zadaną przez kierowcę w kWh.
- Gdy moc nagle spadnie do zera przy niskim SoC, ETA przestaje mieć sens: to sygnał do diagnozy (dom-ev-diagnostics,
  dom-ev-session-lifecycle).

## 5. AC
`P = min(oferta_stacji, OBC × fazy)`, zwykle bez odcinków. Auta 1-fazowe: oferta liczona dla 1 fazy (230 V × prąd).
ETA = energia / P, plus margines na koniec (auto zmniejsza prąd na końcu).

## 6. Co pokazać kierowcy
- Przedział („około 25–35 min”), a nie jedną liczbę.
- Przyczynę, gdy moc jest niska (zimno, wysoki SoC), jednym zdaniem — mniej zgłoszeń „ładuje wolno”.
- Podpowiedź 10–80 % na trasie, gdy cel to >80 % przy ładowarce z dużą mocą.
