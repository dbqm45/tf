# Wymiarowanie klastra — wzory

Spis treści: Pojemność po awarii · Storage · Szablon tabeli

## Pojemność po awarii (N+1)
- Użyteczne rdzenie = (N − 1) × rdzenie na węzeł; użyteczna pamięć = (N − 1) × RAM węzła × (1 − rezerwa hosta ~10–15%) [przykład].
- Stosunek vCPU:rdzeń = suma vCPU / użyteczne rdzenie. Granica zależy od obciążenia; weryfikuj CPU ready/steal.
- Hiperthreading nie podwaja rdzeni; w licencjach liczy się zwykle rdzenie fizyczne.

## Storage
- Pojemność użyteczna: replikacja ×3 → surowa/3; RAID 6 z n dysków → (n−2)/n; EC k+m → k/(k+m).
- Zapas na odbudowę i spadek wydajności po awarii dysku/węzła; w Ceph pula nie powinna przekraczać ~80% [przykład],
  by odbudowa po awarii węzła się zmieściła.
- Przepustowość (MB/s) = IOPS × rozmiar bloku; współbieżność = przepustowość × opóźnienie.

## Szablon tabeli
| zasób | wymaganie (p95) | wyliczenie | z N+1 i zapasem | uwagi |
|---|---|---|---|---|
| vCPU | | | | |
| RAM | | | | |
| IOPS / opóźnienie p99 | | | | |
| pojemność użyteczna | | | | |
| sieć (storage, migracja, VM) | | | | |
