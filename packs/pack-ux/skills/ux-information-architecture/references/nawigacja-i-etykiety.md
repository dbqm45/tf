# Nawigacja, etykiety, wyszukiwanie, mapa serwisu

## Wzorce nawigacji
| Wzorzec | Kiedy | Uwaga |
|---|---|---|
| nawigacja globalna (główne menu) | główne działy, zawsze widoczne | 5–9 pozycji [heurystyka, nie reguła], stałe położenie |
| nawigacja lokalna / boczna | podział w dziale, wiele poziomów | pokazuj położenie (bieżąca pozycja) |
| okruszki | głębsza hierarchia | uzupełnienie, nie zamiennik menu |
| mega menu | dużo pozycji w 2 poziomach | czytelne grupy, klawiatura, nie otwiera się tylko na hover |
| powiązane treści, odsyłacze | treść pasuje do kilku miejsc | zamiast kopii |
| nawigacja fasetowa | sklep, katalog z cechami | filtry z metadanych, liczba wyników |
| stopka | prawne, pomoc, kontakt | nie na zadania główne |
| nawigacja w aplikacji (dolny pasek, zakładki) | 3–5 głównych obszarów | etykiety tekstowe obok ikon |
Dostępność: kolejność fokusu, landmarki `nav`, nazwy dostępne, bez zależności od hovera — fe-web-platform.

## Etykiety
- Z języka użytkowników (sortowanie otwarte, zapytania w wyszukiwarce), nie z organigramu firmy.
- Rozłączne i przewidywalne („Urlopy i nieobecności”, nie „Różne”); koniec z „Inne”, „Pozostałe”, „Usługi” bez dopowiedzenia.
- Jedna nazwa na jedno pojęcie w całym serwisie; pierwsze słowo niesie informację (zapach informacji).
- Linki opisowe („Zasady pracy zdalnej”), nie „Kliknij tutaj”.

## Wyszukiwanie
- Analiza dzienników: najczęstsze zapytania, zapytania bez wyników, wyniki bez kliknięć → synonimy, nowe treści, korekty etykiet.
- Pole widoczne, szeroko; podpowiedzi; tolerancja literówek; filtry z metadanych; wynik z kontekstem (typ, data).
- Brak wyników: komunikat, sugestie, kontakt; nie pusta strona.
- Najlepsze wyniki: strona zadania na górze (promowane wyniki dla częstych zapytań).

## Mapa serwisu
Hierarchia wcięciami albo diagram Mermaid `flowchart TD`: poziom 1 (działy), poziom 2, kluczowe strony; oznacz
treści w kilku miejscach (odsyłacze), strony tylko z wyszukiwarki i planowane usunięcia. Mapa jest wersjonowana
razem z `ia-documentation.md`.
