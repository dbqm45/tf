# Paragon i opłata za zgubiony bilet

Jako kierowca chcę widzieć na wydruku, za jaki czas płacę. Parking chce też pobierać opłatę za zgubiony bilet.

## Kryteria akceptacji
- AC1: Wiersz poleceń przyjmuje opcję `--receipt`: `python3 -m parking.cli 125 --receipt` wypisuje dwie linie:
  `Czas postoju: 2 h 5 min` i `Do zapłaty: 12,00 zł`. Bez opcji wynik jest taki jak dotąd.
- AC2: Funkcja `lost_ticket_fee()` w `parking/fees.py` zwraca opłatę za zgubiony bilet. Wysokość tej opłaty ustala
  dział finansów — jeszcze jej nie podał.

Paragon i opłata za zgubiony bilet to dwie niezależne części. Nie zmieniaj stawki godzinowej ani limitu dobowego.
