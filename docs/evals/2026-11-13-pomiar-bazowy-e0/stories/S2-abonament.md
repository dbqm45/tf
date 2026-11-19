# Zniżka abonamentowa

Jako kierowca z abonamentem chcę płacić mniej za dłuższy postój, żeby abonament się opłacał.

## Kryteria akceptacji
- AC1: `fee(minutes, subscriber=True)` liczy pierwszą rozpoczętą płatną godzinę po pełnej stawce (4 zł), a każdą
  następną za połowę (2 zł). Przykład: 61 minut → 6 zł, 180 minut → 8 zł.
- AC2: Bez abonamentu (`subscriber=False`, wartość domyślna) opłata jest taka jak dotąd.
- AC3: Limit dobowy 40 zł obowiązuje także abonenta; darmowe 30 minut też.
- AC4: Wiersz poleceń przyjmuje opcję `--subscriber`: `python3 -m parking.cli 180 --subscriber` wypisuje `8,00 zł`.
  Bez opcji wynik jest taki jak dotąd.

Nie zmieniaj stawki godzinowej ani limitu dobowego.
