# Test obciążeniowy bramy i reconnect storm

Wzorce to wiedza ogólna o testach obciążeniowych, zastosowana do OCPP-J. Liczby (połączeń na węzeł, komunikatów
na sekundę, czasy) **[do weryfikacji]** — bierz je z własnego pomiaru, nie z tego pliku.

## Co mierzysz
| Wielkość | Po co |
|---|---|
| liczba utrzymanych połączeń WebSocket | pojemność bramy (połączenia, nie komunikaty) |
| tempo udanych handshake’ów na sekundę | odporność na storm |
| opóźnienie odpowiedzi na CALL: p50, p95, p99 | osobno dla BootNotification, Authorize, StartTransaction |
| odsetek CALLERROR i połączeń odrzuconych/zerwanych | błędy pod obciążeniem |
| CPU, pamięć, deskryptory plików węzła bramy i generatora | wąskie gardło po obu stronach |
| głębokość kolejki i opóźnienie konsumenta | zator w domenie za bramą |

## Plan testu
1. **Cel i próg**: np. „N połączeń, p99 odpowiedzi poniżej X” — N i X ustal z wymagań, nie z pamięci.
2. **Generator**: wiele instancji symulatora (`charge_sim.py` w pętli lub własny klient na `ocpp_ws.py`), każda
   z unikalnym ID stacji. Rozłóż je na kilka maszyn; sprawdź limity deskryptorów i portów generatora.
3. **Rampa**: zwiększaj liczbę połączeń stopniowo i zapisuj, w którym punkcie rośnie p99 lub błędy.
4. **Stan ustalony**: utrzymaj połączenia z Heartbeat i MeterValues przez dłuższy czas (wycieki pamięci).
5. **Środowisko**: osobne od produkcji, o znanej konfiguracji; zapisz wersje i sprzęt razem z wynikiem.

## Scenariusz „5000 ładowarek wraca po restarcie”
| Wariant | Opis | Co pokazuje |
|---|---|---|
| Peak | wszystkie symulatory łączą się w tym samym momencie | najgorszy przypadek: CPU na TLS i BootNotification |
| Rampa z jitterem | start rozłożony losowo w oknie czasu | realistyczny powrót stacji z backoffem [do weryfikacji] u firmware |
| Częściowy | wraca jedna strefa lub jeden najemca | izolacja najemców, limity per najemca |
| Z zaległościami | każda stacja po powrocie wysyła kolejkę offline | przepustowość domeny i idempotencja |

Obserwuj: czy brama odrzuca nadmiar sygnałem, który stacja potrafi obsłużyć; czy `Pending` w BootNotification
rozkłada ruch; czy po stabilizacji liczba połączeń wraca do N. Obrona i wzorce — dom-ev-cpms-architecture
(`.claude/skills/dom-ev-cpms-architecture/references/brama-i-routing.md`, sekcja 4).

## Wynik
Zapisz: sprzęt, wersję, N, rampę, p50/p95/p99, błędy, wąskie gardło, wniosek. Wynik jest ważny dla tej konfiguracji —
po zmianie bramy lub sprzętu powtórz test.
