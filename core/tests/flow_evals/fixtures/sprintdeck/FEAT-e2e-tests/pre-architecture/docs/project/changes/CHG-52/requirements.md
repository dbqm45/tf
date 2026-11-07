---
artifact: requirements
status: accepted
inputs: [intent.md]
change: CHG-52
---
# Wymagania CHG-52

## FR-521-1 pokój z 10 klientami
**must** — Playwright uruchamia 10 równoczesnych klientów łączących się do pokoju; każdy wprowadza ryzyko; konsensus
Risk Deck zbiera się bez błędu.
- Given: 10 klientów połączonych do pokoju
- When: każdy klient wysyła ryzyko
- Then: wszystkie ryzyka pojawiają się u wszystkich klientów w < 2 s

## FR-521-2 utrata sieci
**must** — klient traci sieć na 5/10/30 s i wraca; stan pokoju odbudowuje się bez utraty danych.
- Stany błędu: >60 s → klient oznaczony jako offline; zapis z offline odrzucony.

## NF-SD2-1 metryki
**should** — per-klient `realtime_connected`, `realtime_backlog`.
