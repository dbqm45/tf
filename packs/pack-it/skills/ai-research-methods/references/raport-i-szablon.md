# Raport badawczy i lista reprodukowalności

## Szablon `docs/project/02-domain/experiment-<nazwa>.md`
```
# Eksperyment: <nazwa> | autor | data | status: planowany / w toku / zakończony

TL;DR: <wynik w 2 zdaniach, rozrzut, decyzja>
Przekazanie: <następny krok, właściciel>

## Hipoteza i decyzja
Hipoteza (falsyfikowalna): ...  Kryterium porażki: ...  Decyzja, którą zmieni wynik: ...
## Dane
Źródło, licencja, zgody, okres, rozmiar, wersja/skrót, podział (czasowy/grupowy), znane braki.
## Metoda
Baseline (i jego budżet strojenia), kandydat, ablacje, metryka główna (wybrana przed), pomocnicze.
## Wyniki
Tabela: wariant | metryka główna: średnia ± odchylenie (n seedów) | różnica vs baseline [przedział] | koszt.
Wyniki w podgrupach. Liczba porównań i zastosowana korekta.
## Wyniki negatywne
Co nie zadziałało, w jakich warunkach (konfiguracja, skala), ile prób.
## Ograniczenia i zagrożenia trafności
Wewnętrzne (wyciek, strojenie), zewnętrzne (czy uogólnia się na inny okres, kraj, skalę), czego nie sprawdzono.
## Etyka
Dane osobowe, reprezentatywność, ryzyko zastosowań.
## Reprodukowalność
Commit, konfiguracja, seedy, wersja danych, środowisko, komenda, koszt obliczeń.
## Decyzja i dalsze kroki
wypuść pilotaż / zbadaj dalej / porzuć + uzasadnienie.
```
Zasada: raport opisuje także to, co nie zadziałało, i podaje warunki. Wniosek jest tak mocny, jak najsłabsze ogniwo
(mały rozrzut, jedna skala, jeden zbiór) — zapisz to wprost.

## Lista kontrolna reprodukowalności
Zbliżona do listy kontrolnej programu reprodukowalności NeurIPS 2019 (Pineau i in., JMLR 2021) i do list
kontrolnych konferencji; szczegóły pozycji sprawdź w aktualnym formularzu konferencji [niezweryfikowane].
- [ ] kod z commitem (lub załącznik), instrukcja uruchomienia jedną komendą
- [ ] wszystkie hiperparametry i zakresy przeszukiwania, sposób wyboru najlepszych
- [ ] seedy, liczba przebiegów, sposób liczenia rozrzutu
- [ ] dane: źródło, wersja, skrót, podział, kroki przetwarzania, wyjaśnienie wykluczeń
- [ ] środowisko: wersje bibliotek (lockfile), sprzęt, czas i koszt obliczeń
- [ ] wynik z przedziałem lub odchyleniem, nie pojedynczy punkt; test użyty do porównań
- [ ] determinizm: co jest niedeterministyczne (GPU, kolejność) i jak duży to rozrzut
- [ ] surowe wyniki przebiegów zapisane obok tabeli zbiorczej

## Wyniki negatywne i niepowodzenia
Zapisz hipotezę, konfigurację, wynik z rozrzutem, hipotezy o przyczynie (oznaczone jako niezweryfikowane) i czego
nie próbowano. Nie pisz „metoda nie działa”, tylko „w tej konfiguracji, na tych danych, bez efektu ponad szum”.
