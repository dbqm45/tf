# Analiza jednego przepływu (pogłębienie po mapie)

Mapa repo mówi, gdzie patrzeć. Analiza przepływu mówi, **jak jeden przepływ działa dziś** (np. „zapis wiadomości”,
„naliczenie rabatu”) i co jest w nim kruche — przed decyzją o zmianie. Wynik jest wejściem do planu kroku albo do
wyboru refaktoryzacji (eng-refactor-planning). Audyt całego modułu w wielu wymiarach to eng-tech-debt-audit;
przyczyna konkretnego błędu — eng-debugging.

## 1. Kontrakt zakresu
- **Wejście:** mapa repo jako prior — cel ze „Stref ryzyka”, 2–3 pliki startowe z „Pierwszego dnia”, pierwsze
  `unknowns` z „Ograniczeń”. Bez mapy: najpierw mapa albo jawna zgoda człowieka na analizę bez niej.
- **Jeden przepływ**, nie podsystem. Na górze raportu jedna linia celu: co badam, od którego pliku, dlaczego mapa
  wskazała ten obszar.
- **Twarda granica:** tylko stan obecny — bez propozycji refaktoru i bez docelowej architektury.

## 2. Trzech wykonawców równolegle (ten sam kontrakt, tylko odczyt)
1. **Trace end-to-end:** od punktu wejścia przez warstwy do zapisu lub odczytu i z powrotem; kroki z `plik:linia`;
   diagram sekwencji (Mermaid). Skąd dane, kto waliduje, gdzie zmienia się stan, co wraca. Obie strony (np.
   optymistyczny UI i serwer) i miejsce, w którym się uzgadniają. Warstwy, które tylko delegują, nazwij wprost.
2. **Luki w testach:** które metody i gałęzie ścieżki mają test (nazwa testu), które nie — zwłaszcza ścieżki błędów.
3. **Zasięg zmiany:** co musi zmienić się razem — szew interfejsu, warstwy generowane, model, migracje, testy;
   graf statyczny + współzmiany z `git_territory.py --cochange` (para vs hub).
Każde twierdzenie z etykietą evidence / inference / unknown.

## 3. Raport `docs/project/<krok>/research.md`
1. **Cel** (1 linia).
2. **Przegląd przepływu** — przepływ, nie spis plików; diagram sekwencji.
3. **Dług jako mapa kruchości:** rodzaj ryzyka w języku connascence (kolejność, znaczenie, pozycja, algorytm;
   statyczna vs dynamiczna; dystans), luki siatki testów, zasięg. **Osobno sprzężenia tanie** — kod generowany,
   regeneracja, rzeczy łapane przez kompilator lub CI. Nie pisz „tightly coupled”; nazwij rodzaj.
4. **Korekty priorów:** co z mapy okazało się nieaktualne — jawnie, z dowodem.
5. **Unknowns** z tym, jak je rozstrzygnąć (kogo zapytać, co uruchomić).
6. **Weryfikacja twierdzeń strukturalnych** („dokładnie 4 wywołania”, „tylko tutaj”, „zawsze przez X”): każde
   sprawdzone ast-grepem lub LSP, każde zero potwierdzone `rg`; poprawki w miejscu ze śladem „5 (raport: 4)”;
   tabela twierdzenie → werdykt → dowód → metoda.
7. **Hotspoty przepływu:** częstość zmian z mapy × złożoność plików przepływu (tani proxy, np. linie niepuste).

## 4. Kryteria przeglądu raportu (człowiek, świeży kontekst)
- przepływ zamiast listy plików?
- dług nazwany rodzajem ryzyka, a tani oddzielony od groźnego?
- liczby zweryfikowane narzędziem, zera potwierdzone?
- nic nie proponuje zmian?

## 5. Przykład
Przepływ „zapis wiadomości”: 6 warstw w katalogach, z czego 4 tylko delegują; zapis pojedynczy jest fasadą nad
zapisem wsadowym; zapisane obiekty nie są ponownie czytane z bazy. Kruchość: zapis pozycyjny 18 kolumn (connascence
pozycji, bez osłony); model wiadomości na backendzie i jego ręczna kopia na froncie (znaczenie, duży dystans, prawie
zero współzmian — cichy dług); ścieżki błędów bez testów. Tanie: warstwy store generowane z interfejsu (rozjazd
łapie CI). Korekta prioru: mapa podawała 3 warstwy delegujące, są 4. Weryfikacja: „4 wywołania zapisu wsadowego”
→ 5 (raport: 4), piąte w teście integracyjnym.
