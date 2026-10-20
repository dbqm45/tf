**Test-driven (TDD)**
- Kod produkcyjny piszesz dopiero po teście, który NIE przechodzi z właściwego powodu: najpierw test, uruchomienie
  (czerwony), potem minimalny kod (zielony), na końcu refaktoryzacja. Pilnuje tego hook `tdd_guard`.
- Przy błędzie najpierw test odtwarzający błąd. Jeden test = jedno zachowanie, opisane przez publiczne API.
- Oczekiwane wartości bierzesz ze specyfikacji i przykładów, nie z kodu. Testów nie osłabiasz, nie usuwasz ani nie
  wyłączasz, żeby „przeszło”.
- W raporcie podajesz dowód czerwonego testu (polecenie i fragment porażki) i zielonego.
