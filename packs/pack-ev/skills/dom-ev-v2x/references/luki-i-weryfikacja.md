# Luki wiedzy V2X — co sprawdzić, zanim trafi do decyzji

| Temat | Co wiemy w bazie | Czego brak | Jak sprawdzić |
|---|---|---|---|
| OCPP 2.1 V2X/DER | import skilla dom-ev-ocpp-2x: 2.1 dodaje V2X/DER | specyfikacja OCA 2.1 | researcher, openchargealliance.org (pobranie 2.1 po rejestracji) |
| Ujemny limit w 2.0.1 | schemat `limit` bez `minimum` | semantyka w specyfikacji 2.0.1, część K | specyfikacja OCA 2.0.1 |
| Energia oddana w OCPI | `total_energy` w CDR to jedna liczba | oficjalne pole eksportu (OCPI 2.2.1, 2.3.0) | spec OCPI na github.com/ocpi/ocpi, dom-ev-ocpi |
| Wymogi OSD, kody sieci (np. rozporządzenie UE 2016/631 [do weryfikacji] i krajowe) | brak | warunki przyłączenia jednostki wytwórczej, zgoda OSD | OSD, krajowa instrukcja sieciowa |
| Degradacja i gwarancja | brak liczb | wpływ cykli V2X na baterię, polityki producentów | dom-ev-vehicle-battery, warunki gwarancji modelu |
| CHAdeMO V2G | jedno zdanie: historyczna droga V2G, wyparta przez ISO 15118-20 na rynku UE | status w danym kraju | researcher |
| Wymagania normy ISO 15118-20 | tylko to, co ujawnia josev (ranga W) | tekst normy | ISO (płatne), nie cytuj z pamięci |
| Ceny i podatki od energii oddanej | brak | stawki i podatki w PL | dom-ev-regulations-pl, doradca podatkowy |

Reguła: liczby i terminy bez źródła w bazie podawaj jako przykład z oznaczeniem [do weryfikacji]; nie kopiuj tekstu specyfikacji.
