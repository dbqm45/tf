# Decyzja, scenariusze i ryzyka spoza modelu

## Spis treści
1. Jak czytać wynik skryptu
2. Scenariusze
3. Czego model nie widzi
4. KPI finansowe z danych

## 1. Jak czytać wynik skryptu
- `NPV` ujemne i próg utilization poniżej utilization bazowego znaczy: EBITDA jest dodatnia, ale nie zwraca CAPEX.
- Okres zwrotu liczony z niedyskontowanych EBITDA bez finansowania; brak wartości oznacza „poza horyzontem”.
- Wrażliwość pokazuje NPV przy zmianie jednego założenia (utilization ×0,8 i ×1,2, cena ×0,9 i ×1,1, energia ×1,2). Które założenie
  zmienia wynik najbardziej, to je potwierdzasz pierwsze (oferta ładowarek, rachunek energii, umowa roamingowa).
- Kod wyjścia 1 nie jest błędem: to NPV poniżej zera. Kod 2 oznacza błąd wejścia.

## 2. Scenariusze
- Zapisz je w osobnych plikach `<scenariusz>.json` i porównaj `--json`.
- Minimalny zestaw: pesymistyczny (niski utilization, droższa energia, niższa cena), bazowy, optymistyczny.
- Lista `utilization` na każdy rok odtwarza krzywą wzrostu; nie wstawiaj stałej wartości docelowej od roku 1.

## 3. Czego model nie widzi
- Ryzyko i termin przyłącza, zmiany warunków OSD.
- Konkurencję w okolicy i zmianę ruchu (nowa droga, nowy konkurent).
- Regulacje: wymogi dotacji i płatności ad hoc, zmiany taryf energii i opłat.
- Awarie i uptime, które obniżają kWh i reputację (dom-ev-kpi-analytics, dom-ev-asset-operations).
- Podatki, amortyzację, finansowanie, inflację, wymianę sprzętu, wartość rezydualną.
- Zmianę mocy aut w czasie (dom-ev-vehicle-battery) i wzrost średniej mocy.

## 4. KPI finansowe z danych
- Przychód na EVSE, kWh na EVSE, utilization i średnia moc z sesji i CDR; definicje i pułapki liczenia: dom-ev-kpi-analytics.
- Uzgodnij przychód z rozliczeniami roamingu (dom-ev-cdr-settlement), bo CDR może zawierać korekty.
- Porównaj dane rzeczywiste z założeniami skryptu i przelicz NPV z faktycznym utilization po kilku miesiącach pracy.
