# Szczegóły: reguła Sigma, test i metryki

Spis treści: 1. Szablon reguły · 2. Wartości pól · 3. Struktura repozytorium i CI · 4. Karta techniki · 5. Metryki

## 1. Szablon reguły (ilustracja, zachowanie, nie nazwa narzędzia)
```yaml
title: Office uruchamia PowerShell z zakodowanym poleceniem
id: 00000000-0000-4000-8000-000000000000   # [przykład] wygeneruj własny UUID
status: experimental
description: Proces Office tworzy powershell.exe z parametrem kodującym polecenie.
references:
  - https://attack.mitre.org/techniques/T1059/001/
author: Zespół detekcji
date: 2026-10-17
tags:
  - attack.execution
  - attack.t1059.001
logsource:
  category: process_creation
  product: windows
detection:
  parent:
    ParentImage|endswith: ['\winword.exe', '\excel.exe']
  child:
    Image|endswith: '\powershell.exe'
    CommandLine|contains: ['-enc', '-EncodedCommand']
  condition: parent and child
falsepositives:
  - Makra firmowe wdrażające konfigurację (wąski wyjątek po ścieżce dokumentu)
level: high
```
Pola `logsource` (`category`, `product`, `service`) konwertery mapują automatycznie; `definition` jest informacyjne.

## 2. Wartości pól (Sigma Rules Specification 2.1.0, odczyt 2026-10-17)
- `status`: `stable`, `test`, `experimental`, `deprecated`, `unsupported`.
- `level`: `informational`, `low`, `medium`, `high`, `critical`.
- `condition`: `and`, `or`, `not`, `1 of selection*`, `all of them`, nawiasy; pierwszeństwo od najsłabszego: `or`, `and`, `not`, `x of`.
- `tags`: małe litery, cyfry, `_`, `-`, przestrzenie nazw po kropce (`attack.t1234`).
- `related` (z `id` i `type`: `derived`, `obsolete`, `merged`, `renamed`, `similar`) i `name` (do korelacji).
- Polecenie `sigma check` do walidacji: [niezweryfikowane] (README sigma-cli dokumentuje `sigma convert`, `sigma list`, `sigma plugin`).

## 3. Struktura repozytorium i CI
```
rules/<źródło>/<technika-lub-zachowanie>.yml
tests/positive/<id-reguły>.json   # zdarzenia, które MUSZĄ dać alert
tests/negative/<id-reguły>.json   # zdarzenia normalnej pracy, które NIE mogą dać alertu
pipelines/                        # mapowanie pól na schemat SIEM-a
```
Etapy CI: walidacja schematu → kontrola obowiązkowych pól i unikalności `id` → konwersja → test pozytywny i negatywny
na silniku lub w zapytaniu na danych testowych → artefakt (zapytania docelowe). Wdrożenie z artefaktu, nie ręcznie.
Dane testowe bez danych osobowych (zanonimizowane lub z laboratorium).

## 4. Karta techniki (jedna na priorytetową technikę)
Technika (ID, wersja ATT&CK) · źródło danych i jego stan · reguły · ostatni test (data, wynik, czas do wykrycia) ·
luki · właściciel · data następnego przeglądu.

## 5. Metryki (definicje)
- **Czas do wykrycia** = czas alertu − czas wykonania techniki w teście; mediana i p90, nie średnia.
- **Pokrycie przetestowane** = priorytetowe techniki z wynikiem „wykryto” w ostatnim teście / wszystkie priorytetowe.
- **Fałszywe alarmy** = alerty zamknięte jako nieszkodliwe / wszystkie alerty reguły w oknie [przykład: 30 dni].
- **Zdrowie reguł**: odsetek z testem, runbookiem i przeglądem w ostatnich 12 miesiącach.
