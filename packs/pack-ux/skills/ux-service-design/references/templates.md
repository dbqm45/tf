# Szablony artefaktów usługi

## Blueprint — tabela
Jak w przykładzie SKILL.md: kolumny to kroki w czasie, wiersze to pasy. Każdy punkt awarii ma ID (P1…), dowód
(liczba, cytat) i właściciela. Stan obecny i docelowy w osobnych sekcjach.

## Blueprint — Mermaid
```mermaid
flowchart TB
  subgraph Klient
    K1[Wypełnia formularz zwrotu] --> K2[Pakuje i nadaje paczkę] --> K3[Czeka na zwrot pieniędzy]
  end
  subgraph Frontstage
    F1[Infolinia i czat]
  end
  subgraph Backstage
    B1[Przepisanie do ERP] --> B2[Magazyn skanuje paczkę] --> B3[Zgoda księgowości]
  end
  subgraph Wspierające
    S1[ERP] ; S2[System kuriera] ; S3[Bank]
  end
  K1 -.-> B1
  K3 -.-> F1
  B3 --> S3
```
Linie interakcji, widoczności i wewnętrznej opisz w przypisach lub jako osobne węzły-separatory; Mermaid nie ma
natywnych pasów, więc zachowaj kolejność subgraphów.

## Mapa podróży
| Etap | Działania klienta | Kanał | Myśli | Emocja (−2…+2) | Bolączka i dowód |
|---|---|---|---|---|---|
Mapa docelowa ma te same etapy, żeby dało się porównać.

## Mapa interesariuszy
| Strona | Rola w usłudze | Potrzeba | Wpływ (W/Ś/N) | Kto go słucha |
|---|---|---|---|---|

## Inwentarz punktów styku
| Punkt styku | Kanał | Właściciel | System | Dane wspólne z | Spójność (ta sama obietnica, język, dane) | Luka |
|---|---|---|---|---|---|---|

## Omnichannel — test spójności
Dla jednego przypadku klienta przejdź przez wszystkie kanały: czy zmiana kanału wymaga powtórzenia danych, czy
odpowiedź o stanie sprawy jest ta sama, czy pracownik widzi historię z innych kanałów.
