# Przeramowanie — czy rozwiązujemy właściwy problem

Badanie uzupełnia brak danych; przeramowanie poprawia źle postawiony problem. Kolejność zależy od tego, co blokuje.

## Kiedy
- druga nieudana poprawka tego samego objawu;
- badanie otwiera coraz więcej pytań, zamiast zawęzić się do kontraktu;
- implementacja kolejny raz nie spełnia kryteriów albo uporczywie odchodzi od planu w ten sam sposób;
- zgłoszenie łączy objaw z przyczyną i poprawką („X się psuje, zróbmy Y”);
- brak ekspertyzy w obszarze.

Nie dla zmian mechanicznych ani gdy człowiek sam zweryfikował przyczynę.

## Procedura
1. **Rozdziel trzy rzeczy i odczytaj je człowiekowi:** obserwacja (dosłowny efekt) · zakładana przyczyna lub
   podejście · proponowany kierunek. Pewna jest tylko obserwacja, reszta to hipotezy. Nie scalasz ich, nawet gdy
   człowiek naciska „po prostu zaplanuj poprawkę”.
2. **Jedna runda 1–3 pytań** zawężających obserwację (który objaw główny, jeden czy kilka, pojedynczy przypadek czy
   klasa), z opcją „nie wiem / nie rozdzieliłem”. Opcje opisują obserwacje, nigdy przyczyny ani poprawki.
3. **Mapa wymiarów** z przeczytanego kodu i dokumentów: każdy etap łańcucha (wejście, przekształcenie, stan, efekty
   uboczne — albo osie decyzji projektowej), w którym problem mógłby powstać. Zaznacz, gdzie ląduje założenie
   człowieka. Wymiar bez śladu w materiale pomijasz.
4. **Hipotezy równolegle** — 2–4 (najwyżej 5 wykonawców tylko do odczytu, zlecenie w jednej wiadomości). Każdy dostaje
   dosłowną obserwację, jedną hipotezę i pytanie „jakie ślady musiałyby istnieć, gdyby problem był tutaj — i czy są?”.
   Wynik: silne / słabe / brak, z `plik:linia`.
5. **Pytania rozstrzygające** (2–5 łącznie): każde przesuwa ranking hipotez; zawsze z opcją „nie sprawdzałem”. Dowody
   jednoznaczne → pomiń i powiedz dlaczego.
6. **Test od innej strony:** nowy wykonawca dostaje samą obserwację, bez nazwy prowadzącej hipotezy; szukasz podobnych
   zdarzeń w historii (commity, raporty, zgłoszenia); sprawdzasz, czego hipoteza wymaga, a czego zabrania.
   Sprzeczność → wróć do kroku 4.
7. **Zapis** `frame.md` obok raportu kroku (80–150 linii): obserwacja (dosłownie) · pierwotne ujęcie (zachowane) ·
   mapa wymiarów · tabela Hipoteza | Dowód | Werdykt · sygnały zawężające · problem przeramowany albo potwierdzony
   (jedno zdanie) · pewność (wysoka / średnia / niska + co sprawdzić przed planem) · co zmienia się w planie.

## Zasady
- „Pierwotne ujęcie było trafne” to pełnoprawny wynik — nie wymyślasz przeramowania na siłę.
- Bez projektowania rozwiązania (faz, plików, decyzji technicznych) — to robi plan kroku.
- Hipotezy z mapy tego materiału, nie z „widziałem to w innych systemach”; przeczucie bez `plik:linia` nie trafia
  do wyniku.
- Limit: 2–4 rundy wykonawców i 2–5 pytań. Dłużej → potrzebne odtworzenie albo zebranie danych, nie analiza.
- Sprzeciw człowieka → nowa runda hipotez z jego argumentem, nie obrona tezy.
- Plan kroku, który dostał `frame.md`, nie powtarza pytań diagnostycznych; przy pewności „niska” zadaje jedno: najpierw
  weryfikacja czy plan z ryzykiem.

## Przykład
Zgłoszenie: „duplikaty faktur — dodajmy unikalny indeks”. Obserwacja: dwie faktury z tym samym numerem zamówienia,
oba wpisy w odstępie ok. 2 s. Przyczyna zakładana: brak blokady w bazie. Kierunek: indeks. Mapa: przycisk w UI →
żądanie → kolejka → konsument → zapis. Hipotezy: (a) podwójne kliknięcie, (b) ponowienie z kolejki bez idempotencji,
(c) wyścig dwóch konsumentów. Dowody: w logach brokera to samo id wiadomości dostarczone dwa razy po przekroczeniu
limitu potwierdzenia → (b) silne. Przeramowanie: problem to konsument bez idempotencji (be-messaging-outbox); indeks
zamieniłby duplikat w błąd 500 przy ponowieniu.

## Źródła
- Kurs 10xDevs, ed. 3 (2026), moduł 2, lekcja 4 (przeramowanie jako koło ratunkowe przy planowaniu) — materiał
  szkoleniowy (dostęp 2026-10-09).
Opisane własnymi słowami.
