---
artifact: requirements
status: approved
inputs: [intent.md]
change: CHG-SD3
---
# Wymagania CHG-SD3

## FR-SD3-1 wiersz planu z prognozą pdi
**must** — wiersz post-MVP planu pokazuje prognozę pdi (`forecast_id`, `effort`, `confidence`); przy edycji
z UI tworzy się zdarzenie `forecast.referenced`.

## Stany błędu
- pdi offline → wiersz pokazuje „brak prognozy (pdi niedostępny)"
- forecast_id nieistniejący → błąd walidacji, blokuje zapis
